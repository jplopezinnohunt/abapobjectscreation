"""component_map.py — SAP application component → canonical domain. ONE definition.

The authoritative signal for "what does this object belong to" is SAP's own component
hierarchy, resolved deterministically:

    object → TADIR (package) → TDEVC (component id) → DF14L (application component)

Before this module, two consumers each carried their own copy of the mapping and the
classifier did not use it at all — it guessed from package-name regex, which is how
`FTB` came to swallow `FTBB` (bank statements) into deal management with no error.

Longest matching prefix wins, so `FI-BL-PT-BS` beats `FI-BL` beats `FI`. Ordering in the
dict is irrelevant by construction — that is the point: an ordered rule ladder fails
silently when a greedy rule is placed early, and this cannot.
"""
import sqlite3
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Application component prefix -> canonical domain key.
COMPONENT_TO_DOMAIN = {
    "PSM-FM": "PSM_FM", "PSM": "PSM_FM", "IS-PS-CA": "PSM_FM", "PSM-GM": "GM",
    "PA-PM-PB": "PBC",
    "FI-AA": "FI_AA",
    "RE-FX": "RE_FX", "RE": "RE_FX",
    "SD": "SD",
    "PM": "PM", "PM-EQM": "PM",
    "FIN-FSCM-TRM": "TRM", "TR-TM": "TRM",
    "FIN-FSCM-BNK": "Payment_BCM", "FI-BL-PT-AP": "Payment_BCM",
    "FI-AP-AP-PT": "Payment_BCM", "FI-BL-PT-PO": "Payment_BCM",
    "FI-BL-PT-BS": "Treasury_EBS", "FIN-FSCM-CLM": "Treasury_EBS", "FI-BL": "Treasury_EBS",
    "CO": "CO",
    "MM": "Procurement_P2P", "MM-PUR": "Procurement_P2P", "MM-IM": "Procurement_P2P",
    "FI-TV": "Travel",
    "PA": "HCM", "PY": "HCM", "PT": "HCM", "PE": "HCM", "PA-OS": "HCM",
    "PS": "PS",
    "FI": "FI", "FI-GL": "FI", "FI-AP": "FI", "FI-AR": "FI",
    "BC-SRV-BP": "BusinessPartner", "AP-MD-BF-SYN": "BusinessPartner",
    "LO-MD-BP": "BusinessPartner", "CA-GTF-CVI": "BusinessPartner",
    "BC-CTS": "CTS_Transport", "BC-SEC": "Security",
    # technical substrate — a legitimate non-business tier, never a dumping ground
    "BC": "Basis_Security", "BW": "BW_embedded", "SV": "Basis_Security", "ST": "Basis_Security",
}


def component_to_domain(component):
    """Longest matching component prefix wins. Returns (domain, matched_prefix)."""
    if not component:
        return None, None
    c = str(component).upper()
    best = None
    for pref, dom in COMPONENT_TO_DOMAIN.items():
        if c == pref or c.startswith(pref + "-"):
            if best is None or len(pref) > len(best[0]):
                best = (pref, dom)
    return (best[1], best[0]) if best else (None, None)


@lru_cache(maxsize=1)
def _package_component(db_path=None):
    """package (DEVCLASS) -> application component string, via TDEVC + DF14L."""
    path = db_path or str(GOLD)
    if not Path(path).exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        have = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"tdevc", "df14l"} <= have:
            con.close()
            return {}
        rows = con.execute(
            "SELECT d.DEVCLASS, f.PS_POSID FROM tdevc d "
            "JOIN df14l f ON f.FCTR_ID = d.COMPONENT").fetchall()
        con.close()
        return {dc: pos for dc, pos in rows if pos}
    except sqlite3.Error:
        return {}


@lru_cache(maxsize=1)
def _fm_package(db_path=None):
    """function module -> package, via TFDIR -> function group (FUGR) -> TADIR.

    Function modules are NOT repository objects in their own right: they belong to a
    function GROUP, whose program is SAPL<FUGR>. Skipping that hop is why the frontier
    was dominated by BAPIs — BAPI_PR_GETDETAIL, BAPI_TRIP_CHECK_STATUS, BAPI_PO_GETDETAIL1
    all sat unclassified while being plainly Procurement and Travel. They are also exactly
    the satellite calls that make up the externally-orchestrated traffic, so leaving them
    unresolved blinded the model to its own headline.
    """
    path = db_path or str(GOLD)
    if not Path(path).exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        have = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"tfdir_all", "tadir_obj"} <= have:
            con.close()
            return {}
        rows = con.execute(
            "SELECT f.FUNCNAME, t.DEVCLASS FROM tfdir_all f "
            "JOIN tadir_obj t ON t.OBJECT='FUGR' AND t.OBJ_NAME = substr(f.PNAME, 5)").fetchall()
        con.close()
        return {fn.strip(): dc.strip() for fn, dc in rows if dc}
    except sqlite3.Error:
        return {}


# Custom Z/Y function modules have no SAP component: their function group lives in a
# customer package that DF14L cannot resolve, by definition. They need their own rung —
# and they are exactly the objects the product thesis rests on, because no commercial
# tool can label them either. tfdir_custom.APP_DOMAIN is the curated answer.
APP_DOMAIN_TO_CANONICAL = {
    "FM/Budget": "PSM_FM", "PS/Projects": "PS", "Travel": "Travel",
    "HR Workflow": "HR_Workflows", "HR": "HCM",
    "CMT/Vendor": "BusinessPartner", "CMT/Master Data": "BusinessPartner",
    "Procurement": "Procurement_P2P", "FI/Finance": "FI",
    "Banking/Validation": "Payment_BCM", "Mouv/Asset Mgmt": "PM",
    "UBO Field Office": "Treasury_EBS", "Dashboards": "Output",
    "SISTER": "Integration", "UNESDIR": "Integration", "IDoc": "Integration",
    "RFC Utils": "Integration", "Data Extraction": "Integration",
    "SLD/Monitoring": "Basis_Security", "Basis/Tools": "Basis_Security",
}


@lru_cache(maxsize=1)
def _custom_fm_domain(db_path=None):
    """custom function module -> canonical domain, via the curated APP_DOMAIN overlay."""
    path = db_path or str(GOLD)
    if not Path(path).exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        if not con.execute("SELECT name FROM sqlite_master WHERE name='tfdir_custom'").fetchone():
            con.close()
            return {}
        rows = con.execute("SELECT FUNCNAME, APP_DOMAIN FROM tfdir_custom "
                           "WHERE APP_DOMAIN IS NOT NULL AND APP_DOMAIN <> ''").fetchall()
        con.close()
        return {fn.strip(): APP_DOMAIN_TO_CANONICAL.get(ad.strip())
                for fn, ad in rows if APP_DOMAIN_TO_CANONICAL.get(ad.strip())}
    except sqlite3.Error:
        return {}


def package_of_object(name, db_path=None):
    """Package for an object of any kind, including function modules."""
    return _fm_package(db_path).get(name)


def domain_of_function_module(funcname, db_path=None):
    """FM -> domain. Standard taxonomy first, curated custom overlay second.

    The order matters: SAP's own answer wins where it exists, and the curated overlay
    covers exactly what SAP cannot answer — the customer's Z/Y namespace, which is where
    the differentiating processes live.
    """
    dc = _fm_package(db_path).get(funcname)
    d = domain_of_package(dc, db_path) if dc else None
    return d or _custom_fm_domain(db_path).get(funcname)


def domain_of_package(devclass, db_path=None):
    """DEVCLASS -> canonical domain, through SAP's own taxonomy. None when unresolvable."""
    if not devclass:
        return None
    comp = _package_component(db_path).get(devclass)
    dom, _ = component_to_domain(comp)
    return dom


def component_of_package(devclass, db_path=None):
    return _package_component(db_path).get(devclass)


if __name__ == "__main__":
    m = _package_component()
    print(f"{len(m):,} packages resolve to an application component")
    for pkg in ["FBZ", "ME", "MB", "PBAS", "PTRA", "AA", "IEQM", "VA", "CN_PSP_OPR",
                "KACC_ERP50", "RE_CN_CN", "FTA", "FTE", "FTBB", "PAOC_FPM_COM_ENGINE",
                "FMBPA_E"]:
        comp = m.get(pkg)
        dom, pref = component_to_domain(comp)
        print(f"  {pkg:22s} {str(comp):22s} -> {dom} (via {pref})")
