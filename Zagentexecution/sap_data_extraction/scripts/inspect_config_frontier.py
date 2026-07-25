"""
inspect_config_frontier.py
===========================
Turn the freshly-extracted config tables into the actual EVIDENCE that answers
each open hypothesis. Reads the golden DB tables + a couple of live activation
probes (FAGL_ACTIVEC, splitting-active) that aren't worth persisting wide.
"""
import os, sys, sqlite3
MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection

GOLD_DB = r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\sqlite\p01_gold_master_data.db"
db = sqlite3.connect(GOLD_DB)

def cols(t):
    return [r[1] for r in db.execute(f"PRAGMA table_info({t})")]

def show(t, limit=8, where=""):
    c = cols(t)
    w = f" WHERE {where}" if where else ""
    rows = db.execute(f"SELECT * FROM {t}{w} LIMIT {limit}").fetchall()
    n = db.execute(f"SELECT COUNT(*) FROM {t}{w}").fetchone()[0]
    print(f"\n--- {t}  ({n} rows{', filtered' if where else ''}) cols={c}")
    for r in rows:
        print("   ", dict(zip(c, r)))

print("="*70)
print("DOC SPLITTING — is there a method/rule, and method Z000000012?")
print("="*70)
for t in ("t8g17", "t8g40", "t8g12", "t8g20", "t8g21", "t8g30a"):
    try: show(t, 6)
    except Exception as e: print(f"  {t}: {e}")
# grep for the named method anywhere
print("\n[grep] looking for method '12' / 'Z000000012' across split tables:")
for t in ("t8g12","t8g20","t8g21","t8g21a","t8g30a","t8g40","t8g16"):
    try:
        c = cols(t)
        hit = db.execute(f"SELECT * FROM {t} WHERE " +
                         " OR ".join([f'"{col}" LIKE \'%000000012%\'' for col in c])).fetchall()
        if hit: print(f"   {t}: {len(hit)} rows mention *000000012* -> {hit[:3]}")
    except Exception: pass

print("\n"+"="*70)
print("NEW-GL LEDGER — T881 ledgers + T882 totals-table assignment")
print("="*70)
show("t881", 50)
show("t882", 15)
show("t882c", 12)

print("\n"+"="*70)
print("FMDERIVE — step count + which steps use table lookups")
print("="*70)
show("fmderiveenvid", 5)
show("fmderivefuncid", 20)
# FMDERIVEFUNC: count distinct steps per environment
try:
    c = cols("fmderivefunc")
    print(f"\n  FMDERIVEFUNC cols = {c}")
    show("fmderivefunc", 6)
except Exception as e: print(e)

print("\n"+"="*70)
print("AVC TOLERANCE — FMUP01 (tolerance profile), FMUP02 (actions)")
print("="*70)
show("fmup00", 20)
show("fmup01", 30)
show("fmup02", 10)

db.close()

print("\n"+"="*70)
print("LIVE PROBES — new-GL & splitting activation (not persisted)")
print("="*70)
conn = get_connection("P01")
def probe(table, fields, where=""):
    try:
        opt = [{"TEXT": where}] if where else []
        res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                        ROWCOUNT=20, OPTIONS=opt,
                        FIELDS=[{"FIELDNAME": f} for f in fields])
        hdr = [f["FIELDNAME"] for f in res["FIELDS"]]
        print(f"\n  {table} ({len(res['DATA'])} rows): {hdr}")
        for row in res["DATA"]:
            print("     ", row["WA"])
    except Exception as e:
        print(f"  {table}: {type(e).__name__}: {str(e).splitlines()[0]}")

# New GL activation
probe("FAGL_ACTIVEC", ["RLDNR","BUKRS","ACTIVE","SPLIT_ACTIVE","INHERITANCE","DEFAULT_PRCTR"])
# fallback names
probe("FAGL_ACTIVE", ["ACTIVE"])
# splitting active per cocode
probe("FAGL_SPLIT_ACTC", ["BUKRS","SPLIT_ACTIVE"])
# splitting method assigned (global)
probe("FAGL_SPLIT_FLD", ["METHOD"])
conn.close()
