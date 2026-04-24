"""phase0_data_mutation_trace.py — Trace every data-mutation code point.

Closes:
  1. DMEE_TREE_NODE complete (ALL 48 cols including MP_OFFSET, CV_RULE, MP_SC_OFFSET)
  2. OBPM4 Events 00-08: inspect which FMs are registered per format+event (table T042FV + T042FB)
  3. XSLT CGI_XML_CT_XSLT source (table O2XSLT / via RFC)
  4. YCL_IDFI_CGI_DMEE_DE + _IT source extraction
  5. PSTLADRMOR1/2/3 param search: where are these SET? Grep in extracted code + inspect related FMs

Target: P01 SNC/SSO
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection

REPO = HERE.parent.parent
OUT_DIR = REPO / "knowledge" / "domains" / "Payment" / "phase0" / "dmee_full"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CLASS_DIR = REPO / "extracted_code" / "FI" / "DMEE_full_inventory"
CLASS_DIR.mkdir(parents=True, exist_ok=True)

TREES = ["/SEPA_CT_UNES", "/CITI/XML/UNESCO/DC_V3_01", "/CGI_XML_CT_UNESCO", "/CGI_XML_CT_UNESCO_1"]


def step1_dmee_node_all48(conn):
    """Re-extract DMEE_TREE_NODE with ALL 48 columns."""
    print("\n[Step 1] DMEE_TREE_NODE — all 48 columns")
    r = conn.call("DDIF_FIELDINFO_GET", TABNAME="DMEE_TREE_NODE", ALL_TYPES="X")
    all_cols = [f.get("FIELDNAME") for f in r.get("DFIES_TAB", [])]
    print(f"  {len(all_cols)} total columns")

    # Chunk size 8 to fit 512B buffer
    chunk_size = 8
    chunks = [all_cols[i:i+chunk_size] for i in range(0, len(all_cols), chunk_size)]

    all_rows = []
    for tree_id in TREES:
        where = f"TREE_TYPE = 'PAYM' AND TREE_ID = '{tree_id}'"
        # For each chunk, fetch rows in SAME ORDER, merge by index
        chunk_rows_list = []
        for chunk in chunks:
            row_skip = 0
            batch = 2000
            chunk_rows = []
            while True:
                rr = conn.call("RFC_READ_TABLE",
                               QUERY_TABLE="DMEE_TREE_NODE",
                               DELIMITER="|",
                               ROWCOUNT=batch,
                               ROWSKIPS=row_skip,
                               OPTIONS=[{"TEXT": where}],
                               FIELDS=[{"FIELDNAME": c} for c in chunk])
                data = rr.get("DATA", [])
                if not data: break
                for d in data:
                    vals = d.get("WA", "").split("|")
                    chunk_rows.append(dict(zip([h.get("FIELDNAME") for h in rr.get("FIELDS", [])], vals)))
                if len(data) < batch: break
                row_skip += batch
            chunk_rows_list.append(chunk_rows)
        max_len = max((len(c) for c in chunk_rows_list), default=0)
        for i in range(max_len):
            m = {"_tree_id": tree_id}
            for ch_rows in chunk_rows_list:
                if i < len(ch_rows):
                    m.update(ch_rows[i])
            all_rows.append(m)

    out_csv = OUT_DIR / "dmee_tree_node_p01_all48.csv"
    if all_rows:
        cols = sorted({k for r in all_rows for k in r.keys()})
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(all_rows)
    print(f"  {len(all_rows)} rows -> {out_csv.name}")

    # Report: nodes with non-zero MP_OFFSET, CV_RULE
    with_offset = [r for r in all_rows if (r.get("MP_OFFSET") or "").strip() and (r.get("MP_OFFSET") or "").strip() not in ("0", "000000")]
    with_cv = [r for r in all_rows if (r.get("CV_RULE") or "").strip()]
    with_sc_offset = [r for r in all_rows if (r.get("MP_SC_OFFSET") or "").strip() and (r.get("MP_SC_OFFSET") or "").strip() not in ("0", "000000")]
    print(f"  Nodes with MP_OFFSET non-zero:    {len(with_offset)}")
    print(f"  Nodes with MP_SC_OFFSET non-zero: {len(with_sc_offset)}")
    print(f"  Nodes with CV_RULE populated:     {len(with_cv)}")
    if with_cv:
        print("  Sample CV_RULE values:")
        for r in with_cv[:10]:
            print(f"    {r.get('_tree_id')} {r.get('NODE_ID')} {r.get('TECH_NAME','')[:25]} CV_RULE={r.get('CV_RULE')}")
    if with_offset:
        print("  Sample MP_OFFSET (top 10):")
        for r in with_offset[:10]:
            print(f"    {r.get('_tree_id')} {r.get('NODE_ID')} TECH={r.get('TECH_NAME','')[:25]} MP_OFFSET={r.get('MP_OFFSET')} MP_SC_OFFSET={r.get('MP_SC_OFFSET','')}")


def step2_obpm4_events(conn):
    """Inspect OBPM4 Events — tables T042FV / T042FB / T042FE holding event FM registration."""
    print("\n[Step 2] OBPM4 Events — inspect registered FMs per format+event")
    # T042FV likely has format-level values; T042FE or TFPM042FB has the event-FM registrations
    # Try several table names
    for tbl in ["T042FV", "TFPM042FB", "T042FE", "TFPM042FE", "TFPM042FEV"]:
        try:
            r = conn.call("DDIF_FIELDINFO_GET", TABNAME=tbl, ALL_TYPES="X")
            fields = [f.get("FIELDNAME") for f in r.get("DFIES_TAB", [])]
            print(f"  {tbl}: {len(fields)} fields — {fields[:12]}")
            if fields and "FMNAME" in fields or "FORMI" in fields:
                # Pull rows for our trees
                rr = conn.call("RFC_READ_TABLE",
                               QUERY_TABLE=tbl,
                               DELIMITER="|",
                               ROWCOUNT=200,
                               FIELDS=[{"FIELDNAME": c} for c in fields[:10]])
                data = rr.get("DATA", [])
                print(f"    (sample {min(len(data),5)} of {len(data)} rows)")
                for d in data[:5]:
                    vals = d.get("WA", "").split("|")
                    rec = dict(zip([h.get("FIELDNAME") for h in rr.get("FIELDS", [])], vals))
                    print(f"      {rec}")
        except Exception as e:
            print(f"  {tbl}: {e}")


def step3_xslt_extract(conn):
    """Extract the XSLT CGI_XML_CT_XSLT source."""
    print("\n[Step 3] Extract XSLT CGI_XML_CT_XSLT")
    # XSLTs are stored in O2XSLT_INFO / O2XSLT_SRC or as function group/class
    # Try calling RFC_READ_TABLE against XSLT header tables first
    for tbl in ["O2XSLT_INFO", "O2XSLT", "O2XSLTD", "O2XSLT_HEADER"]:
        try:
            r = conn.call("DDIF_FIELDINFO_GET", TABNAME=tbl, ALL_TYPES="X")
            fields = [f.get("FIELDNAME") for f in r.get("DFIES_TAB", [])]
            print(f"  {tbl}: {len(fields)} fields")
            if fields:
                rr = conn.call("RFC_READ_TABLE",
                               QUERY_TABLE=tbl,
                               DELIMITER="|",
                               ROWCOUNT=5,
                               OPTIONS=[{"TEXT": "XSLTDESC LIKE 'CGI_XML%' OR XSLT_NAME LIKE 'CGI_XML%' OR NAME LIKE 'CGI_XML%'"}],
                               FIELDS=[{"FIELDNAME": c} for c in fields[:10]])
                for d in rr.get("DATA", []):
                    vals = d.get("WA", "").split("|")
                    rec = dict(zip([h.get("FIELDNAME") for h in rr.get("FIELDS", [])], vals))
                    print(f"    hit: {rec}")
        except Exception as e:
            pass

    # Try RPY approach — check TADIR for XSLT OBJECT = 'XSLT'
    try:
        r = conn.call("RFC_READ_TABLE",
                      QUERY_TABLE="TADIR",
                      DELIMITER="|",
                      ROWCOUNT=10,
                      OPTIONS=[{"TEXT": "PGMID = 'R3TR' AND OBJECT = 'XSLT' AND OBJ_NAME LIKE 'CGI_XML%'"}],
                      FIELDS=[{"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AUTHOR"}])
        for d in r.get("DATA", []):
            vals = d.get("WA", "").split("|")
            print(f"  TADIR XSLT hit: {dict(zip(['OBJ_NAME','DEVCLASS','AUTHOR'], vals))}")
    except Exception as e:
        print(f"  TADIR XSLT probe: {e}")


def step4_de_it_class_extract(conn):
    """Extract source of YCL_IDFI_CGI_DMEE_DE and _IT classes from P01."""
    print("\n[Step 4] Extract YCL_IDFI_CGI_DMEE_DE and _IT source")
    for cls in ["YCL_IDFI_CGI_DMEE_DE", "YCL_IDFI_CGI_DMEE_IT"]:
        try:
            # RPY_CLASS_READ expects CLASS / RSSOURCE
            r = conn.call("SEO_CLASS_GET_NAME_BY_OBJECT",  # try this first
                          OBJECT_NAME=cls, OBJECT_TYPE="CLAS")
            print(f"  {cls}: name lookup: {r}")
        except Exception as e:
            pass
        try:
            r = conn.call("RPY_CLASS_READ", CLASSKEY=cls)
            src = ""
            for m in r.get("METHODS_SOURCE", []):
                mname = m.get("CLSNAME", "")
                msrc = m.get("SOURCE", [])
                # SOURCE is a table of strings
                if isinstance(msrc, list):
                    src += f"\n*--- METHOD (cm) ---\n" + "\n".join(s.get("LINE", "") if isinstance(s, dict) else s for s in msrc)
            # Alternative: CLAS_SOURCE
            if "IMPLEMENTATIONS" in r:
                print(f"  {cls}: keys={list(r.keys())[:10]}")
            out = CLASS_DIR / f"{cls}.abap"
            out.write_text(json.dumps(r, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            print(f"  {cls}: saved raw response to {out.name}")
        except Exception as e:
            print(f"  {cls}: RPY_CLASS_READ err: {e}")


def step5_pstladrmor_search(conn):
    """Grep extracted code + runtime for PSTLADRMOR1/2/3 parameter writers."""
    print("\n[Step 5] PSTLADRMOR1/2/3 source: grep extracted_code + check for setter FMs")
    import re, os, glob
    patterns = ["PSTLADRMOR1", "PSTLADRMOR2", "PSTLADRMOR3", "PSTLADR", "CDAGPSTLADR", "DBTRPSTLADR"]
    hits = []
    for fp in glob.glob(str(REPO) + "/extracted_code/**/*.abap", recursive=True):
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    for p in patterns:
                        if p in line.upper():
                            hits.append((fp, i, p, line.rstrip()[:140]))
                            break
        except: continue
    print(f"  Total PSTLADRMOR hits in extracted code: {len(hits)}")
    for h in hits[:20]:
        rel = h[0].replace(str(REPO), "").replace("\\", "/").lstrip("/")
        print(f"    {rel}:{h[1]}  [{h[2]}]  {h[3]}")

    # Also check if there's a setter function / parameter structure
    # FPM_CGI / FPM_SEPA mentioned in DMEE_TREE_HEAD PARAM_STRUC
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME="FPM_CGI", ALL_TYPES="X")
        fields = r.get("DFIES_TAB", [])
        print(f"\n  FPM_CGI structure: {len(fields)} fields")
        for f in fields[:40]:
            fn = f.get("FIELDNAME", "")
            if "PSTL" in fn or "ADR" in fn or "MOR" in fn or "CTRY" in fn:
                print(f"    {fn:<25} {f.get('INTTYPE','')} L={f.get('INTLEN','')} {f.get('FIELDTEXT','')[:60]}")
    except Exception as e:
        print(f"  FPM_CGI: {e}")


def main():
    conn = get_connection("P01")
    try:
        step1_dmee_node_all48(conn)
        step2_obpm4_events(conn)
        step3_xslt_extract(conn)
        step4_de_it_class_extract(conn)
        step5_pstladrmor_search(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
