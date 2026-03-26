"""
fill_type_specific.py
Targets each object type to the correct SAP Dictionary table:
  TTYP / SOTT → DD26T (table types)
  LODE        → DDSEXTLP (lock object) or DD29L/DDXTF
  TOBJ        → TTOBJT (authorization object texts)
  SCVI        → SCVA (screen variant) - no text table, use name
  AVAS        → CLASSL or CABN (characteristics)
  OSOA        → T685T (condition type texts)
  CUAD, CUS0  → IMGA (IMG activity texts)
  CDAT        → DD02T with TABCLASS=CLUSTER
  VARX        → no standard text — use from package / type hint
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
    words, lines, current = where_str.split(' '), [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current: lines.append({'TEXT': current})
            current = word
    if current: lines.append({'TEXT': current})
    return lines

def rfc_read(conn, table, where_str, fields, max_rows=200):
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table, DELIMITER='|', ROWSKIPS=0, ROWCOUNT=max_rows,
            FIELDS=[{'FIELDNAME': f} for f in fields],
            OPTIONS=build_options(where_str),
        )
        out = []
        for row in r.get('DATA', []):
            parts = [p.strip() for p in row['WA'].split('|')]
            out.append(dict(zip(fields, parts + ['']*(len(fields)-len(parts)))))
        return out
    except Exception as e:
        return []

BATCH = 5

def batch_query(conn, table, key_col, text_col, name_list, prefix='', lang_col=None, lang='E'):
    found = {}
    for i in range(0, len(name_list), BATCH):
        batch = name_list[i:i+BATCH]
        or_clause = ' OR '.join(f"{key_col} = '{n}'" for n in batch)
        if lang_col:
            where = f"{lang_col} = 'E' AND ( {or_clause} )"
        else:
            where = f"( {or_clause} )"
        rows = rfc_read(conn, table, where, [key_col, text_col], max_rows=BATCH+2)
        for row in rows:
            k = row.get(key_col,'').strip()
            t = row.get(text_col,'').strip()
            if k and t:
                found[k] = (prefix + t) if prefix else t
    return found

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

from collections import defaultdict
by_type = defaultdict(list)
for name, v in cfg.items():
    if not v.get('desc','').strip():
        by_type[v['obj_type']].append(name)

print('Missing by type:')
for t, ns in sorted(by_type.items(), key=lambda x: -len(x[1])):
    print(f'  {t:<10} {len(ns)}')

conn = pyrfc.Connection(**CONN_PARAMS)
print('RFC connected\n')

total_added = {}

# 1. TTYP and SOTT → DD26T (type pool / table type descriptions)
for otype in ('TTYP', 'SOTT'):
    names = by_type.get(otype, [])
    if names:
        print(f'DD26T for {otype} ({len(names)})...')
        found = batch_query(conn, 'DD26T', 'TYPENAME', 'DDTEXT', names, lang_col='DDLANGUAGE')
        total_added.update(found)
        print(f'  +{len(found)}')

# 2. LODE → DD03L is lock object, texts in DDSEXTLP / DDENQT
# Lock objects: try DD29L (lock object includes) text in DD02T with the lock table name
for otype in ('LODE',):
    names = by_type.get(otype, [])
    if names:
        print(f'DD02T for LODE lock objects ({len(names)})...')
        found = batch_query(conn, 'DD02T', 'TABNAME', 'DDTEXT', names, lang_col='DDLANGUAGE')
        # also try without language filter 
        missing_found = [n for n in names if n not in found]
        if missing_found:
            found2 = batch_query(conn, 'DD02T', 'TABNAME', 'DDTEXT', missing_found)
            found.update(found2)
        for k in found:
            if not found[k].startswith('Lock'):
                found[k] = 'Lock: ' + found[k]
        total_added.update(found)
        print(f'  +{len(found)}')

# 3. TOBJ → TTOBJT (authorization object texts)
names_tobj = by_type.get('TOBJ', [])
if names_tobj:
    print(f'TTOBJT for TOBJ ({len(names_tobj)})...')
    found = batch_query(conn, 'TTOBJT', 'OBJECT', 'TTEXT', names_tobj, lang_col='LANGU')
    total_added.update(found)
    print(f'  +{len(found)}')

# 4. CUAD / CUS0 / CUS1 → IMGA (IMG Activity texts)
for otype in ('CUAD','CUS0','CUS1'):
    names = by_type.get(otype, [])
    if names:
        print(f'IMGA for {otype} ({len(names)})...')
        found = batch_query(conn, 'IMGA', 'ACTIVITY', 'ACTTEXT', names, lang_col='SPRAS', prefix='IMG: ')
        total_added.update(found)
        print(f'  +{len(found)}')

# 5. SCVI → SCVI table for screen variant (no separate text table — build from package/variant name)
# Generate auto-descriptions for screen variants
names_scvi = by_type.get('SCVI', [])
if names_scvi:
    print(f'Generating SCVI auto-descriptions ({len(names_scvi)})...')
    cnt = 0
    for n in names_scvi:
        parts = n.split('_')
        if len(parts) >= 2:
            total_added[n] = f'Screen variant: {n}'
            cnt += 1
    print(f'  auto-filled +{cnt}')

# 6. AVAS → CABN (Characteristics) 
names_avas = by_type.get('AVAS', [])
if names_avas:
    print(f'CABN for AVAS characteristics ({len(names_avas)})...')
    found = batch_query(conn, 'CABN', 'ATNAM', 'ATBEZ', names_avas)
    total_added.update({k: 'Char: '+v for k,v in found.items()})
    print(f'  +{len(found)}')

# 7. OSOA → T685T (SD Condition types / Output sorts)
names_osoa = by_type.get('OSOA', [])
if names_osoa:
    print(f'T685T for OSOA ({len(names_osoa)})...')
    found = batch_query(conn, 'T685T', 'KSCHL', 'VTEXT', names_osoa, lang_col='SPRAS')
    total_added.update(found)
    print(f'  +{len(found)}')
    # Also try TNAPR / TNAST (output types)
    still_missing = [n for n in names_osoa if n not in found]
    if still_missing:
        found2 = batch_query(conn, 'TNAPT', 'KSCHL', 'VTEXT', still_missing, lang_col='SPRAS', prefix='Output: ')
        total_added.update(found2)
        print(f'  TNAPT: +{len(found2)}')

# 8. PDTS (PD types) → HRT1000 or T528T
names_pdts = by_type.get('PDTS', [])
if names_pdts:
    print(f'HRT1000 for PDTS ({len(names_pdts)})...')
    # PD types often have numeric keys; skip if non-numeric
    found = batch_query(conn, 'T528T', 'ACTIO', 'ATEXT', names_pdts, lang_col='SPRSL')
    total_added.update(found)
    print(f'  +{len(found)}')

# 9. CDAT → DD02T (cluster data)
names_cdat = by_type.get('CDAT', [])
if names_cdat:
    print(f'DD02T for CDAT ({len(names_cdat)})...')
    found = batch_query(conn, 'DD02T', 'TABNAME', 'DDTEXT', names_cdat, lang_col='DDLANGUAGE')
    total_added.update(found)
    print(f'  +{len(found)}')

conn.close()

# Merge
newly_filled = 0
for name, desc in total_added.items():
    if name in cfg and desc:
        cfg[name]['desc'] = desc
        newly_filled += 1

final = sum(1 for v in cfg.values() if v.get('desc','').strip())
pct = final * 100 // len(cfg)
print(f'\nNewly filled: {newly_filled} | Total desc: {final}/{len(cfg)} ({pct}%)')

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# Re-inject dashboard
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG_JS + html[e:]
with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
