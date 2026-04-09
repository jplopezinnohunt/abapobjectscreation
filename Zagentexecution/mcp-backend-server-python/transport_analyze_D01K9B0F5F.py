"""
transport_analyze_D01K9B0F5F.py
===============================
Extract and analyze transport order D01K9B0F5F contents.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            print(f"  [WARN] {table}: {e}")
            return None
        raise


def run():
    conn = get_connection("D01")
    tr = "D01K9B0F5F"

    # ── E070 — Transport header ──
    print(f"{'='*70}")
    print(f"  TRANSPORT ORDER: {tr}")
    print(f"{'='*70}")

    e070 = safe_read(conn, "E070",
                     ["TRKORR", "TRFUNCTION", "TRSTATUS", "TARSYSTEM",
                      "AS4USER", "AS4DATE", "AS4TIME", "STRKORR"],
                     f"TRKORR = '{tr}'")
    if e070:
        h = e070[0]
        print(f"  Type: {h.get('TRFUNCTION','').strip()}")
        print(f"  Status: {h.get('TRSTATUS','').strip()}")
        print(f"  Target: {h.get('TARSYSTEM','').strip()}")
        print(f"  Owner: {h.get('AS4USER','').strip()}")
        print(f"  Date: {h.get('AS4DATE','').strip()} {h.get('AS4TIME','').strip()}")
        parent = h.get("STRKORR", "").strip()
        if parent:
            print(f"  Parent: {parent}")

    # ── E07T — Description ──
    e07t = safe_read(conn, "E07T",
                     ["TRKORR", "AS4TEXT", "LANESSION"],
                     f"TRKORR = '{tr}'")
    if e07t:
        for row in e07t:
            print(f"  Description: {row.get('AS4TEXT','').strip()}")

    # ── E070 — Tasks (children) ──
    tasks = safe_read(conn, "E070",
                      ["TRKORR", "TRFUNCTION", "TRSTATUS", "AS4USER", "AS4DATE"],
                      f"STRKORR = '{tr}'")
    if tasks:
        print(f"\n  Tasks ({len(tasks)}):")
        task_ids = []
        for t in tasks:
            tid = t.get("TRKORR", "").strip()
            task_ids.append(tid)
            # Get task description
            t_desc = safe_read(conn, "E07T",
                               ["TRKORR", "AS4TEXT"],
                               f"TRKORR = '{tid}'")
            desc = ""
            if t_desc:
                desc = t_desc[0].get("AS4TEXT", "").strip()
            print(f"    {tid} | {t.get('AS4USER','').strip()} | "
                  f"{t.get('TRSTATUS','').strip()} | {desc}")
    else:
        task_ids = [tr]

    # ── E071 — Object list ──
    print(f"\n  {'='*70}")
    print(f"  OBJECT LIST")
    print(f"  {'='*70}")

    all_objects = []
    search_ids = [tr] + task_ids
    for tid in search_ids:
        e071 = safe_read(conn, "E071",
                         ["TRKORR", "AS4POS", "PGMID", "OBJECT", "OBJ_NAME",
                          "OBJFUNC", "LOCKFLAG"],
                         f"TRKORR = '{tid}'")
        if e071:
            all_objects.extend(e071)

    if not all_objects:
        print("  No objects found")
        conn.close()
        return

    print(f"\n  Total objects: {len(all_objects)}")

    # Group by PGMID/OBJECT
    groups = {}
    for obj in all_objects:
        pgmid = obj.get("PGMID", "").strip()
        objtype = obj.get("OBJECT", "").strip()
        name = obj.get("OBJ_NAME", "").strip()
        func = obj.get("OBJFUNC", "").strip()
        key = f"{pgmid}/{objtype}"
        if key not in groups:
            groups[key] = []
        groups[key].append({"name": name, "func": func})

    for key in sorted(groups.keys()):
        entries = groups[key]
        print(f"\n  {key} ({len(entries)} entries):")
        for e in sorted(entries, key=lambda x: x["name"])[:50]:
            func_tag = f" [{e['func']}]" if e["func"] else ""
            print(f"    {e['name']}{func_tag}")
        if len(entries) > 50:
            print(f"    ... and {len(entries)-50} more")

    # ── E071K — Key entries (customizing table contents) ──
    print(f"\n  {'='*70}")
    print(f"  KEY ENTRIES (table contents being transported)")
    print(f"  {'='*70}")

    all_keys = []
    for tid in search_ids:
        e071k = safe_read(conn, "E071K",
                          ["TRKORR", "PGMID", "OBJECT", "OBJNAME", "MASTERTYPE",
                           "MASTERNAME", "TABKEY"],
                          f"TRKORR = '{tid}'")
        if e071k:
            all_keys.extend(e071k)

    if all_keys:
        print(f"\n  Total key entries: {len(all_keys)}")

        # Group by table name
        tables = {}
        for k in all_keys:
            tbl = k.get("MASTERNAME", "").strip() or k.get("OBJNAME", "").strip()
            tabkey = k.get("TABKEY", "").strip()
            if tbl not in tables:
                tables[tbl] = []
            tables[tbl].append(tabkey)

        for tbl in sorted(tables.keys()):
            keys = tables[tbl]
            print(f"\n  {tbl} ({len(keys)} keys):")
            for k in sorted(keys)[:30]:
                print(f"    {k}")
            if len(keys) > 30:
                print(f"    ... and {len(keys)-30} more")
    else:
        print("  No key entries found")

    conn.close()


if __name__ == "__main__":
    run()
