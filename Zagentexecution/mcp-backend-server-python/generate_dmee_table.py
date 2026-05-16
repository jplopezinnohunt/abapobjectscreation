"""Generate full DMEE SEPA_CT_UNES V001 mapping table."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..",
                       "knowledge/domains/Payment/phase0/dmee_full",
                       "dmee_tree_node_d01_sepa_v001.csv")

# Sample values from current FPAYH (run 10001B, vendor 0010008305)
# Captured live from debugger Session #073 (Simona BERTOLDINI)
SAMPLE_FPAYH = {
    "ZNME1": "Simona BERTOLDINI",  "KOINH": "Simona BERTOLDINI",
    "ZSTRA": "BFM/FAS/PAY",         "ZPSTL": "75007",
    "ZORT1": "Paris",               "ZORT2": "Office H.101 bat B4 PATIO",
    "ZLAND": "FR",                  "ZADNR": "0000055667",
    "ZIBAN": "FR7630438001004000018993262", "ZSWIF": "INGBFR21",
    "ZBNKL": "3043800100",          "ZBNKN": "40000189932",
    "ZBNKA": "ING Direct",          "ZBSTR": "3 Rue Du DocteurBauer",
    "ZBORT": "93400 St. Ouen",      "ZBNKS": "FR",
    "ZBUKR": "UNES",                "ABSBU": "UNES",
    "HBKID": "SOG01",               "HKTID": "EUR01",
    "HWAER": "USD",                 "UBHKT": "0001175012",
    "LAUFD": "20260507",            "LAUFI": "10001B",
    "LFDNR": "00528616",            "GRPNO": "100",
    "DORIGIN": "FI-AP",             "GPA1T": "11",
    "GPA1R": "0010008305",          "RWBTR": "(amount)",
    "ZSPRA": "F",                   "ZANRE": "Mrs.",
}
# UNES company-master derived (T001 + ADRC ADDRNUMBER=22029)
UNES_T001 = {"BUTXT": "UNESCO", "ADRNR": "0000022029", "LAND1": "FR"}
UNES_ADRC = {"NAME1": "UNESCO", "STREET": "Place de Fontenoy",
             "HOUSE_NUM1": "7", "POST_CODE1": "75007",
             "CITY1": "PARIS", "COUNTRY": "FR", "STR_SUPPL1": ""}

# Read CSV
nodes = []
with open(CSV_PATH, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        nodes.append(r)

by_id = {n["NODE_ID"]: n for n in nodes}

def xpath_of(nid, _seen=None):
    if _seen is None: _seen = set()
    if nid in _seen or nid not in by_id: return ""
    _seen.add(nid)
    n = by_id[nid]
    parent = n.get("PARENT_ID","").strip()
    tech = (n.get("TECH_NAME") or "").strip()
    if parent and parent in by_id and parent != nid:
        return f"{xpath_of(parent, _seen)}/{tech}" if tech else xpath_of(parent, _seen)
    return f"/{tech}" if tech else ""

def determine_status(n):
    """Return (status_emoji, source_str, sample, notes)."""
    src_tab = (n.get("MP_SC_TAB") or "").strip()
    src_fld = (n.get("MP_SC_FLD") or "").strip()
    exit_   = (n.get("MP_EXIT_FUNC") or "").strip()
    const   = (n.get("MP_CONST") or "").strip()
    cv_rule = (n.get("CV_RULE") or "").strip()
    ntype   = n.get("NODE_TYPE","")

    # Composite types — not leaf
    if ntype not in ("ELEM",):
        return "—", f"({ntype})", "", ""

    # Direct mapping
    if src_tab and src_fld:
        sample = SAMPLE_FPAYH.get(src_fld, "")
        if sample:
            return "✅", f"{src_tab}-{src_fld}", sample, "direct mapping"
        else:
            return "⚠️", f"{src_tab}-{src_fld}", "?", "verificar runtime"

    # Constant
    if const:
        return "✅", f"const={const}", const, "hardcoded constant"

    # Exit (BAdI / function)
    if exit_:
        # SEPA: nodes with BAdI exits route to YCL_IDFI_CGI_DMEE_FALLBACK_CM001
        # for Cdtr; Dbtr would need GET_DEBIT (not implemented yet)
        if "DMEE_EXIT_SE" in exit_:
            return "✅", f"exit={exit_}", "(SAP std)", "SAP-standard SEPA exit"
        if exit_ in ("CGI_VGI_CDTR_AGT","CGI_VGI_CRED_NAME"):
            return "✅", f"exit={exit_}", "(BAdI)", "BAdI YCL_IDFI_CGI_DMEE_FALLBACK"
        return "⚠️", f"exit={exit_}", "?", "BAdI/exit — verificar"

    # CV_RULE (composite-value rule)
    if cv_rule:
        return "⚠️", f"cv={cv_rule}", "?", "composite rule"

    return "❌", "(no source)", "—", "FALTA"


# Build all rows with xpath
out = []
for n in nodes:
    xp = xpath_of(n["NODE_ID"])
    status, src, sample, notes = determine_status(n)
    out.append({
        "xpath": xp, "tech": (n.get("TECH_NAME") or "").strip(),
        "ntype": n.get("NODE_TYPE","").strip(),
        "status": status, "source": src, "sample": sample, "notes": notes,
        "node_id": n["NODE_ID"],
    })
out.sort(key=lambda x: x["xpath"])

# Group by section
def section_of(xp):
    parts = xp.split("/")
    for p in parts:
        if p in ("Dbtr","Cdtr","CdtrAgt","DbtrAgt","CdtrAcct","DbtrAcct",
                 "RmtInf","PmtTpInf","PmtId","CdtTrfTxInf","PmtInf","GrpHdr",
                 "InitgPty"):
            return p
    return "OTHER"

sections = {}
for r in out:
    if not r["xpath"]: continue
    s = section_of(r["xpath"])
    sections.setdefault(s, []).append(r)

# Output as markdown
md = []
md.append("# DMEE `/SEPA_CT_UNES` V001 — mapeo completo")
md.append(f"\nNodos totales: {len(out)} · Sample run: D01 LAUFD=20260507 LAUFI=10001B vendor 0010008305\n")

ORDER = ["GrpHdr","InitgPty","PmtInf","PmtTpInf","Dbtr","DbtrAcct","DbtrAgt",
        "PmtId","CdtTrfTxInf","Cdtr","CdtrAcct","CdtrAgt","RmtInf","OTHER"]
for sec in ORDER:
    if sec not in sections: continue
    md.append(f"\n## {sec}\n")
    md.append("| Nodo XML | Source | Sample | Estado | Notas |")
    md.append("|---|---|---|---|---|")
    for r in sections[sec]:
        if r["ntype"] not in ("ELEM",):  # skip composites in main table
            continue
        xp = r["xpath"][-60:] if len(r["xpath"]) > 60 else r["xpath"]
        sample_display = (r["sample"] or "")[:40]
        notes_display = (r["notes"] or "")[:40]
        md.append(f"| `{xp}` | `{r['source']}` | `{sample_display}` | {r['status']} | {notes_display} |")

# Save
out_path = os.path.join(os.path.dirname(__file__), "..", "..",
                       "knowledge/domains/Payment/dmee_sepa_ct_unes_v001_mapping_table.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print(f"Saved: {out_path}\n")
print("\n".join(md))
