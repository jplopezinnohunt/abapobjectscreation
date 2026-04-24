"""phase0_event05_fm_analysis.py — Deep analysis of SAP standard Event 05 FMs.

Extract source of FI_PAYMEDIUM_DMEE_CGI_05 + /CITIPMW/V3_PAYMEDIUM_DMEE_05.
Grep for PSTLADRMOR1/2/3 setters.
Check FPM_CGI / FPM_SEPA structures.
Find SEPA-equivalent Event 05 FM.

Target: P01 SNC/SSO
Output: extracted_code/FI/DMEE_full_inventory/
"""
from __future__ import annotations
import re, sys, json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

REPO = HERE.parent.parent
OUT_DIR = REPO / "extracted_code" / "FI" / "DMEE_full_inventory"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_fm_source(conn, fm_name: str) -> str:
    """Read FM source via READ_TEXT_TAB → RPY_FUNCTIONMODULE_READ approach."""
    # Try RPY_FUNCTIONMODULE_READ first
    try:
        r = conn.call("RPY_FUNCTIONMODULE_READ", FUNCTIONNAME=fm_name)
        if "SOURCE" in r:
            lines = r.get("SOURCE", [])
            return "\n".join(l.get("LINE", "") if isinstance(l, dict) else l for l in lines)
    except Exception as e:
        pass
    # Fallback: TFDIR to get INCLUDE name, then READ_REPORT
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFDIR",
                      DELIMITER="|",
                      OPTIONS=[{"TEXT": f"FUNCNAME = '{fm_name}'"}],
                      FIELDS=[{"FIELDNAME": "FUNCNAME"}, {"FIELDNAME": "PNAME"},
                              {"FIELDNAME": "INCLUDE"}])
        data = r.get("DATA", [])
        if not data:
            return f"[FM {fm_name} not found in TFDIR]"
        vals = data[0].get("WA", "").split("|")
        rec = dict(zip(["FUNCNAME", "PNAME", "INCLUDE"], [v.strip() for v in vals]))
        pname = rec["PNAME"]
        # Read the FM main include (FB-prefix or custom)
        include_name = pname  # typically SAPLFPAY_EVENTS -> LFPAY_EVENTSU01 for FM
        # But we don't know the include number. Try READ_REPORT on PNAME.
        try:
            rr = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=pname,
                           WITH_LOWERCASE="X", WITH_INCLUDE="X")
            lines = rr.get("SOURCE_EXTENDED", []) or rr.get("SOURCE", [])
            return "\n".join(l.get("LINE", "") if isinstance(l, dict) else l for l in lines)
        except Exception as e:
            return f"[PNAME {pname} read err: {e}]"
    except Exception as e:
        return f"[TFDIR err for {fm_name}: {e}]"


def grep_pstladrmor(source: str, name: str):
    """Grep for PSTLADRMOR1/2/3 assignments or references."""
    patterns = ["PSTLADRMOR1", "PSTLADRMOR2", "PSTLADRMOR3", "PSTLADR", "CDAGPSTLADR",
                "DBTRPSTLADR", "CTRYOFRES"]
    hits = []
    for i, line in enumerate(source.split("\n"), 1):
        up = line.upper()
        for p in patterns:
            if p in up:
                hits.append((i, p, line.rstrip()[:200]))
                break
    print(f"\n  === {name} — PSTLADRMOR hits ({len(hits)}) ===")
    for h in hits[:30]:
        print(f"    :{h[0]:>4} [{h[1]:<14}] {h[2]}")


def main():
    conn = get_connection("P01")
    try:
        print("\n[1] Check FPM_CGI structure fields (9 fields)")
        try:
            r = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPM_CGI", ALL_TYPES="X")
            for f in r.get("DFIES_TAB", []):
                print(f"  {f.get('FIELDNAME',''):<22} {f.get('INTTYPE','')} L={f.get('INTLEN','')} {f.get('FIELDTEXT','')[:80]}")
        except Exception as e:
            print(f"  err: {e}")

        print("\n[2] Check FPM_SEPA structure fields")
        try:
            r = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPM_SEPA", ALL_TYPES="X")
            for f in r.get("DFIES_TAB", []):
                print(f"  {f.get('FIELDNAME',''):<22} {f.get('INTTYPE','')} L={f.get('INTLEN','')} {f.get('FIELDTEXT','')[:80]}")
        except Exception as e:
            print(f"  err: {e}")

        print("\n[3] Find SEPA-equivalent Event 05 FM — inspect TFPM042FB for SEPA trees")
        try:
            r = conn.call("RFC_READ_TABLE",
                          QUERY_TABLE="TFPM042FB",
                          DELIMITER="|",
                          OPTIONS=[{"TEXT": "FORMI LIKE '%SEPA%'"}],
                          FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
            for d in r.get("DATA", [])[:20]:
                vals = d.get("WA", "").split("|")
                print(f"  {dict(zip(['FORMI','EVENT','FNAME'], [v.strip() for v in vals]))}")
        except Exception as e:
            print(f"  err: {e}")

        print("\n[4] Extract FI_PAYMEDIUM_DMEE_CGI_05 source")
        source = read_fm_source(conn, "FI_PAYMEDIUM_DMEE_CGI_05")
        out = OUT_DIR / "FI_PAYMEDIUM_DMEE_CGI_05.abap"
        out.write_text(source, encoding="utf-8", errors="replace")
        print(f"  saved: {out.name} ({len(source):,} chars)")
        grep_pstladrmor(source, "FI_PAYMEDIUM_DMEE_CGI_05")

        print("\n[5] Extract /CITIPMW/V3_PAYMEDIUM_DMEE_05 source")
        source2 = read_fm_source(conn, "/CITIPMW/V3_PAYMEDIUM_DMEE_05")
        out2 = OUT_DIR / "CITIPMW_V3_PAYMEDIUM_DMEE_05.abap"
        out2.write_text(source2, encoding="utf-8", errors="replace")
        print(f"  saved: {out2.name} ({len(source2):,} chars)")
        grep_pstladrmor(source2, "/CITIPMW/V3_PAYMEDIUM_DMEE_05")

        print("\n[6] Also extract FI_PAYMEDIUM_EVENTS function group main include")
        src3 = read_fm_source(conn, "FI_PAYMEDIUM_DMEE_CGI_04")  # sister FM
        if "PSTLADRMOR" in src3 or "PSTLADR" in src3.upper():
            out3 = OUT_DIR / "FI_PAYMEDIUM_DMEE_CGI_04.abap"
            out3.write_text(src3, encoding="utf-8", errors="replace")
            print(f"  saved: {out3.name}")
            grep_pstladrmor(src3, "FI_PAYMEDIUM_DMEE_CGI_04")

        print("\n[7] Also try Events 02 03 06 07 which may complement 05")
        for ev in ["02", "03", "04", "06", "07", "08"]:
            fm = f"FI_PAYMEDIUM_DMEE_CGI_{ev}"
            try:
                r = conn.call("RFC_READ_TABLE",
                              QUERY_TABLE="TFDIR",
                              DELIMITER="|",
                              OPTIONS=[{"TEXT": f"FUNCNAME = '{fm}'"}],
                              FIELDS=[{"FIELDNAME": "FUNCNAME"}])
                data = r.get("DATA", [])
                if data:
                    print(f"  {fm} EXISTS in TFDIR")
            except: pass

    finally:
        conn.close()


if __name__ == "__main__":
    main()
