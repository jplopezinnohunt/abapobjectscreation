"""Extract DMEE_TREE_NODE for tree CGI_XML_CT_V9 (SAP-std reference) Dbtr/PstlAdr children.
Goal: read what SOURCE field SAP itself uses for Dbtr StrtNm/BldgNb/PstCd/TwnNm/Ctry in V9.
If V9 ships paying-co bindings out of the box, we copy them. No BAdI extension needed.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
prefix = "SAP_D01_"
def env(k, d=None): return os.getenv(prefix+k) or os.getenv("SAP_"+k) or d

params = dict(ashost=env("ASHOST"), sysnr=env("SYSNR"), client=env("CLIENT"),
              user=env("USER"), lang=env("LANG","EN"))
pw = env("PASSWD") or env("PASSWORD")
if pw: params["passwd"]=pw
if env("SNC_MODE")=="1":
    params["snc_mode"]="1"; params["snc_partnername"]=env("SNC_PARTNERNAME")
    params["snc_qop"]=env("SNC_QOP","9")

conn = Connection(**params)

TREE = "CGI_XML_CT_V9"

# Read all DMEE_TREE_NODE rows for this tree
fields = ["TREE_TYPE","TREE_ID","NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
          "MP_SC_TAB","MP_SC_FLD","MP_SC_OFFSET","LENGTH","CV_RULE",
          "MP_EXIT_FUNC","VERSION","BROTHER_ID","FIRSTCHILD_ID","REF_NAME"]

result = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="DMEE_TREE_NODE",
    OPTIONS=[{"TEXT": f"TREE_ID = '{TREE}'"}],
    FIELDS=[{"FIELDNAME": f} for f in fields],
    DELIMITER="|", ROWCOUNT=2000)

rows = result.get("DATA", [])
print(f"V9 nodes: {len(rows)}")

if not rows:
    # Try without TREE_ID filter, or check P01 instead
    print("No rows in D01. Checking what trees exist...")
    r2 = conn.call("RFC_READ_TABLE",
        QUERY_TABLE="DMEE_TREE",
        OPTIONS=[{"TEXT": "TREE_ID LIKE '%V9%' OR TREE_ID LIKE '%v9%'"}],
        FIELDS=[{"FIELDNAME":"TREE_ID"},{"FIELDNAME":"TREE_TYPE"}],
        DELIMITER="|", ROWCOUNT=50)
    print("V9-ish trees:", [d.get("WA","") for d in r2.get("DATA",[])])
    sys.exit(0)

# Build dict
by_id = {}
for d in rows:
    parts = d["WA"].split("|")
    rec = dict(zip(fields, [p.strip() for p in parts]))
    by_id[rec["NODE_ID"]] = rec

# Find Dbtr ancestor
def tech(rec): return rec.get("TECH_NAME","")
dbtr_ids = [n for n,r in by_id.items() if tech(r)=="Dbtr"]
print(f"Dbtr nodes: {dbtr_ids}")

# For each Dbtr, walk descendants
def walk(nid, depth=0, max_depth=8):
    if depth > max_depth: return
    if nid not in by_id: return
    r = by_id[nid]
    print(f"{'  '*depth}{nid} [{r['NODE_TYPE']}] {tech(r):20s} TAB/FLD={r['MP_SC_TAB']}/{r['MP_SC_FLD']}  EXIT={r['MP_EXIT_FUNC']}  LEN={r['LENGTH']}  CV={r['CV_RULE']}")
    # children: traverse all that have PARENT_ID = nid
    for cid, cr in by_id.items():
        if cr.get("PARENT_ID") == nid:
            walk(cid, depth+1, max_depth)

for d in dbtr_ids:
    print(f"\n=== Dbtr subtree {d} ===")
    walk(d)

# Save full tree CSV
out = os.path.join(os.path.dirname(__file__), "..", "output", "dmee_v9_tree_d01.csv")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(fields)
    for d in rows:
        w.writerow([p.strip() for p in d["WA"].split("|")])
print(f"\nFull V9 tree saved: {out}")
