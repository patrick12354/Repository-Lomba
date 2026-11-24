"""v9 = v8 with the dispersion correction (expand about the prediction mean, s = 1.05).

No model changes, so nothing is refitted: the v8 out-of-fold matrix and the stored v8
per-model test predictions are exact inputs. The expansion centre is the mean of the
prediction set being expanded -- per fold in CV, over the 734 test rows at test time --
which is the protocol validated in exp26.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from scipy.optimize import nnls

NAME = 'v9_disp'
S = 1.05
SHRINK = 0.25
MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
FAMS = ['P', 'Q', 'R']
OOF = pickle.load(open('outputs/v8_oof.pkl', 'rb'))


def nested(O, shrink=SHRINK):
    out = []
    for k in sorted(O.fold.unique()):
        prev, cur = O[O.fold < k], O[O.fold == k].copy()
        if len(prev) < 200:
            continue
        w, _ = nnls(prev[MS].values, prev.y.values)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(MS)) / len(MS)
        w = (1 - shrink) * w + shrink * np.ones(len(MS)) / len(MS)
        cur['p'] = cur[MS].values @ w
        out.append(cur)
    return pd.concat(out, ignore_index=True)


def expand(D, s=S):
    D = D.copy()
    out = []
    for k, d in D.groupby('fold'):
        d = d.copy(); m = d.p.mean()
        d['p'] = np.clip(m + s * (d.p - m), 5, 100)
        out.append(d)
    return pd.concat(out, ignore_index=True)


print(f'{"config":12s} ' + ' '.join(f'{f}mean {f}wst ' for f in FAMS) + '   avg  avgWst')
SC = {}
for nm, fn in [('v8_qblock', lambda O: nested(O)), ('v9_disp', lambda O: expand(nested(O)))]:
    row = []
    for fam in FAMS:
        L = fn(OOF[('v8', fam)])
        pf = L.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        row.append((float(pf.mean()), float(pf.max())))
        SC[(nm, fam)] = L
    print(f'{nm:12s} ' + ' '.join(f'{m:6.3f} {w:6.3f}' for m, w in row) +
          f' {np.mean([r[0] for r in row]):7.3f} {np.mean([r[1] for r in row]):7.3f}', flush=True)

print('\n### PAIRED DAY-LEVEL BOOTSTRAP, v9 vs v8 (4000 resamples) ###', flush=True)
rng = np.random.default_rng(0)
for fam in FAMS:
    A = SC[('v8_qblock', fam)].copy(); A['day'] = A.dt.dt.date
    B = SC[('v9_disp', fam)]
    M = A[['fold', 'dt', 'y', 'p', 'day']].merge(B[['fold', 'dt', 'p']], on=['fold', 'dt'],
                                                 suffixes=('_a', '_b'))
    fa = M.groupby('fold').apply(lambda d: rmse(d.y, d.p_a))
    fb = M.groupby('fold').apply(lambda d: rmse(d.y, d.p_b))
    dsq = M.assign(sa=(M.p_a - M.y) ** 2, sb=(M.p_b - M.y) ** 2).groupby('day')[['sa', 'sb']].mean()
    days = dsq.index.values
    boot = []
    for _ in range(4000):
        s_ = dsq.loc[rng.choice(days, len(days), replace=True)]
        boot.append(np.sqrt(s_.sb.mean()) - np.sqrt(s_.sa.mean()))
    boot = np.array(boot)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f'  {fam}: pooled {rmse(M.y, M.p_b):.3f} vs {rmse(M.y, M.p_a):.3f} '
          f'(delta {rmse(M.y, M.p_b)-rmse(M.y, M.p_a):+.3f})  folds {int((fb<fa).sum())}/{len(fa)}  '
          f'days {float((dsq.sb<dsq.sa).mean())*100:.1f}%  CI [{lo:+.3f},{hi:+.3f}]  '
          f'P(better) {(boot<0).mean()*100:.1f}%', flush=True)

# ---- test-set predictions -------------------------------------------------------
O = OOF[('v8', 'P')]
w, _ = nnls(O[MS].values, O.y.values)
w = w / w.sum() if w.sum() > 0 else np.ones(len(MS)) / len(MS)
w = (1 - SHRINK) * w + SHRINK * np.ones(len(MS)) / len(MS)
print('\nweights:', {m: round(float(x), 4) for m, x in zip(MS, w)}, flush=True)
pf = O.groupby('fold').apply(lambda d: rmse(d.y, d[MS].values @ w))
Oe = expand(O.assign(p=O[MS].values @ w))
pfe = Oe.groupby('fold').apply(lambda d: rmse(d.y, d.p))
print(f'family-P CV (pooled weights): v8 mean {pf.mean():.4f} worst {pf.max():.4f}', flush=True)
print(f'                              v9 mean {pfe.mean():.4f} worst {pfe.max():.4f} '
      f'{[round(x,3) for x in pfe.values]}', flush=True)

Pt = pd.read_csv('outputs/testpreds_v8_qblock.csv', index_col=0)
pred8 = np.clip(Pt[MS].values @ w, 5, 100)
m = pred8.mean()
pred9 = np.clip(m + S * (pred8 - m), 5, 100)
print(f'\ntest predictions: mean {m:.3f}  std before {pred8.std():.3f} -> after {pred9.std():.3f}')

te = pd.read_csv(D + 'test.csv', parse_dates=['datetime'])
sub = pd.DataFrame({'datetime': te.datetime.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'air_humidity': pred9})
ss = pd.read_csv(D + 'sample_submission.csv')
assert list(sub.columns) == list(ss.columns) and len(sub) == len(ss)
assert (sub.datetime.values == ss.datetime.values).all() and sub.air_humidity.notna().all()
sub.to_csv(f'outputs/submissions/{NAME}.csv', index=False)
print(f'wrote outputs/submissions/{NAME}.csv (validated)')
print('pred:', {k: round(v, 2) for k, v in sub.air_humidity.describe().to_dict().items()})
old = pd.read_csv('outputs/submissions/v8_qblock.csv')
print(f'RMSE between v9 and v8 prediction vectors: {rmse(sub.air_humidity, old.air_humidity):.3f}')
log_experiment(dict(name=NAME, cv_P=float(pfe.mean()), cv_P_worst=float(pfe.max()),
                    expansion=S, notes='v8 + dispersion expansion s=1.05 about the prediction mean'),
               OUT + 'experiments2.jsonl')
print('logged.')
