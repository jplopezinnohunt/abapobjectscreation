"""
cts_tadir_fullscan.py
=====================
Reads ALL of TADIR in paginated chunks (no WHERE filter, which is blocked
on this system). Then matches locally against the objects in cts_10yr_raw.json.

TADIR has ~500K–2M rows on a typical system. We read in pages of 5000 rows.
Checkpointing after each page allows resumption.

Output: cts_10yr_enriched.json (raw JSON + devclass/dlvunit per object)
"""
import json, os, sys
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
import pyrfc

def env(*keys, default=''):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

def rfc_connect():
    params = {
        'ashost': env('SAP_D01_ASHOST','SAP_HOST', default='HQ-SAP-D01.HQ.INT.UNESCO.ORG'),
        'sysnr':  env('SAP_D01_SYSNR','SAP_SYSNR', default='00'),
        'client': env('SAP_D01_CLIENT','SAP_CLIENT', default='350'),
    }
    snc_mode = env('SAP_D01_SNC_MODE','SAP_SNC_MODE')
    snc_pn   = env('SAP_D01_SNC_PARTNERNAME','SAP_SNC_PARTNERNAME')
    if snc_mode and snc_pn:
        params['snc_mode'] = snc_mode
        params['snc_partnername'] = snc_pn
        params['snc_qop'] = env('SAP_SNC_QOP', default='9')
        print('  [RFC] SNC')
    else:
        params['user']   = env('SAP_D01_USER','SAP_USER')
        params['passwd'] = env('SAP_D01_PASSWORD','SAP_PASSWORD')
        print('  [RFC] Basic auth')
    return pyrfc.Connection(**params)

# ── Load which objects we need ─────────────────────────────────────────────────
print('Loading cts_10yr_raw.json...')
with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

SKIP_TYPES  = {'RELE','MERG','SBUL','ACGR','TABU','CINS','CINC','CPUB','CPRO','CPRI',
               'CLSD','METH','SBYP','SBYL','SBXP','SBHL','SBHP','SOTU','LODE','ADIR',
               'CDAT','CPUB','CINS','MERG','RELE'}
# Collect lookup: (obj_type, obj_name) we need DEVCLASS for
needed = set()
for t in raw['transports']:
    if t.get('trkorr','').upper().startswith('E9BK'): continue
    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        if ot and on and ot not in SKIP_TYPES:
            needed.add((ot, on))

print(f'Objects needing TADIR lookup: {len(needed):,}')
needed_by_type = defaultdict(set)
for (ot, on) in needed:
    needed_by_type[ot].add(on)

# ── Checkpoint ────────────────────────────────────────────────────────────────
CHECKPOINT = 'tadir_fullscan_checkpoint.json'
enrichment  = {}   # "TYPE|OBJ_NAME" -> {devclass, dlvunit}
rows_scanned = 0

if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT, encoding='utf-8') as f:
        saved = json.load(f)
    enrichment   = saved.get('enrichment', {})
    rows_scanned = saved.get('rows_scanned', 0)
    print(f'Checkpoint: {len(enrichment):,} enriched, {rows_scanned:,} rows already scanned')

# ── Stream TADIR in pages ─────────────────────────────────────────────────────
PAGE_SIZE = 5000
SAVE_EVERY = 50000   # Save checkpoint every N rows

print('\nConnecting to SAP...')
conn = rfc_connect()
print('Connected!\n')
print(f'Reading TADIR in pages of {PAGE_SIZE}... (will save every {SAVE_EVERY} rows)')
print('Press Ctrl+C to stop and resume later.\n')

found_total = len(enrichment)
skip = rows_scanned

try:
    while True:
        result = conn.call('RFC_READ_TABLE',
            QUERY_TABLE='TADIR',
            DELIMITER='|',
            FIELDS=[
                {'FIELDNAME': 'PGMID'},
                {'FIELDNAME': 'OBJECT'},
                {'FIELDNAME': 'OBJ_NAME'},
                {'FIELDNAME': 'DEVCLASS'},
                {'FIELDNAME': 'DLVUNIT'},
            ],
            OPTIONS=[],   # NO filter — allows cross-client read
            ROWCOUNT=PAGE_SIZE,
            ROWSKIPS=skip,
        )

        page_data = result['DATA']
        if not page_data:
            print(f'\nTADIR fully scanned. Total rows: {skip + len(page_data):,}')
            break

        # Parse and match
        page_matched = 0
        for row in page_data:
            wa = row['WA']
            parts = wa.split('|')
            if len(parts) < 5:
                continue
            pgmid    = parts[0].strip()
            obj_type = parts[1].strip().upper()
            obj_name = parts[2].strip()
            devclass = parts[3].strip()
            dlvunit  = parts[4].strip()

            # Check if we need this object
            if obj_type in needed_by_type and obj_name in needed_by_type[obj_type]:
                key = f'{obj_type}|{obj_name}'
                if key not in enrichment:
                    enrichment[key] = {'devclass': devclass, 'dlvunit': dlvunit}
                    found_total += 1
                    page_matched += 1

        skip += len(page_data)
        rows_scanned = skip

        # Progress
        matched_pct = found_total / len(needed) * 100 if needed else 0
        print(f'  Scanned {skip:>8,} rows | Matched {found_total:>6,} / {len(needed):,} ({matched_pct:.1f}%) | Page hits: {page_matched}')

        # Save checkpoint
        if skip % SAVE_EVERY < PAGE_SIZE or len(page_data) < PAGE_SIZE:
            with open(CHECKPOINT, 'w', encoding='utf-8') as f:
                json.dump({'enrichment': enrichment, 'rows_scanned': rows_scanned}, f)
            print(f'  [CHECKPOINT saved at {skip:,} rows]')

        # Early exit if we found everything
        if found_total >= len(needed):
            print('\nAll needed objects found! Stopping early.')
            break

except KeyboardInterrupt:
    print('\nInterrupted — saving checkpoint...')

conn.close()

# Final checkpoint save
with open(CHECKPOINT, 'w', encoding='utf-8') as f:
    json.dump({'enrichment': enrichment, 'rows_scanned': rows_scanned}, f)
print(f'Checkpoint saved: {len(enrichment):,} enriched, {rows_scanned:,} rows scanned')

# ── Merge into raw JSON ────────────────────────────────────────────────────────
print(f'\nMerging enrichment into transport objects...')
enriched_count = 0
for t in raw['transports']:
    for o in t.get('objects', []):
        ot  = o.get('obj_type', o.get('OBJECT','')).strip().upper()
        on  = o.get('obj_name', o.get('OBJ_NAME','')).strip()
        key = f'{ot}|{on}'
        if key in enrichment:
            o['devclass'] = enrichment[key].get('devclass','')
            o['dlvunit']  = enrichment[key].get('dlvunit','')
            if o['devclass']:
                enriched_count += 1

print(f'Enriched {enriched_count:,} object instances')
with open('cts_10yr_enriched.json', 'w', encoding='utf-8') as f:
    json.dump(raw, f, ensure_ascii=False)
print('Saved: cts_10yr_enriched.json')
