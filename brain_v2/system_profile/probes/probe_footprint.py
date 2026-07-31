"""Bounded volume probe on P01 (READ-ONLY) to close the 'to confirm' modules.

Bounded on purpose: WHERE 2024+ and ROWCOUNT caps, so we never pull a full table.
A hit-cap is reported as '>=cap', never as an exact count.
"""
import sys, json, os
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from rfc_helpers import ConnectionGuard

CAP = 20000
PROBES = [
    ("SD  sales orders 2024+",        "VBAK",   ["VBELN"], ["ERDAT GE '20240101'"]),
    ("SD  sales organisations",       "TVKO",   ["VKORG"], []),
    ("SD  deliveries 2024+",          "LIKP",   ["VBELN"], ["ERDAT GE '20240101'"]),
    ("SD  billing docs 2024+",        "VBRK",   ["VBELN"], ["ERDAT GE '20240101'"]),
    ("AA  asset masters",             "ANLA",   ["ANLN1"], []),
    ("AA  asset cocds",               "T093C",  ["BUKRS"], []),
    ("AA  asset postings 2024+",      "ANEP",   ["ANLN1"], ["GJAHR GE '2024'"]),
    ("RE  contracts",                 "VICNCN", ["RECNNR"], []),
    ("RE  business entities",         "VIBDBE", ["SWENR"], []),
    ("RE  rental objects",            "VIBDRO", ["SMENR"], []),
    ("MM  material masters",          "MARA",   ["MATNR"], []),
    ("MM  goods movements 2024+",     "MKPF",   ["MBLNR"], ["BUDAT GE '20240101'"]),
    ("MM  plants",                    "T001W",  ["WERKS"], []),
    ("PM  equipment",                 "EQUI",   ["EQUNR"], []),
    ("QM  inspection lots",           "QALS",   ["PRUEFLOS"], []),
    ("WM  warehouses",                "T300",   ["LGNUM"], []),
    ("CS  service notifications",     "QMEL",   ["QMNUM"], []),
    ("TRM treasury deals",            "VTBFHA", ["RFHA"], []),
    ("GM  grants",                    "GMGR",   ["GRANT_NBR"], []),
]


def main():
    g = ConnectionGuard("P01"); g.connect()
    out = {}
    for label, tab, fields, where in PROBES:
        try:
            r = g.call("RFC_READ_TABLE", QUERY_TABLE=tab, DELIMITER="|",
                       ROWCOUNT=CAP,
                       FIELDS=[{"FIELDNAME": f} for f in fields],
                       OPTIONS=[{"TEXT": w} for w in where])
            n = len(r["DATA"])
            val = (">=%d" % CAP) if n >= CAP else str(n)
            out[tab] = {"label": label, "rows": val, "exists": True}
            print("%-32s %-8s %s" % (label, tab, val))
        except Exception as e:
            msg = type(e).__name__
            out[tab] = {"label": label, "exists": False, "error": msg + ": " + str(e)[:120]}
            print("%-32s %-8s ERR %s" % (label, tab, msg))
    g.close()
    p = os.path.join(os.path.dirname(__file__), "p01_volume_probe.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\nwritten:", p)


if __name__ == "__main__":
    main()
