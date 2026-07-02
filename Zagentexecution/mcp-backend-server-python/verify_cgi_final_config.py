"""Verify final CGI /CGI_XML_CT_UNESCO config after user edits — dump party PstlAdr subtrees, all versions, flag AdrLine."""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard

TREE = "/CGI_XML_CT_UNESCO"
F = ["TREE_ID","VERSION","NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE","MP_SC_TAB","MP_SC_FLD","MP_SC_OFFSET","LENGTH","MP_EXIT_FUNC"]
g = ConnectionGuard("D01"); g.connect()
r = g.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE", DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in F],
    OPTIONS=[{"TEXT": f"TREE_ID = '{TREE}'"}], ROWCOUNT=8000)
allrows = [dict(zip(F,[v.strip() for v in x["WA"].split("|")])) for x in r.get("DATA",[])]
g.close()

versions = sorted({x["VERSION"] for x in allrows})
print(f"CGI {TREE}: versions present = {versions}, total nodes = {len(allrows)}")

for ver in versions:
    t = [x for x in allrows if x["VERSION"] == ver]
    by_id = {x["NODE_ID"]: x for x in t}
    kids = {}
    for x in t: kids.setdefault(x["PARENT_ID"], []).append(x)
    def path(nid):
        p=[];cur=nid
        while cur in by_id and len(p)<20: p.append(by_id[cur]['TECH_NAME']); cur=by_id[cur]['PARENT_ID']
        return '/'.join(reversed(p))
    print(f"\n########## VERSION {ver} — {len(t)} nodes ##########")
    for party in ["Dbtr","UltmtDbtr","Cdtr","UltmtCdtr","CdtrAgt"]:
        for pr in [x for x in t if x["TECH_NAME"]==party and x["NODE_TYPE"]=="ELEM"]:
            # find PstlAdr descendant(s)
            stack=[pr["NODE_ID"]]; pstls=[]
            while stack:
                n=stack.pop()
                for c in kids.get(n,[]):
                    if c["TECH_NAME"]=="PstlAdr": pstls.append(c["NODE_ID"])
                    stack.append(c["NODE_ID"])
            if not pstls:
                print(f"  {party} ({pr['NODE_ID']}, {path(pr['NODE_ID'])}): no PstlAdr")
                continue
            for pstl in pstls:
                ch=kids.get(pstl,[])
                tags=[c['TECH_NAME'] for c in ch]
                adrl=[c['NODE_ID'] for c in ch if c['TECH_NAME']=='AdrLine']
                print(f"  {party} [{path(pr['NODE_ID'])}] PstlAdr={pstl}: {len(ch)} hijos | AdrLine={'YES '+str(adrl) if adrl else 'none'}")
                print(f"      tags: {tags}")
