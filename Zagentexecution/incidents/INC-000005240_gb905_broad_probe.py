"""
INC-000005240 — GB905/GB921 BROAD probe
=========================================
Previous extraction filtered by SUBSTID='UNESCO' and got 0 rows — which is
either (a) no prerequisite data for UNESCO, or (b) the SUBSTID key uses a
different format in GB905/GB921 than in GB922. Also tests GB93/GB931 (validation
side), and GB92 without digit suffix.

Strategy:
  - Try each table with NO WHERE, ROWCOUNT=5000, see what comes back
  - Dump first 20 rows of each to understand schema
  - Filter client-side for anything matching 'UNESCO' / 'UNES'
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")

CANDIDATES = [
    # --- Substitution header candidates ---
    ("GB91",  []),    # classic substitution header
    ("GB01",  []),    # boolean class header
    # --- Validation header/steps ---
    ("GB931", []),    # validation steps with empty field list to get schema
    ("GB932", []),
    ("GB933", []),
    # --- Other possible linking tables ---
    ("GB00",  []),
    ("GB02",  []),
    # --- Substitution variants ---
    ("GB923", []),
    ("GBCALLPT", []),
]


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    results = {}
    for (table, fields) in CANDIDATES:
        print(f"=" * 80)
        print(f"Probing {table}")
        print("=" * 80)
        try:
            rows = rfc_read_paginated(
                guard, table=table, fields=fields,
                where="", batch_size=5000,
            )
            print(f"  Returned {len(rows)} rows")
            if rows:
                # Print schema (keys of first row)
                print(f"  Columns: {sorted(rows[0].keys())}")
                # First 3 rows
                for i, r in enumerate(rows[:3]):
                    print(f"    row {i}: {r}")
                # Filter for UNESCO/UNES
                matches = [r for r in rows
                           if any("UNES" in str(v).upper() for v in r.values())]
                print(f"  UNES/UNESCO matches (client-side filter): {len(matches)}")
                for r in matches[:20]:
                    print(f"    {r}")
                results[table] = {
                    "total_rows": len(rows),
                    "unes_matches": matches,
                    "sample_keys": sorted(rows[0].keys()) if rows else [],
                }
            else:
                results[table] = {"total_rows": 0, "unes_matches": [], "sample_keys": []}
        except Exception as e:
            print(f"  FAILED: {e}")
            results[table] = {"error": str(e)}

    OUT.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults: {OUT}")


if __name__ == "__main__":
    main()
