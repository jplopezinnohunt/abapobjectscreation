"""
Check P01 for open Customizing Cockpit data extraction requests.
These block transport imports (SAP Notes 1081287, 1083709, 328181).

Investigation targets:
  - SCPR_CTRL / SCPR_CTXT  — BC Set control records
  - SCC_TMS_HDR / SCC_TMS_ITEM — SCC extraction monitoring
  - E070 with TRFUNCTION='T' — Copies/extractions in CTS
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

def probe_table(conn, table, fields=None, options=None, max_rows=100):
    """Try to read a table; return rows or error string."""
    try:
        params = {
            "QUERY_TABLE": table,
            "DELIMITER": "|",
            "ROWCOUNT": max_rows,
        }
        if fields:
            params["FIELDS"] = [{"FIELDNAME": f} for f in fields]
        if options:
            params["OPTIONS"] = [{"TEXT": o} for o in options]

        result = conn.call("RFC_READ_TABLE", **params)
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
        return fnames, rows
    except Exception as e:
        return None, str(e)


def main():
    print("=" * 70)
    print("P01 — Open Data Extraction Requests Investigation")
    print("=" * 70)

    conn = get_connection(system_id="P01")
    print("[OK] Connected to P01\n")

    # 1. Check SCPR_CTRL -- BC Set requests
    print("-" * 50)
    print("1. SCPR_CTRL -- BC Set control records (open status)")
    print("-" * 50)
    fnames, rows = probe_table(
        conn, "SCPR_CTRL",
        fields=["SCPRNAME", "SCPRVERS", "SCPRSTAT", "SCPRUSER", "SCPRDATE"],
        options=["SCPRSTAT NE 'A'"]  # Not 'Activated' = potentially open
    )
    if isinstance(rows, str):
        print(f"  [SKIP] {rows}")
    elif rows:
        print(f"  Found {len(rows)} non-activated BC Sets:")
        for r in rows[:20]:
            print(f"    {r}")
    else:
        print("  No open BC Sets found.")

    # -- 2. Check SCC_TMS_HDR — SCC extraction header --
    print("\n" + "-" * 50)
    print("2. SCC_TMS_HDR — SCC copy/extraction monitor")
    print("-" * 50)
    fnames, rows = probe_table(conn, "SCC_TMS_HDR")
    if isinstance(rows, str):
        print(f"  [SKIP] Table doesn't exist or no auth: {rows[:120]}")
    elif rows:
        print(f"  Found {len(rows)} extraction header records:")
        for r in rows[:20]:
            print(f"    {r}")
    else:
        print("  No records found.")

    # -- 3. Check E070 for copy/extraction transports --
    print("\n" + "-" * 50)
    print("3. E070 — Transports with function 'T' (copies/extractions)")
    print("-" * 50)
    fnames, rows = probe_table(
        conn, "E070",
        fields=["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE", "AS4TEXT"],
        options=["TRFUNCTION = 'T'", "AND TRSTATUS NE 'R'"]  # Not released = open
    )
    if isinstance(rows, str):
        # AS4TEXT might not be in E070, retry without it
        fnames, rows = probe_table(
            conn, "E070",
            fields=["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
            options=["TRFUNCTION = 'T'", "AND TRSTATUS NE 'R'"]
        )
    if isinstance(rows, str):
        print(f"  [SKIP] {rows[:120]}")
    elif rows:
        print(f"  Found {len(rows)} open copy/extraction transports:")
        for r in rows[:20]:
            print(f"    {r}")
    else:
        print("  No open extraction transports.")

    # -- 4. Check CCDEFAULT — Customizing client settings --
    print("\n" + "-" * 50)
    print("4. T000 — Client settings (recording/extraction flags)")
    print("-" * 50)
    fnames, rows = probe_table(
        conn, "T000",
        fields=["MANDT", "MTEXT", "CCCATEGORY", "CCCORACTIV", "CCNOCLIIND"]
    )
    if isinstance(rows, str):
        print(f"  [SKIP] {rows[:120]}")
    elif rows:
        for r in rows:
            print(f"  Client {r.get('MANDT','?')}: {r.get('MTEXT','?')} "
                  f"| Category={r.get('CCCATEGORY','?')} "
                  f"| Recording={r.get('CCCORACTIV','?')} "
                  f"| Protection={r.get('CCNOCLIIND','?')}")

    # -- 5. Check SCDO_CHANGERQ — open change requests for customizing --
    print("\n" + "-" * 50)
    print("5. E070 — Open customizing requests (TRFUNCTION='W')")
    print("-" * 50)
    fnames, rows = probe_table(
        conn, "E070",
        fields=["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
        options=["TRFUNCTION = 'W'", "AND TRSTATUS = 'D'"]  # Modifiable customizing
    )
    if isinstance(rows, str):
        print(f"  [SKIP] {rows[:120]}")
    elif rows:
        print(f"  Found {len(rows)} open customizing requests:")
        for r in rows[:20]:
            print(f"    {r}")
    else:
        print("  No open customizing requests.")

    # -- 6. Probe SCC3-related tables --
    print("\n" + "-" * 50)
    print("6. Probing SCC3-related tables (extraction workbench)")
    print("-" * 50)
    for tbl in ["SCC_EXTR_HDR", "SCC_EXTRACT", "SCC_HISTORY", "SCCMONI", "SCC_MONI"]:
        fnames, rows = probe_table(conn, tbl, max_rows=10)
        if isinstance(rows, str):
            print(f"  {tbl}: [not found / no auth]")
        else:
            print(f"  {tbl}: {len(rows)} records found")
            for r in rows[:5]:
                print(f"    {r}")

    print("\n" + "=" * 70)
    print("Investigation complete. Review findings above.")
    print("Resolution: Transaction SCC3 → process or delete open requests")
    print("=" * 70)


if __name__ == "__main__":
    main()
