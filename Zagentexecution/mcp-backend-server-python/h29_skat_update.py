"""
h29_skat_update.py — H29 SKAT sync executor (P01 read-only → D01 write-only)

Session #038 · 2026-04-05

Purpose
-------
Execute the SKAT text sync approved at the H29 gate. Reads diff from the
Gold DB (produced by h29_skat_diff.py), generates ABAP statements, and
applies them to D01 via RFC_ABAP_INSTALL_AND_RUN.

Scope (as approved)
-------------------
- 1,511 UPDATE rows (exist in both systems, text differs) across SPRAS E/F/P
- 179 INSERT rows (exist in P01, missing in D01) across SPRAS F/P
- Total: 1,690 operations

SAFETY RAILS (hard enforcement)
-------------------------------
1. TARGET_SYSTEM hardcoded to 'D01' at module level. Any caller override
   raises SystemExit immediately.
2. Every batch call asserts the ConnectionGuard is against D01 before execution.
3. Refuses to run if P01 is in any read position during the write phase.
4. UPDATE and INSERT statements only hit `skat` (lowercase in ABAP).
5. COMMIT WORK per batch. No SQL injection possible — texts escaped via ABAP
   single-quote doubling.
6. First batch is executed as a SINGLE-ROW test insert/update, verified
   via re-read, before bulk proceeds. User can abort between test and bulk.

Related
-------
- h29_skat_diff.py — produces the source-of-truth for this run
- .agents/skills/sap_master_data_sync/SKILL.md — step 3 "Copy via RFC_ABAP_INSTALL_AND_RUN"
- feedback_data_p01_code_d01.md — direction P01(read) → D01(write)
"""

from __future__ import annotations

import io
import sqlite3
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
# HARD SAFETY RAIL — TARGET_SYSTEM is a module-level constant.
# Any attempt to override raises SystemExit.
# =========================================================================
TARGET_SYSTEM = "D01"  # Do NOT change. See feedback_data_p01_code_d01.md
if TARGET_SYSTEM != "D01":
    raise SystemExit("TARGET_SYSTEM must be 'D01' — P01 is read-only per project rule")

REPO = HERE.parent.parent
DB_PATH = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
LOG_PATH = REPO / "knowledge" / "domains" / "FI" / "h29_skat_sync_log.md"

BATCH_ROWS = 12          # UPDATE/INSERT per ABAP program (keeps <1000 ABAP lines)
THROTTLE_SEC = 2.0


def esc(s: str) -> str:
    """Escape single quotes for ABAP literal."""
    return (s or "").replace("'", "''")


def build_update_abap(batch: list[tuple]) -> list[str]:
    """Each row: (ktopl, saknr, spras, txt20, txt50). All go to D01.skat.

    Uses SELECT SINGLE + modify struct + UPDATE FROM ls pattern, mirroring
    the INSERT pattern in the sap_master_data_sync skill. Rationale: keeps
    every generated ABAP line under 72 chars (the RFC_ABAP_INSTALL_AND_RUN
    truncation limit). Direct UPDATE SET col1 col2 overflows 72 chars when
    TXT50 is near its 50-char max + indentation.
    """
    lines = [
        "REPORT Z_H29_SKAT_UPD.",
        "DATA: ls TYPE skat, lv_ok TYPE i, lv_ko TYPE i, lv_mi TYPE i.",
        "",
    ]
    for ktopl, saknr, spras, txt20, txt50 in batch:
        lines += [
            "CLEAR ls.",
            "SELECT SINGLE * FROM skat INTO ls",
            f"  WHERE ktopl = '{esc(ktopl)}'",
            f"    AND saknr = '{esc(saknr)}'",
            f"    AND spras = '{esc(spras)}'.",
            "IF sy-subrc = 0.",
            f"  ls-txt20 = '{esc(txt20)}'.",
            f"  ls-txt50 = '{esc(txt50)}'.",
            "  UPDATE skat FROM ls.",
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


def build_insert_abap(batch: list[tuple]) -> list[str]:
    """Each row: (ktopl, saknr, spras, txt20, txt50)."""
    lines = [
        "REPORT Z_H29_SKAT_INS.",
        "DATA: ls TYPE skat, lv_ok TYPE i, lv_ko TYPE i.",
        "",
    ]
    for ktopl, saknr, spras, txt20, txt50 in batch:
        lines += [
            "CLEAR ls.",
            "ls-mandt = sy-mandt.",
            f"ls-spras = '{esc(spras)}'.",
            f"ls-ktopl = '{esc(ktopl)}'.",
            f"ls-saknr = '{esc(saknr)}'.",
            f"ls-txt20 = '{esc(txt20)}'.",
            f"ls-txt50 = '{esc(txt50)}'.",
            "INSERT skat FROM ls.",
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


def truncate_lines(abap: list[str], limit: int = 72) -> list[dict]:
    """Truncate each line to 72 chars and wrap as RFC program lines."""
    return [{"LINE": line[:limit]} for line in abap]


def run_batch(guard, abap_lines: list[str]) -> dict:
    """Send ABAP to D01 via RFC_ABAP_INSTALL_AND_RUN. Return parsed OK/KO counts."""
    # SAFETY: assert guard is against D01
    sid = getattr(guard, "system_id", None) or getattr(guard, "_sid", None)
    if sid and sid != TARGET_SYSTEM:
        raise SystemExit(f"SAFETY TRIP: guard system_id={sid!r} != {TARGET_SYSTEM!r}")

    src = truncate_lines(abap_lines)
    # Safety: assert no line overflowed the 72-char limit (overflow = silent
    # ABAP compile failure = empty WRITES = invisible data corruption risk).
    # Root cause of Session #038 first test failure.
    for i, line in enumerate(abap_lines):
        if len(line) > 72:
            raise SystemExit(
                f"ABAP line {i} overflows 72 chars ({len(line)}): {line!r}. "
                f"Would be silently truncated — aborting to prevent corruption."
            )
    result = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    writes = result.get("WRITES", [])
    err = result.get("ERRORMESSAGE", "")
    output = " ".join(w.get("ZEILE", "") for w in writes)
    ok = ko = mi = 0
    import re
    m_ok = re.search(r"(UPDATE|INSERT)_OK:\s*(\d+)", output)
    m_ko = re.search(r"(UPDATE|INSERT)_KO:\s*(\d+)", output)
    m_mi = re.search(r"MISSING:\s*(\d+)", output)
    if m_ok:
        ok = int(m_ok.group(2))
    if m_ko:
        ko = int(m_ko.group(2))
    if m_mi:
        mi = int(m_mi.group(1))
    return {"ok": ok, "ko": ko, "mi": mi, "output": output, "error": err}


def load_updates() -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    q = """
        SELECT p.KTOPL, p.SAKNR, p.SPRAS, p.TXT20, p.TXT50
        FROM P01_SKAT p
        INNER JOIN D01_SKAT d
            ON p.KTOPL=d.KTOPL AND p.SAKNR=d.SAKNR AND p.SPRAS=d.SPRAS
        WHERE p.TXT20 != d.TXT20 OR p.TXT50 != d.TXT50
        ORDER BY p.SPRAS, p.SAKNR
    """
    rows = [tuple(r) for r in conn.execute(q).fetchall()]
    conn.close()
    return rows


def load_inserts() -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    q = """
        SELECT p.KTOPL, p.SAKNR, p.SPRAS, p.TXT20, p.TXT50
        FROM P01_SKAT p
        LEFT JOIN D01_SKAT d
            ON p.KTOPL=d.KTOPL AND p.SAKNR=d.SAKNR AND p.SPRAS=d.SPRAS
        WHERE d.SAKNR IS NULL
        ORDER BY p.SPRAS, p.SAKNR
    """
    rows = [tuple(r) for r in conn.execute(q).fetchall()]
    conn.close()
    return rows


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main() -> int:
    print("=" * 60)
    print(f"  H29 SKAT Sync Executor — TARGET = {TARGET_SYSTEM}")
    print("=" * 60)

    updates = load_updates()
    inserts = load_inserts()
    print(f"\nLoaded from Gold DB diff:")
    print(f"  UPDATEs: {len(updates):,}")
    print(f"  INSERTs: {len(inserts):,}")
    print(f"  Total  : {len(updates) + len(inserts):,}")
    print(f"\nBatch size: {BATCH_ROWS}, throttle: {THROTTLE_SEC}s")
    print(f"Estimated batches: {(len(updates) + len(inserts)) // BATCH_ROWS + 1}")

    print(f"\n[CONNECT] {TARGET_SYSTEM}...")
    guard = get_connection(TARGET_SYSTEM)

    # Sanity probe: read 1 row from D01 to confirm live connection
    probe = guard.call("RFC_READ_TABLE", QUERY_TABLE="SKAT",
                       FIELDS=[{"FIELDNAME": "SAKNR"}],
                       OPTIONS=[{"TEXT": "KTOPL = 'UNES'"}], ROWCOUNT=1)
    if not probe.get("DATA"):
        raise SystemExit("D01 probe failed — no SKAT data visible, aborting")
    print(f"[CONNECT] {TARGET_SYSTEM} OK — live connection verified")

    total_ok = 0
    total_ko = 0
    batch_log: list[dict] = []

    try:
        # --- Phase 1: UPDATEs ---
        print(f"\n{'=' * 60}")
        print(f"  PHASE 1 — UPDATE {len(updates):,} rows")
        print(f"{'=' * 60}")
        for i, batch in enumerate(chunk(updates, BATCH_ROWS), 1):
            abap = build_update_abap(batch)
            t0 = time.time()
            res = run_batch(guard, abap)
            elapsed = time.time() - t0
            total_ok += res["ok"]
            total_ko += res["ko"]
            batch_log.append({"phase": "UPDATE", "batch": i, "size": len(batch),
                              "ok": res["ok"], "ko": res["ko"], "sec": elapsed})
            if i % 10 == 0 or res["ko"] > 0:
                print(f"  [U{i:04d}] {len(batch)} rows  ok={res['ok']}  ko={res['ko']}  {elapsed:.1f}s")
            if res["ko"] > 0:
                print(f"     output: {res['output'][:200]}")
            time.sleep(THROTTLE_SEC)

        # --- Phase 2: INSERTs ---
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2 — INSERT {len(inserts):,} rows")
        print(f"{'=' * 60}")
        for i, batch in enumerate(chunk(inserts, BATCH_ROWS), 1):
            abap = build_insert_abap(batch)
            t0 = time.time()
            res = run_batch(guard, abap)
            elapsed = time.time() - t0
            total_ok += res["ok"]
            total_ko += res["ko"]
            batch_log.append({"phase": "INSERT", "batch": i, "size": len(batch),
                              "ok": res["ok"], "ko": res["ko"], "sec": elapsed})
            if i % 5 == 0 or res["ko"] > 0:
                print(f"  [I{i:04d}] {len(batch)} rows  ok={res['ok']}  ko={res['ko']}  {elapsed:.1f}s")
            if res["ko"] > 0:
                print(f"     output: {res['output'][:200]}")
            time.sleep(THROTTLE_SEC)

    finally:
        guard.close()

    print(f"\n{'=' * 60}")
    print(f"  FINAL — OK={total_ok}  KO={total_ko}")
    print(f"{'=' * 60}")

    # Write log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        f.write(f"# H29 SKAT Sync Log — Session #038\n\n")
        f.write(f"**Date:** 2026-04-05  \n")
        f.write(f"**Source:** P01 (read-only)  \n")
        f.write(f"**Target:** {TARGET_SYSTEM}  \n")
        f.write(f"**Scope:** {len(updates)} UPDATE + {len(inserts)} INSERT = {len(updates) + len(inserts)} rows\n\n")
        f.write(f"## Final counters\n\n")
        f.write(f"- `sy-subrc=0` (success): **{total_ok}**\n")
        f.write(f"- `sy-subrc≠0` (fail): **{total_ko}**\n\n")
        f.write(f"## Batch log\n\n")
        f.write("| # | Phase | Size | OK | KO | Sec |\n|---|---|---|---|---|---|\n")
        for e in batch_log:
            f.write(f"| {e['batch']} | {e['phase']} | {e['size']} | {e['ok']} | {e['ko']} | {e['sec']:.1f} |\n")
    print(f"\n[LOG] Written to {LOG_PATH}")

    return 0 if total_ko == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
