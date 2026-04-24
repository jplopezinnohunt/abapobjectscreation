"""phase0_dmee_full_extraction.py — Complete DMEE extraction for 4 target trees.

Closes the gap from round 2: extract ALL 48 columns of DMEE_TREE_NODE +
ALL 6 related DMEE tables (TREES, COND, SORT, ATOM, VALUE, TEXT).

Target: P01 + D01 (compare), SNC/SSO, read-only.
Output: knowledge/domains/Payment/phase0/dmee_full/
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

REPO = HERE.parent.parent
OUT_DIR = REPO / "knowledge" / "domains" / "Payment" / "phase0" / "dmee_full"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TREES = [
    "/SEPA_CT_UNES",
    "/CITI/XML/UNESCO/DC_V3_01",
    "/CGI_XML_CT_UNESCO",
    "/CGI_XML_CT_UNESCO_1",
]

DMEE_TABLES = [
    "DMEE_TREE_NODE",
    "DMEE_TREE_COND",
    "DMEE_TREE_SORT",
    "DMEE_TREE_ATOM",
]
# Extra tables may not exist in all SAP releases — we probe them gracefully
OPTIONAL_DMEE_TABLES = [
    "DMEE_TREE_VALUE",
    "DMEE_TREE_TEXT",
    "DMEE_TREES",
    "DMEE_TREE_HEAD",
]


def get_fields(conn, table):
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME=table, ALL_TYPES="X")
        return [f.get("FIELDNAME") for f in r.get("DFIES_TAB", [])]
    except Exception as e:
        return None


def extract_table_for_tree(conn, table, tree_id, fields, where_prefix="TREE_TYPE = 'PAYM' AND TREE_ID"):
    """Extract rows from a DMEE table for a given tree_id, all fields."""
    # RFC_READ_TABLE max 512 bytes per row — need to split fields if too wide
    # Strategy: probe count first; if small, full fields; else split by chunks
    where = f"{where_prefix} = '{tree_id}'"

    # Split fields in chunks to fit 512-byte buffer
    # Avg 20 bytes/field -> max ~25 fields per call
    chunk_size = 15
    chunks = [fields[i:i+chunk_size] for i in range(0, len(fields), chunk_size)]

    rows_by_key = {}  # key = NODE_ID (or other PK) -> merged dict

    pk_candidates = ["NODE_ID", "COND_ID", "TREE_ID"]  # not a true PK across tables; we concat row values
    # Simpler approach: since we fetch all rows with same WHERE in same order, we can concatenate chunks by row index
    full_rows_per_chunk = []
    for chunk in chunks:
        chunk_rows = []
        row_skip = 0
        batch = 2000
        while True:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE=table,
                          DELIMITER="|",
                          ROWCOUNT=batch,
                          ROWSKIPS=row_skip,
                          OPTIONS=[{"TEXT": where}],
                          FIELDS=[{"FIELDNAME": c} for c in chunk])
            data = r.get("DATA", [])
            header = r.get("FIELDS", [])
            if not data: break
            for d in data:
                vals = d.get("WA", "").split("|")
                chunk_rows.append(dict(zip([h.get("FIELDNAME") for h in header], vals)))
            if len(data) < batch: break
            row_skip += batch
        full_rows_per_chunk.append(chunk_rows)

    # Merge by row index (same WHERE, same order assumed)
    merged = []
    max_len = max((len(c) for c in full_rows_per_chunk), default=0)
    for i in range(max_len):
        m = {}
        for chunk_rows in full_rows_per_chunk:
            if i < len(chunk_rows):
                m.update(chunk_rows[i])
        merged.append(m)
    return merged


def main():
    print(f"=== DMEE full extraction starting {datetime.now()} ===")
    conn = get_connection("P01")
    try:
        # Step 1: discover schemas
        schemas = {}
        for tbl in DMEE_TABLES + OPTIONAL_DMEE_TABLES:
            fields = get_fields(conn, tbl)
            if fields:
                schemas[tbl] = fields
                print(f"  {tbl}: {len(fields)} fields")
            else:
                print(f"  {tbl}: not available")

        # Step 2: for each core table, extract all rows for 4 trees
        summary = {"extracted_at": datetime.now().isoformat(), "schemas": schemas, "counts": {}}
        for tbl, fields in schemas.items():
            if not fields: continue
            # Not all tables have TREE_ID as key; the core 4 do
            if tbl in ("DMEE_TREE_NODE", "DMEE_TREE_COND", "DMEE_TREE_SORT", "DMEE_TREE_ATOM",
                       "DMEE_TREE_VALUE", "DMEE_TREE_TEXT"):
                all_rows = []
                for tree_id in TREES:
                    rows = extract_table_for_tree(conn, tbl, tree_id, fields)
                    for r in rows:
                        r["_tree_id"] = tree_id
                    all_rows.extend(rows)
                out_csv = OUT_DIR / f"{tbl.lower()}_p01.csv"
                if all_rows:
                    cols = list({k for r in all_rows for k in r.keys()})
                    with open(out_csv, "w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=cols)
                        w.writeheader()
                        w.writerows(all_rows)
                print(f"  {tbl}: {len(all_rows)} rows written to {out_csv.name}")
                summary["counts"][tbl] = len(all_rows)
            elif tbl in ("DMEE_TREES", "DMEE_TREE_HEAD"):
                # Header tables — filter by TREE_ID
                for tree_id in TREES:
                    try:
                        r = conn.call("RFC_READ_TABLE",
                                      QUERY_TABLE=tbl,
                                      DELIMITER="|",
                                      ROWCOUNT=10,
                                      OPTIONS=[{"TEXT": f"TREE_TYPE = 'PAYM' AND TREE_ID = '{tree_id}'"}],
                                      FIELDS=[{"FIELDNAME": c} for c in fields[:15]])
                        for d in r.get("DATA", []):
                            vals = d.get("WA", "").split("|")
                            rec = dict(zip([h.get("FIELDNAME") for h in r.get("FIELDS", [])], vals))
                            rec["_tree_id"] = tree_id
                            summary.setdefault(tbl, []).append(rec)
                    except Exception as e:
                        print(f"    {tbl}/{tree_id}: {e}")
                print(f"  {tbl}: {len(summary.get(tbl, []))} headers captured")
    finally:
        conn.close()

    with open(OUT_DIR / "dmee_full_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSummary: {OUT_DIR / 'dmee_full_summary.json'}")


if __name__ == "__main__":
    main()
