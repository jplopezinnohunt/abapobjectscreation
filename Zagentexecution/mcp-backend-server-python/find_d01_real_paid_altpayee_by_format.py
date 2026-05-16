"""Find REAL paid alt-payee cases in D01 by format.

A 'real' payment is one with:
  - XVORL = '' (posted, not proposal)
  - VBLNR has prefix '0002' or '3400' (= actual clearing doc, not placeholder)
  - EMPFG is populated

The previous analysis polluted results with placeholders (VBLNR 0100000000) and
proposals (VBLNR empty or F110*).
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

# Pull all REGUH EMPFG fires — 2 narrow passes joined positionally
print("\n=== Pulling ALL D01 REGUH EMPFG rows ===")
a = rd("REGUH", ["EMPFG <> ' '"], ["LAUFD","LAUFI","ZBUKR","LIFNR","EMPFG"], n=2000)
b = rd("REGUH", ["EMPFG <> ' '"], ["LAUFD","LAUFI","ZBUKR","XVORL","VBLNR"], n=2000)
combined = []
for ra, rb in zip(a, b):
    combined.append({
        'laufd': ra['LAUFD'].strip(), 'laufi': ra['LAUFI'].strip(),
        'zbukr': ra['ZBUKR'].strip(), 'lifnr': ra['LIFNR'].strip(),
        'empfg': ra['EMPFG'].strip(),
        'xvorl': rb['XVORL'].strip(), 'vblnr': rb['VBLNR'].strip(),
    })
print(f"  {len(combined)} REGUH-EMPFG rows total")

# Filter: real payments only
real = [r for r in combined
        if r['xvorl'] == ''
        and r['vblnr']
        and r['vblnr'][:4] in ('0002','3400')]
print(f"  REAL payments (XVORL='', VBLNR prefix 0002/3400): {len(real)}")

# For each real payment, look up DFPAYG.FORMI
print("\n=== Cross-ref real-payment runs to DMEE format ===")
run_to_formi = {}
unique_runs = sorted({(r['laufd'], r['laufi'], r['zbukr']) for r in real})
print(f"  {len(unique_runs)} unique runs with real payment + EMPFG")
for laufd, laufi, zb in unique_runs:
    try:
        gpg = rd("DFPAYG",
                 [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                 ["FORMI"], n=10)
        run_to_formi[(laufd, laufi, zb)] = set(g['FORMI'].strip() for g in gpg)
    except Exception:
        run_to_formi[(laufd, laufi, zb)] = set()

# Group real payments by format
by_format = defaultdict(list)
for r in real:
    formis = run_to_formi.get((r['laufd'], r['laufi'], r['zbukr']), set())
    for f in formis:
        by_format[f].append(r)

# Filter by EMPFG pattern (real >NNNNNNNNNN>Z vs batch-tag)
print("\n=== Real-payment alt-payee fires by format ===")
for formi in sorted(by_format.keys()):
    entries = by_format[formi]
    real_pairs = [e for e in entries
                  if e['lifnr'] and e['empfg'].startswith('>') and e['empfg'].endswith('>Z')]
    batch_pairs = [e for e in entries if e not in real_pairs]
    print(f"\n  {formi}")
    print(f"    Total real-payment rows: {len(entries)}")
    print(f"    REAL alt-payee pairs   : {len(real_pairs)}")
    print(f"    Batch-tag fixtures     : {len(batch_pairs)}")
    if real_pairs:
        # Unique runs + pairs
        unique_pairs = sorted({(e['lifnr'], e['empfg']) for e in real_pairs})
        print(f"    --- unique (source, alt-payee) pairs paid via real payment ---")
        for lifnr, empfg in unique_pairs[:15]:
            runs = sorted({(e['laufd'], e['laufi']) for e in real_pairs
                          if e['lifnr']==lifnr and e['empfg']==empfg})
            vblnrs = sorted({e['vblnr'] for e in real_pairs
                            if e['lifnr']==lifnr and e['empfg']==empfg})
            print(f"      SOURCE={lifnr}  →  ALT={empfg}")
            print(f"         runs: {runs[:3]}")
            print(f"         VBLNRs: {vblnrs[:5]}")
