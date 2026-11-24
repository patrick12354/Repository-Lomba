"""Session 21, the adoption decision: price the increment delta on the production-shaped
holdouts, compare the three backbones on the same rows, and describe what the change does
to the submission that would actually be uploaded.

Two things this deliberately does NOT do. It does not convert a holdout delta into a
predicted leaderboard move -- section 144 withdrew the four-point regression that used to
do that. And it does not call the first 220 test rows public: it reports near/far, because
the partition was never confirmed.

    .venv/Scripts/python.exe src/an37_increment_decision.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
SUB = ROOT / 'outputs' / 'submissions'
RNG = np.random.default_rng(20260905)
BOOT = 4000


def block_bootstrap(day, base, cand, block_days, n=BOOT):
    """Circular bootstrap over calendar blocks, resampling whole runs of days so that the
    lag-one error autocorrelation of 0.9330 (section 146) is not treated as independence."""
    days = np.array(sorted(pd.unique(day)))
    k = len(days)
    nb = int(np.ceil(k / block_days))
    pos = {d: i for i, d in enumerate(days)}
    idx_by_day = [np.flatnonzero(day == d) for d in days]
    out = np.empty(n)
    for b in range(n):
        starts = RNG.integers(0, k, nb)
        take = np.concatenate([idx_by_day[(s + j) % k]
                               for s in starts for j in range(block_days)])
        out[b] = fp.rmse(cand[take], np.zeros(len(take))) - fp.rmse(base[take], np.zeros(len(take)))
    return float(np.quantile(out, .025)), float(np.quantile(out, .975))


def main():
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    P['day'] = pd.DatetimeIndex(P.datetime).normalize()
    scores = pd.read_csv(OUT / 'increment_production_scores.csv')
    report = {}

    # ---- delta, priced on the two non-overlapping blocks and on all three ----
    for tag, d in P.groupby('model'):
        clean = d.loc[d.block != 'B3_shift7d']
        ent = dict(
            pooled_base=fp.rmse(d.y, d.base), pooled_increment=fp.rmse(d.y, d.increment),
            nonoverlapping_base=fp.rmse(clean.y, clean.base),
            nonoverlapping_increment=fp.rmse(clean.y, clean.increment))
        for bd in (3, 7):
            ent['ci_%dday_blocks' % bd] = block_bootstrap(
                clean.day.to_numpy(), (clean.base - clean.y).to_numpy(),
                (clean.increment - clean.y).to_numpy(), bd)
        report[tag] = ent
        print(tag, json.dumps(ent), flush=True)

    # ---- backbone comparison on identical rows ----
    piv = P.pivot_table(index=['block', 'datetime'], columns='model',
                        values=['base', 'increment'])
    cmp = {}
    for stage in ('base', 'increment'):
        col = piv[stage]
        truth = P.loc[P.model == 'v12'].set_index(['block', 'datetime']).y.reindex(col.index)
        cmp[stage] = {m: fp.rmse(truth, col[m]) for m in col.columns}
        per_block = scores.pivot(index='block', columns='model', values=stage)
        cmp[stage + '_wins_by_block'] = {m: int((per_block.idxmin(axis=1) == m).sum())
                                         for m in per_block.columns}
    report['backbone_comparison'] = cmp
    print('\nBACKBONE COMPARISON\n' + json.dumps(cmp, indent=2))

    # ---- what the change does to the file that would be uploaded ----
    te = pd.read_csv(ROOT / 'Dataset' / 'test.csv', parse_dates=['datetime'])
    files = {'v12': ('v12_harmbias.csv', 'v21_increment_v12.csv'),
             'v16': ('v16_l2member.csv', 'v21_increment_v16.csv'),
             'v20': ('v20_shrinkonly.csv', 'v21_increment_v20.csv')}
    moves = {}
    for tag, (a, b) in files.items():
        pa, pb = SUB / a, SUB / b
        if not (pa.exists() and pb.exists()):
            continue
        A = pd.read_csv(pa).air_humidity.to_numpy()
        B = pd.read_csv(pb).air_humidity.to_numpy()
        d = B - A
        near = np.arange(len(d)) < 220        # NEAR/FAR, not public/private -- section 144
        moves[tag] = dict(
            rms=float(np.sqrt(np.mean(d ** 2))), max_abs=float(np.abs(d).max()),
            mean=float(d.mean()), rms_near220=float(np.sqrt(np.mean(d[near] ** 2))),
            rms_far514=float(np.sqrt(np.mean(d[~near] ** 2))),
            rows_moved_over_1rh=int((np.abs(d) > 1).sum()),
            sd_before=float(A.std()), sd_after=float(B.std()))
        print('\n%s -> increment: RMS %.4f  max %.4f  near220 %.4f  far514 %.4f'
              % (tag, moves[tag]['rms'], moves[tag]['max_abs'],
                 moves[tag]['rms_near220'], moves[tag]['rms_far514']))
    report['submission_move'] = moves

    # ---- does the reconciliation change the diurnal amplitude it was meant to restore? ----
    tod = te.datetime.dt.hour + te.datetime.dt.minute / 60.0
    amp = {}
    for tag, (a, b) in files.items():
        if not (SUB / a).exists() or not (SUB / b).exists():
            continue
        t = 2 * np.pi * tod.to_numpy() / 24.0
        X = np.column_stack([np.ones(len(t)), np.sin(t), np.cos(t)])
        amp[tag] = {}
        for lbl, f in (('base', a), ('increment', b)):
            c = np.linalg.lstsq(X, pd.read_csv(SUB / f).air_humidity.to_numpy(), rcond=None)[0]
            amp[tag][lbl] = float(np.hypot(c[1], c[2]))
    report['diurnal_amplitude'] = amp
    print('\nDIURNAL AMPLITUDE OF THE SUBMITTED PATH\n' + json.dumps(amp, indent=2))


    # ---- target-blind control on the test window itself ----
    # Section 147's zero-increment control was run on validation folds. The same control
    # can be run on the test window without any label: solve the identical system with the
    # learned increments replaced by zero, which is pure smoothing at the same strength.
    # If the reconciled path sat close to that, the flag would be a smoother wearing a
    # dynamics model's name.
    from scipy.sparse import identity
    from scipy.sparse.linalg import spsolve
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    te_idx = g.index[(g.is_test == 1).to_numpy()]
    tr_mask = pd.Series((g.is_test == 0).to_numpy(), index=g.index) & y.notna()
    inc = fp.fit_increments(F, y, tr_mask,
                            tuple(fp.INC_SEED + i for i in range(fp.INC_SEEDS)))

    A = identity(len(te_idx), format='csc')
    dparts = {}
    for h, lam in fp.INC_SPEC:
        D, stamps = fp.diff_operator(te_idx, h)
        X = fp.inc_design(F, h).loc[stamps]
        d = np.mean([m.predict(X) for m in inc[h]], axis=0)
        dparts[h] = (D, d, lam)
        A = (A + lam * (D.T @ D)).tocsc()

    control = {}
    for tag, (a, b) in files.items():
        if not (SUB / a).exists() or not (SUB / b).exists():
            continue
        base = pd.read_csv(SUB / a).air_humidity.to_numpy()
        got = pd.read_csv(SUB / b).air_humidity.to_numpy()
        smooth = np.clip(spsolve(A, base), 5, 100)
        ent = dict(rms_increment_vs_base=float(np.sqrt(np.mean((got - base) ** 2))),
                   rms_smoothing_vs_base=float(np.sqrt(np.mean((smooth - base) ** 2))),
                   rms_increment_vs_smoothing=float(np.sqrt(np.mean((got - smooth) ** 2))))
        # How far the learned dynamics sit from the level model's own implied dynamics.
        for h, (D, d, lam) in dparts.items():
            ent['step%d_model_vs_stack_rms' % h] = float(np.sqrt(np.mean((d - D @ base) ** 2)))
            ent['step%d_model_sd' % h] = float(d.std())
            ent['step%d_stack_sd' % h] = float((D @ base).std())
        control[tag] = ent
    report['zero_increment_control'] = control
    print(chr(10) + 'ZERO-INCREMENT CONTROL ON THE TEST WINDOW')
    print(json.dumps(control, indent=2))

    (OUT / 'increment_decision.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
