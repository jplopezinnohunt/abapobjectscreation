"""
Deep extraction of all 7 P01 open customizing requests.
Gets E070, E07T, E071, E071K + resolves table meanings for companion section.
Outputs JSON for HTML generation.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection


def read_table(conn, table, fields, options, max_rows=500):
    try:
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table,
            DELIMITER="|",
            ROWCOUNT=max_rows,
            FIELDS=[{"FIELDNAME": f} for f in fields],
            OPTIONS=[{"TEXT": o} for o in options],
        )
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
        return rows
    except Exception as e:
        return []


def main():
    conn = get_connection(system_id="P01")
    print("[OK] Connected to P01")

    transports = [
        "P01K950265", "P01K950267", "P01K950269",
        "P01K950271", "P01K950275", "P01K950277", "P01K950279",
    ]

    results = []

    for tr in transports:
        print(f"\nExtracting {tr}...")
        entry = {"trkorr": tr}

        # Header
        hdr = read_table(conn, "E070",
                         ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                         [f"TRKORR = '{tr}'"])
        entry["header"] = hdr[0] if hdr else {}

        # Description
        desc = read_table(conn, "E07T", ["TRKORR", "AS4TEXT", "LANGU"],
                          [f"TRKORR = '{tr}'"])
        entry["description"] = desc[0].get("AS4TEXT", "") if desc else ""

        # Tasks
        tasks = read_table(conn, "E070",
                           ["TRKORR", "STRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                           [f"STRKORR = '{tr}'"])
        entry["tasks"] = tasks

        # Task descriptions
        for t in tasks:
            tdesc = read_table(conn, "E07T", ["TRKORR", "AS4TEXT"],
                               [f"TRKORR = '{t['TRKORR']}'"])
            t["description"] = tdesc[0].get("AS4TEXT", "") if tdesc else ""

        # Objects from request + all tasks
        all_objects = []
        all_trkorrs = [tr] + [t["TRKORR"] for t in tasks]
        for tk in all_trkorrs:
            objs = read_table(conn, "E071",
                              ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME", "OBJFUNC", "LOCKFLAG"],
                              [f"TRKORR = '{tk}'"])
            all_objects.extend(objs)

        entry["objects"] = all_objects

        # Keys (E071K) for TABU/VDAT/TDAT/CDAT objects
        all_keys = []
        for tk in all_trkorrs:
            keys = read_table(conn, "E071K",
                              ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"],
                              [f"TRKORR = '{tk}'"],
                              max_rows=200)
            all_keys.extend(keys)
        entry["keys"] = all_keys

        results.append(entry)
        print(f"  {len(all_objects)} objects, {len(all_keys)} keys")

    # Save JSON
    out_path = os.path.join(os.path.dirname(__file__), "p01_open_requests_detail.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
