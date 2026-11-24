"""Session 25: the increment predictions are under-dispersed, and the reconciliation cares.

Section 174's learner screen produced a contradiction. The three-learner average had the LOWEST
increment RMSE at both horizons -- 3/3 blocks at 30 minutes, 2/3 at two hours -- and the WORST
reconciled result, 0/3 blocks. Lower increment error made the final answer worse.

The dispersion measurement explains it. Predicted change against actual change:

    B1 h=1  actual sd 3.544   lgb 0.883x   ensemble 0.847x
    B2 h=1  actual sd 3.634   lgb 0.870x   ensemble 0.841x

Every learner under-predicts the amplitude of the change, and averaging makes it worse, because
an average of imperfectly correlated predictions has less variance than its members. This is
section 35's under-dispersion, one level down.

**Why it matters here and not for a point forecast.** In `min ||z-p||^2 + lam ||Dz - d||^2`,
`d` is treated as an unbiased observation of `Dz`, not as an MSE-optimal point estimate. A
shrunk `d` tells the solver the humidity moves less than it does, and the path flattens -- which
is the direction section 147's zero-increment control showed is catastrophic at the limit.
Squared error rewards shrinkage; this loss function does not. So RMSE was the wrong screening
metric for the learner axis, and section 170's method claim needs the qualification that the
intermediate metric only tracks the final one while the dispersion is held fixed.

The fix follows from the diagnosis: rescale the predicted change to the dispersion it should
have. The factor is estimated **out of fold on training rows only** -- three contiguous time
folds inside the training window, never the holdout -- and clipped, so this adds no free
parameter fitted to anything being scored.

PRE-REGISTERED:

  baseline    session-24 shipped: LightGBM, physics design, no rescaling
  candidates  de-shrink; half de-shrink; the three-learner ensemble raw, de-shrunk, half
  primary     the RECONCILED RMSE, because section 174 proved the intermediate metric does not
              track it across this axis. Increment RMSE and achieved dispersion are reported as
              diagnostics, not as the criterion.
  adoption    lower reconciled RMSE on at least two of three blocks AND a negative mean, THEN
              the pipeline's nine folds, which are not part of this screen
  seeds       one per learner while screening; the winner re-confirmed at five

    .venv/Scripts/python.exe src/an45_increment_dispersion.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an44_increment_learner_screen as a44

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
OOF_FOLDS = 3
CLIP = (1.0, 1.5)

CANDIDATES = {
    'incumbent':        dict(members=('lgb',), scale=0.0),
    'deshrink':         dict(members=('lgb',), scale=1.0),
    'deshrink_half':    dict(members=('lgb',), scale=0.5),
    'ens3':             dict(members=('lgb', 'lintree', 'cat'), scale=0.0),
    'ens3_deshrink':    dict(members=('lgb', 'lintree', 'cat'), scale=1.0),
    'ens3_deshrink_half': dict(members=('lgb', 'lintree', 'cat'), scale=0.5),
}


def oof_dispersion(X, tgt, mask, members, seed):
    """sd(actual)/sd(predicted), measured on out-of-fold predictions over the TRAINING rows.

    Three contiguous time folds, so the estimate never uses a row the model was fitted on and
    never touches the window being scored. Returns the factor the prediction must be
    multiplied by for its spread to match the target's."""
    rows = X.index[mask]
    parts = np.array_split(np.arange(len(rows)), OOF_FOLDS)
    pred = pd.Series(np.nan, index=rows)
    for cut in parts:
        va = rows[cut]
        trn = rows.difference(va)
        ps = []
        for n in members:
            mod = a44.fit_learner(n, X.loc[trn], tgt.loc[trn], seed)
            ps.append(np.asarray(mod.predict(X.loc[va])).ravel())
        pred.loc[va] = np.mean(ps, axis=0)
    r = float(tgt.loc[rows].std() / pred.std())
    return float(np.clip(r, *CLIP)), r


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    P = P.loc[P.model == BACKBONE]
    rows, diag = [], []
    for b, d in P.groupby('block'):
        d = d.sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        hs, he = idx.min() - pd.Timedelta(minutes=30), idx.max()
        gh = g.loc[g.index <= he]
        F = fp.make_features(gh)
        yh = y.reindex(gh.index)
        mask0 = (pd.Series((gh.is_test == 0).to_numpy(), index=gh.index)
                 & yh.notna() & (gh.index <= hs))
        truth, base = d.y.to_numpy(), d.base.to_numpy()
        ytrue = pd.Series(truth, index=idx)
        print('%s  base %.5f' % (b, fp.rmse(truth, base)), flush=True)

        pred, act, ops, factor = {}, {}, {}, {}
        for h, lam in fp.INC_SPEC:
            X = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            tgt = (yh - yh.shift(h)).reindex(X.index)
            m = mask0.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            D, st = fp.diff_operator(idx, h)
            ops[h] = (D, lam)
            act[h] = (ytrue.reindex(st).to_numpy()
                      - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
            for key in {('lgb',), ('lgb', 'lintree', 'cat')}:
                factor[(key, h)], raw = oof_dispersion(X, tgt, m, key, fp.INC_SEED)
                diag.append(dict(block=b, steps=h, members='+'.join(key),
                                 factor_clipped=factor[(key, h)], factor_raw=raw))
            for n in a44.BASE_LEARNERS[:3]:
                mod = a44.fit_learner(n, X.loc[m], tgt.loc[m], fp.INC_SEED)
                pred[(n, h)] = np.asarray(mod.predict(X.loc[st])).ravel()
            print('   h=%d train-OOF de-shrink factor: lgb %.4f  ens3 %.4f'
                  % (h, factor[(('lgb',), h)], factor[(('lgb', 'lintree', 'cat'), h)]),
                  flush=True)

        for cand, spec in CANDIDATES.items():
            rec = dict(block=b, candidate=cand)
            A = identity(len(idx), format='csc')
            rhs = base.astype(float).copy()
            for h, lam in fp.INC_SPEC:
                p = np.mean([pred[(n, h)] for n in spec['members']], axis=0)
                f = 1.0 + spec['scale'] * (factor[(tuple(spec['members']), h)] - 1.0)
                p = p.mean() + (p - p.mean()) * f
                rec['inc_rmse_h%d' % h] = fp.rmse(act[h], p)
                rec['disp_h%d' % h] = float(p.std() / act[h].std())
                D, _ = ops[h]
                A = (A + lam * (D.T @ D)).tocsc()
                rhs = rhs + lam * (D.T @ p)
            rec['reconciled'] = fp.rmse(truth, np.clip(spsolve(A, rhs), 5, 100))
            rows.append(rec)
            print('   %-19s inc h1 %.4f (disp %.3f)  h4 %.4f (disp %.3f)  -> reconciled %.5f'
                  % (cand, rec['inc_rmse_h1'], rec['disp_h1'], rec['inc_rmse_h4'],
                     rec['disp_h4'], rec['reconciled']), flush=True)
        pd.DataFrame(rows).to_csv(OUT / 'increment_dispersion.csv', index=False)
        pd.DataFrame(diag).to_csv(OUT / 'increment_dispersion_factors.csv', index=False)

    R = pd.DataFrame(rows)
    ref = R[R.candidate == 'incumbent'].set_index('block')
    summary = {}
    for cand in CANDIDATES:
        c = R[R.candidate == cand].set_index('block')
        e = dict(recon_delta=float((c.reconciled - ref.reconciled).mean()),
                 recon_blocks=int((c.reconciled < ref.reconciled).sum()),
                 recon_pooled=float(c.reconciled.mean()),
                 inc_h1_delta=float((c.inc_rmse_h1 - ref.inc_rmse_h1).mean()),
                 inc_h4_delta=float((c.inc_rmse_h4 - ref.inc_rmse_h4).mean()),
                 disp_h1=float(c.disp_h1.mean()), disp_h4=float(c.disp_h4.mean()))
        e['adopted'] = bool(e['recon_delta'] < 0 and e['recon_blocks'] >= 2)
        summary[cand] = e
    print('\nAGAINST THE SHIPPED CONFIGURATION (negative = better)')
    print(pd.DataFrame(summary).T.to_string())
    (OUT / 'increment_dispersion.json').write_text(json.dumps(summary, indent=2))
    win = [k for k, v in summary.items() if v['adopted'] and k != 'incumbent']
    print('\nPASSES THE PRE-REGISTERED BAR:', win or 'none')


if __name__ == '__main__':
    main()
