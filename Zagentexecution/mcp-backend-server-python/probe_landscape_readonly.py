"""
probe_landscape_readonly.py — ABAP-discipline step #0: read-only landscape probe.

Answers the decisive question for the SAP ABAP change-discipline rule:
  - How many systems are in the transport domain, and what are their roles?
  - Is there a QAS (quality) system in a DEV -> QAS -> PROD route, or is it DEV -> PROD?
  - Are transports actually released (durable versions created)?

100% READ-ONLY: RFC_READ_TABLE on transport-config tables (TMSCSYS / TMSCROUTE /
TMSCDOM) + an E070 release-status count. Touches nothing. Run against D01.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def get(key, default=None):
    return os.getenv("SAP_D01_" + key) or os.getenv("SAP_" + key) or default


def read_table(conn, table, fields=None, options=None, rowcount=0):
    kw = dict(QUERY_TABLE=table, DELIMITER="|")
    if fields:
        kw["FIELDS"] = [{"FIELDNAME": f} for f in fields]
    if options:
        kw["OPTIONS"] = [{"TEXT": o} for o in options]
    if rowcount:
        kw["ROWCOUNT"] = rowcount
    res = conn.call("RFC_READ_TABLE", **kw)
    cols = [f["FIELDNAME"] for f in res["FIELDS"]]
    rows = [dict(zip(cols, r["WA"].split("|"))) for r in res["DATA"]]
    return cols, rows


def main():
    conn = Connection(ashost=get("ASHOST"), sysnr=get("SYSNR"),
                      client=get("CLIENT"), user=get("USER"),
                      passwd=get("PASSWD") or get("PASSWORD"), lang="EN")
    print(f"Connected to D01 ({get('ASHOST')}:{get('SYSNR')} client {get('CLIENT')})\n")

    # 1) Systems in the transport landscape
    print("=" * 70)
    print("TMSCSYS — systems in the transport domain(s)")
    print("=" * 70)
    try:
        _, rows = read_table(conn, "TMSCSYS",
                             fields=["SYSNAM", "SYSTYP", "DOMNAM", "DESCRIPT"])
        for r in rows:
            print(f"  {r.get('SYSNAM',''):6} | type={r.get('SYSTYP',''):3} | "
                  f"domain={r.get('DOMNAM',''):12} | {r.get('DESCRIPT','')}")
        print(f"  -> {len(rows)} systems")
    except Exception as e:
        print(f"  TMSCSYS field set failed ({e}); retrying all-fields...")
        cols, rows = read_table(conn, "TMSCSYS", rowcount=20)
        print("  cols:", cols)
        for r in rows:
            print("  ", r)

    # 2) Transport ROUTES (the DEV->QAS->PROD topology)
    print("\n" + "=" * 70)
    print("TMSCROUTE — consolidation/delivery routes (the DEV->QAS->PROD path)")
    print("=" * 70)
    try:
        cols, rows = read_table(conn, "TMSCROUTE", rowcount=50)
        print("  cols:", cols)
        for r in rows:
            print("  ", {k: v for k, v in r.items() if v.strip()})
        print(f"  -> {len(rows)} route rows")
    except Exception as e:
        print(f"  TMSCROUTE read failed: {e}")

    # 3) Domains
    print("\n" + "=" * 70)
    print("TMSCDOM — transport domains")
    print("=" * 70)
    try:
        cols, rows = read_table(conn, "TMSCDOM", rowcount=20)
        print("  cols:", cols)
        for r in rows:
            print("  ", {k: v for k, v in r.items() if v.strip()})
    except Exception as e:
        print(f"  TMSCDOM read failed: {e}")

    # 4) Are transports released? E070 status distribution (D = modifiable, R = released)
    print("\n" + "=" * 70)
    print("E070 — transport release status (D=modifiable, R=released)")
    print("=" * 70)
    try:
        for st, label in [("D", "modifiable/open"), ("R", "released")]:
            _, rows = read_table(conn, "E070",
                                fields=["TRKORR"],
                                options=[f"TRSTATUS = '{st}'"], rowcount=0)
            print(f"  TRSTATUS={st} ({label}): {len(rows)} requests/tasks")
    except Exception as e:
        print(f"  E070 read failed: {e}")

    conn.close()
    print("\nDONE (read-only — nothing changed).")


if __name__ == "__main__":
    main()
