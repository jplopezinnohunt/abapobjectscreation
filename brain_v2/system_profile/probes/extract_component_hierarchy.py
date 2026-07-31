"""extract_component_hierarchy.py — METHOD M2, promoted to a product tool (s097).

Resolves ANY SAP object to its APPLICATION COMPONENT using the system's own taxonomy:

    object --TADIR--> package --TDEVC--> component id --DF14L--> component (e.g. FI-AA-AA)

This is the deterministic rung of the bottom-up ascent. It replaces guessing a module
from a package name with asking SAP what the object actually belongs to. The finding
that justified building it: PBC resolves to PA-PM-PB — Personnel Management, not PSM —
which is precisely why an FM-shaped search never found the tenant's largest
staff-budget capability.

Writes two durable Gold DB tables:
    df14l      component id -> component string   (~2,687 rows)
    tadir_obj  object       -> package, by type   (~311K rows)

THREE NON-OBVIOUS CONSTRAINTS, each of which silently returned zero rows before being
understood. They are documented here so the next session does not rediscover them:

  1. DF14L has NO field PARENT_ID. Asking for it makes RFC_READ_TABLE raise
     TABLE_WITHOUT_DATA — a FIELD error wearing the costume of an empty table. Three
     extraction runs returned 0 rows with no error because that exception was being
     swallowed as "empty is normal".
  2. A full read of DF14L returns TABLE_WITHOUT_DATA, and `FCTR_ID LIKE 'x%'` matches
     nothing. Only `FCTR_ID EQ '...'` works — so we ask for exactly the ids TDEVC
     references, batched with OR.
  3. OPTIONS has a total length limit. 40 OR-terms is fine; more silently returns
     nothing. And P01 rejects ROWSKIPS, so TADIR paging caps at 40,000 rows per type.

Read-only. Usage:  python brain_v2/system_profile/probes/extract_component_hierarchy.py
"""
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard

DB = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
BATCH = 40          # OR-terms per call — above this OPTIONS silently returns nothing
PAGE = 40000        # P01 rejects ROWSKIPS, so this is a hard cap per object type
TYPES = ["TABL", "FUGR", "CLAS", "TRAN", "FUNC", "PROG", "VIEW", "DTEL", "ENHO", "SXCI"]


def resolve_components(g, con):
    ids = [r[0].strip() for r in con.execute(
        "SELECT DISTINCT COMPONENT FROM tdevc WHERE COMPONENT IS NOT NULL AND COMPONENT<>''")]
    out = []
    for i in range(0, len(ids), BATCH):
        ch = ids[i:i + BATCH]
        opts = ["FCTR_ID EQ '%s'" % ch[0]] + ["OR FCTR_ID EQ '%s'" % x for x in ch[1:]]
        try:
            r = g.call("RFC_READ_TABLE", QUERY_TABLE="DF14L", DELIMITER="|", ROWCOUNT=9999,
                       # NOTE: FCTR_ID + PS_POSID only. PARENT_ID does not exist here.
                       FIELDS=[{"FIELDNAME": f} for f in ["FCTR_ID", "PS_POSID"]],
                       OPTIONS=[{"TEXT": o} for o in opts])
            out += [x["WA"].split("|") for x in r["DATA"]]
        except Exception as e:
            print("  batch error:", str(e)[:80])
    con.execute("DROP TABLE IF EXISTS df14l")
    con.execute("CREATE TABLE df14l (FCTR_ID TEXT PRIMARY KEY, PS_POSID TEXT)")
    con.executemany("INSERT OR REPLACE INTO df14l VALUES (?,?)",
                    [(r[0].strip(), r[1].strip()) for r in out])
    con.commit()
    print("df14l: %d of %d component ids resolved" % (len(out), len(ids)))


def extract_tadir(g, con):
    con.execute("CREATE TABLE IF NOT EXISTS tadir_obj "
                "(OBJECT TEXT, OBJ_NAME TEXT, DEVCLASS TEXT, PRIMARY KEY(OBJECT,OBJ_NAME))")
    for typ in TYPES:
        try:
            r = g.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|", ROWCOUNT=PAGE,
                       FIELDS=[{"FIELDNAME": f} for f in ["OBJ_NAME", "DEVCLASS"]],
                       OPTIONS=[{"TEXT": "PGMID EQ 'R3TR' AND OBJECT EQ '%s'" % typ}])
            rows = [x["WA"].split("|") for x in r["DATA"]]
        except Exception as e:
            if "TABLE_WITHOUT_DATA" not in str(e):
                print("  %s error: %s" % (typ, str(e)[:70]))
            continue
        con.executemany("INSERT OR REPLACE INTO tadir_obj VALUES (?,?,?)",
                        [(typ, x[0].strip(), x[1].strip()) for x in rows])
        con.commit()
        flag = "  (CAPPED — P01 rejects ROWSKIPS)" if len(rows) >= PAGE else ""
        print("  %-6s %6d%s" % (typ, len(rows), flag))
    print("tadir_obj total:", con.execute("SELECT COUNT(*) FROM tadir_obj").fetchone()[0])


def main():
    con = sqlite3.connect(str(DB))
    g = ConnectionGuard("P01")
    g.connect()
    resolve_components(g, con)
    extract_tadir(g, con)
    n = con.execute("""SELECT COUNT(*) FROM tadir_obj t JOIN tdevc d ON d.DEVCLASS=t.DEVCLASS
                       JOIN df14l f ON f.FCTR_ID=d.COMPONENT""").fetchone()[0]
    print("objects with a resolved application component:", n)
    con.close()
    g.close()


if __name__ == "__main__":
    main()
