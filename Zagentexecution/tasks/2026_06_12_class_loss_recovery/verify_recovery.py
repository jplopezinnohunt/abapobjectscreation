"""
verify_recovery.py — READ-ONLY. Verify the 3 damaged classes against the TS2 baseline.

Run NOW  -> shows TS2 baseline (target) vs D01 (currently broken).
Run AFTER the Transport of Copies import -> D01 should match TS2 = recovered.

NO writes. TS2 reached via gateway :3300 (its gateway is not on :4800 like D01/V01).
"""
import sys, json, datetime
from pyrfc import Connection

RECOVER = [
    "YCL_FI_ACCOUNT_SUBST_BL",
    "YCL_FI_ACCOUNT_SUBST_READ",
    "YCL_FI_BANK_RECONCILIATION_BL",
]

def opts(w):
    L, cur = [], ""
    for t in w.split(" AND "):
        p = (cur + " AND " + t) if cur else t
        if len(p) <= 72:
            cur = p
        else:
            if cur: L.append(cur + " AND")
            cur = t
    if cur: L.append(cur)
    return [{"TEXT": x} for x in L]

def conn_d01():
    return Connection(ashost="172.16.4.66", sysnr="00", client="350",
                      user="jp_lopez", snc_mode="1",
                      snc_partnername="p:CN=D01", snc_qop="9", lang="EN")

def conn_ts2():
    # TS2 gateway is on :3300 (not :4800). Force gwserv.
    return Connection(ashost="172.16.4.82", sysnr="00", client="350",
                      user="jp_lopez", gwhost="172.16.4.82", gwserv="3300",
                      snc_mode="1", snc_partnername="p:CN=TS2", snc_qop="9", lang="EN")

def rt(c, t, f, w, rc=0):
    r = c.call("RFC_READ_TABLE", QUERY_TABLE=t, DELIMITER="|",
               FIELDS=[{"FIELDNAME": x} for x in f], OPTIONS=opts(w), ROWCOUNT=rc)
    return [d["WA"].split("|") for d in r["DATA"]]

def class_state(c, cls):
    td = rt(c, "TADIR", ["DEVCLASS"],
            f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME = '{cls}'", 1)
    sc = rt(c, "SEOCLASS", ["CLSNAME"], f"CLSNAME = '{cls}'", 1)
    cp = rt(c, "SEOCOMPO", ["CMPNAME"], f"CLSNAME = '{cls}'")
    comps = sorted(r[0].strip() for r in cp)
    return {"tadir": bool(td), "seoclass": bool(sc),
            "n_comp": len(comps), "components": comps}

def main():
    ts2, d01 = conn_ts2(), conn_d01()
    print("=" * 64)
    print("RECOVERY VERIFY — TS2 baseline (target) vs D01 (current)")
    print(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 64)
    out = []
    all_ok = True
    for cls in RECOVER:
        b = class_state(ts2, cls)     # TS2 = target
        d = class_state(d01, cls)     # D01 = current
        recovered = (d["seoclass"] and d["n_comp"] == b["n_comp"]
                     and d["components"] == b["components"])
        status = "RECOVERED [OK]" if recovered else "STILL BROKEN [X]"
        if not recovered:
            all_ok = False
        print(f"\n{cls}")
        print(f"  TS2 (target): seoclass={b['seoclass']} comp={b['n_comp']}")
        print(f"  D01 (now):    seoclass={d['seoclass']} comp={d['n_comp']}  -> {status}")
        miss = sorted(set(b["components"]) - set(d["components"]))
        if miss:
            print(f"  missing in D01: {len(miss)} -> {miss[:8]}{'...' if len(miss)>8 else ''}")
        out.append({"class": cls, "ts2": b, "d01": d, "recovered": recovered})
    ts2.close(); d01.close()
    json.dump(out, open("verify_recovery_result.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("\n" + ("ALL 3 RECOVERED" if all_ok else "NOT YET RECOVERED (run again after import)"))
    print("wrote verify_recovery_result.json")

if __name__ == "__main__":
    main()
