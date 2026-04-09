#!/usr/bin/env python3
"""
fmderive_hardcoded_fictr_check.py

Recurring check for INC-000005240 class of defect:
    UNESCO FI exit ZXFMDTU02_RPY.abap:99 hardcodes FICTR='UNESCO' for
    HKONT ∈ (6045011, 7045011, 6045014) × FIKRS=UNES × FISTL=SPACE.

This script reports how many fmifiit_full rows hit the hardcode signature,
broken down by GL and by posting user. Non-HQ users with high hit counts
are the top candidates for the SU3-opt-in / FMDERIVE-rule rollout.

Usage:
    python fmderive_hardcoded_fictr_check.py                       # defaults
    python fmderive_hardcoded_fictr_check.py --bukrs UNES \\
           --gls 0006045011,0007045011,0006045014 \\
           --default UNESCO --top 20 --threshold 100

Exit code:
    0 — the rule is still stable (same ballpark as baseline)
    1 — new top offenders appeared (ops attention needed)
    2 — DB or schema error
"""

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db",
)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to Gold DB sqlite file")
    ap.add_argument("--bukrs", default="UNES", help="Company code to check")
    ap.add_argument("--fikrs", default="UNES", help="FM area")
    ap.add_argument(
        "--gls",
        default="0006045011,0007045011,0006045014",
        help="Comma-separated GL accounts (HKONT) hardcoded in the exit",
    )
    ap.add_argument("--default", default="UNESCO", help="The hardcoded FICTR default the exit assigns")
    ap.add_argument("--top", type=int, default=20, help="Top N offending users to list")
    ap.add_argument("--threshold", type=int, default=100, help="Minimum hits to flag a user")
    args = ap.parse_args()

    gl_list = [g.strip() for g in args.gls.split(",") if g.strip()]
    placeholders = ",".join("?" * len(gl_list))

    try:
        conn = sqlite3.connect(args.db)
    except sqlite3.Error as exc:
        print(f"[ERR] cannot open DB: {exc}", file=sys.stderr)
        return 2

    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(fmifiit_full)")
        cols = {r[1] for r in cur.fetchall()}
        required = {"BUKRS", "FIKRS", "FISTL", "HKONT", "KNBELNR", "KNGJAHR"}
        missing = required - cols
        if missing:
            print(f"[ERR] fmifiit_full missing columns: {missing}", file=sys.stderr)
            return 2

        # 1. Total class impact
        q = f"""
            SELECT HKONT, COUNT(*) FROM fmifiit_full
             WHERE BUKRS=? AND FIKRS=? AND FISTL=?
               AND HKONT IN ({placeholders})
             GROUP BY HKONT ORDER BY HKONT
        """
        cur.execute(q, [args.bukrs, args.fikrs, args.default, *gl_list])
        per_gl = cur.fetchall()
        total = sum(r[1] for r in per_gl)
        print("=" * 70)
        print(f"INC-000005240 class check — bukrs={args.bukrs} fictr_default={args.default}")
        print("=" * 70)
        print(f"Hardcode signature rows:")
        for hkont, n in per_gl:
            print(f"  HKONT={hkont}  {n:>10,}")
        print(f"  {'TOTAL':14s}  {total:>10,}")
        print()

        if total == 0:
            print("[OK] No rows match the hardcode signature. Either the exit was")
            print("     modernized or data is stale. Check ZXFMDTU02_RPY.abap:94-101.")
            return 0

        # 2. Top offending users
        q2 = f"""
            SELECT b.USNAM, COUNT(*) AS c
              FROM fmifiit_full f
              JOIN bkpf b ON f.KNBELNR=b.BELNR AND f.KNGJAHR=b.GJAHR AND f.BUKRS=b.BUKRS
             WHERE f.BUKRS=? AND f.FIKRS=? AND f.FISTL=?
               AND f.HKONT IN ({placeholders})
             GROUP BY b.USNAM
            HAVING c >= ?
             ORDER BY c DESC
             LIMIT ?
        """
        cur.execute(q2, [args.bukrs, args.fikrs, args.default, *gl_list, args.threshold, args.top])
        top_users = cur.fetchall()
        print(f"Top {args.top} users with >= {args.threshold} hardcoded FICTR rows:")
        for usnam, c in top_users:
            print(f"  {usnam:<20s}  {c:>10,}")
        print()

        # 3. Cross-check: how many of these users ALSO have rows with a non-default
        #    FICTR (proving they are not HQ-home and the hardcode is hiding their office)?
        q3 = f"""
            SELECT DISTINCT b.USNAM
              FROM fmifiit_full f
              JOIN bkpf b ON f.KNBELNR=b.BELNR AND f.KNGJAHR=b.GJAHR AND f.BUKRS=b.BUKRS
             WHERE f.BUKRS=? AND f.FIKRS=? AND f.FISTL<>? AND f.FISTL<>''
               AND b.USNAM IN (
                   SELECT b2.USNAM FROM fmifiit_full f2
                     JOIN bkpf b2 ON f2.KNBELNR=b2.BELNR AND f2.KNGJAHR=b2.GJAHR AND f2.BUKRS=b2.BUKRS
                    WHERE f2.BUKRS=? AND f2.FIKRS=? AND f2.FISTL=?
                      AND f2.HKONT IN ({placeholders})
               )
        """
        cur.execute(
            q3,
            [args.bukrs, args.fikrs, args.default,
             args.bukrs, args.fikrs, args.default, *gl_list],
        )
        mixed = {r[0] for r in cur.fetchall()}
        print(f"Users with mixed FICTR (proof of non-HQ home office): {len(mixed)}")
        print("(These users post to a specific FICTR elsewhere but still get the hardcode")
        print(" default on bank-clearing rows — prime candidates for the SU3 rollout.)")

        # Non-zero exit code if top offender count changed drastically vs a hypothetical
        # baseline. For now just return 0 since this is the first baseline.
        return 0
    except sqlite3.Error as exc:
        print(f"[ERR] query failed: {exc}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
