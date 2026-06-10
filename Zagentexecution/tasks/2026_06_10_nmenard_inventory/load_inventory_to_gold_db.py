"""Load the s081 N_MENARD TADIR/TFDIR scan into the Gold DB (d01_-prefixed — D01 provenance).

Tables created (replace on rerun):
  d01_tadir_yhr_pa_wf      — 740 objects of package YHR_PA_WF (PGMID, OBJECT, OBJ_NAME, AUTHOR, DEVCLASS, DESCRIPTION)
  d01_tadir_nmenard        — 3,463 objects authored by N_MENARD (same cols)
  d01_tfdir_nmenard_fugr   — FMs of every N_MENARD function group (FUGR, FUNCNAME, FMODE, DESCRIPTION)
"""
import json, sqlite3, sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
DB = ROOT / 'Zagentexecution' / 'sap_data_extraction' / 'sqlite' / 'p01_gold_master_data.db'
d = json.load(open(HERE / 'nmenard_inventory.json', encoding='utf-8'))
DESC = d['descriptions']


def desc_of(obj_type, name):
    name = name.strip()
    if obj_type in ('CLAS', 'INTF'):
        return DESC['SEOCLASSTX'].get(name, '')
    if obj_type in ('TABL', 'VIEW'):
        return DESC['DD02T'].get(name, '')
    if obj_type == 'PROG':
        return DESC['TRDIRT'].get(name, '')
    if obj_type == 'FUGR':
        return DESC['TLIBT'].get(name, '')
    if obj_type == 'DTEL':
        return DESC['DD04T'].get(name, '')
    return ''


con = sqlite3.connect(DB)
cur = con.cursor()

for table, rows in (('d01_tadir_yhr_pa_wf', d['package_objects']),
                    ('d01_tadir_nmenard', d['author_objects'])):
    cur.execute(f'DROP TABLE IF EXISTS {table}')
    cur.execute(f'CREATE TABLE {table} (PGMID TEXT, OBJECT TEXT, OBJ_NAME TEXT, '
                f'AUTHOR TEXT, DEVCLASS TEXT, DESCRIPTION TEXT)')
    cur.executemany(
        f'INSERT INTO {table} VALUES (?,?,?,?,?,?)',
        [(r['PGMID'], r['OBJECT'], r['OBJ_NAME'], r['AUTHOR'], r['DEVCLASS'],
          desc_of(r['OBJECT'].strip(), r['OBJ_NAME'])) for r in rows])
    print(f'{table}: {len(rows)} rows')

cur.execute('DROP TABLE IF EXISTS d01_tfdir_nmenard_fugr')
cur.execute('CREATE TABLE d01_tfdir_nmenard_fugr (FUGR TEXT, FUNCNAME TEXT, FMODE TEXT, DESCRIPTION TEXT)')
fm_rows = [(fg, f['FUNCNAME'].strip(), f.get('FMODE', '').strip(),
            DESC['TFTIT'].get(f['FUNCNAME'].strip(), ''))
           for fg, fms in d['fugr_fms'].items() for f in fms]
cur.executemany('INSERT INTO d01_tfdir_nmenard_fugr VALUES (?,?,?,?)', fm_rows)
print(f'd01_tfdir_nmenard_fugr: {len(fm_rows)} rows')

con.commit()
con.close()
print('DONE.')
