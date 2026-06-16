"""
analyze_postimport_2026.py
=========================
Evidence that the 2026 upgrade had real POST-IMPORT activity (answers
"no action post-import?"). Sources: Gold DB tpalog_upgrades (post-import
transports) + P01 TBTCO job log (generation/SGEN + job volume). Read-only.

Note: Gold DB tbtco is stale (to 2026-03-25, pre-upgrade), so the job log for
the June window is pulled live and saved as tbtco_upgrade2026_jobs.
"""
import sys, os, sqlite3, json
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

GOLD = os.path.join(os.path.dirname(__file__), "..",
                    "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
WIN = ("20260607", "20260614")


def hm(t):
    return f"{t[:2]}:{t[2:4]}" if t and len(t) >= 4 else t


def main():
    db = sqlite3.connect(GOLD); db.row_factory = sqlite3.Row
    conn = get_connection("P01")

    # 1. post-import transports (after main import end 06:39) from TPALOG
    post = {}
    for r in db.execute("SELECT TRTIME,TRKORR FROM tpalog_upgrades "
                        "WHERE _win='2026-06' AND TRTIME>'20260607063917' AND TRKORR<>'ALL'"):
        post.setdefault(r["TRKORR"], []).append(r["TRTIME"])
    transports = []
    for tk in sorted(post, key=lambda k: min(post[k])):
        ts = sorted(post[tk])
        d = rfc_read_paginated(conn, "E07T", ["AS4TEXT"], f"TRKORR = '{tk}'",
                               batch_size=5, throttle=0)
        transports.append({"trkorr": tk, "first": ts[0], "last": ts[-1],
                           "steps": len(ts), "desc": d[0]["AS4TEXT"] if d else ""})

    # 2. P01 jobs that started during the upgrade week (incl. generation/SGEN)
    jobs = rfc_read_paginated(conn, "TBTCO",
                              ["JOBNAME", "STATUS", "STRTDATE", "STRTTIME",
                               "ENDDATE", "ENDTIME", "AUTHCKNAM"],
                              [{"TEXT": f"STRTDATE >= '{WIN[0]}'"},
                               {"TEXT": f"AND STRTDATE <= '{WIN[1]}'"}],
                              batch_size=1_000_000, throttle=0)
    conn.close()

    gen = [j for j in jobs if any(k in (j["JOBNAME"] or "").upper()
           for k in ("SGEN", "GENERAT", "RSPARAGENER", "RDDGEN", "LOAD_GEN"))]

    # persist the job slice (P01)
    cols = ["JOBNAME", "STATUS", "STRTDATE", "STRTTIME", "ENDDATE", "ENDTIME", "AUTHCKNAM"]
    db.execute("DROP TABLE IF EXISTS tbtco_upgrade2026_jobs")
    db.execute(f"CREATE TABLE tbtco_upgrade2026_jobs ({','.join(c+' TEXT' for c in cols)})")
    db.executemany(f"INSERT INTO tbtco_upgrade2026_jobs VALUES ({','.join('?'*len(cols))})",
                   [[j.get(c, "") for c in cols] for j in jobs])
    db.commit()

    print(f"=== POST-IMPORT TRANSPORTS (2026, after 06-07 06:39) ===")
    for t in transports:
        print(f"  {t['trkorr']:<14} {t['first'][:8]} {hm(t['first'][8:])}->{hm(t['last'][8:])}  {t['desc']}")
    print(f"\n=== JOBS in upgrade week ({WIN[0]}..{WIN[1]}): {len(jobs):,} ===")
    print(f"  generation/SGEN jobs: {len(gen)}")
    for j in sorted(gen, key=lambda x: (x["STRTDATE"], x["STRTTIME"]))[:10]:
        print(f"    {j['STRTDATE']} {hm(j['STRTTIME'])}->{hm(j['ENDTIME'])} {j['JOBNAME']} [{j['STATUS']}]")
    print("  top jobs that week:")
    for j, n in Counter(x["JOBNAME"] for x in jobs).most_common(10):
        print(f"    {n:>5}  {j}")

    out = os.path.join(os.path.dirname(__file__), "postimport_2026.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"post_import_transports": transports,
                   "jobs_in_week": len(jobs),
                   "generation_jobs": [{"job": j["JOBNAME"], "start": j["STRTDATE"]+j["STRTTIME"],
                                        "end": j["ENDDATE"]+j["ENDTIME"], "status": j["STATUS"]}
                                       for j in gen]}, fh, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {out} + Gold DB tbtco_upgrade2026_jobs ({len(jobs)} rows)")
    db.close()


if __name__ == "__main__":
    main()
