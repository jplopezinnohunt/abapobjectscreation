"""
Re-extract FMFINCODE + FMFCTR + FMFINT from P01 LIVE per-FIKRS using
the SAME query pattern that verify_icba_fincode_prod.py used (which worked).

Then overwrite Gold DB `funds` + `fund_centers` + `FMFINT`.
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


def read_table(g, table, fields, where, rowcount=80000):
    """Single RFC_READ_TABLE — no pagination wrapper."""
    try:
        res = g.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table,
            FIELDS=[{"FIELDNAME": f} for f in fields],
            OPTIONS=[{"TEXT": where}] if where else [],
            DELIMITER="|",
            ROWCOUNT=rowcount,
        )
    except Exception as e:
        msg = str(e)
        if "TABLE_WITHOUT_DATA" in msg:
            return []
        print(f"  ERR: {msg[:140]}")
        return []
    rows = []
    for d in res.get("DATA", []):
        wa = d["WA"].split("|")
        rows.append({f: wa[i].strip() if i < len(wa) else "" for i, f in enumerate(fields)})
    return rows


def main():
    g = get_connection("P01")
    print("Connected P01.")

    INSTITUTES = ['IBE', 'ICBA', 'ICTP', 'IIEP', 'MGIE', 'UBO', 'UIL', 'UIS', 'UNES']

    # ----- 1. FMFINCODE per FIKRS (with chunked rowskips for UNES which has 55K) -----
    print("\n[1] FMFINCODE per FIKRS")
    fmfincode = []
    for fk in INSTITUTES:
        # Chunk via ROWSKIPS for large institutes
        skip = 0
        page = 30000
        n = 0
        while True:
            try:
                res = g.call(
                    "RFC_READ_TABLE",
                    QUERY_TABLE="FMFINCODE",
                    FIELDS=[{"FIELDNAME": f} for f in ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"]],
                    OPTIONS=[{"TEXT": f"FIKRS = '{fk}'"}],
                    DELIMITER="|",
                    ROWCOUNT=page,
                    ROWSKIPS=skip,
                )
            except Exception as e:
                msg = str(e)
                if "TABLE_WITHOUT_DATA" in msg:
                    break
                print(f"  [{fk} skip={skip}] ERR: {msg[:120]}")
                break
            batch = res.get("DATA", [])
            for d in batch:
                wa = d["WA"].split("|")
                fmfincode.append({
                    "FIKRS": wa[0].strip() if len(wa) > 0 else "",
                    "FINCODE": wa[1].strip() if len(wa) > 1 else "",
                    "TYPE": wa[2].strip() if len(wa) > 2 else "",
                    "ERFDAT": wa[3].strip() if len(wa) > 3 else "",
                    "ERFNAME": wa[4].strip() if len(wa) > 4 else "",
                })
            n += len(batch)
            if len(batch) < page:
                break
            skip += page
        print(f"  [{fk}] {n} rows")

    fikrs_cnt = Counter(r["FIKRS"] for r in fmfincode)
    print(f"\n  TOTAL FMFINCODE pulled: {len(fmfincode)}")
    print(f"  By FIKRS: {dict(sorted(fikrs_cnt.items(), key=lambda x: -x[1]))}")

    # ----- 2. FMFCTR per FIKRS -----
    print("\n[2] FMFCTR per FIKRS")
    fmfctr = []
    for fk in INSTITUTES:
        rows = read_table(g, "FMFCTR", ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"],
                          f"FIKRS = '{fk}'", rowcount=10000)
        print(f"  [{fk}] {len(rows)} rows")
        fmfctr.extend(rows)
    fctr_cnt = Counter(r["FIKRS"] for r in fmfctr)
    print(f"  TOTAL FMFCTR: {len(fmfctr)} - by FIKRS: {dict(fctr_cnt)}")

    # ----- 3. FMFINT for the 3 institutes only -----
    print("\n[3] FMFINT (texts) for MGIE/IBE/ICBA")
    fmfint = []
    for inst in ["MGIE", "IBE", "ICBA"]:
        rows = read_table(g, "FMFINT", ["FIKRS", "FINCODE", "SPRAS", "BEZEICH", "BESCHR"],
                          f"FIKRS = '{inst}' AND SPRAS = 'E'", rowcount=10000)
        print(f"  [{inst}] {len(rows)} rows")
        fmfint.extend(rows)

    g.close()

    # ----- 4. Persist to Gold DB -----
    print("\n[4] Overwriting Gold DB")
    con = sqlite3.connect(GOLD)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM funds")
    before_funds = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM fund_centers")
    before_fc = cur.fetchone()[0]

    cur.execute("DROP TABLE IF EXISTS funds")
    cur.execute("""CREATE TABLE funds (
        FIKRS TEXT, FINCODE TEXT, TYPE TEXT, ERFDAT TEXT, ERFNAME TEXT,
        PRIMARY KEY (FIKRS, FINCODE)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO funds VALUES (?,?,?,?,?)",
        [(r["FIKRS"], r["FINCODE"], r["TYPE"], r["ERFDAT"], r["ERFNAME"]) for r in fmfincode],
    )

    cur.execute("DROP TABLE IF EXISTS fund_centers")
    cur.execute("""CREATE TABLE fund_centers (
        FIKRS TEXT, FICTR TEXT, ERFDAT TEXT, ERFNAME TEXT,
        PRIMARY KEY (FIKRS, FICTR)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO fund_centers VALUES (?,?,?,?)",
        [(r["FIKRS"], r["FICTR"], r["ERFDAT"], r["ERFNAME"]) for r in fmfctr],
    )

    cur.execute("DROP TABLE IF EXISTS FMFINT")
    cur.execute("""CREATE TABLE FMFINT (
        FIKRS TEXT, FINCODE TEXT, SPRAS TEXT, BEZEICH TEXT, BESCHR TEXT,
        PRIMARY KEY (FIKRS, FINCODE, SPRAS)
    )""")
    cur.executemany(
        "INSERT OR REPLACE INTO FMFINT VALUES (?,?,?,?,?)",
        [(r["FIKRS"], r["FINCODE"], r["SPRAS"], r.get("BEZEICH", ""), r.get("BESCHR", ""))
         for r in fmfint],
    )

    con.commit()

    cur.execute("SELECT COUNT(*) FROM funds")
    after_funds = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM fund_centers")
    after_fc = cur.fetchone()[0]

    print(f"  funds:        {before_funds} -> {after_funds}  (delta {after_funds - before_funds:+d})")
    print(f"  fund_centers: {before_fc} -> {after_fc}  (delta {after_fc - before_fc:+d})")

    cur.execute("SELECT FIKRS, COUNT(*) FROM funds GROUP BY FIKRS ORDER BY 2 DESC")
    print("\n  funds by FIKRS (post-refresh):")
    for r in cur.fetchall():
        print(f"    {r[0]:6s}  {r[1]:6d}")
    cur.execute("SELECT FIKRS, COUNT(*) FROM fund_centers GROUP BY FIKRS ORDER BY 2 DESC")
    print("\n  fund_centers by FIKRS (post-refresh):")
    for r in cur.fetchall():
        print(f"    {r[0]:6s}  {r[1]:6d}")
    con.close()


if __name__ == "__main__":
    main()
