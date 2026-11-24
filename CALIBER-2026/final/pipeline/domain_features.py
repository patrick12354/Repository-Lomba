"""Domain features: signals that only exist once the SAP extracts are read as a plant, not as tables.
Every feature is point-in-time: it uses only records dated before `cut`.

  pm_*       PM calendar parsed from 28 free-text cycle formats -> PM executions actually due on the part's FLs
  fl_open_*  maintenance backlog: notifications open at the cut / scheduled to start in the next 90 days
  eq_*       equipment class decoded from the SAP functional-location tag (PP pump, HE exchanger, BF furnace, ...)
  sib_*      same-equipment siblings: other parts installed on the same FLs that were issued recently
  kit_*      kit partners: parts co-issued on the same work orders, and how active they are now
  open_pr_*  planner intent: requisitions raised before the cut, not yet delivered
  twin_*     identical-description twins: pooled history for parts that have none of their own
"""
import re
import numpy as np, pandas as pd

H90 = pd.Timedelta(days=90)

def cycle_days(txt):
    """'5 YEARLY', 'Yearly', '18 MONTHLY', '4 MONTH', '12 WEEK', 'Weekly', ... -> days (None if unparseable)."""
    t = str(txt).strip().upper()
    mm = re.match(r'^(\d+)?\s*(WEEK|MONTH|YEAR)', t)
    if not mm: return None
    n = int(mm.group(1) or 1)
    return n * {'WEEK': 7, 'MONTH': 30.44, 'YEAR': 365.25}[mm.group(2)]

def eq_class(tag):
    """SAP FL tag -> equipment class. 'PX_PP-490A-M' -> MOTOR, 'PX_PP-490A' -> PP, 'PX_1-1/2-CW-16705-A51A' -> LINE."""
    body = str(tag).split('_', 1)[-1]
    if re.match(r'^[\d/]+[-"]', body) or re.match(r'^\d', body): return 'LINE'
    if re.search(r'-M$', body): return 'MOTOR'
    if re.search(r'-CS[ST]$', body): return 'SEAL_SYS'
    m = re.match(r'^([A-Z]+)', body)
    c = m.group(1) if m else 'OTHER'
    if c.endswith('CV') or c in {'SDV', 'MOV', 'XV', 'HV'}: return 'CTRL_VALVE'
    if c in {'PRV', 'PSV', 'TSV'}: return 'RELIEF_VALVE'
    if c.endswith(('IT', 'T')) and len(c) <= 4 and c not in {'KT'}: return 'INSTRUMENT'
    return c

class DomainFeatures:
    def __init__(self, bom, fl, mp, mv, nt, pp, event_types):
        self.b = bom[['Functional Loc.', 'Material No', 'Installed Qty']].drop_duplicates(['Functional Loc.', 'Material No'])
        self.b.columns = ['fl', 'mat', 'inst']
        self.mats = pd.Index(sorted(bom['Material No'].unique()), name='Material No')
        self.mv = mv.copy(); self.mv['evt'] = self.mv.Order.astype(str).str[:4].isin(event_types)
        self.nt = nt.copy(); self.pp = pp.copy()
        p = mp[['Functional Location', 'Cycle Descriptions', 'Start of cycle']].copy()
        p['cyc'] = p['Cycle Descriptions'].map(cycle_days)
        self.pm = p.dropna(subset=['cyc']).rename(columns={'Functional Location': 'fl', 'Start of cycle': 'start'})
        self.n_cycle_formats = mp['Cycle Descriptions'].nunique(); self.pm_parsed = len(self.pm) / len(mp)
        self.cls = pd.Series({f: eq_class(f) for f in set(fl['Functional Location']) | set(self.b.fl)})
        self.b['cls'] = self.b.fl.map(self.cls)
        key = bom.drop_duplicates('Material No').set_index('Material No')['Material Desc.'].map(lambda s: re.sub(r'[^A-Z0-9]', '', str(s).upper()))
        self.twin_key = key[key.map(key.value_counts()) > 1]

    def _per_mat(self, fl_series, how='sum'):
        """FL-level series -> material-level by summing (or averaging) over the FLs the part is installed on."""
        v = self.b.assign(v=self.b.fl.map(fl_series).fillna(0)).groupby('mat').v
        return (v.sum() if how == 'sum' else v.mean()).reindex(self.mats).fillna(0)

    def __call__(self, cut, mo):
        f = pd.DataFrame(index=self.mats); end = cut + H90

        # --- PM calendar: executions due in [cut, cut+90d) and expected executions per 90 days
        p = self.pm[self.pm.start < end].copy()
        k = np.ceil(((cut - p.start).dt.days / p.cyc).clip(lower=0))
        due = p.start + pd.to_timedelta(k * p.cyc, unit='D')
        n_due = np.where(due < end, np.floor(((end - due).dt.days - 1) / p.cyc) + 1, 0)
        p['due90'] = n_due; p['rate90'] = 90 / p.cyc; p['major'] = (p.cyc >= 730) * n_due
        g = p.groupby('fl')
        f['pm_due_90'] = self._per_mat(g.due90.sum()); f['pm_major_due_90'] = self._per_mat(g.major.sum())
        f['pm_rate_90'] = self._per_mat(g.rate90.sum())

        # --- maintenance backlog
        n = self.nt[self.nt['Notification Date'] < cut]
        open_ = n[n['Completion by Date'].isna() | (n['Completion by Date'] >= cut)]
        sched = n[(n['Required Start'] >= cut) & (n['Required Start'] < end)]
        f['fl_open_notif'] = self._per_mat(open_.groupby('Functional Location').size())
        f['fl_sched_90'] = self._per_mat(sched.groupby('Functional Location').size())

        # --- equipment-class failure rate (pooled across all FLs of the same class)
        cls_notif = n.assign(c=n['Functional Location'].map(self.cls)).groupby('c').size()
        cls_rate = cls_notif / self.cls.value_counts() / mo
        self.b['cr'] = self.b.cls.map(cls_rate).fillna(0)
        f['eq_class_notif_rate'] = self.b.groupby('mat').cr.max().reindex(self.mats).fillna(0)
        dom = self.b.sort_values('inst', ascending=False).drop_duplicates('mat').set_index('mat').cls
        f['eq_class'] = dom.reindex(self.mats).fillna('NONE')

        # --- same-equipment siblings and kit partners, activity in the last 90 days
        w9 = self.mv[(self.mv['Posting Date'] >= cut - H90) & (self.mv['Posting Date'] < cut)]
        l90 = w9.groupby('Material Number').size()
        bl = self.b.assign(l=self.b.mat.map(l90).fillna(0))
        fl_l = bl.groupby('fl').l.sum()
        bl['sib'] = bl.fl.map(fl_l) - bl.l
        f['sib_issues_90'] = bl.groupby('mat').sib.sum().reindex(self.mats).fillna(0)
        h = self.mv[(self.mv['Posting Date'] < cut)][['Order', 'Material Number']].drop_duplicates()
        h = h[h.Order.map(h.Order.value_counts()) <= 30]
        pr = h.merge(h, on='Order'); pr = pr[pr['Material Number_x'] != pr['Material Number_y']]
        pr['act'] = pr['Material Number_y'].map(l90).fillna(0)
        kg = pr.groupby('Material Number_x')
        f['kit_partners'] = kg['Material Number_y'].nunique().reindex(self.mats).fillna(0)
        f['kit_partner_act_90'] = kg.act.sum().reindex(self.mats).fillna(0)

        # --- open requisitions (raised before cut, delivery after cut)
        o = self.pp[(self.pp['PR-Date'] < cut) & (self.pp['PO-Delivery Date'] >= cut)]
        f['open_pr_qty'] = o.groupby('PR-Material')['PR-Quantity'].sum().reindex(self.mats).fillna(0)
        f['open_pr_lines'] = o.groupby('PR-Material').size().reindex(self.mats).fillna(0)

        # --- twins: pooled issue rate of identical-description siblings
        hist = self.mv[self.mv['Posting Date'] < cut].groupby('Material Number').size()
        tk = self.twin_key; grp = tk.map(tk.index.to_series().map(hist).fillna(0).groupby(tk).sum())
        f['twin_lines_rate'] = ((grp - tk.index.to_series().map(hist).fillna(0)) / mo).reindex(self.mats).fillna(0)
        return f

GROUPS = {
    'pm_calendar': ['pm_due_90', 'pm_major_due_90', 'pm_rate_90'],
    'backlog': ['fl_open_notif', 'fl_sched_90'],
    'eq_class': ['eq_class_notif_rate', 'eq_class'],
    'siblings': ['sib_issues_90'],
    'kit': ['kit_partners', 'kit_partner_act_90'],
    'open_pr': ['open_pr_qty', 'open_pr_lines'],
    'twins': ['twin_lines_rate'],
}
