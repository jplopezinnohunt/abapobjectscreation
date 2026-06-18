"""Quick read-only dump of ACTTY values in parent vs child for the orphan finding."""
import os, sys, time
from rfc_helpers import get_connection
from pyrfc import RFCError


def read_all(conn, table, fields):
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    all_rows, offset = [], 0
    while True:
        try:
            result = conn.call(
                "RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                ROWCOUNT=2000, ROWSKIPS=offset, OPTIONS=[], FIELDS=rfc_fields,
            )
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" in str(e):
                return []
            raise
        raw = result.get("DATA", [])
        hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        if not raw:
            break
        for row in raw:
            parts = row["WA"].split("|")
            all_rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
        if len(raw) < 2000:
            break
        offset += len(raw)
        time.sleep(0.2)
    return all_rows


def main():
    conn = get_connection("D01")
    parent = read_all(conn, "ZCRP_WFT_ACT_TY", ["MANDT", "ACTTY"])
    child  = read_all(conn, "ZCRP_WFT_ACT_TYT", ["MANDT", "SPRAS", "ACTTY"])
    conn.close()

    print("Parent ZCRP_WFT_ACT_TY (5 expected):")
    for r in parent:
        v = r.get("ACTTY", "")
        print(f"  ACTTY=[{v}] len={len(v)}")

    print("\nChild ZCRP_WFT_ACT_TYT (7 expected):")
    for r in child:
        v = r.get("ACTTY", "")
        s = r.get("SPRAS", "")
        print(f"  SPRAS=[{s}] ACTTY=[{v}] len={len(v)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
