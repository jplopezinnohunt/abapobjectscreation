"""Verify WS existence in HRP1000 and try SWD_API_WFD_FOR_SIMULATION_GET."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))
from rfc_helpers import ConnectionGuard  # noqa: E402

WS_IDS = ["98100016","98100018","98100019","98100020","98100021",
          "98100022","98100023","98100026","98100027"]


def main():
    g = ConnectionGuard("D01"); g.connect()
    try:
        # 1. Check HRP1000 existence for each WS id, no UNAME filter.
        print("== HRP1000 OTYPE=WS for N_MENARD IDs ==")
        for wsid in WS_IDS:
            try:
                r = g.call("RFC_READ_TABLE", QUERY_TABLE="HRP1000", DELIMITER="|",
                           OPTIONS=[{"TEXT": f"OTYPE = 'WS' AND OBJID = '{wsid}'"}],
                           FIELDS=[{"FIELDNAME":"OBJID"},{"FIELDNAME":"SHORT"},
                                   {"FIELDNAME":"STEXT"},{"FIELDNAME":"UNAME"},
                                   {"FIELDNAME":"AEDTM"},{"FIELDNAME":"ISTAT"},
                                   {"FIELDNAME":"PLVAR"}],
                           ROWCOUNT=5)
                rows = [row["WA"].split("|") for row in r["DATA"]]
                print(f"  WS {wsid}: {len(rows)} row(s)")
                for row in rows:
                    print(f"    {[v.strip() for v in row]}")
            except Exception as e:
                print(f"  WS {wsid}: ERR {e}")

        # 2. Signature of SWD_API_WFD_FOR_SIMULATION_GET
        print("\n== SWD_API_WFD_FOR_SIMULATION_GET parameters ==")
        try:
            r = g.call("RFC_GET_FUNCTION_INTERFACE",
                       FUNCNAME="SWD_API_WFD_FOR_SIMULATION_GET",
                       LANGUAGE="E")
            for p in r.get("PARAMS", []):
                print(f"  {p['PARAMTYPE']:10} {p['PARAMETER']:30} {p.get('TABNAME','').strip():20} {p.get('FIELDNAME','').strip():20} {p.get('STEXT','').strip()[:50]}")
        except Exception as e:
            print(f"  ERR {e}")
    finally:
        g.close()


if __name__ == "__main__":
    main()
