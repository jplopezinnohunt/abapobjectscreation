"""
probe_v01_citi_rerun.py
=======================
Identify, in system V01, the PROCESS that produces the Citi DMEE file for tree
'/CITI/XML/UNESCO/DC_V3_01', so it can be re-run.

READ-ONLY (RFC_READ_TABLE). Does NOT execute F110 / SAPFPAYM / any job.

What it gathers:
  0) Connectivity + which system/client we actually reached (T000)
  1) Does V01 have the CITI tree? active version (DMEE_TREE_HEAD)
  2) Format properties / which DMEE tree the PMW format points to (TFPM042F)
  3) Recent CITI payment GROUPS in V01 (DFPAYG WHERE FORMI = tree) -> which runs used it
  4) Run status for those runs (REGUV) -> is the medium already created? re-runnable?
  5) Scheduled jobs running the medium driver (TBTCP PROGNAME = SAPFPAYM / ZWFPAYM_RUN -> TBTCO)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

TREE = "/CITI/XML/UNESCO/DC_V3_01"
SYSTEM = "V01"


def read(c, table, where, fields, rowcount=0):
    opts = [{"TEXT": where}] if where else []
    kw = dict(QUERY_TABLE=table, OPTIONS=opts,
              FIELDS=[{"FIELDNAME": f} for f in fields])
    if rowcount:
        kw["ROWCOUNT"] = rowcount
    r = c.call("RFC_READ_TABLE", **kw)
    return [row["WA"] for row in r.get("DATA", [])]


def section(title):
    print(f"\n{'='*72}\n=== {title}\n{'='*72}")


print(f"\n########## PROBE V01 — CITI re-run process ({TREE}) ##########")
try:
    c = get_connection(SYSTEM)
except Exception as e:
    print(f"  CONN FAIL to {SYSTEM}: {e}")
    sys.exit(1)
print(f"  Connected to {SYSTEM}.")

# 0) which system/client did we actually reach
section("0) T000 — system/client reached (sanity)")
try:
    for w in read(c, "T000", "", ["MANDT", "MTEXT", "ORT01", "MWAER"], rowcount=20):
        print(f"  {w}")
except Exception as e:
    print(f"  T000 ERROR: {e}")

# 1) CITI tree present + active version in V01
section("1) DMEE_TREE_HEAD — CITI tree active version in V01")
try:
    rows = read(c, "DMEE_TREE_HEAD", f"TREE_ID = '{TREE}'",
                ["TREE_ID", "VERSION", "EX_STATUS", "FIRSTNODE_ID",
                 "PARAM_STRUC", "XSLTDESC"])
    if not rows:
        print("  NO ROW — CITI tree does NOT exist in V01")
    for w in rows:
        print(f"  {w}")
    # node count per version
    for ver in ("000", "001"):
        n = read(c, "DMEE_TREE_NODE", f"TREE_ID = '{TREE}' AND VERSION = '{ver}'",
                 ["NODE_ID"])
        print(f"  node count VERSION={ver}: {len(n)}")
except Exception as e:
    print(f"  DMEE_TREE_HEAD ERROR: {e}")

# 2) PMW format properties — TFPM042F (format -> tree, is-DMEE flag)
section("2) TFPM042F — PMW format properties for the CITI format")
try:
    rows = read(c, "TFPM042F", f"FORMI = '{TREE}'",
                ["FORMI", "FORMT", "DTTYP", "FORMTREE", "XDME1", "XLST1"])
    if not rows:
        print("  NO ROW for FORMI = tree (format id may differ from tree id)")
    for w in rows:
        print(f"  {w}")
except Exception as e:
    print(f"  TFPM042F ERROR: {e}")

# 2b) Event 05 / variant registrations
section("2b) TFPM042FB — Event-05 / FM registrations for the CITI format")
try:
    rows = read(c, "TFPM042FB", f"FORMI = '{TREE}'",
                ["FORMI", "EVENT", "FNAME", "ROUTINE"], rowcount=50)
    if not rows:
        print("  NO ROW (no event registrations under this FORMI key)")
    for w in rows:
        print(f"  {w}")
except Exception as e:
    print(f"  TFPM042FB ERROR: {e}")

# 3) Recent CITI payment groups in V01 — which runs used this tree
section("3) DFPAYG — payment groups using the CITI tree (which runs to re-run)")
try:
    rows = read(c, "DFPAYG", f"FORMI = '{TREE}'",
                ["LAUFD", "LAUFI", "GRPNO", "ZBUKR", "HBKID", "RZAWE",
                 "ANZ_ERZ", "ANZ_ERL"], rowcount=40)
    if not rows:
        print("  NO ROW — no payment groups with this FORMI in V01")
    for w in rows:
        print(f"  {w}")
except Exception as e:
    print(f"  DFPAYG ERROR: {e}")

# 5) Scheduled jobs that run the medium driver
section("5) TBTCP/TBTCO — jobs running SAPFPAYM or ZWFPAYM_RUN")
for prog in ("SAPFPAYM", "ZWFPAYM_RUN"):
    print(f"\n  --- PROGNAME = {prog} ---")
    try:
        rows = read(c, "TBTCP", f"PROGNAME = '{prog}'",
                    ["JOBNAME", "JOBCOUNT", "PROGNAME", "VARIANT"], rowcount=25)
        if not rows:
            print(f"    NO step rows for {prog}")
        for w in rows:
            print(f"    {w}")
    except Exception as e:
        print(f"    TBTCP ERROR: {e}")

c.close()
print("\n########## DONE ##########")
