"""Session 25: a better learner for the CHANGE target.

Section 169 priced better increment models at -0.9394 to the oracle. Section 170 collected
about -0.025 of that with two closed-form thermodynamic terms, and section 171 established
that generic extra features collect no more. What is left to vary is the learner itself, which
has been one LightGBM with constant leaves since the session-20 diagnostic screen.

Three reasons to expect the learner to matter more here than it did at the level, where
section 50 tried eleven classes and found ten dead:

* **The change target is nearly a product.** `dRH_const_e = level * (es_ratio - 1)` is the
  dominant term (section 170), and a constant-leaf tree represents a product only by chopping
  it into a staircase. `linear_tree=True` fits a linear model in each leaf, so one leaf can
  hold the whole product. Section 50 found piecewise-linear leaves were the single best of its
  eleven candidates at the LEVEL (-0.014, 11/15) and rejected them on the adoption bar; the
  argument for them is much stronger on a target that is closer to linear.
* **The change target is better conditioned.** Section 168: R² is 0.754 and 0.908 against a
  level model that carries far more irreducible spread, so a learner with lower variance and
  slightly more bias has more to gain and less to lose.
* **Averaging distinct learners reduces the exact quantity the oracle rewards.** The
  reconciliation consumes the increment prediction; anything that lowers its RMSE converts at
  the rate section 169 measured. Five seeds of one learner are nearly the same model -- section
  152 put the across-seed path spread at 0.111 %RH -- so the diversity has to come from
  somewhere else.

PRE-REGISTERED:

  baseline    `physics` + LightGBM, the session-24 shipped configuration
  candidates  piecewise-linear leaves; CatBoost; ridge; LGB+linear average; all three averaged
  primary     increment-model RMSE at h=1 AND h=4 on the three holdouts, ~700 rows each
  secondary   the reconciled RMSE that follows
  adoption    lower increment RMSE at both horizons on at least two of three blocks, AND lower
              reconciled RMSE on at least two of three, THEN the pipeline's nine folds
  seeds       one per learner while screening, so the averages are not simply buying seed
              variance reduction the baseline could also have; the winner is re-confirmed at
              five seeds per component

Residual correlations between learners are reported too: averaging pays in proportion to how
decorrelated the members are, and if they all sit above about 0.98 the route is closed whatever
the individual scores say.

    .venv/Scripts/python.exe src/an44_increment_learner_screen.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
import catboost as cb
from sklearn.linear_model import RidgeCV
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
CAT_KW = dict(iterations=800, learning_rate=0.03, depth=6, l2_leaf_reg=6.0,
              loss_function='RMSE', verbose=0, allow_writing_files=False)

BASE_LEARNERS = ('lgb', 'lintree', 'cat', 'ridge')
CANDIDATES = {
    'lgb': ('lgb',),
    'lintree': ('lintree',),
    'cat': ('cat',),
    'ridge': ('ridge',),
    'avg_lgb_lin': ('lgb', 'lintree'),
    'avg_lgb_lin_cat': ('lgb', 'lintree', 'cat'),
}


def fit_learner(name, Xtr, ytr, seed):
    if name == 'lgb':
        return lgb.LGBMRegressor(random_state=seed, **fp.INC_KW).fit(Xtr, ytr)
    if name == 'lintree':
        return lgb.LGBMRegressor(random_state=seed, linear_tree=True, **fp.INC_KW).fit(Xtr, ytr)
    if name == 'cat':
        return cb.CatBoostRegressor(random_seed=seed, **CAT_KW).fit(Xtr, ytr)
    if name == 'ridge':
        return fp._pipe(RidgeCV(alphas=np.logspace(-2, 4, 25))).fit(Xtr, ytr)
    raise ValueError(name)


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    P = P.loc[P.model == BACKBONE]
    rows, corrs = [], []
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

        # One fit per learner per horizon, reused by every candidate that contains it.
        pred, act, ops = {}, {}, {}
        for h, lam in fp.INC_SPEC:
            X = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            tgt = (yh - yh.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            D, st = fp.diff_operator(idx, h)
            ops[h] = (D, lam)
            act[h] = (ytrue.reindex(st).to_numpy()
                      - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
            for name in BASE_LEARNERS:
                mod = fit_learner(name, X.loc[m], tgt.loc[m], fp.INC_SEED)
                pred[(name, h)] = np.asarray(mod.predict(X.loc[st])).ravel()
            r = pd.DataFrame({n: act[h] - pred[(n, h)] for n in BASE_LEARNERS}).corr()
            for i, a in enumerate(BASE_LEARNERS):
                for bb in BASE_LEARNERS[i + 1:]:
                    corrs.append(dict(block=b, steps=h, pair='%s~%s' % (a, bb),
                                      resid_corr=float(r.loc[a, bb])))
            print('   h=%d residual corr: ' % h + '  '.join(
                '%s~%s %.3f' % (a, bb, r.loc[a, bb]) for i, a in enumerate(BASE_LEARNERS)
                for bb in BASE_LEARNERS[i + 1:]), flush=True)

        for cand, members in CANDIDATES.items():
            rec = dict(block=b, candidate=cand)
            A = identity(len(idx), format='csc')
            rhs = base.astype(float).copy()
            for h, lam in fp.INC_SPEC:
                p = np.mean([pred[(n, h)] for n in members], axis=0)
                rec['inc_rmse_h%d' % h] = fp.rmse(act[h], p)
                D, _ = ops[h]
                A = (A + lam * (D.T @ D)).tocsc()
                rhs = rhs + lam * (D.T @ p)
            rec['reconciled'] = fp.rmse(truth, np.clip(spsolve(A, rhs), 5, 100))
            rows.append(rec)
            print('   %-17s inc h1 %.4f  h4 %.4f  -> reconciled %.5f'
                  % (cand, rec['inc_rmse_h1'], rec['inc_rmse_h4'], rec['reconciled']),
                  flush=True)
        pd.DataFrame(rows).to_csv(OUT / 'increment_learner_screen.csv', index=False)
        pd.DataFrame(corrs).to_csv(OUT / 'increment_learner_corr.csv', index=False)

    R = pd.DataFrame(rows)
    ref = R[R.candidate == 'lgb'].set_index('block')
    summary = {}
    for cand in CANDIDATES:
        c = R[R.candidate == cand].set_index('block')
        e = dict(inc_h1_delta=float((c.inc_rmse_h1 - ref.inc_rmse_h1).mean()),
                 inc_h1_blocks=int((c.inc_rmse_h1 < ref.inc_rmse_h1).sum()),
                 inc_h4_delta=float((c.inc_rmse_h4 - ref.inc_rmse_h4).mean()),
                 inc_h4_blocks=int((c.inc_rmse_h4 < ref.inc_rmse_h4).sum()),
                 recon_delta=float((c.reconciled - ref.reconciled).mean()),
                 recon_blocks=int((c.reconciled < ref.reconciled).sum()),
                 recon_pooled=float(c.reconciled.mean()))
        e['adopted'] = bool(e['inc_h1_blocks'] >= 2 and e['inc_h4_blocks'] >= 2
                            and e['recon_blocks'] >= 2 and e['recon_delta'] < 0)
        summary[cand] = e
    print('\nAGAINST THE SHIPPED LIGHTGBM (negative = better)')
    print(pd.DataFrame(summary).T.to_string())
    C = pd.DataFrame(corrs)
    print('\nMEAN RESIDUAL CORRELATION BETWEEN LEARNERS')
    print(C.groupby(['steps', 'pair']).resid_corr.mean().round(3).to_string())
    (OUT / 'increment_learner_screen.json').write_text(json.dumps(
        {'candidates': summary,
         'residual_corr': C.groupby(['steps', 'pair']).resid_corr.mean().round(4)
         .reset_index().to_dict('records')}, indent=2))
    win = [k for k, v in summary.items() if v['adopted'] and k != 'lgb']
    print('\nPASSES THE PRE-REGISTERED BAR:', win or 'none')


if __name__ == '__main__':
    main()
