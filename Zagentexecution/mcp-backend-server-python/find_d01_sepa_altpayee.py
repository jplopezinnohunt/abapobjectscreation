"""Hunt for any /SEPA_CT_UNES alt-payee case in D01.

Levels of alt-payee:
  1. LFA1.LNRZA — vendor-level (any cocode)
  2. LFB1.LNRZB — cocode-level (overrides LFA1)
  3. BSEG.EMPFB / BSEC.EMPFG — document-level (overrides everything)
  4. REGUH.LNRZB? (resolved alt-payee in payment proposal)

For each level, check whether the firing vendor maps to /SEPA_CT_UNES UNES.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
params = dict(
    ashost=os.getenv("SAP_ASHOST"), sysnr=os.getenv("SAP_SYSNR"),
    client=os.getenv("SAP_CLIENT"), user=os.getenv("SAP_USER"),
    lang="EN", snc_mode="1",
    snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"), snc_qop="9",
)
conn = Connection(**params)

def rd(t, opts, fields, n=200):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t,
                  OPTIONS=[{"TEXT": x} for x in opts],
                  FIELDS=[{"FIELDNAME": x} for x in fields],
                  DELIMITER="|", ROWCOUNT=n)
    cols = [f["FIELDNAME"] for f in r.get("FIELDS",[])] or fields
    return [dict(zip(cols, d["WA"].split("|"))) for d in r.get("DATA", [])]

# ── 1. LFA1.LNRZA — vendor-level alt-payee in D01 ────────────────────────────
print("=== D01 LFA1.LNRZA populated (vendor-level alt-payee) ===")
try:
    rows = rd("LFA1",
              ["LNRZA <> ' '"],
              ["LIFNR","NAME1","KTOKK","LNRZA","LOEVM"], n=200)
    active = [r for r in rows if r["LOEVM"].strip() != "X"]
    print(f"  {len(active)} active rows")
    for r in active[:30]:
        print(f"  {r['LIFNR']} {r['KTOKK']} {r['NAME1'].strip()[:30]:30s} → LNRZA={r['LNRZA'].strip()}")
except Exception as e:
    print(f"  ERR {e}")

# ── 2. LFB1.LNRZB — cocode-level for UNES ────────────────────────────────────
print("\n=== D01 LFB1.LNRZB populated for cocode UNES ===")
try:
    rows = rd("LFB1",
              ["BUKRS = 'UNES'", " AND LNRZB <> ' '"],
              ["LIFNR","BUKRS","LNRZB","LOEVM"], n=200)
    active = [r for r in rows if r["LOEVM"].strip() != "X"]
    print(f"  {len(active)} active rows")
    for r in active[:30]:
        print(f"  LIFNR={r['LIFNR']} BUKRS={r['BUKRS']} LNRZB={r['LNRZB'].strip()}")
except Exception as e:
    print(f"  ERR {e}")

# ── 3. LFB1.LNRZB for ANY cocode ─────────────────────────────────────────────
print("\n=== D01 LFB1.LNRZB populated for ANY cocode ===")
try:
    rows = rd("LFB1",
              ["LNRZB <> ' '"],
              ["LIFNR","BUKRS","LNRZB","LOEVM"], n=200)
    active = [r for r in rows if r["LOEVM"].strip() != "X"]
    print(f"  {len(active)} active rows")
    for r in active[:20]:
        print(f"  LIFNR={r['LIFNR']} BUKRS={r['BUKRS']} LNRZB={r['LNRZB'].strip()}")
except Exception as e:
    print(f"  ERR {e}")

# ── 4. REGUH.EMPFG or similar resolved alt-payee field (if exists in REGUH) ──
print("\n=== D01 REGUH fields related to alt-payee ===")
# REGUH-EMPFG would be the resolved alt-payee. Test field existence.
try:
    rows = rd("REGUH",
              ["LAUFD >= '20240101'", " AND XVORL = ' '"],
              ["LAUFD","LAUFI","LIFNR","EMPFG"], n=20)
    flagged = [r for r in rows if r["EMPFG"].strip()]
    print(f"  {len(rows)} REGUH rows sampled, {len(flagged)} have EMPFG populated")
    for r in flagged[:10]:
        print(f"  {r['LAUFD']}/{r['LAUFI']} LIFNR={r['LIFNR']} EMPFG={r['EMPFG'].strip()}")
except Exception as e:
    print(f"  EMPFG read err: {e}")
