"""Read LIVE P01 TBTCO scheduling definition for the cost-per-output Data Hub jobs.
Goal: determine the SCHEDULED cadence (periodic flag + period fields + event binding),
which is authoritative regardless of run-history retention. READ-ONLY (RFC_READ_TABLE).
"""
import os, sys
MCP_DIR = os.path.join(r"c:\Users\jp_lopez\projects\abapobjectscreation",
                       "Zagentexecution", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection
from pyrfc import RFCError

FIELDS = ["JOBNAME","JOBCOUNT","STATUS","PERIODIC","PRDMINS","PRDHOURS","PRDDAYS",
          "PRDWEEKS","PRDMONTHS","CALENDARID","EVENTID","EVENTPARM",
          "SDLSTRTDT","SDLSTRTTM","STRTDATE","ENDDATE"]
# job families: staff cost + indirect cost data-hub extracts (cost-per-output)
WHERES = [
    "JOBNAME LIKE 'YFM_STAFF_COST%DATA%HUB%'",
    "JOBNAME LIKE 'YFM_IND_COST_DATA_HUB%'",
    "JOBNAME LIKE 'YFM_STAFF_COST_FOR_DATA_HUB%'",
]

def read(conn, where):
    opts = [{"TEXT": where}]
    flds = [{"FIELDNAME": f} for f in FIELDS]
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TBTCO", DELIMITER="|",
                  OPTIONS=opts, FIELDS=flds, ROWCOUNT=0)
    names = [f["FIELDNAME"] for f in r["FIELDS"]]
    rows = []
    for d in r["DATA"]:
        vals = d["WA"].split("|")
        rows.append(dict(zip(names, [v.strip() for v in vals])))
    return rows

def main():
    try:
        conn = get_connection()
    except Exception as e:
        print("CONNECT_FAILED:", type(e).__name__, str(e)[:300]); return 2
    print("CONNECTED to P01.\n")
    allrows = []
    for w in WHERES:
        try:
            rows = read(conn, w)
            allrows += rows
            print(f"[{w}] -> {len(rows)} rows")
        except RFCError as e:
            print(f"[{w}] RFC_ERROR: {str(e)[:200]}")
    print("\n=== distinct jobs: status / periodic / period / event ===")
    seen=set()
    for r in sorted(allrows, key=lambda x:(x.get("JOBNAME",""), x.get("SDLSTRTDT",""))):
        key=(r.get("JOBNAME"), r.get("STATUS"), r.get("PERIODIC"), r.get("PRDMONTHS"),
             r.get("PRDWEEKS"), r.get("PRDDAYS"), r.get("EVENTID"), r.get("SDLSTRTDT"))
        if key in seen: continue
        seen.add(key)
        print(f"  {r.get('JOBNAME'):34} st={r.get('STATUS')} per={r.get('PERIODIC')} "
              f"M/W/D={r.get('PRDMONTHS')}/{r.get('PRDWEEKS')}/{r.get('PRDDAYS')} "
              f"cal={r.get('CALENDARID')} ev={r.get('EVENTID')!r} sdl={r.get('SDLSTRTDT')} strt={r.get('STRTDATE')}")
    # released/scheduled (status S/Y) = standing recurring definition
    sched=[r for r in allrows if r.get("STATUS") in ("S","Y","R")]
    print(f"\n=== RELEASED/SCHEDULED instances (status S/Y/R) = the standing recurrence: {len(sched)} ===")
    for r in sched:
        print(f"  {r.get('JOBNAME'):34} st={r.get('STATUS')} per={r.get('PERIODIC')} "
              f"M/W/D={r.get('PRDMONTHS')}/{r.get('PRDWEEKS')}/{r.get('PRDDAYS')} ev={r.get('EVENTID')!r} sdl={r.get('SDLSTRTDT')}")
    print(f"\nTOTAL rows pulled: {len(allrows)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
