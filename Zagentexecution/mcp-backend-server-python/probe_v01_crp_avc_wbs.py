"""READ-ONLY live V01 check for the CRP re-anchored scenario (14 funds).
FMAVCT (FM AVC totals) rows per fund for 2026 & 2025 (all FISTL/cmmt shown),
+ WBS master (PRPS) release/acct-assign + PS budget (BPJA) on the WBS element.
No writes. RFC_READ_TABLE only (ROWSKIPS-free, ROWCOUNT=0 per V01 secured read)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from rfc_helpers import get_connection

FUNDS = {
 '549RAF2004':('NAI','11'),'218BDI2000':('YAO','11'),'501UZB5002':('TAS','11'),
 '728RAS2003':('JAK','11'),'547RAF1001':('HAR','11'),'520RAF1015':('DAK','11'),
 '503RAF1003':('HAR','11'),'526RAS1036':('BGK','11'),'272GAB2000':('LBV','11'),
 '927CMR5001':('YAO','13'),'218BDI5000':('YAO','13'),'570GLO0028':('CPE','13'),
 '514RLA2004':('SJO','13'),'570GLO1032':('FLI','13'),
}

def _read(conn, table, fields, where):
    opts = [{"TEXT": where}] if where else []
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=0, FIELDS=[{"FIELDNAME": f} for f in fields],
                    OPTIONS=opts)
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return out

def safe(conn, table, fields, where):
    try:
        return _read(conn, table, fields, where), ""
    except Exception as e:
        m = str(e).splitlines()[0][:70]
        if "TABLE_WITHOUT_DATA" in str(e):
            return [], ""   # no rows / field maps to nothing
        return None, m

c = get_connection("V01")
info = c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
print("Connected V01: SYSID=%s HOST=%s CLIENT=%s\n" % (
    info.get("RFCSYSID"), info.get("RFCHOST"), os.getenv("SAP_V01_CLIENT")))

print("=== FMAVCT (AVC totals) — ALL rows per fund, target cmmt in [] ===")
print("%-12s %-4s | %-30s | %-30s" % ("FUND","tgt","2026 (FISTL:cmmt=HSLVT)","2025 (FISTL:cmmt=HSLVT)"))
FF = ["RFUND","RFUNDSCTR","RCMMTITEM","RYEAR","HSLVT"]
for fund,(fis,cm) in FUNDS.items():
    def dump(year):
        rows,err = safe(c,"FMAVCT",FF,f"RFUND = '{fund}' AND RYEAR = '{year}'")
        if err: return "ERR:"+err
        if not rows: return "NONE"
        return " ".join(f"{r['RFUNDSCTR']}:{r['RCMMTITEM']}={r['HSLVT']}" for r in rows[:5])
    print("%-12s %-4s | %-30s | %-30s" % (fund,f"{fis}/{cm}",dump('2026'),dump('2025')))

print("\n=== WBS master (PRPS) + REL status + PS budget (BPJA, WRTTP any) ===")
print("%-12s | acct/plan/del | REL? | BPJA 2026            | BPJA 2025" % "WBS(=fund)")
for fund in FUNDS:
    p,err = safe(c,"PRPS",["POSID","OBJNR","BELKZ","PLAKZ","LOEVM"],f"POSID = '{fund}'")
    if err: print("%-12s | PRPS ERR %s"%(fund,err)); continue
    if not p: print("%-12s | NOT IN PRPS"%fund); continue
    o=p[0]; objnr=o["OBJNR"]
    j,_ = safe(c,"JEST",["OBJNR","STAT","INACT"],f"OBJNR = '{objnr}' AND STAT = 'I0002'")
    rel = "YES" if j and any(x["INACT"]=="" for x in j) else "no"
    def bp(year):
        b,e2 = safe(c,"BPJA",["OBJNR","WRTTP","GJAHR","WTJHR"],f"OBJNR = '{objnr}' AND GJAHR = '{year}'")
        if e2: return "ERR"
        if not b: return "none"
        return ",".join(f"{x['WRTTP']}={x['WTJHR']}" for x in b[:4])
    print("%-12s | %s/%s/%s       | %-4s | %-19s | %s" % (
        fund,o["BELKZ"] or '_',o["PLAKZ"] or '_',o["LOEVM"] or '_',rel,bp('2026'),bp('2025')))

c.close()
print("\n(READ-ONLY. No SAP writes.)")
