"""
extract_spau_2024_detail.py
==========================
Object-by-object breakdown of the 2024-07 SPAU burden (the heaviest upgrade):
which custom-modified objects were re-adjusted, by object type and by package
(DEVCLASS) = where the upgrade fragility concentrates.

Source: smodilog (Gold DB) SPAU-flagged rows -> their adjustment transport
(TRKORR) dated via E070.AS4DATE in the 2024-07 window. DEVCLASS from TADIR.
Read-only P01 SNC/SSO, single-call reads.
"""
import sys, os, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
BIG = 1_000_000
WIN = ("20240701", "20240715")   # 2024-07 upgrade window


def read_full(conn, table, fields, where=""):
    return rfc_read_paginated(conn, table, fields, where, batch_size=BIG, throttle=0)


def in_clauses(field, values, width=68):
    """Build RFC_READ_TABLE OPTIONS for `field IN ('a','b',...)` split <=72 chars/line."""
    opts, line, first = [], f"{field} IN (", True
    for v in values:
        tok = ("" if first else ",") + f"'{v}'"
        if len(line) + len(tok) > width:
            opts.append({"TEXT": line}); line = "   " + (tok[1:] if tok[0] == "," else tok)
        else:
            line += tok
        first = False
    line += ")"
    opts.append({"TEXT": line})
    return opts


def main():
    db = sqlite3.connect(GOLD); db.row_factory = sqlite3.Row
    smod = [dict(r) for r in db.execute(
        "SELECT * FROM smodilog WHERE TRIM(SPAU)<>'' AND TRIM(TRKORR)<>''")]
    print(f"SPAU-flagged modifications with a transport: {len(smod)}")

    conn = get_connection("P01")
    # transports released in the 2024-07 window
    e070 = read_full(conn, "E070", ["TRKORR", "AS4DATE", "AS4USER"],
                     [{"TEXT": f"AS4DATE >= '{WIN[0]}'"},
                      {"TEXT": f"AND AS4DATE <= '{WIN[1]}'"}])
    win_trk = {r["TRKORR"]: r for r in e070}
    print(f"transports released in {WIN[0]}-{WIN[1]}: {len(win_trk)}")

    objs = [r for r in smod if r["TRKORR"] in win_trk]
    print(f"SPAU adjustment records attributed to 2024-07: {len(objs)}")

    # distinct main objects
    distinct = sorted(set((r["OBJ_TYPE"].strip(), r["OBJ_NAME"].strip())
                          for r in objs if r["OBJ_NAME"].strip()))
    print(f"distinct objects: {len(distinct)}")

    # DEVCLASS via TADIR (per-name, best-effort; namespace names can break the WHERE parser)
    names = sorted(set(n for _, n in distinct))
    dev = {}
    for n in names:
        safe = n.replace("'", "''")
        try:
            rows = read_full(conn, "TADIR", ["OBJECT", "OBJ_NAME", "DEVCLASS"],
                             f"OBJ_NAME = '{safe}'")
            if rows:
                dev[n] = rows[0]["DEVCLASS"].strip()
        except Exception:
            pass  # skip names the RFC WHERE parser rejects
    conn.close()
    print(f"DEVCLASS resolved for {len(dev)}/{len(names)} objects")

    # ---- analysis ----
    by_type = Counter(t for t, _ in distinct)
    by_user = Counter(r["MOD_USER"].strip() for r in objs if r["MOD_USER"].strip())
    by_dev = Counter(dev.get(n, "(unknown)") for _, n in distinct)
    # year of original modification (how old is the custom code being re-adjusted)
    by_modyr = Counter(r["MOD_DATE"][:4] for r in objs
                       if r["MOD_DATE"].strip() and r["MOD_DATE"] != "00000000")

    print("\n=== BY OBJECT TYPE (distinct objects) ===")
    for k, v in by_type.most_common():
        print(f"   {k:<6} {v}")
    print("\n=== BY PACKAGE / DEVCLASS (top 15) ===")
    for k, v in by_dev.most_common(15):
        print(f"   {k:<22} {v}")
    print("\n=== BY MODIFIER (top 10) ===")
    for k, v in by_user.most_common(10):
        print(f"   {k:<14} {v}")
    print("\n=== ORIGINAL MODIFICATION YEAR (age of custom code) ===")
    for k in sorted(by_modyr, reverse=True):
        print(f"   {k}: {by_modyr[k]}")

    print("\n=== SAMPLE OBJECTS (type | name | package) ===")
    seen = set()
    for t, n in distinct:
        if t not in seen or list(by_type).index(t) < 3:
            print(f"   {t:<6} {n:<32} {dev.get(n,'?')}")
            seen.add(t)
        if len(seen) > 40:
            break

    out = {
        "window": "2024-07", "adjustment_records": len(objs),
        "distinct_objects": len(distinct),
        "by_object_type": dict(by_type.most_common()),
        "by_package": dict(by_dev.most_common(20)),
        "by_modifier": dict(by_user.most_common(12)),
        "by_modification_year": dict(sorted(by_modyr.items(), reverse=True)),
        "objects": [{"type": t, "name": n, "package": dev.get(n, "")} for t, n in distinct],
    }
    p = os.path.join(os.path.dirname(__file__), "spau_2024_detail.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    # persist objects to Gold DB
    db.execute("DROP TABLE IF EXISTS spau_2024_objects")
    db.execute("CREATE TABLE spau_2024_objects (obj_type TEXT, obj_name TEXT, package TEXT)")
    db.executemany("INSERT INTO spau_2024_objects VALUES (?,?,?)",
                   [(t, n, dev.get(n, "")) for t, n in distinct])
    db.commit(); db.close()
    print(f"\n[SAVED] {p} + Gold DB table spau_2024_objects")


if __name__ == "__main__":
    main()
