"""
targeted_tadir_v2.py
Same approach but properly splits WHERE clause into 72-char lines for RFC_READ_TABLE.
"""
import json, os, time
from dotenv import load_dotenv
import pyrfc

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
CONN_PARAMS = dict(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr=os.environ.get('SAP_SYSNR','00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user=os.environ.get('SAP_USER','jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)

def build_options(where_str, max_len=72):
    """Split a WHERE clause into RFC_READ_TABLE OPTIONS lines of max_len."""
    words   = where_str.split(' ')
    lines   = []
    current = ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                lines.append({'TEXT': current})
            current = word
    if current:
        lines.append({'TEXT': current})
    return lines

def rfc_read(conn, table, where_str, fields, max_rows=300):
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table,
            DELIMITER='|',
            ROWSKIPS=0,
            ROWCOUNT=max_rows,
            FIELDS=[{'FIELDNAME': f} for f in fields],
            OPTIONS=build_options(where_str),
        )
        out = []
        for row in r.get('DATA', []):
            parts = [p.strip() for p in row['WA'].split('|')]
            out.append(dict(zip(fields, parts + ['']*(len(fields)-len(parts)))))
        return out
    except Exception as e:
        # silently skip batch on error
        return []

# ── Test single object first ─────────────────────────────────────────────────
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

conn = pyrfc.Connection(**CONN_PARAMS)
print('RFC connected')

# Quick sanity check
test = rfc_read(conn, 'TADIR', "PGMID = 'R3TR' AND OBJ_NAME = 'TCALS'",
                ['OBJ_NAME','DEVCLASS'], max_rows=5)
print(f'Sanity check TCALS: {test}')

test2 = rfc_read(conn, 'DD02T', "DDLANGUAGE = 'E' AND TABNAME = 'TCALS'",
                 ['TABNAME','DDTEXT'], max_rows=5)
print(f'Sanity DD02T TCALS: {test2}')

# ── Batch all config objects in groups of 5 (short names) ────────────────────
BATCH = 5   # Small batch to stay under 72-char line limits
all_names = sorted(cfg.keys())
tadir_map = {}
dd02t_map = {}
dd25t_map = {}

t0 = time.time()
total = len(all_names)

for i in range(0, total, BATCH):
    batch = all_names[i:i+BATCH]

    # TADIR
    or_clause = ' OR '.join(f"OBJ_NAME = '{n}'" for n in batch)
    rows = rfc_read(conn, 'TADIR', f"PGMID = 'R3TR' AND ( {or_clause} )",
                    ['OBJ_NAME','DEVCLASS'], max_rows=BATCH+2)
    for r in rows:
        if r['OBJ_NAME'] and r['DEVCLASS']:
            tadir_map[r['OBJ_NAME']] = r['DEVCLASS']

    # DD02T
    or_t = ' OR '.join(f"TABNAME = '{n}'" for n in batch)
    rows_t = rfc_read(conn, 'DD02T', f"DDLANGUAGE = 'E' AND ( {or_t} )",
                      ['TABNAME','DDTEXT'], max_rows=BATCH+2)
    for r in rows_t:
        if r['TABNAME'] and r['DDTEXT']:
            dd02t_map[r['TABNAME']] = r['DDTEXT']

    # DD25T for views
    view_batch = [n for n in batch if cfg[n].get('obj_type') in ('VDAT','CDAT','VIED')]
    if view_batch:
        or_v = ' OR '.join(f"VIEWNAME = '{n}'" for n in view_batch)
        rows_v = rfc_read(conn, 'DD25T', f"DDLANGUAGE = 'E' AND ( {or_v} )",
                          ['VIEWNAME','DDTEXT'], max_rows=BATCH+2)
        for r in rows_v:
            if r['VIEWNAME'] and r['DDTEXT']:
                dd25t_map[r['VIEWNAME']] = r['DDTEXT']

    done = min(i+BATCH, total)
    if done % 200 == 0 or done == total:
        elapsed = time.time()-t0
        rate = done/elapsed if elapsed > 0 else 0
        eta = (total-done)/rate if rate > 0 else 0
        print(f'  [{done}/{total}] pkg={len(tadir_map)} desc={len(dd02t_map)+len(dd25t_map)} ETA={eta:.0f}s')

conn.close()
elapsed = time.time()-t0
print(f'\nDone in {elapsed:.0f}s | pkg={len(tadir_map)} | desc={len(dd02t_map)} | views={len(dd25t_map)}')

# Merge
for name, v in cfg.items():
    if name in tadir_map:
        v['package'] = tadir_map[name]
    if name in dd02t_map:
        v['desc'] = dd02t_map[name]
    elif name in dd25t_map:
        v['desc'] = dd25t_map[name]

# Sample
sample = [(n,v.get('package',''),v.get('desc','')) for n,v in cfg.items() if v.get('package') and v.get('desc')][:15]
print('\nSample:')
for n,p,d in sample:
    print(f'  {n:<30} {p:<15} {d[:55]}')

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

with open('cts_sap_packages.json','w',encoding='utf-8') as f:
    json.dump({'tadir':tadir_map,'dd02t':dd02t_map,'dd25t':dd25t_map}, f, ensure_ascii=False)

# Re-inject dashboard
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG_JS + html[e:]
with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
