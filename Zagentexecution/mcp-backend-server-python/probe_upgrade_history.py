"""
probe_upgrade_history.py
========================
EMPIRICAL PROBE (read-only, P01 via SNC/SSO) of the SAP upgrade/support-package
forensic tables, to MEASURE the last 3 upgrades (complexity, timing, start).

We do NOT assume field names (CP-003): for each candidate table we first read
DD03L to get the real field list, then sample rows. Output drives the actual
measurement + companion.

Candidate forensic sources:
  PAT03      patch directory / history (which SPs/EhP applied)
  PAT01      current patch queue
  PAT02      patch queue (alt)
  CVERS      software component version + current SP level (state)
  CVERS_REF  component reference
  TPALOG     SPAM/tp action log (timestamps)
  UVERS      upgrade / release history
  SADL/...   (probed only if above thin)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

CANDIDATES = ["PAT03", "PAT01", "PAT02", "CVERS", "CVERS_REF", "TPALOG", "UVERS"]


def get_fields(conn, table):
    """Real field list from DD03L (POSITION-ordered), excluding .INCLUDE markers."""
    rows = rfc_read_paginated(
        conn, "DD03L",
        ["FIELDNAME", "POSITION", "ROLLNAME", "DATATYPE", "LENG"],
        f"TABNAME = '{table}'",
        batch_size=2000, throttle=0,
    )
    rows = [r for r in rows if r.get("FIELDNAME", "").strip()
            and not r["FIELDNAME"].startswith(".")]
    rows.sort(key=lambda r: int(r.get("POSITION", "0") or "0"))
    return rows


def main():
    conn = get_connection(system_id="P01")
    print("[OK] Connected to P01\n")

    report = {}
    for tbl in CANDIDATES:
        print("=" * 72)
        print(f"TABLE: {tbl}")
        print("=" * 72)
        try:
            fields = get_fields(conn, tbl)
        except Exception as e:
            print(f"  [DD03L error] {e}\n")
            report[tbl] = {"exists": False, "error": str(e)}
            continue

        if not fields:
            print("  (no DD03L entry -> table does not exist in this system)\n")
            report[tbl] = {"exists": False}
            continue

        fnames = [f["FIELDNAME"].strip() for f in fields]
        print(f"  {len(fnames)} fields:")
        for f in fields:
            print(f"    {f['FIELDNAME']:<20} {f.get('ROLLNAME',''):<14} "
                  f"{f.get('DATATYPE',''):<6} {f.get('LENG','')}")

        # sample data (all fields; helper auto-splits wide tables)
        try:
            data = rfc_read_paginated(conn, tbl, fnames, "",
                                      batch_size=200, throttle=0)
        except Exception as e:
            print(f"  [data read error] {e}\n")
            report[tbl] = {"exists": True, "fields": fnames, "error": str(e)}
            continue

        print(f"\n  ROW COUNT (first page cap 200): {len(data)}")
        for i, r in enumerate(data[:8]):
            print(f"    [{i}] " + " | ".join(
                f"{k}={v}" for k, v in r.items() if v.strip()))
        print()
        report[tbl] = {"exists": True, "n_fields": len(fnames),
                       "fields": fnames, "sample_rows": data[:8],
                       "rows_first_page": len(data)}

    conn.close()
    out = os.path.join(os.path.dirname(__file__), "probe_upgrade_history.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
    print(f"[SAVED] {out}")


if __name__ == "__main__":
    main()
