"""
INC-000005240 — FB02 change-document verification
====================================================
Answers two questions raised by the user during review:

  1. Were AL_JONATHAN's 10 BSAK XREF values ('HQ'/'HQ') ever changed via FB02
     after original posting? If no → values are as-posted → substitution is the
     proven source. If yes → re-open investigation.

  2. For L_HANGI sample docs (top-20 XBLNR = 'FU/*'), are the BSEG line items
     actually attributed to those field offices via KOSTL / FIKRS / GSBER /
     PRCTR — or is the XBLNR just free text while her BSEG fields all point to
     HQ? And: were any of her XREF1/XREF2/XBLNR values ever changed via FB02?

Uses CDHDR / CDPOS (change documents, object class BELEG).
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


def read_cdhdr_for_doc(guard, bukrs, belnr, gjahr):
    """CDHDR rows for one FI document (object class BELEG)."""
    objectid = f"{bukrs}{belnr}{gjahr}"
    rows = rfc_read_paginated(
        guard, table="CDHDR",
        fields=["OBJECTCLAS", "OBJECTID", "CHANGENR", "USERNAME", "UDATE", "UTIME", "TCODE"],
        where=f"OBJECTCLAS = 'BELEG' AND OBJECTID = '{objectid}'",
        batch_size=500,
    )
    return rows


def read_cdpos_for_change(guard, objectclas, objectid, changenr):
    """CDPOS rows for one change number, filtered to XREF/XBLNR fields."""
    # CDPOS is keyed by OBJECTCLAS+OBJECTID+CHANGENR
    rows = rfc_read_paginated(
        guard, table="CDPOS",
        fields=["OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME", "TABKEY", "FNAME", "CHNGIND", "VALUE_OLD", "VALUE_NEW"],
        where=f"OBJECTCLAS = '{objectclas}' AND OBJECTID = '{objectid}' AND CHANGENR = '{changenr}'",
        batch_size=500,
    )
    # Only care about XREF / XBLNR / ZUONR
    return [r for r in rows if r.get("FNAME", "").strip() in ("XREF1", "XREF2", "XREF3", "XBLNR", "ZUONR")]


def read_bseg_context(guard, bukrs, belnr, gjahr):
    """Read the document's BSEG lines to see cost center / fund center / biz
    area — does the document's attribution match the XBLNR, or is XBLNR
    decorative free text?
    """
    rows = rfc_read_paginated(
        guard, table="BSEG",
        fields=["BUKRS", "BELNR", "GJAHR", "BUZEI", "KOART", "HKONT", "LIFNR", "KOSTL", "FKBER", "GSBER", "FISTL", "GEBER", "PRCTR", "PS_PSP_PNR", "XREF1", "XREF2", "XREF3", "ZUONR", "SGTXT"],
        where=f"BUKRS = '{bukrs}' AND BELNR = '{belnr}' AND GJAHR = '{gjahr}'",
        batch_size=500,
    )
    return rows


def get_l_hangi_sample_docs(limit=15):
    """From Gold DB, pick a sample of L_HANGI docs whose XBLNR starts with FU/."""
    c = sqlite3.connect(str(GOLD_DB)).cursor()
    c.execute(
        """
        SELECT BUKRS, BELNR, GJAHR, BUDAT, TCODE, XBLNR, BLART
        FROM bkpf
        WHERE USNAM = 'L_HANGI'
          AND BUKRS = 'UNES'
          AND XBLNR LIKE 'FU/%'
          AND BUDAT BETWEEN '20251201' AND '20260331'
        ORDER BY BUDAT DESC
        LIMIT ?
        """,
        (limit,),
    )
    cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in c.fetchall()]


def get_al_jonathan_fbz2_docs():
    """The 10 FBZ2 docs (outgoing payments) that have BSAK vendor lines."""
    c = sqlite3.connect(str(GOLD_DB)).cursor()
    c.execute(
        """
        SELECT BUKRS, BELNR, GJAHR, BUDAT, TCODE, XBLNR, BLART
        FROM bkpf
        WHERE USNAM = 'AL_JONATHAN'
          AND BUKRS = 'UNES'
          AND TCODE = 'FBZ2'
          AND BUDAT BETWEEN '20251201' AND '20260331'
        ORDER BY BUDAT, BELNR
        """
    )
    cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in c.fetchall()]


def check_user_docs(guard, label, docs):
    print(f"\n{'=' * 90}")
    print(f"{label}")
    print(f"{'=' * 90}")
    findings = {"docs": [], "has_xref_changes": False, "has_xblnr_changes": False}
    for d in docs:
        bukrs, belnr, gjahr = d["BUKRS"], d["BELNR"], d["GJAHR"]
        objectid = f"{bukrs}{belnr}{gjahr}"
        print(f"\n{d['BUDAT']} {belnr}/{gjahr} {d['TCODE']} XBLNR={d.get('XBLNR','')!r}")

        # Change history
        cdhdr = read_cdhdr_for_doc(guard, bukrs, belnr, gjahr)
        doc_finding = {**d, "cdhdr_count": len(cdhdr), "xref_changes": [], "xblnr_changes": [], "bseg_attribution": []}
        if not cdhdr:
            print("  CDHDR: no changes (document is as-posted)")
        else:
            for h in cdhdr:
                print(f"  CDHDR: CHANGENR={h['CHANGENR']} USER={h['USERNAME']} DATE={h['UDATE']} TCODE={h['TCODE']}")
                cdpos = read_cdpos_for_change(guard, "BELEG", objectid, h["CHANGENR"])
                for p in cdpos:
                    fname = p.get("FNAME", "").strip()
                    print(f"    {fname}: {p.get('VALUE_OLD','')!r} -> {p.get('VALUE_NEW','')!r} (chng={p.get('CHNGIND','')})")
                    if fname in ("XREF1", "XREF2", "XREF3"):
                        findings["has_xref_changes"] = True
                        doc_finding["xref_changes"].append(p)
                    elif fname == "XBLNR":
                        findings["has_xblnr_changes"] = True
                        doc_finding["xblnr_changes"].append(p)

        # BSEG attribution for L_HANGI sample (to see if her BSEG points to field office)
        if label.startswith("L_HANGI"):
            bseg = read_bseg_context(guard, bukrs, belnr, gjahr)
            doc_finding["bseg_attribution"] = bseg
            print(f"  BSEG lines: {len(bseg)}")
            for b in bseg[:6]:  # print first few
                print(
                    f"    L{b.get('BUZEI','?'):>3s} KOART={b.get('KOART','-')} "
                    f"HKONT={b.get('HKONT','-'):10s} "
                    f"KOSTL={b.get('KOSTL','-'):10s} "
                    f"FIKR={b.get('FISTL','-'):10s} "
                    f"GSBER={b.get('GSBER','-'):5s} "
                    f"FKBER={b.get('FKBER','-'):8s} "
                    f"GEBER={b.get('GEBER','-'):8s} "
                    f"XREF1={b.get('XREF1','-'):10s} "
                    f"XREF2={b.get('XREF2','-'):10s}"
                )

        findings["docs"].append(doc_finding)
    return findings


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    # 1) AL_JONATHAN's 10 FBZ2 docs — prove or disprove FB02 tampering
    al_docs = get_al_jonathan_fbz2_docs()
    print(f"AL_JONATHAN FBZ2 docs to check: {len(al_docs)}")
    al_findings = check_user_docs(guard, "AL_JONATHAN — FB02 change-history audit", al_docs)

    # 2) L_HANGI sample — test the central-processor hypothesis
    lh_docs = get_l_hangi_sample_docs(limit=12)
    print(f"\nL_HANGI sample docs (XBLNR starts with 'FU/'): {len(lh_docs)}")
    lh_findings = check_user_docs(guard, "L_HANGI — XBLNR FB02 audit + BSEG attribution", lh_docs)

    # Save
    out = {"al_jonathan": al_findings, "l_hangi": lh_findings}
    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    # Summary
    print("\n" + "=" * 90)
    print("FINAL VERDICT")
    print("=" * 90)
    print(f"AL_JONATHAN:")
    print(f"  XREF1/2/3 changed via FB02 after posting? {al_findings['has_xref_changes']}")
    print(f"  XBLNR changed?                              {al_findings['has_xblnr_changes']}")
    if not al_findings["has_xref_changes"]:
        print(f"  → Values ARE as-posted. Substitution is the proven source.")
    else:
        print(f"  → WARNING: post-hoc changes found. Root cause needs re-investigation.")
    print(f"\nL_HANGI:")
    print(f"  XREF1/2/3 changed via FB02 after posting? {lh_findings['has_xref_changes']}")
    print(f"  XBLNR changed?                              {lh_findings['has_xblnr_changes']}")
    print(f"  See BSEG attribution above — do her BSEG fields match XBLNR's 'FU/*' or point to HQ?")
    print(f"\nFull data: {OUT}")


if __name__ == "__main__":
    main()
