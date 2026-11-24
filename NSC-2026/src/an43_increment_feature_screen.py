"""Session 24, second screen: the increment models respond to FEATURES, not to capacity.

The first screen (`an42`) tried both. More trees and more leaves lost on every block; the two
candidates carrying closed-form thermodynamic terms won the reconciled metric on three blocks
of three. So the increment models are not capacity-limited, they are information-limited, and
the oracle in `an41` says there is -0.94 still sitting in them.

Four more feature ideas, each with a mechanism stated before it was run.

* **A better level proxy inside `dRH_const_e`.** That term is `level * (es_ratio - 1)`, the
  change thermodynamics alone would produce, and it needs an estimate of the humidity level at
  `t-h`. The shipped version uses `rh_tmin48` because it was to hand. The feature set carries
  six parameter-free level estimates -- `rh_tmin18/48/96` and `rh_q18/48/96` -- and their mean
  is a lower-variance estimate than any one of them.
* **Multi-scale driver context.** The h-step change is the only history the model gets. Whether
  a two-hour temperature fall is the start of a front or the tail of one depends on the six
  hours before it, and the model currently cannot see that.
* **Saturation headroom.** Humidity cannot rise past saturation, so the same cooling produces a
  smaller rise when the air is already near its dewpoint. `100 - level` is that headroom, and
  its product with `es_ratio - 1` is the term the constraint should really be bending.
* **The es ratio at several lags**, so the model can tell a monotone temperature fall from one
  that has already turned.

PRE-REGISTERED, on the same protocol that produced the first clean result:

  baseline    `physics`, the session-24 winner, not the original shipped model
  candidates  better level proxy; multi-scale drivers; saturation headroom; multi-lag ratio; all
  primary     increment-model RMSE at h=1 AND h=4 on the three holdouts, ~700 scored rows each
  secondary   the reconciled RMSE that follows
  adoption    lower increment RMSE at both horizons on at least two of three blocks, AND lower
              reconciled RMSE on at least two of three, THEN the pipeline's nine folds
  seeds       one while screening; the winner re-confirmed at five

    .venv/Scripts/python.exe src/an43_increment_feature_screen.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
LEVEL_PROXIES = ['rh_tmin18', 'rh_tmin48', 'rh_tmin96', 'rh_q18', 'rh_q48', 'rh_q96']
CONTEXT_LAGS = (4, 12)          # 2 h and 6 h of driver history, independent of h
RATIO_LAGS = (1, 4, 12)

CANDIDATES = {
    'physics': dict(proxy=False, context=False, sat=False, ratios=False),
    'better_level_proxy': dict(proxy=True, context=False, sat=False, ratios=False),
    'multiscale_context': dict(proxy=False, context=True, sat=False, ratios=False),
    'saturation': dict(proxy=False, context=False, sat=True, ratios=False),
    'multilag_ratio': dict(proxy=False, context=False, sat=False, ratios=True),
    'all_four': dict(proxy=True, context=True, sat=True, ratios=True),
}


def level_estimate(F, use_mean):
    c = [x for x in LEVEL_PROXIES if x in F.columns]
    return F[c].mean(axis=1) if use_mean else F['rh_tmin48']


def design(F, h, spec):
    """Session-24 `physics` design plus whichever of the four extensions `spec` turns on.
    Every term below is built from temperature, CO2 and pressure, so all of it is
    target-blind and `--selftest` covers it."""
    c = [x for x in fp.INC_PHYS_COLS if x in F.columns]
    ratio = F['esT'].shift(h) / F['esT']
    lvl = level_estimate(F, spec['proxy'])
    extra = {'es_ratio': ratio, 'dRH_const_e': lvl.shift(h) * (ratio - 1.0)}
    if spec['sat']:
        head = (100.0 - lvl).clip(lower=0)
        extra['headroom'] = head
        extra['headroom_x_ratio'] = head.shift(h) * (ratio - 1.0)
    if spec['ratios']:
        for k in RATIO_LAGS:
            if k != h:
                extra['es_ratio_lag%d' % k] = F['esT'].shift(k) / F['esT']
    parts = [F, F[c].shift(h).add_suffix('_prev'), F[c].diff(h).add_suffix('_change'),
             pd.DataFrame(extra, index=F.index)]
    if spec['context']:
        core = [x for x in ['T', 'co2', 'pressure', 'esT'] if x in F.columns]
        for k in CONTEXT_LAGS:
            parts.append(F[core].diff(k).add_suffix('_ctx%d' % k))
    return pd.concat(parts, axis=1)


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    P = P.loc[P.model == BACKBONE]
    rows = []
    for b, d in P.groupby('block'):
        d = d.sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        hs, he = idx.min() - pd.Timedelta(minutes=30), idx.max()
        gh = g.loc[g.index <= he]
        F = fp.make_features(gh)
        yh = y.reindex(gh.index)
        mask = (pd.Series((gh.is_test == 0).to_numpy(), index=gh.index)
                & yh.notna() & (gh.index <= hs))
        truth, base = d.y.to_numpy(), d.base.to_numpy()
        ytrue = pd.Series(truth, index=idx)
        print('%s  base %.5f' % (b, fp.rmse(truth, base)), flush=True)
        for cand, spec in CANDIDATES.items():
            rec = dict(block=b, candidate=cand)
            A = identity(len(idx), format='csc')
            rhs = base.astype(float).copy()
            for h, lam in fp.INC_SPEC:
                X = design(F, h, spec)
                tgt = (yh - yh.shift(h)).reindex(X.index)
                m = mask.reindex(X.index, fill_value=False)
                m = m & tgt.notna() & m.shift(h, fill_value=False)
                mod = lgb.LGBMRegressor(random_state=fp.INC_SEED, **fp.INC_KW)
                mod.fit(X.loc[m], tgt.loc[m])
                D, st = fp.diff_operator(idx, h)
                pred = mod.predict(X.loc[st])
                act = (ytrue.reindex(st).to_numpy()
                       - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
                rec['inc_rmse_h%d' % h] = fp.rmse(act, pred)
                rec['nfeat'] = X.shape[1]
                A = (A + lam * (D.T @ D)).tocsc()
                rhs = rhs + lam * (D.T @ pred)
            rec['reconciled'] = fp.rmse(truth, np.clip(spsolve(A, rhs), 5, 100))
            rows.append(rec)
            print('   %-19s inc h1 %.4f  h4 %.4f  -> reconciled %.5f  (%d feats)'
                  % (cand, rec['inc_rmse_h1'], rec['inc_rmse_h4'], rec['reconciled'],
                     rec['nfeat']), flush=True)
        pd.DataFrame(rows).to_csv(OUT / 'increment_feature_screen.csv', index=False)

    R = pd.DataFrame(rows)
    base_c = R[R.candidate == 'physics'].set_index('block')
    summary = {}
    for cand in CANDIDATES:
        c = R[R.candidate == cand].set_index('block')
        e = dict(inc_h1_delta=float((c.inc_rmse_h1 - base_c.inc_rmse_h1).mean()),
                 inc_h1_blocks=int((c.inc_rmse_h1 < base_c.inc_rmse_h1).sum()),
                 inc_h4_delta=float((c.inc_rmse_h4 - base_c.inc_rmse_h4).mean()),
                 inc_h4_blocks=int((c.inc_rmse_h4 < base_c.inc_rmse_h4).sum()),
                 recon_delta=float((c.reconciled - base_c.reconciled).mean()),
                 recon_blocks=int((c.reconciled < base_c.reconciled).sum()),
                 recon_pooled=float(c.reconciled.mean()))
        e['adopted'] = bool(e['inc_h1_blocks'] >= 2 and e['inc_h4_blocks'] >= 2
                            and e['recon_blocks'] >= 2 and e['recon_delta'] < 0)
        summary[cand] = e
    print('\nAGAINST `physics` (negative = better)')
    print(pd.DataFrame(summary).T.to_string())
    (OUT / 'increment_feature_screen.json').write_text(json.dumps(summary, indent=2))
    win = [k for k, v in summary.items() if v['adopted'] and k != 'physics']
    print('\nPASSES THE PRE-REGISTERED BAR:', win or 'none')


if __name__ == '__main__':
    main()
