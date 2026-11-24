"""Maintenance work ahead, from the plans in Mitem & Mplan, plus recent breakdown notices per equipment type.

The maintenance files list no parts, so a plan cannot be turned into a part quantity. What this gives the planner is
when each job falls due and which parts are fitted on that equipment. The forecast model does not read these dates: they were
tested one by one and added no lift (docs/04_MODEL_DECISIONS.md, section E).

Run from repo root after build_db.py:  py pipeline/maintenance_calendar.py
Writes tables pm_month, pm_major and notif_by_code.
"""
import os, sqlite3, sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'pipeline'))
from domain_features import cycle_days

MAJOR_DAYS = 730                # a cycle of two years or more counts as a major overhaul, as in domain_features.py
DB = os.environ.get('PARTPULSE_DB', str(ROOT / 'app' / 'data' / 'partpulse.db'))
con = sqlite3.connect(DB)
meta = dict(con.execute('select key, value from meta').fetchall())
as_of, ta = pd.Timestamp(meta['as_of_date']), pd.Timestamp(meta['next_ta_default'])

plans = pd.read_excel(ROOT / 'data' / 'Mitem & Mplan.xlsx').drop_duplicates(['Maintenance Plan', 'Maintenance Item'])
plans['cycle'] = plans['Cycle Descriptions'].map(cycle_days)
plans = plans.dropna(subset=['cycle', 'Start of cycle'])

jobs = []
for r in plans.itertuples(index=False):
    start, cycle = r[8], r.cycle
    k = max(0, -((start - as_of).days // cycle))
    due = start + pd.Timedelta(days=k * cycle)
    while due < ta:
        if due.normalize() > as_of:
            jobs.append((due.normalize(), r[0], r[1], r[5], r[2], cycle, r[7]))
        due += pd.Timedelta(days=cycle)
jobs = pd.DataFrame(jobs, columns=['due', 'fl', 'fl_desc', 'task', 'criticality', 'cycle', 'cycle_text'])
jobs['month'] = jobs.due.dt.strftime('%Y-%m')
jobs['major'] = jobs.cycle >= MAJOR_DAYS

month = jobs.groupby('month').agg(jobs=('fl', 'size'), major=('major', 'sum'), equipment=('fl', 'nunique')).reset_index()

bom = pd.read_excel(ROOT / 'data' / 'BoM.xlsx')[['Functional Loc.', 'Material No']].drop_duplicates()
bom.columns = ['fl', 'material_no']
bom['material_no'] = pd.to_numeric(bom.material_no, errors='coerce')
state = pd.read_sql("select material_no, health, mrp_type from materials", con)
fitted = bom.merge(state, on='material_no', how='left')
fitted['low'] = fitted.health.isin(['STOCKOUT', 'BELOW_MIN']) & (fitted.mrp_type == 'Stock Item')
per_fl = fitted.groupby('fl').agg(parts=('material_no', 'nunique'), parts_low=('low', 'sum')).reset_index()

major = jobs[jobs.major].merge(per_fl, on='fl', how='left').fillna({'parts': 0, 'parts_low': 0})
major['due'] = major.due.dt.strftime('%Y-%m-%d')
major = major[['month', 'due', 'fl', 'fl_desc', 'task', 'criticality', 'cycle_text', 'parts', 'parts_low']]

notif = pd.read_excel(ROOT / 'data' / 'Notif History.xlsx')
recent = notif[(notif['Notification Date'] > as_of - pd.Timedelta(days=90)) & (notif['Notification Date'] <= as_of)].copy()
tag = recent['Functional Location'].astype(str).str.extract(r'^[A-Z]+_([A-Z]+)-\d')[0]
is_line = recent['Functional Location'].astype(str).str.match(r'^[A-Z]+_\d[\d/-]*-[A-Z]+-\d')
recent['code'] = tag.fillna('OTHER')
recent.loc[is_line, 'code'] = 'PIPE'
by_code = recent.groupby('code').agg(notices=('code', 'size'), emergency=('Notification Type', lambda s: int((s == 'N2').sum()))).reset_index()

month.to_sql('pm_month', con, if_exists='replace', index=False)
major.to_sql('pm_major', con, if_exists='replace', index=False)
by_code.to_sql('notif_by_code', con, if_exists='replace', index=False)
con.commit()
con.close()

print(month.to_string(index=False))
print('major jobs', len(major), 'on', major.fl.nunique(), 'locations; with low parts', (major.parts_low > 0).sum())
print(major.sort_values('parts_low', ascending=False).head(8).to_string(index=False))
print(by_code.sort_values('notices', ascending=False).head(10).to_string(index=False), 'total', len(recent))
