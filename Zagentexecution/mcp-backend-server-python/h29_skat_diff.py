"""
h29_skat_diff.py — H29 SKAT text divergence extractor

Session #038 · 2026-04-05

Purpose
-------
H29 (raised #034): 510 GL accounts have different TXT20/TXT50 between P01 and D01.
The #034 master-data sync did INSERTs only (69 missing rows). Rows that exist in
BOTH systems but carry different texts were NOT synced. This script:

1. Refreshes P01_SKAT and D01_SKAT LIVE (per skill rule #3 — never trust cache for gap analysis)
2. Compares by (KTOPL, SAKNR, SPRAS)
3. Produces h29_skat_diff.csv + inline sample for user gate
4. Classifies changes: CLOSED-BK prefix (P01 closed bank account), text update, other

Safe: READ-ONLY. No UPDATE / INSERT / DELETE. Gate for user approval before h29_skat_update.py.

Related
-------
- `.agents/skills/sap_master_data_sync/SKILL.md` — 4-step sync pattern (#034)
- `Zagentexecution/sap_data_extraction/scripts/extract_gl_costel_comparison.py` — extraction template
- `feedback_data_p01_code_d01.md` — direction P01 → D01 for data sync
"""

from __future__ import annotations

import csv
import io
import sqlite3
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows for emoji/special chars
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Ensure rfc_helpers is importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

REPO = HERE.parent.parent
DB_PATH = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT_CSV = HERE / "h29_skat_diff.csv"

# SKAT fields (per #034 extraction)
SKAT_FIELDS = ["SPRAS", "KTOPL", "SAKNR", "TXT20", "TXT50"]
# Filter: UNES chart of accounts only. All languages (E, F, P confirmed present #038).
# Multi-language sync discovered in Session #038 — the original #034 note "510 rows"
# was English-only. Real scope is larger once F and P texts are included.
WHERE = "KTOPL = 'UNES'"


def refresh_skat(system_id: str) -> int:
    """Extract SKAT LIVE from {system_id} and overwrite {system}_SKAT in Gold DB."""
    print(f"\n[{system_id}] Connecting...")
    guard = get_connection(system_id)
    try:
        t0 = time.time()
        rows = rfc_read_paginated(guard, "SKAT", SKAT_FIELDS, WHERE,
                                  batch_size=5000, throttle=1.0)
        elapsed = time.time() - t0
        print(f"[{system_id}] SKAT: {len(rows):,} rows in {elapsed:.1f}s")
    finally:
        guard.close()

    # Write to Gold DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    table = f"{system_id}_SKAT"
    cur.execute(f'DROP TABLE IF EXISTS "{table}"')
    cur.execute(f'''
        CREATE TABLE "{table}" (
            SPRAS TEXT, KTOPL TEXT, SAKNR TEXT, TXT20 TEXT, TXT50 TEXT
        )
    ''')
    cur.executemany(
        f'INSERT INTO "{table}" (SPRAS, KTOPL, SAKNR, TXT20, TXT50) VALUES (?, ?, ?, ?, ?)',
        [(r.get("SPRAS", ""), r.get("KTOPL", ""), r.get("SAKNR", ""),
          r.get("TXT20", ""), r.get("TXT50", "")) for r in rows],
    )
    conn.commit()
    conn.close()
    print(f"[{system_id}] Saved to Gold DB as {table}")
    return len(rows)


def compute_diff() -> tuple[list[dict], list[dict]]:
    """Return (updates, inserts):
       updates = rows present in both systems but with different TXT20/TXT50
       inserts = rows present in P01 but missing in D01 (by KTOPL+SAKNR+SPRAS key)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    updates_q = """
        SELECT
            p.KTOPL AS KTOPL,
            p.SAKNR AS SAKNR,
            p.SPRAS AS SPRAS,
            p.TXT20 AS P01_TXT20,
            d.TXT20 AS D01_TXT20,
            p.TXT50 AS P01_TXT50,
            d.TXT50 AS D01_TXT50
        FROM P01_SKAT p
        INNER JOIN D01_SKAT d
            ON p.KTOPL = d.KTOPL
           AND p.SAKNR = d.SAKNR
           AND p.SPRAS = d.SPRAS
        WHERE p.TXT20 != d.TXT20
           OR p.TXT50 != d.TXT50
        ORDER BY p.SPRAS, p.SAKNR
    """
    updates = [dict(r) for r in cur.execute(updates_q).fetchall()]

    inserts_q = """
        SELECT
            p.KTOPL AS KTOPL,
            p.SAKNR AS SAKNR,
            p.SPRAS AS SPRAS,
            p.TXT20 AS P01_TXT20,
            ''     AS D01_TXT20,
            p.TXT50 AS P01_TXT50,
            ''     AS D01_TXT50
        FROM P01_SKAT p
        LEFT JOIN D01_SKAT d
            ON p.KTOPL = d.KTOPL
           AND p.SAKNR = d.SAKNR
           AND p.SPRAS = d.SPRAS
        WHERE d.SAKNR IS NULL
        ORDER BY p.SPRAS, p.SAKNR
    """
    inserts = [dict(r) for r in cur.execute(inserts_q).fetchall()]

    conn.close()
    return updates, inserts


def classify(row: dict) -> str:
    """Classify the diff type."""
    p20 = (row["P01_TXT20"] or "").upper()
    p50 = (row["P01_TXT50"] or "").upper()
    if p20.startswith("CLOSED-BK") or p50.startswith("CLOSED-BK"):
        return "CLOSED-BK"
    if p20.startswith("CLOSED") or p50.startswith("CLOSED"):
        return "CLOSED-OTHER"
    if (row["D01_TXT20"] or "").strip() == "" or (row["D01_TXT50"] or "").strip() == "":
        return "D01-EMPTY"
    return "TEXT-UPDATE"


def write_csv(updates: list[dict], inserts: list[dict]) -> None:
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["OP", "KTOPL", "SAKNR", "SPRAS", "P01_TXT20", "D01_TXT20",
                    "P01_TXT50", "D01_TXT50", "CHANGE_TYPE"])
        for r in updates:
            w.writerow(["UPDATE", r["KTOPL"], r["SAKNR"], r["SPRAS"],
                        r["P01_TXT20"], r["D01_TXT20"],
                        r["P01_TXT50"], r["D01_TXT50"],
                        classify(r)])
        for r in inserts:
            w.writerow(["INSERT", r["KTOPL"], r["SAKNR"], r["SPRAS"],
                        r["P01_TXT20"], "",
                        r["P01_TXT50"], "",
                        "MISSING-IN-D01"])
    print(f"\n[OUT] Wrote {len(updates)} UPDATE + {len(inserts)} INSERT rows to {OUT_CSV}")


def print_summary(updates: list[dict], inserts: list[dict]) -> None:
    from collections import Counter
    print("\n" + "=" * 60)
    print("  H29 SKAT Diff Summary (multi-language)")
    print("=" * 60)

    # UPDATEs — breakdown by language + classifier
    print(f"\n[UPDATE candidates] {len(updates)} rows (exist in both, text differs)")
    by_lang = Counter(r["SPRAS"] for r in updates)
    for lang, n in sorted(by_lang.items()):
        print(f"  SPRAS={lang}: {n:4d}")
    print("  --- classifier breakdown ---")
    by_cat = Counter(classify(r) for r in updates)
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct = 100 * n / max(1, len(updates))
        print(f"  {cat:20s}  {n:5d}  ({pct:5.1f}%)")

    # INSERTs — breakdown by language
    print(f"\n[INSERT candidates] {len(inserts)} rows (exist in P01, missing in D01)")
    by_lang_i = Counter(r["SPRAS"] for r in inserts)
    for lang, n in sorted(by_lang_i.items()):
        print(f"  SPRAS={lang}: {n:4d}")

    # Show samples by language for UPDATEs
    print(f"\n[SAMPLES — UPDATE, one per language]")
    seen_lang = set()
    for r in updates:
        if r["SPRAS"] in seen_lang:
            continue
        seen_lang.add(r["SPRAS"])
        print(f"\n  SPRAS={r['SPRAS']}  SAKNR={r['SAKNR']}  ({classify(r)})")
        print(f"    P01 TXT20: {r['P01_TXT20']!r}")
        print(f"    D01 TXT20: {r['D01_TXT20']!r}")
        print(f"    P01 TXT50: {r['P01_TXT50']!r}")
        print(f"    D01 TXT50: {r['D01_TXT50']!r}")

    # Show samples by language for INSERTs
    print(f"\n[SAMPLES — INSERT, one per language]")
    seen_lang = set()
    for r in inserts:
        if r["SPRAS"] in seen_lang:
            continue
        seen_lang.add(r["SPRAS"])
        print(f"\n  SPRAS={r['SPRAS']}  SAKNR={r['SAKNR']}")
        print(f"    P01 TXT20: {r['P01_TXT20']!r}")
        print(f"    P01 TXT50: {r['P01_TXT50']!r}")

    total = len(updates) + len(inserts)
    print(f"\n[TOTAL SCOPE] {len(updates)} UPDATEs + {len(inserts)} INSERTs = {total} rows")


def main() -> int:
    print("=" * 60)
    print("  H29 SKAT Diff Extractor — Session #038")
    print("=" * 60)

    # Step 1: Refresh both sides LIVE
    p01_n = refresh_skat("P01")
    d01_n = refresh_skat("D01")

    print(f"\n[COUNTS] P01_SKAT: {p01_n:,} | D01_SKAT: {d01_n:,}")

    # Step 2: Compute diff (UPDATEs + INSERTs, all languages)
    updates, inserts = compute_diff()

    # Step 3: Output
    write_csv(updates, inserts)
    print_summary(updates, inserts)

    print("\n" + "=" * 60)
    print("  GATE — User approval required before h29_skat_update.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
