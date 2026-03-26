"""
fast_tadir_lookup.py
Single-pass RFC call using pyrfc directly (not subprocess).
Fetches DEVCLASS from TADIR and DDTEXT from DD02T for all config objects in one shot each.
"""
import json, os, sys
from dotenv import load_dotenv
import pyrfc

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

conn = pyrfc.Connection(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr=os.environ.get('SAP_SYSNR','00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user=os.environ.get('SAP_USER','jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)
print('RFC connected')

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── TADIR: all TABU/VDAT/NROB etc, PGMID=R3TR — no object name filter, read all ──
# Then filter client-side — much faster than 521 OR batches
print('Querying TADIR (unfiltered, R3TR objects)...')
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='TADIR',
    DELIMITER='|',
    ROWSKIPS=0,
    ROWCOUNT=0,
    FIELDS=[{'FIELDNAME':'OBJ_NAME'},{'FIELDNAME':'DEVCLASS'},{'FIELDNAME':'OBJECT'}],
    OPTIONS=[{'TEXT':"PGMID = 'R3TR'"}],
)
tadir_map = {}
for row in result.get('DATA',[]):
    parts = row['WA'].split('|')
    if len(parts) >= 2:
        name = parts[0].strip()
        pkg  = parts[1].strip()
        if name and pkg:
            tadir_map[name] = pkg

print(f'TADIR: {len(tadir_map)} total entries')

# ── DD02T: all table texts (English) ─────────────────────────────────────────
print('Querying DD02T...')
result2 = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='DD02T',
    DELIMITER='|',
    ROWSKIPS=0,
    ROWCOUNT=0,
    FIELDS=[{'FIELDNAME':'TABNAME'},{'FIELDNAME':'DDTEXT'}],
    OPTIONS=[{'TEXT':"DDLANGUAGE = 'E'"}],
)
dd02t_map = {}
for row in result2.get('DATA',[]):
    parts = row['WA'].split('|')
    if len(parts) >= 2:
        name = parts[0].strip()
        text = parts[1].strip()
        if name and text:
            dd02t_map[name] = text
print(f'DD02T: {len(dd02t_map)} entries')

# ── DD25T: view texts ─────────────────────────────────────────────────────────
print('Querying DD25T (views)...')
try:
    result3 = conn.call('RFC_READ_TABLE',
        QUERY_TABLE='DD25T',
        DELIMITER='|',
        ROWSKIPS=0,
        ROWCOUNT=0,
        FIELDS=[{'FIELDNAME':'VIEWNAME'},{'FIELDNAME':'DDTEXT'}],
        OPTIONS=[{'TEXT':"DDLANGUAGE = 'E'"}],
    )
    dd25t_map = {}
    for row in result3.get('DATA',[]):
        parts = row['WA'].split('|')
        if len(parts) >= 2:
            name = parts[0].strip()
            text = parts[1].strip()
            if name and text:
                dd25t_map[name] = text
    print(f'DD25T: {len(dd25t_map)} view entries')
except Exception as e:
    dd25t_map = {}
    print(f'DD25T skip: {e}')

conn.close()

# ── Merge into config detail ──────────────────────────────────────────────────
pkg_hits  = 0
desc_hits = 0
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

print(f'\nMatched: {pkg_hits} packages, {desc_hits} descriptions (of {len(cfg)})')

# Sample output
sample = [(n, v['package'], v.get('desc','')) for n,v in cfg.items() if v.get('package') and v.get('desc')][:15]
print('\nSample (name | package | description):')
for n,p,d in sample:
    print(f'  {n:<30} {p:<20} {d}')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

with open('cts_sap_packages.json', 'w', encoding='utf-8') as f:
    json.dump({'tadir': tadir_map, 'dd02t': dd02t_map, 'dd25t': dd25t_map}, f, ensure_ascii=False)

# Re-inject into dashboard
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]
with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\nDone! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
