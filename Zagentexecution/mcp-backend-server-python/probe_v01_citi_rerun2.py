"""
probe_v01_citi_rerun2.py  — resolve the two open questions:
  A) Does V01 actually hold the CITI DMEE tree today? list all PAYM trees.
  B) Recent CITI runs (DFPAYG FORMI=tree, LAUFD >= 2025) + their REGUV status.
  C) Recent payment-medium jobs (TBTCO JOBNAME LIKE 'PAYM:%') + status text.
READ-ONLY.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

TREE = "/CITI/XML/UNESCO/DC_V3_01"
c = get_connection("V01")
print("Connected to V01 (client from .env).")


def read(table, where, fields, rowcount=0):
    opts = [{"TEXT": where}] if where else []
    kw = dict(QUERY_TABLE=table, OPTIONS=opts,
              FIELDS=[{"FIELDNAME": f} for f in fields])
    if rowcount:
        kw["ROWCOUNT"] = rowcount
    try:
        r = c.call("RFC_READ_TABLE", **kw)
        return [row["WA"] for row in r.get("DATA", [])], None
    except Exception as e:
        return [], str(e)


def sec(t): print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# A) all PAYM trees in V01 — does CITI / SEPA / CGI exist?
sec("A) DMEE_TREE_HEAD — all PAYM trees in V01 (TREE_ID / VERSION / EX_STATUS)")
rows, err = read("DMEE_TREE_HEAD", "TREE_TYPE = 'PAYM'",
                 ["TREE_ID", "VERSION", "EX_STATUS"], rowcount=200)
if err:
    print(f"  ERROR: {err}")
print(f"  rows: {len(rows)}")
hits = [w for w in rows if "CITI" in w or "SEPA_CT_UNES" in w or "CGI_XML_CT_UNESCO" in w]
print("  --- UNESCO in-scope trees present ---")
for w in (hits or ["  (none of the 4 UNESCO trees found)"]):
    print(f"  {w}")
# also explicit point lookups with TREE_TYPE in the key
sec("A2) explicit CITI lookup (with TREE_TYPE key)")
for ver in ("000", "001"):
    rows, err = read("DMEE_TREE_HEAD",
                     f"TREE_TYPE = 'PAYM' AND TREE_ID = '{TREE}' AND VERSION = '{ver}'",
                     ["TREE_ID", "VERSION", "EX_STATUS", "FIRSTNODE_ID"])
    print(f"  V{ver}: {'NO ROW' if not rows else rows[0]}  {('ERR='+err) if err else ''}")

# B) recent CITI runs
sec("B) DFPAYG — CITI runs in 2025-2026 (recent, re-runnable)")
rows, err = read("DFPAYG", f"FORMI = '{TREE}' AND LAUFD >= '20250101'",
                 ["LAUFD", "LAUFI", "GRPNO", "ZBUKR", "HBKID", "RZAWE"], rowcount=60)
if err: print(f"  ERROR: {err}")
print(f"  recent CITI groups: {len(rows)}")
for w in rows[:40]:
    print(f"  {w}")
# max LAUFD overall for CITI
rows_all, _ = read("DFPAYG", f"FORMI = '{TREE}'", ["LAUFD"], rowcount=0)
if rows_all:
    lds = sorted({w[:8] for w in rows_all})
    print(f"  CITI total groups (all time): {len(rows_all)} ; earliest {lds[0]} ; latest {lds[-1]}")

# C) recent payment-medium jobs (all formats) + status
sec("C) TBTCO — payment-medium jobs (JOBNAME LIKE 'PAYM:%'), recent")
rows, err = read("TBTCO", "JOBNAME LIKE 'PAYM:%'",
                 ["JOBNAME", "STATUS", "SDLSTRTDT", "SDLSTRTTM"], rowcount=200)
if err: print(f"  ERROR: {err}")
# keep only 2026 by sched date and show CITI-ish (UNE_XML) + last 25
def jd(w):  # crude sched date extraction from end fields is unreliable; show raw
    return w
recent = [w for w in rows if "/UNE_" in w]
print(f"  PAYM jobs total: {len(rows)} ; with /UNE_ tag: {len(recent)}")
for w in recent[-30:]:
    print(f"  {w}")

c.close()
print("\nDONE")
