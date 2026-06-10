"""Extract the CLASS/METHOD anatomy of all Y* classes from D01 SEO catalog tables (READ-ONLY).

Code and objects are data: class structure lives in tables —
  SEOCLASSDF  — class definition flags (FINAL, ABSTRACT, exposure)
  SEOMETAREL  — inheritance + interface implementation relations
  SEOCOMPO    — components (attributes / methods / events / types)
  SEOCOMPODF  — component definitions (visibility, static/instance, typing)
  SEOSUBCODF  — method parameters (importing/exporting/changing/returning + optional)
  SEOREDEF    — redefined methods

Output: nmenard_seo_anatomy.json + Gold DB tables d01_seo_* (D01 provenance).
"""
import sys, json, sqlite3
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
MCP_DIR = HERE.parent.parent / 'mcp-backend-server-python'
ROOT = HERE.parent.parent.parent
DB = ROOT / 'Zagentexecution' / 'sap_data_extraction' / 'sqlite' / 'p01_gold_master_data.db'
sys.path.insert(0, str(MCP_DIR))
from rfc_helpers import get_connection  # noqa

OUT = HERE / 'nmenard_seo_anatomy.json'


def rfc_read_all(conn, table, fields, where):
    options = []
    cur = ''
    for tok in where.split(' '):
        if len(cur) + len(tok) + 1 > 72:
            options.append({'TEXT': cur}); cur = tok
        else:
            cur = (cur + ' ' + tok).strip()
    if cur:
        options.append({'TEXT': cur})
    result = conn.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|',
                       FIELDS=[{'FIELDNAME': f} for f in fields],
                       OPTIONS=options, ROWCOUNT=0, ROWSKIPS=0)
    rows = []
    for line in result['DATA']:
        parts = line['WA'].split('|')
        rows.append({f: parts[i].strip() if i < len(parts) else ''
                     for i, f in enumerate(fields)})
    return rows


def main():
    conn = get_connection('D01')
    state = {}

    pulls = [
        # (key, table, fields, where)
        ('classdf', 'SEOCLASSDF',
         ['CLSNAME', 'VERSION', 'EXPOSURE', 'CLSFINAL', 'CLSABSTRCT', 'CLSCCINCL', 'AUTHOR'],
         "CLSNAME LIKE 'Y%' AND VERSION = '1'"),
        ('metarel', 'SEOMETAREL',
         ['CLSNAME', 'REFCLSNAME', 'RELTYPE', 'VERSION'],
         "CLSNAME LIKE 'Y%' AND VERSION = '1'"),
        ('compo', 'SEOCOMPO',
         ['CLSNAME', 'CMPNAME', 'CMPTYPE', 'MTDTYPE'],
         "CLSNAME LIKE 'Y%'"),
        ('compodf', 'SEOCOMPODF',
         ['CLSNAME', 'CMPNAME', 'VERSION', 'EXPOSURE', 'ATTDECLTYP', 'TYPE', 'MTDDECLTYP'],
         "CLSNAME LIKE 'Y%' AND VERSION = '1'"),
        ('subcodf', 'SEOSUBCODF',
         ['CLSNAME', 'CMPNAME', 'SCONAME', 'VERSION', 'PARDECLTYP', 'PAROPTIONL', 'TYPE'],
         "CLSNAME LIKE 'Y%' AND VERSION = '1'"),
        ('redef', 'SEOREDEF',
         ['CLSNAME', 'REFCLSNAME', 'MTDNAME', 'VERSION'],
         "CLSNAME LIKE 'Y%' AND VERSION = '1'"),
    ]
    for key, table, fields, where in pulls:
        try:
            rows = rfc_read_all(conn, table, fields, where)
        except Exception as e:
            print(f'{table}: FAILED ({e})')
            rows = []
        state[key] = rows
        print(f'{table}: {len(rows)} rows')
        OUT.write_text(json.dumps(state, indent=0), encoding='utf-8')
    conn.close()

    # Load into Gold DB (d01_ prefix — D01 provenance)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for key, table, fields, _ in pulls:
        t = f'd01_seo_{key}'
        cur.execute(f'DROP TABLE IF EXISTS {t}')
        cur.execute(f'CREATE TABLE {t} ({", ".join(f"{f} TEXT" for f in fields)})')
        cur.executemany(f'INSERT INTO {t} VALUES ({",".join("?"*len(fields))})',
                        [[r[f] for f in fields] for r in state[key]])
        print(f'Gold DB {t}: {len(state[key])} rows')
    con.commit()
    con.close()
    print('DONE.')


if __name__ == '__main__':
    main()
