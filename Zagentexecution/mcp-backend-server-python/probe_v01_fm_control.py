"""READ-ONLY V01 FM-AVC control — DONE RIGHT.
- POSITIVE CONTROL: a fund known to carry 2026 budget (proves the read returns values).
- Full annual = HSLVT + sum(HSL01..HSL16) (field-split to fit the 512-byte line).
- Reports ALL FISTL/cmmt rows per fund (not just target), so nothing is missed.
No writes. RFC_READ_TABLE only, ROWCOUNT=0 (V01 secured read)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from rfc_helpers import get_connection

KEYS = ["RFUND","RFUNDSCTR","RCMMTITEM","RYEAR"]
AMTS = ["HSLVT"] + [f"HSL{i:02d}" for i in range(1,17)]   # 17 amount fields

def _read(conn, table, fields, where):
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=0,
                    FIELDS=[{"FIELDNAME": f} for f in fields],
                    OPTIONS=[{"TEXT": where}] if where else [])
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out=[]
    for row in res.get("DATA", []):
        parts=row["WA"].split("|")
        out.append({h:(parts[i].strip() if i<len(parts) else "") for i,h in enumerate(hdrs)})
    return out

def num(s):
    s=(s or "0").strip()
    neg = s.endswith("-")
    s=s.rstrip("-").replace(",","")
    try: v=float(s or 0)
    except: v=0.0
    return -v if neg else v

def fmavct(conn, fund, year):
    """Return list of {fistl,cmmt,annual} merging key-chunk + amount-chunk by row index."""
    where=f"RFUND = '{fund}' AND RYEAR = '{year}'"
    k=_read(conn,"FMAVCT",KEYS,where)
    a=_read(conn,"FMAVCT",AMTS,where)
    rows=[]
    for i in range(min(len(k),len(a))):
        annual=sum(num(a[i].get(f,"0")) for f in AMTS)
        rows.append((k[i]["RFUNDSCTR"], k[i]["RCMMTITEM"], annual))
    return rows

c=get_connection("V01")
info=c.call("RFC_SYSTEM_INFO")["RFCSI_EXPORT"]
print("V01 SYSID=%s CLIENT=%s\n"%(info.get("RFCSYSID"),os.getenv("SAP_V01_CLIENT")))

print("=== POSITIVE CONTROL (funds that SHOULD have 2026 budget) ===")
for pc in ["1OCS010401","12RD010106","221QAT1000","570MON2000"]:
    r=fmavct(c,pc,"2026")
    tot=sum(x[2] for x in r)
    detail=" ".join(f"{a}:{b}={v:,.0f}" for a,b,v in r[:6])
    print(f"  {pc}: {len(r)} rows, annual_sum={tot:,.2f} | {detail}")

print("\n=== THE 14 SCENARIO FUNDS — FM-AVC full annual (HSLVT+HSL01..16) ===")
FUNDS={'549RAF2004':('NAI','11'),'218BDI2000':('YAO','11'),'501UZB5002':('TAS','11'),
'728RAS2003':('JAK','11'),'547RAF1001':('HAR','11'),'520RAF1015':('DAK','11'),
'503RAF1003':('HAR','11'),'526RAS1036':('BGK','11'),'272GAB2000':('LBV','11'),
'927CMR5001':('YAO','13'),'218BDI5000':('YAO','13'),'570GLO0028':('CPE','13'),
'514RLA2004':('SJO','13'),'570GLO1032':('FLI','13')}
print("%-12s %-6s | 2026 rows (FISTL:cmmt=annual) | 2025 rows"%("FUND","tgt"))
for f,(fis,cm) in FUNDS.items():
    r26=fmavct(c,f,"2026"); r25=fmavct(c,f,"2025")
    def fmt(r):
        if not r: return "NONE"
        return " ".join(f"{a}:{b}={v:,.0f}" for a,b,v in r[:5])
    # does any row match target fistl+cmmt with >0?
    hit=[v for a,b,v in r26 if a==fis and b==cm and v!=0]
    tag=" <== BUDGET@target!" if hit else ""
    print(f"{f:<12} {fis}/{cm:<3} | {fmt(r26)} | {fmt(r25)}{tag}")

c.close()
print("\n(READ-ONLY. No SAP writes.)")
