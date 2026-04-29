"""Diagnose which HRP1000 filter combination returns rows for N_MENARD."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402


def count(guard, where_lines):
    options = []
    for i, w in enumerate(where_lines):
        suffix = " AND" if i < len(where_lines) - 1 else ""
        options.append({"TEXT": w + suffix})
    try:
        r = guard.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="HRP1000",
            DELIMITER="|",
            OPTIONS=options,
            FIELDS=[{"FIELDNAME": "OBJID"}],
            ROWCOUNT=5,
        )
        return len(r["DATA"]), r["DATA"][:3]
    except Exception as e:
        return f"ERR: {e}", []


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        probes = [
            ["OTYPE = 'WS'"],
            ["OTYPE = 'WS'", "PLVAR = '01'"],
            ["OTYPE = 'WS'", "UNAME = 'N_MENARD'"],
            ["OTYPE = 'WS'", "AENAM = 'N_MENARD'"],
            ["UNAME = 'N_MENARD'"],
            ["AENAM = 'N_MENARD'"],
            ["OTYPE = 'TS'", "AENAM = 'N_MENARD'"],
            ["OTYPE = 'T'",  "AENAM = 'N_MENARD'"],
        ]
        for p in probes:
            n, sample = count(g, p)
            print(f"{p}  ->  {n}")
            for s in sample:
                print(f"    {s['WA']}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
