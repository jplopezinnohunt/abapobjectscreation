"""
h29_skat_update_test.py — Single-row test of the H29 UPDATE ABAP pattern.

Session #038 · 2026-04-05

Per sap_master_data_sync SKILL.md rule: "Test 1 account first — always run
a single record, verify field-by-field against P01, then proceed with bulk".

This script:
1. Picks ONE row from the UPDATE candidates
2. Reads current D01 value for that row (pre-state)
3. Executes a single-row UPDATE via RFC_ABAP_INSTALL_AND_RUN
4. Reads D01 value again (post-state)
5. Asserts post-state matches P01 target value
6. If verified, prints GO; if not, prints the diff and exits non-zero

Target: D01 ONLY. P01 is read-only via RFC_READ_TABLE.
"""

from __future__ import annotations

import io
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa: E402
from h29_skat_update import (  # noqa: E402
    TARGET_SYSTEM, build_update_abap, run_batch, DB_PATH,
)


def read_d01_row(guard, ktopl: str, saknr: str, spras: str) -> dict:
    """Read a single SKAT row from D01 for verification."""
    res = guard.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="SKAT",
        FIELDS=[{"FIELDNAME": f} for f in ("KTOPL", "SAKNR", "SPRAS", "TXT20", "TXT50")],
        OPTIONS=[{"TEXT": f"KTOPL = '{ktopl}' AND SAKNR = '{saknr}' AND SPRAS = '{spras}'"}],
        ROWCOUNT=1,
    )
    data = res.get("DATA", [])
    if not data:
        return {}
    fields = res.get("FIELDS", [])
    wa = data[0].get("WA", "")
    vals = {}
    for f in fields:
        off = int(f.get("OFFSET", 0))
        ln = int(f.get("LENGTH", 0))
        vals[f["FIELDNAME"]] = wa[off:off + ln].strip()
    return vals


def main() -> int:
    assert TARGET_SYSTEM == "D01", "TARGET_SYSTEM safety guard tripped"

    # Pick one UPDATE candidate from Gold DB
    conn = sqlite3.connect(DB_PATH)
    q = """
        SELECT p.KTOPL, p.SAKNR, p.SPRAS, p.TXT20, p.TXT50,
               d.TXT20 AS D_TXT20, d.TXT50 AS D_TXT50
        FROM P01_SKAT p
        INNER JOIN D01_SKAT d
            ON p.KTOPL=d.KTOPL AND p.SAKNR=d.SAKNR AND p.SPRAS=d.SPRAS
        WHERE (p.TXT20 != d.TXT20 OR p.TXT50 != d.TXT50)
          AND p.SPRAS = 'E'
        ORDER BY p.SAKNR
        LIMIT 1
    """
    row = conn.execute(q).fetchone()
    conn.close()
    if not row:
        print("No UPDATE candidates found — nothing to test")
        return 1

    ktopl, saknr, spras, p_t20, p_t50, d_t20, d_t50 = row
    print("=" * 60)
    print(f"  H29 SKAT UPDATE — Single-row test")
    print(f"  Target: {TARGET_SYSTEM}")
    print("=" * 60)
    print(f"\nTest row: KTOPL={ktopl}  SAKNR={saknr}  SPRAS={spras}")
    print(f"  P01 (target values): TXT20={p_t20!r}")
    print(f"                       TXT50={p_t50!r}")
    print(f"  D01 (current):       TXT20={d_t20!r}")
    print(f"                       TXT50={d_t50!r}")

    print(f"\n[CONNECT] {TARGET_SYSTEM}")
    guard = get_connection(TARGET_SYSTEM)
    try:
        # Pre-state read
        pre = read_d01_row(guard, ktopl, saknr, spras)
        print(f"\n[PRE-STATE live D01 read] {pre}")
        if pre.get("TXT20") != d_t20:
            print(f"  WARN: live D01 TXT20={pre.get('TXT20')!r} differs from cached {d_t20!r}")

        # Run single-row UPDATE
        batch = [(ktopl, saknr, spras, p_t20, p_t50)]
        abap = build_update_abap(batch)
        print(f"\n[ABAP] Generated {len(abap)} lines. Snippet:")
        for line in abap[:12]:
            print(f"    {line}")
        print("    ...")

        print(f"\n[EXEC] Sending to {TARGET_SYSTEM}...")
        res = run_batch(guard, abap)
        print(f"[RESULT] ok={res['ok']}  ko={res['ko']}  output={res['output'][:200]!r}")

        # Post-state read
        post = read_d01_row(guard, ktopl, saknr, spras)
        print(f"\n[POST-STATE live D01 read] {post}")

        # Verify
        ok = (post.get("TXT20") == p_t20 and post.get("TXT50") == p_t50)
        if ok:
            print(f"\n✅ VERIFIED — D01 now matches P01 target value.")
            print(f"   TXT20: {pre.get('TXT20')!r}  ->  {post.get('TXT20')!r}")
            print(f"   TXT50: {pre.get('TXT50')!r}  ->  {post.get('TXT50')!r}")
            print(f"\n   Ready to run h29_skat_update.py for full 1,690 rows.")
            return 0
        else:
            print(f"\n❌ FAILED — D01 did not update as expected.")
            print(f"   Expected TXT20: {p_t20!r}, got {post.get('TXT20')!r}")
            print(f"   Expected TXT50: {p_t50!r}, got {post.get('TXT50')!r}")
            return 2
    finally:
        guard.close()


if __name__ == "__main__":
    sys.exit(main())
