"""Hypothesis tests behind docs/03_EDGE_PROPOSALS.md.  Run: py analysis/edge_tests.py"""
import sys, re
sys.path.insert(0, 'analysis')
from build_mat import build
import pandas as pd, numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

m, (bom, fl, mp, mv, nt, pp, p), _ = build()
st = m.set_index('Material No')
mv = mv.copy(); mv['ot'] = mv.Order.astype(str).str[:4]

print('== E1 Shutdown replay (order type 2030, Nov-25..Jan-26)')
print('2030 orders per month', mv[mv.ot == '2030'].groupby(mv['Posting Date'].dt.to_period('M')).Order.nunique().to_dict())
ta = mv[(mv.ot == '2030') & (mv['Posting Date'] >= '2025-11-01') & (mv['Posting Date'] < '2026-02-01')]
x = st.join(ta.groupby('Material Number').Quantity.sum().rename('ta'), how='inner')
x['gap'] = (x.ta - x.stock).clip(lower=0)
sa = x.crit.isin(['A', 'B'])          # top two tiers (order A>B>C>S)
print(f'kit materials {len(x)} | orders {ta.Order.nunique()} | short today {(x.gap > 0).sum()} (A/B {((x.gap > 0) & sa).sum()}, A {((x.gap > 0) & (x.crit == 'A')).sum()}) | zero stock {(x.stock == 0).sum()}')
print(f'TA need > Max {(x.ta > x.mx).sum()} (A/B {((x.ta > x.mx) & sa).sum()}) | non-stock in kit {(x.mrp == "Non Stock").sum()}')
print(f'gap value (priced items) Rp{(x.gap * x.px).sum() / 1e9:.2f}bn | LT p90 of short parts median {x[x.gap > 0].lt_p90.median():.0f}d, p90 {x[x.gap > 0].lt_p90.quantile(.9):.0f}d')
tk = set(x.index); q = p[p['PR-Material'].isin(tk)]
print('PR lines for kit materials per month', q.groupby(q['PR-Date'].dt.to_period('M')).size().to_dict())

print('\n== E2 Planning lag: requested delivery shorter than achievable lead time')
q = p[p.lt_days >= 0].copy(); q['req'] = (q['PR-Delivery Date'] - q['PR-Date']).dt.days
q = q[q.groupby('PR-Material').lt_days.transform('size') >= 3]
q['l50'] = q.groupby('PR-Material').lt_days.transform('median'); q['rush'] = q.req < .5 * q.l50
print(f'PR lines {len(q)} | rush share {q.rush.mean():.3f} | late share rush {(q[q.rush].slip > 0).mean():.3f} vs normal {(q[~q.rush].slip > 0).mean():.3f}')
qi = q[q['PO-Currency'] == 'IDR']
print(f'rush share of IDR value {qi[qi.rush].line_val.sum() / qi.line_val.sum():.3f} | unit-price ratio rush/normal (median rel. to material median) '
      f'{(qi[qi.rush].unit_px / qi[qi.rush].groupby("PR-Material").unit_px.transform("median")).median():.2f}')

print('\n== E4 Twin materials (identical normalised description, different material numbers)')
m['key'] = m.desc.map(lambda s: re.sub(r'[^A-Z0-9]', '', s.upper()))
d = m[m.key.map(m.key.value_counts()) > 1]
res = [k for k, g in d.groupby('key') if (((g.stock < g.mn) | ((g.stock == 0) & (g.qty > 0))).any() and (g.stock > g.mx).any())]
print(f'groups {d.key.nunique()} | materials {len(d)} | groups with one twin short while a sibling is above Max {len(res)}')

print('\n== E5 Ledger check: receipts (PO qty at PO delivery date) vs issues, walked back from snapshot')
mats = set(mv['Material Number']) & set(p['PR-Material'])
used = mv[mv['Material Number'].isin(mats)].groupby('Material Number').Quantity.sum()
recv = p[p['PR-Material'].isin(mats) & (p['PO-Delivery Date'] <= '2026-09-30') & (p['PO-Delivery Date'] >= '2025-05-06')].groupby('PR-Material')['PR-Quantity'].sum()
r = pd.concat([used.rename('used'), recv.rename('recv')], axis=1).fillna(0)
r['start'] = st.stock.reindex(r.index) + r.used - r.recv
print(f'materials {len(r)} | received/issued median {(r.recv / r.used).median():.2f} | implied opening stock < 0 {(r.start < 0).mean():.3f}')

print('\n== Rejected: notification text -> parts kit')
n = nt.dropna(subset=['Order']).copy(); n['Order'] = n.Order.astype('int64')
mv['cat'] = mv['Material Descriptions'].str.split(',').str[0]
kit = mv.groupby('Order').agg(cats=('cat', set))
dd = n.merge(kit, left_on='Order', right_index=True).sort_values('Notification Date')
dd['txt'] = dd.Description.str.upper() + ' ' + dd['Functional Location'].str.extract(r'_([A-Z]+)-')[0].fillna('X')
c = int(len(dd) * .7); tr, te = dd.iloc[:c], dd.iloc[c:]
v = TfidfVectorizer(ngram_range=(1, 2), min_df=2).fit(tr.txt)
_, idx = NearestNeighbors(n_neighbors=15, metric='cosine').fit(v.transform(tr.txt)).kneighbors(v.transform(te.txt))
top3 = [k for k, _ in Counter(c_ for s in tr.cats for c_ in s).most_common(3)]
hit = [bool(set(k for k, _ in Counter(c_ for j in idx[i] for c_ in tr.iloc[j].cats).most_common(3)) & r_.cats) for i, (_, r_) in enumerate(te.iterrows())]
print(f'category top-3 hit: text kNN {np.mean(hit):.3f} vs popularity baseline {np.mean([bool(set(top3) & s) for s in te.cats]):.3f}')
