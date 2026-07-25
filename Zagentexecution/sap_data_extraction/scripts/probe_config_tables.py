"""
probe_config_tables.py
======================
Discovery probe for the LAST-FRONTIER SAP config tables (2026-06-19) that
unblock the unesco-sap-brain open hypotheses:

  HYP-018 / CLM-012/024  -> GMDERIVE config       (GMDT* / GM derivation)
  HYP-008 / OI-FI-01     -> Document splitting     (T8G*, FAGL_SPLIT*)
  F3                     -> New-GL ledger          (T881/T882, FAGLFLEXT, FMGLFLEXT)
  CLM-036 / HYP-003      -> Full FMDERIVE 26-step  (FMDT*)
  HYP-012                -> AVC threshold/tolerance (FMUP*, tolerance)

This script ONLY READS (RFC_READ_TABLE over SNC/SSO on P01 = compliant,
read-only). It discovers which tables actually EXIST in the catalog (DD02L),
their class, and field width. ABSENCE / emptiness is itself evidence
(e.g. "is GMDERIVE activated?"), so we record it precisely.

Run:
    python probe_config_tables.py
"""

import os
import sys
import json
from datetime import datetime

MCP = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP))
from rfc_helpers import get_connection  # noqa: E402

# Catalog-pattern groups -> the brain question each one answers.
PATTERN_GROUPS = {
    "GMDERIVE (HYP-018, CLM-012/024)": ["GMDT%", "GMDERIVE%"],
    "DocSplit (HYP-008, OI-FI-01)":    ["T8G%", "FAGL_SPLIT%", "FAGL_ACTSPLIT%"],
    "New-GL ledger (F3)":              ["T881%", "T882%", "FAGLFLEXT%", "FMGLFLEXT%", "FAGL_T_LEDGER%"],
    "FMDERIVE 26-step (CLM-036, HYP-003)": ["FMDT%", "FMDERIVE%"],
    "AVC tolerance (HYP-012)":         ["FMUP%", "FMAVCT_TOL%", "TFM_TOL%", "FMTOLER%"],
}


def dd02l_lookup(conn, like):
    """Return list of {TABNAME, TABCLASS} from DD02L for TABNAME LIKE <like>."""
    res = conn.call(
        "RFC_READ_TABLE", QUERY_TABLE="DD02L", DELIMITER="|",
        ROWCOUNT=0,  # all matching rows
        OPTIONS=[{"TEXT": f"TABNAME LIKE '{like}' AND AS4LOCAL = 'A'"}],
        FIELDS=[{"FIELDNAME": "TABNAME"}, {"FIELDNAME": "TABCLASS"}],
    )
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({"TABNAME": parts[0].strip(), "TABCLASS": parts[1].strip()})
    return out


def field_meta(conn, table):
    """Return (field_names, total_width) using RFC_READ_TABLE's own FIELDS metadata."""
    res = conn.call(
        "RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
        ROWCOUNT=1, OPTIONS=[], FIELDS=[],
    )
    names = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    width = sum(int(f.get("LENGTH", 0)) for f in res.get("FIELDS", []))
    n_sample = len(res.get("DATA", []))
    return names, width, n_sample


def main():
    print(f"=== Config-table discovery probe | P01 | {datetime.now():%Y-%m-%d %H:%M:%S} ===")
    conn = get_connection("P01")
    print("Connected to P01 (SNC/SSO).\n")

    report = {}
    for group, patterns in PATTERN_GROUPS.items():
        print(f"### {group}")
        group_hits = []
        seen = set()
        for pat in patterns:
            try:
                hits = dd02l_lookup(conn, pat)
            except Exception as e:
                print(f"  {pat}: DD02L ERROR {type(e).__name__}: {e}")
                continue
            for h in hits:
                if h["TABNAME"] in seen:
                    continue
                seen.add(h["TABNAME"])
                # only TRANSP/POOL/CLUSTER (real data tables), skip views/structures
                if h["TABCLASS"] not in ("TRANSP", "POOL", "CLUSTER"):
                    continue
                # field meta + sample-row presence
                try:
                    names, width, n_sample = field_meta(conn, h["TABNAME"])
                    h["NFIELDS"] = len(names)
                    h["WIDTH"] = width
                    h["HAS_ROW"] = n_sample > 0
                except Exception as e:
                    h["NFIELDS"] = -1
                    h["WIDTH"] = -1
                    h["HAS_ROW"] = None
                    h["ERR"] = f"{type(e).__name__}: {e}"
                group_hits.append(h)
                flag = "ROWS" if h.get("HAS_ROW") else ("empty" if h.get("HAS_ROW") is False else "?")
                print(f"  {h['TABNAME']:<22} {h['TABCLASS']:<8} fields={h.get('NFIELDS')} width={h.get('WIDTH')} [{flag}]")
        if not group_hits:
            print("  (no matching data tables in catalog)")
        report[group] = group_hits
        print()

    conn.close()
    out_path = os.path.join(os.path.dirname(__file__), "config_tables_discovery.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"Discovery written -> {out_path}")


if __name__ == "__main__":
    main()
