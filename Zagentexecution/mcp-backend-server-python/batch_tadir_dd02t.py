"""
batch_tadir_dd02t.py
Queries SAP TADIR (for DEVCLASS) and DD02T (for short description)
for all config objects in cts_config_detail.json using query_table.py infrastructure.
Processes in small batches using OR conditions.
"""
import json, os, subprocess, sys, re
from collections import defaultdict

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

all_names = sorted(cfg.keys())
print(f'Objects to look up: {len(all_names)}')

devclass_map  = {}  # name -> DEVCLASS
desc_map      = {}  # name -> short description

def run_query(table, options, fields, rows=500):
    """Run query_table.py and parse pipe-delimited output."""
    cmd = [
        sys.executable, 'query_table.py', table,
        '--options', options,
        '--fields', fields,
        '--total_rows', str(rows),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace')
        lines = r.stdout.splitlines()
        # Find separator line
        in_data = False
        header_fields = []
        results = []
        for line in lines:
            if line.startswith('---'): continue
            if '|' in line and not in_data:
                header_fields = [h.strip() for h in line.split('|')]
                in_data = True
                continue
            if line.startswith('---') or line.startswith('--'):
                continue
            if in_data and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                row = dict(zip(header_fields, parts))
                results.append(row)
        return results
    except Exception as e:
        print(f'  Query error: {e}')
        return []

# ── TADIR: Get DEVCLASS in batches ───────────────────────────────────────────
BATCH = 8   # small batches due to WHERE clause length limits in RFC_READ_TABLE
print('\n=== TADIR fetch ===')
done = 0
for i in range(0, len(all_names), BATCH):
    batch = all_names[i:i+BATCH]
    # Build WHERE clause
    name_list = ' OR '.join(f"OBJ_NAME = '{n}'" for n in batch)
    where = f"PGMID = 'R3TR' AND ({name_list})"
    rows = run_query('TADIR', where, 'OBJ_NAME,DEVCLASS,OBJECT', rows=len(batch)+2)
    for row in rows:
        name = row.get('OBJ_NAME','').strip()
        pkg  = row.get('DEVCLASS','').strip()
        if name and pkg:
            devclass_map[name] = pkg
    done += len(batch)
    if done % 80 == 0 or done >= len(all_names):
        print(f'  TADIR: {done}/{len(all_names)} — found {len(devclass_map)} packages')

print(f'TADIR complete: {len(devclass_map)} packages found')

# ── DD02T: Get short descriptions ────────────────────────────────────────────
print('\n=== DD02T fetch ===')
# DD02T has TABNAME and DDTEXT
done = 0
for i in range(0, len(all_names), BATCH):
    batch = all_names[i:i+BATCH]
    name_list = ' OR '.join(f"TABNAME = '{n}'" for n in batch)
    where = f"DDLANGUAGE = 'E' AND ({name_list})"
    rows = run_query('DD02T', where, 'TABNAME,DDTEXT', rows=len(batch)+2)
    for row in rows:
        name = row.get('TABNAME','').strip()
        desc = row.get('DDTEXT','').strip()
        if name and desc:
            desc_map[name] = desc
    done += len(batch)
    if done % 80 == 0 or done >= len(all_names):
        print(f'  DD02T: {done}/{len(all_names)} — found {len(desc_map)} descriptions')

print(f'DD02T complete: {len(desc_map)} descriptions found')

# ── Also try DD01T for domain texts (for VDAT type objects) ──────────────────
# VDAT objects use view names — try DD25T (view texts)
view_names = [n for n, v in cfg.items() if v.get('obj_type') in ('VDAT','CDAT')]
print(f'\n=== DD25T fetch for {len(view_names)} views ===')
for i in range(0, len(view_names), BATCH):
    batch = view_names[i:i+BATCH]
    name_list = ' OR '.join(f"VIEWNAME = '{n}'" for n in batch)
    where = f"DDLANGUAGE = 'E' AND ({name_list})"
    rows = run_query('DD25T', where, 'VIEWNAME,DDTEXT', rows=len(batch)+2)
    for row in rows:
        name = row.get('VIEWNAME','').strip()
        desc = row.get('DDTEXT','').strip()
        if name and desc and name not in desc_map:
            desc_map[name] = desc
print(f'DD25T complete: {len(desc_map)} total descriptions')

# ── Save raw lookups ──────────────────────────────────────────────────────────
with open('cts_sap_packages.json', 'w', encoding='utf-8') as f:
    json.dump({'devclass': devclass_map, 'descriptions': desc_map}, f, ensure_ascii=False, indent=2)

# ── Merge into config detail ──────────────────────────────────────────────────
for name, v in cfg.items():
    if name in devclass_map:
        v['package'] = devclass_map[name]
    if name in desc_map and not v.get('desc'):
        v['desc'] = desc_map[name]
    elif name in desc_map:  # SAP description always wins
        v['desc'] = desc_map[name]

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

real_pkgs  = sum(1 for v in cfg.values() if v.get('package','').startswith(('S','P','K','A','H','F','M','T','Z','Y')) and not v.get('package','').startswith('Z_CUSTOM'))
real_descs = sum(1 for v in cfg.values() if v.get('desc',''))
print(f'\nSummary:')
print(f'  Real DEVCLASS packages: {len(devclass_map)}')
print(f'  Real DD02T descriptions: {len(desc_map)}')
print(f'  Objects with desc: {real_descs}')
print('Saved cts_config_detail.json and cts_sap_packages.json')

# ── Re-inject into dashboard ──────────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]
with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
