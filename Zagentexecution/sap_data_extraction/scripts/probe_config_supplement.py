"""
probe_config_supplement.py
==========================
Bounded follow-up probes to make the hypothesis verdicts airtight:
  - FM-AVC tolerance-LIMIT table (the 50%/100% + action W/E/A) — FMUP* held the
    control flags but not the usage-rate limits; find where those live.
  - Derivation STEP master for strategy FMOA (the "26 steps" claim, CLM-036).
  - GM grants count (GMGR) to characterise GMDERIVE (HYP-018).
Any newly-found POPULATED table is extracted into the golden DB.
"""
import os, sys, sqlite3
MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection, rfc_read_paginated

GOLD_DB = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"

conn = get_connection("P01")

def dd02l(like):
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE="DD02L", DELIMITER="|", ROWCOUNT=0,
                    OPTIONS=[{"TEXT": f"TABNAME LIKE '{like}' AND AS4LOCAL = 'A' AND TABCLASS = 'TRANSP'"}],
                    FIELDS=[{"FIELDNAME": "TABNAME"}])
    return [r["WA"].split("|")[0].strip() for r in res.get("DATA", [])]

def count_and_peek(table, fields=None, where=""):
    try:
        f = [{"FIELDNAME": x} for x in (fields or [])]
        opt = [{"TEXT": where}] if where else []
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        ROWCOUNT=5, OPTIONS=opt, FIELDS=f)
        hdr = [x["FIELDNAME"] for x in res["FIELDS"]]
        rows = res["DATA"]
        return hdr, [r["WA"] for r in rows]
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e).splitlines()[0]}"

print("="*70)
print("AVC tolerance-LIMIT table search (50%/100% usage + action)")
print("="*70)
cand = set()
for pat in ("FM%TOL%", "FMUPL%", "FM%LIMIT%", "FMACG%", "FMAVC%", "BPTR%", "%AVCTOL%", "FMUP%"):
    for t in dd02l(pat):
        cand.add(t)
print("candidate tables:", sorted(cand))
for t in sorted(cand):
    hdr, rows = count_and_peek(t)
    if hdr is None:
        print(f"  {t}: {rows}")
    else:
        print(f"  {t}: cols={hdr}")
        for r in rows[:3]:
            print(f"      {r}")

print("\n"+"="*70)
print("Derivation STEP master search (FMOA strategy, '26 steps')")
print("="*70)
cand2 = set()
for pat in ("%ADRDEF%", "TABADR%", "RWIN", "%DERIVE%STEP%", "TFM%DERIV%", "ABDR%", "FMDERIVE%"):
    for t in dd02l(pat):
        cand2.add(t)
print("candidate tables:", sorted(cand2))
# The generic derivation tool keeps step headers in ADRDEF / TABADR* ; peek
for t in sorted(cand2):
    hdr, rows = count_and_peek(t)
    if hdr and any(c in hdr for c in ("STRATEGY_ID", "ABLNR", "STEP", "ABADRSTRATID", "STRATEGYID")):
        print(f"  {t}: cols={hdr}")
        for r in rows[:3]:
            print(f"      {r}")

# Count steps for FMOA in the most likely step header (ABADRDEF / TABADR06 etc.)
for stepmaster in ("ABADRDEF", "TABADR06", "TABADR05", "TABADR07"):
    hdr, rows = count_and_peek(stepmaster, ["ABADRSTRATID", "ABLNR", "ABNAME"], "ABADRSTRATID = 'FMOA'")
    if hdr:
        print(f"\n  STEP MASTER {stepmaster} (FMOA): cols={hdr}, sample={rows}")

print("\n"+"="*70)
print("GM grants count (HYP-018)")
print("="*70)
for t in ("GMGR", "GMIA", "GMDS_FUND", "GMGRANTD"):
    hdr, rows = count_and_peek(t, [])
    print(f"  {t}: {'rows='+str(len(rows)) if hdr else rows}")

conn.close()
print("\nDone (supplementary probe — no persistence unless a populated AVC-limit table is found).")
