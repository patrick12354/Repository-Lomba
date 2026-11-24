"""v8 = v7 + the q05 quantile block (air_temperature 18/48/96 h, co2 18/48 h) + huber
alpha retuned 4 -> 2.  Reuses the stored v7 OOF so the head-to-head compares against the
exact configuration that scored 3.31582, then refits on all training data and writes the
submission.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

NAME = 'v8_qblock'
SEEDS = (0, 1, 2)
FIT_SEEDS = (0, 1, 2, 3, 4)
SHRINK = 0.25
MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
is_te = pd.Series((g.is_test == 1).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
IDX = g.index
tr = is_tr & y.notna()
T = c['air_temperature']
ESt = pd.Series(es(T.values), index=IDX)
E = y * ESt / 100.0


def qblock(c, wins, q, col='air_temperature', rh=True):
    s = c[col]; d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = s.rolling(w, center=True, min_periods=6).quantile(q)
        hi = s.rolling(w, center=True, min_periods=6).quantile(1 - q)
        d[f'{col}_q{hrs}'] = lo; d[f'{col}_qhi{hrs}'] = hi
        d[f'{col}_qrng{hrs}'] = hi - lo; d[f'{col}_minus_q{hrs}'] = s - lo
        if rh:
            d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(c['air_temperature'].values)
    return pd.DataFrame(d, index=c.index)


F = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
               qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
F = F.replace([np.inf, -np.inf], np.nan)
print(f'v8 features {F.shape[1]}  train {int(tr.sum())}  test {int(is_te.sum())}', flush=True)

KW = dict(objective='huber', alpha=2.0, n_estimators=900, learning_rate=0.03, num_leaves=15,
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
OOF = pickle.load(open('outputs/v7_oof.pkl', 'rb'))
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
    OOF[('v8', fam)] = pd.concat(per, ignore_index=True)
    print(f'  OOF v8/{fam} done ({time.time()-t0:.0f}s)', flush=True)
pickle.dump(OOF, open('outputs/v8_oof.pkl', 'wb'))


def nested_pred(O, models, shrink=SHRINK):
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


CAND = {'v7_airmass': ('v7', MS), 'v8_qblock': ('v8', MS)}
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

print('\n### PAIRED DAY-LEVEL BOOTSTRAP, v8 vs v7 (4000 resamples) ###', flush=True)
rng = np.random.default_rng(0)
for fam in FAM:
    A = SC[('v7_airmass', fam)].copy(); A['day'] = A.dt.dt.date
    B = SC[('v8_qblock', fam)]
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
    print(f'  {fam}: pooled {rmse(M.y, M.p_b):.3f} vs {rmse(M.y, M.p_a):.3f} '
          f'(delta {rmse(M.y, M.p_b)-rmse(M.y, M.p_a):+.3f})  folds {int((fb<fa).sum())}/{len(fa)}  '
          f'days {float((dsq.sb<dsq.sa).mean())*100:.1f}%  CI [{lo:+.3f},{hi:+.3f}]  '
          f'P(better) {(boot<0).mean()*100:.1f}%', flush=True)

print('\nrefit on all training data...', flush=True)
O = OOF[('v8', 'P')]
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
assert list(sub.columns) == list(ss.columns) and len(sub) == len(ss)
assert (sub.datetime.values == ss.datetime.values).all() and sub.air_humidity.notna().all()
sub.to_csv(f'outputs/submissions/{NAME}.csv', index=False)
Pt.to_csv(f'outputs/testpreds_{NAME}.csv')
print(f'\nwrote outputs/submissions/{NAME}.csv (validated)', flush=True)
print('pred:', {k: round(v, 2) for k, v in sub.air_humidity.describe().to_dict().items()})
old = pd.read_csv('outputs/submissions/v7_airmass.csv')
print(f'RMSE between v8 and v7 prediction vectors: {rmse(sub.air_humidity, old.air_humidity):.3f}')
log_experiment(dict(name=NAME, cv_P=float(pf.mean()), cv_P_worst=float(pf.max()),
                    weights={m: round(float(x), 4) for m, x in zip(MS, w)},
                    n_feats=int(F.shape[1]),
                    notes='v7 + q05 block (air_temp 18/48/96, co2 18/48) + huber alpha 4->2'),
                OUT + 'experiments2.jsonl')
print('logged.')
