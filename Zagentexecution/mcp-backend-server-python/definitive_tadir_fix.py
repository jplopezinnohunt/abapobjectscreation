"""
definitive_tadir_fix.py
=======================
The ROOT CAUSE of wrong packages: previous queries hit TADIR without
filtering by OBJECT type. TADIR can have multiple rows for the same
OBJ_NAME (e.g. TABL=ZHR_DEV and DOMA=YBC for name 'YTHR_UNDP').

Fix: for each config object, query TADIR with OBJECT = correct type.

CACHING: saves results to tadir_cache.sqlite so we NEVER call SAP again
for the same (obj_type, obj_name) pair.
"""
import json, os, re, time, sqlite3
from dotenv import load_dotenv
import pyrfc

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
CONN = dict(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr =os.environ.get('SAP_SYSNR', '00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user  =os.environ.get('SAP_USER',  'jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)

# ── CTS obj_type → TADIR OBJECT mapping ──────────────────────────────────────
# CTS obj_type is the E071.OBJECT field.
# For content-type objects (TABU, TDAT) the DEVCLASS comes from the TABLE def.
OBJ_MAP = {
    # Content → underlying table definition
    'TABU': 'TABL', 'TDAT': 'TABL', 'CDAT': 'TABL', 'DATED': 'TABL',
    'TABD': 'TABL', 'TABT': 'TABL',
    # Views
    'VDAT': 'VIEW', 'VIED': 'VIEW',
    # Repository objects — direct 1:1
    'DOMA': 'DOMA', 'DTEL': 'DTEL', 'NROB': 'NROB', 'TTYP': 'TTYP',
    'LODE': 'TABL',  # HR Logical Database Object — under TABL in TADIR
    'OSOA': 'OSOA',  # DataSource
    'SCVI': 'SCVI',  # Screen variant
    'TOBJ': 'SUSO',  # Auth object → SU21
    'PARA': 'PARA',  # Parameter
    'AVAS': 'AVAS',  # Classification characteristic value assignment
    'PMKC': 'CHAR',  # PM Characteristic → CABN
    'VARX': 'VARX',  # Report variant
    'PDTS': 'PDTS',  # HR pay scale/period parameter
    'CUAD': 'CUAD',  # IMG Activity
    'CUS0': 'CUS0',
    'CUS1': 'CUS1',
    'CUS2': 'CUS2',
    'SOTT': 'SOTR',  # OTR short text → SOTR in TADIR
    'SOTS': 'SOTR',
    'LODC': 'ENQU',  # Lock object
    'CLAS': 'CLAS',  # Classification class
    'FORM': 'FORM',  # SAPscript form
    'SMIM': 'SMIM',  # BSP MIME repository
    'PROG': 'PROG',  # ABAP program
    'FUGR': 'FUGR',  # Function group
    'CLAS': 'CLAS',
    'DOMA': 'DOMA',
}
DEFAULT_OBJ = None  # if not in map → query without OBJECT filter (catches all)

# ── SQLite cache ──────────────────────────────────────────────────────────────
cache_db = os.path.join(os.path.dirname(__file__), 'tadir_cache.sqlite')
cconn = sqlite3.connect(cache_db)
cconn.execute('''CREATE TABLE IF NOT EXISTS tadir_cache (
    obj_type TEXT, obj_name TEXT, devclass TEXT,
    PRIMARY KEY (obj_type, obj_name))''')
cconn.commit()

def cache_get(obj_type, obj_name):
    r = cconn.execute('SELECT devclass FROM tadir_cache WHERE obj_type=? AND obj_name=?',
                      (obj_type, obj_name)).fetchone()
    return r[0] if r else None

def cache_set_batch(rows):  # rows = [(obj_type, obj_name, devclass)]
    cconn.executemany('INSERT OR REPLACE INTO tadir_cache VALUES (?,?,?)', rows)
    cconn.commit()

# Load existing cache
cached = {(r[0],r[1]):r[2] for r in cconn.execute('SELECT obj_type,obj_name,devclass FROM tadir_cache').fetchall()}
print(f'Cache loaded: {len(cached)} entries')

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── Identify objects needing lookup ──────────────────────────────────────────
def is_valid_pkg(pkg):
    return bool(pkg) and re.match(r'^[A-Z0-9_/]{1,30}$', str(pkg))

# Only re-query objects NOT already in cache
need_lookup = []
for name, v in cfg.items():
    key = (v.get('obj_type',''), name)
    if key in cached:
        devclass = cached[key]
        v['package'] = devclass if is_valid_pkg(devclass) else ''
    else:
        need_lookup.append((name, v.get('obj_type','')))

print(f'Already cached: {len(cfg)-len(need_lookup)}, Need SAP lookup: {len(need_lookup)}')

# ── Group by TADIR OBJECT type for efficient batching ─────────────────────────
from collections import defaultdict
by_tadir_obj = defaultdict(list)
for name, obj_type in need_lookup:
    tadir_obj = OBJ_MAP.get(obj_type, obj_type)  # fallback: use obj_type itself
    by_tadir_obj[tadir_obj].append((name, obj_type))

print(f'Object type groups to query: {dict((k,len(v)) for k,v in by_tadir_obj.items())}')

# ── RFC helper ────────────────────────────────────────────────────────────────
def build_opts(where, ml=72):
    """Split WHERE clause into 72-char lines for RFC_READ_TABLE"""
    tokens, lines, cur = where.split(' '), [], ''
    for w in tokens:
        c = (cur + ' ' + w).strip()
        if len(c) <= ml:
            cur = c
        else:
            if cur: lines.append({'TEXT': cur})
            cur = w
    if cur: lines.append({'TEXT': cur})
    return lines

def tadir_batch(conn, obj_names, tadir_object):
    """Query TADIR for a batch of names filtered by OBJECT type."""
    # Build WHERE: OBJECT = 'TABL' AND ( OBJ_NAME = 'X' OR OBJ_NAME = 'Y' ... )
    or_names = ' OR '.join(f"OBJ_NAME = '{n}'" for n in obj_names)
    where = f"PGMID = 'R3TR' AND OBJECT = '{tadir_object}' AND ( {or_names} )"
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='TADIR', DELIMITER='|', ROWSKIPS=0,
            ROWCOUNT=len(obj_names)+5,
            FIELDS=[{'FIELDNAME':'OBJ_NAME'},{'FIELDNAME':'DEVCLASS'},{'FIELDNAME':'OBJECT'}],
            OPTIONS=build_opts(where))
        result = {}
        for row in r.get('DATA',[]):
            parts = [p.strip() for p in row['WA'].split('|')]
            if len(parts) >= 2:
                result[parts[0]] = parts[1]
        return result
    except Exception as e:
        print(f'  RFC error ({tadir_object}): {e}')
        return {}

# ── Run lookup ────────────────────────────────────────────────────────────────
if need_lookup:
    sap = pyrfc.Connection(**CONN)
    print('RFC connected')
    
    BATCH = 5
    fixed = 0
    new_cache = []
    t0 = time.time()
    
    for tadir_obj, items in by_tadir_obj.items():
        names = [n for n, _ in items]
        obj_types = {n: ot for n, ot in items}
        
        for i in range(0, len(names), BATCH):
            batch = names[i:i+BATCH]
            result = tadir_batch(sap, batch, tadir_obj)
            
            for name in batch:
                devclass = result.get(name, '')
                ot = obj_types[name]
                new_cache.append((ot, name, devclass))
                if is_valid_pkg(devclass):
                    cfg[name]['package'] = devclass
                    fixed += 1
                elif 'package' in cfg.get(name, {}):
                    # Clear bad inferred package
                    cfg[name]['package'] = ''
    
    sap.close()
    print(f'Fixed {fixed} packages in {time.time()-t0:.0f}s')
    
    # Save to cache
    cache_set_batch(new_cache)
    print(f'Cache now: {len(cached)+len(new_cache)} entries saved to tadir_cache.sqlite')

cconn.close()

# ── Summary ───────────────────────────────────────────────────────────────────
total = len(cfg)
with_pkg = sum(1 for v in cfg.values() if is_valid_pkg(v.get('package','')))
print(f'\nPackage coverage: {with_pkg}/{total} ({100*with_pkg//total}%)')

# Show sample of key objects the user reported as wrong
for test_name in ['YTHR_UNDP','YVHR_REGGR_TXT','YTHR_ANSVH_DASH','TCALS','T16FV']:
    if test_name in cfg:
        v = cfg[test_name]
        print(f'  {test_name}: obj_type={v.get("obj_type")} package={v.get("package")} pkg_desc={v.get("pkg_desc","")}')

# Save updated config
with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)
print('\nSaved cts_config_detail.json')
print('Now re-inject into dashboard by running: python reinject_cfgdetail.py')
