#!/usr/bin/env python3
"""
bcm_role_gap_check.py

Recurring access-control check for BCM signatories: does every person
assigned to a signatory node actually hold a role that grants transaction
BNK_APP?  Being in the node (HRP1001) is NOT enough to sign — the SAP user
also needs the approve authorization (e.g. YS:FI:M:BCM_MON_APP______:<entity>).

Origin: INC-000011781 (Renata Ritter) — "You are not authorized to use
transaction BNK_APP". This is a recurring class of defect: a signatory is in
the panel but cannot validate/sign because their user has no BNK_APP role, so
the workflow item cannot route to them.

MANDATORY: run this for any "Change in Bank Signatory panel" request (any
entity) as part of the reconciliation, and emit the result in the Access
column of the mandatory output table (sap_payment_bcm_agent Step 7).

What it does (live P01, read-only):
  1. Build the set of roles that grant BNK_APP:
        AGR_1251 (OBJECT='S_TCODE', LOW='BNK_APP')   <- authorization value
        U AGR_TCODES (TCODE='BNK_APP')               <- role menu
        U BCM derived roles (YS:FI:M:BCM_MON_APP*, YS:FI:D:BCM*, YT:FI:M:BCM_MON_APP*)
  2. Build the set of users who HOLD any granting role, active today (AGR_USERS).
  3. Read active signatory assignments from the Gold DB
     (bcm_signatory_assignment, endda>=today, istat='1').
  4. For every (node, agent) flag whether the user holds a BNK_APP role.
  5. Rebuild Gold DB tables bcm_node_agent_role_check (node x agent) and
     bcm_signatory_role_gap (per user), and print the gaps.

Prereqs:
  - Gold DB tables bcm_signatory_assignment / bcm_signatory_responsibility
    populated by extract_bcm_signatories.py (refresh first for current membership).
  - RFC backend (rfc_helpers.py) reachable; P01 over SNC/SSO.

Usage:
    python bcm_role_gap_check.py                 # all entities
    python bcm_role_gap_check.py --entity UBO    # one entity (STEXT prefix)
    python bcm_role_gap_check.py --strict        # exit 1 if any gap found

Exit code:
    0 — no missing-role assignments
    1 — at least one assigned signatory has no BNK_APP role  (only with --strict; else 0)
    2 — DB / RFC / schema error
"""

# --- self-declaration, read by quality_checks/run_all.py -------------------
# An undeclared script is reported as UNCLASSIFIED and fails the runner loudly:
# a central registry is a list someone forgets to update.
QUALITY_CHECK = {
    "tier": "live",      # gate | live | analysis | quarantined
    "needs": "rfc_p01",    # gold_db | rfc_p01 | files
    "what": "needs a live P01 RFC session to read the role assignments",
}
# --------------------------------------------------------------------------

import argparse
import os
import sqlite3
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(HERE, "..", "mcp-backend-server-python")
GOLDEN = os.path.join(HERE, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
sys.path.insert(0, BACKEND)

ENTITIES = ("UBO", "UIS", "IIEP", "UIL", "UNES")


def entity_of(stext):
    for e in ENTITIES:
        if stext.startswith(e):
            return e
    return "?"


def rfc_read(conn, table, fields, where=""):
    """Single read-only RFC_READ_TABLE call (no ROWSKIPS — P01 rejects it)."""
    res = conn.call(
        "RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|", ROWCOUNT=0,
        FIELDS=[{"FIELDNAME": f} for f in fields],
        OPTIONS=[{"TEXT": where}] if where else [],
    )
    out = []
    for row in res["DATA"]:
        parts = row["WA"].split("|")
        out.append([(parts[i].strip() if i < len(parts) else "") for i in range(len(fields))])
    return out


def main():
    ap = argparse.ArgumentParser(description="BCM signatory BNK_APP role-gap check (live P01)")
    ap.add_argument("--entity", help="filter to one entity (UBO/UIS/IIEP/UIL/UNES)")
    ap.add_argument("--golden", default=GOLDEN, help="path to the Gold DB")
    ap.add_argument("--system", default="P01", help="SAP system id (default P01)")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any gap found")
    args = ap.parse_args()

    today = date.today().strftime("%Y%m%d")
    ts = date.today().strftime("%Y-%m-%dT00:00:00")

    try:
        from rfc_helpers import get_connection
    except Exception as e:  # noqa
        print(f"ERROR: cannot import rfc_helpers from {BACKEND}: {e}", file=sys.stderr)
        return 2
    try:
        conn = get_connection(args.system)
    except Exception as e:  # noqa
        print(f"ERROR: cannot connect to {args.system} (VPN/SNC?): {str(e).splitlines()[0]}", file=sys.stderr)
        return 2

    # 1) granting roles
    granting = set(r[0] for r in rfc_read(conn, "AGR_1251", ["AGR_NAME", "LOW"],
                                          "OBJECT = 'S_TCODE' AND LOW = 'BNK_APP'"))
    granting |= set(r[0] for r in rfc_read(conn, "AGR_TCODES", ["AGR_NAME", "TCODE"],
                                           "TCODE = 'BNK_APP'"))
    for pat in ("YS:FI:M:BCM_MON_APP%", "YS:FI:D:BCM%", "YT:FI:M:BCM_MON_APP%"):
        for r in rfc_read(conn, "AGR_DEFINE", ["AGR_NAME"], "AGR_NAME LIKE '" + pat + "'"):
            granting.add(r[0])

    # 2) active holders of any granting role
    holders = {}
    for role in granting:
        for r in rfc_read(conn, "AGR_USERS", ["UNAME", "TO_DAT"],
                          "AGR_NAME = '" + role.replace("'", "''") + "'"):
            un, to = r[0], r[1]
            if un and (not to or to >= today):
                holders.setdefault(un, set()).add(role)

    # 3) active signatory assignments
    try:
        db = sqlite3.connect(args.golden)
        cur = db.cursor()
        rows = cur.execute(
            "select ry_objid,rule_number,stext,pernr,uname,firstname,lastname "
            "from bcm_signatory_assignment where endda>=? and istat='1' and uname<>''",
            (today,)).fetchall()
    except Exception as e:  # noqa
        print(f"ERROR: Gold DB read failed ({args.golden}): {e}", file=sys.stderr)
        return 2

    # 4) build matrix
    cur.execute("DROP TABLE IF EXISTS bcm_node_agent_role_check")
    cur.execute("CREATE TABLE bcm_node_agent_role_check(ry_objid TEXT,rule_number TEXT,entity TEXT,"
                "node_stext TEXT,pernr TEXT,person TEXT,uname TEXT,has_bnk_app TEXT,checked_at TEXT)")
    cur.execute("DROP TABLE IF EXISTS bcm_signatory_role_gap")
    cur.execute("CREATE TABLE bcm_signatory_role_gap(uname TEXT,pernr TEXT,name TEXT,entities TEXT,"
                "has_bnk_app TEXT,granting_roles_held TEXT,source_system TEXT,checked_at TEXT)")

    per_user = {}
    node_rows = 0
    for oid, rule, stext, pernr, un, fn, ln in rows:
        ent = entity_of(stext)
        if args.entity and ent != args.entity.upper():
            continue
        held = holders.get(un, set())
        has = "Y" if held else "N"
        cur.execute("INSERT INTO bcm_node_agent_role_check VALUES (?,?,?,?,?,?,?,?,?)",
                    (oid, rule, ent, stext, pernr, f"{ln} {fn}".strip(), un, has, ts))
        node_rows += 1
        d = per_user.setdefault(un, {"pernr": pernr, "name": f"{ln} {fn}".strip(),
                                     "ents": set(), "held": held})
        d["ents"].add(ent)
    for un, d in per_user.items():
        cur.execute("INSERT INTO bcm_signatory_role_gap VALUES (?,?,?,?,?,?,?,?)",
                    (un, d["pernr"], d["name"], ",".join(sorted(d["ents"])),
                     "Y" if d["held"] else "N", ";".join(sorted(d["held"])) or "(none)",
                     args.system, ts))
    db.commit()

    # 5) report
    gaps = sorted((un, d) for un, d in per_user.items() if not d["held"])
    print(f"BCM signatory BNK_APP role check — {args.system} — {ts[:10]}"
          + (f" — entity {args.entity.upper()}" if args.entity else ""))
    print(f"  granting roles: {len(granting)} | active role-holders: {len(holders)}")
    print(f"  active signatory users: {len(per_user)} | node x agent rows: {node_rows}")
    print(f"  MISSING BNK_APP role: {len(gaps)} user(s)\n")
    if gaps:
        print("  users in a node but CANNOT open BNK_APP (grant the entity role or delimit):")
        for un, d in gaps:
            print(f"    {un:<14} {d['name'][:28]:<28} ents={','.join(sorted(d['ents']))}")
        print("\n  per-node gaps:")
        for oid, rule, ent, st, miss in cur.execute(
                "select ry_objid,rule_number,entity,node_stext,group_concat(uname) "
                "from bcm_node_agent_role_check where has_bnk_app='N' "
                "group by ry_objid,rule_number,entity,node_stext order by entity,ry_objid"):
            print(f"    {oid} {ent:<5} {rule:<10} {st[:34]:<34} -> {miss}")
    else:
        print("  OK — every assigned signatory holds a BNK_APP-granting role.")
    print("\n  persisted: bcm_node_agent_role_check, bcm_signatory_role_gap (Gold DB)")
    db.close()
    return 1 if (gaps and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
