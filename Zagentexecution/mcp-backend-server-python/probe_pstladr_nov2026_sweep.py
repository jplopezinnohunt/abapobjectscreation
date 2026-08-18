# -*- coding: utf-8 -*-
"""Post-Nov-2026 readiness sweep: EVERY PstlAdr in a DMEE tree, classified.

The Nov-2026 rules (claim 499, SocGen brochure 3.3.5.1 + the guide the bank's
validator quotes):
  STRUCTURED   = structured tags, NO AdrLine .................. target state
  HYBRID       = structured + AdrLine, no repetition .......... allowed
  UNSTRUCTURED = AdrLine + Ctry only .......................... PROHIBITED
  and in every case: if PstlAdr is emitted, TwnNm AND Ctry are mandatory.
Order is xs:sequence and is checked separately -- a node can be compliant on
content and still be rejected on order (that is what happened on 2026-07-21).

READ-ONLY. Indexes PER VERSION: NODE_IDs repeat across versions and a single
index silently walks a cross-version chimera.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rfc_helpers import get_connection

ISO = ["AdrTp","Dept","SubDept","StrtNm","BldgNb","PstCd","TwnNm","CtrySubDvsn","Ctry","AdrLine"]
STRUCT = {"Dept","SubDept","StrtNm","BldgNb","PstCd","TwnNm","CtrySubDvsn"}
F1 = ["TREE_ID","VERSION","NODE_ID","PARENT_ID","BROTHER_ID","FIRSTCHILD_ID"]
F2 = ["TECH_NAME","MP_SC_TAB","MP_SC_FLD","EX_STATUS"]

def sweep(sysid, tree_id, version):
    c = get_connection(sysid)
    def rd(f):
        r = c.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE", DELIMITER="|",
                   FIELDS=[{"FIELDNAME": x} for x in f], ROWCOUNT=0)
        return [d["WA"].split("|") for d in r["DATA"]]
    recs = [dict(zip(F1+F2, [v.strip() for v in a+b])) for a, b in zip(rd(F1), rd(F2))]
    c.close()
    src = {r["NODE_ID"]: r for r in recs
           if r["TREE_ID"] == tree_id and r["VERSION"] == version}
    if not src:
        print(f"  {sysid} {tree_id} V{version}: NOT PRESENT"); return []
    def path(n):
        o, cur, i = [], src.get(n), 0
        while cur and i < 25:
            o.append(cur["TECH_NAME"]); cur = src.get(cur["PARENT_ID"]); i += 1
        return list(reversed(o))
    def owner(n):
        p = path(n)
        for x in reversed(p[:-1]):
            if x not in ("PstlAdr","FinInstnId","BrnchId"):
                return x
        return "?"
    out = []
    for t in src.values():
        if t["TECH_NAME"] != "PstlAdr":
            continue
        kids, cur = [], src.get(t["FIRSTCHILD_ID"])
        while cur:
            kids.append(cur); cur = src.get(cur["BROTHER_ID"])
        names = [k["TECH_NAME"] for k in kids]
        seq = [n for n in names if n in ISO]
        idx = [ISO.index(n) for n in seq]
        order_ok = idx == sorted(idx)
        has_struct = bool(set(names) & STRUCT)
        has_adr = "AdrLine" in names
        has_twn, has_ctry = "TwnNm" in names, "Ctry" in names
        if has_struct and not has_adr:   kind = "STRUCTURED"
        elif has_struct and has_adr:     kind = "HYBRID"
        elif has_adr:                    kind = "UNSTRUCTURED"
        else:                            kind = "Ctry-only" if has_ctry else "EMPTY"
        bad = []
        if not order_ok:              bad.append("ORDER")
        if kind == "UNSTRUCTURED":    bad.append("PROHIBITED-2026")
        if not has_twn:               bad.append("no TwnNm")
        if not has_ctry:              bad.append("no Ctry")
        out.append((owner(t["NODE_ID"]), t["NODE_ID"], kind, names, bad))
    return out

TARGETS = [("D01","/CGI_XML_CT_UNESCO","001"), ("D01","/CGI_XML_CT_UNESCO","000")]
if len(sys.argv) > 1:
    TARGETS = [tuple(a.split(",")) for a in sys.argv[1:]]
for sysid, tree, ver in TARGETS:
    print("=" * 94)
    print(f"{sysid}  {tree}  V{ver}")
    print("=" * 94)
    rows = sweep(sysid, tree, ver)
    okc = 0
    for who, nid, kind, names, bad in sorted(rows):
        flag = "OK " if not bad else "!! "
        okc += 0 if bad else 1
        print(f" {flag}{who:<13}{nid:<15}{kind:<13}{','.join(names)[:58]}")
        if bad:
            print(f"      -> {' + '.join(bad)}")
    print(f"\n  {len(rows)} PstlAdr | conformes post-Nov-2026: {okc} | a corregir: {len(rows)-okc}\n")
