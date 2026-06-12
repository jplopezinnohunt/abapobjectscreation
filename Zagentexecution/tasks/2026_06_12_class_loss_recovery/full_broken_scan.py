"""
full_broken_scan.py — READ-ONLY. DEFINITIVE list of ALL broken custom classes in D01.

No classification, no dropping. Every broken Z*/Y* class listed with its recoverability.

BROKEN signals (either one):
  A. ORPHAN  : TADIR R3TR CLAS exists in D01 but no SEOCLASS row.
  B. REGRESS : D01 has SEOCLASS but 0 components, yet V01 has it healthy (comp>0).

For each broken class: where it can be recovered from (V01 / TS2 / D01 own version history).
"""
import json
from pyrfc import Connection

def opts(w):
    L, cur = [], ""
    for t in w.split(" AND "):
        p = (cur + " AND " + t) if cur else t
        if len(p) <= 72: cur = p
        else:
            if cur: L.append(cur + " AND")
            cur = t
    if cur: L.append(cur)
    return [{"TEXT": x} for x in L]

def conn(s):
    if s == "D01": return Connection(ashost="172.16.4.66", sysnr="00", client="350", user="jp_lopez", snc_mode="1", snc_partnername="p:CN=D01", snc_qop="9", lang="EN")
    if s == "V01": return Connection(ashost="hq-sap-v01", sysnr="00", client="350", user="jp_lopez", snc_mode="1", snc_partnername="p:CN=V01", snc_qop="9", lang="EN")
    if s == "TS2": return Connection(ashost="172.16.4.82", sysnr="00", client="350", user="jp_lopez", gwhost="172.16.4.82", gwserv="3300", snc_mode="1", snc_partnername="p:CN=TS2", snc_qop="9", lang="EN")

def rt(c, t, f, w, rc=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=t, DELIMITER="|",
               FIELDS=[{"FIELDNAME": x} for x in f], OPTIONS=opts(w), ROWCOUNT=rc)
    return [d["WA"].split("|") for d in r["DATA"]]

def health_sets(c):
    """Return (seoclass_set, has_components_set) for Y*/Z* on connection c."""
    seo, comp = set(), set()
    for ns in ("Y%", "Z%"):
        for r in rt(c, "SEOCLASS", ["CLSNAME"], f"CLSNAME LIKE '{ns}'"):
            seo.add(r[0].strip())
        for r in rt(c, "SEOCOMPO", ["CLSNAME"], f"CLSNAME LIKE '{ns}'"):
            comp.add(r[0].strip())
    return seo, comp

def main():
    print("Loading D01 / V01 / TS2 class health (bulk) ...")
    d01, v01, ts2 = conn("D01"), conn("V01"), conn("TS2")

    # D01 TADIR CLAS + author/pkg
    d01_tadir = {}
    for ns in ("Y%", "Z%"):
        for r in rt(d01, "TADIR", ["OBJ_NAME", "DEVCLASS", "AUTHOR"],
                    f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME LIKE '{ns}'"):
            d01_tadir[r[0].strip()] = (r[1].strip(), r[2].strip())
    d01_seo, d01_comp = health_sets(d01)
    v01_seo, v01_comp = health_sets(v01)
    ts2_seo, ts2_comp = health_sets(ts2)

    v01_healthy = v01_seo & v01_comp
    ts2_healthy = ts2_seo & ts2_comp

    # BROKEN set
    orphans = {n for n in d01_tadir if n not in d01_seo}          # A
    empties = {n for n in (d01_seo - d01_comp) if n in v01_healthy}  # B (only if V01 has it healthy)
    broken = sorted(orphans | empties)
    print(f"D01 TADIR CLAS: {len(d01_tadir)} | orphans(A): {len(orphans)} | "
          f"regress-empties(B): {len(empties)} | TOTAL BROKEN: {len(broken)}\n")

    rows = []
    for n in broken:
        pkg, auth = d01_tadir.get(n, ("?", "?"))
        # ALL VRSD versions (incl. 00000 transport snapshots = retrievable from version mgmt)
        vrsd = rt(d01, "VRSD", ["OBJTYPE", "VERSNO", "AUTHOR", "DATUM"], f"OBJNAME = '{n}'")
        vers = sorted({r[1].strip() for r in vrsd})
        last = max(((r[3].strip(), r[2].strip()) for r in vrsd), default=("", ""))
        rec = []
        if n in v01_healthy: rec.append("V01")
        if n in ts2_healthy: rec.append("TS2")
        if vers: rec.append(f"D01-vmgmt({len(vers)}v,last {last[0]}/{last[1]})")
        kind = "ORPHAN" if n in orphans else "REGRESS"
        rows.append({"class": n, "kind": kind, "package": pkg, "author": auth,
                     "vrsd_versions": vers, "recover_from": rec or ["NONE"]})
        print(f"  {kind:8s} {n:42s} pkg={pkg:13s} auth={auth:10s} "
              f"-> {' | '.join(rec) if rec else 'NONE (no source found)'}")
    d01.close(); v01.close(); ts2.close()

    json.dump(rows, open("full_broken_scan_result.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    nrec = sum(1 for r in rows if r["recover_from"] != ["NONE — gone everywhere"])
    print(f"\nTOTAL broken: {len(rows)} | recoverable somewhere: {nrec} | "
          f"gone everywhere: {len(rows)-nrec}")
    print("wrote full_broken_scan_result.json")

if __name__ == "__main__":
    main()
