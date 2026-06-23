"""
mine_domain.py — the per-domain process-mining ENGINE (executable, parameterized, reusable).
==============================================================================================
Run process mining for ANY domain (or all) and emit the operating-model FOOTPRINT as DATA:
WHAT executes (tcode/report/RFC-BAPI/job) · WHO (actor: human/integration/batch) · WHEN
(monthly) · VOLUME · is-it-a-hidden-extraction · is-it-an-integration. Reuses the SAME
object→domain classifier as executed_objects_domain_map (one source of truth — the next
session RUNS this, it does not re-derive).

    python process_mining/mine_domain.py            # all domains
    python process_mining/mine_domain.py PSM_FM     # one domain
    python process_mining/mine_domain.py HCM PSM_FM # several

Output: brain_v2/domain_footprints/<DOMAIN>.json  +  _index.json (cross-domain summary).
Inputs (Gold DB, read-only): rsau_audit_history (Transaction/Report/RFC), tbtcp (jobs),
plus the cached tadir_prog/tdevc/d01_tstc maps via executed_objects_domain_map.make_classifier.
"""
import re
import sys
import json
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import executed_objects_domain_map as eom  # noqa: E402  (the shared classifier)

REPO = HERE.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUTDIR = REPO / "brain_v2" / "domain_footprints"

CHANNELS = [  # (label, rsau TXSUBCLSID, name-field, resolve-tcode?)
    ("dialog_tcode", "Transaction Start", "PARAM1", True),
    ("report",       "Report Start",      "SLGREPNA", False),
    ("rfc_bapi",     "RFC Function Call", "PARAM3", False),
]
BATCH_USERS = {"JOBBATCH", "WF-BATCH", "WF_BATCH", "SAPSYS", "BATCHUSER", "DDIC", "TMSADM"}
INTEGRATION_PAT = re.compile(r"MULE|BRIDGE|ORION|SISTER|ALEREMOTE|INTERFAC|RFC|_WS|_SVC|SERVICE|_BOT|UNESDIR|_API|PIAPPL|XIAPPL", re.I)


def actor_type(user):
    u = (user or "").strip().upper()
    if not u:
        return "system"
    if u in BATCH_USERS or u.startswith("BATCH"):
        return "batch"
    if INTEGRATION_PAT.search(u):
        return "integration"
    return "human"


def is_query(obj):
    return obj.startswith(("AQ", "!Q")) or "/SAPQUERY/" in obj


def build_objmeta(con, domain_of, ctx):
    """Aggregate every executed object: domain + per-user execs + per-month execs."""
    c = con.cursor()
    objmeta = {}
    for channel, where, field, is_tc in CHANNELS:
        for obj, user, n in c.execute(
                f"SELECT {field}, SLGUSER, COUNT(*) FROM rsau_audit_history "
                f"WHERE TXSUBCLSID='{where}' AND {field}<>'' GROUP BY {field}, SLGUSER"):
            prog = ctx["tc_prog"].get(obj) if is_tc else None
            txt = ctx["tc_text"].get(obj) if is_tc else None
            ov = ctx["fm_dom"].get(obj) if channel == "rfc_bapi" else None
            key = (channel, obj)
            m = objmeta.get(key)
            if m is None:
                m = objmeta[key] = {"domain": domain_of(obj, prog, txt, ov),
                                    "execs": 0, "users": Counter(), "months": Counter()}
            m["execs"] += n
            m["users"][user] += n
        for obj, mo, n in c.execute(
                f"SELECT {field}, substr(SAL_DATE,1,6), COUNT(*) FROM rsau_audit_history "
                f"WHERE TXSUBCLSID='{where}' AND {field}<>'' GROUP BY {field}, substr(SAL_DATE,1,6)"):
            m = objmeta.get((channel, obj))
            if m:
                m["months"][mo] += n
    # batch jobs (tbtcp) — actor is batch by definition
    for prog, n, j in c.execute(
            "SELECT PROGNAME, COUNT(*), COUNT(DISTINCT JOBNAME||JOBCOUNT) FROM tbtcp "
            "WHERE PROGNAME<>'' GROUP BY PROGNAME"):
        objmeta[("batch_job", prog)] = {"domain": domain_of(prog, None, None, ctx["job_dom"].get(prog)),
                                        "execs": n, "users": Counter({"JOBBATCH": n}), "months": Counter()}
    return objmeta


def footprint(objmeta, last_global):
    """Roll objmeta up into per-domain footprints."""
    foot = defaultdict(lambda: {"objects": [], "_by_channel": Counter(), "_by_channel_obj": Counter(),
                                "_by_actor": Counter(), "_months": Counter(), "_users": set()})
    for (channel, obj), m in objmeta.items():
        d = m["domain"]
        actor_mix = Counter()
        for u, n in m["users"].items():
            actor_mix[actor_type(u)] += n
        months = m["months"]
        first, last = (min(months), max(months)) if months else (None, None)
        rec = {"object": obj, "channel": channel, "execs": m["execs"],
               "distinct_users": len(m["users"]), "actor_mix": dict(actor_mix),
               "first_month": first, "last_month": last,
               "dead": bool(channel != "batch_job" and last and last < last_global),
               "hidden_extraction": is_query(obj),
               "integration": (actor_mix.get("integration", 0) + actor_mix.get("batch", 0)) > actor_mix.get("human", 0)}
        f = foot[d]
        f["objects"].append(rec)
        f["_by_channel"][channel] += m["execs"]
        f["_by_channel_obj"][channel] += 1
        for a, n in actor_mix.items():
            f["_by_actor"][a] += n
        for mo, n in months.items():
            f["_months"][mo] += n
        f["_users"].update(m["users"].keys())
    return foot


def emit(foot):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    index = {}
    for d, f in foot.items():
        objs = sorted(f["objects"], key=lambda r: -r["execs"])
        rec = {
            "domain": d,
            "totals": {"objects": len(objs), "execs": sum(r["execs"] for r in objs), "distinct_users": len(f["_users"])},
            "by_channel": {ch: {"objects": f["_by_channel_obj"][ch], "execs": f["_by_channel"][ch]}
                           for ch in f["_by_channel"]},
            "by_actor": dict(f["_by_actor"]),
            "time_monthly": dict(sorted(f["_months"].items())),
            "dead_objects": sum(1 for r in objs if r["dead"]),
            "top_objects": objs[:30],
            "hidden_extractions": [r for r in objs if r["hidden_extraction"]][:30],
            "integration_objects": [r for r in objs if r["integration"]][:30],
        }
        (OUTDIR / f"{d}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        index[d] = {k: rec["totals"][k] for k in rec["totals"]}
        index[d].update({"by_actor": rec["by_actor"], "dead_objects": rec["dead_objects"],
                         "hidden_extractions": len(rec["hidden_extractions"]),
                         "integration_objects": len(rec["integration_objects"])})
    (OUTDIR / "_index.json").write_text(
        json.dumps({"_meta": "per-domain operating-model footprints (mine_domain.py)",
                    "domains": dict(sorted(index.items(), key=lambda kv: -kv[1]["execs"]))},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    return index


def main(argv):
    con = sqlite3.connect(GOLD)
    domain_of, ctx = eom.make_classifier(con)
    print("Mining executed objects (rsau + tbtcp) and rolling up by domain ...")
    objmeta = build_objmeta(con, domain_of, ctx)
    last_global = max((m["months"] and max(m["months"]) for m in objmeta.values() if m["months"]), default="999999")
    foot = footprint(objmeta, last_global)
    want = [a.upper() for a in argv[1:]] if len(argv) > 1 else None
    if want:
        foot = {d: f for d, f in foot.items() if d.upper() in want}
    index = emit(foot)
    con.close()
    print(f"\n=== PER-DOMAIN FOOTPRINTS ({len(index)} domains) → {OUTDIR} ===")
    print(f"  {'domain':18s} {'objs':>6} {'execs':>11}  {'human':>9} {'integ':>8} {'batch':>8}  dead  hidden")
    for d, v in sorted(index.items(), key=lambda kv: -kv[1]["execs"]):
        a = v["by_actor"]
        print(f"  {d:18s} {v['objects']:>6} {v['execs']:>11,}  {a.get('human',0):>9,} "
              f"{a.get('integration',0):>8,} {a.get('batch',0):>8,}  {v['dead_objects']:>4}  {v['hidden_extractions']:>4}")


if __name__ == "__main__":
    main(sys.argv)
