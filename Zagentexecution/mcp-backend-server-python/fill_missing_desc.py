"""
fill_missing_desc.py
Analyses what's still missing descriptions after the main lookup, 
then queries additional SAP Dictionary tables to fill gaps:
- TNROT: Number Range Object texts (for NROB)
- TPARA: Parameter descriptions (for PARA)
- Re-tries DD02T for all still-missing names
- Builds a regex-based pattern fill for Y/Z custom tables
"""
import json, os, time
from dotenv import load_dotenv
import pyrfc
from collections import Counter

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

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

missing_desc  = {n: v for n, v in cfg.items() if not v.get('desc', '').strip()}
has_desc      = len(cfg) - len(missing_desc)
print(f'Total: {len(cfg)} | Has desc: {has_desc} | Missing: {len(missing_desc)}')

# Breakdown by type
type_count = Counter(v['obj_type'] for v in missing_desc.values())
print('\nMissing desc by type:')
for t, c in type_count.most_common(20):
    print(f'  {t:<12} {c}')

conn = pyrfc.Connection(**CONN_PARAMS)
print('\nRFC connected')

BATCH = 5
desc_added = {}

def batch_query_desc(names_and_key, table, key_field, text_field):
    """Generic batch desc lookup."""
    found = {}
    all_keys = list(names_and_key.keys())
    for i in range(0, len(all_keys), BATCH):
        batch = all_keys[i:i+BATCH]
        or_clause = ' OR '.join(f"{key_field} = '{n}'" for n in batch)
        rows = rfc_read(conn, table, f"DDLANGUAGE = 'E' AND ( {or_clause} )", [key_field, text_field], max_rows=BATCH+2)
        for row in rows:
            k = row.get(key_field, '').strip()
            t = row.get(text_field, '').strip()
            if k and t:
                found[k] = t
    return found

# 1. Re-try DD02T for all missing (catching anything missed)
print('\nRe-querying DD02T for missing TABU/TDAT/VIED/DATED objects...')
tabu_missing = {n: v for n, v in missing_desc.items()
                if v['obj_type'] in ('TABU','TDAT','DATED','CUAD','CUS0','CUS1')}
found_dd02t = batch_query_desc(tabu_missing, 'DD02T', 'TABNAME', 'DDTEXT')
desc_added.update(found_dd02t)
print(f'  DD02T retry: +{len(found_dd02t)}')

# 2. DD25T for views still missing
print('Querying DD25T for missing view objects...')
view_missing = {n: v for n, v in missing_desc.items()
                if v['obj_type'] in ('VDAT','CDAT','VIED','SCVI')}
found_dd25t = batch_query_desc(view_missing, 'DD25T', 'VIEWNAME', 'DDTEXT')
desc_added.update(found_dd25t)
print(f'  DD25T views: +{len(found_dd25t)}')

# 3. TNROT for Number Range Objects (NROB)
print('Querying TNROT for NROB...')
nrob_missing = {n: v for n, v in missing_desc.items() if v['obj_type'] == 'NROB'}
if nrob_missing:
    found_nrob = {}
    all_nrob = list(nrob_missing.keys())
    for i in range(0, len(all_nrob), BATCH):
        batch = all_nrob[i:i+BATCH]
        or_clause = ' OR '.join(f"OBJECT = '{n}'" for n in batch)
        rows = rfc_read(conn, 'TNROT', f"LANGU = 'E' AND ( {or_clause} )", ['OBJECT','TXT'], max_rows=BATCH+2)
        for row in rows:
            k = row.get('OBJECT','').strip()
            t = row.get('TXT','').strip()
            if k and t: found_nrob[k] = 'NR: ' + t
    desc_added.update(found_nrob)
    print(f'  TNROT: +{len(found_nrob)}')

# 4. TPARA for Parameters (PARA)
print('Querying TPARA for PARA...')
para_missing = {n: v for n, v in missing_desc.items() if v['obj_type'] == 'PARA'}
if para_missing:
    found_para = {}
    all_para = list(para_missing.keys())
    for i in range(0, len(all_para), BATCH):
        batch = all_para[i:i+BATCH]
        or_clause = ' OR '.join(f"PARID = '{n}'" for n in batch)
        rows = rfc_read(conn, 'TPARA', f"LANGU = 'E' AND ( {or_clause} )", ['PARID','PARTEXT'], max_rows=BATCH+2)
        for row in rows:
            k = row.get('PARID','').strip()
            t = row.get('PARTEXT','').strip()
            if k and t: found_para[k] = 'Param: ' + t
    desc_added.update(found_para)
    print(f'  TPARA: +{len(found_para)}')

# 5. DOKHL for documentation texts (catches Y/Z custom tables)
print('Querying DOKTL for Y/Z custom table texts...')
yz_missing = {n: v for n, v in missing_desc.items() if n.startswith(('Y','Z'))}
if yz_missing:
    found_yz = {}
    all_yz = list(yz_missing.keys())
    for i in range(0, len(all_yz), BATCH):
        batch = all_yz[i:i+BATCH]
        or_clause = ' OR '.join(f"TABNAME = '{n}'" for n in batch)
        rows = rfc_read(conn, 'DD02T', f"DDLANGUAGE = 'E' AND ( {or_clause} )", ['TABNAME','DDTEXT'], max_rows=BATCH+2)
        for row in rows:
            k = row.get('TABNAME','').strip()
            t = row.get('DDTEXT','').strip()
            if k and t: found_yz[k] = t
    desc_added.update(found_yz)
    print(f'  Y/Z DD02T: +{len(found_yz)}')

conn.close()

# Merge new descriptions
newly_filled = 0
for name, desc in desc_added.items():
    if name in cfg and desc:
        cfg[name]['desc'] = desc
        newly_filled += 1

final_with_desc = sum(1 for v in cfg.values() if v.get('desc','').strip())
print(f'\nResult: +{newly_filled} new | Total with desc: {final_with_desc}/{len(cfg)} ({final_with_desc*100//len(cfg)}%)')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# Re-inject
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG_JS + html[e:]
with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
