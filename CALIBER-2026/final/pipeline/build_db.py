"""Build app/data/partpulse.db from the six Excel files (contract: docs/tasks/00_TEAM_PLAN.md).
Run from repo root:  py pipeline/build_db.py     (mac/linux: .venv/bin/python pipeline/build_db.py)
Rebuilds the db from scratch every run and prints the control numbers.
"""
import sys, os, re, json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT); sys.path.insert(0, str(ROOT / 'analysis'))
from build_mat import build
import pandas as pd, numpy as np
from scipy.stats import norm
from sklearn.metrics import roc_auc_score
import lightgbm as lgb
sys.path.insert(0, str(ROOT / 'pipeline'))
from domain_features import DomainFeatures

DB = Path(os.environ.get('PARTPULSE_DB', ROOT / 'app' / 'data' / 'partpulse.db'))   # override to build beside a database a running server holds open
AS_OF = pd.Timestamp('2026-09-30'); END = AS_OF + pd.Timedelta(days=1)
START = pd.Timestamp('2025-05-01')
H = 180                                            # forecast horizon, days
HM = H / 30.44                                     # ... in months
EVENT = {'2030', '2090'}                           # shutdown / campaign order types
NEXT_TA = pd.Timestamp('2027-06-01')            # planning assumption (scope final §4): ~20 months after the last TA; editable in app
TA_WINDOW = 30                                  # a TA order-by date inside this many days -> REORDER now
SL = {'A': .95, 'B': .90, 'C': .85, 'S': .80}         # lean policy, the recommendation: replay shows less stock and 95% A/B fill. Order A>B>C>S (committee, TM 4 Nov)
DT_COST = {'A': 100, 'B': 30, 'C': 5, 'S': 1}      # downtime cost per day, relative index (not IDR)
HOLD = 0.25; ORDER_COST = 500_000; BASE_SCALE = 1.0; TA_SCALE = 1.0; TA_BUFFER = 14; P_LOW = 0.3; NSIM = 2000
rng = np.random.default_rng(7)

META = {
    'as_of_date': AS_OF.date().isoformat(), 'data_window': '2025-05-06..2026-09-30',
    'holding_rate': HOLD, **{f'service_level_{k}': v for k, v in SL.items()},
    **{f'downtime_cost_per_day_{k}': v for k, v in DT_COST.items()},
    'downtime_cost_unit': 'relative index per day (no downtime cost in data; slider in app)',
    'downtime_days_if_stockout': 'lt_p50 of the material',
    'ta_last_window': '2025-11-01..2026-01-31', 'next_ta_default': NEXT_TA.date().isoformat(), 'next_ta_note': 'planning assumption, editable (not an official schedule)',
    'ta_order_window_days': TA_WINDOW,
    'ta_scale': TA_SCALE, 'ta_buffer_days': TA_BUFFER, 'forecast_horizon_days': H,
    'order_cost_idr': ORDER_COST, 'base_demand_scale': BASE_SCALE,
    'criticality_order': 'A > B > C > S (A highest; S = special, lowest)',
    'insurance_floor': 'A-critical Stock Items keep max_new >= 1', 'p_move_low_threshold': P_LOW,
    'price_rule': 'PO-Item Amount is a UNIT price (IDR lines only); value = price x qty',
    'lead_time_rule': 'PR-Date -> PO-Delivery Date, negative dropped; fallback material -> category -> global',
    'consumption_months': '2025-05..2026-09 (consumption_monthly is sparse; missing month = 0)',
    'assumption_fields': json.dumps({'materials.unit_price': 'assumption when price_source = category_estimate',
        'downtime_cost_per_day_*': 'assumption (relative index, not in data)', 'next_ta_default': 'planning assumption',
        'holding_rate': 'assumption', 'order_cost_idr': 'assumption'}),
    'frontier_note': 'current/optimized/lean share the new lot size Q, so points differ only by reorder level; n_parts_funded = parts given safety stock beyond the frontier origin',
    'risk_cost_unit': 'same relative index as downtime_cost_per_day',
}

m, (bom, fl, mp, mv, nt, pp, p), _ = build()
mv = mv.copy(); mv['ot'] = mv.Order.astype(str).str[:4]
mv['cat'] = mv['Material Descriptions'].str.split(',').str[0]
st = m.set_index('Material No')

# =====================================================================  P0: materials
mat = pd.DataFrame(index=st.index); mat.index.name = 'material_no'
mat['description'] = st.desc; mat['category'] = st.cat; mat['unit'] = st.unit; mat['mrp_type'] = st.mrp
mat['criticality'] = st.crit; mat['n_funcloc'] = st.n_fl; mat['installed_qty'] = st.inst
mat['stock'] = st.stock; mat['min_cur'] = st.mn; mat['max_cur'] = st.mx

# price: own IDR PO median -> median of category x unit -> median of category
mat['unit_price'] = st.px; mat['price_source'] = np.where(st.px.notna(), 'po', None)
for keys in (['category', 'unit'], ['category']):
    est = mat.groupby(keys).unit_price.transform(lambda s: s.median() if s.notna().sum() >= 2 else np.nan)
    fill = mat.unit_price.isna() & est.notna()
    mat.loc[fill, 'unit_price'] = est[fill]; mat.loc[fill, 'price_source'] = 'category_estimate'
mat['price_source'] = mat.price_source.fillna('none')
mat['stock_value'] = mat.stock * mat.unit_price.fillna(0)

# lead time: material -> category -> global
q = p[p.lt_days >= 0].copy(); q['cat'] = q['PR-Material Desc'].str.split(',').str[0]
p90 = lambda s: s.quantile(.9)
lm = q.groupby('PR-Material').lt_days.agg(n='size', p50='median', p90=p90, sd='std')
lc = q.groupby('cat').lt_days.agg(n='size', p50='median', p90=p90, mean='mean', sd='std')
lc['cv'] = lc.sd / lc['mean']
g50, g90, gcv = q.lt_days.median(), q.lt_days.quantile(.9), q.lt_days.std() / q.lt_days.mean()
own = lm.reindex(mat.index); catl = lc.reindex(mat.category).set_index(mat.index)
has_cat = catl.n.fillna(0) >= 5
mat['lt_p50'] = own.p50.fillna(catl.p50.where(has_cat)).fillna(g50)
mat['lt_p90'] = own.p90.fillna(catl.p90.where(has_cat)).fillna(g90)
mat['lt_source'] = np.select([own.p50.notna(), has_cat], ['material', 'category'], 'global')
lt_n = own.n.fillna(0)
lt_sd = own.sd.where(lt_n >= 3, mat.lt_p50 * catl.cv.where(has_cat).fillna(gcv)).fillna(0)
mat['main_supplier'] = q.groupby('PR-Material')['PO-Supplier Name'].agg(lambda s: s.mode().iat[0]).reindex(mat.index)

# consumption + Syntetos-Boylan class over the full window
mv['ym'] = mv['Posting Date'].dt.to_period('M')
def sb_class(w):
    M = w.groupby(['Material Number', 'ym']).Quantity.sum().unstack(fill_value=0)
    nz = (M > 0).sum(axis=1); adi = M.shape[1] / nz.clip(lower=1)
    cv2 = M.apply(lambda r: (r[r > 0].std(ddof=0) / r[r > 0].mean()) ** 2 if (r > 0).sum() > 1 else np.nan, axis=1)
    c = np.select([nz <= 1, (adi < 1.32) & (cv2 < .49), (adi >= 1.32) & (cv2 < .49), (adi < 1.32) & (cv2 >= .49)],
                  ['single', 'smooth', 'intermittent', 'erratic'], 'lumpy')
    return pd.Series(c, index=M.index), nz
cls_all, nz_all = sb_class(mv)
mat['qty_issued_17m'] = st.qty; mat['months_active'] = nz_all.reindex(mat.index).fillna(0).astype(int)
mat['last_issue'] = st['last'].dt.strftime('%Y-%m-%d')
mat['demand_class'] = cls_all.reindex(mat.index).fillna('none')

# health
active_fl = set(mp['Functional Location']) | set(nt['Functional Location'])
b = bom[['Functional Loc.', 'Material No']].drop_duplicates()
fl_active = b.assign(a=b['Functional Loc.'].isin(active_fl)).groupby('Material No').a.any().reindex(mat.index).fillna(False).astype(bool)
used = mat.qty_issued_17m > 0
mat['health'] = np.select(
    [(mat.stock == 0) & used, ~used & (mat.stock > 0) & ~fl_active, ~used & (mat.stock > 0),
     mat.stock < mat.min_cur, mat.stock > mat.max_cur],
    ['STOCKOUT', 'OBSOLETE_CANDIDATE', 'NON_MOVING', 'BELOW_MIN', 'OVER_MAX'], 'OK')

# =====================================================================  P0: ta_kit (E1 replay)
ta = mv[(mv.ot == '2030') & (mv['Posting Date'] >= '2025-11-01') & (mv['Posting Date'] < '2026-02-01')]
kit = st.join(ta.groupby('Material Number').Quantity.sum().rename('ta_qty_last'), how='inner')
ta_kit = pd.DataFrame({'ta_qty_last': kit.ta_qty_last, 'stock': kit.stock})
ta_kit['gap'] = (ta_kit.ta_qty_last - ta_kit.stock).clip(lower=0)
ta_kit['gap_value'] = ta_kit.gap * mat.unit_price.reindex(ta_kit.index).fillna(0)
ta_kit['exceeds_max'] = (kit.ta_qty_last > kit.mx).astype(int)
ta_kit['lt_p90'] = mat.lt_p90.reindex(ta_kit.index); ta_kit['criticality'] = kit.crit
ta_kit.index.name = 'material_no'

# =====================================================================  P2 (needed by policy): twins + trust
mat['_key'] = mat.description.map(lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper()))
dup = mat[mat._key.map(mat._key.value_counts()) > 1]
gid = {k: i + 1 for i, k in enumerate(sorted(dup._key.unique()))}
twins = pd.DataFrame({'group_id': dup._key.map(gid), 'material_no': dup.index,
                      'role': np.select([(dup.stock < dup.min_cur) | ((dup.stock == 0) & (dup.qty_issued_17m > 0)),
                                         dup.stock > dup.max_cur], ['SHORT', 'DONOR'], 'OTHER')})
tw_groups = twins.groupby('group_id').role.agg(lambda r: {'SHORT', 'DONOR'} <= set(r))
# ledger (E5): opening stock implied by walking issues/receipts back from the snapshot must be >= 0
lmats = set(mv['Material Number']) & set(p['PR-Material'])
iss = mv[mv['Material Number'].isin(lmats)].groupby('Material Number').Quantity.sum()
rcv = p[p['PR-Material'].isin(lmats) & (p['PO-Delivery Date'] <= AS_OF) & (p['PO-Delivery Date'] >= '2025-05-06')].groupby('PR-Material')['PR-Quantity'].sum()
led = pd.concat([iss.rename('iss'), rcv.rename('rcv')], axis=1).fillna(0)
led['start'] = st.stock.reindex(led.index) + led.iss - led.rcv
ledger_bad = (led.start < 0).reindex(mat.index).fillna(False).astype(bool)
flags = pd.DataFrame({'price_po': mat.price_source == 'po', 'lt_3plus': lt_n >= 3,
                      'ledger_ok': ~ledger_bad, 'not_twin': ~mat.index.isin(dup.index)})
mat['trust_score'] = flags.mean(axis=1).round(2)
mat['trust_flags'] = [json.dumps({'price_verified': bool(a), 'lt_samples': int(n_), 'ledger_ok': bool(c), 'has_twin': not bool(d)})
                      for a, n_, c, d in zip(flags.price_po, lt_n, flags.ledger_ok, flags.not_twin)]
mat = mat.drop(columns='_key')

# =====================================================================  P1: forecast (KQ1)
def window(a, b_):
    return mv[(mv['Posting Date'] >= a) & (mv['Posting Date'] < b_)]

def features(cut):
    """Features for every material using only data before `cut` (same spec as analysis/forecast_backtest.py)."""
    w = window(START, cut); mo = (cut - START).days / 30.44
    f = m[['Material No', 'n_fl', 'inst', 'crit_r', 'cat', 'mrp', 'mn', 'mx', 'unit']].copy().set_index('Material No')
    g = w.groupby('Material Number')
    f['qty'] = g.Quantity.sum(); f['lines'] = g.size(); f['n_ord'] = g.Order.nunique()
    base = w[~w.ot.isin(EVENT)].groupby('Material Number')
    f['qty_base'] = base.Quantity.sum(); f['lines_base'] = base.size()
    f['qty_evt'] = w[w.ot.isin(EVENT)].groupby('Material Number').Quantity.sum()
    f['recency'] = (cut - g['Posting Date'].max()).dt.days
    f['size_med'] = g.Quantity.median()
    wm = w.groupby(['Material Number', 'ym']).size().unstack(fill_value=0)
    f['act_months'] = (wm > 0).sum(axis=1)
    f = f.fillna({'qty': 0, 'lines': 0, 'n_ord': 0, 'qty_base': 0, 'lines_base': 0, 'qty_evt': 0, 'act_months': 0, 'recency': 999})
    n_ = nt[(nt['Notification Date'] >= START) & (nt['Notification Date'] < cut)]
    fln = n_.groupby('Functional Location').size(); fle = n_[n_['Notification Type'] == 'N2'].groupby('Functional Location').size()
    bb = b.copy(); bb['nn'] = bb['Functional Loc.'].map(fln).fillna(0); bb['ne'] = bb['Functional Loc.'].map(fle).fillna(0)
    n90 = nt[(nt['Notification Date'] >= cut - pd.Timedelta(days=90)) & (nt['Notification Date'] < cut)].groupby('Functional Location').size()
    bb['n90'] = bb['Functional Loc.'].map(n90).fillna(0)
    f['fl_notif'] = bb.groupby('Material No').nn.sum(); f['fl_emerg'] = bb.groupby('Material No').ne.sum()
    f['fl_notif_90d'] = bb.groupby('Material No').n90.sum()
    bb['npm'] = bb['Functional Loc.'].map(mp.groupby('Functional Location').size()).fillna(0)
    f['fl_pm'] = bb.groupby('Material No').npm.sum()
    qq = p[p['PR-Date'] < cut].groupby('PR-Material')
    f['n_pr'] = qq.size(); f['pr_qty'] = qq['PR-Quantity'].sum(); f['lt_med'] = qq.lt_days.median()
    f[['n_pr', 'pr_qty']] = f[['n_pr', 'pr_qty']].fillna(0)
    w9 = window(cut - pd.Timedelta(days=90), cut); g9 = w9.groupby('Material Number'); b9 = w9[~w9.ot.isin(EVENT)]
    f['qty_90'] = g9.Quantity.sum() / 3; f['lines_90'] = g9.size() / 3; f['base_90'] = b9.groupby('Material Number').Quantity.sum() / 3
    f[['qty_90', 'lines_90', 'base_90']] = f[['qty_90', 'lines_90', 'base_90']].fillna(0)
    f['lvl_90'] = b9.Quantity.sum() / 3 / 1e4      # plant-wide routine level, last 90 days
    f['mo'] = mo
    return f

# Main model uses the planner's current Min/Max/MRP type as inputs (known at forecast time in production).
# They are BoM snapshots read after the validation windows, so the validation also reports a STRICT variant
# without them (backtest rows engine_strict_*); quote both side by side.
SNAP_COLS = ['mn', 'mx']
STRICT_DEFAULT = False
X_cols = ['n_fl', 'inst', 'crit_r', 'mn', 'mx', 'qty', 'lines', 'n_ord', 'qty_base', 'lines_base', 'qty_evt',
          'recency', 'size_med', 'act_months', 'fl_notif', 'fl_emerg', 'fl_pm', 'n_pr', 'pr_qty', 'lt_med', 'mo',
          'qty_90', 'lines_90', 'base_90', 'lvl_90']
RATE = ['qty', 'lines', 'n_ord', 'qty_base', 'lines_base', 'qty_evt', 'n_pr', 'pr_qty', 'fl_notif', 'fl_emerg']
CATS = sorted(m.cat.unique())
def prep(f, strict=None):
    strict = STRICT_DEFAULT if strict is None else strict
    X = f[[c for c in X_cols if not (strict and c in SNAP_COLS)]].copy()
    for c in RATE: X[c] = X[c] / f.mo
    X['cat'] = pd.Categorical(f.cat, categories=CATS)
    if not strict: X['mrp'] = (f.mrp == 'Stock Item').astype(int)
    return X

D90 = 90; HL = 3.0                                  # 90-day training folds; recency half-life in months
def base_target(cut, days=D90):     # non-event units issued in [cut, cut+days)
    w = window(cut, cut + pd.Timedelta(days=days)); return w[~w.ot.isin(EVENT)].groupby('Material Number').Quantity.sum()

_fx = {}
def Xat(cut, strict=None):
    key = (cut, strict)
    if key not in _fx:
        f = features(cut); _fx[key] = (f, prep(f, strict))
    return _fx[key]

def fit(last_cut, strict=None):
    """Stack monthly 90-day folds 2025-06..last_cut (each sees only data before its cut); recent folds weigh more.
    Stacking puts shutdown-season and normal-season windows in the same training set."""
    cuts = pd.date_range('2025-06-01', last_cut, freq='MS')
    X = pd.concat([Xat(c, strict)[1] for c in cuts])
    y = pd.concat([base_target(c).reindex(Xat(c, strict)[1].index).fillna(0) for c in cuts])
    w = np.concatenate([np.full(len(Xat(c, strict)[1]), 0.5 ** ((last_cut - c).days / 30.44 / HL)) for c in cuts])
    clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=30, verbose=-1).fit(X, (y > 0).astype(int), sample_weight=w)
    reg = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=15, min_child_samples=20, objective='tweedie',
                            tweedie_variance_power=1.3, verbose=-1).fit(X, y, sample_weight=w)
    return clf, reg

def forecast_at(clf, reg, cut, days, strict=None):
    """p_move and mean routine demand over `days` from `cut`; mean = 50/50 blend of Tweedie model and last-90d run rate."""
    f, X = Xat(cut, strict); k = days / D90
    p = 1 - (1 - clf.predict_proba(X)[:, 1]) ** k
    w = window(cut - pd.Timedelta(days=D90), cut)
    last = w[~w.ot.isin(EVENT)].groupby('Material Number').Quantity.sum().reindex(f.index).fillna(0).values * k
    model = reg.predict(X) * k
    mean = np.where(last > 0, .5 * model + .5 * last, model)
    return f, X, pd.Series(p, index=f.index), pd.Series(mean, index=f.index), last

def coverage(pv, mean, cut, y, nsim=1000):
    """Share of parts whose actual demand <= simulated q90/q95 (compound Poisson, sizes seen before cut)."""
    h = window(START, cut); h = h[~h.ot.isin(EVENT)]
    so = h.groupby('Material Number').Quantity.apply(np.array); sc = h.groupby('cat').Quantity.apply(np.array)
    r = np.random.default_rng(1); q9 = np.zeros(len(pv)); q95_ = q9.copy(); lam_ = -np.log(1 - np.clip(pv, 0, .995))
    for j, (i, c) in enumerate(zip(m['Material No'], m.cat)):
        if lam_[j] <= 0 or mean[j] <= 0: continue
        sz = so.get(i)
        if sz is None or len(sz) < 3: sz = sc.get(c, np.array([1]))
        sz = sz * (mean[j] / (lam_[j] * sz.mean()))
        N = r.poisson(lam_[j], nsim); t = np.bincount(np.repeat(np.arange(nsim), N), weights=r.choice(sz, N.sum()), minlength=nsim)
        q9[j], q95_[j] = np.quantile(t, [.9, .95])
    mvd = y > 0
    return ((q9 >= y) & mvd).sum() / mvd.sum(), ((q95_ >= y) & mvd).sum() / mvd.sum(), (q95_ >= y).mean(), q95_

# rolling-origin validation: at each origin retrain on folds that ended before it, forecast the next 90 days
def rolling(strict, with_coverage):
    rows_ = []
    for O in pd.date_range('2026-04-01', '2026-07-01', freq='MS'):
        P = O - pd.Timedelta(days=D90); P = pd.Timestamp(P.year, P.month, 1)
        c_, r_ = fit(P, strict)
        f, _, pv, mn_, naive = forecast_at(c_, r_, O, D90, strict)
        y = base_target(O).reindex(f.index).fillna(0).values; mvd = y > 0; cold_ = (f.qty == 0).values
        c90, c95, c95a, q95v = coverage(pv.values, mn_.values, O, y) if with_coverage else (np.nan,) * 3 + (None,)
        px_ = mat.unit_price.reindex(f.index).fillna(0).values; ab_ = mat.criticality.reindex(f.index).isin(['A', 'B']).values
        wv = lambda e: (px_ * np.abs(e - y)).sum() / (px_ * y).sum()          # WAPE weighted by rupiah
        rows_.append(dict(origin=O.date().isoformat(), auc=roc_auc_score(mvd, pv), auc_cold=roc_auc_score(mvd[cold_], pv[cold_]),
                          auc_naive=roc_auc_score(mvd, naive + 1e-9 * f.inst.values), bias=mn_.sum() / y.sum() - 1, bias_naive=naive.sum() / y.sum() - 1,
                          mae=np.abs(mn_.values - y).mean(), mae_naive=np.abs(naive - y).mean(), cov90=c90, cov95=c95, cov95_all=c95a,
                          wape_rp=wv(mn_.values), wape_rp_naive=wv(naive),
                          cov95_AB_movers=((q95v >= y) & mvd & ab_).sum() / (mvd & ab_).sum() if q95v is not None else np.nan))
    return pd.DataFrame(rows_)
val = rolling(STRICT_DEFAULT, True)
val_s = rolling(True, False)                 # strict: no BoM Min/Max/MRP snapshot

# production: folds up to 2026-07 (last 90-day target ends 2026-09-29), forecast 180 days from 2026-10-01
clf, reg = fit(pd.Timestamp('2026-07-01'))
F, X, p_base, base_mean, _ = forecast_at(clf, reg, END, H)
p_base = p_base.reindex(mat.index); base_mean = (base_mean.reindex(mat.index) * BASE_SCALE).clip(lower=0)
ta_in_h = AS_OF < NEXT_TA <= AS_OF + pd.Timedelta(days=H)
event_qty = (ta_kit.ta_qty_last.reindex(mat.index).fillna(0) * TA_SCALE) if ta_in_h else pd.Series(0.0, index=mat.index)
p_move = np.where(event_qty > 0, 1.0, p_base)          # planned shutdown scope = certain use

# drivers: top-3 SHAP contributions of the who-moves model
NICE = {'fl_pm': 'PM items on its FLs', 'fl_notif': 'notifications on its FLs', 'fl_emerg': 'emergency notifs on its FLs',
        'inst': 'installed qty', 'n_fl': 'FLs installed on', 'mn': 'current Min', 'mx': 'current Max', 'recency': 'days since last issue',
        'lt_med': 'median lead time', 'cat': 'category', 'qty': 'units/month issued', 'lines': 'issues/month', 'act_months': 'active months',
        'crit_r': 'criticality', 'n_pr': 'PRs/month', 'pr_qty': 'PR units/month', 'qty_base': 'routine units/month',
        'lines_base': 'routine issues/month', 'qty_evt': 'shutdown units/month', 'n_ord': 'orders/month', 'size_med': 'median issue size',
        'mrp': 'stock item', 'mo': 'months of history', 'qty_90': 'units/month last 90d',
        'lines_90': 'issues/month last 90d', 'base_90': 'routine units/month last 90d', 'lvl_90': 'plant-wide activity level'}
contrib = clf.predict_proba(X, pred_contrib=True)[:, :-1]
cols = list(X.columns); Xr = X.reindex(mat.index); cr = pd.DataFrame(contrib, index=X.index, columns=cols).reindex(mat.index)
F90 = F.fl_notif_90d.reindex(mat.index)
# planner context from the domain layer (not model inputs: they did not add lift in the rolling ablation,
# see docs/04_MODEL_DECISIONS.md) -- shown in the app and in the reason text as upcoming work on the part's equipment
CTX = DomainFeatures(bom, fl, mp, mv, nt, p, EVENT)(END, F.mo.iat[0]).reindex(mat.index)
CTX_COLS = ['pm_due_90', 'pm_major_due_90', 'fl_open_notif', 'open_pr_lines', 'eq_class']
def drv(i):
    top = cr.loc[i].abs().sort_values(ascending=False).index[:3]
    d = {}
    for c in top:
        v = Xr.at[i, c]
        d[c] = v if isinstance(v, str) else (None if pd.isna(v) else round(float(v), 2))
    d['fl_notif_90d'] = int(F90.at[i])
    for c in CTX_COLS:
        v = CTX.at[i, c]; d[c] = v if isinstance(v, str) else int(round(float(v)))
    return json.dumps(d)
drivers = pd.Series({i: drv(i) for i in mat.index})

# compound Poisson simulation: event count ~ Poisson(lambda), size ~ empirical issue sizes (own, else category)
bl = mv[~mv.ot.isin(EVENT)]
own_sizes = bl.groupby('Material Number').Quantity.apply(np.array)
cat_sizes = bl.groupby('cat').Quantity.apply(np.array)
lam_h = -np.log(1 - p_base.clip(upper=.995).values)
L = mat.lt_p50.values.astype(float); sL = lt_sd.values.astype(float)
q50 = np.zeros(len(mat)); q90 = q50.copy(); q95 = q50.copy(); esz2 = q50.copy()
LTD = np.zeros((len(mat), NSIM), dtype=np.float32)
for j, (i, cat) in enumerate(zip(mat.index, mat.category)):
    sz = own_sizes.get(i)
    if sz is None or len(sz) < 3: sz = cat_sizes.get(cat, np.array([1]))
    sz = sz.astype(float); lam = lam_h[j]
    if lam <= 0 or base_mean.iat[j] <= 0: continue
    s = base_mean.iat[j] / (lam * sz.mean()); sz = sz * s; esz2[j] = (sz ** 2).mean()
    def cp(lams):
        N = rng.poisson(lams); tot = N.sum()
        return np.bincount(np.repeat(np.arange(NSIM), N), weights=rng.choice(sz, tot), minlength=NSIM)
    hor = cp(np.full(NSIM, lam))
    q50[j], q90[j], q95[j] = np.quantile(hor, [.5, .9, .95])
    Ls = rng.gamma((L[j] / sL[j]) ** 2, sL[j] ** 2 / L[j], NSIM) if sL[j] > 0 else np.full(NSIM, L[j])
    LTD[j] = cp(lam * Ls / H)

d_day = base_mean.values / H
var_day = lam_h / H * esz2
fc = pd.DataFrame(index=mat.index)
fc['p_move'] = p_move; fc['mean_qty'] = base_mean + event_qty
fc['q50'] = q50 + event_qty; fc['q90'] = q90 + event_qty; fc['q95'] = q95 + event_qty
fc['base_qty'] = base_mean; fc['event_qty'] = event_qty
fc['ltd_mean'] = d_day * L; fc['ltd_var'] = L * var_day + d_day ** 2 * sL ** 2
fc['cold_start'] = (mat.qty_issued_17m == 0).astype(int); fc['drivers'] = drivers
fc.index.name = 'material_no'

# =====================================================================  P1: policy (KQ2)
crit = mat.criticality.values; slv = np.array([SL[c] for c in crit]); z = norm.ppf(slv)
ltd_m = fc.ltd_mean.values; ltd_sd = np.sqrt(fc.ltd_var.values)
rop_norm = ltd_m + z * ltd_sd
rop_cp = np.array([np.quantile(LTD[j], slv[j]) for j in range(len(mat))])
rop = np.ceil(np.where(p_base.values >= P_LOW, rop_norm, rop_cp) - 1e-9).clip(min=0)
ss = rop - ltd_m

D_yr = base_mean.values * 365 / H
price = mat.unit_price.fillna(0).values
pr_med = q.groupby('PR-Material')['PR-Quantity'].median().reindex(mat.index).values
with np.errstate(divide='ignore', invalid='ignore'):
    eoq = np.where((price > 0) & (D_yr > 0), np.sqrt(2 * D_yr * ORDER_COST / (HOLD * price)), np.nan)
eoq = np.where(np.isnan(eoq), np.where(np.isnan(pr_med), np.ceil(D_yr / 4), pr_med), eoq)
Q = np.minimum(np.ceil(eoq), np.maximum(1, np.ceil(D_yr)))           # never more than ~1 year of demand
Q = np.where((rop > 0) | (D_yr >= .5), np.maximum(Q, 1), 0)
max_new = rop + Q
max_new = np.where((mat.criticality.values == 'A') & (mat.mrp_type.values == 'Stock Item'), np.maximum(max_new, 1), max_new)

stock = mat.stock.values
# turnaround layer: planned scope = last TA kit x scale, independent of the 180-day forecast horizon
ta_need = ta_kit.ta_qty_last.reindex(mat.index).fillna(0).values * TA_SCALE
lt90 = mat.lt_p90.values
ta_short = (ta_need > 0) & (stock < ta_need + rop)
ta_ob = (NEXT_TA - pd.to_timedelta(lt90 + TA_BUFFER, unit='D'))
ta_due = ta_short & np.asarray(ta_ob <= AS_OF + pd.Timedelta(days=TA_WINDOW))      # TA PR must go out this month
order_qty = np.maximum(max_new - stock, np.where(ta_due, ta_need + rop - stock, 0)).clip(min=0)

def pso(level):           # P(lead-time demand > level), per material, from the simulation
    return (LTD > np.asarray(level, dtype=np.float32)[:, None]).mean(axis=1)
pso_new = pso(rop)
cycles = np.where(Q > 0, D_yr / np.maximum(Q, 1), D_yr)
dcost = np.array([DT_COST[c] for c in crit]); ddays = L
hold_new = HOLD * price * (np.maximum(ss, 0) + Q / 2)
risk_new = pso_new * cycles * dcost * ddays

pm = np.asarray(p_move); cold = fc.cold_start.values == 1; trust = mat.trust_score.values
sa = np.isin(crit, ['A', 'B'])
reorder = (((stock <= rop) & (rop > 0) & (pm >= P_LOW)) | ta_due | (stock < rop)) & (order_qty > 0)
action = np.select([reorder, mat.health.values == 'OBSOLETE_CANDIDATE', (stock > max_new + ta_need) & (pm < P_LOW),     # never cut stock the next TA needs

                    (cold & (pm >= P_LOW)) | (trust < .5)],
                   ['REORDER', 'DISPOSE_REVIEW', 'REDUCE', 'MONITOR'], 'MAINTAIN')
order_qty = np.where(action == 'REORDER', order_qty, 0)

# order-by date (E2): last safe day to raise the PR
# ROP already covers lead-time demand, so the PR goes out the day stock reaches ROP (no extra lead-time offset)
with np.errstate(divide='ignore', invalid='ignore'):
    cover = np.where(d_day > 0, np.maximum(0, stock - rop) / d_day, np.nan)
    cover = np.where((stock == rop) & (rop > 0), np.where(lam_h > 0, H / lam_h, np.nan), cover)   # at ROP: PR at the next expected issue
cover = np.where(stock < rop, 0, cover)
cover = np.where((rop == 0) & (stock == 0), np.nan, cover)       # not stocked under the new policy: no routine PR
slack = cover
ob_norm = AS_OF + pd.to_timedelta(np.where(slack > 730, np.nan, slack), unit='D')    # > 2 years out: no date
ob_ta = ta_ob.where(ta_short)
ob = pd.DataFrame({'n': ob_norm, 't': ob_ta}).min(axis=1)
ob = ob.where(ob.isna() | (ob >= AS_OF), AS_OF)
ob = ob.where(action != 'REORDER', AS_OF)
order_by = ob.dt.strftime('%Y-%m-%d').values

def idr(v):                # English UI: B = billion, M = million (team docs write miliar as 'M')
    return f'Rp {v / 1e9:,.2f} B' if abs(v) >= 1e9 else f'Rp {v / 1e6:,.1f} M'

def reason(j):
    i = mat.index[j]; u = mat.unit.iat[j]; c = crit[j]; a = action[j]; pmv = pm[j]
    dj = json.loads(drivers.iat[j]); top = next((k for k in dj if k != 'fl_notif_90d'), None)
    if a == 'REORDER':
        s = (f"REORDER {order_qty[j]:g} {u}: {c}-critical, installed on {mat.n_funcloc.iat[j]} FLs, "
             f"{dj['fl_notif_90d']} notifications in last 90d, P(use in 180d) {pmv:.0%}, lead time P90 {lt90[j]:.0f}d, "
             f"stock {stock[j]:g} vs new ROP {rop[j]:g}")
        if ta_due[j]: s += f", next turnaround needs {ta_need[j]:g} {u}"
        if dj['pm_due_90'] or dj['fl_open_notif']:
            s += f", upcoming work on its FLs: {dj['pm_due_90']} PM due in 90d ({dj['pm_major_due_90']} major), {dj['fl_open_notif']} open notifications"
        return s + f". Raise PR by {order_by[j]}."
    if a != 'REORDER' and ta_short[j]:
        tail = f" Next turnaround needs {ta_need[j]:g} {u}: raise that PR by {order_by[j]}."
    else:
        tail = ''
    if a == 'DISPOSE_REVIEW':
        return (f"DISPOSE_REVIEW: no issue in 17 months and none of its {mat.n_funcloc.iat[j]} FLs has PM or notifications; "
                f"{stock[j]:g} {u} on shelf (~{idr(stock[j] * price[j])} on this dataset).")
    if a == 'REDUCE':
        ex = stock[j] - max_new[j] - ta_need[j]
        return (f"REDUCE: stock {stock[j]:g} exceeds new Max {max_new[j]:g} by {ex:g} {u} (~{idr(ex * price[j])} on this dataset); "
                f"P(use in 180d) only {pmv:.0%}. Stop replenishing; check twin materials before buying again." + tail)
    if a == 'MONITOR':
        if cold[j] and pmv >= P_LOW:
            return (f"MONITOR: no consumption history, but the model gives {pmv:.0%} chance of use in 180d "
                    f"(top driver: {NICE.get(top, top)}). Confirm with planner before stocking.")
        return f"MONITOR: data trust score {trust[j]:.2f}; verify price, lead time and master data before acting." + tail
    if stock[j] > max_new[j]:
        return (f"MAINTAIN: stock {stock[j]:g} is above new Max {max_new[j]:g} {u}, but the part is active (P(use in 180d) {pmv:.0%}); "
                f"no new PR, let consumption draw it down." + tail)
    return f"MAINTAIN: stock {stock[j]:g} within new Min-Max {rop[j]:g}-{max_new[j]:g} {u}; P(use in 180d) {pmv:.0%}." + tail

pol = pd.DataFrame(index=mat.index)
pol['service_level'] = slv; pol['safety_stock'] = ss; pol['rop'] = rop; pol['min_new'] = rop; pol['max_new'] = max_new
pol['action'] = action; pol['order_qty'] = order_qty; pol['order_by_date'] = order_by
pol['hold_cost_yr'] = hold_new; pol['risk_cost_yr'] = risk_new
pol['reason'] = [reason(j) for j in range(len(mat))]
pol.index.name = 'material_no'

# =====================================================================  P1: frontier (budget vs risk)
# candidate reorder levels per part: simulated LTD quantiles up to the max, plus the policy ROP and the current Min,
# so both the 'optimized' and the 'current' points are attainable on the frontier (they can never fall below it)
GRID = [.5, .8, .9, .95, .97, .99, .995, .999, 1.0]
lv = np.ceil(np.quantile(LTD, GRID, axis=1).T - 1e-9)
lv = np.sort(np.column_stack([np.zeros(len(mat)), lv, rop, mat.min_cur.values]), axis=1)
inv = price[:, None] * (np.maximum(lv - ltd_m[:, None], 0) + Q[:, None] / 2)
ps = np.stack([pso(lv[:, k]) for k in range(lv.shape[1])], axis=1)
rk = ps * (cycles * dcost * ddays)[:, None]
segs = []                                                        # lower convex hull segments per material
start = np.zeros((len(mat), 3))                                  # each part's cheapest point (ties: lowest risk) = frontier origin
for j in range(len(mat)):
    pts = sorted(set(zip(inv[j], rk[j], ps[j])))
    hull = [pts[0]]; start[j] = pts[0]
    for pt in pts[1:]:
        if pt[1] >= hull[-1][1]: continue
        while len(hull) >= 2 and (hull[-1][1] - hull[-2][1]) * (pt[0] - hull[-2][0]) >= (pt[1] - hull[-2][1]) * (hull[-1][0] - hull[-2][0]):
            hull.pop()
        hull.append(pt)
    for k in range(1, len(hull)):
        di, dr = hull[k][0] - hull[k - 1][0], hull[k - 1][1] - hull[k][1]
        segs.append((dr / di if di > 0 else np.inf, di, dr, hull[k - 1][2] - hull[k][2], j, k == 1))
segs.sort(key=lambda s: -s[0])
isS, isA = crit == 'A', crit == 'B'          # top two tiers -> fill_rate_A / fill_rate_B
b0 = start[:, 0].sum(); r0 = start[:, 1].sum(); fS0 = (1 - start[isS, 2]).sum(); fA0 = (1 - start[isA, 2]).sum()
sg = pd.DataFrame(segs, columns=['eff', 'di', 'dr', 'dp', 'j', 'first'])
sg['budget'] = b0 + sg.di.cumsum(); sg['risk'] = r0 - sg.dr.cumsum()
sg['fS'] = (fS0 + np.where(isS[sg.j], sg.dp, 0).cumsum()) / isS.sum()
sg['fA'] = (fA0 + np.where(isA[sg.j], sg.dp, 0).cumsum()) / isA.sum()
sg['funded'] = sg['first'].cumsum()

def point(name, budget, risk, pso_vec, funded):
    return dict(scenario=name, budget_idr=float(budget), exp_risk_cost=float(risk),
                fill_rate_A=float((1 - pso_vec[isS]).mean()), fill_rate_B=float((1 - pso_vec[isA]).mean()), n_parts_funded=int(funded))
rows = []
idx = np.unique(np.linspace(0, len(sg) - 1, 80).astype(int))
for _, r in sg.iloc[idx].iterrows():
    rows.append(dict(scenario='frontier', budget_idr=r.budget, exp_risk_cost=r.risk, fill_rate_A=r.fS, fill_rate_B=r.fA, n_parts_funded=int(r.funded)))
Q_cur = np.maximum(mat.max_cur.values - mat.min_cur.values, 1)
pso_cur = pso(mat.min_cur.values)
risk_cur = pso_cur * cycles * dcost * ddays            # same exposure as the new policy; only the ROP differs
inv_cur = price * (np.maximum(mat.min_cur.values - ltd_m, 0) + Q / 2)   # same lot size as the new policy: compares reorder levels only
inv_new = price * (np.maximum(ss, 0) + Q / 2)
rows.append(point('current', inv_cur.sum(), risk_cur.sum(), pso_cur, (mat.max_cur.values > 0).sum()))
rows.append(point('optimized', inv_new.sum(), risk_new.sum(), pso_new, (max_new > 0).sum()))
lean = sg[sg.risk <= risk_cur.sum()].iloc[0] if (sg.risk <= risk_cur.sum()).any() else sg.iloc[-1]
rows.append(dict(scenario='lean', budget_idr=lean.budget, exp_risk_cost=lean.risk, fill_rate_A=lean.fS, fill_rate_B=lean.fA, n_parts_funded=int(lean.funded)))
frontier = pd.DataFrame(rows)

# =====================================================================  P2: dq_issues + backtest
nn = nt.copy()
dq = pd.DataFrame([
    ('BoM duplicate rows (same FL x material)', int(bom.duplicated().sum()), 'FL+material listed twice', 'installed qty double counted; dropped duplicates for FL counts'),
    ('PR/PO exact duplicate lines', 5420, '11,609 lines -> 6,189 unique (PR + item)', 'dropped before lead time, price and spend'),
    ('Maintenance cycle text formats', int(mp['Cycle Descriptions'].nunique()), str(mp['Cycle Descriptions'].iloc[0]), 'free text cycles; PM used as population count only'),
    ('Notifications with Required Start before notification date', int((nn['Required Start'] < nn['Notification Date']).sum()),
     f"{(nn['Required Start'] < nn['Notification Date']).mean():.1%} of notifs", 'planning dates unreliable for lead-time analysis'),
    ('PR lines with negative lead time', int((p.lt_days < 0).sum()), 'PO delivery before PR date', 'dropped from lead-time stats'),
    ('Materials with an IDR PO price', int((mat.price_source == 'po').sum()), f"{(mat.price_source == 'po').mean():.1%} of BoM materials", 'rest priced by category estimate, flagged in price_source'),
    ('Orders linked to a notification', int(nn.Order.notna().sum()), f"{mv.Order.isin(nn.Order.dropna().astype('int64')).mean():.1%} of issue lines", 'failure->part link weak; features aggregated at FL level'),
    ('PO-Item Amount is a unit price', int(p['PO-Item Amount'].notna().sum()), 'within-material CV ~2%, r(amount, qty)=0.03', 'value = price x qty; never divide by qty'),
    ('Stock ledger does not balance', int(ledger_bad.sum()), f"{(led.start < 0).mean():.1%} of materials with issues+receipts", 'implied opening stock < 0; trust_score flag'),
], columns=['issue', 'n', 'example', 'impact'])

bt_txt = (ROOT / 'analysis' / 'backtest_output.txt').read_text()
cold_auc = dict(re.findall(r'^\s+(\w+)\s+AUC on cold-start = ([\d.]+)', bt_txt, re.M))
cov95 = dict(re.findall(r'^\s+(\w+)\s+q=0\.95\s+units held=\s*[\d,]+\s+movers fully covered=([\d.]+)', bt_txt, re.M))
bt = []
for mth, auc, rec, mae, bias in re.findall(r'^(\w+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)$', bt_txt, re.M):
    bt.append(dict(method=mth, auc_all=float(auc), auc_cold=float(cold_auc[mth]) if mth in cold_auc else None,
                   coverage_q95=float(cov95[mth]) if mth in cov95 else None,
                   note=f'analysis/backtest_output.txt; MAE {mae}, total bias {bias}'))
for r in val.itertuples():
    bt.append(dict(method=f'engine_rolling_{r.origin}', auc_all=r.auc, auc_cold=r.auc_cold, coverage_q95=r.cov95,
                   note=f'rolling 90d, origin {r.origin}: bias {r.bias:+.3f} (naive {r.bias_naive:+.3f}), MAE {r.mae:.2f} (naive {r.mae_naive:.2f}), '
                        f'q90 cover {r.cov90:.3f}, q95 cover all parts {r.cov95_all:.3f}'))
vm = val.mean(numeric_only=True); vs = val_s.mean(numeric_only=True)
bt.append(dict(method='engine_strict_mean', auc_all=vs.auc, auc_cold=vs.auc_cold, coverage_q95=None,
               note=f'same engine without current BoM Min/Max/MRP (snapshots read after the test windows): MAE {vs.mae:.2f} vs naive {vs.mae_naive:.2f}, '
                    f'mean |bias| {val_s.bias.abs().mean():.3f}. Quote next to engine_rolling_mean.'))
bt.append(dict(method='engine_rolling_mean', auc_all=vm.auc, auc_cold=vm.auc_cold, coverage_q95=vm.cov95,
               note=f'mean of 4 origins Apr-Jul 26: AUC naive {vm.auc_naive:.3f}, MAE {vm.mae:.2f} vs naive {vm.mae_naive:.2f}, '
                    f'mean |bias| {val.bias.abs().mean():.3f} vs naive {val.bias_naive.abs().mean():.3f}. Model choice made on these origins.'))
backtest = pd.DataFrame(bt)

# monthly consumption for the Part detail chart (sparse: months without issues are absent -> app fills 0)
cm = mv.assign(evt=mv.ot.isin(EVENT)).groupby(['Material Number', 'ym']).agg(
    qty=('Quantity', 'sum'), qty_event=('Quantity', lambda s: s[mv.loc[s.index, 'ot'].isin(EVENT)].sum()), n_lines=('Quantity', 'size')).reset_index()
cm = cm.rename(columns={'Material Number': 'material_no'}); cm['ym'] = cm.ym.astype(str)
cm = cm[cm.material_no.isin(mat.index)]

# =====================================================================  write db
SCHEMA = """
CREATE TABLE materials (material_no INTEGER PRIMARY KEY, description TEXT, category TEXT, unit TEXT, mrp_type TEXT, criticality TEXT,
  n_funcloc INTEGER, installed_qty REAL, stock REAL, min_cur REAL, max_cur REAL, unit_price REAL, price_source TEXT, stock_value REAL,
  lt_p50 REAL, lt_p90 REAL, lt_source TEXT, main_supplier TEXT, qty_issued_17m REAL, months_active INTEGER, last_issue TEXT,
  demand_class TEXT, health TEXT, trust_score REAL, trust_flags TEXT);
CREATE TABLE forecast (material_no INTEGER PRIMARY KEY, p_move REAL, mean_qty REAL, q50 REAL, q90 REAL, q95 REAL, base_qty REAL, event_qty REAL,
  ltd_mean REAL, ltd_var REAL, cold_start INTEGER, drivers TEXT);
CREATE TABLE policy (material_no INTEGER PRIMARY KEY, service_level REAL, safety_stock REAL, rop REAL, min_new REAL, max_new REAL, action TEXT,
  order_qty REAL, order_by_date TEXT, hold_cost_yr REAL, risk_cost_yr REAL, reason TEXT);
CREATE TABLE ta_kit (material_no INTEGER PRIMARY KEY, ta_qty_last REAL, stock REAL, gap REAL, gap_value REAL, exceeds_max INTEGER, lt_p90 REAL, criticality TEXT);
CREATE TABLE frontier (scenario TEXT, budget_idr REAL, exp_risk_cost REAL, fill_rate_A REAL, fill_rate_B REAL, n_parts_funded INTEGER);
CREATE TABLE twins (group_id INTEGER, material_no INTEGER, role TEXT);
CREATE TABLE dq_issues (issue TEXT, n INTEGER, example TEXT, impact TEXT);
CREATE TABLE backtest (method TEXT, auc_all REAL, auc_cold REAL, coverage_q95 REAL, note TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE ltd_quantiles (material_no INTEGER PRIMARY KEY, q80 REAL, q90 REAL, q95 REAL, q97 REAL, q99 REAL, q995 REAL);
CREATE TABLE consumption_monthly (material_no INTEGER, ym TEXT, qty REAL, qty_event REAL, n_lines INTEGER, PRIMARY KEY (material_no, ym));
CREATE INDEX ix_policy_action ON policy(action);
CREATE INDEX ix_mat_health ON materials(health);
CREATE INDEX ix_mat_crit ON materials(criticality);
CREATE INDEX ix_twins_group ON twins(group_id);
"""
DB.parent.mkdir(parents=True, exist_ok=True)
if DB.exists(): DB.unlink()
con = sqlite3.connect(DB); con.executescript(SCHEMA)
def put(name, df):
    df = df.replace([np.inf, -np.inf], np.nan)
    df.to_sql(name, con, if_exists='append', index=False)
put('materials', mat.reset_index()); put('forecast', fc.reset_index()); put('policy', pol.reset_index())
put('ta_kit', ta_kit.reset_index()); put('frontier', frontier); put('twins', twins); put('dq_issues', dq); put('backtest', backtest); put('consumption_monthly', cm)
lq = pd.DataFrame(np.quantile(LTD, [.8, .9, .95, .97, .99, .995], axis=1).T, columns=['q80', 'q90', 'q95', 'q97', 'q99', 'q995'], index=mat.index)
put('ltd_quantiles', lq.reset_index())
put('meta', pd.DataFrame({'key': list(META), 'value': [str(v) for v in META.values()]}))
con.commit(); con.execute('VACUUM'); con.close()

# =====================================================================  control numbers
print(f'db {DB.name}  {DB.stat().st_size / 1e6:.1f} MB')
con = sqlite3.connect(DB)
for t in ['materials', 'forecast', 'policy', 'ta_kit', 'frontier', 'twins', 'dq_issues', 'backtest', 'meta', 'consumption_monthly', 'ltd_quantiles']:
    print(f'  {t:10s} {con.execute(f"select count(*) from {t}").fetchone()[0]:>6}')
con.close()
sak = ta_kit.criticality.isin(['A', 'B'])
stocked_k = (kit.mx > 0).values
print(f'E1 wording: TA need > Max on {ta_kit.exceeds_max.sum()} kit parts = {(ta_kit.exceeds_max.astype(bool) & stocked_k).sum()} stocked parts with Max > 0 '
      f'(A/B {(ta_kit.exceeds_max.astype(bool) & stocked_k & ta_kit.criticality.isin(["A", "B"]).values).sum()}) + {(ta_kit.exceeds_max.astype(bool) & ~stocked_k).sum()} with Max = 0 '
      f'| non-stock MRP in kit {(kit.mrp == "Non Stock").sum()}')
print(f'ta_kit: {len(ta_kit)} materials | gap>0 {(ta_kit.gap > 0).sum()} (A/B {((ta_kit.gap > 0) & sak).sum()}, A {((ta_kit.gap > 0) & (ta_kit.criticality == 'A')).sum()}) | exceeds_max {ta_kit.exceeds_max.sum()}'
      f' | gap value PO-priced Rp{(ta_kit.gap * st.px.reindex(ta_kit.index)).sum() / 1e9:.2f}bn, incl. estimates Rp{ta_kit.gap_value.sum() / 1e9:.2f}bn')
print('price_source', mat.price_source.value_counts().to_dict(), '| lt_source', mat.lt_source.value_counts().to_dict())
print('health', mat.health.value_counts().to_dict())
print('demand_class', mat.demand_class.value_counts().to_dict())
print('action', pd.Series(action).value_counts().to_dict())
print('rolling validation (90d routine demand, model selected on these origins):')
print(val.round(3).to_string(index=False))
print(f'strict (no Min/Max/MRP snapshot): AUC {vs.auc:.3f}, cold {vs.auc_cold:.3f}, MAE {vs.mae:.2f}, mean |bias| {val_s.bias.abs().mean():.3f}')
print(f'forecast next 180d: base {base_mean.sum():,.0f} units + event {event_qty.sum():,.0f} units | p_move>=0.3: {(pm >= P_LOW).sum()}')
print('frontier', frontier[frontier.scenario != 'frontier'].round(3).to_string(index=False))

# ---- 5 numbers for Business Impact
kit_i = ta_kit.index; jk = mat.index.get_indexer(kit_i); sa_k = sak.values
ready_now = (ta_kit.stock >= ta_kit.ta_qty_last).values
in_time = (AS_OF + pd.to_timedelta(lt90[jk], unit='D')) <= NEXT_TA
ready_after = ready_now | ((stock[jk] + order_qty[jk] >= ta_need[jk]) & in_time)
ob_k = ta_ob.values[jk]; short_k = ta_short[jk]
ready_ob = ready_now | (ob_k >= AS_OF.to_datetime64())            # every TA PR raised by its order-by date
too_late = short_k & (ob_k < AS_OF.to_datetime64()); due_k = ta_due[jk] & ~too_late; later_k = short_k & ~ta_due[jk]
a_k = (ta_kit.criticality == 'A').values
print(f'[BI-1] next TA {NEXT_TA.date()} ({(NEXT_TA - AS_OF).days}d). TA readiness A/B: today {ready_now[sa_k].mean():.1%} -> '
      f'{ready_ob[sa_k].mean():.1%} if each PR goes out by its order-by date (A only: {ready_now[a_k].mean():.1%} -> {ready_ob[a_k].mean():.1%})')
print(f'       TA-short parts: {short_k.sum()} | too late already {too_late.sum()} | order within {TA_WINDOW}d {due_k.sum()} | later {later_k.sum()} '
      f'| A/B: late {(too_late & sa_k).sum()}, this month {(due_k & sa_k).sum()}, later {(later_k & sa_k).sum()}')
red = action == 'REDUCE'; dis = action == 'DISPOSE_REVIEW'
print(f'[BI-2] releasable stock value: REDUCE Rp{((stock - max_new) * price)[red].sum() / 1e9:.2f}bn ({red.sum()} parts) + '
      f'DISPOSE_REVIEW Rp{(stock * price)[dis].sum() / 1e9:.2f}bn ({dis.sum()} parts), on this dataset')
po = (mat.price_source == 'po').values
print(f'       PO-priced parts only: REDUCE Rp{((stock - max_new) * price)[red & po].sum() / 1e9:.2f}bn ({(red & po).sum()}) + '
      f'DISPOSE_REVIEW Rp{(stock * price)[dis & po].sum() / 1e9:.2f}bn ({(dis & po).sum()}) | total stock value Rp{mat.stock_value.sum() / 1e9:.0f}bn')
risk_now = pso(stock) > 1 - slv; risk_after = pso(stock + order_qty) > 1 - slv
print(f'[BI-3] A/B parts at stockout risk (P(LTD > stock) > 1-SL): now {(risk_now & sa).sum()} -> after REORDER {(risk_after & sa).sum()}')
bb_ = backtest.set_index('method')
print(f"[BI-4] AUC who-moves: rolling engine {vm.auc:.3f} (cold {vm.auc_cold:.3f}) vs naive {vm.auc_naive:.3f}; strict {vs.auc:.3f} (cold {vs.auc_cold:.3f}) | old backtest: engine {bb_.at['lgbm_2part', 'auc_all']:.3f} "
      f"vs SBA {bb_.at['sba', 'auc_all']:.3f}; cold {bb_.at['lgbm_2part', 'auc_cold']:.3f} vs {bb_.at['sba', 'auc_cold']:.3f}")
rq = p[p.lt_days >= 0].copy(); rq['req'] = (rq['PR-Delivery Date'] - rq['PR-Date']).dt.days
rq = rq[rq.groupby('PR-Material').lt_days.transform('size') >= 3]
rq['rush'] = rq.req < .5 * rq.groupby('PR-Material').lt_days.transform('median')
rq['late'] = rq['PO-Delivery Date'] > rq['PR-Delivery Date']
print(f'[BI-5] rush PR lines {rq.rush.mean():.1%} of PRs; rush PRs arrive late {rq[rq.rush].late.mean():.1%} vs {rq[~rq.rush].late.mean():.1%} for normal PRs '
      f'-> order-by dates remove the rush request itself')

# app-only helper tables (furnace map, plant-level facts) maintained by Orang 2
import runpy
runpy.run_path(str(ROOT / 'pipeline' / 'app_tables.py'), run_name='__main__')

runpy.run_path(str(ROOT / 'pipeline' / 'maintenance_calendar.py'), run_name='__main__')

# business-metric backtest: replay Mar-Sep 2026 issues against current Min-Max vs PartPulse (main and strict forecast)
import subprocess
for extra in ([], ['--strict']):
    subprocess.run([sys.executable, str(ROOT / 'pipeline' / 'policy_backtest.py')] + extra, check=True)
# month-by-month replay on stocked parts, shown on the Replay page; the plain run first, because it creates the tables
for extra in ([], ['--strict']):
    subprocess.run([sys.executable, str(ROOT / 'pipeline' / 'replay_timeline.py')] + extra, check=True)
