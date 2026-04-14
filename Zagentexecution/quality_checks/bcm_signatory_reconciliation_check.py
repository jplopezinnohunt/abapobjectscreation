#!/usr/bin/env python3
"""
bcm_signatory_reconciliation_check.py

Recurring data-quality check for the BCM signatory configuration
(rules 90000004 BNK_COM and 90000005 BNK_INI).

Discovered during INC-000006313 (2026-04-09). Three classes of defect this
check detects against the current Gold DB snapshot of HRP1001:

  (1) GHOST PERNR — a BCM row whose SOBID exists in PA0002 but has NO
      PA0105 SUBTY='0001' (SAP USRID). The workflow cannot route a work
      item to such a signatory; they are silently disabled.
        Historical example: Svein OESTTVEIT, ghost PERNR 10567156
        (real PERNR 10067156, user S_OESTTVEIT).

  (2) ROLE-SPLIT INCONSISTENCY — a user appears on only one of the two
      rules (INI or COM) for the same entity, but the bank's carton des
      signatures lists them as authorized to sign jointly. This means
      the SAP workflow denies them a step they are authorized to do.

  (3) ENTITY-VS-BANK PANEL DRIFT — a list of active SAP signatories per
      entity that can then be diffed manually against each bank account's
      carton des signatures. SAP responsibility groups are ENTITY-LEVEL,
      not bank-account-level, so strict reconciliation requires ALL bank
      cartons for the entity.

Prereqs:
    - Gold DB at Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db
    - Tables `bcm_signatory_assignment` and `bcm_signatory_responsibility`
      populated by `extract_bcm_signatories.py`.

Usage:
    # All entities, default as-of today
    python bcm_signatory_reconciliation_check.py

    # Single entity (substring match on STEXT)
    python bcm_signatory_reconciliation_check.py --entity UIS

    # Diff SAP against a provided carton file (PERNRs, one per line)
    python bcm_signatory_reconciliation_check.py --entity UIS \\
        --carton cartons/uis_citibank_canada_20260402.txt

Exit code:
    0 — no defects detected (or only soft warnings)
    1 — at least one GHOST PERNR or carton mismatch found
    2 — DB / schema error
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Zagentexecution", "sap_data_extraction", "sqlite", "p01_gold_master_data.db",
)


def today_yyyymmdd():
    return datetime.now().strftime("%Y%m%d")


def check_ghost_pernrs(cur, asof):
    """A ghost PERNR is one that appears in bcm_signatory_assignment (active row)
    but has uname='' — meaning our PA0105/0001 lookup at extraction time was empty."""
    rows = cur.execute(
        """
        SELECT DISTINCT pernr, stext, rule_number, firstname || ' ' || lastname AS name,
               begda, endda
        FROM bcm_signatory_assignment
        WHERE endda >= ?
          AND (uname IS NULL OR uname = '')
        ORDER BY pernr, rule_number
        """,
        (asof,),
    ).fetchall()
    return rows


def check_role_split(cur, asof, entity_filter=None):
    """Find users on only one of {COM, INI} rules for the same entity."""
    entity_clause = "AND stext LIKE ?" if entity_filter else ""
    params = [asof]
    if entity_filter:
        params.append(f"%{entity_filter}%")

    com_rows = cur.execute(
        f"""
        SELECT DISTINCT pernr, uname, firstname || ' ' || lastname AS name, stext
        FROM bcm_signatory_assignment
        WHERE rule_number = '90000004' AND endda >= ? {entity_clause}
        """,
        params,
    ).fetchall()

    ini_rows = cur.execute(
        f"""
        SELECT DISTINCT pernr, uname, firstname || ' ' || lastname AS name, stext
        FROM bcm_signatory_assignment
        WHERE rule_number = '90000005' AND endda >= ? {entity_clause}
        """,
        params,
    ).fetchall()

    com_pernrs = {r[0] for r in com_rows}
    ini_pernrs = {r[0] for r in ini_rows}

    com_only = com_pernrs - ini_pernrs
    ini_only = ini_pernrs - com_pernrs

    com_details = [r for r in com_rows if r[0] in com_only]
    ini_details = [r for r in ini_rows if r[0] in ini_only]
    return com_details, ini_details


def entity_snapshot(cur, asof, entity):
    """Snapshot of all active signatories for an entity, grouped by rule+stext."""
    rows = cur.execute(
        """
        SELECT rule_number, stext, pernr, uname,
               firstname || ' ' || lastname AS name, begda, endda
        FROM bcm_signatory_assignment
        WHERE endda >= ?
          AND stext LIKE ?
        ORDER BY rule_number, stext, lastname
        """,
        (asof, f"%{entity}%"),
    ).fetchall()
    return rows


def diff_against_carton(cur, asof, entity, carton_path):
    """Given a file with one PERNR per line, diff SAP active signatories
    (for the entity) against the carton list."""
    with open(carton_path, "r", encoding="utf-8") as f:
        carton_pernrs = {
            line.split("#", 1)[0].strip().lstrip("0")
            for line in f if line.strip() and not line.strip().startswith("#")
        }

    rows = cur.execute(
        """
        SELECT DISTINCT pernr, uname, firstname || ' ' || lastname AS name,
               rule_number, stext
        FROM bcm_signatory_assignment
        WHERE endda >= ?
          AND stext LIKE ?
        """,
        (asof, f"%{entity}%"),
    ).fetchall()

    sap_pernrs = {r[0].lstrip("0") for r in rows}
    sap_by_pernr = {}
    for r in rows:
        sap_by_pernr.setdefault(r[0].lstrip("0"), []).append(r)

    extras = sap_pernrs - carton_pernrs       # in SAP, not on carton
    missing = carton_pernrs - sap_pernrs      # on carton, not in SAP
    match = sap_pernrs & carton_pernrs

    return sap_by_pernr, extras, missing, match


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to Gold DB sqlite file")
    ap.add_argument("--asof", default=today_yyyymmdd(),
                    help="Cutoff date YYYYMMDD (default: today). "
                         "Rows with ENDDA < asof are ignored.")
    ap.add_argument("--entity", default=None,
                    help="Filter STEXT containing this substring (e.g. UIS, UNES, IIEP, UBO, UIL)")
    ap.add_argument("--carton", default=None,
                    help="Path to a file with one PERNR per line (# comments ok). "
                         "Requires --entity.")
    ap.add_argument("--quiet", action="store_true", help="Only print defects")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: Gold DB not found: {args.db}", file=sys.stderr)
        return 2

    try:
        con = sqlite3.connect(args.db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bcm_signatory_assignment'")
        if not cur.fetchone():
            print("ERROR: table bcm_signatory_assignment not in Gold DB. "
                  "Run extract_bcm_signatories.py first.", file=sys.stderr)
            return 2
    except sqlite3.Error as e:
        print(f"DB error: {e}", file=sys.stderr)
        return 2

    exit_code = 0

    # --- Check 1: Ghost PERNRs (always run, all entities) ---
    print("=" * 78)
    print(f"[1] GHOST PERNR CHECK — active signatories with empty PA0105/0001 SAP user")
    print(f"    (as of {args.asof})")
    print("=" * 78)
    ghosts = check_ghost_pernrs(cur, args.asof)
    if ghosts:
        print(f"FOUND {len(ghosts)} ghost row(s):")
        for pernr, stext, rule, name, begda, endda in ghosts:
            print(f"  PERNR={pernr}  rule={rule}  group={stext!r}")
            print(f"    name={name!r}  period={begda}->{endda}")
        print("\nImpact: workflow 90000003 cannot route a work item to these PERNRs.")
        print("Action: investigate the PERNR in PA0002/PA0105, find the real PERNR,")
        print("        delimit the ghost row and insert the correct one.")
        exit_code = 1
    else:
        print("  No ghost PERNRs detected.")
    print()

    # --- Check 2: Role-split inconsistency ---
    print("=" * 78)
    label = f" for entity matching {args.entity!r}" if args.entity else ""
    print(f"[2] ROLE-SPLIT CHECK{label} — users on only one of INI/COM rules")
    print("=" * 78)
    com_only, ini_only = check_role_split(cur, args.asof, args.entity)
    if com_only or ini_only:
        if com_only:
            print(f"On COM (90000004) but NOT on INI (90000005): {len(com_only)}")
            for pernr, uname, name, stext in com_only:
                print(f"  {pernr}  {uname:<14} {name}  ({stext})")
        if ini_only:
            print(f"On INI (90000005) but NOT on COM (90000004): {len(ini_only)}")
            for pernr, uname, name, stext in ini_only:
                print(f"  {pernr}  {uname:<14} {name}  ({stext})")
        print("\nImpact: user can only perform ONE of the two signature steps even")
        print("        though the bank carton may authorize both. Confirm with TRS")
        print("        whether the split is intentional (e.g., Treasurer commits only).")
    else:
        if not args.quiet:
            print("  No role-split inconsistencies detected.")
    print()

    # --- Check 3: Entity snapshot + optional carton diff ---
    if args.entity:
        print("=" * 78)
        print(f"[3] SAP ACTIVE SIGNATORIES — entity {args.entity!r}")
        print("=" * 78)
        snapshot = entity_snapshot(cur, args.asof, args.entity)
        if not snapshot:
            print(f"  No active signatories for {args.entity!r}.")
        else:
            last_key = None
            for rule, stext, pernr, uname, name, begda, endda in snapshot:
                key = (rule, stext)
                if key != last_key:
                    print(f"\n  [{rule}] {stext}")
                    print(f"  {'PERNR':<10}{'User':<14}{'Name':<35}{'From':<10}{'Until':<10}")
                    print(f"  {'-'*9} {'-'*13} {'-'*34} {'-'*9} {'-'*9}")
                    last_key = key
                print(f"  {pernr:<10}{uname:<14}{name[:33]:<35}{begda:<10}{endda:<10}")
        print()

        if args.carton:
            print("=" * 78)
            print(f"[4] CARTON DIFF — SAP vs {args.carton}")
            print("=" * 78)
            if not os.path.exists(args.carton):
                print(f"  ERROR: carton file not found: {args.carton}", file=sys.stderr)
                exit_code = 2
            else:
                sap_by_pernr, extras, missing, match = diff_against_carton(
                    cur, args.asof, args.entity, args.carton
                )
                print(f"  MATCH   ({len(match)}): {', '.join(sorted(match)) or '-'}")
                if extras:
                    print(f"\n  EXTRAS  ({len(extras)}) — in SAP, NOT on carton:")
                    for p in sorted(extras):
                        for _, uname, name, rule, stext in sap_by_pernr[p]:
                            print(f"    {p}  {uname:<14} {name:<35} rule={rule}  group={stext!r}")
                    print("  -> may be legitimate if entity has other bank accounts with different panels")
                    exit_code = 1
                if missing:
                    print(f"\n  MISSING ({len(missing)}) — on carton, NOT in SAP:")
                    for p in sorted(missing):
                        print(f"    {p}  (not active in any SAP {args.entity} group)")
                    print("  -> these people are authorized at the bank but cannot sign in SAP")
                    exit_code = 1
                if not extras and not missing:
                    print("  Perfect match — no reconciliation gap.")
        print()

    # Summary
    print("=" * 78)
    print(f"Exit code: {exit_code}")
    print("=" * 78)
    con.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
