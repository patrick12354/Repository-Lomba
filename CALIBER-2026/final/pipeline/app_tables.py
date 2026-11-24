"""App-only helper tables, appended to app/data/partpulse.db after build_db.py.

Run from repo root, after the engine:  py pipeline/build_db.py && py pipeline/app_tables.py

material_location: where each turnaround-kit part is installed (equipment tag taken from the
functional location code, e.g. PX_BF-105-COIL21 -> BF-105, class BF). Feeds the furnace map.
The app hides the map when this table is missing, so build_db.py alone still works.
"""
import os
import sqlite3
import pandas as pd

DB = os.environ.get('PARTPULSE_DB', 'app/data/partpulse.db')   # override to build beside a database a running server holds open
bom = pd.read_excel('data/BoM.xlsx')
con = sqlite3.connect(DB)
kit = set(pd.read_sql('select material_no from ta_kit', con).material_no)
loc = bom[bom['Material No'].isin(kit)][['Material No', 'Functional Loc.']].drop_duplicates()
ex = loc['Functional Loc.'].astype(str).str.extract(r'^[A-Z]+_([A-Z]+)-(\d+[A-Z]?)')
loc['equip_class'] = ex[0]
loc['equipment'] = ex[0] + '-' + ex[1]
out = loc.dropna(subset=['equipment'])[['Material No', 'equipment', 'equip_class']].drop_duplicates()
out = out.rename(columns={'Material No': 'material_no'})
con.execute('drop table if exists material_location')
con.execute('create table material_location (material_no INTEGER, equipment TEXT, equip_class TEXT)')
out.to_sql('material_location', con, if_exists='append', index=False)
con.execute('create index if not exists ix_loc on material_location(material_no)')
con.commit()
# material_code: every part's equipment code from its functional location, e.g. PX_PP-490A-M -> PP,
# PX_3-MS-3548-B21A-H (a line number) -> PIPE. Feeds the code filter and routes tasks to a maintenance section.
SECTION = {
    **dict.fromkeys(['PP', 'KC', 'KT'], 'rotating'),
    **dict.fromkeys(['HE', 'BF', 'VD', 'CL', 'PIPE'], 'static'),
    **dict.fromkeys(['FCV', 'PCV', 'LCV', 'TCV', 'PRV', 'SDV', 'MOV', 'ROF', 'PIT', 'FIT', 'LIT', 'TIT', 'PGI', 'DPT', 'TEL', 'JBX'], 'instrument'),
}
fl = bom[['Material No', 'Functional Loc.']].dropna().copy()
tag = fl['Functional Loc.'].astype(str).str.extract(r'^[A-Z]+_([A-Z]+)-\d')[0]
is_line = fl['Functional Loc.'].astype(str).str.match(r'^[A-Z]+_\d[\d/-]*-[A-Z]+-\d')
fl['code'] = tag.where(tag.isin(SECTION), other=None)
fl.loc[is_line, 'code'] = 'PIPE'
fl['code'] = fl['code'].fillna('OTHER')
codes = fl.groupby(['Material No', 'code']).size().reset_index(name='n').rename(columns={'Material No': 'material_no'})
codes['section'] = codes.code.map(SECTION).fillna('static')
con.execute('drop table if exists material_code')
con.execute('create table material_code (material_no INTEGER, code TEXT, section TEXT, n INTEGER)')
codes.to_sql('material_code', con, if_exists='append', index=False)
con.execute('create index if not exists ix_code on material_code(material_no)')
con.commit()
print('material_code parts', codes.material_no.nunique(), codes.groupby('code').material_no.nunique().sort_values(ascending=False).to_dict())

# app_facts: plant-level numbers the app quotes that are not per-material (PR guardrail, EDA F5)
pp = pd.read_excel('data/PR PO.xlsx').drop_duplicates()   # 5,420 exact duplicate lines (docs/04_SCOPE_FINAL.md §4)
idr = pp[pp['PO-Currency'] == 'IDR'].copy()
idr['line_val'] = idr['PO-Item Amount'] * idr['PR-Quantity']          # PO-Item Amount is a unit price
mat = pd.read_sql('select material_no, stock, max_cur from materials', con)
over = set(mat.loc[(mat.max_cur > 0) & (mat.stock > mat.max_cur), 'material_no'])
facts = {
    'spend_idr_total': float(idr.line_val.sum()),
    'pct_spend_above_max': float(idr.loc[idr['PR-Material'].isin(over), 'line_val'].sum() / idr.line_val.sum()),
}
con.execute('drop table if exists app_facts')
con.execute('create table app_facts (key TEXT PRIMARY KEY, value REAL)')
con.executemany('insert into app_facts values (?, ?)', list(facts.items()))
con.commit()
print('app_facts', {k: round(v, 4) for k, v in facts.items()})

furn = out[out.equipment.str.match(r'^BF-1(0[1-9]|1[0-2])$')]
print(f'material_location rows {len(out)} | TA parts in furnaces BF-101..112: {furn.material_no.nunique()}')
con.close()
