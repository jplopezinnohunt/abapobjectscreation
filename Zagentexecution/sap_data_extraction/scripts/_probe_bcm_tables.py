"""Probe which BCM/DMEE/PAYM tables exist in P01 with 1-row sample."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP = os.path.abspath(os.path.join(SCRIPTS_DIR, "..", "..", "mcp-backend-server-python"))
if MCP not in sys.path: sys.path.insert(0, MCP)

from rfc_helpers import ConnectionGuard

g = ConnectionGuard("P01")
g.connect()
print("[OK] Connected to P01", flush=True)

# Candidate tables for the E2E chain
tables = [
    # BCM structure / batch -> payment -> file
    "BNK_BATCH_PAYM",       # batch -> payment rows
    "BNK_PAYM",             # payment master
    "BNK_PAYM_STR",         # payment structure (optional)
    "BNK_PAYM_FILE",        # physical file output
    "BNK_BATCH_STATUS",     # status transitions
    "BNK_BATCH_STR",        # batch structure
    "BNK_APL_COMP",         # BCM application config
    "BNK_APL_STR",          # BCM application structure
    # Rule defs
    "T74F_RC_NAMES",        # BCM rule names
    "T74F_ROUT_RULE",       # routing rule
    "T74F_ROUT_RULE_CR",    # rule criteria
    # DMEE
    "T042Y",                # DME format per PM
    "DMEE_TREES",           # DMEE tree master
    "FDTA_DMEE_HD",         # DMEE file output header
    "FDTA_DMEE_IT",         # DMEE file output item
    "TZBZ",                 # payment program variants
    # Alternative / older
    "REGUA",                # payment program admin
    "REGUS",                # payment program stats
]

for t in tables:
    try:
        r = g.call("RFC_READ_TABLE", QUERY_TABLE=t, ROWCOUNT=1, DELIMITER="|", FIELDS=[])
        fields = [f["FIELDNAME"] for f in r.get("FIELDS", [])]
        data = r.get("DATA", [])
        print(f"  [OK]   {t:<25}  fields={len(fields):>3}  sample_rows={len(data)}")
    except Exception as e:
        msg = str(e)[:80]
        print(f"  [FAIL] {t:<25}  {type(e).__name__}: {msg}")

g.close()
print("DONE", flush=True)
