"""
extract_bcm_signatories.py — Extract BCM signatory responsibilities (rules 90000004/90000005)
================================================================================================
Source of truth: OOCU_RESP, which writes PD infotype data in HRP1000/HRP1001.

Data model discovered from P01:
  * Responsibility groups are PD objects of OTYPE='RY' (PLVAR='01').
  * SHORT='BNK_01_01_03' → BNK_COM rule (90000004, "X signatures for all transfers" / "up to N")
  * SHORT='BNK_01_01_04' → BNK_INI rule (90000005, "X AP Validation up to N", etc.)
  * STEXT holds the user-facing description (e.g., "UNES signatures for all transfers").
  * HRP1001 RELAT='007' SCLAS='P' is the RY→Person assignment (signatory).
  * SOBID is the 8-char PERNR.

This script:
  1. Pulls every RY object with SHORT IN the two rule classes.
  2. Pulls every HRP1001/007/P assignment with validity dates.
  3. Resolves PERNRs via PA0001 (PERNR→ENAME+USRID) and PA0002 (firstname/lastname).
  4. Writes to Gold DB tables bcm_signatory_responsibility + bcm_signatory_assignment.
  5. Prints a grouped report reproducing the OOCU_RESP screen layout.

Usage:
    python extract_bcm_signatories.py
"""

import sqlite3
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from rfc_helpers import get_connection

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"

RULE_SHORTS = {
    "BNK_01_01_03": ("90000004", "BNK_COM_01_01_03"),
    "BNK_01_01_04": ("90000005", "BNK_INI_01_01_04"),
}


def rfc_read(conn, table, fields, where="", rowcount=20000):
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    rfc_options = [{"TEXT": where}] if where else []
    result = conn.call(
        "RFC_READ_TABLE",
        QUERY_TABLE=table,
        DELIMITER="|",
        ROWCOUNT=rowcount,
        ROWSKIPS=0,
        OPTIONS=rfc_options,
        FIELDS=rfc_fields,
    )
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in result.get("DATA", []):
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows


def fetch_responsibility_objects(conn):
    """Pull all RY objects for our two rule classes from HRP1000."""
    rows = []
    for short in RULE_SHORTS:
        r = rfc_read(
            conn, "HRP1000",
            ["PLVAR", "OTYPE", "OBJID", "ISTAT", "BEGDA", "ENDDA", "SHORT", "STEXT"],
            where=f"OTYPE = 'RY' AND SHORT = '{short}'",
            rowcount=200,
        )
        for rec in r:
            rec["_rule_number"], rec["_rule_class"] = RULE_SHORTS[short]
        rows.extend(r)
    # Dedupe on (PLVAR, OTYPE, OBJID, BEGDA) — HRP1000 can hold historical rows.
    seen = {}
    for rec in rows:
        k = (rec["PLVAR"], rec["OTYPE"], rec["OBJID"])
        # Prefer active (ISTAT='1') rows
        if k not in seen or rec.get("ISTAT") == "1":
            seen[k] = rec
    return list(seen.values())


def fetch_assignments(conn, ry_objids):
    """Pull HRP1001 RY->P assignments with RELAT='007' (one OBJID at a time, SAP security rejects IN)."""
    rows = []
    for objid in ry_objids:
        r = rfc_read(
            conn, "HRP1001",
            ["OTYPE", "OBJID", "RELAT", "ISTAT", "SCLAS", "SOBID", "BEGDA", "ENDDA"],
            where=f"OTYPE = 'RY' AND OBJID = '{objid}' AND RELAT = '007' AND SCLAS = 'P'",
            rowcount=2000,
        )
        rows.extend(r)
    return rows


def fetch_personnel(conn, pernrs):
    """Resolve PERNR -> name (PA0002) + SAP user (PA0105/0001) + email (PA0105/0010)."""
    if not pernrs:
        return {}
    result = {}
    for i, pernr in enumerate(pernrs):
        padded = pernr.zfill(8)
        info = {"pernr": pernr, "firstname": "", "lastname": "", "uname": "", "email": ""}

        # Name from PA0002 (latest record)
        try:
            r = rfc_read(
                conn, "PA0002",
                ["BEGDA", "VORNA", "NACHN"],
                where=f"PERNR = '{padded}'",
                rowcount=20,
            )
            if r:
                latest = max(r, key=lambda x: x["BEGDA"])
                info["firstname"] = latest["VORNA"].strip()
                info["lastname"] = latest["NACHN"].strip()
        except Exception:
            pass

        # SAP user + email from PA0105
        try:
            r = rfc_read(
                conn, "PA0105",
                ["SUBTY", "BEGDA", "USRID", "USRID_LONG"],
                where=f"PERNR = '{padded}'",
                rowcount=30,
            )
            # Keep latest valid record per subtype
            by_subty = {}
            for rec in r:
                st = rec["SUBTY"]
                if st not in by_subty or rec["BEGDA"] > by_subty[st]["BEGDA"]:
                    by_subty[st] = rec
            if "0001" in by_subty:
                info["uname"] = by_subty["0001"]["USRID"].strip()
            if "0010" in by_subty:
                info["email"] = by_subty["0010"]["USRID_LONG"].strip()
        except Exception:
            pass

        result[pernr] = info
        if (i + 1) % 20 == 0:
            print(f"      ...resolved {i + 1}/{len(pernrs)}")
    return result


def sqlite_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS bcm_signatory_responsibility (
        plvar       TEXT,
        objid       TEXT,
        short       TEXT,
        stext       TEXT,
        rule_number TEXT,
        rule_class  TEXT,
        istat       TEXT,
        begda       TEXT,
        endda       TEXT,
        extracted_at TEXT,
        PRIMARY KEY (plvar, objid)
    );
    CREATE TABLE IF NOT EXISTS bcm_signatory_assignment (
        plvar       TEXT,
        ry_objid    TEXT,
        rule_class  TEXT,
        rule_number TEXT,
        stext       TEXT,
        pernr       TEXT,
        begda       TEXT,
        endda       TEXT,
        firstname   TEXT,
        lastname    TEXT,
        uname       TEXT,
        email       TEXT,
        istat       TEXT,
        extracted_at TEXT,
        PRIMARY KEY (plvar, ry_objid, pernr, begda)
    );
    """)


def save_to_gold(responsibilities, assignments, personnel):
    db = sqlite3.connect(DB_PATH)
    sqlite_schema(db)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = db.cursor()

    for r in responsibilities:
        cur.execute(
            "INSERT OR REPLACE INTO bcm_signatory_responsibility VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r["PLVAR"], r["OBJID"], r["SHORT"], r["STEXT"],
             r["_rule_number"], r["_rule_class"],
             r["ISTAT"], r["BEGDA"], r["ENDDA"], now),
        )

    # Clear old assignment rows (we're writing full snapshot for these two rules)
    cur.execute("DELETE FROM bcm_signatory_assignment WHERE rule_number IN ('90000004','90000005')")

    # Build STEXT/rule lookup by OBJID
    ry_lookup = {r["OBJID"]: r for r in responsibilities}
    for a in assignments:
        ry = ry_lookup.get(a["OBJID"])
        if not ry:
            continue
        pernr = a["SOBID"].strip().lstrip("0") or "0"
        person = personnel.get(pernr, {})
        cur.execute(
            "INSERT OR REPLACE INTO bcm_signatory_assignment VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (a.get("PLVAR", "01"), a["OBJID"], ry["_rule_class"], ry["_rule_number"],
             ry["STEXT"], pernr, a["BEGDA"], a["ENDDA"],
             person.get("firstname", ""), person.get("lastname", ""),
             person.get("uname", ""), person.get("email", ""),
             a["ISTAT"], now),
        )

    db.commit()
    db.close()


def fmt_date(yyyymmdd):
    if not yyyymmdd or len(yyyymmdd) != 8 or yyyymmdd == "99991231":
        return "Unlimited"
    return f"{yyyymmdd[6:8]}.{yyyymmdd[4:6]}.{yyyymmdd[0:4]}"


def print_report(responsibilities, assignments, personnel):
    print()
    print("=" * 90)
    print("BCM SIGNATORY RESPONSIBILITIES — rules 90000004 / 90000005")
    print("=" * 90)

    # Group by rule class, then by responsibility group (RY OBJID)
    grouped = defaultdict(lambda: defaultdict(list))
    ry_lookup = {r["OBJID"]: r for r in responsibilities}
    for a in assignments:
        ry = ry_lookup.get(a["OBJID"])
        if not ry:
            continue
        grouped[ry["_rule_class"]][a["OBJID"]].append(a)

    for rule_class in sorted(grouped.keys()):
        rule_number = RULE_SHORTS[[k for k, v in RULE_SHORTS.items() if v[1] == rule_class][0]][0]
        print(f"\n>>> RULE {rule_number} — {rule_class}")
        print("-" * 90)

        for ry_objid, assigns in sorted(grouped[rule_class].items()):
            ry = ry_lookup[ry_objid]
            print(f"\n  [{ry_objid}] {ry['STEXT']}")
            print(f"  {'PERNR':<10}{'SAP User':<14}{'Name':<40}{'From':<13}{'Until':<13}")
            print(f"  {'-'*10}{'-'*14}{'-'*40}{'-'*13}{'-'*13}")
            for a in sorted(assigns, key=lambda x: (x["BEGDA"], x["SOBID"])):
                pernr = a["SOBID"].strip().lstrip("0") or "0"
                p = personnel.get(pernr, {})
                fullname = f"{p.get('firstname','')} {p.get('lastname','')}".strip()
                print(f"  {pernr:<10}{p.get('uname',''):<14}{fullname[:38]:<40}"
                      f"{fmt_date(a['BEGDA']):<13}{fmt_date(a['ENDDA']):<13}")

    # Summary
    print()
    print("=" * 90)
    total_ry = len(responsibilities)
    total_assign = len(assignments)
    unique_pernr = len({a["SOBID"].strip() for a in assignments})
    print(f"Responsibility groups: {total_ry}")
    print(f"Total assignments:     {total_assign}")
    print(f"Unique signatories:    {unique_pernr}")
    print("=" * 90)


def main():
    print("[1/4] Connecting to P01...")
    conn = get_connection("P01")
    print("      Connected.")

    print("[2/4] Pulling RY responsibility groups from HRP1000...")
    resps = fetch_responsibility_objects(conn)
    print(f"      Found {len(resps)} responsibility groups.")

    ry_objids = sorted({r["OBJID"] for r in resps})
    print("[3/4] Pulling RY->Person assignments from HRP1001...")
    assigns = fetch_assignments(conn, ry_objids)
    print(f"      Found {len(assigns)} assignments.")

    pernrs = sorted({a["SOBID"].strip().lstrip("0") or "0" for a in assigns})
    print(f"[4/4] Resolving {len(pernrs)} PERNRs via PA0001...")
    personnel = fetch_personnel(conn, pernrs)
    print(f"      Resolved {len(personnel)} names.")

    conn.close()

    save_to_gold(resps, assigns, personnel)
    print(f"\n      Saved to {DB_PATH.name}")
    print(f"      Tables: bcm_signatory_responsibility, bcm_signatory_assignment")

    print_report(resps, assigns, personnel)


if __name__ == "__main__":
    main()
