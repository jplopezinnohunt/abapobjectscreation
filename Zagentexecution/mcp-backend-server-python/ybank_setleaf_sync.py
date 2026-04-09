"""
ybank_setleaf_sync.py — Sync YBANK SETLEAF entries P01 → D01

Session #043 · 2026-04-07

Purpose
-------
Extract SETLEAF rows for all YBANK sets from both P01 and D01,
compare by key, and sync D01 to match P01 exactly via RFC_ABAP_INSTALL_AND_RUN.

SAFETY RAILS
------------
1. TARGET_SYSTEM hardcoded to 'D01'. NEVER writes to P01.
2. Batch size: 10 rows per RFC call.
3. Throttle: 2 seconds between batches.
4. COMMIT WORK per batch.
5. Test with 1 row first, then bulk.
6. 72-char ABAP line limit enforced.
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
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

# =========================================================================
# HARD SAFETY RAIL
# =========================================================================
TARGET_SYSTEM = "D01"
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be 'D01'")

BATCH_ROWS = 10
THROTTLE_SEC = 2.0

# Key fields for comparison
KEY_FIELDS = ("SETCLASS", "SUBCLASS", "SETNAME", "LINEID")
ALL_FIELDS = ["MANDT", "SETCLASS", "SUBCLASS", "SETNAME", "LINEID",
              "VALSIGN", "VALOPTION", "VALFROM", "VALTO", "SEQNR"]
COMPARE_FIELDS = ["VALSIGN", "VALOPTION", "VALFROM", "VALTO", "SEQNR"]


def esc(s: str) -> str:
    """Escape single quotes for ABAP literal."""
    return (s or "").replace("'", "''")


def make_key(row: dict) -> tuple:
    return tuple(row.get(k, "") for k in KEY_FIELDS)


def extract_setleaf(system_id: str) -> list[dict]:
    """Extract all YBANK SETLEAF rows from a system."""
    print(f"\n[EXTRACT] {system_id} — SETLEAF WHERE SETCLASS='0000' AND SETNAME LIKE 'YBANK%'")
    guard = get_connection(system_id)
    try:
        where = [
            {"TEXT": "SETCLASS = '0000'"},
            {"TEXT": " AND SETNAME LIKE 'YBANK%'"},
        ]
        rows = rfc_read_paginated(guard, "SETLEAF", ALL_FIELDS, where,
                                  batch_size=5000, throttle=1.0)
        print(f"[EXTRACT] {system_id}: {len(rows)} rows")
        return rows
    finally:
        guard.close()


def compute_diff(p01_rows: list[dict], d01_rows: list[dict]):
    """Compare P01 vs D01 and return (inserts, deletes, updates)."""
    p01_map = {make_key(r): r for r in p01_rows}
    d01_map = {make_key(r): r for r in d01_rows}

    p01_keys = set(p01_map.keys())
    d01_keys = set(d01_map.keys())

    to_insert = [p01_map[k] for k in sorted(p01_keys - d01_keys)]
    to_delete = [d01_map[k] for k in sorted(d01_keys - p01_keys)]

    to_update = []
    for k in sorted(p01_keys & d01_keys):
        p, d = p01_map[k], d01_map[k]
        if any(p.get(f, "") != d.get(f, "") for f in COMPARE_FIELDS):
            to_update.append(p01_map[k])

    return to_insert, to_delete, to_update


def build_insert_abap(batch: list[dict]) -> list[str]:
    lines = [
        "REPORT Z_YBANK_INS.",
        "DATA: ls TYPE setleaf,",
        "      lv_ok TYPE i,",
        "      lv_ko TYPE i.",
        "",
    ]
    for row in batch:
        lines += [
            "CLEAR ls.",
            "ls-mandt = sy-mandt.",
            f"ls-setclass = '{esc(row['SETCLASS'])}'.",
            f"ls-subclass = '{esc(row['SUBCLASS'])}'.",
            f"ls-setname = '{esc(row['SETNAME'])}'.",
            f"ls-lineid = '{esc(row['LINEID'])}'.",
            f"ls-valsign = '{esc(row['VALSIGN'])}'.",
            f"ls-valoption = '{esc(row['VALOPTION'])}'.",
            f"ls-valfrom = '{esc(row['VALFROM'])}'.",
            f"ls-valto = '{esc(row['VALTO'])}'.",
            f"ls-seqnr = '{esc(row['SEQNR'])}'.",
            "INSERT setleaf FROM ls.",
            "IF sy-subrc = 0.",
            "  ADD 1 TO lv_ok.",
            "ELSE.",
            "  ADD 1 TO lv_ko.",
            "ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'INSERT_OK:', lv_ok,",
        "       '  INSERT_KO:', lv_ko.",
    ]
    return lines


def build_delete_abap(batch: list[dict]) -> list[str]:
    lines = [
        "REPORT Z_YBANK_DEL.",
        "DATA: lv_ok TYPE i,",
        "      lv_ko TYPE i.",
        "",
    ]
    for row in batch:
        lines += [
            "DELETE FROM setleaf",
            f"  WHERE setclass = '{esc(row['SETCLASS'])}'",
            f"    AND subclass = '{esc(row['SUBCLASS'])}'",
            f"    AND setname = '{esc(row['SETNAME'])}'",
            f"    AND lineid = '{esc(row['LINEID'])}'.",
            "IF sy-subrc = 0.",
            "  ADD 1 TO lv_ok.",
            "ELSE.",
            "  ADD 1 TO lv_ko.",
            "ENDIF.",
            "",
        ]
    lines += [
        "COMMIT WORK.",
        "WRITE: / 'DELETE_OK:', lv_ok,",
        "       '  DELETE_KO:', lv_ko.",
    ]
    return lines


def build_update_abap(batch: list[dict]) -> list[str]:
    lines = [
        "REPORT Z_YBANK_UPD.",
        "DATA: ls TYPE setleaf,",
        "      lv_ok TYPE i,",
        "      lv_ko TYPE i,",
        "      lv_mi TYPE i.",
        "",
    ]
    for row in batch:
        lines += [
            "CLEAR ls.",
            "SELECT SINGLE * FROM setleaf INTO ls",
            f"  WHERE setclass = '{esc(row['SETCLASS'])}'",
            f"    AND subclass = '{esc(row['SUBCLASS'])}'",
            f"    AND setname = '{esc(row['SETNAME'])}'",
            f"    AND lineid = '{esc(row['LINEID'])}'.",
            "IF sy-subrc = 0.",
            f"  ls-valsign = '{esc(row['VALSIGN'])}'.",
            f"  ls-valoption = '{esc(row['VALOPTION'])}'.",
            f"  ls-valfrom = '{esc(row['VALFROM'])}'.",
            f"  ls-valto = '{esc(row['VALTO'])}'.",
            f"  ls-seqnr = '{esc(row['SEQNR'])}'.",
            "  UPDATE setleaf FROM ls.",
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


def run_batch(guard, abap_lines: list[str], op_type: str) -> dict:
    """Send ABAP to D01 via RFC_ABAP_INSTALL_AND_RUN."""
    sid = getattr(guard, "system_id", None)
    if sid and sid != TARGET_SYSTEM:
        raise SystemExit(f"SAFETY: guard system_id={sid!r} != {TARGET_SYSTEM!r}")

    # Enforce 72-char limit
    for i, line in enumerate(abap_lines):
        if len(line) > 72:
            raise SystemExit(
                f"ABAP line {i} overflows 72 chars ({len(line)}): {line!r}"
            )

    src = truncate_lines(abap_lines)
    result = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    writes = result.get("WRITES", [])
    err = result.get("ERRORMESSAGE", "")
    output = " ".join(w.get("ZEILE", "") for w in writes)

    ok = ko = mi = 0
    m_ok = re.search(rf"{op_type}_OK:\s*(\d+)", output)
    m_ko = re.search(rf"{op_type}_KO:\s*(\d+)", output)
    m_mi = re.search(r"MISSING:\s*(\d+)", output)
    if m_ok:
        ok = int(m_ok.group(1))
    if m_ko:
        ko = int(m_ko.group(1))
    if m_mi:
        mi = int(m_mi.group(1))
    return {"ok": ok, "ko": ko, "mi": mi, "output": output, "error": err}


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def execute_phase(guard, label: str, op_type: str, items: list[dict],
                  builder_fn) -> tuple[int, int]:
    """Execute a sync phase (INSERT/DELETE/UPDATE). Returns (total_ok, total_ko)."""
    if not items:
        print(f"  {label}: 0 rows — skipping")
        return 0, 0

    total_ok = total_ko = 0

    # --- Test with 1 row first ---
    test_row = items[0]
    print(f"\n  [{label}] TEST — 1 row: {make_key(test_row)}")
    abap = builder_fn([test_row])
    res = run_batch(guard, abap, op_type)
    print(f"  [{label}] TEST result: ok={res['ok']} ko={res['ko']} output={res['output'][:200]}")
    if res["ko"] > 0:
        print(f"  [{label}] TEST FAILED — aborting this phase")
        return res["ok"], res["ko"]
    total_ok += res["ok"]
    total_ko += res["ko"]
    time.sleep(THROTTLE_SEC)

    # --- Bulk: remaining rows ---
    remaining = items[1:]
    if not remaining:
        return total_ok, total_ko

    batches = list(chunk(remaining, BATCH_ROWS))
    print(f"  [{label}] BULK — {len(remaining)} rows in {len(batches)} batches")

    for i, batch in enumerate(batches, 1):
        abap = builder_fn(batch)
        t0 = time.time()
        res = run_batch(guard, abap, op_type)
        elapsed = time.time() - t0
        total_ok += res["ok"]
        total_ko += res["ko"]

        if i % 5 == 0 or res["ko"] > 0 or i == len(batches):
            print(f"    [{label[0]}{i:04d}] {len(batch)} rows  "
                  f"ok={res['ok']}  ko={res['ko']}  {elapsed:.1f}s")
        if res["ko"] > 0:
            print(f"      output: {res['output'][:200]}")
        if res.get("error"):
            print(f"      error: {res['error'][:200]}")

        time.sleep(THROTTLE_SEC)

    return total_ok, total_ko


def main() -> int:
    print("=" * 60)
    print(f"  YBANK SETLEAF Sync — P01 (read) → {TARGET_SYSTEM} (write)")
    print("=" * 60)

    # --- Step 1: Extract from both systems ---
    p01_rows = extract_setleaf("P01")
    d01_rows = extract_setleaf("D01")

    # Show set names found
    p01_sets = sorted(set(r["SETNAME"] for r in p01_rows))
    d01_sets = sorted(set(r["SETNAME"] for r in d01_rows))
    print(f"\nP01 sets ({len(p01_sets)}): {p01_sets}")
    print(f"D01 sets ({len(d01_sets)}): {d01_sets}")

    # --- Step 2: Compare ---
    to_insert, to_delete, to_update = compute_diff(p01_rows, d01_rows)
    print(f"\n--- DIFF ---")
    print(f"  INSERT (in P01, not D01): {len(to_insert)}")
    print(f"  DELETE (in D01, not P01): {len(to_delete)}")
    print(f"  UPDATE (different values): {len(to_update)}")
    total_changes = len(to_insert) + len(to_delete) + len(to_update)
    print(f"  TOTAL changes: {total_changes}")

    if total_changes == 0:
        print("\nD01 already matches P01. Nothing to do.")
        return 0

    # --- Step 3: Execute changes on D01 ---
    print(f"\n[CONNECT] {TARGET_SYSTEM}...")
    guard = get_connection(TARGET_SYSTEM)

    # Sanity probe
    probe = guard.call("RFC_READ_TABLE", QUERY_TABLE="SETLEAF",
                       FIELDS=[{"FIELDNAME": "SETNAME"}],
                       OPTIONS=[{"TEXT": "SETCLASS = '0000' AND SETNAME = 'YBANK'"}],
                       ROWCOUNT=1)
    print(f"[CONNECT] {TARGET_SYSTEM} OK — live connection verified")

    grand_ok = grand_ko = 0

    try:
        # Phase 1: DELETEs first (remove extra rows from D01)
        print(f"\n{'=' * 60}")
        print(f"  PHASE 1 — DELETE {len(to_delete)} rows from D01")
        print(f"{'=' * 60}")
        ok, ko = execute_phase(guard, "DELETE", "DELETE", to_delete,
                               build_delete_abap)
        grand_ok += ok
        grand_ko += ko

        # Phase 2: UPDATEs (fix differing values)
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2 — UPDATE {len(to_update)} rows in D01")
        print(f"{'=' * 60}")
        ok, ko = execute_phase(guard, "UPDATE", "UPDATE", to_update,
                               build_update_abap)
        grand_ok += ok
        grand_ko += ko

        # Phase 3: INSERTs (add missing rows)
        print(f"\n{'=' * 60}")
        print(f"  PHASE 3 — INSERT {len(to_insert)} rows into D01")
        print(f"{'=' * 60}")
        ok, ko = execute_phase(guard, "INSERT", "INSERT", to_insert,
                               build_insert_abap)
        grand_ok += ok
        grand_ko += ko

    finally:
        guard.close()

    print(f"\n{'=' * 60}")
    print(f"  SYNC COMPLETE — OK={grand_ok}  KO={grand_ko}")
    print(f"{'=' * 60}")

    # --- Step 3b: Update SETHEADER audit trail for affected sets ---
    affected_sets = set()
    for r in to_insert + to_delete + to_update:
        affected_sets.add(r.get("SETNAME", "").strip())

    if affected_sets:
        print(f"\n{'=' * 60}")
        print(f"  PHASE 4 — UPDATE SETHEADER audit for {len(affected_sets)} sets")
        print(f"{'=' * 60}")
        guard = get_connection(TARGET_SYSTEM)
        try:
            for sn in sorted(affected_sets):
                # Count actual SETLEAF entries for this set
                abap = [
                    "REPORT Z_YBANK_HDR.",
                    "DATA: ls TYPE setheader,",
                    "      lv_cnt TYPE i.",
                    "",
                    f"SELECT COUNT(*) FROM setleaf",
                    f"  INTO lv_cnt",
                    f"  WHERE setclass = '0000'",
                    f"    AND setname = '{esc(sn)}'.",
                    "",
                    "SELECT SINGLE * FROM setheader",
                    "  INTO ls",
                    f"  WHERE setclass = '0000'",
                    f"    AND setname = '{esc(sn)}'.",
                    "IF sy-subrc = 0.",
                    "  ls-upduser = sy-uname.",
                    "  ls-upddate = sy-datum.",
                    "  ls-updtime = sy-uzeit.",
                    "  ls-setlines = lv_cnt.",
                    "  UPDATE setheader FROM ls.",
                    "  IF sy-subrc = 0.",
                    "    COMMIT WORK.",
                    "    WRITE: / 'HDR_OK:',",
                    f"           '{esc(sn)}',",
                    "           'LINES:', lv_cnt.",
                    "  ELSE.",
                    "    WRITE: / 'HDR_KO:',",
                    f"           '{esc(sn)}'.",
                    "  ENDIF.",
                    "ELSE.",
                    "  WRITE: / 'HDR_MISS:',",
                    f"         '{esc(sn)}'.",
                    "ENDIF.",
                ]
                res = run_batch(guard, abap, "HDR")
                print(f"    {sn}: {res['output'][:200]}")
                time.sleep(THROTTLE_SEC)
        finally:
            guard.close()

    # --- Step 4: Verify ---
    print(f"\n[VERIFY] Re-extracting D01 to confirm sync...")
    d01_after = extract_setleaf("D01")
    ins2, del2, upd2 = compute_diff(p01_rows, d01_after)
    remaining_diff = len(ins2) + len(del2) + len(upd2)
    print(f"\n--- POST-SYNC DIFF ---")
    print(f"  INSERT remaining: {len(ins2)}")
    print(f"  DELETE remaining: {len(del2)}")
    print(f"  UPDATE remaining: {len(upd2)}")
    print(f"  TOTAL remaining: {remaining_diff}")

    if remaining_diff == 0:
        print("\n  VERIFICATION PASSED — D01 matches P01 exactly.")
    else:
        print("\n  VERIFICATION FAILED — differences remain!")
        if ins2:
            for r in ins2[:5]:
                print(f"    MISSING: {make_key(r)}")
        if del2:
            for r in del2[:5]:
                print(f"    EXTRA:   {make_key(r)}")
        if upd2:
            for r in upd2[:5]:
                print(f"    DIFFER:  {make_key(r)}")

    return 0 if remaining_diff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
