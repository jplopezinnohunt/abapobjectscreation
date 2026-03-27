"""
extract_payment_objects.py
Extract ALL custom SAP objects related to payment processing.
Queries TADIR from P01 for packages: YWFI, YFIP, YFI*, YCEI, YDEF_FI, ZFI*
Also searches by object name patterns: Z*PAYM*, Y*PAYM*, Z*BCM*, Z*WF_FI*, Z*SWIFT*
Saves to Gold DB table: payment_objects
"""
import sys, io, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

try:
    import pyrfc
    HAS_RFC = True
except ImportError:
    HAS_RFC = False
    print("pyrfc not available — will use tadir_enrichment from Gold DB only")

DB = Path(__file__).parent.parent / 'sap_data_extraction/sqlite/p01_gold_master_data.db'
db = sqlite3.connect(str(DB))

def read_table(conn, table, fields, where='', max_rows=5000):
    try:
        opts = [{'TEXT': where}] if where else []
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table,
            FIELDS=[{'FIELDNAME': f} for f in fields],
            OPTIONS=opts,
            ROWCOUNT=max_rows,
            DELIMITER='|')
        rows = []
        field_names = [f['FIELDNAME'] for f in r['FIELDS']]
        for d in r['DATA']:
            vals = [v.strip() for v in d['WA'].split('|')]
            rows.append(dict(zip(field_names, vals)))
        return rows, field_names
    except Exception as e:
        print(f"  ERROR reading {table}: {e}")
        return [], []

all_objects = []

if HAS_RFC:
    P01 = {'ashost':'172.16.4.100','sysnr':'00','client':'300','snc_partnername':'p:CN=P01, OU=SAP-Systems, O=UNESCO, C=FR','snc_lib':'C:/Program Files/SAP/FrontEnd/SAPgui/sapcrypto.dll','snc_myname':'p:CN=JLOPEZ, OU=Users, O=UNESCO, C=FR','snc_qop':'9','snc_sso':'1'}
    try:
        conn = pyrfc.Connection(**P01)
        print("Connected to P01")

        # ── Payment-related packages
        PAY_PACKAGES = ['YWFI','YFIP','YFIPA','YDEF_FI','YWFI_FI','YCEI','YYWFI']
        print(f"\nSearching packages: {PAY_PACKAGES}")
        for pkg in PAY_PACKAGES:
            rows, _ = read_table(conn, 'TADIR',
                ['PGMID','OBJECT','OBJ_NAME','DEVCLASS','SRCSYSTEM','AUTHOR','CREATED_ON'],
                f"DEVCLASS = '{pkg}'")
            if rows:
                print(f"  {pkg}: {len(rows)} objects")
                for r in rows:
                    r['source'] = f'PACKAGE:{pkg}'
                    all_objects.append(r)

        # ── Search by name patterns
        PATTERNS = [
            ("Z*PAYM*", "TADIR obj name Z*PAYM*"),
            ("Y*PAYM*", "TADIR obj name Y*PAYM*"),
            ("Z*BCM*",  "TADIR obj name Z*BCM*"),
            ("Z*WF_FI*","TADIR obj name Z*WF_FI*"),
            ("Y*WF_FI*","TADIR obj name Y*WF_FI*"),
            ("Z*SWIFT*","TADIR obj name Z*SWIFT*"),
            ("Z*DMEE*", "TADIR obj name Z*DMEE*"),
            ("Y*DMEE*", "TADIR obj name Y*DMEE*"),
            ("Z*F110*", "TADIR obj name Z*F110*"),
            ("Y*F110*", "TADIR obj name Y*F110*"),
            ("ZFI_*",   "TADIR obj name ZFI_*"),
            ("YFI_*",   "TADIR obj name YFI_*"),
        ]
        seen = set()
        for pattern, desc in PATTERNS:
            rows, _ = read_table(conn, 'TADIR',
                ['PGMID','OBJECT','OBJ_NAME','DEVCLASS','AUTHOR','CREATED_ON'],
                f"OBJ_NAME LIKE '{pattern}'")
            for r in rows:
                key = r.get('OBJ_NAME','') + r.get('OBJECT','')
                if key not in seen:
                    seen.add(key)
                    r['source'] = desc
                    all_objects.append(r)
            if rows:
                print(f"  Pattern {pattern}: {len(rows)} objects")

        # ── Specific known objects (ensure they're included)
        KNOWN = ['ZPAYM','ZFI_PAYREL_EMAIL','SAPFPAYM_SCHEDULE','VBWF15']
        for nm in KNOWN:
            rows, _ = read_table(conn, 'TADIR',
                ['PGMID','OBJECT','OBJ_NAME','DEVCLASS','AUTHOR','CREATED_ON'],
                f"OBJ_NAME = '{nm}'")
            for r in rows:
                key = r.get('OBJ_NAME','') + r.get('OBJECT','')
                if key not in seen:
                    seen.add(key)
                    r['source'] = 'KNOWN_OBJECT'
                    all_objects.append(r)

        # ── Also get FUNCTION MODULE details for YWFI
        print("\nGetting function modules in YWFI package...")
        fm_rows, _ = read_table(conn, 'TFDIR',
            ['FUNCNAME','PNAME','FMODE','REMOTE_CALL'],
            "PNAME LIKE 'SAPL%WF%FI%'")
        print(f"  TFDIR YWFI-like FMs: {len(fm_rows)}")
        for r in fm_rows:
            r['OBJECT'] = 'FUNC'
            r['OBJ_NAME'] = r.get('FUNCNAME','')
            r['DEVCLASS'] = 'via_TFDIR'
            r['source'] = 'TFDIR_YWFI'
            seen_key = r['OBJ_NAME'] + 'FUNC'
            if seen_key not in seen:
                seen.add(seen_key)
                all_objects.append(r)

        conn.close()
        print(f"\nTotal objects found: {len(all_objects)}")
    except Exception as e:
        print(f"RFC connection failed: {e}")
        HAS_RFC = False

# ── Supplement from tadir_enrichment (Gold DB)
print("\nSearching tadir_enrichment in Gold DB...")
pay_terms = ['PAYM','BCM','SWIFT','DMEE','F110','WF_FI','PAYREL','ZFI_','YFI_']
local_hits = []
for row in db.execute('SELECT obj_type, obj_name, devclass FROM tadir_enrichment').fetchall():
    obj_name = row[1] or ''
    devclass = row[2] or ''
    if any(t in obj_name.upper() for t in pay_terms) or any(t in devclass.upper() for t in ['YWFI','YFIP','YCEI']):
        local_hits.append({'OBJECT':row[0], 'OBJ_NAME':row[1], 'DEVCLASS':row[2], 'source':'tadir_enrichment'})
print(f"  tadir_enrichment payment objects: {len(local_hits)}")

# Merge
seen_local = set(r.get('OBJ_NAME','') + r.get('OBJECT','') for r in all_objects)
for r in local_hits:
    key = r['OBJ_NAME'] + r['OBJECT']
    if key not in seen_local:
        all_objects.append(r)
        seen_local.add(key)

# ── Save to DB
db.execute('DROP TABLE IF EXISTS payment_objects')
db.execute('''CREATE TABLE payment_objects (
    object_type TEXT, obj_name TEXT, devclass TEXT,
    pgmid TEXT, author TEXT, created_on TEXT, source TEXT,
    description TEXT
)''')

for r in all_objects:
    db.execute('INSERT INTO payment_objects VALUES (?,?,?,?,?,?,?,?)', (
        r.get('OBJECT',''),
        r.get('OBJ_NAME','') or r.get('FUNCNAME',''),
        r.get('DEVCLASS',''),
        r.get('PGMID',''),
        r.get('AUTHOR',''),
        r.get('CREATED_ON',''),
        r.get('source',''),
        r.get('description','')
    ))
db.commit()
print(f"\nSaved {len(all_objects)} objects to payment_objects table")

# ── Print summary
print("\n=== PAYMENT OBJECTS BY TYPE ===")
for r in db.execute("""
    SELECT object_type, COUNT(*) as cnt, GROUP_CONCAT(DISTINCT devclass) as pkgs
    FROM payment_objects GROUP BY object_type ORDER BY cnt DESC
""").fetchall():
    print(f"  {r[0]:10} {r[1]:4}  packages: {(r[2] or '')[:80]}")

print("\n=== ALL OBJECTS (sorted by type + name) ===")
for r in db.execute("""
    SELECT object_type, obj_name, devclass, source
    FROM payment_objects ORDER BY object_type, obj_name
""").fetchall():
    print(f"  {r[0]:10} {r[1]:40} {r[2]:15} [{r[3]}]")

db.close()
