"""Check D01 REGUH.EMPFG directly via RFC.

Mirror of the P01 check (verify_p01_reguh_empfg.py) but pointed at D01.
The prior conclusion that 'D01 has no alt-payee runs' was based on the
narrow REGUH extract (8 cols) — EMPFG was never inspected. This script
goes straight to D01 REGUH.EMPFG via RFC_READ_TABLE.
"""
import os
from collections import Counter
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')

# D01 uses unprefixed SAP_* with SNC. No password (locked).
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01 via SNC")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# Step 1: D01 REGUH with EMPFG populated (all dates — D01 has limited data)
print("\n=== D01 REGUH.EMPFG populated (any date) ===")
try:
    rows = rd("REGUH",
              ["EMPFG <> ' '"],
              ["LAUFD","LAUFI","ZBUKR","LIFNR","EMPFG","XVORL"],
              n=2000)
    print(f"  HITS: {len(rows)}")
    by_format = {}  # we'll annotate FORMI via DFPAYG below
    for r in rows[:40]:
        print(f"  {r['LAUFD']}/{r['LAUFI']}/{r['ZBUKR']} LIFNR={r['LIFNR']} EMPFG={r['EMPFG']} XVORL='{r['XVORL']}'")
    if len(rows) > 40:
        print(f"  ... and {len(rows)-40} more")
except Exception as e:
    print(f"  ERR: {e}")
    rows = []

# Step 2: cross-ref EMPFG hits → DFPAYG to learn format
if rows:
    print(f"\n=== Cross-ref D01 EMPFG fires → DFPAYG format ===")
    formi_dist = Counter()
    examples_per_formi = {}
    seen_runs = set()
    for r in rows:
        laufd, laufi, zb = r['LAUFD'].strip(), r['LAUFI'].strip(), r['ZBUKR'].strip()
        run_key = (laufd, laufi, zb)
        if run_key in seen_runs:
            continue
        seen_runs.add(run_key)
        try:
            gpg = rd("DFPAYG",
                     [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                     ["FORMI"], n=10)
            for g in gpg:
                formi = g['FORMI'].strip()
                formi_dist[formi] += 1
                if formi not in examples_per_formi:
                    examples_per_formi[formi] = f"{laufd}/{laufi}/{zb}"
        except Exception:
            pass

    print(f"  Format breakdown of D01 EMPFG runs:")
    for formi, n in formi_dist.most_common():
        print(f"    {formi:40s} {n} runs  (example: {examples_per_formi[formi]})")

# Step 3: total summary
print(f"\n=== Summary D01 ===")
print(f"  REGUH.EMPFG rows: {len(rows)}")
print(f"  Distinct runs with EMPFG: {len(seen_runs) if rows else 0}")
