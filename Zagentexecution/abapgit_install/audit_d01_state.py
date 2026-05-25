"""READ-ONLY full audit of everything touched on D01 today (2026-05-25) by user JP_LOPEZ.
Goal: find ANY half-baked / inactive / orphaned object that the Pull crash may have left.
Touches NOTHING. Pure SELECT.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + r"\..\mcp-backend-server-python")
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-backend-server-python", ".env"))
from pyrfc import Connection

p = {"ashost": os.getenv("SAP_ASHOST"), "sysnr": os.getenv("SAP_SYSNR"),
     "client": os.getenv("SAP_CLIENT"), "user": os.getenv("SAP_USER"),
     "passwd": os.getenv("SAP_PASSWD"), "lang": "EN"}
conn = Connection(**p)

TODAY = "20260525"

print("=" * 80)
print("AUDIT — everything touched on D01 by JP_LOPEZ on 2026-05-25")
print("=" * 80)

# 1. ALL TADIR rows created today by JP_LOPEZ
print("\n[1] ALL TADIR rows AUTHOR=JP_LOPEZ AND CREATED_ON=20260525:")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
              OPTIONS=[{"TEXT": f"AUTHOR = 'JP_LOPEZ' AND CREATED_ON = '{TODAY}'"}],
              FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                      {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                      {"FIELDNAME": "EDTFLAG"}, {"FIELDNAME": "GENFLAG"},
                      {"FIELDNAME": "DELFLAG"}],
              ROWCOUNT=200)
rows = r.get("DATA", [])
print(f"  Total rows: {len(rows)}")
for row in rows:
    print(f"  {row['WA']}")

# 2. ALL packages in $DEV_ABAPGIT family
print(f"\n[2] Packages whose name contains DEV_ABAPGIT or ABAPGIT:")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TDEVC", DELIMITER="|",
              OPTIONS=[{"TEXT": "DEVCLASS LIKE '%ABAPGIT%'"}],
              FIELDS=[{"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AS4USER"},
                      {"FIELDNAME": "PDEVCLASS"}, {"FIELDNAME": "AS4DATE"}],
              ROWCOUNT=30)
rows = r.get("DATA", [])
print(f"  Total: {len(rows)}")
for row in rows:
    print(f"  {row['WA']}")

# 3. Inactive REPOSRC rows by JP_LOPEZ today
print(f"\n[3] Inactive REPOSRC rows by JP_LOPEZ today (orphan inactive shells):")
abap = [
    {"LINE": "REPORT zaudit_inactive."},
    {"LINE": "DATA: lt_r TYPE TABLE OF reposrc."},
    {"LINE": "SELECT progname r3state cnam unam udat utime"},
    {"LINE": "  FROM reposrc INTO TABLE @DATA(lt2)"},
    {"LINE": f"  WHERE ( cnam = 'JP_LOPEZ' OR unam = 'JP_LOPEZ' )"},
    {"LINE": f"    AND ( cdat = '{TODAY}' OR udat = '{TODAY}' )"},
    {"LINE": "  ORDER BY progname r3state."},
    {"LINE": "DATA(lv_n) = lines( lt2 )."},
    {"LINE": "WRITE: / 'REPOSRC rows touched today by JP_LOPEZ:', lv_n."},
    {"LINE": "LOOP AT lt2 ASSIGNING FIELD-SYMBOL(<r>)."},
    {"LINE": "  WRITE: / <r>-progname, 'R3=', <r>-r3state, 'CN=', <r>-cnam,"},
    {"LINE": "           'UN=', <r>-unam, 'UD=', <r>-udat, 'UT=', <r>-utime."},
    {"LINE": "ENDLOOP."},
]
r = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap, MODE="F")
for w in r.get("WRITES", []):
    print(f"  {w.get('ZEILE', dict(w))}")
if r.get("ERRORMESSAGE"):
    print(f"  ERROR: {r['ERRORMESSAGE']}")

# 4. Outstanding enqueue locks
print(f"\n[4] Outstanding enqueue locks held by JP_LOPEZ:")
try:
    r = conn.call("ENQUE_READ", GUNAME="JP_LOPEZ", GCLIENT="350")
    locks = r.get("ENQ", [])
    print(f"  Locks held: {len(locks)}")
    for lk in locks[:20]:
        print(f"  {dict(lk)}")
except Exception as e:
    # Fallback: read SM12-equivalent
    print(f"  ENQUE_READ not available ({e}); skipping lock check")

# 5. TBTCO background jobs JP_LOPEZ today
print(f"\n[5] Background jobs queued by JP_LOPEZ today:")
r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TBTCO", DELIMITER="|",
              OPTIONS=[{"TEXT": f"AUTHCKMAN = 'JP_LOPEZ' AND SDLDATE = '{TODAY}'"}],
              FIELDS=[{"FIELDNAME": "JOBNAME"}, {"FIELDNAME": "STATUS"},
                      {"FIELDNAME": "SDLSTRTDT"}, {"FIELDNAME": "SDLSTRTTM"}],
              ROWCOUNT=20)
rows = r.get("DATA", [])
print(f"  Jobs: {len(rows)}")
for row in rows:
    print(f"  {row['WA']}")

conn.close()
print()
print("=" * 80)
print("Audit complete. READ-ONLY — nothing modified.")
print("=" * 80)
