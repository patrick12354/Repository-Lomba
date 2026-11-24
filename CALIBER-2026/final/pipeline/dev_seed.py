"""Dev seed for app/data/partpulse.db (contract in docs/tasks/00_TEAM_PLAN.md).

Simplified, real-data stand-in so the app can be built before Orang 1's engine lands.
Orang 1's partpulse.db replaces this file at the same path. meta.source = 'dev_seed'.

Run from repo root:  py pipeline/dev_seed.py
"""
import sys, re, json, math, sqlite3, os
sys.path.insert(0, 'analysis')
from build_mat import build
import pandas as pd, numpy as np

AS_OF = pd.Timestamp('2026-11-04')
NEXT_TA = pd.Timestamp('2027-03-04')          # assumption: ~120 days out, user can change in app
TA_START, TA_END = '2025-11-01', '2026-02-01'
HORIZON_M = 6
SL = {'S': .98, 'A': .95, 'B': .90, 'C': .85}
Z = {'S': 2.054, 'A': 1.645, 'B': 1.282, 'C': 1.036}
HOLD = 0.20
DT_COST = {'S': 500e6, 'A': 150e6, 'B': 30e6, 'C': 5e6}   # IDR per day of downtime, assumption
DT_DAYS = 1.0                                           # days lost per stockout event, assumption
OUT = 'app/data/partpulse.db'
# Superseded by build_db.py. Never overwrite the engine's database by accident.
if os.path.exists(OUT) and '--force' not in sys.argv:
    sys.exit(f'{OUT} exists (built by pipeline/build_db.py). This dev seed is kept for history; pass --force to overwrite.')

m, (bom, fl, mp, mv, nt, pp, p), months = build()
m = m.rename(columns={'Material No': 'material_no'})
m['crit'] = m.crit.fillna('C')
mv = mv.copy()
mv['ot'] = mv.Order.astype(str).str[:4]
mv['ym'] = mv['Posting Date'].dt.strftime('%Y-%m')
N_MONTHS = mv.ym.nunique()

# ---- history -------------------------------------------------------------
act = mv.groupby('Material Number').ym.nunique().rename('months_active')
ev = mv[mv.ot.isin(['2030', '2090'])].groupby('Material Number').Quantity.sum().rename('ev_hist')
ta = mv[(mv.ot == '2030') & (mv['Posting Date'] >= TA_START) & (mv['Posting Date'] < TA_END)]
ta_qty = ta.groupby('Material Number').Quantity.sum().rename('ta_qty')
size = (mv.groupby('Material Number').Quantity.sum() / mv.groupby('Material Number').size()).rename('size')
m = (m.merge(act, left_on='material_no', right_index=True, how='left')
      .merge(ev, left_on='material_no', right_index=True, how='left')
      .merge(ta_qty, left_on='material_no', right_index=True, how='left')
      .merge(size, left_on='material_no', right_index=True, how='left'))
m[['months_active', 'ev_hist', 'ta_qty']] = m[['months_active', 'ev_hist', 'ta_qty']].fillna(0)
m['size'] = m['size'].fillna(1)
m['base_hist'] = (m.qty - m.ev_hist).clip(lower=0)
m['base_rate'] = m.base_hist / months                    # per month

def demand_class(row_months):
    return row_months

mon = mv.groupby(['Material Number', 'ym']).Quantity.sum().unstack(fill_value=0)
def sba(r):
    nz = r[r > 0]
    if len(nz) == 0: return 'none'
    if len(nz) == 1: return 'single'
    adi = len(r) / len(nz); cv2 = (nz.std(ddof=0) / nz.mean()) ** 2
    if adi < 1.32: return 'smooth' if cv2 < .49 else 'erratic'
    return 'intermittent' if cv2 < .49 else 'lumpy'
m['demand_class'] = m.material_no.map(mon.apply(sba, axis=1)).fillna('none')

# ---- equipment signals (notifs and PM items on the FLs where a part sits) --------
nt_recent = nt[nt['Notification Date'] >= nt['Notification Date'].max() - pd.Timedelta(days=180)]
fl_notif = nt_recent.groupby('Functional Location').size()
fl_pm = mp.groupby('Functional Location').size()
bfl = bom[['Functional Loc.', 'Material No']].drop_duplicates()
bfl['notif'] = bfl['Functional Loc.'].map(fl_notif).fillna(0)
bfl['pm'] = bfl['Functional Loc.'].map(fl_pm).fillna(0)
sig = bfl.groupby('Material No')[['notif', 'pm']].sum()
m['fl_notif'] = m.material_no.map(sig.notif).fillna(0)
m['fl_pm'] = m.material_no.map(sig.pm).fillna(0)

# ---- price, lead time, supplier -----------------------------------------
cat_px = m.groupby('cat').px.median()
m['price_source'] = np.where(m.px.notna(), 'po', np.where(m.cat.map(cat_px).notna(), 'category_estimate', 'none'))
m['unit_price'] = m.px.fillna(m.cat.map(cat_px))
glob50, glob90 = p.lt_days.median(), p.lt_days.quantile(.9)
cat_lt50 = m[m.n_pr >= 3].groupby('cat').lt_med.median(); cat_lt90 = m[m.n_pr >= 3].groupby('cat').lt_p90.median()
own = m.n_pr.fillna(0) >= 3
m['lt_source'] = np.where(own, 'material', np.where(m.cat.map(cat_lt50).notna(), 'category', 'global'))
m['lt_p50'] = np.where(own, m.lt_med, m.cat.map(cat_lt50).fillna(glob50))
m['lt_p90'] = np.where(own, m.lt_p90, m.cat.map(cat_lt90).fillna(glob90))
m['lt_p90'] = np.maximum(m.lt_p90, m.lt_p50)
sup = p.groupby('PR-Material')['PO-Supplier Name'].agg(lambda s: s.mode().iat[0] if len(s.mode()) else None)
m['main_supplier'] = m.material_no.map(sup)

# ---- forecast (simple: history rate blended with installed-base prior) ------
def prior17(n):
    return .15 if n <= 1 else .27 if n == 2 else .51 if n <= 5 else .80 if n <= 10 else .97 if n <= 50 else .99
m['p_prior'] = m.n_fl.map(lambda n: 1 - (1 - prior17(n)) ** (HORIZON_M / 17))
m['p_hist'] = 1 - (1 - m.months_active / N_MONTHS) ** HORIZON_M
m['cold'] = (m.months_active == 0).astype(int)
p_move = np.where(m.cold == 1, m.p_prior, .75 * m.p_hist + .25 * m.p_prior)
p_move = p_move * (1 + .06 * np.minimum(m.fl_notif, 5))
m['p_move'] = np.clip(p_move, .01, .98)

cat_size = m[m.qty > 0].groupby('cat')['size'].median()
ta_in_horizon = (NEXT_TA - AS_OF).days <= HORIZON_M * 30.44
m['event_qty'] = m.ta_qty if ta_in_horizon else 0.0
m['base_qty'] = np.where(m.cold == 1, m.p_move * m.cat.map(cat_size).fillna(1), m.base_rate * HORIZON_M)
m['mean_qty'] = m.base_qty + m.event_qty
sd = np.sqrt(m.base_qty * np.maximum(1, m['size']) * 1.5 + (m.event_qty * .3) ** 2)
m['q50'] = m.mean_qty.round(1)
m['q90'] = (m.mean_qty + 1.2816 * sd).round(1)
m['q95'] = (m.mean_qty + 1.645 * sd).round(1)
rate_d = (m.base_rate / 30.44).values   # stock policy uses history only; cold-start parts go to MONITOR or insurance
lt_sd = (m.lt_p90 - m.lt_p50) / 1.2816
m['ltd_mean'] = rate_d * m.lt_p50
m['ltd_var'] = m.ltd_mean * np.maximum(1, m['size']) * 1.5 + (rate_d * lt_sd) ** 2

# ---- policy ------------------------------------------------------------
def ncdf(x): return .5 * (1 + math.erf(x / math.sqrt(2)))
z = m.crit.map(Z)
m['service_level'] = m.crit.map(SL)
m['safety_stock'] = (z * np.sqrt(m.ltd_var)).round(2)
m['rop'] = (m.ltd_mean + m.safety_stock).round(2)
insurance = (m.base_rate == 0) & m.crit.isin(['S', 'A']) & (m.p_move >= .3) & (m.mrp == 'Stock Item')
m.loc[insurance, 'rop'] = np.maximum(m.loc[insurance, 'rop'], 1)
m['min_new'] = np.where(m.rop >= .05, np.ceil(m.rop), 0)
m['max_new'] = m.min_new + np.where(m.min_new > 0, np.maximum(np.ceil(m.base_rate * 3), 1), 0)

m['insurance'] = insurance
def act_row(r):
    used = r.qty > 0
    if not used and r.stock > 0 and r.p_move < .1 and r.crit in ('B', 'C') and r.n_fl <= 2: return 'DISPOSE_REVIEW'
    if r.min_new > 0 and r.stock < r.min_new and (used or r.insurance): return 'REORDER'
    if r.stock > 0 and r.stock > 2 * max(r.max_new, 1) and r.stock - r.max_new >= 2 and (used or r.crit in ('B', 'C') or r.stock > r.mx > 0): return 'REDUCE'
    if r.cold == 1 and r.p_move >= .25 and r.stock == 0: return 'MONITOR'
    return 'MAINTAIN'
m['action'] = m.apply(act_row, axis=1)
m['order_qty'] = np.where(m.action == 'REORDER', np.maximum(m.max_new - m.stock, 1), 0)
days_to_rop = np.where(rate_d > 0, (m.stock - m.rop) / np.maximum(rate_d, 1e-9), np.where(m.stock < m.min_new, 0, np.inf))
days_to_rop = np.clip(days_to_rop, 0, 365)   # below the reorder point already -> order today
m['order_by_date'] = [(AS_OF + pd.Timedelta(days=int(round(d)))).strftime('%Y-%m-%d') if (a == 'REORDER' or d < 180) and np.isfinite(d) and (a in ('REORDER', 'MAINTAIN', 'MONITOR')) and (rate_d_i > 0 or a == 'REORDER') else None
                      for d, a, rate_d_i in zip(days_to_rop, m.action, rate_d)]

def p_short(r):
    if r.ltd_mean <= 0: return 1.0 if r.stock == 0 else 0.0
    sdv = math.sqrt(max(r.ltd_var, 1e-9))
    return 1 - ncdf((r.stock + .5 - r.ltd_mean) / sdv)
m['p_short'] = m.apply(p_short, axis=1)
p_year = 1 - (1 - m.p_move) ** 2
m['hold_cost_yr'] = (HOLD * m.unit_price.fillna(0) * m.stock).round(0)
m['risk_cost_yr'] = (p_year * m.p_short * m.crit.map(DT_COST) * DT_DAYS).round(0)

def reason(r):
    lt = int(round(r.lt_p90))
    if r.action == 'REORDER':
        if r.cold == 1: return f"Never used yet, but installed in {int(r.n_fl)} places. Supplier takes up to {lt} days."
        return f"Stock {r.stock:g} is under the new minimum {r.min_new:g}. Supplier takes up to {lt} days."
    if r.action == 'REDUCE': return f"{r.stock:g} on the shelf, about {max(r.q95, 0):g} needed in 6 months."
    if r.action == 'DISPOSE_REVIEW': return f"Not used in 17 months and fitted in only {int(r.n_fl)} place."
    if r.action == 'MONITOR': return f"Likely to be needed soon ({int(round(r.p_move * 10))} in 10). Stock is enough for now."
    return "Stock fits the expected demand."
m['reason'] = m.apply(reason, axis=1)

# ---- health --------------------------------------------------------------
def health(r):
    if r.stock == 0 and r.qty > 0: return 'STOCKOUT'
    if r.mn > 0 and r.stock < r.mn: return 'BELOW_MIN'
    if r.qty == 0 and r.stock > 0 and r.n_fl <= 1 and (pd.isna(r.n_pr) or r.n_pr == 0) and r.crit in ('B', 'C'): return 'OBSOLETE_CANDIDATE'
    if r.qty == 0 and r.stock > 0: return 'NON_MOVING'
    if r.mx > 0 and r.stock > r.mx: return 'OVER_MAX'
    return 'OK'
m['health'] = m.apply(health, axis=1)

# ---- twins ---------------------------------------------------------------
m['key'] = m.desc.map(lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper()))
dup = m[m.key.map(m.key.value_counts()) > 1].copy()
dup['group_id'] = dup.groupby('key').ngroup() + 1
short = (dup.stock < dup.mn) | ((dup.stock == 0) & (dup.qty > 0))
donor = (dup.mx >= 0) & (dup.stock > dup.mx) & (dup.stock > 0)
dup['role'] = np.where(short, 'SHORT', np.where(donor, 'DONOR', 'OTHER'))
twins = dup[['group_id', 'material_no', 'role']]

# ---- trust ---------------------------------------------------------------
used = mv.groupby('Material Number').Quantity.sum()
recv = p[(p['PO-Delivery Date'] <= '2026-09-30') & (p['PO-Delivery Date'] >= '2025-05-06')].groupby('PR-Material')['PR-Quantity'].sum()
opening = m.set_index('material_no').stock + used.reindex(m.material_no).fillna(0).values - recv.reindex(m.material_no).fillna(0).values
m['ledger_ok'] = (opening.values >= 0)
m['has_twin'] = m.material_no.isin(twins.material_no)
m['trust_score'] = (.35 * (m.price_source == 'po') + .35 * np.minimum(m.n_pr.fillna(0), 5) / 5 + .3 * m.ledger_ok).round(2)
m['trust_flags'] = [json.dumps({'price_verified': bool(a), 'lt_samples': int(b), 'ledger_ok': bool(c), 'has_twin': bool(d)})
                    for a, b, c, d in zip(m.price_source == 'po', m.n_pr.fillna(0), m.ledger_ok, m.has_twin)]

m['drivers'] = [json.dumps({'n_funcloc': int(a), 'crit': c, 'fl_notif_180d': int(n), 'fl_pm_items': int(pm), 'months_active': int(ma), 'lt_p90': int(round(lt)), 'category': cat})
                for a, c, n, pm, ma, lt, cat in zip(m.n_fl, m.crit, m.fl_notif, m.fl_pm, m.months_active, m.lt_p90, m.cat)]

# ---- ta_kit + location -----------------------------------------------------
tk = m[m.ta_qty > 0].copy()
tk['gap'] = (tk.ta_qty - tk.stock).clip(lower=0)
tk['gap_value'] = (tk.gap * tk.unit_price).where(tk.price_source == 'po')
tk['exceeds_max'] = (tk.ta_qty > tk.mx).astype(int)
loc = bom[bom['Material No'].isin(tk.material_no)][['Material No', 'Functional Loc.']].drop_duplicates()
ex = loc['Functional Loc.'].astype(str).str.extract(r'^[A-Z]+_([A-Z]+)-(\d+[A-Z]?)')
loc['equip_class'] = ex[0].fillna('OTHER')
loc['equipment'] = (ex[0] + '-' + ex[1]).fillna('')
material_location = loc[loc.equipment != ''][['Material No', 'equipment', 'equip_class']].drop_duplicates().rename(columns={'Material No': 'material_no'})

# ---- frontier (uniform service-level sweep vs today's stock) ----------------
def eval_policy(alpha):
    zz = {k: math.sqrt(2) * _erfinv(2 * alpha - 1) for k in 'SABC'}
    ss = m.crit.map(zz) * np.sqrt(m.ltd_var); rop = m.ltd_mean + ss
    cold_hold = (m.cold == 1) & (p_year >= min(.9, 2 * (1 - alpha)))   # insurance spare for never-used parts
    rop = np.where(insurance | cold_hold, np.maximum(rop, 1), rop)
    mn = np.where(rop >= .05, np.ceil(rop), 0); mx = mn + np.where(mn > 0, np.maximum(np.ceil(m.base_rate * 3), 1), 0)
    avg = (mn + mx) / 2
    sdv = np.sqrt(np.maximum(m.ltd_var, 1e-9))
    ps = np.array([1 - ncdf((s + .5 - mu) / sd_) if mu > 0 else (1.0 if s == 0 else 0.0) for s, mu, sd_ in zip(mn, m.ltd_mean, sdv)])
    return avg, ps
def _erfinv(y):
    a = .147; ln = math.log(1 - y * y); t = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(math.sqrt(t * t - ln / a) - t), y)
priced = m.price_source == 'po'   # money views use verified PO prices only (matches EDA)
need = (m.p_move >= .1) & (m.ltd_mean > 0)
rows = []
risk_now = m.risk_cost_yr.sum()
sa_need = need & m.crit.isin(['S', 'A'])
rows.append(('current', float((m.unit_price.fillna(0) * m.stock)[priced].sum()), float(risk_now),
             float(1 - m.p_short[need & (m.crit == 'S')].mean()), float(1 - m.p_short[need & (m.crit == 'A')].mean()), int((m.stock > 0).sum())))
for alpha in [.5, .7, .8, .85, .9, .95, .98, .99, .995]:
    avg, ps = eval_policy(alpha)
    budget = float((m.unit_price.fillna(0) * avg)[priced].sum())
    risk = float((p_year * ps * m.crit.map(DT_COST) * DT_DAYS).sum())
    rows.append((f'sl_{alpha}', budget, risk, float(1 - ps[(need & (m.crit == 'S')).values].mean()),
                 float(1 - ps[(need & (m.crit == 'A')).values].mean()), int((avg > 0).sum())))
frontier = pd.DataFrame(rows, columns=['scenario', 'budget_idr', 'exp_risk_cost', 'fill_rate_S', 'fill_rate_A', 'n_parts_funded'])

# ---- data quality ---------------------------------------------------------
idr = p[p['PO-Currency'] == 'IDR']
raw, true = idr['PO-Item Amount'].sum(), (idr['PO-Item Amount'] * idr['PR-Quantity']).sum()
orders = mv.Order.dropna().astype('int64').unique()
with_notif = set(nt.Order.dropna().astype('int64'))
dq = pd.DataFrame([
    ('PO-Item Amount is a unit price, not a line total', len(idr), f'Summed raw: Rp {raw/1e9:,.1f} B. Price x qty: Rp {true/1e9:,.1f} B.', f'Spend would read about {true/raw:.0f}x too low.'),
    ('Stock records do not balance', int((~m.ledger_ok).sum()), f'{(~m.ledger_ok[m.material_no.isin(used.index) & m.material_no.isin(recv.index)]).mean()*100:.1f}% of bought-and-used parts imply negative opening stock.', 'Count stock before large orders.'),
    ('Duplicate rows in the bill of materials', int(bom.duplicated().sum()), 'Same location, part and quantity listed twice.', 'Installed counts would be inflated.'),
    ('Parts without a purchase price', int((m.price_source != 'po').sum()), f'{(m.price_source == "po").mean()*100:.0f}% of parts have a PO price.', 'Money figures use category estimates, flagged.'),
    ('Same part under several numbers', int(twins.group_id.nunique()), f'{len(twins)} part numbers share an identical description.', 'Stock hides under a twin number.'),
    ('Parts issued without a maintenance notification', int(sum(o not in with_notif for o in orders)), f'{np.mean([o in with_notif for o in orders])*100:.1f}% of orders link to a notification.', 'Equipment is inferred from the bill of materials.'),
    ('Maintenance cycles written in many formats', int(mp['Cycle Descriptions'].nunique()), 'For example "1 MON", "12 Month", "Yearly".', 'Cycles normalised to months before use.'),
], columns=['issue', 'n', 'example', 'impact'])

backtest = pd.DataFrame([
    ('Naive mean', .791, .500, None, 'Predicts zero for parts with no history'),
    ('Croston SBA', .787, .613, .560, 'Classic intermittent-demand method'),
    ('TSB', .790, None, None, 'Classic intermittent-demand method'),
    ('PartPulse driver model', .887, .841, None, 'Installed base, PM, notifications, category, procurement'),
    ('Installed-base Empirical Bayes', .772, .587, .743, 'Quantity layer, q95 coverage'),
], columns=['method', 'auc_all', 'auc_cold', 'coverage_q95', 'note'])

cons = mv.groupby(['Material Number', 'ym']).agg(qty=('Quantity', 'sum')).reset_index()
cons_ta = mv[mv.ot == '2030'].groupby(['Material Number', 'ym']).Quantity.sum().rename('qty_ta')
cons = cons.merge(cons_ta, left_on=['Material Number', 'ym'], right_index=True, how='left').fillna({'qty_ta': 0})
cons = cons.rename(columns={'Material Number': 'material_no', 'ym': 'month'})
iss = mv.groupby('ym').agg(lines_total=('Quantity', 'size'))
iss['lines_ta'] = mv[mv.ot == '2030'].groupby('ym').size()
iss = iss.fillna(0).reset_index().rename(columns={'ym': 'month'})

pi = p[p['PO-Currency'] == 'IDR']
over = set(m.loc[(m.mx > 0) & (m.stock > m.mx), 'material_no'])
pct_above_max = pi.loc[pi['PR-Material'].isin(over), 'line_val'].sum() / pi.line_val.sum()

meta = {
    'pct_spend_above_max': round(float(pct_above_max), 4), 'spend_idr_total': round(float(pi.line_val.sum()), 0),
    'source': 'dev_seed', 'as_of_date': AS_OF.strftime('%Y-%m-%d'),
    'data_window': f"{mv['Posting Date'].min():%Y-%m-%d}..{mv['Posting Date'].max():%Y-%m-%d}",
    'holding_rate': HOLD, **{f'service_level_{k}': v for k, v in SL.items()},
    **{f'downtime_cost_per_day_{k}': v for k, v in DT_COST.items()}, 'downtime_days_per_event': DT_DAYS,
    'ta_last_window': f'{TA_START}..2026-01-31', 'next_ta_default': NEXT_TA.strftime('%Y-%m-%d'), 'ta_buffer_days': 14,
}

# ---- write ---------------------------------------------------------------
os.makedirs(os.path.dirname(OUT), exist_ok=True)
if os.path.exists(OUT): os.remove(OUT)
con = sqlite3.connect(OUT)
mat = pd.DataFrame({
    'material_no': m.material_no, 'description': m.desc, 'category': m.cat, 'unit': m.unit, 'mrp_type': m.mrp,
    'criticality': m.crit, 'n_funcloc': m.n_fl, 'installed_qty': m.inst, 'stock': m.stock, 'min_cur': m.mn, 'max_cur': m.mx,
    'unit_price': m.unit_price, 'price_source': m.price_source, 'stock_value': m.unit_price * m.stock,
    'lt_p50': m.lt_p50.round(0), 'lt_p90': m.lt_p90.round(0), 'lt_source': m.lt_source, 'main_supplier': m.main_supplier,
    'qty_issued_17m': m.qty, 'months_active': m.months_active.astype(int),
    'last_issue': m['last'].dt.strftime('%Y-%m-%d'), 'demand_class': m.demand_class, 'health': m.health,
    'trust_score': m.trust_score, 'trust_flags': m.trust_flags})
con.executescript("""
CREATE TABLE materials (material_no INTEGER PRIMARY KEY, description TEXT, category TEXT, unit TEXT, mrp_type TEXT,
  criticality TEXT, n_funcloc INTEGER, installed_qty REAL, stock REAL, min_cur REAL, max_cur REAL, unit_price REAL,
  price_source TEXT, stock_value REAL, lt_p50 REAL, lt_p90 REAL, lt_source TEXT, main_supplier TEXT, qty_issued_17m REAL,
  months_active INTEGER, last_issue TEXT, demand_class TEXT, health TEXT, trust_score REAL, trust_flags TEXT);
CREATE TABLE forecast (material_no INTEGER PRIMARY KEY, p_move REAL, mean_qty REAL, q50 REAL, q90 REAL, q95 REAL,
  base_qty REAL, event_qty REAL, ltd_mean REAL, ltd_var REAL, cold_start INTEGER, drivers TEXT);
CREATE TABLE policy (material_no INTEGER PRIMARY KEY, service_level REAL, safety_stock REAL, rop REAL, min_new REAL,
  max_new REAL, action TEXT, order_qty REAL, order_by_date TEXT, hold_cost_yr REAL, risk_cost_yr REAL, reason TEXT);
CREATE TABLE ta_kit (material_no INTEGER PRIMARY KEY, ta_qty_last REAL, stock REAL, gap REAL, gap_value REAL,
  exceeds_max INTEGER, lt_p90 REAL, criticality TEXT);
CREATE TABLE frontier (scenario TEXT, budget_idr REAL, exp_risk_cost REAL, fill_rate_S REAL, fill_rate_A REAL, n_parts_funded INTEGER);
CREATE TABLE twins (group_id INTEGER, material_no INTEGER, role TEXT);
CREATE TABLE dq_issues (issue TEXT, n INTEGER, example TEXT, impact TEXT);
CREATE TABLE backtest (method TEXT, auc_all REAL, auc_cold REAL, coverage_q95 REAL, note TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE consumption_monthly (material_no INTEGER, month TEXT, qty REAL, qty_ta REAL);
CREATE TABLE issues_monthly (month TEXT PRIMARY KEY, lines_total INTEGER, lines_ta INTEGER);
CREATE TABLE material_location (material_no INTEGER, equipment TEXT, equip_class TEXT);
""")
mat.to_sql('materials', con, if_exists='append', index=False)
pd.DataFrame({'material_no': m.material_no, 'p_move': m.p_move.round(3), 'mean_qty': m.mean_qty.round(2), 'q50': m.q50, 'q90': m.q90,
              'q95': m.q95, 'base_qty': m.base_qty.round(2), 'event_qty': m.event_qty, 'ltd_mean': m.ltd_mean.round(3),
              'ltd_var': m.ltd_var.round(3), 'cold_start': m.cold, 'drivers': m.drivers}).to_sql('forecast', con, if_exists='append', index=False)
pd.DataFrame({'material_no': m.material_no, 'service_level': m.service_level, 'safety_stock': m.safety_stock, 'rop': m.rop,
              'min_new': m.min_new, 'max_new': m.max_new, 'action': m.action, 'order_qty': m.order_qty, 'order_by_date': m.order_by_date,
              'hold_cost_yr': m.hold_cost_yr, 'risk_cost_yr': m.risk_cost_yr, 'reason': m.reason}).to_sql('policy', con, if_exists='append', index=False)
pd.DataFrame({'material_no': tk.material_no, 'ta_qty_last': tk.ta_qty, 'stock': tk.stock, 'gap': tk.gap, 'gap_value': tk.gap_value,
              'exceeds_max': tk.exceeds_max, 'lt_p90': tk.lt_p90.round(0), 'criticality': tk.crit}).to_sql('ta_kit', con, if_exists='append', index=False)
frontier.to_sql('frontier', con, if_exists='append', index=False)
twins.to_sql('twins', con, if_exists='append', index=False)
dq.to_sql('dq_issues', con, if_exists='append', index=False)
backtest.to_sql('backtest', con, if_exists='append', index=False)
pd.DataFrame(list(meta.items()), columns=['key', 'value']).astype(str).to_sql('meta', con, if_exists='append', index=False)
cons.to_sql('consumption_monthly', con, if_exists='append', index=False)
iss.to_sql('issues_monthly', con, if_exists='append', index=False)
material_location.to_sql('material_location', con, if_exists='append', index=False)
con.execute('CREATE INDEX ix_cons ON consumption_monthly(material_no)')
con.execute('CREATE INDEX ix_loc ON material_location(material_no)')
con.commit()

print(f'materials {len(mat)} | ta_kit {len(tk)} (short {(tk.gap > 0).sum()}, exceeds max {tk.exceeds_max.sum()}) | twins groups {twins.group_id.nunique()}')
print('actions', m.action.value_counts().to_dict())
print('health (stock items)', m[m.mrp == 'Stock Item'].health.value_counts().to_dict())
print('frontier', frontier.round(3).to_dict('records')[:3])
print('db size MB', round(os.path.getsize(OUT) / 1e6, 2))
con.close()
