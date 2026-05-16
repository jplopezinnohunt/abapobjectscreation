"""
Generate the COMPLETE Cdtr+Dbtr mapping comparison table with 3 columns:
  1. Tree mapping (MP_SC_TAB-MP_SC_FLD) — what the tree configuration says
  2. Tree exit (MP_EXIT_FUNC)            — FM that computes the value
  3. CGI BAdI post-process                — what YCL_IDFI_CGI_DMEE_FALLBACK does
+ proposed Y_FI_DMEE_ADR unified source.

Reads dmee_tree_node_d01_sepa_v001_fresh.csv (108 nodes).
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))

CSV = os.path.join(os.path.dirname(__file__), "..", "..",
                   "knowledge/domains/Payment/phase0/dmee_full",
                   "dmee_tree_node_d01_sepa_v001_fresh.csv")

# What YCL_IDFI_CGI_DMEE_FALLBACK_CM001 GET_CREDIT does for each XPath
# (extracted from extracted_code/FI/DMEE_p01_canonical/YCL_IDFI_CGI_DMEE_FALLBACK====CM001.abap)
BADI_BEHAVIOR = {
    "<PmtInf><CdtTrfTxInf><Cdtr><Nm>":
        "if item.origin=TR-CM-BT → c_value=fpayp-sgtxt; truncate to 35; buffer overflow",
    "<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>":
        "prepend mv_cdtr_name+35 (name overflow) if same fpayh; truncate to 70",
    "<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>":
        "[commented out — uses fpayh-zbnkl else clear]",
}

# Live samples from debugger session #073 (run 10001B, vendor 0010008305)
SAMPLE_FPAYH = {
    "ZNME1":"Simona BERTOLDINI", "KOINH":"Simona BERTOLDINI",
    "ZSTRA":"BFM/FAS/PAY",        "ZPSTL":"75007",
    "ZORT1":"Paris",              "ZORT2":"Office H.101 bat B4 PATIO",
    "ZLAND":"FR",                 "ZADNR":"0000055667",
    "ZIBAN":"FR7630438001004000018993262", "ZSWIF":"INGBFR21",
    "ZBNKL":"3043800100",         "ZBNKN":"40000189932",
    "ZBNKA":"ING Direct",         "ZBSTR":"3 Rue Du DocteurBauer",
    "ZBORT":"93400 St. Ouen",     "ZBNKS":"FR",
    "ZBUKR":"UNES",               "ABSBU":"UNES",
    "HBKID":"SOG01",              "HKTID":"EUR01",
    "HWAER":"USD",                "UBHKT":"0001175012",
    "LAUFD":"20260507",           "LAUFI":"10001B",
    "LFDNR":"00528616",           "GRPNO":"100",
    "DORIGIN":"FI-AP",            "GPA1T":"11",
    "GPA1R":"0010008305",         "RWBTR":"100.00",
}
# UNES paying co (T001 + ADRC)
UNES_ADRC = {"NAME1":"UNESCO","STREET":"Place de Fontenoy",
             "HOUSE_NUM1":"7","POST_CODE1":"75007",
             "CITY1":"PARIS","COUNTRY":"FR","REGION":""}
# Vendor 0010008305 ADRC (real address from ADDRNUMBER=0000055667)
VEND_ADRC = {"NAME1":"Simona BERTOLDINI","STREET":"Place de Fontenoy",
             "HOUSE_NUM1":"7","POST_CODE1":"75007",
             "CITY1":"PARIS","COUNTRY":"FR","REGION":""}

# Read CSV
nodes = []
with open(CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        nodes.append(r)
by_id = {n["NODE_ID"]: n for n in nodes}

def xpath(nid, _seen=None):
    if _seen is None: _seen = set()
    if nid in _seen or nid not in by_id: return ""
    _seen.add(nid)
    n = by_id[nid]
    p = n.get("PARENT_ID","").strip()
    t = (n.get("TECH_NAME") or "").strip()
    if p and p in by_id and p != nid:
        return f"{xpath(p,_seen)}/{t}" if t else xpath(p,_seen)
    return f"/{t}" if t else ""

def section(xp):
    for s in ("Cdtr","Dbtr","CdtrAgt","DbtrAgt","CdtrAcct","DbtrAcct","RmtInf",
             "PmtTpInf","PmtId","CdtTrfTxInf","PmtInf","GrpHdr","InitgPty"):
        if f"/{s}/" in xp or xp.endswith(f"/{s}"): return s
    return "OTHER"

def proposed_y_source(xp, tech):
    """If we migrated this node to Y_FI_DMEE_ADR, what would it return?"""
    is_cdtr = "/Cdtr/" in xp or xp.endswith("/Cdtr")
    is_dbtr = "/Dbtr/" in xp or xp.endswith("/Dbtr")
    if not (is_cdtr or is_dbtr): return ""
    src = VEND_ADRC if is_cdtr else UNES_ADRC
    m = {"Nm":"NAME1","StrtNm":"STREET","BldgNb":"HOUSE_NUM1",
         "PstCd":"POST_CODE1","TwnNm":"CITY1","Ctry":"COUNTRY",
         "CtrySubDvsn":"REGION"}
    fld = m.get(tech)
    if not fld: return ""
    val = src.get(fld) or ""
    return f"ADRC-{fld} = '{val}'"

# Build short xpath form (e.g. <PmtInf><CdtTrfTxInf><Cdtr><Nm>)
def short_path(nid):
    parts = []
    cur = nid
    seen = set()
    while cur and cur in by_id and cur not in seen:
        seen.add(cur)
        n = by_id[cur]
        t = (n.get("TECH_NAME") or "").strip()
        if t: parts.append(t)
        cur = n.get("PARENT_ID","").strip()
    parts.reverse()
    # drop the Document/CstmrCdtTrfInitn prefix if present
    while parts and parts[0] in ("Document","CstmrCdtTrfInitn"):
        parts.pop(0)
    return "<" + "><".join(parts) + ">" if parts else ""

# Build rows
rows = []
for n in nodes:
    if n.get("NODE_TYPE") not in ("ELEM",): continue
    xp = xpath(n["NODE_ID"])
    sect = section(xp)
    if sect not in ("Cdtr","Dbtr","CdtrAgt","DbtrAgt","CdtrAcct","DbtrAcct"): continue
    sp = short_path(n["NODE_ID"])
    tech = (n.get("TECH_NAME") or "").strip()
    src_tab = (n.get("MP_SC_TAB") or "").strip()
    src_fld = (n.get("MP_SC_FLD") or "").strip()
    exit_   = (n.get("MP_EXIT_FUNC") or "").strip()
    const   = (n.get("MP_CONST") or "").strip()

    tree_map = f"{src_tab}-{src_fld}" if src_tab else (f"const={const}" if const else "—")
    tree_exit = exit_ or "—"
    badi_post = BADI_BEHAVIOR.get(sp, "(no redefinition — passthrough)")

    # Sample
    sample = ""
    if src_tab == "FPAYH" and src_fld:
        sample = SAMPLE_FPAYH.get(src_fld, "?")
    elif const:
        sample = const
    elif exit_ == "Y_FI_DMEE_ADR":
        # uses UNES address
        m = {"Nm":"NAME1","StrtNm":"STREET","BldgNb":"HOUSE_NUM1",
             "PstCd":"POST_CODE1","TwnNm":"CITY1"}
        if tech in m: sample = UNES_ADRC.get(m[tech],"")

    # Status
    if not src_tab and not exit_ and not const:
        status = "❌ FALTA"
    elif tech == "StrtNm" and "/Cdtr/" in xp and src_fld == "ZSTRA":
        status = "❌ WRONG (BFM/FAS/PAY)"
    elif exit_ == "Y_FI_DMEE_ADR" and tech in ("Ctry","Dept","SubDept","CtrySubDvsn"):
        status = "❌ FM no maneja"
    elif exit_ == "Y_FI_DMEE_ADR":
        status = "✅"
    elif src_tab:
        status = "✅"
    else:
        status = "⚠️"

    rows.append({
        "section": sect, "xpath": sp, "tech": tech,
        "tree_map": tree_map, "tree_exit": tree_exit,
        "badi_post": badi_post, "sample": sample,
        "y_source": proposed_y_source(xp, tech), "status": status,
    })

# Sort: Dbtr first, Cdtr second; then by xpath
section_order = {"Dbtr":1,"DbtrAgt":2,"DbtrAcct":3,"Cdtr":4,"CdtrAgt":5,"CdtrAcct":6}
rows.sort(key=lambda r: (section_order.get(r["section"],99), r["xpath"]))

# Output Markdown
md = ["# DMEE `/SEPA_CT_UNES` V001 — Tabla comparativa de mapping",
      "",
      f"Sample run: D01 LAUFD=20260507 LAUFI=10001B vendor 0010008305 (Simona BERTOLDINI)",
      f"UNES paying co address (T001/ADRC): Place de Fontenoy 7, 75007 PARIS, FR",
      f"Vendor 0010008305 address (ADRC): Place de Fontenoy 7, 75007 PARIS, FR",
      "",
      "## Leyenda",
      "- **Tree mapping**: `MP_SC_TAB-MP_SC_FLD` configurado en DMEE_TREE_NODE",
      "- **Tree exit**: `MP_EXIT_FUNC` (FM que el motor llama para computar el value)",
      "- **CGI BAdI post-process**: lo que `YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT` hace AL c_value DESPUÉS de que el árbol lo populó",
      "- **Y_FI_DMEE_ADR (propuesta)**: lo que devolvería si lo migráramos al FM unificado",
      ""]

current_sec = None
for r in rows:
    if r["section"] != current_sec:
        current_sec = r["section"]
        md.append(f"\n## {current_sec}\n")
        md.append("| Nodo | Tree mapping | Tree exit | CGI BAdI post-process | Sample actual | Y_FI_DMEE_ADR (propuesta) | Estado |")
        md.append("|---|---|---|---|---|---|---|")
    xp = r["xpath"][-50:] if len(r["xpath"]) > 50 else r["xpath"]
    md.append(f"| `{r['tech']}` | `{r['tree_map']}` | `{r['tree_exit']}` | {r['badi_post'][:60]} | `{r['sample'][:30]}` | `{r['y_source']}` | {r['status']} |")

# Save and print
out_path = os.path.join(os.path.dirname(__file__), "..", "..",
                       "knowledge/domains/Payment/dmee_sepa_v001_compare_table.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"Saved: {out_path}\n")
print("\n".join(md))
