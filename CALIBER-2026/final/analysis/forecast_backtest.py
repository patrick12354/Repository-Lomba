"""Out-of-time backtest of spare-part demand forecasting methods.
Run from repo root:  py analysis/forecast_backtest.py
Fit window : 2025-05-06 .. 2026-02-28  (includes the Nov-Jan shutdown spike)
Test window: 2026-03-01 .. 2026-09-30  (7 months, never seen)
Universe   : every BoM material (7,481), including parts with no history (cold start).
"""
import sys, re
sys.path.insert(0, 'analysis')
from build_mat import build
import pandas as pd, numpy as np
from scipy.stats import poisson
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

m, (bom, fl, mp, mv, nt, pp, p), _ = build()
mv = mv.copy(); mv['otype'] = mv.Order.astype(str).str[:4]
EVENT = {'2030', '2090'}            # campaign / shutdown-type orders (spike Nov-Dec 2025, Jul-Aug 2025)
START = pd.Timestamp('2025-05-01')

def window(a, b):
    return mv[(mv['Posting Date'] >= a) & (mv['Posting Date'] < b)]

def features(cut, months_back):
    """Features for every material using only data before `cut`."""
    a = START; w = window(a, cut); mo = months_back
    f = m[['Material No', 'n_fl', 'inst', 'crit_r', 'cat', 'mrp', 'stock', 'mn', 'mx', 'unit']].copy().set_index('Material No')
    g = w.groupby('Material Number')
    f['qty'] = g.Quantity.sum(); f['lines'] = g.size(); f['n_ord'] = g.Order.nunique()
    base = w[~w.otype.isin(EVENT)].groupby('Material Number')
    f['qty_base'] = base.Quantity.sum(); f['lines_base'] = base.size()
    f['qty_evt'] = w[w.otype.isin(EVENT)].groupby('Material Number').Quantity.sum()
    f['recency'] = (cut - g['Posting Date'].max()).dt.days
    f['size_med'] = g.Quantity.median()
    wm = w.assign(ym=w['Posting Date'].dt.to_period('M')).groupby(['Material Number', 'ym']).size().unstack(fill_value=0)
    f['act_months'] = (wm > 0).sum(axis=1)
    f = f.fillna({'qty': 0, 'lines': 0, 'n_ord': 0, 'qty_base': 0, 'lines_base': 0, 'qty_evt': 0, 'act_months': 0, 'recency': 999})
    # failure history on the FuncLocs where the part is installed
    n_ = nt[(nt['Notification Date'] >= a) & (nt['Notification Date'] < cut)]
    fln = n_.groupby('Functional Location').size(); fle = n_[n_['Notification Type'] == 'N2'].groupby('Functional Location').size()
    b = bom[['Functional Loc.', 'Material No']].drop_duplicates()
    b['nn'] = b['Functional Loc.'].map(fln).fillna(0); b['ne'] = b['Functional Loc.'].map(fle).fillna(0)
    f['fl_notif'] = b.groupby('Material No').nn.sum(); f['fl_emerg'] = b.groupby('Material No').ne.sum()
    # planned maintenance population on its FuncLocs
    b['npm'] = b['Functional Loc.'].map(mp.groupby('Functional Location').size()).fillna(0)
    f['fl_pm'] = b.groupby('Material No').npm.sum()
    # procurement history
    q = p[p['PR-Date'] < cut].groupby('PR-Material')
    f['n_pr'] = q.size(); f['pr_qty'] = q['PR-Quantity'].sum(); f['lt_med'] = q.lt_days.median()
    f[['n_pr', 'pr_qty']] = f[['n_pr', 'pr_qty']].fillna(0)
    f['mo'] = mo
    return f

def target(a, b):
    return window(a, b).groupby('Material Number').Quantity.sum()

# ---------- classic per-item methods ----------
def monthly(cut):
    w = window(START, cut).assign(ym=lambda d: d['Posting Date'].dt.to_period('M'))
    M = w.groupby(['Material Number', 'ym']).Quantity.sum().unstack(fill_value=0)
    allm = pd.period_range(START, cut - pd.Timedelta(days=1), freq='M')
    return M.reindex(columns=allm, fill_value=0)

def sba(y, a=0.1):
    z = p_ = None; q = 1
    for v in y:
        if v > 0:
            if z is None: z, p_ = v, q
            else: z = z + a * (v - z); p_ = p_ + a * (q - p_)
            q = 1
        else: q += 1
    return 0.0 if z is None else (1 - a / 2) * z / p_

def tsb(y, a=0.1, b=0.1):
    nz = [v for v in y if v > 0]
    if not nz: return 0.0
    z = nz[0]; pr = len(nz) / len(y)
    for v in y:
        if v > 0: z = z + a * (v - z); pr = pr + b * (1 - pr)
        else: pr = pr + b * (0 - pr)
    return pr * z

# ---------- run ----------
CUT = pd.Timestamp('2026-03-01'); END = pd.Timestamp('2026-10-01'); H = 7
fit_mo = (CUT - START).days / 30.44
F = features(CUT, fit_mo)
y = target(CUT, END).reindex(F.index).fillna(0)
M = monthly(CUT).reindex(F.index).fillna(0)

pred = pd.DataFrame(index=F.index)
pred['zero'] = 0.0
pred['naive_mean'] = F.qty / fit_mo * H
pred['sba'] = M.apply(lambda r: sba(r.values), axis=1) * H
pred['tsb'] = M.apply(lambda r: tsb(r.values), axis=1) * H
pred['cleansed_mean'] = F.qty_base / fit_mo * H

# Empirical-Bayes installed-base model: issue-events ~ Poisson(rate * installed_units * months)
# prior rate pooled per category (gamma), shrink each item's own history toward it.
ev = F.lines_base; expo = F.inst.clip(lower=1) * fit_mo
cat = F.cat.where(F.cat.map(F.cat.value_counts()) >= 30, 'OTHER')
cr = (ev.groupby(cat).sum() / expo.groupby(cat).sum())
prior_rate = cat.map(cr)
k = 2.0                                       # prior strength in "pseudo-events"
beta = k / prior_rate.clip(lower=1e-6)
rate = (k + ev) / (beta + expo)
size = F.size_med.fillna(F.groupby(cat).size_med.transform('median')).fillna(1)
pred['eb_installed'] = rate * F.inst.clip(lower=1) * H * size

# Two-part LightGBM trained on an EARLIER cut (features < 2025-10-01, target Oct-25..Feb-26),
# then applied at CUT. Pure out-of-time.
C0 = pd.Timestamp('2025-10-01'); H0 = (CUT - C0).days / 30.44
F0 = features(C0, (C0 - START).days / 30.44); y0 = target(C0, CUT).reindex(F0.index).fillna(0) / H0
# NOTE: current 'stock' is a snapshot taken AFTER the test window -> leakage, excluded.
X_cols = ['n_fl', 'inst', 'crit_r', 'mn', 'mx', 'qty', 'lines', 'n_ord', 'qty_base', 'lines_base', 'qty_evt',
          'recency', 'size_med', 'act_months', 'fl_notif', 'fl_emerg', 'fl_pm', 'n_pr', 'pr_qty', 'lt_med', 'mo']
def prep(f):
    X = f[X_cols].copy()
    for c in ['qty', 'lines', 'n_ord', 'qty_base', 'lines_base', 'qty_evt', 'n_pr', 'pr_qty', 'fl_notif', 'fl_emerg']:
        X[c] = X[c] / f.mo                    # per-month rates so different window lengths are comparable
    X['cat'] = f.cat.astype('category'); X['mrp'] = (f.mrp == 'Stock Item').astype(int)
    return X
X0, X1 = prep(F0), prep(F)
X1['cat'] = pd.Categorical(X1['cat'], categories=X0['cat'].cat.categories)
clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=30, verbose=-1)
clf.fit(X0, (y0 > 0).astype(int))
pos = y0 > 0
reg = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=20, objective='poisson', verbose=-1)
reg.fit(X0[pos], y0[pos])
p_move = pd.Series(clf.predict_proba(X1)[:, 1], index=F.index)
pred['lgbm_2part'] = p_move * reg.predict(X1) * H

# HYBRID (our engine): LightGBM decides WHO will move (uses failure history, PM population,
# installed base, category, procurement); Empirical-Bayes installed-base model decides HOW MUCH.
lam = (rate * F.inst.clip(lower=1) * H).clip(lower=1e-9)          # expected issue events in horizon
cond_events = lam / (1 - np.exp(-lam))                              # E[events | at least one]
pred['hybrid'] = p_move * cond_events * size

# ---------- evaluation ----------
moved = (y > 0).astype(int)
print(f'Universe {len(y)} materials | moved in test {moved.sum()} | of which NO history in fit window {int(((F.qty == 0) & (y > 0)).sum())}')
rows = []
for c in pred:
    e = pred[c]
    auc = roc_auc_score(moved, e + 1e-9 * F.inst) if c != 'zero' else 0.5
    top = e.rank(ascending=False, method='first') <= moved.sum()
    rows.append(dict(method=c, AUC_who_moves=round(auc, 3), recall_topK=round((top & (moved == 1)).sum() / moved.sum(), 3),
                     MAE=round((e - y).abs().mean(), 2), total_bias=round(e.sum() / y.sum() - 1, 3)))
res = pd.DataFrame(rows).set_index('method'); print(res.to_string())

cold = F.qty == 0
print(f'\nCold-start materials (no history): {cold.sum()} | moved in test {int(moved[cold].sum())}')
for c in ['naive_mean', 'sba', 'eb_installed', 'lgbm_2part', 'hybrid']:
    e = pred[c][cold]
    print(f'  {c:14s} AUC on cold-start = {roc_auc_score(moved[cold], e + 1e-9 * F.inst[cold]):.3f}' if e.std() > 0 or c != 'naive_mean' else f'  {c:14s} AUC on cold-start = 0.500 (predicts 0 for all)')

# Inventory-relevant test: stock each part at the q-quantile of a Poisson(event) x size distribution
print('\nStocking trade-off (hold q-quantile of forecast over 7 months; service = parts whose test demand fully covered, among movers)')
def zt_quantile(qq, lam_):
    # quantile of zero-truncated Poisson
    p0 = np.exp(-lam_); target_ = p0 + qq * (1 - p0)
    return np.maximum(poisson.ppf(np.clip(target_, 0, 1 - 1e-12), lam_), 1)
for c in ['naive_mean', 'sba', 'cleansed_mean', 'eb_installed', 'lgbm_2part', 'hybrid']:
    for q in [0.8, 0.9, 0.95]:
        if c == 'hybrid':
            qq = (q - (1 - p_move)) / p_move
            hold = np.where(qq > 0, zt_quantile(qq.clip(0, 1), lam), 0) * size
        else:
            lam_ = (pred[c] / size).clip(lower=0)
            hold = poisson.ppf(q, lam_) * size
        cov = ((hold >= y) & (moved == 1)).sum() / moved.sum()
        print(f'  {c:14s} q={q:.2f}  units held={hold.sum():>10,.0f}  movers fully covered={cov:.3f}')
print('  actual test demand units =', f'{y.sum():,.0f}')

imp = pd.Series(clf.feature_importances_, index=X0.columns).sort_values(ascending=False)
print('\nLGBM who-moves feature importance (split count):', imp.head(10).to_dict())
pred.assign(actual=y).to_csv('analysis/backtest_predictions.csv')
