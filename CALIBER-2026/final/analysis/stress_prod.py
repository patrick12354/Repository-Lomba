"""Stress / feasibility test of E1-E4 against the PRODUCTION engine (pipeline/build_db.py) and app/data/partpulse.db.
Run from repo root:  py analysis/stress_prod.py   (~10 min; never writes the db)
E3 re-runs build_db's own rolling validation (code up to '# production: folds') under variants:
dropping BoM snapshot fields (Min/Max/MRP type are read after the test window, like stock) and de-duplicating PR PO.
"""
import sys, re, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'analysis'))
from load import load
from build_mat import build

con = sqlite3.connect(f'file:{ROOT / "app" / "data" / "partpulse.db"}?mode=ro', uri=True)
q = lambda s: pd.read_sql(s, con)
meta = dict(q('select key, value from meta').values)
AS_OF = pd.Timestamp(meta['as_of_date']); NEXT_TA = pd.Timestamp(meta['next_ta_default']); BUF = float(meta['ta_buffer_days'])
m, (bom, fl, mp, mv, nt, pp, p), _ = build()
pdd = p.drop_duplicates(subset=list(pp.columns))
print(f'db as_of {AS_OF.date()} | next_ta_default {NEXT_TA.date()} ({(NEXT_TA - AS_OF).days}d after as_of) | PR PO duplicates still in pipeline: {len(p) - len(pdd)}')

# ------------------------------------------------------------------ E1 (ta_kit + policy in db)
print('\n== E1 Shutdown Readiness (db)')
k = q('select k.*, m.mrp_type, m.max_cur, m.lt_source, p.order_by_date, p.action from ta_kit k join materials m using(material_no) join policy p using(material_no)')
ab = k.criticality.isin(['A', 'B'])
print(f'kit {len(k)} | short {(k.gap > 0).sum()} (A/B {((k.gap > 0) & ab).sum()}) | exceeds_max {k.exceeds_max.sum()}: '
      f'Max=0 {((k.exceeds_max == 1) & (k.max_cur == 0)).sum()}, Stock Item with Max>0 {((k.exceeds_max == 1) & (k.max_cur > 0) & (k.mrp_type == "Stock Item")).sum()}')
for s in [.5, .75, 1.]:
    print(f'  TA scale {s}: A/B short {((k.ta_qty_last * s > k.stock) & ab).sum()}')
lt_src = k[k.gap > 0].lt_source.value_counts().to_dict()
print(f'  lead time source of short kit parts: {lt_src}')
q_ = pdd[pdd.lt_days >= 0].groupby('PR-Material').lt_days.quantile(.9)
k['lt90_dedup'] = k.material_no.map(q_).fillna(k.lt_p90)
print(f'  lt_p90 of short kit parts: db median {k[k.gap > 0].lt_p90.median():.0f}d vs dedup {k[k.gap > 0].lt90_dedup.median():.0f}d')
ready_now = (k.stock >= k.ta_qty_last)
print(f'  readiness A/B now {ready_now[ab].mean():.1%}; after ordering today, by days to next TA (lt_p90 + {BUF:.0f}d buffer):')
for d in [32, 60, 90, 120, 180, 240, 270]:
    r = ready_now | (k.lt_p90 + BUF <= d); rd = ready_now | (k.lt90_dedup + BUF <= d)
    print(f'    {d:>3}d: {r[ab].mean():.1%} (dedup LT {rd[ab].mean():.1%}) | A/B parts already too late {(~r & ab).sum()}')
ob = pd.to_datetime(k.order_by_date)
print(f'  order_by_date of short A/B kit parts: = as_of (clamped, already late) {((ob == AS_OF) & (k.gap > 0) & ab).sum()} of {((k.gap > 0) & ab).sum()} '
      f'| action REORDER {((k.action == "REORDER") & (k.gap > 0) & ab).sum()}')

# ------------------------------------------------------------------ E2 (BI-5 under dedup)
print('\n== E2 Order-by date / planning lag (BI-5)')
first_issue = mv.groupby('Material Number')['Posting Date'].min()
for name, src in [('pipeline (raw)', p), ('dedup', pdd)]:
    rq = src[src.lt_days >= 0].copy(); rq['req'] = (rq['PR-Delivery Date'] - rq['PR-Date']).dt.days
    rq = rq[rq.groupby('PR-Material').lt_days.transform('size') >= 3]
    rq['rush'] = rq.req < .5 * rq.groupby('PR-Material').lt_days.transform('median')
    fs = (rq['PR-Material'].map(first_issue) < rq['PR-Date']) | rq['PR-Material'].isin(k.material_no)
    print(f'  {name:14s} lines {len(rq)} | rush {rq.rush.mean():.1%} | late rush {(rq[rq.rush].slip > 0).mean():.1%} vs normal {(rq[~rq.rush].slip > 0).mean():.1%} '
          f'| "preventable" {fs[rq.rush].mean():.1%} (same test on NON-rush lines {fs[~rq.rush].mean():.1%})')
pol = q('select p.order_by_date, p.action, m.criticality from policy p join materials m using(material_no)')
re_ = pol[pol.action == 'REORDER']; obd = pd.to_datetime(re_.order_by_date)
print(f'  REORDER parts {len(re_)} | order_by_date missing {obd.isna().sum()} | already = as_of {(obd == AS_OF).sum()} | within 30d {((obd > AS_OF) & (obd <= AS_OF + pd.Timedelta(days=30))).sum()}')

# ------------------------------------------------------------------ E4 (twins in db)
print('\n== E4 Twin materials (db)')
tw = q('select t.*, m.unit, m.description, m.criticality, m.stock, m.max_cur, m.min_cur, m.unit_price, m.price_source from twins t join materials m using(material_no)')
g = tw.groupby('group_id')
hit = g.role.agg(lambda r: {'SHORT', 'DONOR'} <= set(r)); H = tw[tw.group_id.map(hit)]
print(f'groups {tw.group_id.nunique()} | SHORT+DONOR groups {hit.sum()} | with mixed units {(H.groupby("group_id").unit.nunique() > 1).sum()} '
      f'| touching A/B {H.groupby("group_id").criticality.agg(lambda c: c.isin(["A", "B"]).any()).sum()}')
need = (H.min_cur - H.stock).clip(lower=0).where(H.role == 'SHORT', 0); spare = (H.stock - H.max_cur).clip(lower=0).where(H.role == 'DONOR', 0)
cov = pd.concat([need.groupby(H.group_id).sum(), spare.groupby(H.group_id).sum()], axis=1, keys=['need', 'spare'])
val = (np.minimum(cov.need, cov.spare) * H.groupby('group_id').unit_price.median()).sum()
print(f'  groups where donor spare >= short need {(cov.spare >= cov.need).sum()} | value of shortage covered by twins Rp{val / 1e9:.2f}bn (incl. estimated prices)')

# ------------------------------------------------------------------ E3 (production rolling validation, variants)
print('\n== E3 Production engine, rolling validation (4 origins, 90d routine demand; coverage sim skipped)')
SRC = (ROOT / 'pipeline' / 'build_db.py').read_text(encoding='utf-8').split('# production: folds')[0]
def patch(s, old, new):
    assert old in s, old; return s.replace(old, new, 1)
def run(drop=(), dedup=False):
    s = patch(SRC, 'val = rolling(STRICT_DEFAULT, True)', 'val = rolling(STRICT_DEFAULT, False)')   # skip coverage sim
    s = patch(s, 'val_s = rolling(True, False)', 'val_s = val')
    s = patch(s, "RATE = [", f"X_cols = [c for c in X_cols if c not in {list(drop)!r}]\nRATE = [")
    if 'mrp' in drop: s = patch(s, 'STRICT_DEFAULT = False', 'STRICT_DEFAULT = True')   # engine switch for the no-snapshot variant
    if dedup: s = patch(s, "m, (bom, fl, mp, mv, nt, pp, p), _ = build()", "m, (bom, fl, mp, mv, nt, pp, p), _ = build(); p = p.drop_duplicates(subset=list(pp.columns))")
    g_ = {'__file__': str(ROOT / 'pipeline' / 'build_db.py'), '__name__': 'stress'}
    exec(compile(s, 'build_db[validation]', 'exec'), g_)
    return g_['val']
SNAP = ('mn', 'mx', 'mrp')
for name, kw in [('as shipped', {}), ('no Min/Max/MRP snapshot', dict(drop=SNAP)),
                 ('no snapshot + dedup PR PO', dict(drop=SNAP, dedup=True)),
                 ('no snapshot + dedup + no lt_med', dict(drop=SNAP + ('lt_med',), dedup=True))]:
    v = run(**kw)
    print(f'  {name:32s} AUC {v.auc.mean():.3f} (naive {v.auc_naive.mean():.3f}) | cold {v.auc_cold.mean():.3f} '
          f'| per-origin cold {v.auc_cold.round(3).tolist()} | MAE {v.mae.mean():.2f} (naive {v.mae_naive.mean():.2f}) | |bias| {v.bias.abs().mean():.3f}', flush=True)
