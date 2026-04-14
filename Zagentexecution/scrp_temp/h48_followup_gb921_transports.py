"""H48 follow-up:
- GB921 UNESCO steps (completes KU-031)
- GB905 for boolean rule metadata
- E071/E071K transport history for YRGGBS00 (alternative to VRSD for KU-030)
"""
import sys, os, json
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

    print("=" * 60)
    print("GB921 — substitution step to CONDID linkage (UNESCO)")
    print("=" * 60)
    rows, fields = read(guard, "GB921", options=[{"TEXT": "SUBSTID = 'UNESCO'"}])
    if isinstance(fields, list):
        cols = [f["FIELDNAME"] for f in fields]
        print(f"Columns: {cols}")
        print(f"Rows for SUBSTID='UNESCO': {len(rows) if rows else 0}")
        for row in (rows or []):
            print(f"  {row['WA']}")
    else:
        print(f"Error: {fields}")

    print()
    print("=" * 60)
    print("GB921 — all distinct SUBSTID (sample 50)")
    print("=" * 60)
    rows, _ = read(guard, "GB921", fields=[{"FIELDNAME": "SUBSTID"}, {"FIELDNAME": "SUBSEQNR"}, {"FIELDNAME": "CONDID"}], rowcount=500)
    if rows:
        from collections import Counter
        substids = Counter(r["WA"].split()[0] if r["WA"].strip() else "" for r in rows)
        print(f"Total rows sampled: {len(rows)}")
        for sid, cnt in substids.most_common(15):
            print(f"  {sid}: {cnt}")

    print()
    print("=" * 60)
    print("GB905 — boolean rule metadata for UNES-related BOOLIDs")
    print("=" * 60)
    rows, fields = read(guard, "GB905", options=[{"TEXT": "BOOLID LIKE '%UNES%' OR BOOLID LIKE '3IIEP%' OR BOOLID LIKE '2IIEP%'"}])
    if isinstance(fields, list):
        cols = [f["FIELDNAME"] for f in fields]
        print(f"Columns: {cols}")
        print(f"Rows: {len(rows) if rows else 0}")
        for row in (rows or [])[:10]:
            print(f"  {row['WA']}")

    print()
    print("=" * 60)
    print("GB931 — VALIDATION step to CONDID linkage for VALID='UNES'")
    print("=" * 60)
    rows, fields = read(guard, "GB931", options=[{"TEXT": "VALID = 'UNES'"}])
    if isinstance(fields, list):
        cols = [f["FIELDNAME"] for f in fields]
        print(f"Columns: {cols}")
        print(f"Rows for VALID='UNES': {len(rows) if rows else 0}")
        for row in (rows or [])[:15]:
            print(f"  {row['WA']}")

    print()
    print("=" * 60)
    print("E071 — transports containing YRGGBS00 (KU-030 alternative)")
    print("=" * 60)
    rows, fields = read(guard, "E071", options=[{"TEXT": "OBJ_NAME = 'YRGGBS00' AND OBJECT = 'REPS'"}])
    if isinstance(fields, list):
        cols = [f["FIELDNAME"] for f in fields]
        print(f"Columns: {cols[:10]}")
        print(f"Transports with YRGGBS00 (REPS): {len(rows) if rows else 0}")
        for row in (rows or [])[:20]:
            print(f"  {row['WA'][:140]}")

    print()
    print("=" * 60)
    print("E070 — transport header metadata for YRGGBS00 transports")
    print("=" * 60)
    # get TRKORR list from prior
    trkorrs = []
    for row in (rows or []):
        parts = row["WA"].split()
        if parts:
            trkorrs.append(parts[1] if len(parts) > 1 else parts[0])
    # query E070 for those trkorrs
    for trkorr in trkorrs[:20]:
        tk = trkorr.strip()
        if not tk:
            continue
        r2, _ = read(guard, "E070", options=[{"TEXT": f"TRKORR = '{tk}'"}], rowcount=5)
        if r2:
            for row in r2:
                print(f"  {row['WA'][:180]}")

    guard.close()


if __name__ == "__main__":
    main()
