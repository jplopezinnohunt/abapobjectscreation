"""
INC-000005240 — live RFC diagnostic (READ-ONLY, P01)
=====================================================
Pulls USR05 for AL_JONATHAN and a handful of comparison users, then pulls
BSAK (vendor cleared items) for AL_JONATHAN's recent FBZ1/FBZ2 documents
to verify the actual XREF1/XREF2 values written by the substitution chain.

Usage:
    python INC-000005240_live_diagnostic.py

This is diagnostic-only. It writes nothing to Gold DB. Output goes to stdout
and to a JSON next to this script for the incident report evidence section.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))

from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

GOLD_DB = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

OUT = Path(__file__).with_suffix(".json")

SUBJECT_USER = "AL_JONATHAN"

# Top active posters (from Gold DB query, Dec/2025-March/2026 UNES) + a few
# extra to vary the office landscape
COMPARISON_USERS = [
    "AL_JONATHAN",
    "T_ENG",
    "S_EARLE",
    "C_LOPEZ",
    "I_MARQUAND",
    "B_GAZI",
    "I_WETTIE",
    "S_AGOSTO",
    "JJ_YAKI-PAHI",
    "L_HANGI",
    "O_RASHIDI",
    "DA_ENGONGA",
]


def read_usr05(guard, bnames):
    """Read USR05 one user at a time.

    USR05 blocks RFC_READ_TABLE with IN (...) WHERE clauses (SAP "suspicious
    WHERE condition" safety check on security-sensitive tables). Read per user.
    """
    all_rows = []
    for b in bnames:
        try:
            rows = rfc_read_paginated(
                guard,
                table="USR05",
                fields=["BNAME", "PARID", "PARVA"],
                where=f"BNAME = '{b}'",
                batch_size=500,
            )
            all_rows.extend(rows)
        except Exception as e:
            print(f"    USR05 read failed for {b}: {e}")
    return all_rows


def read_user_fbz_docs_from_gold(bname):
    """Read BKPF header rows from local Gold DB (already extracted, faster)."""
    c = sqlite3.connect(str(GOLD_DB)).cursor()
    c.execute(
        """
        SELECT BUKRS, BELNR, GJAHR, BUDAT, TCODE, USNAM, XBLNR, BLART
        FROM bkpf
        WHERE BUKRS = 'UNES'
          AND USNAM = ?
          AND TCODE IN ('FBZ1','FBZ2','F-53')
          AND BUDAT BETWEEN '20251201' AND '20260331'
        ORDER BY BUDAT
        """,
        (bname,),
    )
    cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in c.fetchall()]


def read_line_items_for_docs(guard, doc_keys, tables=("BSAK", "BSAS", "BSIS", "BSIK", "BSAD", "BSID")):
    """Read BSEG line items across all 6 clearing/open tables for specific docs.

    doc_keys: list of (BUKRS, BELNR, GJAHR) tuples. Reads one doc per table
    per call to dodge the 72-char WHERE-line limit and SAIS suspicious-WHERE.
    """
    all_rows = []
    # Fields common to all 6 tables
    common_fields = [
        "BUKRS", "GJAHR", "BELNR", "BUZEI",
        "XREF1", "XREF2", "XREF3",
        "ZUONR", "WRBTR", "SHKZG", "BLART", "BUDAT", "HKONT",
    ]
    for table in tables:
        # BSAK/BSIK have LIFNR, BSAD/BSID have KUNNR, BSAS/BSIS have neither
        fields = list(common_fields)
        if table in ("BSAK", "BSIK"):
            fields.append("LIFNR")
        elif table in ("BSAD", "BSID"):
            fields.append("KUNNR")
        for (b, n, g) in doc_keys:
            where = f"BUKRS = '{b}' AND BELNR = '{n}' AND GJAHR = '{g}'"
            try:
                rows = rfc_read_paginated(
                    guard, table=table, fields=fields, where=where, batch_size=500,
                )
                for r in rows:
                    r["_source_table"] = table
                all_rows.extend(rows)
            except Exception as e:
                print(f"    {table} read failed for {b}/{n}/{g}: {e}")
    return all_rows


def main():
    print(f"Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    out = {"subject": SUBJECT_USER}

    # ---- 1. USR05 for comparison users ---------------------------------
    print(f"Step 1 — USR05 for {len(COMPARISON_USERS)} users...")
    usr05_rows = read_usr05(guard, COMPARISON_USERS)
    print(f"  Returned {len(usr05_rows)} PARID rows")
    out["usr05_rows"] = usr05_rows

    by_user = {}
    for r in usr05_rows:
        by_user.setdefault(r["BNAME"].strip(), []).append(
            (r["PARID"].strip(), r["PARVA"].strip())
        )

    print("\n  Per-user PARID dump:")
    for u in COMPARISON_USERS:
        rows = by_user.get(u, [])
        relevant = [p for p in rows if p[0] in ("Y_USERFO", "FOCOD", "Y_FO", "BUK")]
        y_userfo = next((pv for pid, pv in rows if pid == "Y_USERFO"), None)
        marker = "[SUBJECT]" if u == SUBJECT_USER else ""
        print(f"    {u:16s} {len(rows):3} PARIDs  Y_USERFO={y_userfo!r:20s} {marker}")
        if u == SUBJECT_USER and rows:
            print(f"      FULL PARID list for {u}:")
            for pid, pv in rows:
                print(f"        {pid:20s} = {pv!r}")

    out["by_user_y_userfo"] = {
        u: next((pv for pid, pv in rows if pid == "Y_USERFO"), None)
        for u, rows in by_user.items()
    }

    # ---- 2. AL_JONATHAN's FBZ1/FBZ2 documents (from Gold DB) -----------
    print(f"\nStep 2 — BKPF docs for {SUBJECT_USER} (Gold DB, FBZ1/FBZ2/F-53, Dec/2025-March/2026)...")
    bkpf_rows = read_user_fbz_docs_from_gold(SUBJECT_USER)
    print(f"  Returned {len(bkpf_rows)} documents")
    out["bkpf_rows"] = bkpf_rows

    doc_keys = [(r["BUKRS"], r["BELNR"], r["GJAHR"]) for r in bkpf_rows]
    for r in bkpf_rows:
        print(f"    {r['BUDAT']} {r['BELNR']}/{r['GJAHR']} {r['TCODE']} {r['BLART']} XBLNR={r['XBLNR']!r}")

    # ---- 3. All BSEG line items across 6 tables ------------------------
    print(f"\nStep 3 — Full BSEG line-item sweep (BSAK/BSAS/BSIS/BSIK/BSAD/BSID) for {len(doc_keys)} docs...")
    all_lines = read_line_items_for_docs(guard, doc_keys)
    print(f"  Returned {len(all_lines)} line items")
    out["all_line_items"] = all_lines

    # CRITICAL: save JSON BEFORE any printing that could fail
    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"  Raw data written to: {OUT}")

    # Dump raw keys of first row to diagnose any field-name loss
    if all_lines:
        print(f"\n  First row keys: {sorted(all_lines[0].keys())}")

    # Breakdown by source table
    from collections import Counter
    by_table = Counter(r.get("_source_table", "?") for r in all_lines)
    print(f"  By source table: {dict(by_table)}")

    # Defensive printing — use .get() for every field
    def g(r, k):
        v = r.get(k, "")
        return str(v).strip() if v else ""

    print("\n  ALL line items (defensive print):")
    try:
        sorted_rows = sorted(
            all_lines,
            key=lambda x: (g(x, "BUDAT"), g(x, "BELNR"), g(x, "BUZEI"))
        )
    except Exception as e:
        print(f"    sort failed: {e}")
        sorted_rows = all_lines
    for r in sorted_rows:
        partner = g(r, "LIFNR") or g(r, "KUNNR") or "-"
        print(
            f"    {g(r,'BUDAT'):10s} {g(r,'BELNR'):10s}/{g(r,'GJAHR'):4s} "
            f"L{g(r,'BUZEI'):>3s} "
            f"{r.get('_source_table','?'):4s} "
            f"HKONT={g(r,'HKONT'):10s} "
            f"P={partner:<10} "
            f"XREF1={g(r,'XREF1')!r:14s} "
            f"XREF2={g(r,'XREF2')!r:14s} "
            f"XREF3={g(r,'XREF3')!r:14s} "
            f"ZUONR={g(r,'ZUONR')!r}"
        )

    # ---- Summary -------------------------------------------------------
    al_y_userfo = out["by_user_y_userfo"].get(SUBJECT_USER)
    al_xref1_set = {g(r, "XREF1") for r in all_lines}
    al_xref2_set = {g(r, "XREF2") for r in all_lines}
    al_xref3_set = {g(r, "XREF3") for r in all_lines}
    print("\n" + "=" * 80)
    print(f"SUMMARY for {SUBJECT_USER}:")
    print(f"  USR05 Y_USERFO PARVA        : {al_y_userfo!r}")
    print(f"  Distinct XREF1 values       : {sorted(al_xref1_set)}")
    print(f"  Distinct XREF2 values       : {sorted(al_xref2_set)}")
    print(f"  Distinct XREF3 values       : {sorted(al_xref3_set)}")
    print(f"  Total line items            : {len(all_lines)}")
    print(f"  Lines with XREF1='HQ'       : {sum(1 for r in all_lines if g(r,'XREF1') == 'HQ')}")
    print(f"  Lines with XREF2='HQ'       : {sum(1 for r in all_lines if g(r,'XREF2') == 'HQ')}")
    print("=" * 80)

    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults written to: {OUT}")


if __name__ == "__main__":
    main()
