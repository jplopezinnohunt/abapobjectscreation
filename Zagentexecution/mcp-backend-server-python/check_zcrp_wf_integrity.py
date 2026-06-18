"""
check_zcrp_wf_integrity.py
==========================
Read-only referential integrity health check for 7 ZCRP_WF* tables in D01 (350).

Counts rows in each table and verifies 6 parent/child relationships for orphaned
foreign keys BEFORE FKs are declared in DDIC. Writes JSON output and prints
a text summary.

NO writes. Pure SELECT via RFC_READ_TABLE.
"""
import json
import os
import sys
import time

from rfc_helpers import get_connection

TABLES = {
    "ZCRP_WFT_TYPE":     ["WFTYPE"],
    "ZCRP_WFT_TYPET":    ["SPRAS", "WFTYPE"],
    "ZCRP_WFT_STEP":     ["WFTYPE", "WFSTEP"],
    "ZCRP_WFT_STEPT":    ["SPRAS", "WFTYPE", "WFSTEP"],
    "ZCRP_WFT_ACT_TY":   ["ACTTY"],
    "ZCRP_WFT_ACT_TYT":  ["SPRAS", "ACTTY"],
    "ZCRP_WFT_STPACT":   ["WFTYPE", "WFSTEP", "ACTTY"],
}

# Relations: (child_table, parent_table, list of fields to match on both sides)
RELATIONS = [
    ("ZCRP_WFT_TYPET",   "ZCRP_WFT_TYPE",   ["WFTYPE"]),
    ("ZCRP_WFT_STEP",    "ZCRP_WFT_TYPE",   ["WFTYPE"]),
    ("ZCRP_WFT_STEPT",   "ZCRP_WFT_STEP",   ["WFTYPE", "WFSTEP"]),
    ("ZCRP_WFT_ACT_TYT", "ZCRP_WFT_ACT_TY", ["ACTTY"]),
    ("ZCRP_WFT_STPACT",  "ZCRP_WFT_STEP",   ["WFTYPE", "WFSTEP"]),
    ("ZCRP_WFT_STPACT",  "ZCRP_WFT_ACT_TY", ["ACTTY"]),
]

OUT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "tmp",
        "zcrp_wf_integrity_check.json",
    )
)


def _rfc_read_all(conn, table, fields, batch_size=2000, throttle=0.2):
    """Read all rows for a Z catalog table (small) -- no WHERE, paginate."""
    from pyrfc import RFCError
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    all_rows = []
    offset = 0
    while True:
        try:
            result = conn.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table,
                DELIMITER="|",
                ROWCOUNT=batch_size,
                ROWSKIPS=offset,
                OPTIONS=[],
                FIELDS=rfc_fields,
            )
        except RFCError as e:
            err = str(e)
            if "TABLE_WITHOUT_DATA" in err:
                return []
            raise
        raw = result.get("DATA", [])
        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        if not raw:
            break
        for row in raw:
            parts = row["WA"].split("|")
            all_rows.append(
                {h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)}
            )
        if len(raw) < batch_size:
            break
        offset += len(raw)
        if throttle > 0:
            time.sleep(throttle)
    return all_rows


def main():
    print("[INFO] Connecting to D01 (client 350) ...")
    conn = get_connection("D01")
    print("[INFO] Connected. Reading 7 ZCRP_WF* tables ...")

    # --- Read every table once (full PK columns only, plus MANDT for context) ---
    table_data = {}
    counts = {}
    for tname, key_cols in TABLES.items():
        # Read MANDT + key columns only -- we don't need attribute data for integrity
        cols = ["MANDT"] + key_cols
        try:
            rows = _rfc_read_all(conn, tname, cols)
            table_data[tname] = rows
            counts[tname] = len(rows)
            print(f"  [OK] {tname}: {len(rows):,} rows")
        except Exception as e:
            print(f"  [ERROR] {tname}: {type(e).__name__}: {e}")
            table_data[tname] = None
            counts[tname] = None

    conn.close()

    # --- Compute orphans for each relation ---
    orphans = {}
    any_orphans = False
    any_error = False

    for child, parent, match_fields in RELATIONS:
        key = f"{child}→{parent}"
        if table_data.get(child) is None or table_data.get(parent) is None:
            orphans[key] = {
                "count": None,
                "samples": [],
                "error": "table extraction failed",
                "match_fields": match_fields,
            }
            any_error = True
            continue

        # Build set of parent keys (tuple of match field values)
        parent_keys = set()
        for prow in table_data[parent]:
            parent_keys.add(tuple(prow.get(f, "") for f in match_fields))

        # Walk child rows and detect orphans
        orphan_rows = []
        for crow in table_data[child]:
            ckey = tuple(crow.get(f, "") for f in match_fields)
            if ckey not in parent_keys:
                # Capture full PK of the child row for traceability
                full_pk = {f: crow.get(f, "") for f in (["MANDT"] + TABLES[child])}
                orphan_rows.append(full_pk)

        orphans[key] = {
            "count": len(orphan_rows),
            "samples": orphan_rows[:5],
            "match_fields": match_fields,
        }
        if orphan_rows:
            any_orphans = True

    if any_error:
        verdict = "ERROR"
    elif any_orphans:
        verdict = "ORPHANS_FOUND"
    else:
        verdict = "CLEAN"

    out = {
        "system": "D01",
        "client": "350",
        "counts": counts,
        "orphans": orphans,
        "verdict": verdict,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Wrote {OUT_PATH}")

    # --- Text summary ---
    print("\n" + "=" * 60)
    print("COUNTS")
    print("=" * 60)
    print(f"  {'Table':<22} {'Rows':>10}")
    print(f"  {'-' * 22} {'-' * 10}")
    for t in TABLES:
        c = counts.get(t)
        c_str = f"{c:,}" if isinstance(c, int) else "ERROR"
        print(f"  {t:<22} {c_str:>10}")

    print("\n" + "=" * 60)
    print("ORPHAN CHECK (child rows whose key has no parent)")
    print("=" * 60)
    print(f"  {'#':<3} {'Child → Parent':<45} {'Orphans':>10}")
    print(f"  {'-' * 3} {'-' * 45} {'-' * 10}")
    for i, (child, parent, _mf) in enumerate(RELATIONS, 1):
        key = f"{child}→{parent}"
        ocount = orphans[key]["count"]
        ostr = f"{ocount:,}" if isinstance(ocount, int) else "ERROR"
        label = f"{child} → {parent}"
        print(f"  {i:<3} {label:<45} {ostr:>10}")

    print("\n" + "=" * 60)
    print(f"VERDICT: {verdict}")
    print("=" * 60)

    if verdict == "ORPHANS_FOUND":
        print("\nSamples (first 5 per relation with orphans):")
        for key, info in orphans.items():
            if info.get("count"):
                print(f"\n  {key}  ({info['count']} orphans, match on {info['match_fields']}):")
                for s in info["samples"]:
                    print(f"    {s}")

    return 0 if verdict == "CLEAN" else (1 if verdict == "ORPHANS_FOUND" else 2)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)
