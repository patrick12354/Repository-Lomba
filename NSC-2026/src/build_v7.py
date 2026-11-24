"""Final: v7 = v6 + a 96h Tmin window (exp21) + co2 order statistics (exp20).

Scores v7 against v5 (shipped, LB 3.95445) and v6 on all three fold families with NESTED
blend weights, runs a paired day-level bootstrap, then refits on all training data and
writes the submission. v5/v6 OOF is reloaded from final_v6.py so the comparison is exact.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

NAME = 'v7_airmass'
SEEDS = (0, 1, 2)
FIT_SEEDS = (0, 1, 2, 3, 4)
SHRINK = 0.25
MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
is_te = pd.Series((g.is_test == 1).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
F = build_v7(c)
IDX = g.index
tr = is_tr & y.notna()
T = c['air_temperature']
ESt = pd.Series(es(T.values), index=IDX)
E = y * ESt / 100.0
print(f'v7 features {F.shape[1]}  train {int(tr.sum())}  test {int(is_te.sum())}', flush=True)

KW = dict(objective='huber', alpha=4.0, n_estimators=900, learning_rate=0.03, num_leaves=15,
          min_child_samples=25, subsample=0.8, subsample_freq=1, colsample_bytree=0.7,
          reg_lambda=3.0, verbose=-1)


def pipe(e):
    return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), e)


def predict(name, t, v, seeds=SEEDS):
    if name == 'hbt':
        return np.mean([lgb.LGBMRegressor(random_state=s, **KW).fit(F[t], y[t]).predict(F[v])
                        for s in seeds], 0)
    if name == 'cat':
        return np.mean([cb.CatBoostRegressor(iterations=1200, learning_rate=0.035, depth=6,
                        l2_leaf_reg=6., loss_function='Huber:delta=4', random_seed=s, verbose=0,
                        allow_writing_files=False).fit(F[t], y[t]).predict(F[v]) for s in seeds], 0)
    if name == 'ridge':
        return pipe(Ridge(alpha=20.)).fit(F[t], y[t]).predict(F[v])
    if name == 'enet':
        return pipe(ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=8000)).fit(F[t], y[t]).predict(F[v])
    if name == 'ridge_e':
        m = pipe(Ridge(alpha=20.)).fit(F[t], E[t])
        return 100.0 * m.predict(F[v]) / ESt[v].values
    raise ValueError(name)


FAM = {'P': origins(IDX[tr], n=9, val_days=15, step_days=2),
       'Q': origins(IDX[tr], n=6, val_days=15, step_days=3),
       'R': origins(IDX[tr], n=5, val_days=21, step_days=3)}

t0 = time.time()
OOF = pickle.load(open('outputs/v6_oof.pkl', 'rb'))
for fam, folds in FAM.items():
    per = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve)
        t = tr & (IDX <= vs)
        if t.sum() < 300 or v.sum() < 50:
            continue
        d = pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values))
        for m in MS:
            d[m] = np.clip(predict(m, t, v), 5, 100)
        per.append(d)
    OOF[('v7', fam)] = pd.concat(per, ignore_index=True)
    print(f'  OOF v7/{fam} done ({time.time()-t0:.0f}s)', flush=True)
pickle.dump(OOF, open('outputs/v7_oof.pkl', 'wb'))


def nested_pred(O, models, shrink=SHRINK):
    """Blend fold k using NNLS weights fitted only on folds < k."""
    out = []
    for k in sorted(O.fold.unique()):
        prev = O[O.fold < k]
        cur = O[O.fold == k].copy()
        if len(prev) < 200:
            continue
        w, _ = nnls(prev[models].values, prev.y.values)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
        w = (1 - shrink) * w + shrink * np.ones(len(models)) / len(models)
        cur['p'] = cur[models].values @ w
        out.append(cur)
    return pd.concat(out, ignore_index=True)


CAND = {'v5_shipped': ('v5', ['hbt', 'cat', 'ridge', 'enet']),
        'v6_airmass': ('v6', MS),
        'v7_airmass': ('v7', MS)}
print('\n' + f'{"candidate":13s} ' + ' '.join(f'{f}mean {f}wst ' for f in FAM) + '   avg  avgWst', flush=True)
SC = {}
for nm, (cn, ms) in CAND.items():
    row = []
    for fam in FAM:
        L = nested_pred(OOF[(cn, fam)], ms)
        pf = L.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        row.append((float(pf.mean()), float(pf.max())))
        SC[(nm, fam)] = L
    print(f'{nm:13s} ' + ' '.join(f'{m:6.3f} {w:6.3f}' for m, w in row) +
          f' {np.mean([r[0] for r in row]):7.3f} {np.mean([r[1] for r in row]):7.3f}', flush=True)

print('\n### PAIRED DAY-LEVEL BOOTSTRAP vs v5_shipped (family P, 4000 resamples) ###', flush=True)
rng = np.random.default_rng(0)
A = SC[('v5_shipped', 'P')].copy()
A['day'] = A.dt.dt.date
for nm in ('v6_airmass', 'v7_airmass'):
    B = SC[(nm, 'P')]
    M = A[['fold', 'dt', 'y', 'p', 'day']].merge(B[['fold', 'dt', 'p']], on=['fold', 'dt'], suffixes=('_a', '_b'))
    fa = M.groupby('fold').apply(lambda d: rmse(d.y, d.p_a))
    fb = M.groupby('fold').apply(lambda d: rmse(d.y, d.p_b))
    dsq = M.assign(sa=(M.p_a - M.y) ** 2, sb=(M.p_b - M.y) ** 2).groupby('day')[['sa', 'sb']].mean()
    days = dsq.index.values
    boot = []
    for _ in range(4000):
        s = dsq.loc[rng.choice(days, len(days), replace=True)]
        boot.append(np.sqrt(s.sb.mean()) - np.sqrt(s.sa.mean()))
    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f'  {nm}: pooled {rmse(M.y, M.p_b):.3f} vs {rmse(M.y, M.p_a):.3f} '
          f'(delta {rmse(M.y, M.p_b)-rmse(M.y, M.p_a):+.3f})  folds {int((fb<fa).sum())}/{len(fa)}  '
          f'days {float((dsq.sb<dsq.sa).mean())*100:.1f}%  CI [{lo:+.3f},{hi:+.3f}]  '
          f'P(better) {(boot<0).mean()*100:.1f}%', flush=True)

print('\nrefit on all training data...', flush=True)
O = OOF[('v7', 'P')]
w, _ = nnls(O[MS].values, O.y.values)
w = w / w.sum() if w.sum() > 0 else np.ones(len(MS)) / len(MS)
w = (1 - SHRINK) * w + SHRINK * np.ones(len(MS)) / len(MS)
print('weights:', {m: round(float(x), 4) for m, x in zip(MS, w)}, flush=True)
pf = O.groupby('fold').apply(lambda d: rmse(d.y, d[MS].values @ w))
print(f'family-P CV (pooled weights): mean {pf.mean():.4f} worst {pf.max():.4f} '
      f'{[round(x,3) for x in pf.values]}', flush=True)

Pt = pd.DataFrame({m: np.clip(predict(m, tr, is_te, FIT_SEEDS if m in ('hbt', 'cat') else (0,)), 5, 100)
                   for m in MS}, index=IDX[is_te])
pred = np.clip(Pt[MS].values @ w, 5, 100)
te = pd.read_csv(D + 'test.csv', parse_dates=['datetime'])
sub = pd.DataFrame({'datetime': te.datetime.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'air_humidity': pd.Series(pred, index=IDX[is_te]).reindex(te.datetime).values})
ss = pd.read_csv(D + 'sample_submission.csv')
assert list(sub.columns) == list(ss.columns) and len(sub) == len(ss) == 734
assert (sub.datetime.values == ss.datetime.values).all()
assert sub.air_humidity.notna().all() and sub.air_humidity.between(0, 100).all()
assert not sub.datetime.duplicated().any()
sub.to_csv(f'outputs/submissions/{NAME}.csv', index=False)
Pt.to_csv(f'outputs/testpreds_{NAME}.csv')
print(f'\nwrote outputs/submissions/{NAME}.csv  (734 rows, datetimes match sample_submission)', flush=True)
print('pred:', sub.air_humidity.describe().round(2).to_dict())
print('RMSE between prediction vectors:')
for old in ['v6_airmass', 'v5_final']:
    o = pd.read_csv(f'outputs/submissions/{old}.csv')
    print(f'  vs {old}: {rmse(sub.air_humidity, o.air_humidity):.3f}')
log_experiment(dict(name=NAME, n_feats=int(F.shape[1]), models=MS,
                    weights={m: round(float(x), 4) for m, x in zip(MS, w)},
                    cv_P_mean=float(pf.mean()), cv_P_worst=float(pf.max()),
                    notes='v7: v6 + Tmin 96h window + co2 order stats'), OUT + 'experiments2.jsonl')
print(f'\n{time.time()-t0:.0f}s  logged.')
