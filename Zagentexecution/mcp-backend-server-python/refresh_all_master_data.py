"""
Full refresh: PROJ, PRPS, CSKS for all 9 institutes from P01 LIVE.
Overwrites Gold DB tables proj, prps, CSKS.

Adds CSKT (cost center texts) too.
"""
import sys
import sqlite3
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # type: ignore

REPO = HERE.parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
INSTITUTES = ["MGIE", "IBE", "ICBA", "ICTP", "IIEP", "UIS", "UIL", "UBO", "UNES"]


def chunked_read(g, table, fields, where, label, page=30000):
    rows = []
    skip = 0
    while True:
        try:
            res = g.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table,
                FIELDS=[{"FIELDNAME": f} for f in fields],
                OPTIONS=[{"TEXT": where}] if where else [],
                DELIMITER="|",
                ROWCOUNT=page,
                ROWSKIPS=skip,
            )
        except Exception as e:
            msg = str(e)
            if "TABLE_WITHOUT_DATA" in msg:
                break
            print(f"  [{label} skip={skip}] ERR: {msg[:120]}")
            break
        batch = res.get("DATA", [])
        for d in batch:
            wa = d["WA"].split("|")
            rows.append({f: wa[i].strip() if i < len(wa) else "" for i, f in enumerate(fields)})
        if len(batch) < page:
            break
        skip += page
    return rows


def main():
    g = get_connection("P01")
    print("Connected P01.")

    # ----- PROJ -----
    print("\n[PROJ]")
    proj = []
    for inst in INSTITUTES:
        rows = chunked_read(g, "PROJ",
                            ["VBUKR", "PSPID", "POST1", "VERNR", "ERDAT", "PSPNR"],
                            f"VBUKR = '{inst}'", f"PROJ[{inst}]")
        print(f"  [{inst}] {len(rows)}")
        proj.extend(rows)
    print(f"  PROJ total: {len(proj)}")

    # ----- PRPS -----
    print("\n[PRPS]")
    prps = []
    for inst in INSTITUTES:
        rows = chunked_read(g, "PRPS",
                            ["PBUKR", "POSID", "POST1", "VERNR", "ERDAT", "PSPHI", "PSPNR", "OBJNR"],
                            f"PBUKR = '{inst}'", f"PRPS[{inst}]")
        print(f"  [{inst}] {len(rows)}")
        prps.extend(rows)
    print(f"  PRPS total: {len(prps)}")

    # ----- CSKS + CSKT -----
    print("\n[CSKS]")
    csks = []
    for inst in INSTITUTES:
        rows = chunked_read(g, "CSKS",
                            ["KOKRS", "KOSTL", "DATBI", "DATAB", "BUKRS", "KOSAR", "VERAK", "ERSDA", "USNAM"],
                            f"BUKRS = '{inst}'", f"CSKS[{inst}]")
        print(f"  [{inst}] {len(rows)}")
        csks.extend(rows)
    print(f"  CSKS total: {len(csks)}")

    print("\n[CSKT — texts per KOKRS]")
    cskt = []
    kokrs_set = sorted({r["KOKRS"] for r in csks if r["KOKRS"]})
    for kk in kokrs_set:
        rows = chunked_read(g, "CSKT",
                            ["KOKRS", "KOSTL", "DATBI", "KTEXT", "LTEXT"],
                            f"KOKRS = '{kk}' AND SPRAS = 'E'", f"CSKT[{kk}]")
        print(f"  [{kk}] {len(rows)}")
        cskt.extend(rows)
    print(f"  CSKT total: {len(cskt)}")

    # Enrich CSKS with text
    txt_map = {(r["KOKRS"], r["KOSTL"], r["DATBI"]): r for r in cskt}
    for r in csks:
        t = txt_map.get((r["KOKRS"], r["KOSTL"], r["DATBI"]))
        r["KTEXT"] = t.get("KTEXT", "") if t else ""
        r["LTEXT"] = t.get("LTEXT", "") if t else ""

    g.close()

    # ----- Persist -----
    print("\n[Persist Gold DB]")
    con = sqlite3.connect(GOLD)
    cur = con.cursor()

    # Backup before
    backups = {}
    for t in ["proj", "prps", "CSKS"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            backups[t] = cur.fetchone()[0]
        except Exception:
            backups[t] = None

    cur.execute("DROP TABLE IF EXISTS proj")
    cur.execute("""CREATE TABLE proj (
        VBUKR TEXT, PSPID TEXT, POST1 TEXT, VERNR TEXT, ERDAT TEXT, PSPNR TEXT,
        PRIMARY KEY (PSPNR)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO proj VALUES (?,?,?,?,?,?)",
        [(r["VBUKR"], r["PSPID"], r["POST1"], r["VERNR"], r["ERDAT"], r["PSPNR"]) for r in proj],
    )

    cur.execute("DROP TABLE IF EXISTS prps")
    cur.execute("""CREATE TABLE prps (
        PBUKR TEXT, POSID TEXT, POST1 TEXT, VERNR TEXT, ERDAT TEXT,
        PSPHI TEXT, PSPNR TEXT, OBJNR TEXT,
        PRIMARY KEY (PSPNR)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO prps VALUES (?,?,?,?,?,?,?,?)",
        [(r["PBUKR"], r["POSID"], r["POST1"], r["VERNR"], r["ERDAT"],
          r["PSPHI"], r["PSPNR"], r["OBJNR"]) for r in prps],
    )

    cur.execute("DROP TABLE IF EXISTS CSKS")
    cur.execute("""CREATE TABLE CSKS (
        KOKRS TEXT, KOSTL TEXT, DATBI TEXT, DATAB TEXT, BUKRS TEXT,
        KOSAR TEXT, VERAK TEXT, ERSDA TEXT, USNAM TEXT, KTEXT TEXT, LTEXT TEXT,
        PRIMARY KEY (KOKRS, KOSTL, DATBI)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO CSKS VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(r["KOKRS"], r["KOSTL"], r["DATBI"], r["DATAB"], r["BUKRS"],
          r["KOSAR"], r["VERAK"], r["ERSDA"], r["USNAM"],
          r.get("KTEXT", ""), r.get("LTEXT", "")) for r in csks],
    )
    con.commit()

    print("\n  Before -> After:")
    for t in ["proj", "prps", "CSKS"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        after = cur.fetchone()[0]
        before = backups.get(t)
        delta = after - before if before is not None else after
        print(f"    {t:8s}: {str(before):>8s} -> {after:>8d}  ({delta:+d})")

    # By-institute breakdown
    for t, key in [("proj", "VBUKR"), ("prps", "PBUKR"), ("CSKS", "BUKRS")]:
        print(f"\n  {t} by {key}:")
        cur.execute(f"SELECT {key}, COUNT(*) FROM {t} GROUP BY {key} ORDER BY 2 DESC")
        for r in cur.fetchall():
            print(f"    {r[0]:8s}  {r[1]:6d}")
    con.close()


if __name__ == "__main__":
    main()
