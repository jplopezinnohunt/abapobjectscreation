"""
uba01_fix_xintb_d01.py
=======================
Remove XINTB flag on all 4 UBA01 G/L accounts in D01.
Sets SKB1.XINTB = '' (empty) via RFC_ABAP_INSTALL_AND_RUN.

TARGET: D01 ONLY.
"""
import sys, os, io, re, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

TARGET = "D01"
BUKRS = "UNES"
GLS = ["0001065421", "0001165421", "0001065424", "0001165424"]


def run():
    print(f"{'='*60}")
    print(f"  FIX XINTB on UBA01 accounts — {TARGET}")
    print(f"{'='*60}")

    conn = get_connection(TARGET)

    # Step 1: Verify current state
    print(f"\n  BEFORE:")
    for gl in GLS:
        result = conn.call("RFC_READ_TABLE",
                           QUERY_TABLE="SKB1",
                           FIELDS=[{"FIELDNAME": "SAKNR"}, {"FIELDNAME": "XINTB"}],
                           OPTIONS=[{"TEXT": f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'"}],
                           ROWCOUNT=1)
        data = result.get("DATA", [])
        if data:
            raw = data[0].get("WA", "")
            print(f"    {gl}: XINTB='{raw.strip()}'")
        else:
            print(f"    {gl}: NOT FOUND")

    # Step 2: Update via ABAP
    print(f"\n  Updating XINTB to empty...")

    abap = [
        "REPORT Z_FIX_XINTB.",
        "DATA: ls TYPE skb1,",
        "      lv_ok TYPE i,",
        "      lv_ko TYPE i.",
        "",
    ]

    for gl in GLS:
        abap += [
            "CLEAR ls.",
            f"SELECT SINGLE * FROM skb1 INTO ls",
            f"  WHERE bukrs = '{BUKRS}'",
            f"    AND saknr = '{gl}'.",
            "IF sy-subrc = 0.",
            "  ls-xintb = ' '.",
            "  UPDATE skb1 FROM ls.",
            "  IF sy-subrc = 0.",
            "    ADD 1 TO lv_ok.",
            "  ELSE.",
            "    ADD 1 TO lv_ko.",
            "  ENDIF.",
            "ELSE.",
            "  ADD 1 TO lv_ko.",
            "ENDIF.",
            "",
        ]

    abap += [
        "COMMIT WORK.",
        "WRITE: / 'OK:', lv_ok,",
        "       '  KO:', lv_ko.",
    ]

    # Enforce 72-char limit
    for i, line in enumerate(abap):
        if len(line) > 72:
            raise SystemExit(f"Line {i} exceeds 72 chars: {line}")

    src = [{"LINE": line} for line in abap]
    result = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)

    writes = result.get("WRITES", [])
    output = " ".join(w.get("ZEILE", "") for w in writes)
    err = result.get("ERRORMESSAGE", "")

    print(f"  Result: {output}")
    if err:
        print(f"  Error: {err}")

    # Step 3: Verify after
    print(f"\n  AFTER:")
    for gl in GLS:
        result = conn.call("RFC_READ_TABLE",
                           QUERY_TABLE="SKB1",
                           FIELDS=[{"FIELDNAME": "SAKNR"}, {"FIELDNAME": "XINTB"}],
                           OPTIONS=[{"TEXT": f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'"}],
                           ROWCOUNT=1)
        data = result.get("DATA", [])
        if data:
            raw = data[0].get("WA", "")
            xintb = raw.strip()
            status = "FIXED" if not xintb else "STILL SET"
            print(f"    {gl}: XINTB='{xintb}' [{status}]")

    conn.close()
    print(f"\n  Done.")


if __name__ == "__main__":
    run()
