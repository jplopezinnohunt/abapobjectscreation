"""
targeted_tadir_lookup.py
Queries TADIR and DD02T for exactly the objects in cts_config_detail.json.
Uses pyrfc directly in batches of 15 (small enough for RFC_READ_TABLE WHERE clause).
Runs fast because it spawns real pyrfc connections, not subprocess overhead.
"""
import json, os
from dotenv import load_dotenv
import pyrfc
import time

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

CONN_PARAMS = dict(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr=os.environ.get('SAP_SYSNR','00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user=os.environ.get('SAP_USER','jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

all_names = sorted(cfg.keys())
print(f'Objects: {len(all_names)}')

conn = pyrfc.Connection(**CONN_PARAMS)
print('RFC connected')

def read_table_batch(conn, table, where_lines, fields, max_rows=200):
    """Call RFC_READ_TABLE with given WHERE lines."""
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table,
            DELIMITER='|',
            ROWSKIPS=0,
            ROWCOUNT=max_rows,
            FIELDS=[{'FIELDNAME': f} for f in fields],
            OPTIONS=[{'TEXT': w} for w in where_lines],
        )
        out = []
        for row in r.get('DATA', []):
            parts = [p.strip() for p in row['WA'].split('|')]
            out.append(dict(zip(fields, parts + ['']*(len(fields)-len(parts)))))
        return out
    except Exception as e:
        return []

BATCH = 15   # 15 names per batch — keeps WHERE clause within RFC limits
tadir_map = {}
dd02t_map = {}
dd25t_map = {}

total = len(all_names)
t0 = time.time()

for i in range(0, total, BATCH):
    batch = all_names[i:i+BATCH]
    name_or = ' OR '.join(f"OBJ_NAME = '{n}'" for n in batch)
    where = [f"PGMID = 'R3TR' AND ({name_or})"]
    rows = read_table_batch(conn, 'TADIR', where, ['OBJ_NAME','DEVCLASS','OBJECT'])
    for row in rows:
        if row['OBJ_NAME'] and row['DEVCLASS']:
            tadir_map[row['OBJ_NAME']] = row['DEVCLASS']

    # DD02T (table texts)
    name_or_t = ' OR '.join(f"TABNAME = '{n}'" for n in batch)
    where_t = [f"DDLANGUAGE = 'E' AND ({name_or_t})"]
    rows_t = read_table_batch(conn, 'DD02T', where_t, ['TABNAME','DDTEXT'])
    for row in rows_t:
        if row['TABNAME'] and row['DDTEXT']:
            dd02t_map[row['TABNAME']] = row['DDTEXT']

    # Views (DD25T)
    view_batch = [n for n in batch if cfg[n].get('obj_type') in ('VDAT','CDAT','VIED')]
    if view_batch:
        name_or_v = ' OR '.join(f"VIEWNAME = '{n}'" for n in view_batch)
        where_v = [f"DDLANGUAGE = 'E' AND ({name_or_v})"]
        rows_v = read_table_batch(conn, 'DD25T', where_v, ['VIEWNAME','DDTEXT'])
        for row in rows_v:
            if row['VIEWNAME'] and row['DDTEXT']:
                dd25t_map[row['VIEWNAME']] = row['DDTEXT']

    done = min(i+BATCH, total)
    if done % 150 == 0 or done == total:
        elapsed = time.time()-t0
        rate = done/elapsed if elapsed > 0 else 0
        eta = (total-done)/rate if rate > 0 else 0
        print(f'  [{done}/{total}] pkg={len(tadir_map)} desc={len(dd02t_map)+len(dd25t_map)} ETA={eta:.0f}s')

conn.close()
print(f'\nTotal elapsed: {time.time()-t0:.0f}s')
print(f'TADIR: {len(tadir_map)} packages found')
print(f'DD02T: {len(dd02t_map)} table descriptions')
print(f'DD25T: {len(dd25t_map)} view descriptions')

# Merge
pkg_hits = desc_hits = 0
for name, v in cfg.items():
    if name in tadir_map:
        v['package'] = tadir_map[name]
        pkg_hits += 1
    if name in dd02t_map:
        v['desc'] = dd02t_map[name]
        desc_hits += 1
    elif name in dd25t_map:
        v['desc'] = dd25t_map[name]
        desc_hits += 1

print(f'Matched: {pkg_hits} packages, {desc_hits} descriptions')

# Sample
samples = [(n, v.get('package',''), v.get('desc','')) for n,v in cfg.items()
           if v.get('package') and v.get('desc')][:12]
print('\nSample:')
for n,p,d in samples:
    print(f'  {n:<30} {p:<20} {d[:50]}')

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

with open('cts_sap_packages.json','w',encoding='utf-8') as f:
    json.dump({'tadir':tadir_map,'dd02t':dd02t_map,'dd25t':dd25t_map}, f, ensure_ascii=False)

# Re-inject into dashboard
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]
with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)

print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
print('Done!')
