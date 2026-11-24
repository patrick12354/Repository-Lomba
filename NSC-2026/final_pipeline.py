"""
NSC 2026 - Air Humidity Prediction - complete, self-contained pipeline.

Reads ONLY the three official competition files and writes the submission. No other
module, no cached artefact, no network access, no external data. Deterministic: every
model carries a fixed seed, so re-running reproduces the submitted file byte for byte.

    python final_pipeline.py              # reproduces the best submission, LB 3.04904
    python final_pipeline.py --selftest   # + prove no feature depends on the target
    python final_pipeline.py --tod-blend  # session-8 candidate -> v10_todblend.csv, LB 3.02942
    python final_pipeline.py --tod-blend --tod-bias   # LB 3.00589 -> v11_seed5.csv
    python final_pipeline.py --selftest --tod-blend --harm-bias --l2-member --increment
                                          # BEST validated, session 21 -> v21_increment_v16.csv

Design notes relevant to the competition rules
----------------------------------------------
* Models are fitted exclusively on rows from train.csv. No test row is ever fitted on.
* The target never enters feature construction. Verified by rebuilding every feature with
  the target column wiped to NaN and comparing bit for bit (see `--selftest`).
* Nothing is hand-entered. Blend weights come from non-negative least squares on
  out-of-fold predictions; the only fixed numbers are model hyper-parameters and the
  physical clip of relative humidity to [5, 100].
* The one deliberate transductive choice: centered rolling windows on a TEST row average
  exogenous readings from neighbouring test rows. That is future feature data, never
  future target data, and it is what the brief asks for -- the weather station and IoT
  probes keep recording through the test period and all 25 exogenous columns are supplied
  in test.csv. Those sensor columns are the only test-file information used anywhere.
* `--tod-bias` additionally subtracts the per-time-of-day-band bias, with the global level
  removed. Non-negative least squares cannot produce an intercept, so `--tod-blend` leaves
  that offset untouched; the blend under-predicts the ~04:00 humidity peak and over-predicts
  the ~15:00 trough in 18 of 18 nested folds. Worth -0.070 nested (95% CI [-0.091, -0.050],
  17/18 folds, all three fold families), against -0.009 for a random conditioner with the
  same three free parameters. It took the leaderboard from 3.02942 to 3.00589. See
  progress.md section 69.
* `--tod-blend` fits one blend weight vector per time-of-day band instead of one for the
  whole day. Nested cross-validation puts it at -0.080 (95% CI [-0.120, -0.042]), it wins
  in all three fold families under two nesting schemes, and a random conditioner with the
  same parameter count buys only -0.007. Off by default so the no-flag run still
  reproduces the scored file byte for byte; see progress.md section 61.
* `--increment` adds a second family of models that predict the CHANGE in humidity over 30
  minutes and 2 hours, then reconciles that path against the stack's level prediction by a
  single sparse least-squares solve. It fits on train rows only, both endpoints of every
  training difference are train rows, and inference reads only exogenous columns -- no RH
  value from the test window is an input and nothing is fed back recursively. The two
  horizons and their weights were frozen by the session-20 screen before this flag existed.
  See `reconcile()` and progress.md sections 147 and 150.
* Two further flags exist for variants that were tried and are OFF by default:
  `--calibrate` (dispersion slope) and `--strict-features` (boundary-truncated training
  features). Together they scored 3.28564 against this file's 3.04904. Keep them off
  unless you are deliberately reproducing that experiment.
"""
import argparse
import re
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

import lightgbm as lgb
import catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls
from scipy.sparse import csc_matrix, diags, identity
from scipy.sparse.linalg import spsolve

DATA = 'Dataset/'
OUT = 'outputs/submissions/final_submission_v2.csv'
OUT_TOD = 'outputs/submissions/v10_todblend.csv'   # written by --tod-blend
TARGET = 'air_humidity'
SEEDS_OOF = (0, 1, 2)        # default; --oof-seeds overrides
SEEDS_FIT = (0, 1, 2, 3, 4)  # default; --seeds overrides
OUT_SEED = 'outputs/submissions/v11_seed%d.csv'   # written when --seeds is raised
BLEND_SHRINK = 0.25          # legacy default: NNLS weights pulled toward equal weighting
# Session 16 measured what that pull costs. Across all 18 nested folds NNLS gives `ridge`,
# `ridge_e` and `l2` a weight of exactly zero, every fold, sd 0.000 -- so the shrinkage is
# not stabilising anything, it is handing 12.6% of the blend to three members the fit
# rejects unanimously. Removing it is worth -0.058 nested (15/18 folds, negative in P, Q
# and R, 95% CI [-0.084, -0.030]) and it drops `ridge` and `ridge_e` to zero, which are the
# two members section 80 showed are wrecked by the private slice's out-of-support pressure
# block. See progress.md sections 105-107.
# SUPERSEDED (progress.md section 279): do NOT pass --blend-shrink 0.0. Sections 106 and
# 138 measured that change on the legacy meta-validation, which shared labels across
# folds; on the repaired past-only harness the response is monotone the other way --
# +0.016 pooled at 0.15 rising to +0.055 at 0.00, with BOTH primary blocks worse. The
# public score agreed (v20_shrinkonly 3.05372 against v16's 3.02586) while three internal
# evaluations were wrong together, because all three ran on the same leaky harness.
SHRINK_V17 = 0.0
CAL_SHRINK = 0.70            # dispersion slope pulled toward 1.0, only if --calibrate
# Session 48. The 0.70 above is session-6's value and it belongs to the verdict section 46 wrote:
# the slope was fitted on interior CV folds and applied to a window whose prediction spread was
# above every one of them, and it lost 0.237 on the leaderboard AS PART OF A BUNDLE with
# --strict-features. Section 317 re-measures the slope forward -- fitted on each block's own
# past-only inner frame, applied to the block -- and gets 1.021-1.051 across six blocks against
# realised slopes of 0.980-1.079. --cal-shrink exposes the strength; 0.50 is the value section 318
# measures and the one every other correction in this file uses.
# Session 47. `cat` is the only blend member with a large forward LEVEL bias: on the scored rows
# of the forward cache its mean signed error is -2.89 (outer) and -4.50 (inner) against +-0.8 for
# every other member, while its IN-SAMPLE bias is -0.006. That is a property of `Huber:delta=4`
# on a target with sd 18 %RH -- past 4 %RH the gradient is constant, so the member tracks
# something close to a conditional median and lands low when asked to predict forward. It holds
# about a quarter of the blend weight and nothing downstream can remove the offset: NNLS weights
# are non-negative and normalised, so the blend has no intercept, and `tod_bias` and `harm_bias`
# both fit an intercept and deliberately discard it (sections 69 and 73). Subtracting the
# member's own out-of-fold mean error, at the same 0.5 every other correction in this file uses,
# is worth -0.077 pooled on B1+B2 with five of six forward blocks better. See section 310.
DEBIAS_MEMBERS = ('cat',)    # which members --cat-debias corrects
CATDB_SHRINK = 0.50          # strength of that correction, only if --cat-debias
TOD_BINS = 3                 # time-of-day bands for --tod-blend
TOD_SHRINK = 0.50            # per-band weights pulled back toward the global vector
TODB_SHRINK = 0.50           # per-band bias correction pulled toward zero (--tod-bias)
HARM_SHRINK = 0.50           # harmonic bias correction pulled toward zero (--harm-bias)
OUT_HARM = 'outputs/submissions/v12_harmbias.csv'
OUT_DROP = 'outputs/submissions/v13_lowsupport.csv'
OUT_RNG  = 'outputs/submissions/v14_rngbias.csv'      # with --drop-lowsupport
OUT_RNG2 = 'outputs/submissions/v15_rngonly.csv'      # without it - the isolated bet
OUT_L2   = 'outputs/submissions/v16_l2member.csv'     # --l2-member
OUT_V17  = 'outputs/submissions/v17_shrink.csv'       # --blend-shrink 0.0 [--robust-core]
ROBUST   = 'robust_hbt'   # the stable-core LightGBM, see stable_core() and section 108
NOPRESS  = 'bag_nopress'  # LightGBM without the pressure block, see section 115
OUT_V18  = 'outputs/submissions/v18_nopress.csv'    # + --bag-nopress
OUT_V19  = 'outputs/submissions/v19_noridge.csv'    # + --drop-ridge
OUT_V20  = 'outputs/submissions/v20_shrinkonly.csv' # --blend-shrink 0.0 and nothing else
OUT_V21  = 'outputs/submissions/v21_increment_%s.csv'  # --increment, tagged by backbone


def base_model(name):
    """Which learner a blend member is; the robust core is `hbt` on fewer columns."""
    return 'hbt' if name in (ROBUST, NOPRESS) else name
RNGB_SHRINK = 0.25           # wide-diurnal-range correction, deliberately heavily shrunk
RNGB_Q = 5.0 / 6.0           # band cut: the training 5/6 quantile of T_rng48
SUPPORT_BAR = 0.885          # section 19.2's audit bar, applied to the whole test set.
                             # Set to select exactly the eleven columns validated at blend
                             # level in progress.md section 81 -- `T_over_dailymax` sits at
                             # 0.890 support and was NOT tested, so it stays in.

# Defaults reproduce the best leaderboard submission (3.04904). The two flags below were
# tried afterwards and the combination scored 3.28564 -- worse. See the guard in
# `apply_calibration` and the post-mortem in progress.md.

FAST = ['air_temperature', 'co2', 'pressure']
SOIL = ['soil_ec_line1', 'soil_humidity_line1', 'soil_temp_line1',
        'soil_ec_line2', 'soil_humidity_line2', 'soil_temp_line2',
        'soil_ec_line3', 'soil_humidity_line3', 'soil_temp_line3']
DAILY = ['standard_day_degree', 'daily_mean_temperature', 'daily_max_above_Tbase',
         'daily_max', 'daily_max_reduction', 'ontario_units']
CUMUL = ['gdd', 'water_volume_line1', 'water_volume_line2', 'water_volume_line3']
TMIN_WINS = (18, 48, 96)
CO2_WINS = (18, 48)


# --------------------------------------------------------------------- physics
def es(t):
    """Saturation vapour pressure in hPa (Magnus/Bolton)."""
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


# --------------------------------------------------------------------- loading
def load_grid():
    tr = pd.read_csv(DATA + 'train.csv', parse_dates=['datetime'])
    te = pd.read_csv(DATA + 'test.csv', parse_dates=['datetime'])
    tr['is_test'] = 0
    te['is_test'] = 1
    te[TARGET] = np.nan
    al = pd.concat([tr, te], ignore_index=True).sort_values('datetime')
    g = al.set_index('datetime').asfreq('30min')
    g['is_test'] = g['is_test'].fillna(-1)
    return g


# -------------------------------------------------------------------- cleaning
def hampel(s, w=7, k=6.0, scale_win=289):
    """Centered Hampel filter with the scale taken from a long rolling IQR, so a locally
    quiet stretch does not get every wiggle flagged. Deliberately loose: it catches the
    physically impossible excursions and leaves genuine fast greenhouse transitions
    (vents opening, cloud crossing the sun) intact."""
    med = s.rolling(w, center=True, min_periods=3).median()
    dev = (s - med).abs()
    scale = dev.rolling(scale_win, center=True, min_periods=48).quantile(0.75) * 2.5
    return s.mask(dev > (k * scale).clip(lower=1e-9))


def clean_exog(g):
    c = g.copy()
    for col in FAST + SOIL + DAILY:
        c[col] = hampel(c[col]).interpolate('time', limit_direction='both')
    for col in CUMUL:
        cl = hampel(c[col], w=9).interpolate('time', limit_direction='both').cummax()
        c[col] = cl
        c[col + '_rate'] = cl.diff().clip(lower=0).rolling(48, min_periods=1).sum()
    return c


# -------------------------------------------------------------------- features
def build_features(c):
    """Base block. Centered windows are used throughout; for test rows this is exactly
    the concurrent-sensor information the brief provides."""
    idx = c.index
    f = {}
    T = c['air_temperature']
    f['T'] = T
    f['esT'] = es(T)
    f['log_esT'] = np.log(es(T))
    tod = idx.hour + idx.minute / 60.0
    for h in (1, 2, 3):
        f[f'sin{h}'] = np.sin(2 * np.pi * h * tod / 24)
        f[f'cos{h}'] = np.cos(2 * np.pi * h * tod / 24)
    f['tod'] = tod
    for col in FAST + SOIL:
        s = c[col]
        f[col] = s
        for w, nm in ((3, '1h'), (13, '6h'), (49, '24h')):
            m = s.rolling(w, center=True, min_periods=2).mean()
            f[f'{col}_c{nm}'] = m
            f[f'{col}_a{nm}'] = s - m
        f[f'{col}_sd6h'] = s.rolling(13, center=True, min_periods=3).std()
    for col in FAST:
        s = c[col]
        for l in (-4, -2, -1, 1, 2, 4):
            f[f'{col}_s{l}'] = s.shift(l)
        f[f'{col}_slope'] = (s.shift(-2) - s.shift(2)) / 4.0
    for col in DAILY:
        f[col] = c[col]
    for col in CUMUL:
        f[col + '_rate'] = c[col + '_rate']
    f['T_minus_soilT1'] = c['air_temperature'] - c['soil_temp_line1']
    f['T_minus_soilT2'] = c['air_temperature'] - c['soil_temp_line2']
    f['T_minus_soilT3'] = c['air_temperature'] - c['soil_temp_line3']
    f['T_minus_dailymean'] = c['air_temperature'] - c['daily_mean_temperature']
    f['T_over_dailymax'] = c['air_temperature'] / c['daily_max'].replace(0, np.nan)
    f['co2_x_T'] = c['co2'] * c['air_temperature']
    f['esT_ratio_daily'] = es(T) / es(c['daily_mean_temperature'])
    return pd.DataFrame(f, index=idx)


def low_support(F, is_tr, is_te, bar=SUPPORT_BAR):
    """Columns whose test values sit outside the training 1-99% band too often.

    This is section 19.2's extrapolation audit turned into a filter. It selects on
    COVERAGE, which is a property of the feature values alone -- no target is involved, so
    it is not section 38's prune-by-CV-score trap. Section 7 dropped the soil block on
    exactly this criterion and it was one of the largest wins in the log.

    At bar=0.885 it selects eleven columns: the ten near-duplicate pressure level and lag
    columns (mean pairwise correlation 0.987, combined ridge contribution swinging 2.7 %RH
    for a variable with |r| < 0.25 against the target), plus `esT_ratio_daily`. On the
    private 70% of the test window those ten pressure columns fall to 0.69-0.82 support
    against 0.91-0.96 on the public 30%.

    Read progress.md section 81 before turning this on: the member-level evidence is
    overwhelming (ridge -0.69, enet -0.51, ridge_e -1.00, all 18/18 folds) and the
    BLEND-level evidence is not (-0.070, 11/18, 95% CI crossing zero, family Q flipping
    sign). It does not clear this log's adoption bar on cross-validation. The argument for
    it is section 77 -- cross-validation cannot see the axis this is meant to protect.
    """
    tr, te = F[is_tr], F[is_te]
    lo, hi = tr.quantile(0.01), tr.quantile(0.99)
    cov = (((te >= lo) & (te <= hi)) | te.isna()).mean()
    return sorted(cov[cov < bar].index)


def no_pressure(F):
    """Columns for the section-115 member: everything except the ten pressure level and
    lag columns. Selection is by column name alone -- no target, no coverage statistic.

    Section 80 measured this block as ten near-identical copies of one weak predictor (mean
    pairwise |r| 0.987, |r| against the target under 0.25) whose combined ridge contribution
    swings 2.71 %RH, and section 78 measured its support falling to 0.69-0.82 on the private
    slice against 0.91-0.96 on the public one. The bounded `pressure_a24h` anomaly and
    `pressure_sd6h`/`pressure_slope` stay, so the pressure INFORMATION survives; only the
    redundant levels go.

    Section 80 tried this on every member at once and the blend ate the gain, because the
    uniform floor had already decided how much weight the linear members got. As a single
    additional member under free NNLS it is worth -0.028 nested, 16/18 folds, negative in P,
    Q and R -- and NNLS then gives it 0.490 and drops plain `hbt` to zero. See section 115.
    """
    return [c for c in F.columns
            if not (c == 'pressure' or c.startswith('pressure_c')
                    or re.fullmatch(r'pressure_s-?\d+', c))]


def stable_core(F, is_tr, is_te, bar=0.916):
    """Columns for the robust-core member: everything that keeps its training support in
    the test window, minus the two blocks section 78 identified as the ones that shift.

    Selection uses coverage and column names only, so no target is involved -- the same
    basis as section 7's soil drop and section 19.2's audit. The two named blocks are the
    ten near-duplicate pressure level and lag columns (private-slice support 0.69-0.82) and
    the diurnal-range block, whose train-vs-private adversarial AUC jumps +0.29 to +0.34
    from its train-vs-public value.

    The member trained on these columns is worth -0.013 nested as a seventh member, 14/18
    folds, negative in P, Q and R -- and it earns that on time-of-day band weight alone,
    because NNLS gives it zero global weight. See progress.md section 108.
    """
    tr, te = F[is_tr], F[is_te]
    lo, hi = tr.quantile(0.01), tr.quantile(0.99)
    cov = (((te >= lo) & (te <= hi)) | te.isna()).mean()
    def is_pressure_level(n):
        return n == 'pressure' or n.startswith('pressure_c') or re.fullmatch(r'pressure_s-?\d+', n)
    def is_shifted_range(n):
        return n.startswith('T_rng') or 'air_temperature_qrng' in n or n == 'esT_ratio_daily'
    return [c for c in F.columns
            if float(cov.get(c, 0.0)) >= bar
            and not is_pressure_level(c) and not is_shifted_range(c)]


def drop_soil(F):
    """The soil probes stop fluctuating in the test window because irrigation halts, so
    only 7-12% of their rolling-statistic values have any training support. Dropped."""
    return [c for c in F.columns if not c.startswith('soil_') and not c.endswith('_rate')]


def tmin_block(c, wins=TMIN_WINS):
    """Daily-minimum temperature as a dewpoint proxy: moist air cools overnight until it
    reaches its dewpoint and stalls there, latent heat halting further cooling. So
    es(Tmin)/es(T) is a parameter-free RH estimate, and the diurnal range separates clear
    dry days (wide) from humid cloudy ones (narrow)."""
    T = c['air_temperature']
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        mn = T.rolling(w, center=True, min_periods=6).min()
        mx = T.rolling(w, center=True, min_periods=6).max()
        d[f'T_min{hrs}'] = mn
        d[f'T_max{hrs}'] = mx
        d[f'T_minus_min{hrs}'] = T - mn
        d[f'T_rng{hrs}'] = mx - mn
        d[f'rh_tmin{hrs}'] = 100 * es(mn.values) / es(T.values)
    return pd.DataFrame(d, index=c.index)


def tend_block(c):
    """Synoptic tendency: falling pressure precedes moist advection, and the co2 trend
    tracks the ventilation regime."""
    p = c['pressure']
    pm = p.rolling(49, center=True, min_periods=8).mean()
    return pd.DataFrame({
        'p_tend24h': pm.diff(48),
        'p_tend48h': pm.diff(96),
        'p_sd24h': p.rolling(49, center=True, min_periods=8).std(),
        'co2_tend24h': c['co2'].rolling(49, center=True, min_periods=8).mean().diff(48),
    }, index=c.index)


def ordstat_block(c, col, wins):
    """Windowed min/max/range. Applied to co2 only: the same block on pressure lost
    clearly, which is the control showing the gain is dewpoint physics rather than
    'more rolling statistics'."""
    s = c[col]
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        mn = s.rolling(w, center=True, min_periods=6).min()
        mx = s.rolling(w, center=True, min_periods=6).max()
        d[f'{col}_min{hrs}'] = mn
        d[f'{col}_max{hrs}'] = mx
        d[f'{col}_rng{hrs}'] = mx - mn
        d[f'{col}_minus_min{hrs}'] = s - mn
    return pd.DataFrame(d, index=c.index)


def qblock(c, wins, q=0.05, col='air_temperature', rh=True):
    """Windowed 5th/95th percentiles alongside the hard extremes. A minimum reports the
    single coldest sample; a 5th percentile reports where the cold bulk sits. On a clear
    night the two nearly coincide, under broken cloud they separate, and that gap is
    itself a moisture signal. They are complements, not substitutes."""
    s = c[col]
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = s.rolling(w, center=True, min_periods=6).quantile(q)
        hi = s.rolling(w, center=True, min_periods=6).quantile(1 - q)
        d[f'{col}_q{hrs}'] = lo
        d[f'{col}_qhi{hrs}'] = hi
        d[f'{col}_qrng{hrs}'] = hi - lo
        d[f'{col}_minus_q{hrs}'] = s - lo
        if rh:
            d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(c['air_temperature'].values)
    return pd.DataFrame(d, index=c.index)


def make_features(grid):
    c = clean_exog(grid)
    base = build_features(c)
    base = base[drop_soil(base)]
    F = pd.concat([base, tmin_block(c), tend_block(c),
                   ordstat_block(c, 'co2', CO2_WINS),
                   qblock(c, TMIN_WINS), qblock(c, CO2_WINS, col='co2', rh=False)], axis=1)
    return F.replace([np.inf, -np.inf], np.nan)


# ------------------------------------------------------- increment reconciliation
# Session 21. The stack predicts a LEVEL: RH at time t. A second family of models
# predicts a CHANGE: RH[t] - RH[t-h]. Those are different tasks, and a slowly drifting
# weather offset that the level model carries into every hour of a day cancels out of the
# difference. Section 146 measured 36.31% of the error mass sitting in exactly that
# per-day offset, and the lag-one error autocorrelation at 0.9330, so the level model's
# mistakes are smooth in time while its errors in SHAPE are what is left.
#
# Both endpoints of every training difference are train rows, and inference reads only
# exogenous columns, so no RH value from the validation or test window is ever an input.
# There is no recursive feeding of the model's own output either: the two increment models
# are fitted once and the whole path is recovered in a single linear solve.
#
# The two horizons and their weights were frozen after the session-20 screen (progress.md
# section 147) and are NOT tuned here. The 6-hour member was screened and rejected: it
# diluted the short-scale signal, +0.06254 mean and only 5/12 folds.
INC_COLS = ['T', 'co2', 'pressure', 'rh_tmin48', 'T_rng48', 'sin1', 'cos1']
# Session 24. At constant vapour pressure RH[t] = RH[t-h] * es(T[t-h])/es(T[t]) exactly, and
# that ratio is most of what an RH change IS: corr(dRH, dT)^2 is 0.643 at 30 minutes and 0.817
# at 2 hours. Without these columns the model rediscovers the ratio through splits on T and
# T_prev, which is capacity spent on a closed-form identity. `es_ratio` hands it over, and
# `dRH_const_e` multiplies it by section 19's parameter-free dewpoint-proxy level estimate to
# give the change thermodynamics alone would produce. Temperature only, so target-blind.
INC_PHYS_COLS = INC_COLS + ['esT', 'log_esT']
INC_SPEC = ((1, 4.0), (4, 1.0))   # (half-hour steps, reconciliation weight): 30 min, 2 h
INC_SEED = 20260905
INC_SEEDS = 5     # seeds averaged per increment model; see progress.md section 152
# Session 22. `D` sums to zero on every row, so the increment terms cannot move the level --
# they only fix within-day shape. Section 146 put 36.31% of MSE in the per-day mean, which is
# therefore out of their reach. A centered moving-average operator does NOT have zero row
# sums, so a model of the SMOOTHED humidity can move it. That is the point and the danger:
# sections 6, 35 and 46 each failed at correcting the level, and the session-22 screen shows
# this term wrecking a holdout at weight 1.0 while helping at 0.25. It ships heavily shrunk
# and behind its own flag. See progress.md section 158.
SMOOTH_SPEC = ((49, 0.25),)   # (window in half-hour points, weight): 24 h, only --smooth-level
# Session 23. Relative humidity moves whenever temperature moves, because es(T) sits in its
# denominator, and that part of the motion is thermodynamics rather than weather: on the
# training grid corr(dRH, dT) is -0.802 at 30 min and -0.904 at 2 h, so 82% of the variance of
# the two-hour RH change is temperature. Vapour pressure e = RH*es(T)/100 divides that out and
# moves only by advection, condensation and ventilation -- corr(de, dT) is +0.461 and +0.580.
# With w = es(T)/mean_train(es(T)), the h-step change in RH*w is (D diag(w)) z, still linear in
# z, so it is one more quadratic term in the same solve. Half the increment weights, because
# at short horizons w barely moves and the constraint is nearly collinear with the RH one.
VP_SPEC = ((1, 2.0), (4, 0.5))   # (half-hour steps, weight), only with --vapour-increment
# Session 25. Every increment learner under-predicts the AMPLITUDE of the change: measured
# against the truth on the holdouts, LightGBM's 30-minute predictions have 0.87-0.88 of the
# actual spread. Squared error rewards that shrinkage, which is why an averaged ensemble scored
# the best increment RMSE of any candidate and the worst reconciled result -- averaging shrinks
# harder still. But `min ||z-p||^2 + lam ||Dz - d||^2` treats d as an unbiased observation of
# Dz, not as an MSE-optimal point estimate, so a shrunk d tells the solver the humidity moves
# less than it does and flattens the path. The factor is estimated out of fold on TRAINING rows
# only, and applied at half strength -- the same 0.5 this log uses for every other correction it
# does not fully trust. See progress.md sections 174-176.
INC_DESHRINK = 0.5           # pull toward the measured dispersion factor, only --inc-deshrink
DESHRINK_CLIP = (1.0, 1.5)   # a factor below 1 would be shrinking further; refuse it
DESHRINK_FOLDS = 3           # contiguous time folds inside train for the out-of-fold estimate
INC_KW = dict(objective='regression', n_estimators=500, learning_rate=0.03,
              num_leaves=15, min_child_samples=30, reg_lambda=5.0,
              colsample_bytree=0.8, verbose=-1)


def inc_design(F, h, cols=INC_COLS, physics=False):
    """Features for the h-step increment model: everything the level models see at t, plus
    the same short list of drivers at t-h and their change over the interval. The change
    columns are what let the model say "temperature fell 3 C in the last two hours" without
    having to infer it from two absolute levels.

    With `physics`, two analytic thermodynamic terms are appended -- see INC_PHYS_COLS."""
    c = [x for x in cols if x in F.columns]
    parts = [F, F[c].shift(h).add_suffix('_prev'), F[c].diff(h).add_suffix('_change')]
    if physics:
        ratio = F['esT'].shift(h) / F['esT']
        parts.append(pd.DataFrame(
            {'es_ratio': ratio,
             'dRH_const_e': F['rh_tmin48'].shift(h) * (ratio - 1.0)}, index=F.index))
    return pd.concat(parts, axis=1)


# Session 28. Sections 174, 184 and 185 swapped the increment LEARNER five times over --
# HistGB, CatBoost, a ridge, extra-trees, a physical spline and several averages of them -- and
# every one of them read the same two points on the trajectory: the drivers at t, the drivers at
# t-h, and their difference. Section 195 finally varied the REPRESENTATION instead, with causal
# lags out to 24 hours, but swapped the learner to a Ridge in the same step and the Ridge lost;
# the log then came close to writing off multi-lag information on that evidence. Section 202
# holds the learner, the hyperparameters, the seeds, the horizons, the weights and the
# de-shrink estimator all fixed and adds only these columns. It is worth -0.0250 pooled with
# the alignment term negative on all three blocks and the path standard deviation essentially
# unchanged -- better information rather than more amplitude, which is the distinction section 9
# says to care about.
INC_LAGS = (0, 1, 2, 4, 8, 16, 24, 48)   # half-hour steps: 30 min to 24 h back
INC_LAG_COLS = ('T', 'co2', 'pressure', 'rh_tmin48')


def inc_lag_design(F, h, cols=INC_COLS, physics=False):
    """`inc_design` plus the causal lag trajectory, de-duplicated by name AND by value.

    `inc_design` already carries `F` whole, so `sin1`/`cos1`/`sin2`/`cos2` and every `*_lag0`
    column is a duplicate by construction, and at h=1 the `_prev` block IS the lag-1 block.
    Feeding LightGBM two identical columns splits their importance and changes tie-breaking for
    no information, so they are dropped.

    Column ORDER is part of the contract, not cosmetics: LightGBM breaks equal-gain splits by
    feature index, so a reordering is a different model with the same inputs. Duplicates are
    tested against the matrix AS IT GROWS, which is what produced the scored artifact.

    No target and no lag of the target appears here. The humidity that enters is `rh_tmin48`,
    the parameter-free dewpoint proxy built from temperature alone, exactly as the increment
    models already use it."""
    assert (pd.DatetimeIndex(F.index).to_series().diff().dropna()
            == pd.Timedelta(minutes=30)).all(), \
        'inc_lag_design needs a complete 30-minute grid; shift(k) would not mean k half-hours'
    X = inc_design(F, h, cols, physics)
    lag = {}
    for k in INC_LAGS:
        for c in INC_LAG_COLS:
            if c in F.columns:
                lag['%s_lag%d' % (c, k)] = F[c].shift(k)
    dT = F['T'] - F['T'].shift(4)
    lag['warm2h'] = dT.clip(lower=0)
    lag['cool2h'] = (-dT).clip(lower=0)
    for c in ('sin1', 'cos1', 'sin2', 'cos2'):
        if c in F.columns:
            lag[c] = F[c]
    for name, col in lag.items():
        if name in X.columns or any(col.equals(X[k]) for k in X.columns):
            continue
        X[name] = col
    return X


def increment_design(F, h, cols=INC_COLS, physics=False, lags=False):
    """The one place that decides which increment design is in force."""
    return (inc_lag_design if lags else inc_design)(F, h, cols, physics)


def smooth_operator(idx, w):
    """Centered moving-average operator over a block, plus the timestamps it scores.

    One row per position whose complete w-point window is present in `idx`, so a block edge or
    a hole produces no row rather than an average over a shorter, differently-biased window.
    Row sums are 1, not 0 -- which is exactly why this term can move the level where
    `diff_operator` cannot."""
    idx = pd.DatetimeIndex(idx)
    pos = pd.Series(np.arange(len(idx)), index=idx)
    half = w // 2
    cols, keep = [], np.ones(len(idx), bool)
    for k in range(-half, half + 1):
        p = pos.reindex(idx + pd.Timedelta(minutes=30 * k)).to_numpy()
        keep &= ~np.isnan(p)
        cols.append(p)
    i = np.flatnonzero(keep)
    if len(i) == 0:
        return None, idx[:0]
    rows = np.repeat(np.arange(len(i)), w)
    col = np.column_stack([c[i] for c in cols]).ravel().astype(int)
    S = csc_matrix((np.full(len(rows), 1.0 / w), (rows, col)), shape=(len(i), len(idx)))
    return S, idx[i]


def vp_weight(F, train_mask):
    """es(T) normalised by its training mean. Temperature only, so it is target-blind, and
    the same constant whatever the reconciliation is asked to do."""
    e = pd.Series(es(F['T'].to_numpy()), index=F.index)
    return e / float(e[train_mask.reindex(F.index, fill_value=False)].mean())


def smooth_design(F, w, cols=INC_COLS):
    """Features for the smoothed-humidity model: the level models' columns plus centered
    rolling means of the same short driver list, matched to the target's window."""
    c = [x for x in cols if x in F.columns]
    m = F[c].rolling(w, center=True, min_periods=w).mean().add_suffix('_sm%d' % w)
    return pd.concat([F, m], axis=1)


def diff_operator(idx, h):
    """Sparse difference operator over a block, plus the timestamps it scores.

    One row per pair of positions whose timestamps are exactly h half-hours apart, so a
    hole in the index simply produces no row instead of silently differencing across it.
    Row k holds -1 at the earlier position and +1 at the later one, so `(D @ z)[k]` is the
    h-step change ending at `stamps[k]`."""
    idx = pd.DatetimeIndex(idx)
    pos = pd.Series(np.arange(len(idx)), index=idx)
    later = idx + pd.Timedelta(minutes=30 * h)
    hit = later.isin(idx)
    i = np.flatnonzero(hit)
    if len(i) == 0:
        return None, idx[:0]
    j = pos.reindex(later[hit]).to_numpy()
    rows = np.repeat(np.arange(len(i)), 2)
    cols = np.empty(2 * len(i), int)
    cols[0::2], cols[1::2] = i, j
    vals = np.tile([-1.0, 1.0], len(i))
    D = csc_matrix((vals, (rows, cols)), shape=(len(i), len(idx)))
    return D, idx[j]


def fit_increments(F, y, train_mask, seeds=(INC_SEED,), smooth=False, vapour=False,
                   physics=False, deshrink=False, lags=False):
    """One LightGBM per frozen horizon, keyed by that horizon. `train_mask` selects rows
    usable as the LATER endpoint; the shift check below additionally requires the earlier
    endpoint to be a labelled training row, so a difference can never straddle the forecast
    origin. With `smooth`, one more model per SMOOTH_SPEC window predicts the centered mean
    of the target, and every label inside that window must also be a training row."""
    out = {'physics': physics, 'cols': INC_PHYS_COLS if physics else INC_COLS, 'lags': lags}
    for h, _ in INC_SPEC:
        X = increment_design(F, h, out['cols'], physics, lags)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = train_mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        out[h] = [lgb.LGBMRegressor(random_state=s, **INC_KW).fit(X.loc[m], tgt.loc[m])
                  for s in seeds]
        if deshrink:
            # Out-of-fold on the training rows, one seed: the factor is a single scalar and
            # does not need the seed averaging the predictions themselves get.
            rows = X.index[m]
            oof = pd.Series(np.nan, index=rows)
            for cut in np.array_split(np.arange(len(rows)), DESHRINK_FOLDS):
                va, trn = rows[cut], rows.difference(rows[cut])
                oof.loc[va] = lgb.LGBMRegressor(random_state=INC_SEED, **INC_KW).fit(
                    X.loc[trn], tgt.loc[trn]).predict(X.loc[va])
            out[('f', h)] = float(np.clip(tgt.loc[rows].std() / oof.std(), *DESHRINK_CLIP))
    if smooth:
        for w, _ in SMOOTH_SPEC:
            X = smooth_design(F, w)
            tgt = y.reindex(X.index).rolling(w, center=True, min_periods=w).mean()
            full = (train_mask.reindex(X.index, fill_value=False).astype(float)
                    .rolling(w, center=True, min_periods=w).sum() == w)
            m = full.fillna(False) & tgt.notna()
            out[('s', w)] = [lgb.LGBMRegressor(random_state=s, **INC_KW).fit(X.loc[m], tgt.loc[m])
                             for s in seeds]
    if vapour:
        out['vp_weight'] = vp_weight(F, train_mask)
        q = y * out['vp_weight'].reindex(y.index)
        for h, _ in VP_SPEC:
            X = inc_design(F, h)
            tgt = (q - q.shift(h)).reindex(X.index)
            m = train_mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            out[('v', h)] = [lgb.LGBMRegressor(random_state=s, **INC_KW).fit(X.loc[m], tgt.loc[m])
                             for s in seeds]
    return out


def reconcile(p, idx, F, inc, lam_scale=1.0):
    """Solve  min_z ||z-p||^2 + sum_h lam_h ||D_h z - d_h||^2 + sum_w mu_w ||S_w z - s_w||^2.

    p is the stack's level prediction, d_h the fitted h-step change, s_w the fitted centered
    mean. The solution is the one RH path that stays close to the level prediction while
    following the learned dynamics; it is a single sparse symmetric positive-definite solve,
    no iteration and no free parameter beyond the frozen weights. `lam_scale` multiplies the
    increment weights only -- pulling z harder toward the learned dynamics and away from the
    level prediction. The smoothing terms are present only if `fit_increments` was asked for
    them."""
    p = np.asarray(p, float)
    A = identity(len(p), format='csc')
    rhs = p.copy()
    dcols, dphys = inc.get('cols', INC_COLS), inc.get('physics', False)
    dlags = inc.get('lags', False)
    # Each term is (operator, scored stamps, design, models, weight, dispersion key).
    terms = [(diff_operator(idx, h), increment_design(F, h, dcols, dphys, dlags), inc.get(h),
              lam * lam_scale, ('f', h)) for h, lam in INC_SPEC]
    terms += [(smooth_operator(idx, w), smooth_design(F, w), inc.get(('s', w)), mu, None)
              for w, mu in SMOOTH_SPEC if ('s', w) in inc]
    if any(('v', h) in inc for h, _ in VP_SPEC):
        wv = inc['vp_weight'].reindex(idx).to_numpy()
        for h, nu in VP_SPEC:
            D, stamps = diff_operator(idx, h)
            M = None if D is None else (D @ diags(wv)).tocsc()
            terms.append(((M, stamps), inc_design(F, h), inc.get(('v', h)), nu, None))
    for (M, stamps), X, models, lam, key in terms:
        if M is None or models is None:
            continue
        t = np.mean([m.predict(X.loc[stamps]) for m in models], axis=0)
        if key is not None and key in inc:
            # Restore the amplitude the learner shrank away, at half strength.
            f = 1.0 + INC_DESHRINK * (inc[key] - 1.0)
            t = t.mean() + (t - t.mean()) * f
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    z = spsolve(A, rhs)
    assert np.max(np.abs(A @ z - rhs)) < 1e-7, 'reconciliation solve did not converge'
    assert np.isfinite(z).all()
    return np.clip(z, 5, 100)


# ---------------------------------------------------------------------- models
LGB_KW = dict(objective='huber', alpha=2.0, n_estimators=900, learning_rate=0.03,
              num_leaves=15, min_child_samples=25, subsample=0.8, subsample_freq=1,
              colsample_bytree=0.7, reg_lambda=3.0, verbose=-1)
MODELS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
# Plain-L2 LightGBM. The metric is RMSE and every tree member in MODELS uses a huber loss
# (hbt alpha=2, cat delta=4), both of which deliberately under-weight the large residuals
# that section 35's under-dispersion lives in. Adding an L2-matched tree is worth -0.013
# nested, negative in all three fold families, 15/18 folds, 95% CI [-0.0225, -0.0036]. Small,
# because its residuals correlate 0.950 with `hbt` -- it is nearly a duplicate and NNLS puts
# it on the 0.042 floor. See progress.md section 98.
MODELS_L2 = MODELS + ['l2']


def _pipe(est):
    return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), est)


def predict(name, Xtr, ytr, Xva, esv, etr, seeds):
    if name == 'l2':
        kw = dict(LGB_KW); kw.pop('alpha'); kw['objective'] = 'regression'
        return np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    if name == 'hbt':
        return np.mean([lgb.LGBMRegressor(random_state=s, **LGB_KW).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    if name == 'cat':
        return np.mean([cb.CatBoostRegressor(
            iterations=1200, learning_rate=0.035, depth=6, l2_leaf_reg=6.0,
            loss_function='Huber:delta=4', random_seed=s, verbose=0,
            allow_writing_files=False).fit(Xtr, ytr).predict(Xva) for s in seeds], 0)
    if name == 'ridge':
        return _pipe(Ridge(alpha=20.0)).fit(Xtr, ytr).predict(Xva)
    if name == 'enet':
        return _pipe(ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=8000)).fit(Xtr, ytr).predict(Xva)
    if name == 'ridge_e':
        # same ridge, fitted in vapour-pressure space then converted back. It loses on its
        # own but is the one genuinely decorrelated member of the blend.
        m = _pipe(Ridge(alpha=20.0)).fit(Xtr, etr)
        return 100.0 * m.predict(Xva) / esv
    raise ValueError(name)


def tod_blend_weights(O, w_global, nbins=TOD_BINS, shrink=TOD_SHRINK, models=None,
                      blend_shrink=BLEND_SHRINK):
    """One blend weight vector per time-of-day band instead of one for the whole day.

    The members are not equally good around the clock. Fitted per band, `ridge_e` -- the
    ridge fitted in vapour-pressure space -- goes from its 0.05 floor overnight to 0.17
    through the middle of the day, which is where es(T) is largest and a vapour-pressure
    parameterisation should carry the most; `cat` rises in the evening instead. A single
    global vector averages those regimes together.

    Worth -0.080 CV nested on the shipped expanding-window protocol (95% CI [-0.120,
    -0.042], 11/15 folds) and -0.067 under leave-one-fold-out (CI [-0.091, -0.044], 17/18
    folds), negative in all three fold families under both schemes. The control that
    matters: conditioning on a RANDOM variable with the same number of free parameters
    buys only -0.007, so what this measures is signal rather than the added capacity.

    Returns (edges, {band: weight vector}). Edges are quantiles of the training rows' hour
    of day, so they are data-derived rather than hand-placed.
    """
    models = MODELS if models is None else models
    edges = np.quantile(O.tod.values, np.linspace(0, 1, nbins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    b = np.digitize(O.tod.values, edges[1:-1])
    W = {}
    for i in range(nbins):
        d = O[b == i]
        if len(d) < 150:
            W[i] = w_global
            continue
        wi, _ = nnls(d[models].values, d.y.values)
        wi = wi / wi.sum() if wi.sum() > 0 else np.ones(len(models)) / len(models)
        wi = (1 - blend_shrink) * wi + blend_shrink * np.ones(len(models)) / len(models)
        W[i] = (1 - shrink) * wi + shrink * w_global
    return edges, W


def tod_bias(O, edges, shrink=TODB_SHRINK):
    """Per-time-of-day-band bias, measured on out-of-fold predictions, with the GLOBAL
    level removed.

    Non-negative least squares cannot produce an intercept, so re-weighting the members
    per band (--tod-blend) leaves a per-band offset untouched. It is large and it is the
    same in every fold: the blend under-predicts the ~04:00 humidity peak and
    over-predicts the ~15:00 trough, i.e. the huber loss and the tree averaging compress
    the diurnal amplitude. Across 18 nested folds the sign is the same 18/18 times in all
    three bands.

    The global level is deliberately subtracted out. Correcting the overall bias is what
    sections 6, 35 and 46 tried and rejected; on the nested scan here it buys -0.010,
    which is inside the -0.009 random-conditioner control. The diurnal *shape* is a
    different quantity, it buys -0.070 at shrink 0.5 (17/18 folds, bootstrap 95% CI
    [-0.091, -0.050]), and it is guarded by the same band-occupancy check as --tod-blend,
    which hour of day passes with a 0.008 shift. See progress.md section 67.
    """
    b = np.digitize(O.tod.values, edges[1:-1])
    r = (O.blend - O.y).values
    rel = np.array([r[b == i].mean() for i in range(len(edges) - 1)]) - r.mean()
    return shrink * rel


def harm_bias(O, shrink=HARM_SHRINK):
    """The same diurnal offset as `tod_bias`, but as one sinusoid in hour of day instead of
    three step bands -- the same two free parameters, fitted to the shape rather than to a
    piecewise average of it.

    The true bias is continuous in hour, so terciles put their edges at 07:50 and 15:40 and
    average the ~04:00 peak and ~15:00 trough away inside 8-hour blocks. A single harmonic
    lands on them. Nested over the same 18 folds it is worth -0.095 against -0.070 for the
    bands, 18/18 folds against 17/18, and a random conditioner with two free parameters buys
    +0.001.

    It also transfers better. The fitted band offsets move with the regime (band 0 correlates
    +0.75 with fold mean temperature, band 2 correlates -0.80), whereas this correction's
    amplitude sits in 1.34-2.11 %RH across all 18 folds with corr(fold temperature,
    amplitude) = +0.05, and the cosine term is negative 18/18. The shape it encodes is the
    same every time: raise the overnight peak, lower the midday trough, by about 0.8 %RH
    after shrinkage. See progress.md section 73.
    """
    t = 2 * np.pi * O.tod.values / 24.0
    X = np.column_stack([np.sin(t), np.cos(t)])
    r = (O.blend - O.y).values
    b = np.linalg.lstsq(np.c_[np.ones(len(X)), X], r, rcond=None)[0][1:]
    return shrink * b


def apply_harm_bias(pred, tod, b):
    t = 2 * np.pi * np.asarray(tod) / 24.0
    return pred - (np.sin(t) * b[0] + np.cos(t) * b[1])


def member_bias(O, models, members=DEBIAS_MEMBERS, shrink=CATDB_SHRINK):
    """Each named member's mean signed out-of-fold error, shrunk, as one scalar per member.

    `O` holds only rows a fold predicted from its own past, so this is a forward measurement of
    the same quantity the test window will exhibit -- not an in-sample residual, which is about
    zero for every member here.

    Section 46's dispersion slope and section 253's transport both failed because they applied a
    RATIO fitted in one regime to another. This is an offset on a single member, it is the
    smallest correction the blend can be given, and its direction control -- adding the offset
    instead of subtracting it -- loses by twice what subtracting it wins, on all six forward
    blocks. See progress.md section 310.
    """
    return {m: shrink * float((O[m] - O.y).mean()) for m in members if m in models}


def rng_bias(O, rng_tr, shrink=RNGB_SHRINK, q=RNGB_Q):
    """Correction for the widest-diurnal-range rows, where the blend over-predicts humidity.

    Wide 48-hour temperature range means clear dry air, and those are the driest hours of
    the training set. The blend over-predicts them by about 4 %RH -- it will not follow the
    target down to its extreme, which is section 35's under-dispersion showing up on a band a
    feature can actually identify.

    THIS ONE BREAKS A STANDING RULE AND DOES SO KNOWINGLY. Section 63 requires a conditioner
    to pass the occupancy guard, and T_rng48 fails it badly: the band holds 17% of training
    rows, 30% of the private test rows and *zero* public rows. Read progress.md section 87
    before using it. The short version:

      * the effect rests on 8 distinct training days in two separate weather episodes
        (Aug 6-9 and Aug 23-26), not on 267 independent rows
      * both episodes agree in sign and rough size; day-level bootstrap puts the bias at
        +4.11, 95% CI [+3.25, +5.24]
      * because the band contains no public rows, this cannot change the public score and
        cannot ever be verified before the deadline
      * the shrink is 0.25 rather than 0.5 precisely because the evidence is thin: at that
        level the correction pays off unless the true bias is under 0.5 %RH, and it costs
        about +0.04 if the effect is entirely imaginary

    Returns (cut, correction) where correction is already shrunk.
    """
    cut = float(np.quantile(rng_tr, q))
    r = (O.blend - O.y).values
    m = O.rng.values > cut
    if m.sum() < 100:
        return cut, 0.0
    return cut, shrink * (r[m].mean() - r.mean())


def apply_tod_bias(pred, tod, edges, rel):
    b = np.digitize(np.asarray(tod), edges[1:-1])
    return pred - rel[b]


def apply_tod_blend(P, tod, edges, W):
    """Blend a member-prediction matrix row by row, by each row's time-of-day band."""
    b = np.digitize(np.asarray(tod), edges[1:-1])
    out = np.empty(len(P))
    for i, wi in W.items():
        m = b == i
        if m.any():
            out[m] = P[m] @ wi
    return out


def increment_tag(l2_member, blend_shrink, drop_ridge, bag_nopress, robust_core,
                  smooth_level, vapour_increment, inc_physics, inc_deshrink, inc_lags,
                  inc_lambda_scale, tod_bias_on, harm_bias_on, hbt_trees=None,
                  cat_debias=False, cat_debias_shrink=CATDB_SHRINK,
                  calibrate=False, cal_shrink=CAL_SHRINK):
    """Filename tag for an --increment run: every flag that changes the predictions.

    Section 179's rule, generalised: a setting that moves the output belongs in the name, or two
    different models write one path and the second destroys the first. That near-miss was about
    `INC_DESHRINK`; session 43 found the same defect for the DIURNAL BIAS FORM, which was not in
    this list at all -- so `--tod-bias` and `--harm-bias` both produced `v16_noridge`, and running
    the first would have overwritten the file that scored 2.85383.

    `--harm-bias` alone stays untagged so every previously scored filename is unchanged; the three
    other bias configurations get their own names. `tests/test_v21_submission_naming.py` pins both
    halves of that.
    """
    tag = ('v20' if (l2_member and blend_shrink == 0.0) else
           'v16' if l2_member else 'v12')
    bias = {(True, False): '', (False, True): 'todbias',
            (True, True): 'todbias_harm', (False, False): 'nobias'}[
        (bool(harm_bias_on), bool(tod_bias_on))]
    for flag, name in ((drop_ridge, 'noridge'), (bag_nopress, 'nopress'),
                       (robust_core, 'robustcore'), (bias, bias),
                       (smooth_level, 'smooth'),
                       (vapour_increment, 'vp'), (inc_physics, 'phys'),
                       (inc_deshrink, 'dsh'), (inc_lags, 'lags'),
                       # Session 25 near-miss: a full-strength observation run silently
                       # overwrote the half-strength file, because the tag encoded the flag
                       # but not its strength. A constant moved for an experiment belongs in
                       # the file name. See progress.md section 179.
                       (inc_deshrink and INC_DESHRINK != 0.5, 'dsh%g' % INC_DESHRINK),
                       (inc_lambda_scale != 1.0, 'lam%g' % inc_lambda_scale),
                       (hbt_trees is not None, 'trees%s' % hbt_trees),
                       (cat_debias, 'catdb'),
                       (cat_debias and cat_debias_shrink != CATDB_SHRINK,
                        'catdb%g' % cat_debias_shrink),
                       # Session 48: `--calibrate` was in NO version of this tag, so
                       # `--increment --calibrate` wrote the same path as `--increment`. That is
                       # section 296's defect for the third time; see section 318.
                       (calibrate, 'cal%g' % cal_shrink)):
        if flag:
            tag += '_' + name
    return tag


def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def rolling_origins(idx, n=9, val_days=15, step_days=2, min_train_days=30):
    """Each fold trains on everything before a cut and validates the next 15 days, which
    is the shape of the real task."""
    d0, end, out = idx.min(), idx.max(), []
    for i in range(n):
        cut = end - pd.Timedelta(days=step_days * i)
        vs = cut - pd.Timedelta(days=val_days)
        if (vs - d0).days < min_train_days:
            break
        out.append((vs, cut))
    return out[::-1]


# ------------------------------------------------------------------------ main
def main(selftest=False, calibrate=False, strict_features=False, tod_blend=False,
         seeds=len(SEEDS_FIT), oof_seeds=len(SEEDS_OOF), tod_bias_on=False,
         harm_bias_on=False, drop_lowsupport=False, rng_bias_on=False,
         l2_member=False, robust_core=False, blend_shrink=BLEND_SHRINK,
         bag_nopress=False, drop_ridge=False, increment=False,
         inc_seeds=INC_SEEDS, smooth_level=False, inc_lambda_scale=1.0,
         vapour_increment=False, inc_physics=False, inc_deshrink=False, inc_lags=False,
         hbt_trees=None, cat_debias=False, cat_debias_shrink=CATDB_SHRINK,
         cal_shrink=CAL_SHRINK):
    if hbt_trees is not None:
        # Session 40's family J: the response is monotone over 900/1100/1400/1800/2400 on every
        # block and two seed blocks. Off by default, so every scored file still reproduces.
        LGB_KW['n_estimators'] = int(hbt_trees)
    models = MODELS_L2 if l2_member else MODELS
    if drop_ridge:
        # Section 53's rule is that a member is judged by the drop-one ablation and nothing
        # else. On the v18 stack `ridge` scores -0.0009 -- removing it HELPS -- and its
        # global NNLS weight has been exactly zero in all 18 folds since the uniform floor
        # came off. Section 80 explains why it should also be the first member to go on the
        # private slice: it is the one most damaged by the out-of-support pressure block,
        # improving -0.690 on 18/18 folds when that block is removed. Dropping it is worth
        # -0.037 on the OOD stress score (block-bootstrap CI [-0.063, -0.004]) and -0.083 on
        # the worst stress block. `enet` survives as the linear member; the two have residual
        # correlation 0.990 (s52), so nothing is lost. See progress.md section 122.
        models = [m for m in models if m != 'ridge']
    if robust_core:
        models = models + [ROBUST]
    if bag_nopress:
        models = models + [NOPRESS]
    if tod_bias_on and harm_bias_on:
        raise SystemExit('--tod-bias and --harm-bias are two forms of the same correction')
    # CatBoost carries 5.49 %RH of per-row seed noise here -- 15x LightGBM's 0.37 -- so the
    # shipped 5-seed average still leaves ~2.05 %RH of pure Monte-Carlo error in a member
    # holding 23% of the blend weight. Averaging more seeds removes it. It adds no free
    # parameter, so it cannot overfit; the only cost is fitting time. See progress.md s66.
    seeds_oof, seeds_fit = tuple(range(oof_seeds)), tuple(range(seeds))
    g = load_grid()
    IDX = g.index
    is_tr = (g.is_test == 0).values
    is_te = (g.is_test == 1).values
    y = g[TARGET]
    boundary = IDX[is_tr][-1]

    # --strict-features builds training-row features from a grid truncated at the
    # train/test boundary, so no training feature can see past it. It touches 96 of 2946
    # training rows (the ones within the widest centered window, 48 h, of the boundary).
    # Off by default because the submitted-and-scored file was built without it.
    F_test = make_features(g)
    if strict_features:
        F_train = make_features(g[IDX <= boundary])[F_test.columns]
    else:
        F_train = F_test
    F_test = F_test[F_train.columns]

    if drop_lowsupport:
        gone = low_support(F_test, is_tr, is_te)
        print(f'low-support filter (bar {SUPPORT_BAR}): dropping {len(gone)} columns')
        print('  ' + ', '.join(gone))
        keep = [c for c in F_train.columns if c not in set(gone)]
        F_train, F_test = F_train[keep], F_test[keep]

    cols = {m: list(F_train.columns) for m in models}
    if robust_core:
        cols[ROBUST] = stable_core(F_test, is_tr, is_te)
        print(f'robust-core member: {len(cols[ROBUST])} of {F_train.shape[1]} columns')
    if bag_nopress:
        cols[NOPRESS] = no_pressure(F_test)
        print(f'no-pressure member: {len(cols[NOPRESS])} of {F_train.shape[1]} columns')

    print(f'features {F_train.shape[1]}   train rows {int(is_tr.sum())}   test rows {int(is_te.sum())}')

    if selftest:
        g2 = g.copy()
        g2[TARGET] = np.nan
        Fb = make_features(g2)[F_train.columns]
        ok = all(np.array_equal(F_test[c].values, Fb[c].values, equal_nan=True)
                 for c in F_train.columns)
        print(f'SELFTEST target-blind features identical: {ok}')
        print(f'SELFTEST target among feature names     : {TARGET in list(F_train.columns)}')
        if not ok:
            raise SystemExit('feature construction depends on the target - aborting')
        if increment:
            # The increment design matrix is a pure function of F, so the check above
            # already covers it -- but it is cheap to prove rather than argue, because
            # this is the one block whose TARGET is a difference of labels.
            design = (lambda M, h: increment_design(
                M, h, INC_PHYS_COLS if inc_physics else INC_COLS, inc_physics, inc_lags))
            inc_ok = all(np.array_equal(design(F_test, h)[c].values,
                                        design(Fb, h)[c].values, equal_nan=True)
                         for h, _ in INC_SPEC
                         for c in design(F_test, h).columns)
            names = [c for h, _ in INC_SPEC for c in design(F_test, h).columns]
            print(f'SELFTEST increment design target-blind  : {inc_ok}')
            print(f'SELFTEST target among increment columns : {TARGET in names}')
            if not inc_ok or TARGET in names:
                raise SystemExit('increment design depends on the target - aborting')

    tr_idx = IDX[is_tr & y.notna().values]
    tr_mask = pd.Series(False, index=IDX)
    tr_mask.loc[tr_idx] = True
    ytr_all = y.loc[tr_idx]
    esT_train = pd.Series(es(F_train.loc[tr_idx, 'T'].values), index=tr_idx)
    E_train = ytr_all * esT_train / 100.0

    # ---- out-of-fold predictions: used for blend weights and the calibration slope ----
    folds = rolling_origins(tr_idx)
    oof = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr_idx[(tr_idx > vs) & (tr_idx <= ve)]
        t = tr_idx[tr_idx <= vs]
        if len(t) < 300 or len(v) < 50:
            continue
        d = pd.DataFrame({'fold': fi, 'dt': v, 'y': ytr_all.loc[v].values,
                          'tod': F_train.loc[v, 'tod'].values,
                          'rng': F_train.loc[v, 'T_rng48'].values})
        for m in models:
            c = cols[m]
            p = predict(base_model(m), F_train.loc[t, c], ytr_all.loc[t], F_train.loc[v, c],
                        esT_train.loc[v].values, E_train.loc[t], seeds_oof)
            d[m] = np.clip(p, 5, 100)
        oof.append(d)
        print(f'  fold {fi}: train {len(t)}  val {len(v)}')
    O = pd.concat(oof, ignore_index=True)

    # ---- member level de-bias: one scalar per member, measured forward on O ----
    debias = {}
    if cat_debias:
        debias = member_bias(O, models, shrink=cat_debias_shrink)
        print('\nmember de-bias (out-of-fold mean error, shrunk %.2f):' % cat_debias_shrink,
              {m: round(b, 4) for m, b in debias.items()})
        for m, b in debias.items():
            O[m] = np.clip(O[m].values - b, 5, 100)

    # ---- blend weights: non-negative least squares, shrunk toward equal weighting ----
    w, _ = nnls(O[models].values, O.y.values)
    w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
    w = (1 - blend_shrink) * w + blend_shrink * np.ones(len(models)) / len(models)
    O['blend'] = O[models].values @ w
    print('\nblend weights:', {m: round(float(x), 4) for m, x in zip(models, w)})

    tod_edges, tod_W = None, None
    if tod_blend:
        tod_edges, tod_W = tod_blend_weights(O, w, models=models,
                                             blend_shrink=blend_shrink)
        O['blend'] = apply_tod_blend(O[models].values, O.tod.values, tod_edges, tod_W)
        print('time-of-day blend, band edges %s h:' % np.round(tod_edges[1:-1], 2))
        for i, wi in tod_W.items():
            print('  band %d: %s' % (i, {m: round(float(x), 4)
                                         for m, x in zip(models, wi)}))

    rel_bias = None
    if tod_bias_on:
        if tod_edges is None:
            raise SystemExit('--tod-bias needs --tod-blend (it reuses the same bands)')
        rel_bias = tod_bias(O, tod_edges)
        print('time-of-day bias correction (band minus global, shrunk %.2f): %s'
              % (TODB_SHRINK, np.round(rel_bias, 3)))
        O['blend'] = np.clip(apply_tod_bias(O.blend.values, O.tod.values,
                                            tod_edges, rel_bias), 5, 100)

    harm_b = None
    if harm_bias_on:
        harm_b = harm_bias(O)
        amp, peak = float(np.hypot(*harm_b)), (np.degrees(np.arctan2(*harm_b)) % 360) / 15.0
        print('harmonic bias correction (shrunk %.2f): sin %+.3f  cos %+.3f'
              '   amplitude %.3f %%RH, peak %.1f h' % (HARM_SHRINK, harm_b[0], harm_b[1],
                                                       amp, peak))
        if not (0.5 <= amp / HARM_SHRINK <= 3.0):
            print('  WARNING: amplitude outside the 1.34-2.11 %RH band seen across 18 nested'
                  ' folds - the correction is not the one that was validated.')
        O['blend'] = np.clip(apply_harm_bias(O.blend.values, O.tod.values, harm_b), 5, 100)

    rng_cut, rng_c = None, 0.0
    if rng_bias_on:
        rng_cut, rng_c = rng_bias(O, F_train.loc[tr_idx, 'T_rng48'].values)
        rng_occ_tr = float((O.rng.values > rng_cut).mean())
        print('wide-range correction: cut %.2f C, subtracting %.3f %%RH from rows above it'
              % (rng_cut, rng_c))
        O['blend'] = np.clip(np.where(O.rng.values > rng_cut, O.blend - rng_c, O.blend),
                             5, 100)

    pf_b = O.groupby('fold').apply(lambda d: rmse(d.y, d.blend))
    print(f'CV: mean {pf_b.mean():.4f}  worst {pf_b.max():.4f}')
    print('  per fold:', [round(x, 3) for x in pf_b.values])

    inc_sd = tuple(INC_SEED + i for i in range(inc_seeds))
    if increment:
        # Refit the increment models per fold at that fold's own origin, exactly as the
        # test-window fit below sits at the train/test boundary. Nothing from the
        # validation window enters either endpoint.
        O['level'] = O.blend.values
        for fi, (vs, ve) in enumerate(folds):
            d = O[O.fold == fi]
            if not len(d):
                continue
            v = pd.DatetimeIndex(d.dt)
            mods = fit_increments(F_train, y, tr_mask & (IDX <= vs), inc_sd,
                                  smooth=smooth_level, vapour=vapour_increment,
                                  physics=inc_physics, deshrink=inc_deshrink,
                                  lags=inc_lags)
            O.loc[d.index, 'blend'] = reconcile(d.level.values, v, F_train, mods,
                                               inc_lambda_scale)
        pf_i = O.groupby('fold').apply(lambda d: rmse(d.y, d.blend))
        print('CV after increment reconciliation: mean %.4f  worst %.4f  (%d/%d folds better)'
              % (pf_i.mean(), pf_i.max(), int((pf_i < pf_b).sum()), len(pf_i)))
        print('  per fold:', [round(x, 3) for x in pf_i.values])
        print('  per-fold delta:', [round(x, 3) for x in (pf_i - pf_b).values])
        print('  pooled %.4f -> %.4f' % (rmse(O.y, O.level), rmse(O.y, O.blend)))

    # ---- optional dispersion calibration ----
    # An averaged tree ensemble blends many leaf values and predicts a compressed spread,
    # so on cross-validation a slope > 1 helps (13/13 folds, three fold families). It then
    # LOST on the leaderboard, 3.04904 -> 3.28564, because the deficit is regime-dependent:
    # across CV folds the blend's prediction std is 16.06-17.03, but on the test window it
    # is 18.43 -- already wider than anywhere the correction was measured. Off by default.
    slope = 1.0
    if calibrate:
        centre = O.blend.mean()
        num = ((O.y - centre) * (O.blend - centre)).sum()
        den = ((O.blend - centre) ** 2).sum()
        slope_raw = float(num / den)
        slope = 1.0 + cal_shrink * (slope_raw - 1.0)
        print(f'dispersion slope: fitted {slope_raw:.4f}  shrunk({cal_shrink}) -> {slope:.4f}')
        pf_f = O.assign(final=np.clip(centre + slope * (O.blend - centre), 5, 100)) \
                .groupby('fold').apply(lambda d: rmse(d.y, d['final']))
        print(f'CV after calibration: mean {pf_f.mean():.4f}  worst {pf_f.max():.4f}')

    # ---- refit on all training rows, predict the test window ----
    te_idx = IDX[is_te]
    esT_test = es(F_test.loc[te_idx, 'T'].values)
    P = {}
    for m in models:
        c = cols[m]
        sd = seeds_fit if base_model(m) in ('hbt', 'cat') else (0,)
        P[m] = np.clip(predict(base_model(m), F_train.loc[tr_idx, c], ytr_all,
                               F_test.loc[te_idx, c], esT_test, E_train, sd), 5, 100)
    for m, b in debias.items():
        P[m] = np.clip(P[m] - b, 5, 100)
    Pmat = pd.DataFrame(P)[models].values
    if tod_blend:
        tod_te = F_test.loc[te_idx, 'tod'].values
        # The same guard as the dispersion check below, applied to the conditioning
        # variable: per-band weights only transfer if the test rows populate the bands
        # the way the training rows did. Hour of day is uniform across a 15-day window,
        # so this passes comfortably -- unlike temperature, where the test window puts
        # 48% of its rows in the coldest training quartile against 25% in training,
        # which is why temperature-conditional weights were rejected despite scoring
        # about as well on cross-validation.
        occ_tr = np.bincount(np.digitize(O.tod.values, tod_edges[1:-1]),
                             minlength=TOD_BINS) / len(O)
        occ_te = np.bincount(np.digitize(tod_te, tod_edges[1:-1]),
                             minlength=TOD_BINS) / len(tod_te)
        shift = float(np.abs(occ_te - occ_tr).max())
        print()
        print('tod occupancy: train %s  test %s  max shift %.3f'
              % (np.round(occ_tr, 3), np.round(occ_te, 3), shift))
        if shift > 0.05:
            print('  WARNING: the test rows do not populate the time-of-day bands the'
                  ' way the training rows do, so per-band weights will not transfer.')
        blend_te = apply_tod_blend(Pmat, tod_te, tod_edges, tod_W)
        if rel_bias is not None:
            blend_te = np.clip(apply_tod_bias(blend_te, tod_te, tod_edges, rel_bias),
                               5, 100)
        if harm_b is not None:
            blend_te = np.clip(apply_harm_bias(blend_te, tod_te, harm_b), 5, 100)
        if rng_cut is not None:
            rng_te = F_test.loc[te_idx, 'T_rng48'].values
            rng_occ_te = float((rng_te > rng_cut).mean())
            print('wide-range occupancy: train %.3f  test %.3f  shift %.3f'
                  % (rng_occ_tr, rng_occ_te, abs(rng_occ_te - rng_occ_tr)))
            if abs(rng_occ_te - rng_occ_tr) > 0.05:
                print('  NOTE: this FAILS the section 63 occupancy guard. It is a priced bet,'
                      ' not an adoption - see progress.md section 87.')
            blend_te = np.clip(np.where(rng_te > rng_cut, blend_te - rng_c, blend_te),
                               5, 100)
    else:
        blend_te = Pmat @ w
    if increment:
        inc_mod = fit_increments(F_train, y, tr_mask, inc_sd, smooth=smooth_level,
                                 vapour=vapour_increment, physics=inc_physics,
                                 deshrink=inc_deshrink, lags=inc_lags)
        level_te = blend_te.copy()
        blend_te = reconcile(level_te, te_idx, F_test, inc_mod, inc_lambda_scale)
        print('\nincrement reconciliation on the test window: horizons %s, weights %s,'
              ' %d seed(s)' % ([h for h, _ in INC_SPEC],
                               [l * inc_lambda_scale for _, l in INC_SPEC], len(inc_sd)))
        if inc_deshrink:
            print('  de-shrink factors (train out-of-fold, applied at %.2f): %s'
                  % (INC_DESHRINK, {h: round(inc_mod[('f', h)], 4)
                                    for h, _ in INC_SPEC if ('f', h) in inc_mod}))
        if inc_physics:
            # Report the matrix the models were actually fitted on. This line read
            # `inc_design` unconditionally and so under-reported by 20 columns the moment
            # --inc-lags was on -- the same class of provenance slip as section 179's.
            print('  physics terms on: es_ratio and dRH_const_e, %d design columns%s'
                  % (increment_design(F_test, INC_SPEC[0][0], INC_PHYS_COLS, True,
                                      inc_lags).shape[1],
                     ' (%d of them causal lags out to %d h)'
                     % (increment_design(F_test, INC_SPEC[0][0], INC_PHYS_COLS,
                                         True, True).shape[1]
                        - inc_design(F_test, INC_SPEC[0][0], INC_PHYS_COLS, True).shape[1],
                        max(INC_LAGS) // 2) if inc_lags else ''))
        if vapour_increment:
            print('  vapour-pressure terms: horizons %s, weights %s -- the RH change is'
                  ' 82%% temperature at 2 h, this term is the moisture part'
                  % ([h for h, _ in VP_SPEC], [n for _, n in VP_SPEC]))
        if smooth_level:
            print('  smoothed-level terms: windows %s, weights %s -- the one part of the'
                  ' reconciliation that can move the level'
                  % ([w for w, _ in SMOOTH_SPEC], [m for _, m in SMOOTH_SPEC]))
            print('  level shift applied: %+.4f %%RH'
                  % float(blend_te.mean() - level_te.mean()))
        print('  moved the test path by RMS %.4f %%RH, max %.4f'
              % (float(np.sqrt(np.mean((blend_te - level_te) ** 2))),
                 float(np.max(np.abs(blend_te - level_te)))))
    c_te = blend_te.mean()
    pred = np.clip(c_te + slope * (blend_te - c_te), 5, 100)

    # Guard: a calibration fitted on cross-validation is only transferable if the quantity
    # it corrects looks the same on the test set. Prediction spread needs no target, so
    # this check is free -- and skipping it is exactly how 3.04904 became 3.28564.
    cv_std = O.groupby('fold').blend.std()
    print(f'\ndispersion check: CV fold prediction std {cv_std.min():.2f}-{cv_std.max():.2f}'
          f'   test prediction std {blend_te.std():.2f}')
    if not (cv_std.min() <= blend_te.std() <= cv_std.max()):
        msg = ('  WARNING: test prediction spread is OUTSIDE the range seen in CV, so a '
               'dispersion slope fitted on CV does not transfer.')
        print(msg + ('  Calibration is ON - this is the known failure mode.' if calibrate
                     else '  Calibration is off, as it should be.'))

    te_raw = pd.read_csv(DATA + 'test.csv', parse_dates=['datetime'])
    sub = pd.DataFrame({'datetime': te_raw.datetime.dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'air_humidity': pd.Series(pred, index=te_idx).reindex(te_raw.datetime).values})
    ss = pd.read_csv(DATA + 'sample_submission.csv')
    assert list(sub.columns) == list(ss.columns)
    assert len(sub) == len(ss)
    assert (sub.datetime.values == ss.datetime.values).all()
    assert sub.air_humidity.notna().all()
    if increment:
        out = OUT_V21 % increment_tag(
            l2_member, blend_shrink, drop_ridge, bag_nopress, robust_core, smooth_level,
            vapour_increment, inc_physics, inc_deshrink, inc_lags, inc_lambda_scale,
            tod_bias_on, harm_bias_on, hbt_trees, cat_debias, cat_debias_shrink,
            calibrate, cal_shrink)
    elif drop_ridge:
        out = OUT_V19
    elif bag_nopress:
        out = OUT_V18
    elif robust_core:
        out = OUT_V17
    elif blend_shrink != BLEND_SHRINK:
        out = OUT_V20
    elif l2_member:
        out = OUT_L2
    elif rng_bias_on:
        out = OUT_RNG if drop_lowsupport else OUT_RNG2
    elif drop_lowsupport:
        out = OUT_DROP
    elif harm_bias_on:
        out = OUT_HARM
    elif tod_bias_on or seeds != len(SEEDS_FIT) or oof_seeds != len(SEEDS_OOF):
        out = OUT_SEED % seeds
    else:
        out = OUT_TOD if tod_blend else OUT
    sub.to_csv(out, index=False)
    print()
    print('wrote ' + out)
    print('prediction summary:', {k: round(v, 3) for k, v in sub.air_humidity.describe().to_dict().items()})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true',
                    help='verify no feature depends on the target before running')
    ap.add_argument('--calibrate', action='store_true',
                    help='apply the dispersion slope (LOST on the leaderboard - see progress.md)')
    ap.add_argument('--strict-features', dest='strict_features', action='store_true',
                    help='build training features from a boundary-truncated grid')
    ap.add_argument('--tod-blend', dest='tod_blend', action='store_true',
                    help='one blend weight vector per time-of-day band (session 8)')
    ap.add_argument('--seeds', type=int, default=len(SEEDS_FIT),
                    help='seeds averaged per tree model at the final fit (default 5)')
    ap.add_argument('--oof-seeds', dest='oof_seeds', type=int, default=len(SEEDS_OOF),
                    help='seeds averaged per tree model inside cross-validation (default 3)')
    ap.add_argument('--tod-bias', dest='tod_bias_on', action='store_true',
                    help='subtract the per-time-of-day-band bias (needs --tod-blend)')
    ap.add_argument('--harm-bias', dest='harm_bias_on', action='store_true',
                    help='subtract the harmonic diurnal bias - BEST, supersedes --tod-bias')
    ap.add_argument('--drop-lowsupport', dest='drop_lowsupport', action='store_true',
                    help='drop features without training support in the test window (s81)')
    ap.add_argument('--rng-bias', dest='rng_bias_on', action='store_true',
                    help='wide-diurnal-range correction - FALSIFIED, see s95. Do not use.')
    ap.add_argument('--l2-member', dest='l2_member', action='store_true',
                    help='add a plain-L2 LightGBM as a sixth blend member (s98)')
    ap.add_argument('--drop-ridge', dest='drop_ridge', action='store_true',
                    help='remove the plain ridge member, whose drop-one contribution is'
                         ' negative and whose private-slice exposure is the worst (s122)')
    ap.add_argument('--bag-nopress', dest='bag_nopress', action='store_true',
                    help='add a LightGBM fitted without the pressure level block (s115)')
    ap.add_argument('--robust-core', dest='robust_core', action='store_true',
                    help='add a LightGBM trained on the support-stable columns (s108)')
    ap.add_argument('--increment', action='store_true',
                    help='reconcile the stack level with learned 30-minute and 2-hour RH'
                         ' increments (session 21, progress.md s147/s150)')
    ap.add_argument('--inc-deshrink', dest='inc_deshrink', action='store_true',
                    help='restore the amplitude the increment learner shrank away, at'
                         ' half the out-of-fold measured factor (s176)')
    ap.add_argument('--hbt-trees', dest='hbt_trees', type=int, default=None,
                    help='hbt n_estimators; family J (progress.md section 274) found the '
                         'response monotone over 900/1100/1400/1800/2400 on all six blocks '
                         'and two seed blocks. Default None keeps the shipped 900.')
    ap.add_argument('--cat-debias', dest='cat_debias', action='store_true',
                    help='subtract the de-bias members out-of-fold mean error before'
                         ' blending. `cat` is -2.9 forward and -0.006 in sample; NNLS has no'
                         ' intercept and both bias corrections discard theirs, so nothing else'
                         ' can reach it (progress.md section 310)')
    ap.add_argument('--cal-shrink', dest='cal_shrink', type=float, default=CAL_SHRINK,
                    help='strength of --calibrate (default %.2f, the session-6 value;'
                         ' section 318 measures 0.50)' % CAL_SHRINK)
    ap.add_argument('--cat-debias-shrink', dest='cat_debias_shrink', type=float,
                    default=CATDB_SHRINK,
                    help='strength of --cat-debias (default %.2f, the same pull every other'
                         ' correction in this file uses)' % CATDB_SHRINK)
    ap.add_argument('--inc-lags', dest='inc_lags', action='store_true',
                    help='add the causal lag trajectory to the increment design'
                         ' (session 28, progress.md s202)')
    ap.add_argument('--inc-physics', dest='inc_physics', action='store_true',
                    help='give the increment models the closed-form thermodynamic terms'
                         ' es_ratio and dRH_const_e (s169)')
    ap.add_argument('--vapour-increment', dest='vapour_increment', action='store_true',
                    help='also constrain the change in vapour pressure, which is the RH'
                         ' change with thermodynamics divided out (s163)')
    ap.add_argument('--smooth-level', dest='smooth_level', action='store_true',
                    help='add the 24-hour smoothed-humidity term, the only part of the'
                         ' reconciliation that can move the level (s158)')
    ap.add_argument('--inc-lambda-scale', dest='inc_lambda_scale', type=float,
                    default=1.0, help='multiply the increment weights; 2.0 pulls harder'
                         ' toward the learned dynamics (s158)')
    ap.add_argument('--inc-seeds', dest='inc_seeds', type=int, default=INC_SEEDS,
                    help='seeds averaged per increment model (default %d; pass 1 to'
                         ' reproduce the frozen single-seed session-20 screen)' % INC_SEEDS)
    ap.add_argument('--blend-shrink', dest='blend_shrink', type=float, default=BLEND_SHRINK,
                    help='pull of the NNLS weights toward equal weighting; 0.0 removes the'
                         ' uniform floor, which is worth -0.058 nested (s105-107)')
    main(**vars(ap.parse_args()))
