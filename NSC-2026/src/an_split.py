"""Is the far 70% of the test window a different animal from the near 30%?

Everything measured on the leaderboard so far is the public slice. If the split is
temporal, that is rows 0-219 (29 Aug 15:00 -> 3 Sep 04:30) and the private slice is rows
220-733 (3 Sep -> 13 Sep). This asks whether the model's *inputs* drift further out over
that second stretch, and whether its predictions do anything odd there.
"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
import final_pipeline as FP

g = FP.load_grid()
F = FP.make_features(g)
is_te = (g.is_test == 1).values
is_tr = (g.is_test == 0).values & g[FP.TARGET].notna().values
IDX = g.index
te_idx = IDX[is_te]
K = 220                                    # 30% of 734
nearm = np.zeros(len(te_idx), bool); nearm[:K] = True

Xtr = F[is_tr]
Xte = F[is_te]
print('features: %d   train rows %d   test rows %d' % (F.shape[1], is_tr.sum(), is_te.sum()))
print('test near : %s -> %s' % (te_idx[0], te_idx[K - 1]))
print('test far  : %s -> %s' % (te_idx[K], te_idx[-1]))

# ---------- 1. coverage: fraction of test values inside the train 1-99% band ----------
lo = Xtr.quantile(0.01); hi = Xtr.quantile(0.99)
inside = ((Xte >= lo) & (Xte <= hi))
cov_n = inside[nearm].mean(); cov_f = inside[~nearm].mean()
D = pd.DataFrame(dict(near=cov_n, far=cov_f))
D['drop'] = D.near - D.far
print('\nmean coverage: near %.4f   far %.4f' % (cov_n.mean(), cov_f.mean()))
print('\nfeatures whose training support collapses MOST in the far slice:')
print(D.sort_values('drop', ascending=False).head(15).round(3).to_string())
print('\nfeatures with the worst FAR coverage outright:')
print(D.sort_values('far').head(15).round(3).to_string())
print('\ncount of features with far coverage < 0.5: %d   near < 0.5: %d'
      % ((D.far < 0.5).sum(), (D.near < 0.5).sum()))

# ---------- 2. adversarial AUC: train vs near-test, and train vs far-test ----------
import lightgbm as lgb
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score

def adv(mask):
    Xa = pd.concat([Xtr, Xte[mask]]); ya = np.r_[np.zeros(len(Xtr)), np.ones(mask.sum())]
    m = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.05, num_leaves=15, verbose=-1,
                           random_state=0)
    p = cross_val_predict(m, Xa, ya, cv=4, method='predict_proba')[:, 1]
    return roc_auc_score(ya, p)

print('\nadversarial AUC  train vs near-test: %.4f' % adv(nearm))
print('adversarial AUC  train vs far-test : %.4f' % adv(~nearm))
# near vs far directly
Xa = pd.concat([Xte[nearm], Xte[~nearm]]); ya = np.r_[np.zeros(K), np.ones((~nearm).sum())]
m = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.05, num_leaves=15, verbose=-1,
                       random_state=0)
p = cross_val_predict(m, Xa, ya, cv=4, method='predict_proba')[:, 1]
print('adversarial AUC  near-test vs far-test: %.4f' % roc_auc_score(ya, p))

# ---------- 3. raw regime: what the weather is doing ----------
raw = g.loc[:, ['air_temperature', 'co2', 'pressure', FP.TARGET]].copy()
raw['seg'] = np.where(is_tr, 'train', np.where(np.r_[np.zeros(is_tr.sum(), bool), nearm],
                                               'test_near', 'test_far'))
print('\n=== regime by segment (raw sensors) ===')
print(raw.groupby('seg').agg(['mean', 'std', 'min', 'max'])['air_temperature'].round(2).to_string())
print()
for col in ['co2', 'pressure']:
    print(col, raw.groupby('seg')[col].agg(['mean', 'std']).round(2).to_dict('index'))

# daily amplitude of air_temperature -- this is what drives RH variance
d = pd.DataFrame({'T': g.air_temperature, 'seg': raw.seg}, index=IDX)
amp = d.groupby([d.index.floor('D'), 'seg']).T.agg(lambda s: s.max() - s.min()).reset_index()
print('\ndaily air_temperature amplitude (drives RH swing):')
print(amp.groupby('seg').T.agg(['mean', 'std', 'count']).round(2).to_string())

# ---------- 4. what the submission predicts on each slice ----------
sub = pd.read_csv('outputs/submissions/v8_qblock.csv').air_humidity.values
print('\n=== v8 predictions ===')
print('near: mean %.2f std %.2f  min %.2f max %.2f' % (sub[:K].mean(), sub[:K].std(), sub[:K].min(), sub[:K].max()))
print('far : mean %.2f std %.2f  min %.2f max %.2f' % (sub[K:].mean(), sub[K:].std(), sub[K:].min(), sub[K:].max()))
ytr = g.loc[is_tr, FP.TARGET]
print('train y: mean %.2f std %.2f' % (ytr.mean(), ytr.std()))
