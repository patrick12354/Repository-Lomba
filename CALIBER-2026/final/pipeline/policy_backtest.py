"""Policy backtest: replay the actual goods issues of 2026-03-01..2026-09-30 against
  (a) the current BoM Min-Max, and
  (b) the PartPulse policy computed point-in-time on 2026-03-01 (forecast trained only on folds that ended before
      that day, lead times only from PRs raised before it),
then report business metrics: fill rate (units and issue lines; all and A/B), stockout-days on A/B parts,
average inventory value and number of purchase orders.

Run from repo root after build_db.py (build_db.py calls it at the end):  py pipeline/policy_backtest.py [--strict]
Writes table policy_backtest and rows policy_* in table backtest of app/data/partpulse.db.

Simulation rules (same for every policy): continuous review, order up to Max when inventory position <= Min/ROP,
unmet demand is lost (it would be an emergency purchase in reality), every policy starts the window at its own Max,
replenishment lead times are drawn per part from its pre-cut lead-time history (common random numbers across policies).
"""
import os, sys, json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
src = (ROOT / 'pipeline' / 'build_db.py').read_text(encoding='utf-8').split('# rolling-origin validation')[0]
g = {'__file__': str(ROOT / 'pipeline' / 'build_db.py'), '__name__': 'policy_backtest'}
exec(compile(src, 'build_db[engine]', 'exec'), g)
pd, np = g['pd'], g['np']
from scipy.stats import norm

mat, mv, p, EVENT, H = g['mat'], g['mv'], g['p'], g['EVENT'], g['H']
C, E = pd.Timestamp('2026-03-01'), pd.Timestamp('2026-10-01'); T = (E - C).days
N = len(mat); idx = mat.index
crit = mat.criticality.values; price = mat.unit_price.fillna(0).values; po = (mat.price_source == 'po').values
rng = np.random.default_rng(11)

# ---- point-in-time lead times (PRs raised before C)
q = p[(p.lt_days >= 0) & (p['PR-Date'] < C)].copy(); q['cat'] = q['PR-Material Desc'].str.split(',').str[0]
lm = q.groupby('PR-Material').lt_days.agg(n='size', p50='median', p90=lambda s: s.quantile(.9), sd='std').reindex(idx)
lc = q.groupby('cat').lt_days.agg(n='size', p50='median', p90=lambda s: s.quantile(.9), mean='mean', sd='std')
lc['cv'] = lc.sd / lc['mean']; catl = lc.reindex(mat.category).set_index(idx); has = (catl.n.fillna(0) >= 5).values
gcv = q.lt_days.std() / q.lt_days.mean()
L = lm.p50.fillna(catl.p50.where(has)).fillna(q.lt_days.median()).values.astype(float)
sL = np.where(lm.n.fillna(0).values >= 3, lm.sd.fillna(0).values, L * catl.cv.where(has).fillna(gcv).values)
sL = np.nan_to_num(sL)
own_lt = q.groupby('PR-Material').lt_days.apply(np.array)
K = 40                                                    # pre-drawn lead time per (part, k-th order): common random numbers
LT = np.empty((N, K))
for j, i in enumerate(idx):
    s_ = own_lt.get(i)
    LT[j] = rng.choice(s_, K) if s_ is not None and len(s_) >= 3 else np.maximum(1, rng.gamma((L[j] / max(sL[j], 1)) ** 2, max(sL[j], 1) ** 2 / L[j], K))
LT = np.maximum(1, np.round(LT)).astype(int)

# ---- point-in-time forecast at C (rolling engine, folds ending before C)
STRICT = '--strict' in sys.argv                          # forecast without the BoM Min/Max/MRP snapshot
clf, reg = g['fit'](pd.Timestamp('2025-12-01'), STRICT)
_, _, pb, mean, _ = g['forecast_at'](clf, reg, C, H, STRICT)
pb = pb.reindex(idx).values; mean = mean.reindex(idx).clip(lower=0).values

# ---- lead-time demand simulation at C (compound Poisson, sizes seen before C)
bl = mv[(~mv.ot.isin(EVENT)) & (mv['Posting Date'] < C)]
own_sz = bl.groupby('Material Number').Quantity.apply(np.array); cat_sz = bl.groupby('cat').Quantity.apply(np.array)
lam = -np.log(1 - np.clip(pb, 0, .995)); NS = 1000
LTD = np.zeros((N, NS), dtype=np.float32); esz2 = np.zeros(N)
for j, (i, c) in enumerate(zip(idx, mat.category)):
    if lam[j] <= 0 or mean[j] <= 0: continue
    sz = own_sz.get(i)
    if sz is None or len(sz) < 3: sz = cat_sz.get(c, np.array([1]))
    sz = sz.astype(float) * (mean[j] / (lam[j] * sz.mean())); esz2[j] = (sz ** 2).mean()
    Ls = rng.gamma((L[j] / sL[j]) ** 2, sL[j] ** 2 / L[j], NS) if sL[j] > 0 else np.full(NS, L[j])
    Nn = rng.poisson(lam[j] * Ls / H)
    LTD[j] = np.bincount(np.repeat(np.arange(NS), Nn), weights=rng.choice(sz, Nn.sum()), minlength=NS)
d_day = mean / H; ltd_m = d_day * L; ltd_v = L * lam / H * esz2 + d_day ** 2 * sL ** 2
D_yr = mean * 365 / H
pr_med = q.groupby('PR-Material')['PR-Quantity'].median().reindex(idx).values

def partpulse_policy(SL):
    """Same rules as build_db.py (ROP, EOQ capped at 1 year, A-critical insurance floor) at service levels SL."""
    slv = np.array([SL[c] for c in crit])
    rop = np.where(pb >= g['P_LOW'], ltd_m + norm.ppf(slv) * np.sqrt(ltd_v), np.array([np.quantile(LTD[j], slv[j]) for j in range(N)]))
    rop = np.ceil(rop - 1e-9).clip(min=0)
    with np.errstate(divide='ignore', invalid='ignore'):
        eoq = np.where((price > 0) & (D_yr > 0), np.sqrt(2 * D_yr * g['ORDER_COST'] / (g['HOLD'] * price)), np.nan)
    eoq = np.where(np.isnan(eoq), np.where(np.isnan(pr_med), np.ceil(D_yr / 4), pr_med), eoq)
    Q = np.minimum(np.ceil(eoq), np.maximum(1, np.ceil(D_yr)))
    Q = np.where((rop > 0) | (D_yr >= .5), np.maximum(Q, 1), 0)
    mx = rop + Q
    mx = np.where((crit == 'A') & (mat.mrp_type.values == 'Stock Item'), np.maximum(mx, 1), mx)
    return rop, mx

def classic_policy(SL):
    """Best non-AI alternative, retuned point-in-time at C with the same service levels and lead times:
    textbook ROP = mean daily use x lead time + z x sd x sqrt(lead time) from the last 180 days of history,
    Max = ROP + the same lot-size rule. Parts with no use in those 180 days keep today's SAP Min/Max,
    because a history-only method has nothing to go on for them."""
    h0 = C - pd.Timedelta(days=180)
    hist = bl[bl['Posting Date'] >= h0]
    daily = np.zeros((N, 180)); pos_ = idx.get_indexer(hist['Material Number']); ok_ = pos_ >= 0
    np.add.at(daily, (pos_[ok_], (hist['Posting Date'][ok_] - h0).dt.days.values), hist.Quantity.values[ok_])
    mu = daily.mean(axis=1); sd = daily.std(axis=1); used = daily.sum(axis=1) > 0
    slv = np.array([SL[c] for c in crit])
    rop = np.ceil(mu * L + norm.ppf(slv) * sd * np.sqrt(L) - 1e-9).clip(min=0)
    dy = mu * 365
    with np.errstate(divide='ignore', invalid='ignore'):
        eoq = np.where((price > 0) & (dy > 0), np.sqrt(2 * dy * g['ORDER_COST'] / (g['HOLD'] * price)), np.nan)
    eoq = np.where(np.isnan(eoq), np.where(np.isnan(pr_med), np.ceil(dy / 4), pr_med), eoq)
    Q = np.where(dy > 0, np.maximum(1, np.minimum(np.ceil(eoq), np.maximum(1, np.ceil(dy)))), 0)
    mn = np.where(used, rop, mat.min_cur.values.astype(float)); mx = np.where(used, rop + Q, mat.max_cur.values.astype(float))
    return mn, mx

# ---- actual daily issues in the replay window
w = mv[(mv['Posting Date'] >= C) & (mv['Posting Date'] < E)]
dem = np.zeros((N, T)); pos = idx.get_indexer(w['Material Number']); ok = pos >= 0
np.add.at(dem, (pos[ok], (w['Posting Date'][ok] - C).dt.days.values), w.Quantity.values[ok])
movers = dem.sum(axis=1) > 0; ab = np.isin(crit, ['A', 'B'])

def simulate(s, S):
    on = S.astype(float).copy(); pipe = np.zeros((N, T + LT.max() + 1)); onord = np.zeros(N); k = np.zeros(N, int)
    served = np.zeros(N); lines = np.zeros(N); lines_ok = np.zeros(N); inv = np.zeros(T); inv_po = np.zeros(T); so = np.zeros(N); n_ord = 0
    for t in range(T):
        on += pipe[:, t]; onord -= pipe[:, t]
        d = dem[:, t]; sv = np.minimum(on, d); on -= sv; served += sv
        lines += d > 0; lines_ok += (d > 0) & (sv >= d)
        ip = on + onord
        trig = np.where((ip <= s) & (S > ip) & (S > 0))[0]
        for j in trig:
            qty = S[j] - ip[j]; lt = LT[j, k[j] % K]; k[j] += 1
            pipe[j, t + lt] += qty; onord[j] += qty; n_ord += 1
        inv[t] = (on * price).sum(); inv_po[t] = (on * price * po).sum(); so += on <= 0
    tot = dem.sum(axis=1)
    f = lambda msk: served[msk].sum() / tot[msk].sum()
    fl = lambda msk: lines_ok[msk].sum() / lines[msk].sum()
    return dict(fill_units=f(movers), fill_units_AB=f(movers & ab), fill_lines=fl(movers), fill_lines_AB=fl(movers & ab),
                stockout_days_AB=float(so[movers & ab].sum()), avg_inv_idr=float(inv.mean()), avg_inv_idr_po=float(inv_po.mean()), orders=int(n_ord))

SL_DEF = {'A': .99, 'B': .97, 'C': .95, 'S': .90}; SL_LEAN = {'A': .95, 'B': .90, 'C': .85, 'S': .80}   # high-availability alternative vs the recommended lean policy
sfx = '_strict' if STRICT else ''
runs, notes = {}, []
if not STRICT:
    runs['policy_minmax_current'] = (mat.min_cur.values.astype(float), mat.max_cur.values.astype(float))
    notes.append('current BoM Min/Max snapshot held constant over the window')
    runs['policy_classic_lean'] = classic_policy(SL_LEAN); notes.append(f'Best non-AI alternative: textbook ROP from the last 180 days of use, same lean service levels {SL_LEAN} and lead times, retuned on {C.date()}; parts with no recent use keep SAP Min/Max')
runs['policy_partpulse' + sfx] = partpulse_policy(SL_DEF); notes.append(f'PartPulse at high-availability service levels {SL_DEF}, computed point-in-time on {C.date()}' + (', forecast without Min/Max/MRP snapshot' if STRICT else ''))
runs['policy_partpulse_lean' + sfx] = partpulse_policy(SL_LEAN); notes.append(f'PartPulse at lean service levels {SL_LEAN}, computed point-in-time on {C.date()}' + (', forecast without Min/Max/MRP snapshot' if STRICT else ''))
res = {k: simulate(*v) for k, v in runs.items()}
out = pd.DataFrame(res).T.reset_index().rename(columns={'index': 'policy'})
out['note'] = notes

DB = Path(os.environ.get('PARTPULSE_DB', ROOT / 'app' / 'data' / 'partpulse.db'))
con = sqlite3.connect(DB)
con.execute('create table if not exists policy_backtest (policy TEXT PRIMARY KEY, fill_units REAL, fill_units_AB REAL, fill_lines REAL, fill_lines_AB REAL, '
            'stockout_days_AB REAL, avg_inv_idr REAL, avg_inv_idr_po REAL, orders INTEGER, note TEXT)')
for k in runs:
    con.execute('delete from policy_backtest where policy = ?', (k,)); con.execute('delete from backtest where method = ?', (k,))
out.to_sql('policy_backtest', con, if_exists='append', index=False)
for r in out.itertuples():
    con.execute('insert into backtest (method, auc_all, auc_cold, coverage_q95, note) values (?, NULL, NULL, ?, ?)',
                (r.policy, r.fill_lines_AB, json.dumps({'fill_units': round(r.fill_units, 4), 'fill_units_AB': round(r.fill_units_AB, 4),
                 'fill_lines_AB': round(r.fill_lines_AB, 4), 'stockout_days_AB': r.stockout_days_AB, 'avg_inv_idr': round(r.avg_inv_idr),
                 'avg_inv_idr_po': round(r.avg_inv_idr_po), 'orders': r.orders, 'window': f'{C.date()}..{(E - pd.Timedelta(days=1)).date()}'})))
con.commit(); con.close()

print(f'policy backtest {C.date()}..{(E - pd.Timedelta(days=1)).date()} | parts with demand {movers.sum()} (A/B {(movers & ab).sum()})')
pd.set_option('display.width', 220)
show = out.drop(columns='note').copy()
show['avg_inv_idr'] = (show.avg_inv_idr / 1e9).round(1).astype(str) + ' B'; show['avg_inv_idr_po'] = (show.avg_inv_idr_po / 1e9).round(1).astype(str) + ' B'
print(show.round(3).to_string(index=False))
