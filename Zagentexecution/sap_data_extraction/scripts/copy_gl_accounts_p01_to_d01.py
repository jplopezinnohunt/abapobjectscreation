"""
copy_gl_accounts_p01_to_d01.py
==============================
Copy 69 GL accounts (SKA1 + SKAT) from P01 to D01 using RFC_ABAP_INSTALL_AND_RUN.

Approach:
  - Read the 69 missing accounts from Gold DB (extracted from P01)
  - For each account, generate ABAP INSERT statements for SKA1 and SKAT
  - Execute on D01 via RFC_ABAP_INSTALL_AND_RUN
  - Verify after completion
"""

import os
import sys
import sqlite3
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python"))
from rfc_helpers import get_connection

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sqlite", "p01_gold_master_data.db")


def get_missing_accounts():
    """Get the 69 accounts in P01 but not in D01, with texts."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('''
        SELECT a.KTOPL, a.SAKNR, a.BILKT, a.GVTYP, a.KTOKS, a.XBILK, a.XLOEV,
               a.FUNC_AREA, a.XSPEA, a.XSPEB, a.XSPEP,
               t.TXT20, t.TXT50
        FROM P01_SKA1 a
        LEFT JOIN P01_SKAT t ON a.KTOPL = t.KTOPL AND a.SAKNR = t.SAKNR
        WHERE a.SAKNR NOT IN (SELECT SAKNR FROM D01_SKA1 WHERE KTOPL = a.KTOPL)
        ORDER BY a.SAKNR
    ''').fetchall()
    conn.close()
    return rows


def escape_abap(s):
    """Escape single quotes for ABAP string literals."""
    if not s:
        return ""
    return s.replace("'", "''")


def build_insert_abap(accounts, batch_start, batch_size):
    """Build ABAP code to INSERT a batch of accounts into SKA1 and SKAT."""
    batch = accounts[batch_start:batch_start + batch_size]

    lines = [
        "REPORT Z_GL_COPY.",
        "DATA: ls_ska1 TYPE ska1,",
        "      ls_skat TYPE skat,",
        "      lv_cnt  TYPE i.",
        "",
    ]

    for acc in batch:
        ktopl, saknr, bilkt, gvtyp, ktoks, xbilk, xloev, func_area, xspea, xspeb, xspep, txt20, txt50 = acc

        # SKA1 INSERT
        lines.append(f"CLEAR ls_ska1.")
        lines.append(f"ls_ska1-mandt = sy-mandt.")
        lines.append(f"ls_ska1-ktopl = '{escape_abap(ktopl)}'.")
        lines.append(f"ls_ska1-saknr = '{escape_abap(saknr)}'.")
        if ktoks:
            lines.append(f"ls_ska1-ktoks = '{escape_abap(ktoks)}'.")
        if xbilk:
            lines.append(f"ls_ska1-xbilk = '{escape_abap(xbilk)}'.")
        if gvtyp:
            lines.append(f"ls_ska1-gvtyp = '{escape_abap(gvtyp)}'.")
        if bilkt:
            lines.append(f"ls_ska1-bilkt = '{escape_abap(bilkt)}'.")
        if xloev:
            lines.append(f"ls_ska1-xloev = '{escape_abap(xloev)}'.")
        if func_area:
            lines.append(f"ls_ska1-func_area = '{escape_abap(func_area)}'.")
        if xspea:
            lines.append(f"ls_ska1-xspea = '{escape_abap(xspea)}'.")
        if xspeb:
            lines.append(f"ls_ska1-xspeb = '{escape_abap(xspeb)}'.")
        if xspep:
            lines.append(f"ls_ska1-xspep = '{escape_abap(xspep)}'.")
        lines.append(f"ls_ska1-erdat = sy-datum.")
        lines.append(f"ls_ska1-ernam = sy-uname.")
        lines.append(f"INSERT ska1 FROM ls_ska1.")
        lines.append(f"IF sy-subrc = 0.")
        lines.append(f"  ADD 1 TO lv_cnt.")
        lines.append(f"ENDIF.")
        lines.append("")

        # SKAT INSERT (English text)
        if txt20 or txt50:
            lines.append(f"CLEAR ls_skat.")
            lines.append(f"ls_skat-mandt = sy-mandt.")
            lines.append(f"ls_skat-spras = 'E'.")
            lines.append(f"ls_skat-ktopl = '{escape_abap(ktopl)}'.")
            lines.append(f"ls_skat-saknr = '{escape_abap(saknr)}'.")
            if txt20:
                lines.append(f"ls_skat-txt20 = '{escape_abap(txt20)}'.")
            if txt50:
                lines.append(f"ls_skat-txt50 = '{escape_abap(txt50)}'.")
            lines.append(f"INSERT skat FROM ls_skat.")
            lines.append("")

    lines.append("COMMIT WORK.")
    lines.append(f"WRITE: / 'Inserted', lv_cnt, 'SKA1 entries'.")
    lines.append(f"WRITE: / 'Batch {batch_start+1}-{batch_start+len(batch)}'.")

    return lines


def run_abap_on_d01(abap_lines):
    """Execute ABAP on D01 via RFC_ABAP_INSTALL_AND_RUN."""
    guard = get_connection("D01")
    src = [{"LINE": line[:72]} for line in abap_lines]
    try:
        res = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        output = []
        for w in res.get("WRITES", []):
            val = w.get("ZEILE") or list(w.values())[0]
            output.append(val)
            print(f"  SAP: {val}")
        err = res.get("ERRORMESSAGE", "")
        if err:
            print(f"  ERROR: {err}")
        return output, err
    except Exception as e:
        print(f"  FAILED: {e}")
        return [], str(e)
    finally:
        guard.close()


def verify_on_d01(accounts):
    """Verify accounts exist in D01 SKA1."""
    guard = get_connection("D01")
    found = 0
    missing = []
    for acc in accounts:
        saknr = acc[1]
        result = guard.call("RFC_READ_TABLE", QUERY_TABLE="SKA1", DELIMITER="|",
            FIELDS=[{"FIELDNAME": "SAKNR"}],
            OPTIONS=[{"TEXT": f"SAKNR = '{saknr}'"}],
            ROWCOUNT=1)
        if result.get("DATA"):
            found += 1
        else:
            missing.append(saknr)
    guard.close()
    return found, missing


def main():
    accounts = get_missing_accounts()
    print(f"Accounts to copy from P01 to D01: {len(accounts)}")

    # Process in batches of 10 (ABAP line limit: 72 chars × ~1000 lines max)
    batch_size = 10
    total_batches = (len(accounts) + batch_size - 1) // batch_size

    for i in range(0, len(accounts), batch_size):
        batch_num = i // batch_size + 1
        batch_end = min(i + batch_size, len(accounts))
        print(f"\n{'='*50}")
        print(f"  Batch {batch_num}/{total_batches}: accounts {i+1}-{batch_end}")
        print(f"{'='*50}")

        abap = build_insert_abap(accounts, i, batch_size)
        print(f"  ABAP lines: {len(abap)}")

        output, err = run_abap_on_d01(abap)
        if err:
            print(f"  BATCH FAILED — stopping. Error: {err}")
            break

        time.sleep(2)  # Throttle

    # Verify
    print(f"\n{'='*50}")
    print(f"  VERIFICATION")
    print(f"{'='*50}")
    found, missing = verify_on_d01(accounts)
    print(f"  Found in D01: {found}/{len(accounts)}")
    if missing:
        print(f"  Missing: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    else:
        print(f"  ALL {len(accounts)} accounts successfully copied!")


if __name__ == "__main__":
    main()
