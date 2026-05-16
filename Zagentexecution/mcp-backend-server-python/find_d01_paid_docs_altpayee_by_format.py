"""For D01: list all PAID docs with alt-payee (REGUH.EMPFG populated),
grouped by the DMEE format that processed them.

Method:
  1. Pull all D01 REGUH rows where EMPFG <> '' (any date)
  2. For each unique (LAUFD, LAUFI, ZBUKR), look up DFPAYG.FORMI
  3. For each REGUH row, pull REGUP items (the FI docs that got paid via that EMPFG)
  4. Cross-tab: format → list of (source LIFNR, alt-payee, paid docs)

Note: we use REGUH.EMPFG (resolved alt-payee at proposal time) because it captures
BOTH doc-level (BSEG.EMPFB) AND master-level (LFA1.LNRZA, LFB1.LNRZB) alt-payee.
BSEG cluster can't be read via RFC_READ_TABLE.
"""
import os
from collections import defaultdict
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# Step 1: all REGUH with EMPFG
print("\n=== STEP 1: D01 REGUH with EMPFG populated ===")
reguh = rd("REGUH",
           ["EMPFG <> ' '"],
           ["LAUFD","LAUFI","ZBUKR","LIFNR","EMPFG","XVORL","VBLNR"], n=2000)
print(f"  {len(reguh)} REGUH rows")

# Step 2: for each unique run, look up DFPAYG format
print("\n=== STEP 2: DFPAYG format per run ===")
unique_runs = sorted({(r['LAUFD'].strip(), r['LAUFI'].strip(), r['ZBUKR'].strip()) for r in reguh})
print(f"  {len(unique_runs)} unique runs")
run_to_formi = {}
for laufd, laufi, zb in unique_runs:
    try:
        gpg = rd("DFPAYG",
                 [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                 ["FORMI"], n=10)
        formis = set(g['FORMI'].strip() for g in gpg)
        run_to_formi[(laufd, laufi, zb)] = formis
    except Exception:
        run_to_formi[(laufd, laufi, zb)] = set()

# Step 3: per format, list (run, source LIFNR, alt-payee, REGUP items)
print("\n=== STEP 3: organize by format ===")
by_format = defaultdict(list)  # formi → list of (laufd, laufi, lifnr, alt_empfg, xvorl)
for r in reguh:
    key = (r['LAUFD'].strip(), r['LAUFI'].strip(), r['ZBUKR'].strip())
    formis = run_to_formi.get(key, set())
    for f in formis:
        by_format[f].append({
            'laufd': key[0], 'laufi': key[1], 'zbukr': key[2],
            'lifnr': r['LIFNR'].strip(), 'empfg': r['EMPFG'].strip(),
            'xvorl': r['XVORL'].strip(), 'vblnr': r['VBLNR'].strip(),
        })

# Step 4: print summary per format
print("\n=== STEP 4: summary per DMEE format ===")
for formi in sorted(by_format.keys()):
    entries = by_format[formi]
    unique_pairs = sorted({(e['lifnr'], e['empfg']) for e in entries})
    unique_runs_fmt = sorted({(e['laufd'], e['laufi']) for e in entries})
    # filter: only show pairs with a real source LIFNR (not the batch-tag fixtures)
    real_pairs = [(l, e) for l, e in unique_pairs if l and e.startswith('>') and e.endswith('>Z')]
    batch_pairs = [(l, e) for l, e in unique_pairs if not l or not (e.startswith('>') and e.endswith('>Z'))]
    print(f"\n  {formi}")
    print(f"    Runs: {len(unique_runs_fmt)}  Pairs (LIFNR,EMPFG): {len(unique_pairs)}  Real: {len(real_pairs)}  Batch-tag: {len(batch_pairs)}")
    if real_pairs:
        print(f"    --- REAL alt-payee pairs ---")
        for lifnr, empfg in real_pairs[:10]:
            # Also show runs that fired this pair
            runs = sorted({(e['laufd'], e['laufi']) for e in entries if e['lifnr']==lifnr and e['empfg']==empfg})
            print(f"      SOURCE={lifnr}  →  EMPFG={empfg}   in runs: {runs[:3]}")

# Step 5: for the TOP candidate(s), pull REGUP items
print("\n=== STEP 5: paid documents per real alt-payee fire ===")
for formi, entries in by_format.items():
    real_entries = [e for e in entries if e['lifnr'] and e['empfg'].startswith('>')]
    if not real_entries:
        continue
    print(f"\n  --- {formi} ---")
    seen_runs = set()
    for e in real_entries:
        run_key = (e['laufd'], e['laufi'], e['zbukr'])
        if run_key in seen_runs:
            continue
        seen_runs.add(run_key)
        try:
            regup = rd("REGUP",
                       [f"LAUFD = '{e['laufd']}'", f" AND LAUFI = '{e['laufi']}'",
                        f" AND ZBUKR = '{e['zbukr']}'", f" AND LIFNR = '{e['lifnr']}'"],
                       ["BUKRS","BELNR","GJAHR","BUZEI","BLART","BLDAT"], n=20)
            print(f"    Run {e['laufd']}/{e['laufi']}/{e['zbukr']}  source={e['lifnr']} → alt={e['empfg']}")
            for p in regup:
                print(f"      Doc paid: {p['BUKRS']}/{p['BELNR']}/{p['GJAHR']}/{p['BUZEI']} BLART={p['BLART']} BLDAT={p['BLDAT']}")
        except Exception as ex:
            print(f"    REGUP err for {e['laufd']}/{e['laufi']}: {ex}")
