"""Explore SWDPHEADER + SWDSDSTEPS to find N_MENARD workflows and Return outcomes."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402


def rr(g, table, where, fields, rc=50):
    opts = []
    for i, w in enumerate(where):
        opts.append({"TEXT": w + (" AND" if i < len(where) - 1 else "")})
    try:
        r = g.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                   OPTIONS=opts, FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=rc)
        cols = [f["FIELDNAME"] for f in r["FIELDS"]]
        return [dict(zip(cols, [v.strip() for v in row["WA"].split("|")])) for row in r["DATA"]]
    except Exception as e:
        return f"ERR: {e}"


def schema(g, table):
    rows = rr(g, "DD03L",
              [f"TABNAME = '{table}'", "FIELDNAME <> '.INCLUDE'"],
              ["FIELDNAME", "POSITION", "DATATYPE", "LENG", "KEYFLAG"], 40)
    if isinstance(rows, list):
        rows.sort(key=lambda r: int(r["POSITION"]) if r["POSITION"].isdigit() else 0)
        return rows
    return []


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # Schema of the key tables
        for t in ["SWDPHEADER", "SWDSDSTEPS", "SWDSCONT", "SWDAAGNTS", "SWDPCMD", "SWDPCMDT"]:
            print(f"\n== schema {t} ==")
            for r in schema(g, t):
                keyf = "K" if r["KEYFLAG"] == "X" else " "
                print(f"  {keyf} pos={r['POSITION']:>4} {r['FIELDNAME']:20} {r['DATATYPE']:8} len={r['LENG']}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
