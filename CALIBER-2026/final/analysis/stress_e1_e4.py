"""Stress tests for edges E1-E4 in docs/03_EDGE_PROPOSALS.md.  Run: py analysis/stress_e1_e4.py
Each block tries to break one claim: duplicates, leakage, trivial definitions, mechanical effects,
single-event risk, and sensitivity to thresholds.
Data-level checks on the edge claims; E3 here tests the legacy analysis/forecast_backtest.py model.
For the production engine (pipeline/build_db.py) see analysis/stress_prod.py.
Importing forecast_backtest rewrites analysis/backtest_predictions.csv (same values): `git checkout` it after.
"""
import sys, re, io, contextlib
sys.path.insert(0, 'analysis')
import pandas as pd, numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

with contextlib.redirect_stdout(io.StringIO()):   # reuse the backtest objects, mute its report
    import forecast_backtest as fb
m, mv, p, pp, bom = fb.m, fb.mv, fb.p, fb.pp, fb.bom
st = m.set_index('Material No')
# committee answer (4 Nov): criticality order A>B>C>S, so recompute each material's strongest class
R4 = {'A': 4, 'B': 3, 'C': 2, 'S': 1}
cr = bom.merge(fb.fl if hasattr(fb, 'fl') else pd.read_excel('data/FuncLoc list.xlsx'), left_on='Functional Loc.', right_on='Functional Location', how='left')
st['crit'] = cr.assign(r=cr['FuncLoc Criticallity'].map(R4)).groupby('Material No').r.max().map({v: k for k, v in R4.items()})
m['crit'] = m['Material No'].map(st.crit)
pd_ =p.drop_duplicates(subset=list(pp.columns))   # PR PO has exact duplicate rows
print(f'PR PO rows {len(p)} | exact duplicates {len(p) - len(pd_)} ({1 - len(pd_) / len(p):.1%}) | Movement exact duplicates {mv.drop(columns="otype").duplicated().sum()}')
print(f'spend raw Rp{p[p["PO-Currency"] == "IDR"].line_val.sum() / 1e9:,.1f}bn vs dedup Rp{pd_[pd_["PO-Currency"] == "IDR"].line_val.sum() / 1e9:,.1f}bn (IDR lines)')

def mat_lt(q):
    g = q[q.lt_days >= 0].groupby('PR-Material').lt_days
    return g.quantile(.9), g.size()

# ------------------------------------------------------------------ E1
print('\n== E1 Shutdown replay')
ta = mv[(mv.otype == '2030') & (mv['Posting Date'] >= '2025-11-01') & (mv['Posting Date'] < '2026-02-01')]
x = st.join(ta.groupby('Material Number').Quantity.sum().rename('ta'), how='inner')
sa = x.crit.isin(['A', 'B'])
over = x.ta > x.mx
print(f'TA need > Max: {over.sum()} | of which Max==0: {(over & (x.mx == 0)).sum()} | Non Stock: {(over & (x.mrp == "Non Stock")).sum()} '
      f'| Stock Item with Max>0: {(over & (x.mx > 0) & (x.mrp == "Stock Item")).sum()} (A/B {(over & (x.mx > 0) & (x.mrp == "Stock Item") & sa).sum()})')
for s in [0.5, 0.75, 1.0]:
    short = x.ta * s > x.stock
    print(f'  scale {s:.2f}: short {short.sum()} (A/B {(short & sa).sum()}) | Stock Items only {(short & (x.mrp == "Stock Item")).sum()}')
gap = (x.ta - x.stock).clip(lower=0)
pxd = pd_[pd_['PO-Currency'] == 'IDR'].groupby('PR-Material').unit_px.median()
gv = (gap * x.px).dropna().sort_values(ascending=False); gvd = (gap * pxd.reindex(x.index)).dropna()
print(f'gap value raw Rp{gv.sum() / 1e9:.2f}bn vs dedup-price Rp{gvd.sum() / 1e9:.2f}bn | priced short parts {int((gv > 0).sum())} of {(gap > 0).sum()} '
      f'| top-5 parts = {gv.head(5).sum() / gv.sum():.0%} of gap value')
print('  top-5 gap:', [(st.desc.get(i, '')[:40], round(v / 1e9, 2)) for i, v in gv.head(5).items()])
qtop = x.ta.sort_values(ascending=False)
print(f'kit concentration: top-10 materials = {qtop.head(10).sum() / qtop.sum():.0%} of TA qty (mixed units)')
# single-event risk: do other event windows reuse the same parts?
def kit(otype, a, b):
    w = mv[(mv.otype == otype) & (mv['Posting Date'] >= a) & (mv['Posting Date'] < b)]
    return set(w['Material Number'])
nov, dec = kit('2030', '2025-11-01', '2025-12-01'), kit('2030', '2025-12-01', '2026-01-01')
rest2030 = set(mv[(mv.otype == '2030') & ~mv.index.isin(ta.index)]['Material Number'])
e2090 = set(mv[mv.otype == '2090']['Material Number'])
K = set(x.index); J = lambda a, b: len(a & b) / max(len(a | b), 1)
print(f'Nov vs Dec 2030 kit Jaccard {J(nov, dec):.2f} | TA kit parts also used by non-TA 2030 orders {len(K & rest2030) / len(K):.0%} '
      f'| by 2090 orders {len(K & e2090) / len(K):.0%}')
base_users = set(mv[~mv.otype.isin(['2030', '2090'])]['Material Number'])
print(f'TA kit parts that ALSO appear in routine (non-event) demand: {len(K & base_users) / len(K):.0%}')
# does procurement react around the TA? (dedup, rush share by month for kit parts)
q = pd_[pd_['PR-Material'].isin(K) & (pd_.lt_days >= 0)].copy()
q['req'] = (q['PR-Delivery Date'] - q['PR-Date']).dt.days
q['l50'] = q['PR-Material'].map(pd_[pd_.lt_days >= 0].groupby('PR-Material').lt_days.median())
q['rush'] = q.req < .5 * q.l50
mo = q.groupby(q['PR-Date'].dt.to_period('M')).agg(lines=('rush', 'size'), rush=('rush', 'mean'))
print('kit PR lines/month (dedup):', {str(k): v for k, v in mo.lines.items()})
print('kit rush share/month:', {str(k): round(v, 2) for k, v in mo.rush.items()})
# readiness clock: if next TA is N days away, how many short S/A parts are already past "TA - LT p90"?
lt90, nlt = mat_lt(pd_)
xs = x[gap > 0].assign(ltp=lambda d: lt90.reindex(d.index), n=lambda d: nlt.reindex(d.index).fillna(0))
print(f'short parts with no own lead-time history: {xs.ltp.isna().sum()} of {len(xs)} | with <3 PO lines: {(xs.n < 3).sum()}')
ltf = xs.ltp.fillna(lt90.median())
for N in [60, 90, 120, 180, 270]:
    late = ltf > N
    print(f'  TA in {N:>3}d: short parts already past safe-order date {late.sum()} (A/B {(late & xs.crit.isin(["A", "B"])).sum()})')

# ------------------------------------------------------------------ E2
print('\n== E2 Planning lag')
def rush_table(q_, prior_only):
    q_ = q_[q_.lt_days >= 0].sort_values('PR-Date').copy()
    q_['req'] = (q_['PR-Delivery Date'] - q_['PR-Date']).dt.days
    g = q_.groupby('PR-Material').lt_days
    if prior_only:   # what the system could have known when the PR was raised
        q_['l50'] = g.transform(lambda s: s.expanding().median().shift(1)); q_['n'] = g.cumcount()
    else:
        q_['l50'] = g.transform('median'); q_['n'] = g.transform('size') - 1
    return q_[q_.n >= 3]
for name, src, prior in [('raw, in-sample LT', p, False), ('dedup, in-sample LT', pd_, False), ('dedup, prior-only LT', pd_, True)]:
    q_ = rush_table(src, prior)
    for thr in ([0.3, 0.5, 0.7] if name.startswith('dedup, prior') else [0.5]):
        r = q_.req < thr * q_.l50
        print(f'  {name:22s} thr {thr}: lines {len(q_)} rush {r.mean():.3f} | late rush {(q_[r].slip > 0).mean():.3f} vs normal {(q_[~r].slip > 0).mean():.3f} '
              f'| late>30d rush {(q_[r].slip > 30).mean():.3f} vs normal {(q_[~r].slip > 30).mean():.3f}')
q_ = rush_table(pd_, True); r = q_.req < .5 * q_.l50
print(f'  actual LT / expected LT (median): rush {(q_[r].lt_days / q_[r].l50).median():.2f} vs normal {(q_[~r].lt_days / q_[~r].l50).median():.2f}  '
      '(rush < 1 => supplier does speed up, but not enough to meet the request)')
rho_line = spearmanr(q_.req, q_.lt_days).correlation
mm = q_.groupby('PR-Material').agg(req=('req', 'median'), ltm=('lt_days', 'median'))
print(f'  does the requester know the lead time? Spearman(req, actual LT): line {rho_line:.2f} | material medians {spearmanr(mm.req, mm.ltm).correlation:.2f}')
print(f'  requested-days distribution: p10 {q_.req.quantile(.1):.0f} p50 {q_.req.median():.0f} p90 {q_.req.quantile(.9):.0f} | expected LT p50 {q_.l50.median():.0f}')

# ------------------------------------------------------------------ E3
print('\n== E3 Cold-start forecast')
moved, cold, X0, X1, y0 = fb.moved, fb.cold, fb.X0, fb.X1, fb.y0
def fit_auc(cols, seed=0):
    c = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=30, verbose=-1, random_state=seed)
    c.fit(X0[cols], (y0 > 0).astype(int)); s = pd.Series(c.predict_proba(X1[cols])[:, 1], index=X1.index)
    return s, roc_auc_score(moved, s), roc_auc_score(moved[cold], s[cold])
allc = list(X0.columns)
snap = ['mn', 'mx', 'mrp']                        # BoM snapshot fields, taken after the test window (like stock)
for name, cols in [('as in deck', allc), ('drop Min/Max/MRP snapshot', [c for c in allc if c not in snap]),
                   ('drop snapshot + procurement', [c for c in allc if c not in snap + ['n_pr', 'pr_qty', 'lt_med']]),
                   ('installed base + FL drivers only', ['n_fl', 'inst', 'crit_r', 'fl_notif', 'fl_emerg', 'fl_pm', 'cat'])]:
    s, a, ac = fit_auc(cols)
    print(f'  {name:34s} AUC all {a:.3f} | cold {ac:.3f}')
    if name.startswith('drop Min'): s_clean = s
F = fb.F
print('  single-feature AUC (all | cold):', {c: (round(roc_auc_score(moved, F[c].fillna(0)), 3), round(roc_auc_score(moved[cold], F[c].fillna(0)[cold]), 3))
                                          for c in ['n_fl', 'inst', 'fl_pm', 'fl_notif', 'mn', 'mx']})
rng = np.random.default_rng(0); sba = fb.pred['sba']
def boot(mask):
    idx = np.where(mask)[0]; d = []
    for _ in range(300):
        b = rng.choice(idx, len(idx)); yy = moved.values[b]
        d.append(roc_auc_score(yy, s_clean.values[b]) - roc_auc_score(yy, sba.values[b] + 1e-9 * F.inst.values[b]))
    return np.percentile(d, [2.5, 97.5])
print(f'  bootstrap 95% CI of AUC gain (clean model - SBA): all {boot(np.ones(len(moved), bool)).round(3)} | cold {boot(cold.values).round(3)}')
top = s_clean[cold].sort_values(ascending=False)
k = int(moved[cold].sum())
print(f'  cold-start precision@{k}: {moved[cold][top.index[:k]].mean():.2f} (base rate {moved[cold].mean():.3f}) | '
      f'recall in top 10% of cold parts {moved[cold][top.index[:len(top) // 10]].sum() / k:.2f}')
print(f'  quantity bias (deck): lgbm_2part {fb.pred.lgbm_2part.sum() / fb.y.sum() - 1:+.0%} | hybrid {fb.pred.hybrid.sum() / fb.y.sum() - 1:+.0%} | eb {fb.pred.eb_installed.sum() / fb.y.sum() - 1:+.0%}')

# ------------------------------------------------------------------ E4
print('\n== E4 Twin materials')
m['key'] = m.desc.map(lambda s: re.sub(r'[^A-Z0-9]', '', s.upper()))
d = m[m.key.map(m.key.value_counts()) > 1].copy()
d['has_spec'] = d.desc.str.contains(r'\d'); d['ntok'] = d.desc.str.split(r'[\s,]+').str.len()
G = d.groupby('key')
gi = pd.DataFrame({'n': G.size(), 'units': G.unit.nunique(), 'spec': G.has_spec.first(), 'ntok': G.ntok.first(),
                   'hit': G.apply(lambda g: (((g.stock < g.mn) | ((g.stock == 0) & (g.qty > 0))).any() and (g.stock > g.mx).any()))})
h = gi[gi.hit]
print(f'groups {len(gi)} | flagged {len(h)} | flagged with mixed units {int((h.units > 1).sum())} | flagged w/o any digit in desc {int((~h.spec).sum())} '
      f'| flagged desc <=3 tokens {int((h.ntok <= 3).sum())}')
# do twins live on the same FuncLoc (=> maybe different positions, not interchangeable)?
fls = bom.groupby('Material No')['Functional Loc.'].apply(set)
def share_fl(g): s = [fls.get(i, set()) for i in g['Material No']]; return any(a & b for i, a in enumerate(s) for b in s[i + 1:])
co = d[d.key.isin(h.index)].groupby('key').apply(share_fl)
iss = mv.groupby('Order')['Material Number'].apply(set)
twin_of = d.set_index('Material No').key
co_iss = iss.map(lambda s: len({twin_of[i] for i in s if i in twin_of.index}) < len([i for i in s if i in twin_of.index])).sum()
print(f'flagged groups where two twins share a FuncLoc: {int(co.sum())} | orders issuing 2+ twins of the same group together: {int(co_iss)}')
# value of "use twin stock": shortage covered by sibling stock above its own Max
rows = []
for k_, g in d[d.key.isin(h.index)].groupby('key'):
    need = ((g.mn - g.stock).clip(lower=0)).where(g.mn > 0, (g.qty > 0) * (g.stock == 0) * 1.0)
    spare = (g.stock - g.mx).clip(lower=0)
    cov = min(need.sum(), spare.sum()); px_ = g.px.median()
    rows.append(dict(key=k_, need=need.sum(), covd=cov, val=cov * px_ if pd.notna(px_) else np.nan, sa=g.crit.isin(['A', 'B']).any(), unit=g.unit.nunique()))
R = pd.DataFrame(rows)
print(f'shortage units fully covered by a twin: {int((R.covd >= R.need).sum())} of {len(R)} groups | priced value covered Rp{R.val.sum() / 1e9:.2f}bn '
      f'({R.val.notna().sum()} groups priced) | groups touching A/B {int(R.sa.sum())}')
print('examples:')
for k_ in h.sort_values('ntok').index[:4].tolist() + h.sort_values('ntok').index[-3:].tolist():
    g = d[d.key == k_]
    print('  ', g.desc.iloc[0][:60], '|', g[['Material No', 'unit', 'mrp', 'stock', 'mn', 'mx']].values.tolist()[:4])
