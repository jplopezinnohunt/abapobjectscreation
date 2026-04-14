"""H48 deep: transport history dates + GB901 boolean expressions for UNESCO substitution prereqs.

- Goal 1 (KU-030): find the transport that commented IF bseg_xref1 = space. Look for XREF1/UXR1/xref keywords in E07T descriptions on YRGGBS00 transports.
- Goal 2 (KU-031): for UNESCO step 005 (XREF1) = CONDID '3UNESCO#005', get the boolean expression from GB901.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard


def read(guard, table, options=None, fields=None, rowcount=200):
    try:
        kw = {"QUERY_TABLE": table, "ROWCOUNT": rowcount, "FIELDS": fields or []}
        if options:
            kw["OPTIONS"] = options
        r = guard.call("RFC_READ_TABLE", **kw)
        return r.get("DATA", []), r.get("FIELDS", [])
    except Exception as e:
        return None, str(e)


def main():
    guard = ConnectionGuard("P01")
    guard.connect()

    # Step 1: Get 57 TRKORRs + E070 headers (dates + users) — all at once
    print("=" * 60)
    print("YRGGBS00 transport history (E070 headers sorted by date)")
    print("=" * 60)
    rows, _ = read(guard, "E071",
                   options=[{"TEXT": "OBJ_NAME = 'YRGGBS00' AND OBJECT = 'REPS'"}],
                   fields=[{"FIELDNAME": "TRKORR"}],
                   rowcount=200)
    trkorrs = sorted({r["WA"].strip() for r in (rows or [])})
    print(f"Distinct transports: {len(trkorrs)}")

    # E070 in batches of 10 for WHERE IN clause performance
    all_headers = []
    for t in trkorrs:
        r2, _ = read(guard, "E070",
                     options=[{"TEXT": f"TRKORR = '{t}'"}],
                     fields=[{"FIELDNAME": "TRKORR"},
                             {"FIELDNAME": "TRFUNCTION"},
                             {"FIELDNAME": "TRSTATUS"},
                             {"FIELDNAME": "AS4USER"},
                             {"FIELDNAME": "AS4DATE"},
                             {"FIELDNAME": "AS4TIME"}],
                     rowcount=3)
        if r2:
            for row in r2:
                all_headers.append(row["WA"])
    # Sort by AS4DATE (extract from row string, positions depend on field widths)
    # Print top 40 most recent
    all_headers.sort()
    print(f"\nAll {len(all_headers)} headers (sorted by TRKORR -> roughly chronological):")
    for h in all_headers:
        print(f"  {h}")

    # Step 2: Get E07T descriptions — they often say what the change was
    print()
    print("=" * 60)
    print("YRGGBS00 transport descriptions (E07T)")
    print("=" * 60)
    for t in trkorrs:
        r3, _ = read(guard, "E07T",
                     options=[{"TEXT": f"TRKORR = '{t}'"}],
                     fields=[{"FIELDNAME": "TRKORR"},
                             {"FIELDNAME": "AS4TEXT"}],
                     rowcount=3)
        if r3:
            for row in r3:
                txt = row["WA"]
                if "XREF" in txt.upper() or "UXR" in txt.upper() or "GUARD" in txt.upper() or "SUBST" in txt.upper() or "USR05" in txt.upper() or "Y_USERFO" in txt.upper() or "SUBSTITUT" in txt.upper():
                    print(f"  [FLAG] {txt}")
                else:
                    print(f"        {txt[:180]}")

    # Step 3: GB901 — boolean expression for UNESCO step 5 prereq = '3UNESCO#005'
    print()
    print("=" * 60)
    print("GB901 — UNESCO substitution CONDID prerequisites (UXR1 = step 005)")
    print("=" * 60)
    rows, fields = read(guard, "GB901",
                        options=[{"TEXT": "BOOLID LIKE '3UNESCO%'"}],
                        rowcount=200)
    if isinstance(fields, list):
        cols = [f["FIELDNAME"] for f in fields]
        print(f"Columns: {cols}")
        print(f"Rows: {len(rows) if rows else 0}")
        for row in (rows or [])[:40]:
            print(f"  {row['WA']}")

    # Step 4: verify the missing piece — step 5 specific (XREF1)
    print()
    print("=" * 60)
    print("GB901 — CONDID '3UNESCO#005' (prerequisite for UXR1 XREF1 substitution)")
    print("=" * 60)
    rows, _ = read(guard, "GB901",
                   options=[{"TEXT": "BOOLID = '3UNESCO#005'"}],
                   rowcount=50)
    if rows:
        for row in rows:
            print(f"  {row['WA']}")
    else:
        print("  NO PREREQUISITE — step 005 fires unconditionally")

    # Step 6 (XREF2)
    print()
    print("=" * 60)
    print("GB901 — CONDID '3UNESCO#006' (prerequisite for UXR2 XREF2)")
    print("=" * 60)
    rows, _ = read(guard, "GB901",
                   options=[{"TEXT": "BOOLID = '3UNESCO#006'"}],
                   rowcount=50)
    if rows:
        for row in rows:
            print(f"  {row['WA']}")
    else:
        print("  NO PREREQUISITE — step 006 fires unconditionally")

    guard.close()


if __name__ == "__main__":
    main()
