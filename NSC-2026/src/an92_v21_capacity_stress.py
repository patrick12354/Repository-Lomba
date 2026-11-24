"""Session 40: the OOD stress gate for the family-J `hbt` capacity curve.

Section 110 killed four shrinkage changes that had passed every in-regime gate this log has --
nested CV, the family gate, the bootstrap and the random-conditioner control -- because on the
stress blocks they transferred four to six times worse than they gained. Section 114 made running
this a standing rule for *every* candidate, hyper-parameter changes included. Family J is a
hyper-parameter change with an in-regime gain, so it does not get recommended without this.

**What the stress blocks are.** Section 109's design, unchanged: five 3-day validation blocks
inside the training period, ranked by a TARGET-FREE distance between their descriptors (pressure,
diurnal range, missingness, season) and the private slice's, each with a 96-hour embargo and
past-only training. Labels come only from `train.csv`; the private features say which direction
counts as stressed and nothing else.

**The statistic is pooled, not the mean of per-block RMSEs.** Section 109 caught that mistake: a
block at 6.5 carries fourteen times the weight of one at 1.75, the competition pools squared error
over all rows, and the mean-of-RMSE statistic reversed the verdict on v17.

**What varies and what does not.** Only `hbt`'s `n_estimators`. The other five members are fitted
once per split and shared by every arm, so a delta cannot come from anywhere else, and the blend
weights are refitted per split from that split's own past-only inner folds.

    .venv/Scripts/python.exe src/an92_v21_capacity_stress.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an36_increment_production as a36
import v21_campaign_registry as reg
from robust_eval import block_descriptors, make_stress_splits, score_blocks_against_reference

OUT = ROOT / 'outputs' / 'audit_v21_s40'
PUBLIC_ROWS = 220           # the near 30%; the private descriptor is taken from the rest


def _arms():
    """The control plus the registered family-J tree counts. Nothing invented here."""
    arms = {'control': dict(fp.LGB_KW)}
    for t in reg.wave2_trials():
        if set(t['params']) == {'n_estimators'}:
            arms[t['id']] = dict(fp.LGB_KW, **t['params'])
    return arms


ARMS = _arms()


def pooled_rmse(blocks):
    """One RMSE over every row of every block, which is what the leaderboard computes.

    `blocks` is a sequence of (y, pred) pairs. Section 109: the mean of per-block RMSEs
    re-weights toward the easy blocks and is not the metric.
    """
    y = np.concatenate([np.asarray(a, float) for a, _ in blocks])
    p = np.concatenate([np.asarray(b, float) for _, b in blocks])
    return float(np.sqrt(np.mean((y - p) ** 2)))


def stress_splits(F, is_tr, is_te):
    trF = F.loc[is_tr]
    priv = F.loc[is_te].iloc[PUBLIC_ROWS:]
    ref = pd.Series({'pressure': priv.pressure.median(),
                     'temp_range': priv.T_rng48.median(),
                     'missing': priv.isna().mean().mean(),
                     'season': (priv.index.min() - trF.index.min()).total_seconds() / 86400.0})
    desc = block_descriptors(trF, block_days=3)
    desc['stress_score'] = score_blocks_against_reference(desc, ref)
    return make_stress_splits(trF.index, desc, n=5, embargo_hours=96, min_train_rows=1000)


def _fit(name, kw, F, y, tr, va):
    """One member on one split. `hbt` takes the arm's hyper-parameters; the rest are shipped.

    `kw=None` means "the shipped parameters" for every member including `hbt`, so a caller that
    wants a plain control stack does not have to know which member is the tunable one.
    """
    esv = fp.es(F.loc[va, 'T'].to_numpy())
    etr = y.loc[tr] * fp.es(F.loc[tr, 'T'].to_numpy()) / 100.0
    if name == 'hbt':
        import lightgbm as lgb
        kw = dict(fp.LGB_KW) if kw is None else kw
        p = np.mean([lgb.LGBMRegressor(random_state=s, **kw)
                     .fit(F.loc[tr], y.loc[tr]).predict(F.loc[va]) for s in fp.SEEDS_OOF], 0)
    else:
        p = fp.predict(name, F.loc[tr], y.loc[tr], F.loc[va], esv, etr, fp.SEEDS_OOF)
    return np.clip(p, 5, 100)


def inner_folds(tr_idx, n=3, val_days=6, step_days=4):
    """Past-only rolling origins inside a split's own training rows."""
    out, end = [], tr_idx.max()
    for i in range(n):
        cut = end - pd.Timedelta(days=step_days * i)
        vs = cut - pd.Timedelta(days=val_days)
        v = tr_idx[(tr_idx > vs) & (tr_idx <= cut)]
        t = tr_idx[tr_idx <= vs]
        if len(t) > 700 and len(v) > 100:
            out.append((t, v))
    return out[::-1]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    splits = stress_splits(F, is_tr, is_te)
    models = list(fp.MODELS_L2)
    print('stress splits: %s' % [(str(v.min().date()), len(v)) for _, v in splits], flush=True)

    per_arm = {a: [] for a in ARMS}
    rows = []
    for sid, (ti, vi) in enumerate(splits):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        folds = inner_folds(tr)
        # the five members that no arm changes: fitted once, on the outer split and on each
        # inner fold, and shared by every arm.
        shared_out = {m: _fit(m, None, F, y, tr, va) for m in models if m != 'hbt'}
        shared_in = [{m: _fit(m, None, F, y, t, v) for m in models if m != 'hbt'}
                     for t, v in folds]
        for arm, kw in ARMS.items():
            V = pd.DataFrame({**shared_out, 'hbt': _fit('hbt', kw, F, y, tr, va)}, index=va)
            V['y'] = y.loc[va].to_numpy()
            V['tod'] = va.hour + va.minute / 60.0
            O = []
            for (t, v), sh in zip(folds, shared_in):
                d = pd.DataFrame({**sh, 'hbt': _fit('hbt', kw, F, y, t, v)},
                                 index=pd.DatetimeIndex(v))
                d['y'] = y.loc[v].to_numpy()
                d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
                O.append(d.reset_index(names='dt'))
            O = pd.concat(O, ignore_index=True)
            p = a36.stack(O, V, models, fp.BLEND_SHRINK)
            per_arm[arm].append((V.y.to_numpy(), p))
            rows.append(dict(split=sid, arm=arm, n=len(va),
                             start=str(va.min()), rmse=fp.rmse(V.y, p),
                             rmse_member=fp.rmse(V.y, V.hbt)))
        print('  split %d  %s  n=%d  [%.0f s]  %s'
              % (sid, va.min().date(), len(va), time.time() - t0,
                 '  '.join('%s %.4f' % (a, rows[-len(ARMS) + i]['rmse'])
                           for i, a in enumerate(ARMS))), flush=True)

    L = pd.DataFrame(rows)
    L.to_csv(OUT / 'capacity_stress.csv', index=False)
    base = pooled_rmse(per_arm['control'])
    base_worst = max(fp.rmse(a, b) for a, b in per_arm['control'])
    summary = {}
    print('\n%-8s %10s %10s %10s %10s  blocks improved' % ('arm', 'pooled', 'd_pooled',
                                                           'worst', 'd_worst'))
    for arm in ARMS:
        pl = pooled_rmse(per_arm[arm])
        wo = max(fp.rmse(a, b) for a, b in per_arm[arm])
        imp = sum(fp.rmse(a, b) < fp.rmse(c, d)
                  for (a, b), (c, d) in zip(per_arm[arm], per_arm['control']))
        summary[arm] = dict(pooled=pl, d_pooled=pl - base, worst=wo, d_worst=wo - base_worst,
                            blocks_improved=int(imp), n_blocks=len(splits))
        print('%-8s %10.5f %+10.5f %10.5f %+10.5f  %d/%d'
              % (arm, pl, pl - base, wo, wo - base_worst, imp, len(splits)))
    (OUT / 'capacity_stress.json').write_text(json.dumps(summary, indent=2))
    print('\nSection 110: an in-regime gain that reverses here is the signature to reject on.')
    return L, summary


if __name__ == '__main__':
    run()
