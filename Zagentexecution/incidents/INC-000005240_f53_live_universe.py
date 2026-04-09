"""
INC-000005240 — LIVE F-53 universe fetch
=========================================
Gold DB's bkpf extraction has zero rows with TCODE='F-53' for any user — but
the user reports they see F-53 in live BKPF. So Gold DB has an extraction gap.

This script bypasses Gold DB entirely and reads BKPF via RFC for AL_JONATHAN,
filtering strictly by TCODE='F-53'. Then it pulls BSAK/BSAS/BSIS for those
docs and checks cdhdr for any post-posting modifications.

Two-phase method (per user instruction):
  Phase 1: Universe = BKPF WHERE USNAM='AL_JONATHAN' AND TCODE='F-53'
  Phase 2: For each doc — line items + change history
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    # ---- Phase 1: strict F-53 universe ------------------------------------
    print("Phase 1 — BKPF where TCODE='F-53' AND USNAM='AL_JONATHAN' AND BUKRS='UNES'")
    bkpf_rows = rfc_read_paginated(
        guard, table="BKPF",
        fields=["BUKRS", "BELNR", "GJAHR", "BUDAT", "BLDAT", "BLART",
                "TCODE", "USNAM", "XBLNR", "BKTXT", "WAERS", "CPUDT", "CPUTM"],
        where="BUKRS = 'UNES' AND USNAM = 'AL_JONATHAN' AND TCODE = 'F-53'",
        batch_size=500,
    )
    print(f"  Returned {len(bkpf_rows)} documents")
    for r in bkpf_rows:
        print(f"    {r['BUDAT']} {r['BELNR']}/{r['GJAHR']} {r['TCODE']} {r['BLART']} "
              f"XBLNR={r['XBLNR']!r} BKTXT={r['BKTXT']!r}")

    # Cross-check: how many total F-53 docs exist in UNES at all?
    print("\nCross-check — total F-53 docs in BKPF (all users, UNES):")
    try:
        total = rfc_read_paginated(
            guard, table="BKPF",
            fields=["BUKRS", "BELNR", "GJAHR", "USNAM"],
            where="BUKRS = 'UNES' AND TCODE = 'F-53' AND BUDAT >= '20260101'",
            batch_size=5000,
        )
        print(f"  Total F-53 docs in UNES since 20260101: {len(total)}")
        from collections import Counter
        top_users = Counter(r["USNAM"] for r in total).most_common(15)
        print(f"  Top 15 F-53 posters (USNAM):")
        for u, c in top_users:
            print(f"    {u:20s} {c:>6}")
    except Exception as e:
        print(f"  Cross-check failed: {e}")

    doc_keys = [(r["BUKRS"], r["BELNR"], r["GJAHR"]) for r in bkpf_rows]

    if not doc_keys:
        print("\n*** WARNING: Phase 1 returned ZERO docs. Either:")
        print("    1. AL_JONATHAN posted no F-53 docs to UNES")
        print("    2. BKPF.TCODE stores them under a different value")
        print("    Scroll up to the cross-check to see if F-53 exists at all in UNES")
        json.dump({"bkpf_rows": bkpf_rows}, OUT.open("w", encoding="utf-8"),
                  indent=2, default=str, ensure_ascii=False)
        return

    # ---- Phase 2a: line items for those docs ------------------------------
    print(f"\nPhase 2a — line items for {len(doc_keys)} F-53 docs (BSAK/BSAS/BSIS)")

    def read_lines(table, fields, b, n, g):
        try:
            return rfc_read_paginated(
                guard, table=table, fields=fields,
                where=f"BUKRS = '{b}' AND BELNR = '{n}' AND GJAHR = '{g}'",
                batch_size=500,
            )
        except Exception as e:
            print(f"    {table} {b}/{n}/{g}: {e}")
            return []

    all_lines = []
    line_fields = ["BUKRS", "GJAHR", "BELNR", "BUZEI",
                   "XREF1", "XREF2", "XREF3",
                   "ZUONR", "HKONT", "BLART", "BUDAT"]
    vendor_fields = line_fields + ["LIFNR"]
    for (b, n, g) in doc_keys:
        for tab, fld in (("BSAK", vendor_fields), ("BSAS", line_fields), ("BSIS", line_fields)):
            rows = read_lines(tab, fld, b, n, g)
            for r in rows: r["_src"] = tab
            all_lines.extend(rows)

    print(f"  Total line items: {len(all_lines)}")
    print("\n  All F-53 line items:")
    for r in sorted(all_lines, key=lambda x: (x.get("BUDAT",""), x.get("BELNR",""), x.get("BUZEI",""))):
        p = r.get("LIFNR","-") or "-"
        print(f"    {r.get('BUDAT',''):8s} {r.get('BELNR',''):10s}/{r.get('GJAHR','')} "
              f"L{r.get('BUZEI','?'):>3s} {r['_src']:4s} "
              f"HKONT={r.get('HKONT','-'):10s} "
              f"LIFNR={p:<10} "
              f"XREF1={str(r.get('XREF1','')).strip()!r:10s} "
              f"XREF2={str(r.get('XREF2','')).strip()!r:10s} "
              f"ZUONR={str(r.get('ZUONR','')).strip()!r}")

    # ---- Phase 2b: CDHDR change history -----------------------------------
    print(f"\nPhase 2b — CDHDR change history for {len(doc_keys)} F-53 docs")
    all_cdhdr = []
    for (b, n, g) in doc_keys:
        objectid = f"{b}{n}{g}"
        try:
            rows = rfc_read_paginated(
                guard, table="CDHDR",
                fields=["OBJECTCLAS", "OBJECTID", "CHANGENR", "USERNAME", "UDATE", "UTIME", "TCODE"],
                where=f"OBJECTCLAS = 'BELEG' AND OBJECTID = '{objectid}'",
                batch_size=500,
            )
            all_cdhdr.extend(rows)
            status = f"{len(rows)} changes" if rows else "UNCHANGED"
            print(f"    {b}/{n}/{g}: {status}")
            for h in rows:
                print(f"      CHANGENR={h['CHANGENR']} BY={h['USERNAME']} DATE={h['UDATE']} "
                      f"TCODE={h['TCODE']}")
        except Exception as e:
            print(f"    {b}/{n}/{g}: CDHDR read failed: {e}")

    # ---- Phase 2c: if any changes, get CDPOS detail for XREF fields ------
    if all_cdhdr:
        print(f"\nPhase 2c — CDPOS detail for {len(all_cdhdr)} change records (XREF/XBLNR/ZUONR only)")
        for h in all_cdhdr:
            try:
                cdpos = rfc_read_paginated(
                    guard, table="CDPOS",
                    fields=["OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME", "TABKEY",
                            "FNAME", "CHNGIND", "VALUE_OLD", "VALUE_NEW"],
                    where=(f"OBJECTCLAS='BELEG' AND OBJECTID='{h['OBJECTID']}' "
                           f"AND CHANGENR='{h['CHANGENR']}'"),
                    batch_size=500,
                )
                relevant = [p for p in cdpos if p.get("FNAME","").strip() in
                            ("XREF1","XREF2","XREF3","XBLNR","ZUONR")]
                if relevant:
                    print(f"  {h['OBJECTID']} CHANGENR={h['CHANGENR']}:")
                    for p in relevant:
                        print(f"    {p['FNAME'].strip()}: {p['VALUE_OLD']!r} -> {p['VALUE_NEW']!r}")
            except Exception as e:
                print(f"    CDPOS {h['CHANGENR']}: {e}")

    # ---- Save -------------------------------------------------------------
    out = {"bkpf_rows": bkpf_rows, "all_lines": all_lines, "cdhdr_rows": all_cdhdr}
    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    # ---- Summary ----------------------------------------------------------
    print("\n" + "=" * 80)
    print("VERDICT — AL_JONATHAN's F-53 universe (live, strict filter TCODE='F-53')")
    print("=" * 80)
    print(f"  F-53 documents      : {len(bkpf_rows)}")
    print(f"  Total line items    : {len(all_lines)}")
    bsak_lines = [r for r in all_lines if r.get("_src") == "BSAK"]
    xref_hq    = [r for r in bsak_lines if str(r.get("XREF1","")).strip() == "HQ"]
    print(f"  BSAK (vendor) lines : {len(bsak_lines)}")
    print(f"  BSAK with XREF1='HQ': {len(xref_hq)} / {len(bsak_lines)}")
    print(f"  Change records      : {len(all_cdhdr)}")
    print(f"  Changes touching XREF/XBLNR/ZUONR: see Phase 2c above")
    print(f"\n  Results: {OUT}")


if __name__ == "__main__":
    main()
