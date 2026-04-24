"""
phase0_gap_probe.py — UNESCO Structured Address Phase 0 pyrfc gap closure.

Closes:
  GAP-002 (Event 05 handlers)
  GAP-003 (YCL_IDFI_CGI_DMEE_AE / _BH existence in P01)
  GAP-004 (CI_FPAYHX full schema)
  GAP-006 (DMEE_TREE_NODE with EXIT_FUNC/SRC_VAL columns for 4 target trees)

Target: P01, SNC/SSO, read-only
Output: knowledge/domains/Payment/phase0/
"""

from __future__ import annotations
import csv, json, os, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

REPO = HERE.parent.parent
OUT_DIR = REPO / "knowledge" / "domains" / "Payment" / "phase0"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TREES = [
    "/SEPA_CT_UNES",
    "/CITI/XML/UNESCO/DC_V3_01",
    "/CGI_XML_CT_UNESCO",
    "/CGI_XML_CT_UNESCO_1",
]

report = {"probed_at": None, "target_system": "P01", "gaps": {}}


def gap003_ae_bh(conn):
    """GAP-003: AE/BH classes existence in P01."""
    print("\n===== GAP-003: AE/BH classes in P01 TADIR =====")
    findings = {}
    for obj_name in [
        "YCL_IDFI_CGI_DMEE_AE",
        "YCL_IDFI_CGI_DMEE_BH",
        "Y_IDFI_CGI_DMEE_COUNTRY_AE",
        "Y_IDFI_CGI_DMEE_COUNTRY_BH",
        "YCL_IDFI_CGI_DMEE_DE",
        "YCL_IDFI_CGI_DMEE_IT",
    ]:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TADIR",
                      DELIMITER="|",
                      OPTIONS=[{"TEXT": f"OBJ_NAME = '{obj_name}'"}],
                      FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                              {"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AUTHOR"},
                              {"FIELDNAME": "CREATED_ON"}])
        rows = r.get("DATA", [])
        findings[obj_name] = {
            "exists": len(rows) > 0,
            "rows": [x.get("WA", "") for x in rows],
        }
        exists = "EXISTS" if rows else "NOT FOUND"
        print(f"  {obj_name}: {exists} ({len(rows)} rows)")
    report["gaps"]["GAP-003"] = findings
    return findings


def gap004_fpayhx_schema(conn):
    """GAP-004: CI_FPAYHX full schema + all FPAYHX Z-fields."""
    print("\n===== GAP-004: FPAYHX schema =====")
    # Get full FPAYHX fields via DDIF_FIELDINFO_GET
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPAYHX", ALL_TYPES="X")
        fields = r.get("DFIES_TAB", [])
        z_fields = [f for f in fields if f.get("FIELDNAME", "").startswith("Z")]
        print(f"  FPAYHX: {len(fields)} total fields, {len(z_fields)} Z-fields")
        for f in z_fields[:30]:
            print(f"    {f.get('FIELDNAME', ''):<20} {f.get('INTTYPE', '')} L={f.get('INTLEN', '')} {f.get('FIELDTEXT', '')[:60]}")
        report["gaps"]["GAP-004"] = {
            "total_fields": len(fields),
            "z_fields_count": len(z_fields),
            "z_fields": [{"name": f.get("FIELDNAME"), "type": f.get("INTTYPE"), "len": f.get("INTLEN"),
                          "text": f.get("FIELDTEXT", "")} for f in z_fields],
        }
    except Exception as e:
        print(f"  ERROR on FPAYHX: {e}")
        report["gaps"]["GAP-004"] = {"error": str(e)}

    # Also FPAYH REF fields
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPAYH", ALL_TYPES="X")
        fields = r.get("DFIES_TAB", [])
        ref_fields = [f for f in fields if f.get("FIELDNAME", "").startswith("REF")]
        print(f"\n  FPAYH REF fields: {len(ref_fields)}")
        for f in ref_fields:
            print(f"    {f.get('FIELDNAME', ''):<15} {f.get('INTTYPE', '')} L={f.get('INTLEN', '')} {f.get('FIELDTEXT', '')[:60]}")
        report["gaps"].setdefault("GAP-004", {})["fpayh_ref_fields"] = [
            {"name": f.get("FIELDNAME"), "type": f.get("INTTYPE"), "len": f.get("INTLEN"),
             "text": f.get("FIELDTEXT", "")} for f in ref_fields
        ]
    except Exception as e:
        print(f"  ERROR on FPAYH: {e}")


def gap006_dmee_full_nodes(conn):
    """GAP-006: DMEE_TREE_NODE with all relevant columns for 4 target trees."""
    print("\n===== GAP-006: DMEE_TREE_NODE full columns for 4 target trees =====")
    # Discover columns of DMEE_TREE_NODE first
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME="DMEE_TREE_NODE", ALL_TYPES="X")
        fields = r.get("DFIES_TAB", [])
        all_col_names = [f.get("FIELDNAME") for f in fields]
        print(f"  DMEE_TREE_NODE: {len(all_col_names)} columns")
        print(f"  Columns: {all_col_names[:40]}")
        report["gaps"]["GAP-006"] = {"columns": all_col_names}
    except Exception as e:
        print(f"  DDIF ERROR: {e}")
        report["gaps"]["GAP-006"] = {"error_ddif": str(e)}
        return

    # Choose the most relevant columns
    desired_cols = [
        "TREE_TYPE", "TREE_ID", "NODE_ID", "PARENT_ID", "NODE_TYPE", "TECH_NAME",
        "MP_FCODE", "MP_SC_TAB", "MP_SC_FLD", "MP_CONST", "EXIT_FUNC",
        "MP_TARGET_TAG", "COMBINE_LEVEL", "MP_OPERATOR", "MP_LEFT_OP", "MP_RIGHT_OP",
    ]
    keep = [c for c in desired_cols if c in all_col_names]
    print(f"  Using columns: {keep}")

    # Extract nodes for each target tree
    all_rows = []
    for tree_id in TREES:
        print(f"\n  Probing tree: {tree_id}")
        where = f"TREE_TYPE = 'PAYM' AND TREE_ID = '{tree_id}'"
        try:
            # Pagination-safe — use small batch
            all_for_tree = []
            row_skip = 0
            batch = 2000
            while True:
                r = conn.call("RFC_READ_TABLE",
                              QUERY_TABLE="DMEE_TREE_NODE",
                              DELIMITER="|",
                              ROWCOUNT=batch,
                              ROWSKIPS=row_skip,
                              OPTIONS=[{"TEXT": where}],
                              FIELDS=[{"FIELDNAME": c} for c in keep])
                data = r.get("DATA", [])
                header = r.get("FIELDS", [])
                if not data:
                    break
                for d in data:
                    vals = d.get("WA", "").split("|")
                    all_for_tree.append(dict(zip([h.get("FIELDNAME") for h in header], vals)))
                if len(data) < batch:
                    break
                row_skip += batch
            print(f"    {tree_id}: {len(all_for_tree)} nodes")
            for row in all_for_tree:
                row["_tree_id"] = tree_id
                all_rows.append(row)
        except Exception as e:
            print(f"    ERROR: {e}")

    # Save all rows
    out_csv = OUT_DIR / "gap006_dmee_tree_nodes_full.csv"
    if all_rows:
        cols_out = list({k for r in all_rows for k in r.keys()})
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols_out)
            w.writeheader()
            for r in all_rows:
                w.writerow(r)
        print(f"\n  Wrote: {out_csv} ({len(all_rows)} rows)")
        report["gaps"]["GAP-006"]["rows_written"] = len(all_rows)
        report["gaps"]["GAP-006"]["output_file"] = str(out_csv.relative_to(REPO))

    # Now filter for address nodes and exit functions
    addr_nodes = [r for r in all_rows if any(a.strip().strip('<>').lower() in (r.get('TECH_NAME','') or '').lower()
                                              for a in ['StrtNm', 'BldgNb', 'PstCd', 'TwnNm', 'Ctry', 'AdrLine',
                                                        'PstlAdr', 'CdtrAgt', 'Dbtr', 'Cdtr', 'UltmtCdtr'])]
    print(f"\n  Address-related nodes: {len(addr_nodes)}")
    report["gaps"]["GAP-006"]["address_nodes_count"] = len(addr_nodes)

    # EXIT_FUNC distribution
    if "EXIT_FUNC" in (all_rows[0] if all_rows else {}):
        from collections import Counter
        ef = Counter(r.get("EXIT_FUNC", "").strip() for r in all_rows if r.get("EXIT_FUNC", "").strip())
        print(f"\n  Distinct EXIT_FUNC values: {len(ef)}")
        for func, cnt in ef.most_common(15):
            print(f"    {func}: {cnt} nodes")
        report["gaps"]["GAP-006"]["exit_funcs"] = dict(ef)


def gap002_event05(conn):
    """GAP-002: Event 05 / SAPLFPAY_EVENTS handlers."""
    print("\n===== GAP-002: SAPLFPAY_EVENTS / FPAY_EVENT / Y/Z_FPAY_EVENT =====")
    findings = {}
    for obj_name_pattern in [
        "SAPLFPAY_EVENTS",
        "FPAY_EVENT_%",
        "Y_FPAY_EVENT%",
        "Z_FPAY_EVENT%",
        "Y_FPAY_%",
        "Z_FPAY_%",
        "FPAY_EVENT_05",
    ]:
        for pgmid in ("R3TR",):
            for obj in ("FUGR", "PROG", "FUNC"):
                try:
                    r = conn.call("RFC_READ_TABLE",
                                  QUERY_TABLE="TADIR",
                                  DELIMITER="|",
                                  ROWCOUNT=100,
                                  OPTIONS=[{"TEXT": f"PGMID = '{pgmid}' AND OBJECT = '{obj}' AND OBJ_NAME LIKE '{obj_name_pattern}'"}],
                                  FIELDS=[{"FIELDNAME": "PGMID"}, {"FIELDNAME": "OBJECT"},
                                          {"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"},
                                          {"FIELDNAME": "AUTHOR"}])
                    rows = r.get("DATA", [])
                    if rows:
                        for row in rows:
                            vals = row.get("WA", "").split("|")
                            rec = dict(zip(["PGMID", "OBJECT", "OBJ_NAME", "DEVCLASS", "AUTHOR"], vals))
                            rec = {k: (v or "").strip() for k, v in rec.items()}
                            key = f"{rec['OBJECT']}:{rec['OBJ_NAME']}"
                            if key not in findings:
                                findings[key] = rec
                except Exception:
                    pass
    print(f"  Total distinct Event/FM objects found: {len(findings)}")
    for key, rec in list(findings.items())[:30]:
        print(f"    {rec['OBJECT']:<5} {rec['OBJ_NAME']:<40} devclass={rec['DEVCLASS']} author={rec['AUTHOR']}")
    report["gaps"]["GAP-002"] = {"count": len(findings), "items": list(findings.values())}


def main():
    print("=" * 70)
    print("Phase 0 pyrfc gap closure probe — target P01")
    print("=" * 70)
    from datetime import datetime
    report["probed_at"] = datetime.utcnow().isoformat() + "Z"
    conn = get_connection("P01")

    try:
        gap003_ae_bh(conn)
        gap004_fpayhx_schema(conn)
        gap002_event05(conn)
        gap006_dmee_full_nodes(conn)
    finally:
        conn.close()

    # Save the full report
    out_json = OUT_DIR / "gap_probe_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nReport saved: {out_json}")


if __name__ == "__main__":
    main()
