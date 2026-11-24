"""Month-by-month replay of real use, Mar-Sep 2026, on the parts that are meant to be kept on the shelf.

Non Stock parts are bought per job, so an empty shelf is normal for them. They keep today's SAP setting here and are
left out of availability, which matches what the SAP export changes (Stock Items only).

Rules on top of policy_backtest.py:
- Sparekit limits are recomputed on the first day of every month, using only data before that day.
- The classic re-tune is recomputed on the same days, so the comparison stays fair.
- Today's Min and Max stay fixed, as they do in SAP.
- Every plan starts at its own Max, and a second run starts every plan from the shelf as recorded in the BoM.

Run from repo root after build_db.py:  py pipeline/replay_timeline.py
Writes tables replay_policy, replay_monthly, replay_refresh and replay_parts.
"""
import json, os, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / 'pipeline' / 'policy_backtest.py').read_text(encoding='utf-8')
src = src.replace('Path(__file__).resolve().parent.parent', f'Path(r"{ROOT}")').split('SL_DEF = {')[0]
exec(compile(src, 'policy_backtest[engine]', 'exec'))

SL = {'A': .95, 'B': .90, 'C': .85, 'S': .80}
C0 = C
stock_item = mat.mrp_type.values == 'Stock Item'
keep = movers & ab & stock_item
mn0, mx0 = mat.min_cur.values.astype(float), mat.max_cur.values.astype(float)
FIRSTS = list(pd.date_range(C0, E - pd.Timedelta(days=1), freq='MS'))
day_month = np.array([(C0 + pd.Timedelta(days=t)).strftime('%Y-%m') for t in range(T)])
MONTHS = sorted(set(day_month))


def refresh_inputs(when):
    """Recompute the forecast and lead-time inputs of partpulse_policy and classic_policy as of `when`."""
    global C, q, L, sL, bl, pb, mean, LTD, ltd_m, ltd_v, D_yr, pr_med
    C = when
    q = p[(p.lt_days >= 0) & (p['PR-Date'] < C)].copy()
    q['cat'] = q['PR-Material Desc'].str.split(',').str[0]
    lm = q.groupby('PR-Material').lt_days.agg(n='size', p50='median', sd='std').reindex(idx)
    lc = q.groupby('cat').lt_days.agg(n='size', p50='median', mean='mean', sd='std')
    lc['cv'] = lc.sd / lc['mean']
    catl = lc.reindex(mat.category).set_index(idx)
    has = (catl.n.fillna(0) >= 5).values
    gcv = q.lt_days.std() / q.lt_days.mean()
    L = np.maximum(lm.p50.fillna(catl.p50.where(has)).fillna(q.lt_days.median()).values.astype(float), 1)
    sL = np.nan_to_num(np.where(lm.n.fillna(0).values >= 3, lm.sd.fillna(0).values, L * catl.cv.where(has).fillna(gcv).values))

    P = C - pd.Timedelta(days=g['D90'])
    clf_, reg_ = g['fit'](pd.Timestamp(P.year, P.month, 1), STRICT)
    _, _, pb_, mean_, _ = g['forecast_at'](clf_, reg_, C, H, STRICT)
    pb = pb_.reindex(idx).values
    mean = mean_.reindex(idx).clip(lower=0).values

    bl = mv[(~mv.ot.isin(EVENT)) & (mv['Posting Date'] < C)]
    own = bl.groupby('Material Number').Quantity.apply(np.array)
    cat_ = bl.groupby('cat').Quantity.apply(np.array)
    lam_ = -np.log(1 - np.clip(pb, 0, .995))
    LTD = np.zeros((N, NS), dtype=np.float32)
    e2 = np.zeros(N)
    for j, (i, c_) in enumerate(zip(idx, mat.category)):
        if lam_[j] <= 0 or mean[j] <= 0:
            continue
        sz = own.get(i)
        if sz is None or len(sz) < 3:
            sz = cat_.get(c_, np.array([1]))
        sz = sz.astype(float) * (mean[j] / (lam_[j] * sz.mean()))
        e2[j] = (sz ** 2).mean()
        Ls = rng.gamma((L[j] / sL[j]) ** 2, sL[j] ** 2 / L[j], NS) if sL[j] > 0 else np.full(NS, L[j])
        Nn = rng.poisson(lam_[j] * Ls / H)
        LTD[j] = np.bincount(np.repeat(np.arange(NS), Nn), weights=rng.choice(sz, Nn.sum()), minlength=NS)
    d = mean / H
    ltd_m = d * L
    ltd_v = L * lam_ / H * e2 + d ** 2 * sL ** 2
    D_yr = mean * 365 / H
    pr_med = q.groupby('PR-Material')['PR-Quantity'].median().reindex(idx).values


def stock_items_only(s, S):
    return np.where(stock_item, s, mn0), np.where(stock_item, S, mx0)


# one set of limits per month; the first set is the same point-in-time run as policy_backtest.py
spark, classic, why = [], [], []
for i_, day in enumerate(FIRSTS):
    if i_:
        refresh_inputs(day)
    spark.append(stock_items_only(*partpulse_policy(SL)))
    classic.append(stock_items_only(*classic_policy(SL)))
    # what the limits were built from that day, so the page can say why a Min moved
    why.append(dict(chance=pb.copy(), use_in_delivery=ltd_m.copy(), delivery=L.copy()))
    print('limits ready', day.date(), flush=True)
today = (mn0, mx0)


def run(plan, start=None):
    """plan = one (s, S) pair, or one pair per month. Returns monthly totals, per-part totals, daily stock and, for the
    kept parts, each unmet request and each order placed."""
    plans = plan if isinstance(plan, list) else [plan]
    slot = {j: n_ for n_, j in enumerate(np.where(keep)[0])}
    short = {n_: [] for n_ in slot.values()}
    placed = {n_: [] for n_ in slot.values()}
    first_day = {(d - C0).days: k for k, d in enumerate(FIRSTS)}
    s, S = plans[0]
    on = (S if start is None else start).astype(float).copy()
    pipe = np.zeros((N, T + LT.max() + 1))
    onord = np.zeros(N)
    k = np.zeros(N, int)
    served = np.zeros(N)
    so = np.zeros(N)
    hist = np.zeros((int(keep.sum()), T))
    monthly = {m_: dict(requested=0.0, served=0.0, lines=0, lines_ok=0, stockout_days=0, inv=[], inv_po=[], orders=0) for m_ in MONTHS}
    for t in range(T):
        if t in first_day and len(plans) > 1:
            s, S = plans[first_day[t]]
        row = monthly[day_month[t]]
        on += pipe[:, t]
        onord -= pipe[:, t]
        d = dem[:, t]
        sv = np.minimum(on, d)
        on -= sv
        served += sv
        for j in np.where(keep & (d > sv))[0]:
            short[slot[j]].append([t, round(float(d[j] - sv[j]), 1)])
        row['requested'] += d[keep].sum()
        row['served'] += sv[keep].sum()
        row['lines'] += int((d[keep] > 0).sum())
        row['lines_ok'] += int(((d > 0) & (sv >= d))[keep].sum())
        ip = on + onord
        for j in np.where((ip <= s) & (S > ip) & (S > 0))[0]:
            qty = S[j] - ip[j]
            pipe[j, t + LT[j, k[j] % K]] += qty
            if j in slot:
                placed[slot[j]].append([t, round(float(qty), 1), int(t + LT[j, k[j] % K])])
            onord[j] += qty
            k[j] += 1
            row['orders'] += 1
        row['inv'].append((on * price).sum())
        row['inv_po'].append((on * price * po).sum())
        row['stockout_days'] += int((on[keep] <= 0).sum())
        so += on <= 0
        hist[:, t] = on[keep]
    return monthly, served, hist, short, placed


if STRICT:
    # Same replay with a forecast that does not read today's Min, Max or MRP type. Adds one row and stops.
    mo = run(spark)[0]
    req, srv = sum(r['requested'] for r in mo.values()), sum(r['served'] for r in mo.values())
    li, ok_ = sum(r['lines'] for r in mo.values()), sum(r['lines_ok'] for r in mo.values())
    inv = np.concatenate([r['inv'] for r in mo.values()])
    ipo = np.concatenate([r['inv_po'] for r in mo.values()])
    con = sqlite3.connect(Path(os.environ.get('PARTPULSE_DB', ROOT / 'app' / 'data' / 'partpulse.db')))
    con.execute("delete from replay_policy where policy = 'sparekit_strict'")
    con.execute('insert into replay_policy (policy, label, parts, fill_units, fill_lines, stockout_days, avg_inv_idr, avg_inv_idr_po, end_inv_idr, orders) values (?,?,?,?,?,?,?,?,?,?)',
                ('sparekit_strict', "Sparekit, refreshed monthly, forecast without today's Min and Max", int(keep.sum()), srv / req, ok_ / li,
                 sum(r['stockout_days'] for r in mo.values()), float(inv.mean()), float(ipo.mean()), float(inv[-1]), sum(r['orders'] for r in mo.values())))
    con.commit()
    con.close()
    print(f'strict: fill {srv / req:.3f}, lines {ok_ / li:.3f}, days {sum(r["stockout_days"] for r in mo.values())}, stock {inv.mean() / 1e9:.0f} B')
    sys.exit(0)

RUNS = {
    'today': ("Today's Min and Max", today, None),
    'classic': ('Classic formula, refreshed monthly', classic, None),
    'sparekit_once': ('Sparekit, set once on 1 Mar', spark[0], None),
    'sparekit': ('Sparekit, refreshed monthly', spark, None),
    'today_shelf': ("Today's Min and Max, from the shelf on record", today, mat.stock.values.astype(float)),
    'sparekit_shelf': ('Sparekit, from the shelf on record', spark, mat.stock.values.astype(float)),
}
res = {k_: run(plan_, start_) for k_, (_, plan_, start_) in RUNS.items()}

policy_rows, month_rows = [], []
for k_, (label, _, _) in RUNS.items():
    mo = res[k_][0]
    req, srv = sum(r['requested'] for r in mo.values()), sum(r['served'] for r in mo.values())
    li, ok_ = sum(r['lines'] for r in mo.values()), sum(r['lines_ok'] for r in mo.values())
    inv = np.concatenate([r['inv'] for r in mo.values()])
    ipo = np.concatenate([r['inv_po'] for r in mo.values()])
    policy_rows.append(dict(policy=k_, label=label, parts=int(keep.sum()), fill_units=srv / req, fill_lines=ok_ / li,
                            stockout_days=sum(r['stockout_days'] for r in mo.values()), avg_inv_idr=float(inv.mean()),
                            avg_inv_idr_po=float(ipo.mean()), end_inv_idr=float(inv[-1]), orders=sum(r['orders'] for r in mo.values())))
    for m_, r in mo.items():
        month_rows.append(dict(policy=k_, month=m_, requested=r['requested'], served=r['served'], lines=r['lines'], lines_ok=r['lines_ok'],
                               stockout_days=r['stockout_days'], avg_inv_idr=float(np.mean(r['inv'])), end_inv_idr=float(r['inv'][-1]), orders=r['orders']))

refresh_rows = []
for i_, m_ in enumerate(MONTHS):
    now_s, now_S = spark[i_]
    prev_s = spark[i_ - 1][0] if i_ else mn0
    prev_S = spark[i_ - 1][1] if i_ else mx0
    a, b_ = np.round(now_s), np.round(prev_s)
    refresh_rows.append(dict(month=m_, compared_to='sap' if i_ == 0 else 'last_month',
                             changed=int((stock_item & ((a != b_) | (np.round(now_S) != np.round(prev_S)))).sum()),
                             min_up=int((stock_item & (a > b_)).sum()), min_down=int((stock_item & (a < b_)).sum()),
                             critical=int((stock_item & ab & ((a != b_) | (np.round(now_S) != np.round(prev_S)))).sum()),
                             value_max_idr=float((now_S * price).sum())))

r1 = lambda a_: [round(float(x), 1) for x in a_]
kept = idx[keep]
pos_keep = np.where(keep)[0]
part_rows = []
for n_, (mno, j) in enumerate(zip(kept, pos_keep)):
    mins = [float(np.round(spark[i_][0][j])) for i_ in range(len(MONTHS))]
    maxs = [float(np.round(spark[i_][1][j])) for i_ in range(len(MONTHS))]
    part_rows.append(dict(
        material_no=int(mno), requested=float(tot_ if (tot_ := dem[j].sum()) else 0), served_today=float(res['today'][1][j]), served_sparekit=float(res['sparekit'][1][j]),
        min_moves=int(sum(a_ != b_ for a_, b_ in zip(mins, mins[1:]))),
        data=json.dumps(dict(use=r1(dem[j]), today=r1(res['today'][2][n_]), sparekit=r1(res['sparekit'][2][n_]), mins=mins, maxs=maxs,
                             min_today=float(mn0[j]), max_today=float(mx0[j]),
                             short_today=res['today'][3][n_], short_sparekit=res['sparekit'][3][n_],
                             orders_today=res['today'][4][n_], orders_sparekit=res['sparekit'][4][n_],
                             chance=[round(float(w['chance'][j]), 3) for w in why],
                             use_in_delivery=[round(float(w['use_in_delivery'][j]), 1) for w in why],
                             delivery=[round(float(w['delivery'][j])) for w in why]), separators=(',', ':')),
    ))

DB = Path(os.environ.get('PARTPULSE_DB', ROOT / 'app' / 'data' / 'partpulse.db'))
con = sqlite3.connect(DB)
pd.DataFrame(policy_rows).to_sql('replay_policy', con, if_exists='replace', index=False)
pd.DataFrame(month_rows).to_sql('replay_monthly', con, if_exists='replace', index=False)
pd.DataFrame(refresh_rows).to_sql('replay_refresh', con, if_exists='replace', index=False)
pd.DataFrame(part_rows).to_sql('replay_parts', con, if_exists='replace', index=False)
con.commit()
con.close()

pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 20)
print(pd.DataFrame(policy_rows).drop(columns='label').round(3).to_string(index=False))
print(pd.DataFrame(refresh_rows).to_string(index=False))
print(pd.DataFrame(month_rows).query("policy in ['today','sparekit']").drop(columns=['lines', 'lines_ok']).round(0).to_string(index=False))
pr = pd.DataFrame(part_rows).drop(columns='data')
print('parts', len(pr), 'moved at least once', (pr.min_moves > 0).sum(), 'db bytes', sum(len(r['data']) for r in part_rows))
