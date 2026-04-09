"""
Analyze contents of 7 open customizing requests in P01.
Check E071 (object list) and E07T (descriptions) for each transport.
"""
import sys, os
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
        return str(e)


def main():
    conn = get_connection(system_id="P01")
    print("[OK] Connected to P01\n")

    transports = [
        "P01K950265", "P01K950267", "P01K950269",
        "P01K950271", "P01K950275", "P01K950277", "P01K950279",
    ]

    for tr in transports:
        print("=" * 70)
        print(f"Transport: {tr}")
        print("=" * 70)

        # Get description from E07T
        desc = read_table(conn, "E07T", ["TRKORR", "AS4TEXT", "LANGU"],
                          [f"TRKORR = '{tr}'"])
        if isinstance(desc, list) and desc:
            print(f"  Description: {desc[0].get('AS4TEXT', '?')}")
        else:
            print(f"  Description: (none)")

        # Get tasks (sub-requests) from E070
        tasks = read_table(conn, "E070",
                           ["TRKORR", "STRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                           [f"STRKORR = '{tr}'"])
        if isinstance(tasks, list) and tasks:
            print(f"  Tasks ({len(tasks)}):")
            for t in tasks:
                status_map = {"D": "Modifiable", "L": "Protected", "R": "Released", "N": "Released(import)"}
                st = status_map.get(t.get("TRSTATUS", ""), t.get("TRSTATUS", "?"))
                print(f"    {t['TRKORR']} | User: {t.get('AS4USER','')} | Status: {st} | Date: {t.get('AS4DATE','')}")

                # Get task description
                tdesc = read_table(conn, "E07T", ["TRKORR", "AS4TEXT"],
                                   [f"TRKORR = '{t['TRKORR']}'"])
                if isinstance(tdesc, list) and tdesc:
                    print(f"      Desc: {tdesc[0].get('AS4TEXT', '')}")
        else:
            print(f"  Tasks: none")

        # Get objects from E071
        objects = read_table(conn, "E071",
                             ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                             [f"TRKORR LIKE '{tr[:4]}%'",
                              f"AND STRKORR = '{tr}'"])
        # Also check direct objects on the request itself
        objects_direct = read_table(conn, "E071",
                                    ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                                    [f"TRKORR = '{tr}'"])

        all_objects = []
        if isinstance(objects, list):
            all_objects.extend(objects)
        if isinstance(objects_direct, list):
            all_objects.extend(objects_direct)

        # Also get objects from tasks
        if isinstance(tasks, list):
            for t in tasks:
                task_obj = read_table(conn, "E071",
                                      ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                                      [f"TRKORR = '{t['TRKORR']}'"])
                if isinstance(task_obj, list):
                    all_objects.extend(task_obj)

        # Deduplicate
        seen = set()
        unique_objects = []
        for o in all_objects:
            key = f"{o.get('TRKORR','')}-{o.get('PGMID','')}-{o.get('OBJECT','')}-{o.get('OBJ_NAME','')}"
            if key not in seen:
                seen.add(key)
                unique_objects.append(o)

        if unique_objects:
            print(f"  Objects ({len(unique_objects)}):")
            for o in unique_objects:
                print(f"    {o.get('PGMID',''):4s} | {o.get('OBJECT',''):10s} | {o.get('OBJ_NAME','')}")
        else:
            print(f"  Objects: EMPTY (no objects recorded)")

        # Get keys from E071K if any customizing entries
        has_customizing = any(o.get("PGMID") == "R3TR" and o.get("OBJECT") == "TABU"
                              for o in unique_objects)
        if has_customizing:
            for o in unique_objects:
                if o.get("OBJECT") == "TABU":
                    keys = read_table(conn, "E071K",
                                      ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "TABKEY"],
                                      [f"TRKORR = '{o['TRKORR']}'",
                                       f"AND OBJNAME = '{o.get('OBJ_NAME','')}'"],
                                      max_rows=20)
                    if isinstance(keys, list) and keys:
                        print(f"  Table keys for {o.get('OBJ_NAME','')}:")
                        for k in keys:
                            print(f"    Key: {k.get('TABKEY', '')}")

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Empty transports = safe to delete (SE01 -> Delete Request)")
    print("Transports with objects = review with owner before releasing/deleting")


if __name__ == "__main__":
    main()
