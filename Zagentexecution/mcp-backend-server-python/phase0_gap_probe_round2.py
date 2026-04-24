"""
phase0_gap_probe_round2.py — Second-round pyrfc probes for UNESCO Structured Address Phase 0.

Closes:
  GAP-006 deep (MP_EXIT_FUNC distribution — correct column name this time)
  GAP-002 broader (BAdI implementations of FI_CGI_DMEE_EXIT_W_BADI via SXS_ATTR / SXS_INTER)
  Francesco E071 (5 transports FP_SPEZZANO — inspect E071 object keys to identify touched DMEE nodes)

Target: P01, SNC/SSO, read-only
Output: knowledge/domains/Payment/phase0/
"""

from __future__ import annotations
import csv, json, sys
from pathlib import Path
from collections import Counter

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

FRANCESCO_TRANSPORTS = [
    "D01K9B0CZ0",  # 2025-03-20 /CGI_XML_CT_UNESCO
    "D01K9B0CWS",  # 2025-03-07 /CGI_XML_CT_UNESCO_1
    "D01K9B0CUS",  # 2025-02-21 /CGI_XML_CT_UNESCO_1
    "D01K9B0CUT",  # 2025-02-21 /CGI_XML_CT_UNESCO_1
    "D01K9B0CTP",  # 2025-02-20 /CGI_XML_CT_UNESCO_1
]

report = {"probed_at": None, "target_system": "P01", "gaps": {}}


def gap006_deep(conn):
    """GAP-006 deep — DMEE_TREE_NODE with MP_EXIT_FUNC + classify exit funcs."""
    print("\n===== GAP-006 DEEP: MP_EXIT_FUNC distribution =====")

    keep = [
        "TREE_TYPE", "TREE_ID", "NODE_ID", "PARENT_ID", "NODE_TYPE", "TECH_NAME",
        "MP_FCODE" if False else "MP_SC_TAB", "MP_SC_FLD", "MP_CONST",
        "MP_EXIT_FUNC", "CK_EXIT_FUNC",
    ]
    # correct column set
    keep = ["TREE_TYPE","TREE_ID","NODE_ID","PARENT_ID","NODE_TYPE","TECH_NAME",
            "MP_SC_TAB","MP_SC_FLD","MP_CONST","MP_EXIT_FUNC","CK_EXIT_FUNC"]

    all_rows = []
    for tree_id in TREES:
        where = f"TREE_TYPE = 'PAYM' AND TREE_ID = '{tree_id}'"
        row_skip = 0
        batch = 2000
        tree_rows = []
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
            if not data: break
            for d in data:
                vals = d.get("WA", "").split("|")
                tree_rows.append(dict(zip([h.get("FIELDNAME") for h in header], vals)))
            if len(data) < batch: break
            row_skip += batch
        for row in tree_rows:
            row["_tree_id"] = tree_id
            all_rows.append(row)

    print(f"  Total nodes re-probed: {len(all_rows)}")

    # Save full dump
    out_csv = OUT_DIR / "gap006_dmee_nodes_with_exit.csv"
    if all_rows:
        cols_out = list({k for r in all_rows for k in r.keys()})
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols_out)
            w.writeheader()
            w.writerows(all_rows)
        print(f"  Wrote: {out_csv}")

    # Exit func distribution per tree
    ef_global = Counter()
    ck_global = Counter()
    for r in all_rows:
        mf = (r.get("MP_EXIT_FUNC") or "").strip()
        cf = (r.get("CK_EXIT_FUNC") or "").strip()
        if mf: ef_global[mf] += 1
        if cf: ck_global[cf] += 1

    print(f"\n  Distinct MP_EXIT_FUNC values: {len(ef_global)}")
    print(f"  Distinct CK_EXIT_FUNC values: {len(ck_global)}")
    print("  Top MP_EXIT_FUNC:")
    for fn, cnt in ef_global.most_common(20):
        print(f"    {fn}: {cnt}")
    print("  Top CK_EXIT_FUNC:")
    for fn, cnt in ck_global.most_common(20):
        print(f"    {fn}: {cnt}")

    # Per tree
    print("\n  Per tree — address-related nodes WITH exit funcs:")
    address_kw = ['StrtNm','BldgNb','PstCd','TwnNm','Ctry','AdrLine','PstlAdr','CdtrAgt','Dbtr','Cdtr','UltmtCdtr']
    for tree in TREES:
        tree_rows = [r for r in all_rows if r.get("_tree_id") == tree]
        addr_with_exit = [r for r in tree_rows
                          if (r.get("MP_EXIT_FUNC") or "").strip() or (r.get("CK_EXIT_FUNC") or "").strip()]
        addr_exit = [r for r in addr_with_exit if any(kw in (r.get("TECH_NAME") or "") for kw in address_kw)]
        print(f"    {tree}: {len(addr_with_exit)} with any exit, {len(addr_exit)} of them address-related")

    report["gaps"]["GAP-006_deep"] = {
        "total_nodes": len(all_rows),
        "mp_exit_funcs": dict(ef_global),
        "ck_exit_funcs": dict(ck_global),
        "csv": str(out_csv.relative_to(REPO)),
    }


def gap002_broader(conn):
    """GAP-002 broader — BAdI impls of FI_CGI_DMEE_EXIT_W_BADI via SXS_ATTR/SXS_INTER."""
    print("\n===== GAP-002 BROADER: BAdI implementations for FI_CGI_DMEE_EXIT_W_BADI =====")
    findings = {}

    # Try SXS_ATTR — BAdI implementation attributes
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="SXS_ATTR",
                      DELIMITER="|",
                      ROWCOUNT=200,
                      OPTIONS=[{"TEXT": "EXIT_NAME = 'FI_CGI_DMEE_EXIT_W_BADI'"}],
                      FIELDS=[{"FIELDNAME": "IMP_NAME"}, {"FIELDNAME": "EXIT_NAME"},
                              {"FIELDNAME": "IMP_CLASS"}, {"FIELDNAME": "STATUS"}])
        for d in r.get("DATA", []):
            vals = d.get("WA", "").split("|")
            rec = dict(zip(["IMP_NAME", "EXIT_NAME", "IMP_CLASS", "STATUS"], [v.strip() for v in vals]))
            findings[rec["IMP_NAME"]] = rec
        print(f"  SXS_ATTR hits for FI_CGI_DMEE_EXIT_W_BADI: {len(findings)}")
        for imp, rec in findings.items():
            print(f"    {imp}: class={rec['IMP_CLASS']} status={rec['STATUS']}")
    except Exception as e:
        print(f"  SXS_ATTR error: {e}")
        findings["_sxs_attr_error"] = str(e)

    # Also BADI filter values / enhancement spots
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="V_EXT_IMP",
                      DELIMITER="|",
                      ROWCOUNT=200,
                      OPTIONS=[{"TEXT": "EXIT_NAME LIKE 'FI_CGI_DMEE%' OR SPOT LIKE 'FI_CGI_DMEE%' OR NAME LIKE 'Y_IDFI_CGI%' OR NAME LIKE 'Z_IDFI_CGI%'"}],
                      FIELDS=[{"FIELDNAME": "NAME"}, {"FIELDNAME": "SPOT"}, {"FIELDNAME": "EXIT_NAME"}])
        print(f"\n  V_EXT_IMP hits: {len(r.get('DATA',[]))}")
        for d in r.get("DATA", [])[:30]:
            vals = d.get("WA", "").split("|")
            rec = dict(zip(["NAME", "SPOT", "EXIT_NAME"], [v.strip() for v in vals]))
            print(f"    {rec}")
    except Exception as e:
        print(f"  V_EXT_IMP error: {e}")

    # Also enhancement implementations (ENH_BADI_IMPL)
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="ENHBADIIMPL",
                      DELIMITER="|",
                      ROWCOUNT=200,
                      OPTIONS=[{"TEXT": "BADI_DEF = 'FI_CGI_DMEE_EXIT_W_BADI'"}],
                      FIELDS=[{"FIELDNAME": "ENHNAME"}, {"FIELDNAME": "BADI_DEF"},
                              {"FIELDNAME": "IMP_NAME"}, {"FIELDNAME": "IMP_CLASS"}])
        print(f"\n  ENHBADIIMPL hits: {len(r.get('DATA',[]))}")
        for d in r.get("DATA", []):
            vals = d.get("WA", "").split("|")
            rec = dict(zip(["ENHNAME", "BADI_DEF", "IMP_NAME", "IMP_CLASS"], [v.strip() for v in vals]))
            print(f"    {rec}")
            findings[f"ENH_{rec['ENHNAME']}"] = rec
    except Exception as e:
        print(f"  ENHBADIIMPL error: {e}")

    report["gaps"]["GAP-002_broader"] = findings


def francesco_e071(conn):
    """Inspect E071 for Francesco's 5 DMEE transports."""
    print("\n===== Francesco E071 node-level inspection =====")
    classifications = {}
    for trkorr in FRANCESCO_TRANSPORTS:
        print(f"\n  -- {trkorr} --")
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE="E071",
                          DELIMITER="|",
                          ROWCOUNT=50,
                          OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}'"}],
                          FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "PGMID"},
                                  {"FIELDNAME": "OBJECT"}, {"FIELDNAME": "OBJ_NAME"}])
            objs = []
            for d in r.get("DATA", []):
                vals = d.get("WA", "").split("|")
                rec = dict(zip(["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"], [v.strip() for v in vals]))
                objs.append(rec)
                print(f"    {rec['PGMID']} {rec['OBJECT']} {rec['OBJ_NAME']}")
            classifications[trkorr] = {"objects": objs}
        except Exception as e:
            print(f"    ERROR: {e}")
            classifications[trkorr] = {"error": str(e)}

        # For DMEE objects, also get E071K (key entries for table-like objects)
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE="E071K",
                          DELIMITER="|",
                          ROWCOUNT=100,
                          OPTIONS=[{"TEXT": f"TRKORR = '{trkorr}'"}],
                          FIELDS=[{"FIELDNAME": "TRKORR"}, {"FIELDNAME": "PGMID"},
                                  {"FIELDNAME": "OBJECT"}, {"FIELDNAME": "OBJNAME"},
                                  {"FIELDNAME": "TABKEY"}])
            keys = []
            for d in r.get("DATA", []):
                vals = d.get("WA", "").split("|")
                rec = dict(zip(["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"], [v.strip() for v in vals]))
                keys.append(rec)
            classifications[trkorr]["e071k"] = keys
            if keys:
                print(f"    E071K keys: {len(keys)}")
                for k in keys[:10]:
                    print(f"      {k['PGMID']} {k['OBJECT']} {k['OBJNAME']} TABKEY={k['TABKEY'][:80]}")
        except Exception as e:
            print(f"    E071K ERROR: {e}")

    report["gaps"]["francesco_e071"] = classifications


def main():
    from datetime import datetime
    report["probed_at"] = datetime.now().isoformat()
    conn = get_connection("P01")
    try:
        gap006_deep(conn)
        gap002_broader(conn)
        francesco_e071(conn)
    finally:
        conn.close()

    out_json = OUT_DIR / "gap_probe_results_round2.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    print(f"\nReport saved: {out_json}")


if __name__ == "__main__":
    main()
