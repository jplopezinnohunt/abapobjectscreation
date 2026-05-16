"""RFC refresh: current /SEPA_CT_UNES V001 Dbtr/PstlAdr state in D01.
Pull both DMEE_TREE_NODE + DMEE_TREE_COND for accurate post-V9-copy state.
"""
import os, sys, csv
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

prefix = "SAP_D01_"
def env(k, d=None):
    return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d

params = dict(
    ashost=env("ASHOST"),
    sysnr=env("SYSNR"),
    client=env("CLIENT"),
    user=env("USER"),
    lang=env("LANG", "EN"),
)
pw = env("PASSWD") or env("PASSWORD")
if pw:
    params["passwd"] = pw
if env("SNC_MODE") == "1":
    params["snc_mode"] = "1"
    params["snc_partnername"] = env("SNC_PARTNERNAME")
    params["snc_qop"] = env("SNC_QOP", "9")

print(f"Connecting to D01 ashost={params.get('ashost')} sysnr={params.get('sysnr')} client={params.get('client')} user={params.get('user')} pw={'YES' if pw else 'NO'}")

conn = Connection(**params)
print("Connected.")

NODE_FIELDS = ["TREE_ID","NODE_ID","PARENT_ID","TECH_NAME","NODE_TYPE",
               "MP_SC_TAB","MP_SC_FLD","MP_SC_OFFSET","LENGTH","CV_RULE",
               "MP_EXIT_FUNC","MP_CONST","VERSION","BROTHER_ID","FIRSTCHILD_ID",
               "REF_NAME","MP_SELECTION","DATA_TYPE"]

# 1) Fetch /SEPA_CT_UNES V001 nodes
r = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="DMEE_TREE_NODE",
    OPTIONS=[{"TEXT":"TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001'"}],
    FIELDS=[{"FIELDNAME":f} for f in NODE_FIELDS],
    DELIMITER="|", ROWCOUNT=2000)

nodes = {}
for d in r.get("DATA", []):
    rec = dict(zip(NODE_FIELDS, [p.strip() for p in d["WA"].split("|")]))
    nodes[rec["NODE_ID"]] = rec
print(f"\nTotal /SEPA_CT_UNES V001 nodes: {len(nodes)}")

# 2) Locate Dbtr/PstlAdr
dbtr_ids = [n for n,r in nodes.items() if r.get("TECH_NAME")=="Dbtr"]
print(f"Dbtr nodes: {dbtr_ids}")

for d in dbtr_ids:
    pst = [n for n,r in nodes.items() if r.get("PARENT_ID")==d and r.get("TECH_NAME")=="PstlAdr" and r.get("NODE_TYPE")=="ELEM"]
    for p in pst:
        kids = [(n,r) for n,r in nodes.items() if r.get("PARENT_ID")==p]
        print(f"\n=== Dbtr {d} -> PstlAdr {p} -> {len(kids)} children ===")
        for n,rec in sorted(kids, key=lambda x: x[1].get("TECH_NAME","")):
            print(f"  {rec['TECH_NAME']:25s} NODE={n} TYPE={rec['NODE_TYPE']:4s} TAB/FLD={rec['MP_SC_TAB']:8s}/{rec['MP_SC_FLD']:10s} EXIT={rec['MP_EXIT_FUNC']:30s} LEN={rec['LENGTH']} CV='{rec['CV_RULE']}' MAPSEL={rec['MP_SELECTION']} CONST='{rec['MP_CONST']}'")

# 3) Fetch CONDITIONS for Dbtr/PstlAdr children
print("\n=== CONDITIONS for Dbtr/PstlAdr children (DMEE_TREE_COND) ===")
COND_FIELDS = ["TREE_ID","NODE_ID","COND_NUM","ARG1_TAB","ARG1_FLD","COMP_OP","ARG2_TAB","ARG2_FLD","ARG2_VAL","LINK_OP","VERSION"]
all_pst_kids = []
for d in dbtr_ids:
    pst = [n for n,r in nodes.items() if r.get("PARENT_ID")==d and r.get("TECH_NAME")=="PstlAdr" and r.get("NODE_TYPE")=="ELEM"]
    for p in pst:
        all_pst_kids.extend([n for n,r in nodes.items() if r.get("PARENT_ID")==p])

for nid in all_pst_kids:
    rc = conn.call("RFC_READ_TABLE",
        QUERY_TABLE="DMEE_TREE_COND",
        OPTIONS=[{"TEXT":f"TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001' AND NODE_ID = '{nid}'"}],
        FIELDS=[{"FIELDNAME":f} for f in COND_FIELDS],
        DELIMITER="|", ROWCOUNT=10)
    rows = rc.get("DATA", [])
    if rows:
        for d in rows:
            rec = dict(zip(COND_FIELDS, [p.strip() for p in d["WA"].split("|")]))
            tn = nodes[nid].get("TECH_NAME","?")
            arg2 = rec['ARG2_TAB'] + '-' + rec['ARG2_FLD'] if rec['ARG2_TAB'] else repr(rec['ARG2_VAL'])
            print(f"  {tn:15s} {nid} cond#{rec['COND_NUM']}: {rec['ARG1_TAB']}-{rec['ARG1_FLD']} {rec['COMP_OP']} {arg2}")
    else:
        tn = nodes[nid].get("TECH_NAME","?")
        print(f"  {tn:15s} {nid}: NO CONDITIONS")

# 4) Save full Dbtr/PstlAdr extract for reference
out = os.path.join(os.path.dirname(__file__), "..", "output", "sepa_v001_dbtr_pstladr_d01_REFRESH.csv")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(NODE_FIELDS)
    for nid in all_pst_kids:
        w.writerow([nodes[nid].get(k,"") for k in NODE_FIELDS])
print(f"\nSaved fresh extract: {out}")
