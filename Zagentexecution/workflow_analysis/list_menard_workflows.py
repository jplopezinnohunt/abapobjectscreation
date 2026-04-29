"""
list_menard_workflows.py — Phase 1 discovery
============================================
List all workflow templates (WS) and standard tasks (TS) in D01 authored
or last-changed by N_MENARD.

Source tables:
  HRP1000 — object index (OTYPE, OBJID, BEGDA, ENDDA, UNAME, AENAM, SHORT, STEXT)
    OTYPE = 'WS' → workflow template
    OTYPE = 'TS' → standard task
    UNAME = creator, AENAM = last changer

Output:
  Zagentexecution/workflow_analysis/menard_workflows.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT_DIR, exist_ok=True)

USER = "N_MENARD"


def fetch(guard, otype, where_extra=""):
    """Pull HRP1000 rows for a given OTYPE filtered by UNAME/AENAM = N_MENARD."""
    # RFC_READ_TABLE has 72-char OPTIONS line limit; keep WHERE compact.
    where = [
        f"OTYPE = '{otype}'",
        "PLVAR = '01'",
        "ISTAT = '1'",
        f"( UNAME = '{USER}' OR AENAM = '{USER}' )",
    ]
    if where_extra:
        where.append(where_extra)
    # pyrfc requires list of dicts of {"TEXT": "..."} each <=72 chars.
    options = [{"TEXT": t} for t in [f"{w} AND" for w in where[:-1]] + [where[-1]]]
    fields = [{"FIELDNAME": f} for f in [
        "OTYPE", "OBJID", "BEGDA", "ENDDA", "UNAME", "AENAM", "SHORT", "STEXT"
    ]]
    result = guard.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="HRP1000",
        DELIMITER="|",
        OPTIONS=options,
        FIELDS=fields,
        ROWCOUNT=0,
    )
    cols = [f["FIELDNAME"] for f in result["FIELDS"]]
    rows = []
    for r in result["DATA"]:
        vals = [v.strip() for v in r["WA"].split("|")]
        rows.append(dict(zip(cols, vals)))
    return rows


def main():
    # system_id="D01" → no SAP_D01_* vars exist → falls back to SAP_* = D01 box
    guard = ConnectionGuard("D01")
    guard.connect()
    try:
        out = {"user": USER, "system": "D01", "client": 350}
        for otype, label in [("WS", "workflow_templates"), ("TS", "standard_tasks")]:
            rows = fetch(guard, otype)
            print(f"[{otype}] {len(rows)} rows")
            out[label] = rows
        path = os.path.join(OUT_DIR, "menard_workflows.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\nwrote {path}")
        print(f"  WS: {len(out['workflow_templates'])}")
        print(f"  TS: {len(out['standard_tasks'])}")
    finally:
        guard.close()


if __name__ == "__main__":
    main()
