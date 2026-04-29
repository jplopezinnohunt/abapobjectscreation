"""phase1_complete_extraction.py — extract everything still missing.

After agents identified gaps, extract:
1. /CITIPMW/V3_GET_BANKCODE + 12 /CITIPMW/V3_* exit FMs from DMEE_TREE_NODE EXIT_FUNC column
2. Verify TFPM042FB CITI tree Event 05 registration explicit
3. Sample DMEE_TREE_COND for country-gates / AdrLine gates affecting structured siblings
4. Try XSLT CGI_XML_CT_XSLT extraction via STRANS / O2 alternatives
5. Find any other UNESCO Z-FMs registered in OBPM4 that might affect address
"""
from __future__ import annotations
import csv, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

REPO = HERE.parent.parent
OUT_CODE = REPO / "extracted_code" / "FI" / "DMEE_full_inventory"
OUT_DATA = REPO / "knowledge" / "domains" / "Payment" / "phase0" / "dmee_full"
OUT_CODE.mkdir(parents=True, exist_ok=True)
OUT_DATA.mkdir(parents=True, exist_ok=True)


def read_fm_via_new(conn, fm_name):
    """Use RPY_FUNCTIONMODULE_READ_NEW with NEW_SOURCE field."""
    try:
        r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=fm_name)
        ns = r.get("NEW_SOURCE", [])
        if isinstance(ns, list):
            return "\n".join(l.get("LINE", "") if isinstance(l, dict) else str(l) for l in ns)
        return str(ns) if ns else None
    except Exception as e:
        return None


def step1_citipmw_exit_fms(conn):
    """Extract all /CITIPMW/V3_* exit FMs identified in DMEE_TREE_NODE."""
    print("\n[1] Extract /CITIPMW/V3_* exit FMs (from DMEE_TREE_NODE MP_EXIT_FUNC)")
    fms = [
        "/CITIPMW/V3_GET_BANKCODE",
        "/CITIPMW/V3_GET_CDTR_BLDG",
        "/CITIPMW/V3_GET_CDTR_EMAIL",
        "/CITIPMW/V3_CGI_CRED_PO_CITY",
        "/CITIPMW/V3_CGI_CRED_STREET",
        "/CITIPMW/V3_CGI_CRED_REGION",
        "/CITIPMW/V3_EXIT_CGI_CRED_NAME",
        "/CITIPMW/V3_EXIT_CGI_CRED_CITY",
        "/CITIPMW/V3_EXIT_CGI_CRED_NM2",
        "/CITIPMW/V3_DMEE_EXIT_CGI_XML",
        "/CITIPMW/V3_POSTALCODE",
        "/CITIPMW/V3_DMEE_EXIT_INV_DESC",
        "/CITIPMW/V3_CGI_TAX_CATEGORY",
        "/CITIPMW/V3_CGI_TAX_METHOD",
        "/CITIPMW/V3_CGI_REGULATORY_INF",
    ]
    extracted = 0
    for fm in fms:
        src = read_fm_via_new(conn, fm)
        if src and src.strip():
            safe = fm.replace("/", "_").strip("_")
            out = OUT_CODE / f"{safe}.abap"
            out.write_text(src, encoding="utf-8")
            non_empty = sum(1 for l in src.split("\n") if l.strip() and not l.strip().startswith("*"))
            print(f"  ✅ {fm}: {len(src)} chars / {non_empty} non-comment lines")
            extracted += 1
        else:
            print(f"  ❌ {fm}: empty / not found")
    print(f"\n  Total extracted: {extracted}/{len(fms)}")


def step2_verify_tfpm042fb_citi(conn):
    """Verify TFPM042FB has explicit CITI tree Event 05 registration."""
    print("\n[2] Verify TFPM042FB CITI Event 05 registration (read-only)")
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFPM042FB", DELIMITER="|",
                      OPTIONS=[{"TEXT": "FORMI = '/CITI/XML/UNESCO/DC_V3_01'"}],
                      FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
        rows = r.get("DATA", [])
        if rows:
            print(f"  CITI tree has {len(rows)} event registration(s):")
            for d in rows:
                vals = [v.strip() for v in d.get("WA","").split("|")]
                print(f"    {dict(zip(['FORMI','EVENT','FNAME'], vals))}")
        else:
            print("  ❌ NO events registered for /CITI/XML/UNESCO/DC_V3_01 — but FM /CITIPMW/V3_PAYMEDIUM_DMEE_05 exists")
            print("     → Either: (a) registered under different OBPM4 mechanism, (b) different table, or (c) hardcoded in FM dispatcher")
    except Exception as e:
        print(f"  err: {e}")

    # Also check ALL Citi-related events
    print("\n  All TFPM042FB rows where FORMI contains CITI:")
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFPM042FB", DELIMITER="|",
                      OPTIONS=[{"TEXT": "FORMI LIKE '%CITI%'"}],
                      FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
        for d in r.get("DATA", []):
            vals = [v.strip() for v in d.get("WA","").split("|")]
            print(f"    {dict(zip(['FORMI','EVENT','FNAME'], vals))}")
    except Exception as e:
        print(f"  err: {e}")


def step3_cond_hidden_gates(conn):
    """Sample DMEE_TREE_COND for country-gates and AdrLine suppression conditions."""
    print("\n[3] DMEE_TREE_COND country-gate sample for our 4 trees")
    csv_path = OUT_DATA / "dmee_tree_cond_p01.csv"
    if not csv_path.exists():
        print(f"  CSV not found: {csv_path}")
        return
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  Total conditions: {len(rows)}")

    # Bucket by tree, tag-related conditions
    from collections import Counter
    target_trees = {"/SEPA_CT_UNES", "/CITI/XML/UNESCO/DC_V3_01", "/CGI_XML_CT_UNESCO", "/CGI_XML_CT_UNESCO_1"}
    target_rows = [r for r in rows if (r.get("_tree_id") or r.get("TREE_ID") or "") in target_trees]
    print(f"  Target tree conditions: {len(target_rows)}")

    # Find conditions that reference LAND1, BANKL, UBNKS (country/bank-based gates)
    country_gates = []
    address_gates = []
    for r in target_rows:
        arg1_fld = (r.get("ARG1_FLD") or "").strip().upper()
        arg2_fld = (r.get("ARG2_FLD") or "").strip().upper()
        arg1_const = (r.get("ARG1_CONST") or "").strip()
        arg2_const = (r.get("ARG2_CONST") or "").strip()
        if arg1_fld in ("LAND1","UBNKS","UBISO","ZBNKS","BNKS1","ZLAND") or arg2_fld in ("LAND1","UBNKS","UBISO","ZBNKS","BNKS1","ZLAND"):
            country_gates.append(r)
        ref = (r.get("ARG1_REF_NAME") or "") + (r.get("ARG2_REF_NAME") or "")
        if any(kw in ref.upper() for kw in ["ADR", "PSTL", "STRT", "TWN", "PSTC"]):
            address_gates.append(r)

    print(f"\n  Country-gate conditions in target trees: {len(country_gates)}")
    for r in country_gates[:15]:
        tid = r.get("_tree_id") or r.get("TREE_ID")
        print(f"    {tid[:30]:<30} cond_num={r.get('COND_NUMBER','')} {r.get('ARG1_FLD','')} {r.get('OPERATOR','')} {r.get('ARG2_CONST','')[:30]}")

    print(f"\n  Address-related condition references in target trees: {len(address_gates)}")
    addr_ref_counter = Counter(((r.get("ARG1_REF_NAME") or "") + " | " + (r.get("ARG2_REF_NAME") or "")).strip() for r in address_gates)
    for ref, cnt in addr_ref_counter.most_common(15):
        print(f"    {cnt:>3}x  {ref[:80]}")


def step4_xslt_via_strans(conn):
    """Try XSLT CGI_XML_CT_XSLT extraction via STRANS API alternatives."""
    print("\n[4] XSLT CGI_XML_CT_XSLT extraction attempts")
    # Strategy 1: try via O2_API alternate FMs
    for api_fm in ["O2_GET_OBJECT_FROM_DB", "STRANS_API_GET_XSLT", "API_TXTPL_READ", "XSLT_READ", "PROG_READ_XML"]:
        try:
            r = conn.call(api_fm, NAME="CGI_XML_CT_XSLT")
            keys = list(r.keys()) if isinstance(r, dict) else []
            print(f"  {api_fm}: returned keys = {keys[:8]}")
            for key in keys:
                val = r.get(key)
                if isinstance(val, list) and val:
                    text = "\n".join(l.get("LINE","") if isinstance(l, dict) else str(l) for l in val)
                    if text.strip() and "<" in text:
                        out = OUT_CODE / f"CGI_XML_CT_XSLT.xsl"
                        out.write_text(text, encoding="utf-8")
                        print(f"    → saved {len(text)} chars to {out.name}")
                        break
        except Exception as e:
            pass

    # Strategy 2: try reading the underlying TADIR + transport object
    print("\n  TADIR XSLT entry:")
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TADIR", DELIMITER="|",
                      OPTIONS=[{"TEXT": "PGMID = 'R3TR' AND OBJECT = 'XSLT' AND OBJ_NAME = 'CGI_XML_CT_XSLT'"}],
                      FIELDS=[{"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AUTHOR"}, {"FIELDNAME": "SRCSYSTEM"}])
        for d in r.get("DATA", []):
            vals = [v.strip() for v in d.get("WA","").split("|")]
            print(f"    {dict(zip(['OBJ_NAME','DEVCLASS','AUTHOR','SRCSYSTEM'], vals))}")
    except Exception as e:
        print(f"    err: {e}")

    # Strategy 3: O2STRP includes
    print("\n  Try direct READ on possible XSLT include names:")
    for nm in ["CGI_XML_CT_XSLT", "CGI_XML_CT_XSLT_M", "_CGI_XML_CT_XSLT_"]:
        try:
            r = conn.call("RPY_PROGRAM_READ", PROGRAM_NAME=nm, WITH_LOWERCASE="X")
            lines = r.get("SOURCE_EXTENDED", []) or r.get("SOURCE", [])
            text = "\n".join(l.get("LINE","") if isinstance(l, dict) else l for l in lines)
            if text.strip():
                print(f"    ✅ {nm}: {len(text)} chars")
                out = OUT_CODE / f"{nm}.xsl"
                out.write_text(text, encoding="utf-8")
        except Exception as e:
            pass


def step5_find_other_z_fms_in_obpm4(conn):
    """Find any UNESCO Y/Z FMs registered in OBPM4 we haven't extracted."""
    print("\n[5] Find any other Y/Z FMs registered in OBPM4 (TFPM042FB FNAME)")
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFPM042FB", DELIMITER="|", ROWCOUNT=999,
                      OPTIONS=[{"TEXT": "FNAME LIKE 'Y%' OR FNAME LIKE 'Z%'"}],
                      FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
        rows = r.get("DATA", [])
        print(f"  Y/Z custom FMs registered: {len(rows)}")
        for d in rows[:20]:
            vals = [v.strip() for v in d.get("WA","").split("|")]
            print(f"    {dict(zip(['FORMI','EVENT','FNAME'], vals))}")
    except Exception as e:
        print(f"  err: {e}")

    # Also search for /CITIPMW/* FMs registered
    print("\n  /CITIPMW/* FMs registered:")
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TFPM042FB", DELIMITER="|", ROWCOUNT=999,
                      OPTIONS=[{"TEXT": "FNAME LIKE '/CITIPMW/%'"}],
                      FIELDS=[{"FIELDNAME": "FORMI"}, {"FIELDNAME": "EVENT"}, {"FIELDNAME": "FNAME"}])
        rows = r.get("DATA", [])
        for d in rows[:10]:
            vals = [v.strip() for v in d.get("WA","").split("|")]
            print(f"    {dict(zip(['FORMI','EVENT','FNAME'], vals))}")
    except Exception as e:
        print(f"  err: {e}")


def main():
    conn = get_connection("P01")
    try:
        step1_citipmw_exit_fms(conn)
        step2_verify_tfpm042fb_citi(conn)
        step3_cond_hidden_gates(conn)
        step4_xslt_via_strans(conn)
        step5_find_other_z_fms_in_obpm4(conn)
    finally:
        conn.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
