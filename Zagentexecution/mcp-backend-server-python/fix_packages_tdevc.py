"""
fix_packages_tdevc.py
1. Identify objects with wrong/inferred package values (contains spaces or parens)
2. Re-query TADIR for those objects with all object types (not just TABU)
3. Fetch TDEVC package short descriptions for all real packages
4. Save enriched data and re-inject into dashboard
"""
import json, os, re, time
from dotenv import load_dotenv
import pyrfc

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
CONN = dict(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr=os.environ.get('SAP_SYSNR','00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user=os.environ.get('SAP_USER','jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)

def build_opts(where, ml=72):
    words, lines, cur = where.split(' '), [], ''
    for w in words:
        c = (cur+' '+w).strip()
        if len(c) <= ml: cur = c
        else:
            if cur: lines.append({'TEXT': cur})
            cur = w
    if cur: lines.append({'TEXT': cur})
    return lines

def rfc_read(conn, table, where, fields, maxr=200):
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table, DELIMITER='|', ROWSKIPS=0, ROWCOUNT=maxr,
            FIELDS=[{'FIELDNAME':f} for f in fields], OPTIONS=build_opts(where))
        out = []
        for row in r.get('DATA',[]):
            parts = [p.strip() for p in row['WA'].split('|')]
            out.append(dict(zip(fields, parts+['']*(len(fields)-len(parts)))))
        return out
    except: return []

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── Step 1: Identify bad package values ──────────────────────────────────────
def is_bad_pkg(pkg):
    if not pkg: return False
    # Real DEVCLASS: uppercase, underscores, max 30 chars, no spaces, no parens
    return bool(re.search(r'[ \(\)]', pkg)) or not re.match(r'^[A-Z0-9_/]{1,30}$', pkg)

bad_pkg_names = [n for n, v in cfg.items() if is_bad_pkg(v.get('package',''))]
no_pkg_names  = [n for n, v in cfg.items() if not v.get('package','')]
print(f'Bad package values: {len(bad_pkg_names)}')
print(f'No package at all:  {len(no_pkg_names)}')
print(f'Examples of bad: {bad_pkg_names[:5]}')

# Clear bad packages so they don't pollute display
for n in bad_pkg_names:
    cfg[n]['package'] = ''

# ── Step 2: Re-query TADIR for all bad + no-package objects ──────────────────
to_requery = list(set(bad_pkg_names + no_pkg_names))
print(f'\nRe-querying TADIR for {len(to_requery)} objects...')

conn = pyrfc.Connection(**CONN)
print('RFC connected')

BATCH = 5
fixed = 0
t0 = time.time()
for i in range(0, len(to_requery), BATCH):
    batch = to_requery[i:i+BATCH]
    # Query without restricting OBJECT type — catches TABU, VIED, DOMA, CLAS etc.
    or_clause = ' OR '.join(f"OBJ_NAME = '{n}'" for n in batch)
    rows = rfc_read(conn, 'TADIR', f"PGMID = 'R3TR' AND ( {or_clause} )",
                    ['OBJ_NAME','DEVCLASS','OBJECT'], maxr=BATCH*3)
    for r in rows:
        n = r['OBJ_NAME']
        pkg = r['DEVCLASS']
        if n in cfg and pkg and not is_bad_pkg(pkg):
            cfg[n]['package'] = pkg
            fixed += 1

elapsed = time.time()-t0
print(f'Fixed {fixed} packages in {elapsed:.0f}s')

# ── Step 3: Fetch TDEVC package descriptions ─────────────────────────────────
all_pkgs = sorted(set(v.get('package','') for v in cfg.values() if v.get('package','')))
print(f'\nFetching TDEVC descriptions for {len(all_pkgs)} unique packages...')

pkg_desc = {}
for i in range(0, len(all_pkgs), BATCH):
    batch = all_pkgs[i:i+BATCH]
    or_clause = ' OR '.join(f"DEVCLASS = '{p}'" for p in batch)
    rows = rfc_read(conn, 'TDEVC', f"( {or_clause} )", ['DEVCLASS','CTEXT'], maxr=BATCH+2)
    for r in rows:
        k = r.get('DEVCLASS','').strip()
        t = r.get('CTEXT','').strip()
        if k and t: pkg_desc[k] = t

conn.close()
print(f'TDEVC: {len(pkg_desc)} package descriptions found')

# Sample
print('\nSample package descriptions:')
for p,d in list(pkg_desc.items())[:15]:
    print(f'  {p:<30} {d}')

# ── Step 4: Add pkg_desc to cfg objects ──────────────────────────────────────
for name, v in cfg.items():
    pkg = v.get('package','')
    if pkg and pkg in pkg_desc:
        v['pkg_desc'] = pkg_desc[pkg]

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

with open('cts_pkg_descriptions.json','w',encoding='utf-8') as f:
    json.dump(pkg_desc, f, ensure_ascii=False)

print(f'\nSaved. Objects with valid package: {sum(1 for v in cfg.values() if v.get("package"))}')
print(f'Objects with pkg_desc: {sum(1 for v in cfg.values() if v.get("pkg_desc"))}')
