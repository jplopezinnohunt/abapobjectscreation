"""READ-ONLY: compare Fund master (FMFINCODE) 633CRP* between P01 (PRD) and V01.
Key = FIKRS+FINCODE. Validity = DATAB (valid-from) / DATBIS (valid-to).
Also compares TYPE, FINUSE, PROFIL, DECKUNG, DATE_EXP, DATE_CAN.
No writes. RFC_READ_TABLE ROWCOUNT=0 single-call (secured wrapper rejects ROWSKIPS)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from rfc_helpers import get_connection

FIELDS = ["FIKRS","FINCODE","DATAB","DATBIS","TYPE","FINUSE","PROFIL","DECKUNG","DATE_EXP","DATE_CAN"]
WHERE  = "FINCODE LIKE '633CRP%'"

def read_funds(sysid):
    c = get_connection(sysid)
    info = c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
    res = c.call("RFC_READ_TABLE", QUERY_TABLE="FMFINCODE", DELIMITER="|", ROWCOUNT=0,
                 FIELDS=[{"FIELDNAME": f} for f in FIELDS], OPTIONS=[{"TEXT": WHERE}])
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = {}
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        d = {h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)}
        out[(d["FIKRS"], d["FINCODE"])] = d
    c.close()
    print(f"  {sysid}: SYSID={info.get('RFCSYSID')} CLIENT={os.getenv('SAP_'+sysid+'_CLIENT')} -> {len(out)} funds 633CRP*")
    return out

print("=== Reading FMFINCODE 633CRP* from both systems (READ-ONLY) ===")
p01 = read_funds("P01")
v01 = read_funds("V01")

keys = sorted(set(p01) | set(v01))
print(f"\n=== COMPARISON ({len(keys)} distinct FIKRS+FINCODE) ===")
print("%-6s %-12s | %-8s %-8s | %-4s %-5s | %s" % ("FIKRS","FINCODE","DATAB","DATBIS","TYPE","FINUSE","VERDICT"))
same = diff = onlyp = onlyv = 0
diffs = []
for k in keys:
    a, b = p01.get(k), v01.get(k)
    fik, fin = k
    if a and not b:
        onlyp += 1; print("%-6s %-12s | ONLY IN P01 (missing in V01)" % (fik, fin)); continue
    if b and not a:
        onlyv += 1; print("%-6s %-12s | ONLY IN V01 (missing in P01)" % (fik, fin)); continue
    mism = [f for f in FIELDS if a.get(f) != b.get(f)]
    if mism:
        diff += 1
        print("%-6s %-12s | %-8s %-8s | %-4s %-5s | DIFF: %s" % (
            fik, fin, a["DATAB"], a["DATBIS"], a["TYPE"], a["FINUSE"],
            ", ".join(f"{f}(P01={a.get(f)!r} V01={b.get(f)!r})" for f in mism)))
        diffs.append((k, mism, a, b))
    else:
        same += 1
        print("%-6s %-12s | %-8s %-8s | %-4s %-5s | SAME" % (
            fik, fin, a["DATAB"], a["DATBIS"], a["TYPE"], a["FINUSE"]))

print(f"\nSUMMARY: {same} identical | {diff} differ | {onlyp} only-P01 | {onlyv} only-V01")
print("(READ-ONLY. No SAP writes.)")
