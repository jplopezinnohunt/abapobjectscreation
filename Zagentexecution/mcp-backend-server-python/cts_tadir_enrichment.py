"""
cts_tadir_enrichment.py
=======================
Queries TADIR for every unique (PGMID, OBJECT, OBJ_NAME) in cts_10yr_raw.json
to retrieve DEVCLASS and DLVUNIT — the true functional domain.

TADIR columns we need:
  PGMID    - Repository ID (CORR or LIMU)
  OBJECT   - Object type (PROG, CLAS, TABU, etc.)
  OBJ_NAME - Object name
  DEVCLASS - Package (e.g. ZHCM_PAYROLL, ZFI_ACCOUNTS)
  DLVUNIT  - Software component/unit (e.g. ZEAPC, SAP_HR)
  SRCSYSTEM- Originating system

Strategy:
  1. Collect all unique (OBJECT, OBJ_NAME) pairs from raw JSON
  2. Batch by OBJECT type — query TADIR WHERE OBJECT = 'CLAS' AND OBJ_NAME IN (...)
     But RFC_READ_TABLE doesn't support IN → query per OBJ_NAME (batched)
  3. Checkpoint per object type to allow resumption
  4. Save enrichment map: { obj_type+obj_name -> {devclass, dlvunit} }
  5. Merge back into a cts_10yr_enriched.json
"""
import json, os, sys, time
from collections import defaultdict

# ── SAP connection ────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv() # Load .env file

def env(key, default=None):
    return os.environ.get(key, default)

try:
    import pyrfc
    from pyrfc import Connection
except ImportError:
    print("pyrfc not installed — run: pip install pyrfc"); sys.exit(1)

def rfc_connect():
    snc_mode = env('SAP_D01_SNC_MODE') or env('SAP_SNC_MODE')
    snc_pn   = env('SAP_D01_SNC_PARTNERNAME') or env('SAP_SNC_PARTNERNAME')
    params = {
        "ashost": env("SAP_D01_ASHOST") or env("SAP_HOST") or "HQ-SAP-D01.HQ.INT.UNESCO.ORG",
        "sysnr":  env("SAP_D01_SYSNR")  or env("SAP_SYSNR")  or "00",
        "client": env("SAP_D01_CLIENT") or env("SAP_CLIENT") or "350",
    }
    if snc_mode and snc_pn:
        params["snc_mode"]        = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"]         = env("SAP_D01_SNC_QOP") or env("SAP_SNC_QOP") or "9"
        print("  [RFC] SNC connection to D01")
    else:
        params["user"]   = env("SAP_D01_USER") or env("SAP_USER")
        params["passwd"] = env("SAP_D01_PASSWORD") or env("SAP_PASSWORD")
        print("  [RFC] Basic auth to D01")
    return Connection(**params)

def rfc_read_table(conn, table, fields, options, max_rows=5000):
    """Wrapper for RFC_READ_TABLE with automatic field parsing."""
    try:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table,
            DELIMITER='|',
            FIELDS=[{'FIELDNAME': f} for f in fields],
            OPTIONS=[{'TEXT': o} for o in options],
            ROWCOUNT=max_rows
        )
        rows = []
        col_names = [f['FIELDNAME'] for f in result['FIELDS']]
        col_offsets = [(int(f['OFFSET']), int(f['OFFSET']) + int(f['LENGTH'])) for f in result['FIELDS']]
        for data_row in result['DATA']:
            line = data_row['WA']
            parts = line.split('|')
            if len(parts) >= len(col_names):
                rows.append({col_names[i]: parts[i].strip() for i in range(len(col_names))})
        return rows
    except Exception as e:
        return []

# ── Load raw data ─────────────────────────────────────────────────────────────
print("Loading cts_10yr_raw.json...")
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# Collect unique (OBJECT type, OBJ_NAME) — skip EPI-USE and transport meta
SKIP_TYPES = {'RELE','MERG','SBUL'}
unique_objects = set()   # (obj_type, obj_name)
for t in raw['transports']:
    if t.get('trkorr','').upper().startswith('E9BK'): continue
    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        if ot and on and ot not in SKIP_TYPES:
            unique_objects.add((ot, on))

# Group by object type for efficient batching
by_type = defaultdict(list)
for (ot, on) in unique_objects:
    by_type[ot].append(on)

print(f"Unique objects to enrich: {len(unique_objects):,} across {len(by_type)} types")

# ── Load checkpoint ───────────────────────────────────────────────────────────
CHECKPOINT = 'tadir_enrichment_checkpoint.json'
enrichment  = {}   # key: "TYPE|OBJ_NAME" -> {devclass, dlvunit}
completed_types = set()

if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT, encoding='utf-8') as f:
        saved = json.load(f)
    enrichment       = saved.get('enrichment', {})
    completed_types  = set(saved.get('completed_types', []))
    print(f"Checkpoint loaded: {len(enrichment):,} enriched, {len(completed_types)} types done")

# ── Process each type ─────────────────────────────────────────────────────────
# Strategy: ONE RFC call per object type pulling ALL rows for that type.
# 168 object types = 168 RFC calls total (vs 29,100 individual calls).
# Filter locally to only the names we care about.
type_order = sorted(by_type.keys(), key=lambda t: -len(by_type[t]))

print(f"\nConnecting to SAP...")
conn = rfc_connect()
print("Connected.")

for obj_type in type_order:
    if obj_type in completed_types:
        print(f"  [{obj_type}] already done — skip", end='\r')
        continue

    names_needed = set(by_type[obj_type])
    print(f"\n  [{obj_type}] {len(names_needed):,} objects — bulk TADIR query...")

    # Pull ALL TADIR rows for this object type (one RFC call)
    all_rows = rfc_read_table(conn, 'TADIR',
        ['OBJ_NAME','DEVCLASS','DLVUNIT'],
        [f"OBJECT = '{obj_type}'"],
        max_rows=50000
    )

    # Build lookup from the result
    tadir_map = {r['OBJ_NAME'].strip(): r for r in all_rows}
    type_found = 0
    for obj_name in names_needed:
        key = f"{obj_type}|{obj_name}"
        match = tadir_map.get(obj_name, tadir_map.get(obj_name[:40], None))
        if match:
            enrichment[key] = {
                'devclass': match.get('DEVCLASS','').strip(),
                'dlvunit':  match.get('DLVUNIT','').strip(),
            }
            if match.get('DEVCLASS','').strip():
                type_found += 1
        else:
            enrichment[key] = {'devclass':'','dlvunit':''}

    completed_types.add(obj_type)
    print(f"    -> {type_found:,}/{len(names_needed)} found in TADIR ({len(all_rows):,} rows pulled)")

    # Save checkpoint after each type
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump({'enrichment': enrichment, 'completed_types': list(completed_types)}, f)

conn.close()

# ── Merge enrichment back into raw JSON ───────────────────────────────────────
print(f"\nMerging enrichment into transport objects...")
enriched_count = 0
for t in raw['transports']:
    for o in t.get('objects', []):
        ot  = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on  = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        key = f"{ot}|{on}"
        if key in enrichment:
            info = enrichment[key]
            o['devclass']  = info.get('devclass','')
            o['dlvunit']   = info.get('dlvunit','')
            o['srcsystem'] = info.get('srcsystem','')
            if info.get('devclass'):
                enriched_count += 1

print(f"Enriched {enriched_count:,} object instances with DEVCLASS/DLVUNIT")

with open('cts_10yr_enriched.json', 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False)
print("Saved: cts_10yr_enriched.json")
print("Done! Re-run cts_domain_year_type.py pointing to cts_10yr_enriched.json for precise domains.")
