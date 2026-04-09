"""
Check D01 for open customizing requests — compare with P01 findings.
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
    conn = get_connection(system_id="D01")
    print("[OK] Connected to D01\n")

    # Open customizing requests in D01
    print("=" * 70)
    print("D01 - Open customizing requests (TRFUNCTION='W', TRSTATUS='D')")
    print("=" * 70)
    requests = read_table(conn, "E070",
                          ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                          ["TRFUNCTION = 'W'", "AND TRSTATUS = 'D'"])

    if isinstance(requests, str):
        print(f"  Error: {requests[:200]}")
        return

    print(f"  Found {len(requests)} open customizing requests in D01\n")

    for tr in requests:
        trkorr = tr["TRKORR"]
        # Description
        desc = read_table(conn, "E07T", ["TRKORR", "AS4TEXT"],
                          [f"TRKORR = '{trkorr}'"])
        desc_text = desc[0].get("AS4TEXT", "") if isinstance(desc, list) and desc else ""

        # Object count
        objects = read_table(conn, "E071",
                             ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                             [f"TRKORR = '{trkorr}'"])
        # Also check tasks
        tasks = read_table(conn, "E070",
                           ["TRKORR", "AS4USER"],
                           [f"STRKORR = '{trkorr}'"])
        task_obj_count = 0
        if isinstance(tasks, list):
            for t in tasks:
                tobj = read_table(conn, "E071",
                                  ["TRKORR", "PGMID", "OBJECT", "OBJ_NAME"],
                                  [f"TRKORR = '{t['TRKORR']}'"])
                if isinstance(tobj, list):
                    task_obj_count += len(tobj)

        obj_count = (len(objects) if isinstance(objects, list) else 0) + task_obj_count

        print(f"  {trkorr} | {tr.get('AS4USER',''):15s} | {tr.get('AS4DATE','')} | {obj_count:3d} objects | {desc_text}")

    # Client settings
    print("\n" + "=" * 70)
    print("D01 - Client settings (T000)")
    print("=" * 70)
    clients = read_table(conn, "T000",
                         ["MANDT", "MTEXT", "CCCATEGORY", "CCCORACTIV", "CCNOCLIIND"],
                         [])
    if isinstance(clients, list):
        for c in clients:
            print(f"  Client {c.get('MANDT','?')}: {c.get('MTEXT','?')} | Category={c.get('CCCATEGORY','?')} | Recording={c.get('CCCORACTIV','?')} | Protection={c.get('CCNOCLIIND','?')}")

    # Comparison summary
    print("\n" + "=" * 70)
    print("COMPARISON: P01 vs D01")
    print("=" * 70)
    print(f"  P01: 7 open customizing requests")
    print(f"  D01: {len(requests)} open customizing requests")

    # Check if same views/objects appear in both
    p01_objects = [
        "V_T77HRFPM_CLSNG", "TABADRH", "VV_FMTABADRH_REASSIGNMENT",
        "VV_FMREAS_RULES_REASSIGNMENT", "V_FMYC_CFC1_A",
        "VV_FMABP_CNTRL_BFC", "VV_FMABP_ED_DEF_BFC", "V_T100C",
        "V_T163K", "V_VBWF15", "PDWS_LSO", "PDST_LSO",
        "VC_T012N", "V_001_B", "ADDRESS", "ADDRESS_4.6"
    ]
    print(f"\n  P01 objects in open requests: {', '.join(p01_objects)}")
    print(f"\n  Checking if same objects appear in D01 open requests...")

    d01_all_objects = set()
    for tr in requests:
        trkorr = tr["TRKORR"]
        objects = read_table(conn, "E071",
                             ["PGMID", "OBJECT", "OBJ_NAME"],
                             [f"TRKORR = '{trkorr}'"])
        if isinstance(objects, list):
            for o in objects:
                d01_all_objects.add(o.get("OBJ_NAME", ""))
        tasks = read_table(conn, "E070", ["TRKORR"],
                           [f"STRKORR = '{trkorr}'"])
        if isinstance(tasks, list):
            for t in tasks:
                tobj = read_table(conn, "E071",
                                  ["PGMID", "OBJECT", "OBJ_NAME"],
                                  [f"TRKORR = '{t['TRKORR']}'"])
                if isinstance(tobj, list):
                    for o in tobj:
                        d01_all_objects.add(o.get("OBJ_NAME", ""))

    overlap = set(p01_objects) & d01_all_objects
    if overlap:
        print(f"  OVERLAP (same objects in both): {', '.join(overlap)}")
    else:
        print(f"  No overlap - P01 and D01 have different objects in open requests")


if __name__ == "__main__":
    main()
