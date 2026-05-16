"""REGUH.EMPFG es el alt-payee RESUELTO en proposal — fuente forensic más directa.

Cuando F110 selecciona un vendor con LFA1.LNRZA o LFB1.LNRZB, o cuando el doc
tiene BSEG.EMPFG override, F110 escribe el LIFNR resuelto en REGUH.EMPFG (junto
con REGUH.NAME1 y otros campos de address-on-record para el proposal).

Si REGUH.EMPFG está populado en CUALQUIER run de /SEPA/CGI/CITI en P01 desde 2024,
es prueba directa de alt-payee fire. Sample sin restricción de format primero.
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

# ── TEST A: probe REGUH.EMPFG existence + populated count ──
print("\n=== TEST A: REGUH.EMPFG existence + populated count (large sample) ===")
try:
    # Sample 5000 REGUH rows since 2024
    rows = rd("REGUH",
              ["LAUFD >= '20240101'", " AND XVORL = ' '"],
              ["LAUFD","LAUFI","ZBUKR","LIFNR","EMPFG"],
              n=5000)
    print(f"  Sample {len(rows)} REGUH rows since 2024")
    pop = [r for r in rows if r['EMPFG'].strip()]
    print(f"  REGUH.EMPFG populated: {len(pop)} rows")
    if pop:
        bukrs = Counter(r['ZBUKR'].strip() for r in pop)
        print(f"  Cocode distribution of EMPFG fires: {dict(bukrs.most_common())}")
        print(f"\n  First 10 fires:")
        for r in pop[:10]:
            print(f"    {r['LAUFD']}/{r['LAUFI']}/{r['ZBUKR']} LIFNR={r['LIFNR']} EMPFG={r['EMPFG']}")
except Exception as e:
    print(f"  ERR: {e}")

# ── TEST B: filter REGUH where EMPFG <> ' ' directly (might filter at SAP side)
print("\n=== TEST B: REGUH WHERE EMPFG <> ' ' directly ===")
try:
    rows = rd("REGUH",
              ["EMPFG <> ' '", " AND LAUFD >= '20240101'"],
              ["LAUFD","LAUFI","ZBUKR","LIFNR","EMPFG"],
              n=1000)
    print(f"  HITS: {len(rows)}")
    for r in rows[:20]:
        print(f"    {r['LAUFD']}/{r['LAUFI']}/{r['ZBUKR']} LIFNR={r['LIFNR']} EMPFG={r['EMPFG']}")
except Exception as e:
    print(f"  ERR: {e}")

# ── TEST C: REGUH for runs of our 3 target formats specifically ──
print("\n=== TEST C: REGUH.EMPFG for runs of /SEPA_CT_UNES, /CGI_XML_CT_UNESCO, /CITI ===")
# First get the runs from DFPAYG, then check each REGUH.EMPFG
formats = ["/SEPA_CT_UNES","/CGI_XML_CT_UNESCO","/CITI/XML/UNESCO/DC_V3_01"]
total_runs = 0
total_reguh = 0
total_empfg = 0
empfg_by_format = Counter()
for fmt in formats:
    dfpg = rd("DFPAYG",
              ["LAUFD >= '20240101'", f" AND FORMI = '{fmt}'"],
              ["LAUFD","LAUFI","ZBUKR"], n=4000)
    print(f"\n  {fmt}: {len(dfpg)} runs")
    fmt_empfg = 0
    fmt_reguh = 0
    for g in dfpg[:500]:  # cap at 500 runs per format for time
        laufd, laufi, zb = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip()
        try:
            reguh = rd("REGUH",
                       [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                       ["LIFNR","EMPFG"], n=500)
            fmt_reguh += len(reguh)
            hits = [r for r in reguh if r['EMPFG'].strip()]
            fmt_empfg += len(hits)
            if hits:
                empfg_by_format[fmt] += len(hits)
                for h in hits[:3]:
                    print(f"    ★ {laufd}/{laufi}/{zb} LIFNR={h['LIFNR']} EMPFG={h['EMPFG']}")
        except Exception:
            pass
        total_runs += 1
    total_reguh += fmt_reguh
    total_empfg += fmt_empfg
    print(f"    Runs scanned: {min(len(dfpg),500)}  REGUH rows: {fmt_reguh}  EMPFG fires: {fmt_empfg}")

print(f"\n=== TEST C SUMMARY ===")
print(f"  Total REGUH rows scanned: {total_reguh:,}")
print(f"  Total EMPFG fires: {total_empfg}")
print(f"  By format: {dict(empfg_by_format)}")
