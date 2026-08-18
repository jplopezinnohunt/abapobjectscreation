# -*- coding: utf-8 -*-
"""D01 /CGI_XML_CT_UNESCO: full V000 (active) vs V001 (maintenance) diff.

Version model, claim #314: V000 = ACTIVE/productive, V001 = MAINTENANCE/working
(edited by the operator, does not reach F110 until activated -- activation makes
V001 OVERWRITE V000), V002+ = backup snapshot via Generate Version.

Operator reports V001 may have been copied wholesale from elsewhere. This shows
exactly what differs, so the blast radius of activating V001 is known BEFORE it
overwrites production config. READ-ONLY.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rfc_helpers import get_connection

TREE = "/CGI_XML_CT_UNESCO"
SYS = sys.argv[1] if len(sys.argv) > 1 else "D01"
# 48 columns is too wide for one RFC_READ_TABLE call (512-byte line buffer);
# these are the ones that decide what the engine emits.
F1 = ["TREE_ID", "VERSION", "NODE_ID", "PARENT_ID", "BROTHER_ID", "FIRSTCHILD_ID"]
# Field names verified via DDIF_FIELDINFO_GET, not guessed: it is LENGTH (not
# MP_LENGTH) and LEV (not LEVEL). An invalid field makes RFC_READ_TABLE raise
# AD718 TABLE_WITHOUT_DATA -- which reads like "empty table", not "bad field".
F2 = ["TECH_NAME", "NODE_TYPE", "MP_SC_TAB", "MP_SC_FLD", "MP_OFFSET", "LENGTH"]
F3 = ["MP_EXIT_FUNC", "CV_RULE", "MP_CONST", "MP_IF_TP", "REF_NAME", "LEV"]
F4 = ["EX_STATUS", "MP_SELECTION", "CK_EXIT_FUNC", "MP_SC_NODE", "MP_SC_REF_NAME"]

conn = get_connection(SYS)
def read(fields):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE="DMEE_TREE_NODE", DELIMITER="|",
                  FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=0)
    return [d["WA"].split("|") for d in r["DATA"]]
a, b, c, d = read(F1), read(F2), read(F3), read(F4)
FIELDS = F1 + F2 + F3 + F4
recs = [dict(zip(FIELDS, [v.strip() for v in w + x + y + z]))
        for w, x, y, z in zip(a, b, c, d)]
tree = [r for r in recs if r["TREE_ID"] == TREE]
print(f"SYSTEM {SYS}  {TREE}")
vers = sorted({r["VERSION"] for r in tree})
for v in vers:
    print(f"  V{v}: {sum(1 for r in tree if r['VERSION']==v)} nodes")

v0 = {r["NODE_ID"]: r for r in tree if r["VERSION"] == "000"}
v1 = {r["NODE_ID"]: r for r in tree if r["VERSION"] == "001"}
only0, only1 = sorted(set(v0) - set(v1)), sorted(set(v1) - set(v0))
COMPARE = [f for f in FIELDS if f != "VERSION"]
changed = []
for nid in sorted(set(v0) & set(v1)):
    d = [(f, v0[nid][f], v1[nid][f]) for f in COMPARE if v0[nid][f] != v1[nid][f]]
    if d:
        changed.append((nid, v0[nid]["TECH_NAME"], d))

print(f"\n=== V000 vs V001 ===")
print(f"  only in V000 (V001 would DELETE) : {len(only0)}")
print(f"  only in V001 (V001 would ADD)    : {len(only1)}")
print(f"  shared but CHANGED               : {len(changed)}")

def path(nid, src):
    names, cur, i = [], src.get(nid), 0
    while cur and i < 20:
        names.append(cur["TECH_NAME"]); cur = src.get(cur["PARENT_ID"]); i += 1
    return " > ".join(reversed(names))

for nid in only0:
    print(f"\n  [DELETE] {nid} {v0[nid]['TECH_NAME']}")
    print(f"           {path(nid, v0)}")
    print(f"           src={v0[nid]['MP_SC_TAB']}-{v0[nid]['MP_SC_FLD']} "
          f"exit={v0[nid]['MP_EXIT_FUNC']}")
for nid in only1:
    print(f"\n  [ADD]    {nid} {v1[nid]['TECH_NAME']}")
    print(f"           {path(nid, v1)}")
    print(f"           src={v1[nid]['MP_SC_TAB']}-{v1[nid]['MP_SC_FLD']} "
          f"exit={v1[nid]['MP_EXIT_FUNC']}")
for nid, tn, d in changed:
    print(f"\n  [CHANGE] {nid} {tn}   {path(nid, v0)}")
    for f, a_, b_ in d:
        print(f"           {f}: V000={a_!r}  ->  V001={b_!r}")

# the node under review
print("\n=== the node under review: CdtrAgt/FinInstnId/PstlAdr ===")
for label, src in (("V000", v0), ("V001", v1)):
    tgt = [r for r in src.values()
           if r["TECH_NAME"] == "PstlAdr" and "CdtrAgt" in path(r["NODE_ID"], src)]
    for t in tgt:
        kids, cur = [], src.get(t["FIRSTCHILD_ID"])
        while cur:
            kids.append(cur); cur = src.get(cur["BROTHER_ID"])
        print(f"  {label} {t['NODE_ID']}: " + " | ".join(
            f"{k['TECH_NAME']}<-{k['MP_SC_TAB']}-{k['MP_SC_FLD']}"
            if k["MP_SC_TAB"] else k["TECH_NAME"] for k in kids))
conn.close()
