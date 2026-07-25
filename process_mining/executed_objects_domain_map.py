"""
executed_objects_domain_map.py — MAP EVERYTHING executed, by domain (AUTHORITATIVE).
------------------------------------------------------------------------------------
Classifies EVERY executed object (4 channels, system-wide) to a domain using the
AUTHORITATIVE signal: each object's DEVELOPMENT PACKAGE (TADIR.DEVCLASS), which is
module-coded (FMRP=FM, FBAS=FI, ME=MM-purch, PC10=HR-payroll, CJ*=PS, ...) and always
populated — far more reliable than the cryptic tcode/report name.

Channels: dialog tcode (rsau Transaction Start -> PARAM1 -> program via d01_tstc),
report (rsau Report Start -> SLGREPNA = program), RFC/BAPI (rsau RFC Function Call ->
PARAM3), batch job (tbtcp -> PROGNAME).

Classifier layers (first hit): (1) DEVCLASS->domain (package prefix) via TADIR;
(2) DLVUNIT->domain (software component) via TDEVC; (3) authoritative overlays
(tfdir_custom.APP_DOMAIN, job_classification); (4) name-prefix; (5) tcode TEXT.

Caches TADIR(PROG) + TDEVC into the Gold DB (tadir_prog, tdevc) on first run so the
object->domain map becomes a durable Gold DB asset. Emits brain_v2/executed_objects_domain_map.json.
Run: python process_mining/executed_objects_domain_map.py
"""
import re
import sys
import json
import sqlite3
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[0]
MCP = REPO / "Zagentexecution" / "mcp-backend-server-python"
sys.path.insert(0, str(MCP))
from gold_ref import GOLD  # T5: resolved via golden_manifest.json, not a hardcoded path
JOBCLASS = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "job_classification.json"
OUT = REPO / "brain_v2" / "executed_objects_domain_map.json"

# DEVCLASS (package) prefix -> domain. Authoritative grouping. First match wins.
DEVCLASS_RULES = [
    ("PSM_FM",          r"^(FM|FMRP|FMFR|FMBAS|FMCA|FMRE|FMOA|FMOI|FMDM|FMHH|FMFG|FMKU|FMAVC|FMCE|FMDT|FMBW|FMFI|BPIN|BP$|BPFM|AYM|/?ISPSFM|ISPS_FM)"),
    ("Payment_BCM",     r"^(FZ|FPAYM|PAYM|FCHK|FMKK|BFIBL|FIBL_PAY|FPAY|FMEC|FCH)"),
    ("FI",              r"^(FB|FBAS|FIBP|FI[A-Z]|FAGL|FVVD|GLT|FGL|FQ|GBAS|FBA|FINS|GLE|FDES|FAA|AABA|FBAA|FICA|FGLG|RFK|GL_)"),
    ("Treasury_EBS",    r"^(FF|FTE|FTBB|IDFI|TRTM|FTR|FQM|FDT)"),
    ("Procurement_P2P", r"^(ME|MM|MEPO|MR|MB|EINK|MMPUR|WRF|MEWP|ML|MMIM|MMINV)"),
    ("PS",              r"^(CJ|PS[A-Z]?|KPR|PROJ|CN|PSEX|PSHLP|RPSCO)"),
    ("Controlling",     r"^(KO|KB|KS|KA|CO[A-Z]|KE|KKB|KAZB|KAL|KKS|RKE)"),
    ("HCM",             r"^(PA|PB|PC|PT|PU|P[0-9]|HRPAY|PAOC|PCAL|HRAS|PBAS|PXX|RPAA|PCPO|PSPAR|HRPADXX|PAOCFB|PTIM|PBEN|PCAS|HRFPM|PEPM)"),
    ("Travel",          r"^(FITV|PTRM|TRV|FTRV|PTRA)"),
    ("BusinessPartner", r"^(BUPA|BUP|FK|FD|FLBP|KD|WKR|LO_MD_BP|VLC|BUS_LOCATOR)"),
    ("Integration",     r"^(SAB|ED|BD|WL|SRT|SAI|IDOC|SIW|SWLWP|SOA|RSEEP|SDYN_INT)"),
    ("HR_Workflows",    r"^(SWF|SWO|RHSWF|SWUS|WFSC|SWU|PVWF|HRWPC)"),
    ("Output",          r"^(NA|SD_NACE|VN)"),
    ("CTS_Transport",   r"^(SCTS|STRD|SPAU|STMS|SLDB|SDEPL|SPAM|SAINT|SP00)"),
    # custom packages (Z*/Y*) by sub-namespace
    ("HCM",             r"^(ZHR|YHR|ZP[0-9A-Z]|YP[0-9A-Z]|ZTHR)"),
    ("PSM_FM",          r"^(ZICTP|ZFM|YFM|ZPS_BCS|ZBCS)"),
    ("FI",              r"^(ZFI|YFI|FREP|ZGL|FMBPA_E|FMAVCA_E)"),
    ("Payment_BCM",     r"^(ZPAY|YPAY|ZBCM)"),
    ("Integration",     r"^(SMOI|SAI_|SBDC|KC_GEN|ZINT|ZRFC|ZIDOC)"),
    ("Basis_Security",  r"^(S[A-Z]|BC|SUSR|STSK|SRSR|SEU|SDYN|SABP|SAPP|SBC|SCSC|SZ|SPO|ST_|SMON|SARA|SYST|SUU|RSPO|RSAU|SUST|SWNC|SECU|SDB|SDWB|SDIC)"),
]
# table / infotype / object-name -> domain (for generated programs that embed an object)
TABLE_RULES = [
    ("HCM",             r"^(PA[0-9]|PB[0-9]|PCL|T5[0-9]|HRP|HRT|T52|T51|T7|PEVE|PTEX|PA_IT)"),
    ("PSM_FM",          r"^(FM|BPJA|BPGE|FMFIN|FMIOI|FMIFIIT|FMAVC|YTFM)"),
    ("FI",              r"^(BSE|BSI|BSA|BKPF|SKA|SKB|FAGL|GLT|T001|KNC|LFC)"),
    ("Procurement_P2P", r"^(EK|ME|MEMEBANF|RSEG|RBKP|ESLL|EBAN)"),
    ("PS",              r"^(PRPS|PROJ|PRHI|RPSCO|AUFK)"),
    ("Payment_BCM",     r"^(REGU|PAYR|BNKA|FEB|T012|T042)"),
    ("BusinessPartner", r"^(LFA|LFB|KNA|KNB|BUT|ADRC|CVI)"),
    ("Treasury_EBS",    r"^(FEBKO|FEBEP|T028|T033)"),
    ("HR_Workflows",    r"^(ZTHRFIORI|SWW|HRWP)"),
]


def resolve_generated(name):
    """Generated program -> the embedded object token (table/infotype/query) for classification."""
    n = (name or "").strip()
    if n.startswith("/1BCDWB/DB"):          # generated DB/logical-db program -> table
        return n[len("/1BCDWB/DB"):].strip()
    if n.startswith(("AQ", "!Q")):           # SAP Query generated program
        # tokens after the workspace padding often reference the table/infotype
        toks = re.split(r"=+|/", n)
        for t in toks:
            if t and not t.startswith(("AQ", "!Q", "SAPQUERY", "ZZ")) and len(t) >= 3:
                return t
    return None


def _match_table(tok):
    t = (tok or "").strip().upper()
    if not t:
        return None
    for dom, pat in TABLE_RULES:
        if re.match(pat, t):
            return dom
    return None
DLVUNIT_RULES = [
    ("PSM_FM", r"EA-PS|^IS_PS|PSM"),
    ("HCM", r"SAP_HR|EA-HR|SAP_HRRXX|SAP_HRGXX|HR_"),
    ("Treasury_EBS", r"FIN_TRM|EA-FINSERV"),
    ("FI", r"SAP_FIN|EA-FIN|^FI"),
    ("Procurement_P2P", r"SAP_APPL.*MM|SRM"),
    ("Basis_Security", r"SAP_BASIS|WEBCUIF|SAP_UI|SAP_GWFND|ST-PI|SAP_ABA|BBPCRM"),
]
APP_DOMAIN_MAP = {
    "FM/Budget": "PSM_FM", "PS/Projects": "PS", "Travel": "Travel", "HR Workflow": "HR_Workflows",
    "HR": "HCM", "CMT/Vendor": "BusinessPartner", "CMT/Master Data": "BusinessPartner",
    "Procurement": "Procurement_P2P", "FI/Finance": "FI", "Banking/Validation": "Payment_BCM",
    "SISTER": "Integration", "UNESDIR": "Integration", "IDoc": "Integration", "RFC Utils": "Integration",
    "Mouv/Asset Mgmt": "FI", "UBO Field Office": "Treasury_EBS", "Dashboards": "Output",
    "SLD/Monitoring": "Basis_Security", "Basis/Tools": "Basis_Security", "Data Extraction": "Integration",
}
JOBLABEL_MAP = {"FM": "PSM_FM", "Payment": "Payment_BCM", "FI": "FI", "Procurement": "Procurement_P2P",
                "HCM": "HCM", "HR": "HCM", "PS": "PS", "Treasury": "Treasury_EBS",
                "Basis/System": "Basis_Security", "SAPConnect/Email": "Basis_Security", "Integration": "Integration"}
# name-prefix + text fallbacks (reuse from prior version, condensed)
NAME_RULES = [
    ("PSM_FM", r"^(FM[0-9A-Z]|RFFM|YFM|YPS|ZFM|ZICTP_REP|ZICTP_COCKPIT)"),
    ("Payment_BCM", r"^(F110|FBZP|REGU|PAYR|FCH|RFFO|SAPFPAYM|DMEE|FEB)"),
    ("Procurement_P2P", r"^(ME[0-9]|MIGO|MIRO|MB|MR[0-9])"),
    ("FI", r"^(FB|F-[0-9]|FBL|FS[0-9]|FAGL|RFITEM|OB[A-Z])"),
    ("PS", r"^(CJ|CN[0-9]|PROJ|RPSCO)"),
    ("HCM", r"^(PA[0-9]|PA30|PT|PU|PC00|HR|RP[A-Z]|MP[0-9])"),
]
TEXT_RULES = [
    ("PSM_FM", r"budget|fund|commitment item|funds cent|avc|earmark"),
    ("Payment_BCM", r"payment|bank transfer|\bdme\b|check|cheque|house bank"),
    ("Procurement_P2P", r"purchas|requisition|goods receipt|invoice receipt"),
    ("FI", r"\bg/?l\b|general ledger|accounting doc|post document|asset"),
    ("HCM", r"payroll|personnel|employee|infotype|absence"),
    ("PS", r"\bwbs\b|project|network activit"),
    ("BusinessPartner", r"vendor|customer|business partner|creditor|debtor"),
    ("Controlling", r"cost center|internal order|cost element"),
]


def _read_all(g, tbl, fields, where=""):
    r = g.call("RFC_READ_TABLE", QUERY_TABLE=tbl, FIELDS=[{"FIELDNAME": f} for f in fields],
               OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=0)
    meta = r["FIELDS"]
    return [tuple(row["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip() for f in meta)
            for row in r["DATA"]]


def ensure_cache(con):
    """Pull TADIR(PROG) + TDEVC into the Gold DB once (durable)."""
    cur = con.cursor()
    have = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "tadir_prog" in have and "tdevc" in have:
        return
    from rfc_helpers import get_connection  # type: ignore
    g = get_connection("P01")
    print("  caching TADIR(PROG) ~388k + TDEVC ~28k from P01 (one-time) ...")
    if "tadir_prog" not in have:
        rows = _read_all(g, "TADIR", ["OBJ_NAME", "DEVCLASS"], "PGMID = 'R3TR' AND OBJECT = 'PROG'")
        cur.execute("CREATE TABLE tadir_prog (OBJ_NAME TEXT PRIMARY KEY, DEVCLASS TEXT)")
        cur.executemany("INSERT OR REPLACE INTO tadir_prog VALUES (?,?)", rows); con.commit()
        print(f"    tadir_prog: {len(rows)} programs")
    if "tdevc" not in have:
        rows = _read_all(g, "TDEVC", ["DEVCLASS", "DLVUNIT", "COMPONENT"])
        cur.execute("CREATE TABLE tdevc (DEVCLASS TEXT PRIMARY KEY, DLVUNIT TEXT, COMPONENT TEXT)")
        cur.executemany("INSERT OR REPLACE INTO tdevc VALUES (?,?,?)", rows); con.commit()
        print(f"    tdevc: {len(rows)} packages")
    g.close()


def _match(rules, val):
    v = (val or "").strip().upper()
    if not v:
        return None
    for dom, pat in rules:
        if re.match(pat, v) if rules in (DEVCLASS_RULES, NAME_RULES) else re.search(pat, v):
            return dom
    return None


def make_classifier(con):
    """Load maps + return (domain_of, ctx). REUSABLE so mine_domain.py uses the SAME classifier — one
    source of truth, no wheel reinvention next session."""
    ensure_cache(con)
    c = con.cursor()
    prog_dc = dict(c.execute("SELECT OBJ_NAME, DEVCLASS FROM tadir_prog").fetchall())
    dc_dlv = {dc: dl for dc, dl, _ in c.execute("SELECT DEVCLASS, DLVUNIT, COMPONENT FROM tdevc").fetchall()}
    tc_prog = dict(c.execute("SELECT TCODE, PGMNA FROM d01_tstc").fetchall())
    tc_text = {tc: tx for tc, tx in c.execute("SELECT TCODE, TTEXT FROM d01_tstct WHERE SPRSL='E'").fetchall()}
    fm_dom = {fn: APP_DOMAIN_MAP.get(ad.strip()) for fn, ad in
              c.execute("SELECT FUNCNAME, APP_DOMAIN FROM tfdir_custom").fetchall() if ad and ad.strip()}
    job_dom = {}
    try:
        jc = json.loads(JOBCLASS.read_text(encoding="utf-8"))
        for prog, meta in jc.get("programs", {}).items():
            if isinstance(meta, dict) and meta.get("label"):
                job_dom[prog] = JOBLABEL_MAP.get(meta["label"])
    except Exception:
        pass

    def domain_of(name, program=None, text=None, overlay=None):
        prog = program or (name if name in prog_dc else None)
        dc = prog_dc.get(prog) if prog else None
        return (overlay
                or _match(DEVCLASS_RULES, dc)
                or _match(DLVUNIT_RULES, dc_dlv.get(dc) if dc else None)
                or _match(NAME_RULES, name) or _match(NAME_RULES, program)
                or _match(TEXT_RULES, text)
                or _match_table(resolve_generated(name))
                or "Uncatalogued")

    return domain_of, {"prog_dc": prog_dc, "dc_dlv": dc_dlv, "tc_prog": tc_prog,
                       "tc_text": tc_text, "fm_dom": fm_dom, "job_dom": job_dom}


def main():
    con = sqlite3.connect(GOLD)
    domain_of, ctx = make_classifier(con)
    tc_prog, tc_text, fm_dom, job_dom = ctx["tc_prog"], ctx["tc_text"], ctx["fm_dom"], ctx["job_dom"]
    c = con.cursor()

    def grouped(where, field):
        return c.execute(f"SELECT {field} o, COUNT(*) n, COUNT(DISTINCT SLGUSER) u FROM rsau_audit_history "
                         f"WHERE TXSUBCLSID='{where}' AND {field}<>'' GROUP BY {field}").fetchall()

    print("Scanning rsau (15.6M) + tbtcp; classifying by DEVCLASS ...")
    census = defaultdict(lambda: defaultdict(lambda: {"objects": 0, "execs": 0}))
    obj_index = defaultdict(list)

    def add(channel, rows, resolve_tcode=False, overlay_map=None):
        for o, n, u in rows:
            prog = tc_prog.get(o) if resolve_tcode else None
            txt = tc_text.get(o) if resolve_tcode else None
            dom = domain_of(o, prog, txt, (overlay_map or {}).get(o))
            census[dom][channel]["objects"] += 1
            census[dom][channel]["execs"] += n
            obj_index[dom].append((channel, o, n, u))

    add("dialog_tcode", grouped("Transaction Start", "PARAM1"), resolve_tcode=True)
    add("report", grouped("Report Start", "SLGREPNA"))
    add("rfc_bapi", grouped("RFC Function Call", "PARAM3"), overlay_map=fm_dom)
    add("batch_job", c.execute("SELECT PROGNAME o, COUNT(*) n, COUNT(DISTINCT JOBNAME||JOBCOUNT) u "
                               "FROM tbtcp WHERE PROGNAME<>'' GROUP BY PROGNAME").fetchall(), overlay_map=job_dom)

    domains = {d: {"total_objects": sum(v["objects"] for v in ch.values()),
                   "total_execs": sum(v["execs"] for v in ch.values()),
                   "by_channel": {k: dict(v) for k, v in ch.items()}} for d, ch in census.items()}
    out = {"_meta": {"source": "rsau(~4mo)+tbtcp; classifier=DEVCLASS(TADIR)->DLVUNIT->overlay->name->text",
                     "channels": ["dialog_tcode", "report", "rfc_bapi", "batch_job"]},
           "by_domain": dict(sorted(domains.items(), key=lambda kv: -kv[1]["total_execs"])),
           "top_objects_by_domain": {d: [{"channel": ch, "object": o, "execs": n, "users": u}
                                          for ch, o, n, u in sorted(obj_index[d], key=lambda x: -x[2])[:15]]
                                     for d in domains}}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tot = sum(d["total_objects"] for d in domains.values())
    unc = domains.get("Uncatalogued", {}).get("total_objects", 0)
    print(f"\n=== EXECUTED OBJECTS BY DOMAIN ({tot:,} distinct) — {100*(tot-unc)/tot:.1f}% classified ===")
    print(f"  {'domain':18s} {'objects':>8} {'execs':>12}   channels")
    for d, v in out["by_domain"].items():
        ch = " ".join(f"{k.split('_')[0]}:{cv['objects']}" for k, cv in v["by_channel"].items())
        print(f"  {d:18s} {v['total_objects']:>8,} {v['total_execs']:>12,}   {ch}")
    print(f"\n  Uncatalogued: {unc:,} · Emitted: {OUT}")
    con.close()


if __name__ == "__main__":
    main()
