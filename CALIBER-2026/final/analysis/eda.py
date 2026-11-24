"""Reproducible EDA for CALIBER 2026 Final - Case 3 Spare Part Intelligence.
Run from repo root:  py analysis/eda.py
All numbers in docs/01_EDA_FINDINGS.md come from this script.
"""
import sys, re
sys.path.insert(0, 'analysis')
from build_mat import build
import pandas as pd, numpy as np

ASOF = pd.Timestamp('2026-11-04')
m, (bom, fl, mp, mv, nt, pp, p), months = build()
mm = m.set_index('Material No')
out = []
def say(*a): print(*a)

say('== Window: movement', mv['Posting Date'].min().date(), '->', mv['Posting Date'].max().date(), f'({months:.1f} months)')
say('materials', len(m), m.mrp.value_counts().to_dict())

# 1. Inventory health (stock items)
st = m[m.mrp == 'Stock Item'].copy()
say('\n== 1. Inventory health, stock items n =', len(st))
say('below min', round((st.stock < st.mn).mean(), 3), '| zero', round((st.stock == 0).mean(), 3),
    '| over max', round((st.stock > st.mx).mean(), 3), '| no issue in window', round((st.qty == 0).mean(), 3))
say('below-min rate by criticality', st.assign(b=st.stock < st.mn).groupby('crit').b.mean().round(3).to_dict())
say('no-issue rate by criticality', st.assign(b=st.qty == 0).groupby('crit').b.mean().round(3).to_dict())
ns = m[m.mrp == 'Non Stock']
say('non-stock items holding stock', round((ns.stock > 0).mean(), 3))
risk = st[(st.stock < st.mn) & (st.qty > 0)]
say('below-min AND consumed', len(risk), '| crit A/B', int(risk.crit.isin(['A', 'B']).sum()))
z = st[(st.stock == 0) & (st.qty > 0)]
say('zero stock AND consumed', len(z), '| crit A/B', int(z.crit.isin(['A', 'B']).sum()))

v = st[st.px.notna()].copy(); v['val'] = v.stock * v.px
v['excess'] = (v.stock - v.mx).clip(lower=0) * v.px; v['dead'] = np.where(v.qty == 0, v.val, 0)
say(f'priced stock items {len(v)} | value Rp{v.val.sum()/1e9:.1f}bn | above-max Rp{v.excess.sum()/1e9:.1f}bn | no-issue Rp{v.dead.sum()/1e9:.1f}bn')
say('top-10% items value share', round(v.val.nlargest(int(len(v) * .1)).sum() / v.val.sum(), 3))

# 2. Min/Max calibration vs lead-time demand
c = st[(st.qty > 0) & st.lt_med.notna()].copy(); c['ltd'] = c.mon_dem / 30.44 * c.lt_med
say('\n== 2. Min vs lead-time demand, n =', len(c))
say('Min/LTD quantiles', (c.mn / c.ltd).quantile([.1, .25, .5, .75, .9]).round(2).to_dict())
say('Min < LTD', round((c.mn < c.ltd).mean(), 3), '| Min > 3x LTD', round((c.mn > 3 * c.ltd).mean(), 3))
cov = st.stock / st.mon_dem.replace(0, np.nan)
say('months of cover (moving items)', cov.quantile([.25, .5, .75, .9]).round(1).to_dict())

# 3. Demand pattern
mv['ym'] = mv['Posting Date'].dt.to_period('M')
M = mv.groupby(['Material Number', 'ym']).Quantity.sum().unstack(fill_value=0)
nz = (M > 0).sum(axis=1); adi = M.shape[1] / nz
cv2 = M.apply(lambda r: (r[r > 0].std(ddof=0) / r[r > 0].mean()) ** 2 if (r > 0).sum() > 1 else np.nan, axis=1)
cls = np.select([nz <= 1, (adi < 1.32) & (cv2 < .49), (adi >= 1.32) & (cv2 < .49), (adi < 1.32) & (cv2 >= .49)],
                ['single', 'smooth', 'intermittent', 'erratic'], 'lumpy')
say('\n== 3. Demand classes (Syntetos-Boylan)', pd.Series(cls).value_counts().to_dict())
say('issue lines per month', {str(k): v for k, v in mv.groupby('ym').size().items()})

# 4. Procurement
q = p[p.lt_days >= 0]
say('\n== 4. Procurement, PR-PO lines', len(p), '| negative LT dropped', int((p.lt_days < 0).sum()))
say('PR->PO delivery LT median', q.lt_days.median(), 'p90', q.lt_days.quantile(.9))
say('PO delivery later than PR requested', round((q.slip > 0).mean(), 3), '| >30d late', round((q.slip > 30).mean(), 3))
say('LT by currency (median days)', q.groupby('PO-Currency').lt_days.median().to_dict())
g = q.groupby('PR-Material').lt_days.agg(['count', 'median', 'std']); g = g[g['count'] >= 3]
say('within-material LT CV median', round((g['std'] / g['median']).median(), 2))
say('materials with exactly 1 supplier', round((q.groupby('PR-Material')['PO-Supplier Code'].nunique() == 1).mean(), 3))
pi = p[p['PO-Currency'] == 'IDR']; tot = pi['line_val'].sum()
never = set(m[m.qty == 0]['Material No']); over = set(st[st.stock > st.mx]['Material No'])
say(f'IDR spend Rp{tot/1e9:.1f}bn | on never-issued mats {pi[pi["PR-Material"].isin(never)]["line_val"].sum()/tot:.3f}'
    f' | on currently over-max mats {pi[pi["PR-Material"].isin(over)]["line_val"].sum()/tot:.3f}')
b = m[m.n_pr > 0]
say('purchased materials', len(b), '| bought >2x what was issued', round((b.pr_qty / b.qty.replace(0, np.nan) > 2).mean(), 3))
pr_ = p.groupby('PR-Material').unit_px.agg(['min', 'max', 'count']); pr_ = pr_[pr_['count'] > 1]
say('same material unit-price max/min median', round((pr_['max'] / pr_['min']).median(), 2))

# 5. Notifications
n = nt.copy(); n['Order'] = n['Order'].astype('Int64')
n['dur'] = (n['Completion by Date'] - n['Notification Date']).dt.days
n['late'] = (n['Completion by Date'] - n['Required End']).dt.days
n['crit'] = n['Functional Location'].map(fl.set_index('Functional Location')['FuncLoc Criticallity'])
say('\n== 5. Notifications', len(n), n.Status.value_counts().to_dict())
say(n.groupby('Priority').agg(dur_med=('dur', 'median'), late_share=('late', lambda s: (s > 0).sum() / s.notna().sum())).round(2).to_dict())
say('completion late share by FL criticality', n.groupby('crit').late.apply(lambda s: (s > 0).sum() / s.notna().sum()).round(2).to_dict())
o = n[n.Status == 'In Progress']
say('open backlog', len(o), 'median age (days, vs 30-Sep-26)', (pd.Timestamp('2026-09-30') - o['Notification Date']).dt.days.median(),
    'past required end', round((o['Required End'] < pd.Timestamp('2026-09-30')).mean(), 3))
mo = set(mv.Order); no = set(n.Order.dropna())
say('movement orders traceable to a notification', round(len(mo & no) / len(mo), 3), '| notifs with parts issued', round(n.Order.isin(mo).mean(), 3))
fi = mv.groupby('Order')['Posting Date'].min()
say('notif -> first part issue (days) median', (n.Order.map(fi) - n['Notification Date']).dt.days.median())

# 6. PM plan forward look
def months_of(s):
    s = s.upper(); g_ = re.match(r'(\d+)?\s*(\w+)', s); k = int(g_.group(1)) if g_.group(1) else 1; u = g_.group(2)
    return k * 12 if u.startswith('YEAR') else k if u.startswith('MONTH') else k * 12 / 52
mp['cyc_m'] = mp['Cycle Descriptions'].map(months_of)
def nd(r):
    d = r['Start of cycle']; s = pd.DateOffset(months=int(round(r.cyc_m))) if r.cyc_m >= 1 else pd.Timedelta(days=r.cyc_m * 30.44)
    while d < ASOF: d = d + s
    return d
mp['next'] = mp.apply(nd, axis=1)
say('\n== 6. PM plan: FL with BoM', round(mp['Functional Location'].isin(set(bom['Functional Loc.'])).mean(), 3))
h = mp[mp.next < ASOF + pd.DateOffset(months=12)]
say('PM items due next 12m', len(h), '| by month', {str(k): v for k, v in h.groupby(h.next.dt.to_period('M')).size().items()})
ov = mp[mp['Maint. item text'].str.contains('overhaul|Overhaul|cleaning|Recert|recert|change') & (mp.next < ASOF + pd.DateOffset(months=6))]
j = ov.merge(bom, left_on='Functional Location', right_on='Functional Loc.').merge(m[['Material No', 'stock', 'lt_med']], on='Material No')
j['dtp'] = (j.next - ASOF).dt.days; r = j[j.stock < j['Installed Qty']]
say('intrusive PM events next 6m', ov['Maintenance Item'].nunique(), '| BoM lines', len(j), '| short lines', len(r),
    '| events w/ short part', r['Maintenance Item'].nunique(),
    '| events w/ short part whose LT > days-to-PM', r[r.lt_med > r.dtp]['Maintenance Item'].nunique())

# 7. Gaps & hotspots not covered above
say('\n== 7. Extra')
crit = fl.set_index('Functional Location')['FuncLoc Criticallity']
say('notifs on FL with null criticality', int(n.crit.isna().sum()), '| prefixes', n[n.crit.isna()]['Functional Location'].str.split('_').str[0].value_counts().to_dict())
sa = fl[fl['FuncLoc Criticallity'].isin(['A', 'B'])]['Functional Location']
say('A/B FLs', len(sa), '| without PM plan', int((~sa.isin(mp['Functional Location'])).sum()),
    '| without BoM', int((~sa.isin(bom['Functional Loc.'])).sum()),
    '| without both', int((~sa.isin(mp['Functional Location']) & ~sa.isin(bom['Functional Loc.'])).sum()))
top = n['Functional Location'].value_counts()
say('top-10 FL by notifs', top.head(10).to_dict(), '| share of all notifs', round(top.head(10).sum() / len(n), 3))
bf = n['Functional Location'].str.match(r'PX_BF-1\d\d$')
say('furnace PX_BF-1xx notifs', int(bf.sum()), '| share', round(bf.mean(), 3), '| Emergency', int((bf & (n.Priority == 'Emergency')).sum()))
bfo = set(n[bf].Order.dropna()); x = mv[mv.Order.isin(bfo)]
say('parts issued on furnace orders: lines', len(x), '| top', x.groupby('Material Descriptions').size().nlargest(5).to_dict())
say('notifs per month', {str(k): v for k, v in n.groupby(n['Notification Date'].dt.to_period('M')).size().items()})
sp = q.groupby('PO-Supplier Name').agg(n=('slip', 'size'), late=('slip', lambda s: (s > 0).mean())).query('n >= 50')
say('suppliers n>=50', len(sp), '| late share min/median/max', round(sp.late.min(), 2), round(sp.late.median(), 2), round(sp.late.max(), 2),
    '| worst', sp.late.nlargest(3).round(2).to_dict())
sup = pi.groupby('PO-Supplier Name')['line_val'].sum().sort_values(ascending=False)
say('top-10 supplier spend share', round(sup.head(10).sum() / tot, 3), '| top-20% suppliers', round(sup.head(int(len(sup) * .2)).sum() / tot, 3))
say('materials on >1 FL', int((m.n_fl > 1).sum()), '| max FLs per material', int(m.n_fl.max()),
    '| consumed materials on >=5 FL', int(((m.n_fl >= 5) & (m.qty > 0)).sum()))
