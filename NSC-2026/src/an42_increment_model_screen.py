"""Session 24: improve the increment MODELS, which is the lever nobody has pulled.

Sessions 22 and 23 tuned the reconciliation -- weights, horizons, extra operators, per-row
weights, a vapour-pressure term -- and found a flat surface and no survivors. They were tuning
the wrong thing. `src/an41_increment_oracle.py`'s ceiling, on the two non-overlapping holdouts:

    no reconciliation                       5.5047
    shipped increment models                5.3841
    half the increment models' error        4.8417
    ORACLE increments (the true changes)    4.4447

**Improving the increment models is worth up to -0.94 from where we stand**, and halving their
error already collects -0.54 of it. Unlike the per-day level of section 163 -- ceiling -1.24,
leave-one-day-out R2 negative, unreachable -- this component is demonstrably reachable: the
models already explain 75 % of the 30-minute change and 91 % of the 2-hour change.

And the models were never built for production. `INC_KW` and `INC_COLS` were set once in
session 20 for a diagnostic screen and frozen through three sessions of tuning something else.
Two specific gaps:

* **`esT` is not in the prev/change list.** The dominant term in a humidity change is
  thermodynamic: at constant vapour pressure `RH[t] = RH[t-h] * es(T[t-h])/es(T[t])`. Squared
  correlation of dRH with dT is 0.643 at 30 minutes and 0.817 at 2 hours, so the model spends
  most of its capacity rediscovering that ratio through splits on T and T_prev. Handing it
  `es_ratio` directly, and the analytic constant-vapour-pressure change built from the
  parameter-free `rh_tmin48` level estimate, gives it the term instead of making it learn one.
* **Capacity.** 500 trees at 15 leaves, against the level models' 900. Never varied.

METHOD, and this is the point of the session. Sessions 22 and 23 screened on the final
reconciled RMSE, which moves by hundredths on 720 correlated rows -- so two of fourteen
candidates passed at roughly the rate chance produces. Here the primary screen is the
increment model's OWN out-of-sample RMSE at each horizon, ~700 scored rows per block per
horizon, a quantity that moves by tenths. High signal first, then the final metric, then the
pipeline's nine folds.

PRE-REGISTERED:

  candidates  shipped; +physics features; +capacity; +both; +wider driver list; all three
  primary     increment-model RMSE at h=1 AND h=4, on the three production holdouts
  secondary   the reconciled RMSE that follows from it
  adoption    lower increment RMSE at both horizons on at least two of three blocks, AND lower
              reconciled RMSE on at least two of three, THEN confirmation on the pipeline's
              nine folds, which are not part of this screen
  seeds       one while screening; the winner is re-confirmed at five

    .venv/Scripts/python.exe src/an42_increment_model_screen.py
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

PHYS_COLS = fp.INC_COLS + ['esT', 'log_esT']
WIDE_COLS = PHYS_COLS + ['T_min48', 'T_minus_min48', 'co2_c6h', 'p_tend24h', 'rh_q48']
BIG_KW = dict(fp.INC_KW, n_estimators=900, num_leaves=31, min_child_samples=20)

CANDIDATES = {
    'shipped':          dict(cols=fp.INC_COLS, phys=False, kw=fp.INC_KW),
    'physics':          dict(cols=PHYS_COLS,   phys=True,  kw=fp.INC_KW),
    'capacity':         dict(cols=fp.INC_COLS, phys=False, kw=BIG_KW),
    'physics_capacity': dict(cols=PHYS_COLS,   phys=True,  kw=BIG_KW),
    'wide':             dict(cols=WIDE_COLS,   phys=True,  kw=fp.INC_KW),
    'wide_capacity':    dict(cols=WIDE_COLS,   phys=True,  kw=BIG_KW),
}


def design(F, h, cols, phys):
    """Increment design. With `phys`, two analytic thermodynamic terms are added.

    `es_ratio` is exactly the factor by which relative humidity changes over the interval if
    the vapour pressure does not move, and `dRH_const_e` multiplies it by a parameter-free
    estimate of the level -- `rh_tmin48`, the dewpoint-proxy of section 19 -- to give the
    predicted change under pure thermodynamics. Both use temperature only, so both are
    target-blind.
    """
    c = [x for x in cols if x in F.columns]
    parts = [F, F[c].shift(h).add_suffix('_prev'), F[c].diff(h).add_suffix('_change')]
    if phys:
        ratio = F['esT'].shift(h) / F['esT']
        extra = pd.DataFrame({'es_ratio': ratio,
                              'dRH_const_e': F['rh_tmin48'].shift(h) * (ratio - 1.0)},
                             index=F.index)
        parts.append(extra)
    return pd.concat(parts, axis=1)


def fit(F, y, mask, h, spec, seeds):
    X = design(F, h, spec['cols'], spec['phys'])
    tgt = (y - y.shift(h)).reindex(X.index)
    m = mask.reindex(X.index, fill_value=False)
    m = m & tgt.notna() & m.shift(h, fill_value=False)
    return [lgb.LGBMRegressor(random_state=s, **spec['kw']).fit(X.loc[m], tgt.loc[m])
            for s in seeds], X


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
            rec = dict(block=b, candidate=cand, base=fp.rmse(truth, base))
            A = identity(len(idx), format='csc')
            rhs = base.astype(float).copy()
            for h, lam in fp.INC_SPEC:
                models, X = fit(F, yh, mask, h, spec, (fp.INC_SEED,))
                D, st = fp.diff_operator(idx, h)
                pred = np.mean([m.predict(X.loc[st]) for m in models], axis=0)
                # Both endpoints of the scored change lie inside the holdout, so the
                # increment model can be scored directly and precisely.
                act = (ytrue.reindex(st).to_numpy()
                       - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
                rec['inc_rmse_h%d' % h] = fp.rmse(act, pred)
                rec['n_h%d' % h] = len(st)
                rec['nfeat_h%d' % h] = X.shape[1]
                A = (A + lam * (D.T @ D)).tocsc()
                rhs = rhs + lam * (D.T @ pred)
            rec['reconciled'] = fp.rmse(truth, np.clip(spsolve(A, rhs), 5, 100))
            rows.append(rec)
            print('   %-17s inc h1 %.4f  h4 %.4f  -> reconciled %.5f  (%d feats)'
                  % (cand, rec['inc_rmse_h1'], rec['inc_rmse_h4'], rec['reconciled'],
                     rec['nfeat_h1']), flush=True)
        pd.DataFrame(rows).to_csv(OUT / 'increment_model_screen.csv', index=False)

    R = pd.DataFrame(rows)
    piv = R.pivot(index='candidate', columns='block')
    print('\nAGAINST THE SHIPPED INCREMENT MODEL (negative = better)')
    summary = {}
    for cand in CANDIDATES:
        c = R[R.candidate == cand].set_index('block')
        s = R[R.candidate == 'shipped'].set_index('block')
        e = dict(
            inc_h1_delta=float((c.inc_rmse_h1 - s.inc_rmse_h1).mean()),
            inc_h1_blocks=int((c.inc_rmse_h1 < s.inc_rmse_h1).sum()),
            inc_h4_delta=float((c.inc_rmse_h4 - s.inc_rmse_h4).mean()),
            inc_h4_blocks=int((c.inc_rmse_h4 < s.inc_rmse_h4).sum()),
            recon_delta=float((c.reconciled - s.reconciled).mean()),
            recon_blocks=int((c.reconciled < s.reconciled).sum()),
            recon_pooled=float(c.reconciled.mean()))
        e['adopted'] = bool(e['inc_h1_blocks'] >= 2 and e['inc_h4_blocks'] >= 2
                            and e['recon_blocks'] >= 2 and e['recon_delta'] < 0)
        summary[cand] = e
    T = pd.DataFrame(summary).T
    print(T.to_string())
    (OUT / 'increment_model_screen.json').write_text(json.dumps(summary, indent=2))
    win = [k for k, v in summary.items() if v['adopted'] and k != 'shipped']
    print('\nPASSES THE PRE-REGISTERED BAR:', win or 'none')


if __name__ == '__main__':
    main()
