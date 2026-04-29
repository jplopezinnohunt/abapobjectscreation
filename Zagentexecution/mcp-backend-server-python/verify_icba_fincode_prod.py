"""
Definitive verification: does ICBA have FMFINCODE entries in P01 production?

Multiple cross-checks:
  1. FMFINCODE WHERE FIKRS = 'ICBA'  (direct)
  2. FMFINCODE GROUP BY FIKRS  (full enumeration)
  3. FMFINCODE WHERE FINCODE LIKE '%ICBA%'  (naming heuristic)
  4. FMFINCODE WHERE ERFNAME LIKE '%ICBA%' OR similar (creator naming)
  5. Compare row counts: P01 live FMFINCODE vs Gold DB funds table
  6. Sample of any rows that mention ICBA at all
"""
import sys
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # type: ignore


def query(g, table, fields, where, label, rowcount=200):
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
            print(f"  [{label}] 0 rows (TABLE_WITHOUT_DATA)")
            return []
        print(f"  [{label}] ERR: {msg[:120]}")
        return []
    rows = []
    for d in res.get("DATA", []):
        wa = d["WA"].split("|")
        rows.append({f: wa[i].strip() if i < len(wa) else "" for i, f in enumerate(fields)})
    print(f"  [{label}] {len(rows)} rows")
    return rows


def count_paginated(g, table, where, label):
    """Count via paginated read (RFC_READ_TABLE has no COUNT(*))."""
    total = 0
    skip = 0
    page = 30000
    while True:
        try:
            res = g.call(
                "RFC_READ_TABLE",
                QUERY_TABLE=table,
                FIELDS=[{"FIELDNAME": "FIKRS"}],
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
        n = len(res.get("DATA", []))
        total += n
        if n < page:
            break
        skip += page
    print(f"  [{label}] total = {total}")
    return total


def main():
    g = get_connection("P01")
    print("Connected P01 production.")

    print("\n[A] Direct: FMFINCODE WHERE FIKRS = 'ICBA'")
    icba = query(g, "FMFINCODE", ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"],
                 "FIKRS = 'ICBA'", "ICBA direct", rowcount=500)

    print("\n[B] FMFINCODE WHERE FINCODE LIKE 'ICBA%'  (any FIKRS)")
    icba_named = query(g, "FMFINCODE", ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"],
                       "FINCODE LIKE 'ICBA%'", "FINCODE ICBA*", rowcount=500)

    print("\n[C] FMFINCODE WHERE FINCODE LIKE '%ICBA%'  (substring)")
    icba_sub = query(g, "FMFINCODE", ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"],
                     "FINCODE LIKE '%ICBA%'", "FINCODE *ICBA*", rowcount=500)

    print("\n[D] FMFINCODE distinct FIKRS in production (paginated count)")
    # Pull all rows (FIKRS only) to enumerate institutes that actually have funds
    fikrs_rows = []
    skip = 0
    page = 30000
    while True:
        try:
            res = g.call("RFC_READ_TABLE", QUERY_TABLE="FMFINCODE",
                         FIELDS=[{"FIELDNAME": "FIKRS"}], DELIMITER="|",
                         ROWCOUNT=page, ROWSKIPS=skip)
        except Exception as e:
            print(f"  page skip={skip} ERR: {str(e)[:100]}")
            break
        rows = res.get("DATA", [])
        fikrs_rows.extend(d["WA"].strip() for d in rows)
        if len(rows) < page:
            break
        skip += page
    cnt = Counter(fikrs_rows)
    print(f"  Total FMFINCODE rows in P01: {len(fikrs_rows)}")
    print(f"  Distinct FIKRS in production:")
    for fk, n in sorted(cnt.items(), key=lambda x: -x[1]):
        marker = " <-- ICBA" if fk == "ICBA" else ""
        print(f"    {fk:8s}  {n:6d}{marker}")

    print("\n[E] FMFCTR (fund centers) WHERE FIKRS = 'ICBA'")
    fc_icba = query(g, "FMFCTR", ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"],
                    "FIKRS = 'ICBA'", "FMFCTR ICBA")

    print("\n[F] FMFCTR distinct FIKRS in production")
    fctr_rows = []
    skip = 0
    while True:
        try:
            res = g.call("RFC_READ_TABLE", QUERY_TABLE="FMFCTR",
                         FIELDS=[{"FIELDNAME": "FIKRS"}], DELIMITER="|",
                         ROWCOUNT=10000, ROWSKIPS=skip)
        except Exception as e:
            break
        rows = res.get("DATA", [])
        fctr_rows.extend(d["WA"].strip() for d in rows)
        if len(rows) < 10000:
            break
        skip += 10000
    cnt2 = Counter(fctr_rows)
    print(f"  Total FMFCTR rows: {len(fctr_rows)}")
    for fk, n in sorted(cnt2.items(), key=lambda x: -x[1]):
        marker = " <-- ICBA" if fk == "ICBA" else ""
        print(f"    {fk:8s}  {n:5d}{marker}")

    print("\n[G] Are there postings for ICBA against UNES funds? Check FMIFIIT (committed) sample")
    icba_post = query(g, "FMIFIIT", ["FIKRS", "FONDS", "BUKRS", "GJAHR"],
                      "BUKRS = 'ICBA'", "FMIFIIT BUKRS=ICBA", rowcount=20)
    if icba_post:
        ufunds = Counter((r["FIKRS"], r["FONDS"]) for r in icba_post)
        print("  Sample (FIKRS, FONDS) pairs used by ICBA postings:")
        for (fk, fo), n in ufunds.most_common(10):
            print(f"    FIKRS={fk:6s}  FONDS={fo:20s}  count={n}")

    g.close()


if __name__ == "__main__":
    main()
