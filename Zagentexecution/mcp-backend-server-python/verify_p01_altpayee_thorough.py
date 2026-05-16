"""Verificación exhaustiva: alt-payee en P01 producción para los 3 formatos UNESCO.

Tres mecanismos forenses distintos:
  (1) BSEG.EMPFG     — alt-payee LIFNR a nivel línea de doc (override por documento)
  (2) BSEC.NAME1/etc — one-time vendor address (CPD)
  (3) LFA1.LNRZA + LFB1.LNRZB — alt-payee a nivel master (ya validado vía Gold DB)

Sesión #75 anterior solo verificó (2) con muestreo 2.5%. Aquí extendemos:
  - Probar si EMPFG existe como columna utilizable en BSAK/BSIK
  - Ampliar el scan a 1000+ runs por formato si la columna existe
"""
import os
from collections import Counter
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_P01_ASHOST'), sysnr=os.getenv('SAP_P01_SYSNR'),
    client=os.getenv('SAP_P01_CLIENT'), user=os.getenv('SAP_P01_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_P01_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected P01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# ── Test 1: confirm EMPFG exists in BSAK by requesting it ────────────────────
print("\n=== TEST 1: confirm EMPFG column in BSAK ===")
try:
    rows = rd("BSAK",
              ["BUDAT >= '20240101'"],
              ["BUKRS","BELNR","LIFNR","EMPFG"],
              n=200)
    print(f"  Read OK: {len(rows)} rows returned")
    populated = [r for r in rows if r['EMPFG'].strip()]
    print(f"  Rows with EMPFG populated: {len(populated)} of {len(rows)}")
    if populated:
        print("  EXAMPLES of EMPFG fire in BSAK:")
        for r in populated[:10]:
            print(f"    {r['BUKRS']}/{r['BELNR']} LIFNR={r['LIFNR']} EMPFG={r['EMPFG']}")
    else:
        print("  EMPFG column exists but NEVER populated in this 200-row sample.")
except Exception as e:
    print(f"  ERR: {e}")

# ── Test 2: scan BSAK for EMPFG-populated rows by chunking on BUKRS ─────────
print("\n=== TEST 2: scan BSAK by BUKRS (UNES/ICTP/IIEP/UIL) for EMPFG hits ===")
empfg_hits = {}
for bukrs in ('UNES','ICTP','IIEP','UIL'):
    try:
        rows = rd("BSAK",
                  [f"BUKRS = '{bukrs}'", " AND BUDAT >= '20240101'"],
                  ["BUKRS","BELNR","GJAHR","LIFNR","EMPFG","BUDAT"],
                  n=5000)
        hits = [r for r in rows if r['EMPFG'].strip()]
        empfg_hits[bukrs] = hits
        print(f"  {bukrs}: {len(rows)} BSAK rows scanned, {len(hits)} have EMPFG populated")
        for h in hits[:5]:
            print(f"    {h['BUKRS']}/{h['BELNR']}/{h['GJAHR']} LIFNR={h['LIFNR']} EMPFG={h['EMPFG']} BUDAT={h['BUDAT']}")
    except Exception as e:
        print(f"  {bukrs}: ERR {e}")

# ── Test 3: scan BSIK (open items) for any EMPFG ─────────────────────────────
print("\n=== TEST 3: scan BSIK (open items) ===")
for bukrs in ('UNES','ICTP'):
    try:
        rows = rd("BSIK",
                  [f"BUKRS = '{bukrs}'"],
                  ["BUKRS","BELNR","GJAHR","LIFNR","EMPFG"],
                  n=2000)
        hits = [r for r in rows if r['EMPFG'].strip()]
        print(f"  {bukrs} BSIK: {len(rows)} rows, {len(hits)} EMPFG hits")
        for h in hits[:3]:
            print(f"    {h['BUKRS']}/{h['BELNR']}/{h['GJAHR']} LIFNR={h['LIFNR']} EMPFG={h['EMPFG']}")
    except Exception as e:
        print(f"  {bukrs} BSIK: ERR {e}")

# ── Summary: total EMPFG hits found ─────────────────────────────────────────
total_empfg = sum(len(hits) for hits in empfg_hits.values())
print(f"\n=== SUMMARY: total BSAK EMPFG fires found = {total_empfg} ===")
if total_empfg > 0:
    # For each hit, find which DFPAYG run paid it
    print(f"\n=== Cross-ref EMPFG hits → DFPAYG to learn payment format ===")
    formi_dist = Counter()
    for bukrs, hits in empfg_hits.items():
        for h in hits[:50]:  # cap per bukrs
            try:
                rp = rd("REGUP",
                        [f"BUKRS = '{h['BUKRS']}'", f" AND BELNR = '{h['BELNR']}'", f" AND GJAHR = '{h['GJAHR']}'"],
                        ["LAUFD","LAUFI","ZBUKR"], n=5)
                for p in rp:
                    laufd, laufi, zb = p['LAUFD'].strip(), p['LAUFI'].strip(), p['ZBUKR'].strip()
                    gpg = rd("DFPAYG",
                             [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                             ["FORMI"], n=3)
                    for g in gpg:
                        formi_dist[g['FORMI'].strip()] += 1
            except Exception:
                pass
    print(f"  Format breakdown: {dict(formi_dist.most_common())}")
