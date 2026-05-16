"""
Compare CGI standard tree (CGI_XML_CT_UNESCO) vs UNESCO V001 (SEPA_CT_UNES)
for Dbtr/Cdtr nodes — show which exit function each one uses.
Also identify BAdI methods (GET_CREDIT/GET_DEBIT/...) and compare logic.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

# --- 1. Extract CGI_XML_CT_UNESCO tree (standard CGI baseline)
print("=== Extract CGI_XML_CT_UNESCO V000 from D01 ===")
cgi_rows = rfc_read_paginated(c, "DMEE_TREE_NODE",
    fields=["NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
            "MP_SC_TAB","MP_SC_FLD","MP_EXIT_FUNC","MP_CONST"],
    where="TREE_ID = '/CGI_XML_CT_UNESCO' AND VERSION = '000'",
    batch_size=200, throttle=0.0)
print(f"  CGI standard: {len(cgi_rows)} nodes")
if not cgi_rows:
    # try another tree id form
    for trid in ("CGI_XML_CT_UNESCO", "CGI_XML_CT", "CGI_XML_CT_UNESCO_1",
                 "/CGI_XML_CT_UNESCO_1"):
        rows = rfc_read_paginated(c, "DMEE_TREE_NODE",
            fields=["NODE_ID","TECH_NAME","MP_EXIT_FUNC"],
            where=f"TREE_ID = '{trid}'",
            batch_size=10, throttle=0.0)
        print(f"  probe TREE_ID='{trid}': {len(rows)} nodes")
        if rows:
            cgi_rows = rfc_read_paginated(c, "DMEE_TREE_NODE",
                fields=["NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
                        "MP_SC_TAB","MP_SC_FLD","MP_EXIT_FUNC","MP_CONST"],
                where=f"TREE_ID = '{trid}'",
                batch_size=200, throttle=0.0)
            break

# Build path lookup
def build_xpath(rows):
    by_id = {r["NODE_ID"]: r for r in rows}
    def xp(nid, _seen=None):
        if _seen is None: _seen=set()
        if nid in _seen or nid not in by_id: return ""
        _seen.add(nid)
        n = by_id[nid]
        p = n.get("PARENT_ID","").strip()
        t = (n.get("TECH_NAME") or "").strip()
        if p and p in by_id and p != nid:
            return f"{xp(p,_seen)}/{t}" if t else xp(p,_seen)
        return f"/{t}" if t else ""
    return {r["NODE_ID"]: xp(r["NODE_ID"]) for r in rows}

cgi_paths = build_xpath(cgi_rows)

# --- 2. Read UNESCO V001 SEPA from CSV we already have
print("\n=== Read UNESCO V001 SEPA_CT_UNES from local CSV ===")
sepa_rows = []
csv_path = os.path.join(os.path.dirname(__file__), "..", "..",
    "knowledge/domains/Payment/phase0/dmee_full",
    "dmee_tree_node_d01_sepa_v001_fresh.csv")
with open(csv_path, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        sepa_rows.append(r)
print(f"  SEPA V001 UNESCO: {len(sepa_rows)} nodes")
sepa_paths = build_xpath(sepa_rows)

# --- 3. Build merged comparison: by TECH_NAME, only Dbtr-related leaves
def is_dbtr_leaf(xp): return "/Dbtr/" in xp and not "/DbtrAgt" in xp and not "/DbtrAcct" in xp
def is_cdtr_leaf(xp): return "/Cdtr/" in xp and not "/CdtrAgt" in xp and not "/CdtrAcct" in xp

def collect(rows, paths, predicate):
    out = []
    for r in rows:
        xp = paths.get(r["NODE_ID"],"")
        if not predicate(xp): continue
        if r.get("NODE_TYPE") not in ("ELEM",): continue
        out.append({
            "tech": (r.get("TECH_NAME") or "").strip(),
            "xp": xp,
            "src": f"{(r.get('MP_SC_TAB') or '').strip()}-{(r.get('MP_SC_FLD') or '').strip()}".strip("-"),
            "exit": (r.get("MP_EXIT_FUNC") or "").strip(),
            "const": (r.get("MP_CONST") or "").strip(),
        })
    return out

cgi_dbtr = collect(cgi_rows, cgi_paths, is_dbtr_leaf)
cgi_cdtr = collect(cgi_rows, cgi_paths, is_cdtr_leaf)
sepa_dbtr = collect(sepa_rows, sepa_paths, is_dbtr_leaf)
sepa_cdtr = collect(sepa_rows, sepa_paths, is_cdtr_leaf)

# --- 4. Print comparison tables
def print_table(title, cgi_list, sepa_list):
    print(f"\n## {title}\n")
    # Build by tech_name + xpath suffix
    def key(r): return (r["xp"].split("/")[-2:][0] if "/" in r["xp"] else "")+"/"+r["tech"]
    cgi_map = {key(r): r for r in cgi_list}
    sepa_map = {key(r): r for r in sepa_list}
    all_keys = sorted(set(cgi_map.keys()) | set(sepa_map.keys()))
    print(f"  {'Tech':<20} {'CGI src':<25} {'CGI exit':<32} {'V001 src':<25} {'V001 exit':<32}")
    print(f"  {'-'*20} {'-'*25} {'-'*32} {'-'*25} {'-'*32}")
    for k in all_keys:
        cgi = cgi_map.get(k, {})
        sepa = sepa_map.get(k, {})
        cs = cgi.get("src","-") or "-"
        ce = cgi.get("exit","-") or "-"
        ss = sepa.get("src","-") or "-"
        se = sepa.get("exit","-") or "-"
        # mark difference
        diff = " [DIFF]" if (ce != se or cs != ss) else ""
        print(f"  {k[:20]:<20} {cs[:25]:<25} {ce[:32]:<32} {ss[:25]:<25} {se[:32]:<32}{diff}")

print_table("Dbtr leaves — CGI standard vs UNESCO V001", cgi_dbtr, sepa_dbtr)

# --- 5. Look for GET_DEBIT in BAdI class
print("\n=== Search BAdI methods (CCDEF/CCIMP/CMxxx files) for GET_DEBIT ===")
import glob
search_dir = os.path.join(os.path.dirname(__file__), "..", "..",
                         "extracted_code/FI/DMEE_p01_canonical")
for f in sorted(glob.glob(os.path.join(search_dir, "YCL_IDFI_CGI_DMEE_FALLBACK*"))):
    sz = os.path.getsize(f)
    print(f"  {sz:>6}  {os.path.basename(f)}")
