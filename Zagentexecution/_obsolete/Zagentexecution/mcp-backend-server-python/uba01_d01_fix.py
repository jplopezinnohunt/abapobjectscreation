"""
uba01_d01_fix.py — Fix G/L account config in D01 for UBA01 bank setup

Session #043 · 2026-04-07

3 Operations (ALL on D01 only):
  1. INSERT missing accounts 1165421 & 1165424 (SKA1 + SKB1 + SKAT)
     - Source: P01 (read-only)
     - Overrides: ERDAT→sy-datum, ERNAM→sy-uname, HBKID→UBA01
  2. UPDATE KTOKS from OTHR→BANK on 1065421 & 1065424 in SKA1
  3. UPDATE XINTB = X on 1065421 & 1065424 in SKB1

SAFETY RAILS:
  - TARGET_SYSTEM = D01 only. P01 is read-only.
  - RFC_ABAP_INSTALL_AND_RUN with 72-char limit enforced
  - COMMIT WORK per batch
"""

from __future__ import annotations

import io
import re
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa: E402

# =========================================================================
# HARD SAFETY RAIL
# =========================================================================
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be 'D01'")

KTOPL = "UNES"
BUKRS = "UNES"
INSERT_ACCOUNTS = ["0001165421", "0001165424"]
UPDATE_ACCOUNTS = ["0001065421", "0001065424"]

# Fields to override when inserting into D01
AUDIT_FIELDS = {"ERDAT", "ERNAM", "AEDAT", "AENAM"}
HBKID_OVERRIDE = "UBA01"

# Fields to skip entirely (client field handled by sy-mandt)
SKIP_FIELDS = {"MANDT"}


def esc(s: str) -> str:
    """Escape single quotes for ABAP literal."""
    return (s or "").replace("'", "''")


def discover_fields(conn, table_name):
    """Get all field names and their lengths from a table."""
    result = conn.call(
        "RFC_READ_TABLE", QUERY_TABLE=table_name,
        ROWCOUNT=0, DELIMITER="|", OPTIONS=[], FIELDS=[],
    )
    return [(f["FIELDNAME"], int(f["LENGTH"])) for f in result.get("FIELDS", [])]


def read_account_rows(conn, table_name, fields, key_filter, key_value, account):
    """Read all rows for a single account from a table."""
    from rfc_helpers import rfc_read_paginated
    where = f"{key_filter} = '{key_value}' AND SAKNR = '{account}'"
    return rfc_read_paginated(conn, table_name, [f[0] for f in fields],
                              where, batch_size=100, throttle=0.5)


def build_insert_abap(table_name: str, fields: list[tuple],
                      rows: list[dict], overrides: dict) -> list[str]:
    """Build ABAP INSERT program for a table.

    fields: list of (FIELDNAME, LENGTH)
    rows: list of row dicts from P01
    overrides: dict of field->value to override
    """
    lines = [
        "REPORT Z_UBA01_INS.",
        f"DATA: ls TYPE {table_name.lower()},",
        "      lv_ok TYPE i, lv_ko TYPE i.",
        "",
    ]
    for row in rows:
        lines.append("CLEAR ls.")
        lines.append("ls-mandt = sy-mandt.")
        for fname, flen in fields:
            if fname in SKIP_FIELDS:
                continue

            # Determine value
            if fname in overrides:
                val = overrides[fname]
            elif fname in AUDIT_FIELDS:
                if fname in ("ERDAT", "AEDAT"):
                    lines.append(f"ls-{fname.lower()} = sy-datum.")
                    continue
                elif fname in ("ERNAM", "AENAM"):
                    lines.append(f"ls-{fname.lower()} = sy-uname.")
                    continue
            else:
                val = row.get(fname, "").strip()

            if not val:
                continue  # skip empty fields

            # For values, check if the assignment fits in 72 chars
            escaped = esc(val)
            assignment = f"ls-{fname.lower()} = '{escaped}'."
            if len(assignment) > 72:
                # Split long text values using ABAP concatenate
                # This shouldn't happen for GL accounts but safety
                half = flen // 2
                lines.append(f"ls-{fname.lower()} =")
                lines.append(f"  '{escaped}'.")
            else:
                lines.append(assignment)

        lines.append(f"INSERT {table_name.lower()} FROM ls.")
        lines.append("IF sy-subrc = 0.")
        lines.append("  ADD 1 TO lv_ok.")
        lines.append("ELSE.")
        lines.append("  ADD 1 TO lv_ko.")
        lines.append("ENDIF.")
        lines.append("")

    lines += [
        "COMMIT WORK.",
        "WRITE: / 'INSERT_OK:', lv_ok,",
        "       '  INSERT_KO:', lv_ko.",
    ]
    return lines


def build_update_ska1_ktoks() -> list[str]:
    """UPDATE KTOKS from OTHR to BANK for 1065421 and 1065424."""
    lines = [
        "REPORT Z_UBA01_UPD_KTOKS.",
        "DATA: ls TYPE ska1, lv_ok TYPE i,",
        "      lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for acct in UPDATE_ACCOUNTS:
        lines += [
            "CLEAR ls.",
            "SELECT SINGLE * FROM ska1 INTO ls",
            f"  WHERE ktopl = '{KTOPL}'",
            f"    AND saknr = '{acct}'.",
            "IF sy-subrc = 0.",
            "  ls-ktoks = 'BANK'.",
            "  UPDATE ska1 FROM ls.",
            "  IF sy-subrc = 0.",
            "    ADD 1 TO lv_ok.",
            "  ELSE.",
            "    ADD 1 TO lv_ko.",
            "  ENDIF.",
            "ELSE.",
            "  ADD 1 TO lv_mi.",
            "ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'UPDATE_OK:', lv_ok,",
        "       '  UPDATE_KO:', lv_ko,",
        "       '  MISSING:', lv_mi.",
    ]
    return lines


def build_update_skb1_xintb() -> list[str]:
    """UPDATE XINTB = X for 1065421 and 1065424."""
    lines = [
        "REPORT Z_UBA01_UPD_XINTB.",
        "DATA: ls TYPE skb1, lv_ok TYPE i,",
        "      lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for acct in UPDATE_ACCOUNTS:
        lines += [
            "CLEAR ls.",
            "SELECT SINGLE * FROM skb1 INTO ls",
            f"  WHERE bukrs = '{BUKRS}'",
            f"    AND saknr = '{acct}'.",
            "IF sy-subrc = 0.",
            "  ls-xintb = 'X'.",
            "  UPDATE skb1 FROM ls.",
            "  IF sy-subrc = 0.",
            "    ADD 1 TO lv_ok.",
            "  ELSE.",
            "    ADD 1 TO lv_ko.",
            "  ENDIF.",
            "ELSE.",
            "  ADD 1 TO lv_mi.",
            "ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'UPDATE_OK:', lv_ok,",
        "       '  UPDATE_KO:', lv_ko,",
        "       '  MISSING:', lv_mi.",
    ]
    return lines


def truncate_lines(abap: list[str], limit: int = 72) -> list[dict]:
    return [{"LINE": line[:limit]} for line in abap]


def check_72(abap_lines: list[str]):
    """Abort if any line exceeds 72 chars."""
    for i, line in enumerate(abap_lines):
        if len(line) > 72:
            raise SystemExit(
                f"ABAP line {i} overflows 72 chars ({len(line)}): {line!r}"
            )


def run_abap(guard, abap_lines: list[str], label: str) -> dict:
    """Send ABAP to D01, parse output."""
    sid = getattr(guard, "system_id", None)
    if sid and sid != TARGET_SYSTEM:
        raise SystemExit(f"SAFETY: guard={sid!r} != {TARGET_SYSTEM!r}")

    check_72(abap_lines)
    src = truncate_lines(abap_lines)

    print(f"\n  [{label}] Sending {len(abap_lines)} ABAP lines...")
    result = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    writes = result.get("WRITES", [])
    err = result.get("ERRORMESSAGE", "")
    output = " ".join(w.get("ZEILE", "") for w in writes)

    ok = ko = mi = 0
    m_ok = re.search(r"(UPDATE|INSERT)_OK:\s*(\d+)", output)
    m_ko = re.search(r"(UPDATE|INSERT)_KO:\s*(\d+)", output)
    m_mi = re.search(r"MISSING:\s*(\d+)", output)
    if m_ok:
        ok = int(m_ok.group(2))
    if m_ko:
        ko = int(m_ko.group(2))
    if m_mi:
        mi = int(m_mi.group(1))

    status = "OK" if ko == 0 and mi == 0 else "ISSUES"
    print(f"  [{label}] {status} — ok={ok} ko={ko} mi={mi}")
    if err:
        print(f"  [{label}] ERROR: {err}")
    if output:
        print(f"  [{label}] Output: {output}")
    return {"ok": ok, "ko": ko, "mi": mi, "output": output, "error": err}


def verify_read(guard, table, key_filter, key_value, accounts, check_fields):
    """Read back rows from D01 to verify changes."""
    from rfc_helpers import rfc_read_paginated
    print(f"\n  [VERIFY] Reading {table} from {TARGET_SYSTEM}...")
    for acct in accounts:
        where = f"{key_filter} = '{key_value}' AND SAKNR = '{acct}'"
        rows = rfc_read_paginated(guard, table, check_fields,
                                  where, batch_size=10, throttle=0.5)
        if rows:
            print(f"    {acct}: {', '.join(f'{k}={v}' for k, v in rows[0].items())}")
        else:
            print(f"    {acct}: NOT FOUND")


def main() -> int:
    print("=" * 70)
    print(f"  UBA01 D01 Fix — TARGET = {TARGET_SYSTEM}")
    print("=" * 70)

    # =========================================================
    # Step 1: Read source data from P01 for INSERT accounts
    # =========================================================
    print("\n[PHASE 0] Reading source data from P01...")
    p01 = get_connection("P01")

    p01_data = {}  # table -> account -> [rows]
    table_fields = {}  # table -> [(fname, flen)]

    for table_name, cfg in [
        ("SKA1", {"key_filter": "KTOPL", "key_value": KTOPL}),
        ("SKB1", {"key_filter": "BUKRS", "key_value": BUKRS}),
        ("SKAT", {"key_filter": "KTOPL", "key_value": KTOPL}),
    ]:
        print(f"  Discovering {table_name} fields...")
        fields = discover_fields(p01, table_name)
        table_fields[table_name] = fields
        print(f"    {table_name}: {len(fields)} fields")

        p01_data[table_name] = {}
        for acct in INSERT_ACCOUNTS:
            rows = read_account_rows(p01, table_name, fields,
                                     cfg["key_filter"], cfg["key_value"], acct)
            p01_data[table_name][acct] = rows
            print(f"    {acct} in {table_name}: {len(rows)} rows")
            if rows:
                # Print key fields for verification
                for r in rows:
                    key_vals = {k: r.get(k, "").strip() for k in
                                ["SAKNR", "KTOPL", "BUKRS", "SPRAS",
                                 "KTOKS", "XBILK", "HBKID", "HKTID"]
                                if r.get(k, "").strip()}
                    print(f"      {key_vals}")

    p01.close()
    print("  P01 connection closed.")

    # =========================================================
    # Step 2: Connect to D01
    # =========================================================
    print(f"\n[CONNECT] {TARGET_SYSTEM}...")
    d01 = get_connection(TARGET_SYSTEM)

    # Sanity probe
    probe = d01.call("RFC_READ_TABLE", QUERY_TABLE="SKA1",
                     FIELDS=[{"FIELDNAME": "SAKNR"}],
                     OPTIONS=[{"TEXT": f"KTOPL = '{KTOPL}'"}], ROWCOUNT=1)
    if not probe.get("DATA"):
        raise SystemExit("D01 probe failed — no SKA1 data, aborting")
    print(f"[CONNECT] {TARGET_SYSTEM} OK")

    total_ok = 0
    total_ko = 0

    try:
        # =========================================================
        # Operation 1: INSERT missing accounts
        # =========================================================
        print(f"\n{'=' * 70}")
        print("  OPERATION 1 — INSERT missing 1165421 & 1165424")
        print(f"{'=' * 70}")

        for table_name, cfg in [
            ("SKA1", {"key_filter": "KTOPL", "key_value": KTOPL}),
            ("SKB1", {"key_filter": "BUKRS", "key_value": BUKRS}),
            ("SKAT", {"key_filter": "KTOPL", "key_value": KTOPL}),
        ]:
            fields = table_fields[table_name]
            all_rows = []
            for acct in INSERT_ACCOUNTS:
                all_rows.extend(p01_data[table_name].get(acct, []))

            if not all_rows:
                print(f"\n  {table_name}: No P01 rows found — skipping")
                continue

            # Build overrides
            overrides = {}
            if table_name == "SKB1":
                overrides["HBKID"] = HBKID_OVERRIDE

            print(f"\n  {table_name}: Inserting {len(all_rows)} rows...")
            abap = build_insert_abap(table_name, fields, all_rows, overrides)

            # Debug: print first few lines
            for ln in abap[:5]:
                print(f"    | {ln}")
            print(f"    | ... ({len(abap)} total lines)")

            res = run_abap(d01, abap, f"INS-{table_name}")
            total_ok += res["ok"]
            total_ko += res["ko"]

        # Verify inserts
        verify_read(d01, "SKA1", "KTOPL", KTOPL, INSERT_ACCOUNTS,
                    ["SAKNR", "KTOKS", "XBILK"])
        verify_read(d01, "SKB1", "BUKRS", BUKRS, INSERT_ACCOUNTS,
                    ["SAKNR", "HBKID", "HKTID", "XINTB"])
        verify_read(d01, "SKAT", "KTOPL", KTOPL, INSERT_ACCOUNTS,
                    ["SAKNR", "SPRAS", "TXT20", "TXT50"])

        time.sleep(2)

        # =========================================================
        # Operation 2: UPDATE KTOKS OTHR→BANK
        # =========================================================
        print(f"\n{'=' * 70}")
        print("  OPERATION 2 — UPDATE KTOKS → BANK on 1065421 & 1065424")
        print(f"{'=' * 70}")

        # Verify current state first
        verify_read(d01, "SKA1", "KTOPL", KTOPL, UPDATE_ACCOUNTS,
                    ["SAKNR", "KTOKS"])

        abap = build_update_ska1_ktoks()
        res = run_abap(d01, abap, "UPD-KTOKS")
        total_ok += res["ok"]
        total_ko += res["ko"]

        # Verify
        verify_read(d01, "SKA1", "KTOPL", KTOPL, UPDATE_ACCOUNTS,
                    ["SAKNR", "KTOKS"])

        time.sleep(2)

        # =========================================================
        # Operation 3: UPDATE XINTB = X
        # =========================================================
        print(f"\n{'=' * 70}")
        print("  OPERATION 3 — UPDATE XINTB → X on 1065421 & 1065424")
        print(f"{'=' * 70}")

        # Verify current state first
        verify_read(d01, "SKB1", "BUKRS", BUKRS, UPDATE_ACCOUNTS,
                    ["SAKNR", "XINTB"])

        abap = build_update_skb1_xintb()
        res = run_abap(d01, abap, "UPD-XINTB")
        total_ok += res["ok"]
        total_ko += res["ko"]

        # Verify
        verify_read(d01, "SKB1", "BUKRS", BUKRS, UPDATE_ACCOUNTS,
                    ["SAKNR", "XINTB"])

    finally:
        d01.close()

    # =========================================================
    # Final Summary
    # =========================================================
    print(f"\n{'=' * 70}")
    status = "ALL OK" if total_ko == 0 else f"ISSUES: {total_ko} failures"
    print(f"  FINAL — OK={total_ok}  KO={total_ko}  [{status}]")
    print(f"{'=' * 70}")

    return 0 if total_ko == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
