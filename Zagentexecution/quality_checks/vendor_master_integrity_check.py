"""
Vendor Master Integrity Check
=============================

Detects vendors whose LFB1.AKONT (reconciliation account) diverges from the
canonical mapping for their LFA1.KTOKK (vendor account group).

Background — INC-000006073 (Session #048):
  Vendor 10133079 (Katja HINZ) had KTOKK=SCSA + AKONT=2021011 in IIEP company code.
  The canonical AKONT for KTOKK=SCSA is 2021061 (used by 6,101 vendors).
  AKONT=2021011 is NOT covered by any GGB1 substitution rule for business area
  derivation, which silently broke travel posting on the first cross-funded
  intercompany trip (IIEP traveler on UNES budget).

The defect is a CLASS, not a one-off. This script enumerates the class.

Usage:
    python vendor_master_integrity_check.py                       # full scan, all KTOKK
    python vendor_master_integrity_check.py --vendor 10133079     # one vendor
    python vendor_master_integrity_check.py --ktokk SCSA          # one account group
    python vendor_master_integrity_check.py --ktokk SCSA --bukrs IIEP
    python vendor_master_integrity_check.py --json                # machine-readable
    python vendor_master_integrity_check.py --threshold 0.05      # AKONTs covering <5% are outliers
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from pathlib import Path

GOLD_DB = Path(__file__).resolve().parents[1] / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Outlier definition: an AKONT that is used by < threshold of vendors with the
# same (KTOKK, BUKRS) AND is not the top-2 most common is considered a
# deviation from the canonical mapping. Threshold catches Katja HINZ
# (KTOKK=SCSA, BUKRS=IIEP, AKONT=2021011, share = 4 / 91 = 4.4%).
DEFAULT_OUTLIER_THRESHOLD = 0.05   # 5%


def open_db() -> sqlite3.Connection:
    if not GOLD_DB.exists():
        sys.exit(f"Gold DB not found at {GOLD_DB}")
    conn = sqlite3.connect(str(GOLD_DB))
    conn.row_factory = sqlite3.Row
    return conn


def build_canonical_map(conn: sqlite3.Connection, threshold: float):
    """For each (KTOKK, BUKRS) combo, compute:
       - the modal AKONT (most common)
       - the share of each AKONT
       Returns: { (KTOKK, BUKRS): { 'modal': '0002021061',
                                    'akont_share': { '0002021061': 0.88, '0002021042': 0.11, ... },
                                    'total': 6902 } }
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.KTOKK, b.BUKRS, b.AKONT, COUNT(*) AS cnt
        FROM LFA1 a JOIN LFB1 b ON a.LIFNR = b.LIFNR AND a.MANDT = b.MANDT
        WHERE a.KTOKK <> '' AND b.AKONT <> ''
        GROUP BY a.KTOKK, b.BUKRS, b.AKONT
        """
    )
    canonical = {}
    for ktokk, bukrs, akont, cnt in cur.fetchall():
        key = (ktokk, bukrs)
        canonical.setdefault(key, {"akont_counts": {}, "total": 0})
        canonical[key]["akont_counts"][akont] = cnt
        canonical[key]["total"] += cnt

    for key, info in canonical.items():
        total = info["total"]
        info["akont_share"] = {a: c / total for a, c in info["akont_counts"].items()}
        # Sort AKONTs by descending count
        ranked = sorted(info["akont_counts"].items(), key=lambda kv: -kv[1])
        info["ranked_akonts"] = [a for a, _ in ranked]
        info["modal"] = ranked[0][0]
        info["modal_share"] = info["akont_share"][info["modal"]]
        # An outlier is: NOT the top-2 ranked AND share < threshold.
        # Top-2 protection avoids flagging natural bimodal distributions
        # (e.g., when two AKONTs both legitimately exist in a group).
        top2 = set(info["ranked_akonts"][:2])
        info["outlier_akonts"] = [
            a for a in info["ranked_akonts"]
            if a not in top2 and info["akont_share"][a] < threshold
        ]
    return canonical


def find_violations(conn, canonical, where_clauses, params):
    cur = conn.cursor()
    base_q = """
        SELECT a.LIFNR, a.NAME1, a.KTOKK, b.BUKRS, b.AKONT, b.PERNR
        FROM LFA1 a JOIN LFB1 b ON a.LIFNR = b.LIFNR AND a.MANDT = b.MANDT
        WHERE a.KTOKK <> '' AND b.AKONT <> ''
    """
    if where_clauses:
        base_q += " AND " + " AND ".join(where_clauses)
    cur.execute(base_q, params)

    violations = []
    for lifnr, name1, ktokk, bukrs, akont, pernr in cur.fetchall():
        info = canonical.get((ktokk, bukrs))
        if not info:
            continue
        if akont in info["outlier_akonts"]:
            violations.append(
                {
                    "lifnr": lifnr.strip(),
                    "name1": (name1 or "").strip(),
                    "ktokk": ktokk,
                    "bukrs": bukrs,
                    "akont": akont,
                    "pernr": (pernr or "").strip(),
                    "expected_modal_akont": info["modal"],
                    "modal_share_pct": round(info["modal_share"] * 100, 1),
                    "outlier_akont_share_pct": round(info["akont_share"][akont] * 100, 2),
                    "peers_in_group": info["total"],
                }
            )
    return violations


def cross_check_ggb1_coverage(conn, violations):
    """For each violation, see if its AKONT is covered by any YTFI_BA_SUBST rule
    (which would mean GGB1 substitution might still rescue it). Annotate the
    violation with `ggb1_covered: True/False`. AKONT in YTFI_BA_SUBST.LOW is
    stored with leading zeros, e.g. '0002021011'.
    """
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT LOW FROM YTFI_BA_SUBST")
    covered = {row[0].strip().lstrip("0") for row in cur.fetchall() if row[0]}
    for v in violations:
        akont_norm = v["akont"].lstrip("0")
        v["ggb1_covered"] = akont_norm in covered
    return violations


def render_text(violations, canonical, args):
    print("=" * 80)
    print("VENDOR MASTER INTEGRITY CHECK")
    print("=" * 80)
    print(f"Gold DB:    {GOLD_DB}")
    print(f"Threshold:  AKONT used by <{args.threshold * 100:.1f}% of group is an outlier")
    print()
    print(f"Total (KTOKK,BUKRS) groups analyzed: {len(canonical)}")
    print(f"Violations found: {len(violations)}")
    print()
    if not violations:
        print("PASS — no vendors with outlier AKONT for their account group.")
        return

    print("FAIL — vendors with outlier AKONT (same defect class as INC-000006073):")
    print()
    print(f"{'LIFNR':<12} {'KTOKK':<6} {'BUKRS':<6} {'AKONT':<12} {'Expected':<12} "
          f"{'Share%':>7} {'Peers':>7} {'GGB1?':<5} NAME1")
    print("-" * 110)

    grouped = {}
    for v in violations:
        grouped.setdefault((v["ktokk"], v["bukrs"], v["akont"]), []).append(v)

    for (ktokk, bukrs, akont), items in sorted(grouped.items(),
                                                key=lambda kv: -len(kv[1])):
        for v in items:
            ggb1_flag = "yes" if v.get("ggb1_covered") else "NO"
            print(f"{v['lifnr']:<12} {ktokk:<6} {bukrs:<6} {akont:<12} "
                  f"{v['expected_modal_akont']:<12} {v['outlier_akont_share_pct']:>6.2f}% "
                  f"{v['peers_in_group']:>7} {ggb1_flag:<5} {v['name1'][:30]}")
        print()  # blank line per group

    # Summary by group
    print("=" * 80)
    print("SUMMARY BY DEFECT CLASS")
    print("=" * 80)
    print(f"{'KTOKK':<6} {'BUKRS':<6} {'Outlier AKONT':<14} {'Count':>7} {'GGB1 covered':<14}")
    print("-" * 60)
    for (ktokk, bukrs, akont), items in sorted(grouped.items(),
                                                key=lambda kv: -len(kv[1])):
        ggb1 = "yes" if items[0].get("ggb1_covered") else "NO (RISK)"
        print(f"{ktokk:<6} {bukrs:<6} {akont:<14} {len(items):>7} {ggb1:<14}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vendor", help="Restrict to one LIFNR")
    p.add_argument("--ktokk", help="Restrict to one account group")
    p.add_argument("--bukrs", help="Restrict to one company code")
    p.add_argument("--threshold", type=float, default=DEFAULT_OUTLIER_THRESHOLD,
                   help=f"Outlier threshold (default {DEFAULT_OUTLIER_THRESHOLD})")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = p.parse_args()

    conn = open_db()

    where = []
    params = []
    if args.vendor:
        where.append("a.LIFNR = ?")
        params.append(args.vendor.zfill(10))
    if args.ktokk:
        where.append("a.KTOKK = ?")
        params.append(args.ktokk.upper())
    if args.bukrs:
        where.append("b.BUKRS = ?")
        params.append(args.bukrs.upper())

    canonical = build_canonical_map(conn, args.threshold)
    violations = find_violations(conn, canonical, where, params)
    violations = cross_check_ggb1_coverage(conn, violations)

    if args.json:
        print(json.dumps(
            {
                "threshold": args.threshold,
                "groups_analyzed": len(canonical),
                "violations_count": len(violations),
                "violations": violations,
            },
            indent=2,
        ))
    else:
        render_text(violations, canonical, args)

    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
