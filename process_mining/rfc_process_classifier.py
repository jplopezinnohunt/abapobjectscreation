"""
SYSTEM-EXPLANATION ENGINE — classify every RFC/BAPI/IDoc call into a KNOWN business process vs UNKNOWN.
The UNKNOWN bucket = the worklist of what we still have to explain; shrinking it each run = a measurable
"how much of the system do we understand" metric. Replicable process-mining method (per user 2026-06-21):
  call stream (rsau_audit_history RFC Function Call + edidc IDocs)  ->  classify  ->  coverage % + worklist.
Each classified call is an EVENT (resource = satellite/user, activity = BAPI->business-action, process = the bucket).

Run:  python process_mining/rfc_process_classifier.py
Extend: add a (process, [patterns]) row to KNOWN to explain more of the UNKNOWN tail.
"""
import sqlite3, re
from collections import defaultdict

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from gold_ref import GOLD  # T5: resolved via golden_manifest.json, not a hardcoded path

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

# Ordered: first matching pattern wins. Patterns are substrings of the FM name (upper).
KNOWN = [
    ("MDM-Vendor",      ["VENDOR", "KRED", "LFA1", "CREDITOR"]),
    ("MDM-GL/CostElem", ["GL_ACC", "GLACCOUNT", "SAKO", "COSTELEMENT", "CSKB"]),
    ("MDM-Customer",    ["CUSTOMER", "DEBTOR", "KNA1", "DEBMAS"]),
    ("MDM-Bank",        ["_BANK_", "BANK_COUNTRY", "HOUSE_BANK", "BNKA"]),
    ("Travel",          ["YHRTRV", "TRIP", "TRAVEL", "PTRV", "FITV"]),
    ("HCM",             ["HR_", "RHAK", "PA00", "INFOTYPE", "PAYROLL", "PERNR", "HRFPM", "PBC", "ZHRCA", "POSTAL"]),
    ("PSM-Budget/FM",   ["FUND", "FMKU", "BCS", "FMRESERV", "FMFCTR", "YEBU", "FMSU", "FM5", "RFFMEP", "FMRP"]),
    ("PS-Project",      ["WBS", "PROJECT", "PRPS", "PROJ", "YPS"]),  # YPS8 = MuleSoft project-financials sync
    ("P2P-PR",          ["REQUISITION", "BAPI_PR_", "_PR_CREATE", "_PR_CHANGE"]),
    ("P2P-PO",          ["BAPI_PO_", "_PO_CREATE", "_PO_CHANGE", "_PO_GET"]),
    ("P2P-Service",     ["ENTRYSHEET"]),
    ("P2P-GR",          ["GOODSMVT", "GOODSRECEIPT"]),
    ("P2P-Invoice",     ["INCOMINGINVOICE", "INVOICE_CREATE"]),
    ("Payment/Bank",    ["PAYMENT", "F110", "PAYR", "DMEE", "FEB", "BNK_"]),
    ("FI-Posting",      ["ACC_DOCUMENT", "ACC_GL", "FI_DOCUMENT", "BKPF", "ACGL"]),
    ("Identity/Role",   ["GET_USER", "Z_RFC_GET_USER", "ROLE", "AGR_", "USER_"]),
]
OURS = ["RFC_READ_TABLE", "DDIF_", "RFC_ABAP_INSTALL", "DD_DOMA", "RSAU_API", "RFC_GET_FUNCTION_INTERFACE"]
TECH = ["RFCPING", "RFC_PING", "SYSTEM_INFO", "/SDF/", "SALC", "AMDP", "ENQ_CTX", "ARFC_", "ICM_", "TH_",
        "SXMI", "FUNCTION_EXISTS", "SAPGUI_CHECK", "LOGICAL_SYSTEM", "PROGRESS_INDICATOR", "TMS_", "DETERMINE",
        "TRANSACTION_COMMIT", "TRINT_TP", "RODPS", "RSBATCH", "LOGWRITER", "GET_UNICODE", "CALL_SUBROUTINE",
        "ABAP4_CALL_TRANSACTION", "MESSAGE_GETDETAIL", "OBJECTS_SEND", "/SSF/", "RSPO_", "BAPI_MESSAGE"]
OUR_USERS = {"JP_LOPEZ", "P_LUVHIMBI"}


# ORIGIN axis (host/dest/user) — WHO/WHICH SYSTEM makes the call. As important as the FM:
# the same BAPI from MULESOFT (external satellite) vs an internal report are different things.
SATELLITES = {"MULESOFT": "MuleSoft (external bus)", "BRIDGE-RFC": "BRIDGE-RFC (external portal)",
              "SMTMSBP": "SolMan (external monitor)"}
INTERNAL_BATCH = {"JOBBATCH", "WF-BATCH", "SAPSYS", "HIPER", "WF-BATCH", "TMSADM", "DDIC"}


def classify_origin(user):
    if user in OUR_USERS: return "us (JP_LOPEZ extraction)"
    if user in SATELLITES: return SATELLITES[user]
    if user in INTERNAL_BATCH: return "internal batch/system"
    return "named user (dialog/portal-as-user)"


def classify(fm, user):
    f = (fm or "").upper()
    if user in OUR_USERS and any(p in f for p in OURS): return ("_ours", "_ours")
    if any(p in f for p in OURS): return ("_ours", "_ours")
    if any(p in f for p in TECH): return ("_technical", "_technical")
    for proc, pats in KNOWN:
        if any(p in f for p in pats): return ("KNOWN", proc)
    return ("UNKNOWN", "UNKNOWN")


def main():
    c = sqlite3.connect(GOLD, timeout=10)
    rows = c.execute("SELECT PARAM3, SLGUSER, COUNT(*) FROM rsau_audit_history "
                     "WHERE TXSUBCLSID='RFC Function Call' AND PARAM3<>'' GROUP BY PARAM3, SLGUSER").fetchall()
    bucket = defaultdict(int); proc_vol = defaultdict(int); unknown = defaultdict(int); unk_user = defaultdict(set)
    origin_vol = defaultdict(int); origin_unknown = defaultdict(int)
    for fm, user, n in rows:
        b, proc = classify(fm, user)
        bucket[b] += n
        if b in ("KNOWN", "UNKNOWN"):
            o = classify_origin(user); origin_vol[o] += n
            if b == "UNKNOWN": origin_unknown[o] += n
        if b == "KNOWN": proc_vol[proc] += n
        elif b == "UNKNOWN": unknown[fm] += n; unk_user[fm].add(user)
    business = bucket["KNOWN"] + bucket["UNKNOWN"]
    total = sum(bucket.values())
    print("=== RFC/BAPI call classification (rsau_audit_history) ===")
    print(f"  total RFC calls: {total:,}  |  ours: {bucket['_ours']:,}  technical: {bucket['_technical']:,}")
    print(f"  BUSINESS calls: {business:,}  ->  KNOWN {bucket['KNOWN']:,} / UNKNOWN {bucket['UNKNOWN']:,}")
    cov = 100 * bucket["KNOWN"] / business if business else 0
    print(f"  *** SYSTEM-EXPLANATION COVERAGE: {cov:.1f}% of business calls mapped to a known process ***\n")
    print("  KNOWN business volume by process:")
    for p, n in sorted(proc_vol.items(), key=lambda x: -x[1]):
        print(f"    {n:>9,}  {p}")
    print("\n  UNKNOWN worklist (top — explain these next, biggest first):")
    for fm, n in sorted(unknown.items(), key=lambda x: -x[1])[:15]:
        print(f"    {n:>8,}  {fm:38} ({len(unk_user[fm])} callers)")

    print("\n  BUSINESS calls by ORIGIN (host/dest/user) — the satellite topology:")
    sat = 0
    for o, n in sorted(origin_vol.items(), key=lambda x: -x[1]):
        unk = origin_unknown.get(o, 0)
        if "external" in o: sat += n
        print(f"    {n:>9,}  {o:36} ({unk:,} process still UNKNOWN)")
    print(f"  *** {100*sat/business:.1f}% of business RFC is driven by EXTERNAL satellites "
          f"(MuleSoft + BRIDGE-RFC) — the system is operated from outside ***")

    # IDoc layer (edidc) — same known/unknown idea on message types
    tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "edidc" in tabs:
        cols = {x[1].upper() for x in c.execute("PRAGMA table_info(edidc)")}
        mt = "MESTYP" if "MESTYP" in cols else None
        if mt:
            print("\n=== IDoc layer (edidc) by message type ===")
            for m, n in c.execute(f"SELECT {mt}, COUNT(*) FROM edidc WHERE {mt}<>'' GROUP BY {mt} ORDER BY COUNT(*) DESC LIMIT 12"):
                print(f"    {n:>7,}  {m}")


if __name__ == "__main__":
    main()
