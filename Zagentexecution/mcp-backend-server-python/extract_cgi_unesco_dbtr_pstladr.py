"""Extract /CGI_XML_CT_UNESCO Dbtr/PstlAdr current state from D01 (V000 active + V001 if exists).
Goal: identify gap vs V9 SAP-std reference for structured-address Dbtr leaves.
Output: side-by-side comparison TwnNm/StrtNm/BldgNb/PstCd/Ctry/CtrySubDvsn between V9 and CGI_XML_CT_UNESCO.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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

fields = ["TREE_TYPE","TREE_ID","NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
          "MP_SC_TAB","MP_SC_FLD","MP_SC_OFFSET","LENGTH","CV_RULE",
          "MP_EXIT_FUNC","VERSION","BROTHER_ID","FIRSTCHILD_ID","REF_NAME"]

def fetch_tree(tree_id):
    r = conn.call("RFC_READ_TABLE",
        QUERY_TABLE="DMEE_TREE_NODE",
        OPTIONS=[{"TEXT": f"TREE_ID = '{tree_id}'"}],
        FIELDS=[{"FIELDNAME":f} for f in fields],
        DELIMITER="|", ROWCOUNT=3000)
    nodes = {}
    for d in r.get("DATA", []):
        rec = dict(zip(fields, [p.strip() for p in d["WA"].split("|")]))
        nodes[rec["NODE_ID"]] = rec
    return nodes

trees = {}
for tid in ["/CGI_XML_CT_UNESCO", "CGI_XML_CT_V9"]:
    nodes = fetch_tree(tid)
    print(f"{tid}: {len(nodes)} nodes")
    trees[tid] = nodes

def find_dbtr_pstladr(nodes):
    """Find Dbtr (the one with PstlAdr child) and return its PstlAdr ELEM children dict {tech_name: rec}."""
    dbtr_ids = [n for n,r in nodes.items() if r.get("TECH_NAME")=="Dbtr"]
    for d in dbtr_ids:
        pstladr_kids = [n for n,r in nodes.items() if r.get("PARENT_ID")==d and r.get("TECH_NAME")=="PstlAdr" and r.get("NODE_TYPE")=="ELEM"]
        for p in pstladr_kids:
            children = {}
            for n,r in nodes.items():
                if r.get("PARENT_ID")==p:
                    tn = r.get("TECH_NAME","")
                    children.setdefault(tn, []).append(r)
            return d, p, children
    return None, None, {}

print("\n=== /CGI_XML_CT_UNESCO Dbtr/PstlAdr ===")
dbtr_u, pst_u, kids_u = find_dbtr_pstladr(trees["/CGI_XML_CT_UNESCO"])
print(f"  Dbtr={dbtr_u} PstlAdr={pst_u}")
for tn in sorted(kids_u.keys()):
    for r in kids_u[tn]:
        print(f"  {tn:25s} NODE={r['NODE_ID']} TYPE={r['NODE_TYPE']} TAB/FLD={r['MP_SC_TAB']}/{r['MP_SC_FLD']} EXIT={r['MP_EXIT_FUNC']} LEN={r['LENGTH']} CV={r['CV_RULE']}")

print("\n=== CGI_XML_CT_V9 Dbtr/PstlAdr ===")
dbtr_v, pst_v, kids_v = find_dbtr_pstladr(trees["CGI_XML_CT_V9"])
print(f"  Dbtr={dbtr_v} PstlAdr={pst_v}")
for tn in sorted(kids_v.keys()):
    for r in kids_v[tn]:
        print(f"  {tn:25s} NODE={r['NODE_ID']} TYPE={r['NODE_TYPE']} TAB/FLD={r['MP_SC_TAB']}/{r['MP_SC_FLD']} EXIT={r['MP_EXIT_FUNC']} LEN={r['LENGTH']} CV={r['CV_RULE']}")

print("\n=== DIFF (V9 vs UNESCO Dbtr/PstlAdr) ===")
all_tn = sorted(set(kids_u.keys()) | set(kids_v.keys()))
for tn in all_tn:
    in_u = tn in kids_u
    in_v = tn in kids_v
    u_str = ", ".join(f"{r['MP_SC_TAB']}/{r['MP_SC_FLD']} EXIT={r['MP_EXIT_FUNC']}" for r in kids_u.get(tn,[])) or "MISSING"
    v_str = ", ".join(f"{r['MP_SC_TAB']}/{r['MP_SC_FLD']} EXIT={r['MP_EXIT_FUNC']}" for r in kids_v.get(tn,[])) or "MISSING"
    flag = "OK " if u_str == v_str else "DIFF"
    print(f"  [{flag}] {tn:25s}  UNES={u_str}  | V9={v_str}")

# Save full extracts
out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(out_dir, exist_ok=True)
for tid in trees:
    safe = tid.replace("/","").replace(" ","")
    with open(os.path.join(out_dir, f"dmee_{safe}_d01.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fields)
        for r in trees[tid].values():
            w.writerow([r.get(k,"") for k in fields])
print(f"\nFull tree CSVs saved to {out_dir}")
