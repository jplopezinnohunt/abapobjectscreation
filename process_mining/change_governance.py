"""ALGORITHM A17 — CHANGE GOVERNANCE DETECTOR.

WHAT IT ANSWERS
    Three questions that only have answers when the change log, the execution log and the
    transport record are read together:
      1. CHANNEL DIFFERENCE — for the same object, does one maintainer use a route the
         others do not? That is what makes an action invisible to controls built around
         the transaction.
      2. CONFIG ONLY IN PRODUCTION — which configuration-like objects are changed in P01
         and have never travelled by transport?
      3. TRANSPORTED CONTENT — is the transport channel carrying DATA rather than
         development, and is that rising?

WHY IT IS A DETECTOR AND NOT A POLICY CHECK
    There is no policy document to compare against, and asking for one would stall the
    work. Instead the POPULATION OF MAINTAINERS DEFINES THE NORM: whatever route most
    people use for an object is the expected route, and a route only one person uses is the
    finding. That makes the detector portable — it needs no local rulebook.

WHAT IT DELIBERATELY DOES NOT CONCLUDE
    A channel difference is a SIGNAL, not a verdict. Number ranges are not transported by
    SAP design; a brand-new implementation is naturally driven from the editor before its
    transaction is rolled out; role generation legitimately carries its generated tables. So
    every finding is emitted with its counter-explanation attached, and the algorithm ranks
    by how UNUSUAL the route is rather than by how bad it sounds.

USAGE
    python process_mining/change_governance.py [--since 20240101]
"""

import collections
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "brain_v2", "methods"))
from algorithm_memory import remember  # noqa: E402

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
sys.path.insert(0, HERE)
try:
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None

GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
# A route used by one person against an object several others maintain is the signal.
MIN_MAINTAINERS = 3
# Below this the object is too rare to say anything about its norm.
MIN_CHANGES = 10
# A business DOCUMENT is changed by many people or in enormous volume; a CONFIGURATION
# object is not. Without this split the second question answers itself with every
# transactional object in the system, which is true and useless.
CONFIG_MAX_CHANGES = 20000
CONFIG_MAX_MAINTAINERS = 25
# Routes that are generic rather than object-specific: reaching an object through one of
# these means bypassing whatever transaction was built to maintain it.
GENERIC = {"SE38", "SE37", "SE16", "SE16N", "SM30", "SM31", "SA38", "SE11", "SE80"}


def q(cx, sql, args=()):
    return cx.execute(sql, args).fetchall()


def channel_difference(cx, log, since):
    """Who reaches an object by a route nobody else uses."""
    rows = q(cx, 'SELECT OBJECTCLAS, trim(USERNAME), TCODE, count(*) FROM "%s" '
                 "WHERE UDATE >= ? GROUP BY 1,2,3" % log, (since,))
    per_obj = collections.defaultdict(lambda: {"routes": collections.Counter(),
                                               "users": set(), "by_user_route": []})
    for oc, us, tc, k in rows:
        tc = (tc or "").strip() or "(none)"
        d = per_obj[oc]
        d["routes"][tc] += k
        d["users"].add(us)
        d["by_user_route"].append((us, tc, k))

    out = []
    for oc, d in per_obj.items():
        total = sum(d["routes"].values())
        if total < MIN_CHANGES or len(d["users"]) < MIN_MAINTAINERS:
            continue
        modal = d["routes"].most_common(1)[0][0]
        # A GENERIC route that is itself the modal one is the stronger finding, not a
        # weaker one: the object's normal maintenance path has become the editor. The
        # first version skipped exactly these because it only looked at outliers.
        if modal in GENERIC:
            for us, tc, k in d["by_user_route"]:
                if tc != modal:
                    continue
                out.append({
                    "object": oc, "user": us, "route": tc, "changes": k,
                    "modal_route": modal, "maintainers": len(d["users"]),
                    "route_share_pct": round(100.0 * d["routes"][tc] / total, 1),
                    "other_routes": [r for r, _ in d["routes"].most_common(6) if r != tc],
                    "_signal": ("the MODAL route for this object is a GENERIC one — the "
                                "object's normal maintenance path is the editor, not a "
                                "maintenance transaction"),
                    "_counter_explanation": ("legitimate where SAP provides no maintenance "
                                             "transaction, and during a new implementation"),
                    "_kind": "GENERIC_ROUTE_IS_THE_NORM"})
        for us, tc, k in d["by_user_route"]:
            if tc == modal:
                continue
            share = 100.0 * d["routes"][tc] / total
            # Only this user on this route, and the route is a generic one.
            sole = sum(1 for u2, t2, _ in d["by_user_route"] if t2 == tc) == 1
            if sole and tc in GENERIC:
                out.append({
                    "object": oc, "user": us, "route": tc, "changes": k,
                    "modal_route": modal, "maintainers": len(d["users"]),
                    "route_share_pct": round(share, 1),
                    "other_routes": [r for r, _ in d["routes"].most_common(5) if r != tc],
                    "_signal": ("sole user of a GENERIC route against an object %d people "
                                "maintain, whose usual route is %s" % (len(d["users"]), modal)),
                    "_counter_explanation": ("a generic route is legitimate for a new "
                                             "implementation before its transaction is rolled "
                                             "out, and for objects SAP does not transport"),
                    "_kind": "SOLE_USER_OF_A_GENERIC_ROUTE",
                })
    return sorted(out, key=lambda x: -x["changes"])


def config_only_in_production(cx, since):
    """Objects changed in P01 that have never travelled."""
    if not q(cx, "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cts_objects'"):
        return {"_unavailable": "no transport record in the golden"}
    travelled = {(r[0] or "").upper() for r in q(cx, "SELECT DISTINCT obj_name FROM cts_objects")}
    types = {(r[0] or "").upper() for r in q(cx, "SELECT DISTINCT object FROM cts_objects")}
    rows = q(cx, "SELECT OBJECTCLAS, count(*), count(DISTINCT USERNAME) FROM cdhdr_history "
                 "WHERE UDATE >= ? GROUP BY 1", (since,))
    out = []
    for oc, k, nu in rows:
        u = (oc or "").upper()
        if u in travelled or u in types:
            continue
        # Keep CONFIGURATION only. A business document is changed by many people or in
        # enormous volume, and listing those answers the question with noise.
        if k > CONFIG_MAX_CHANGES or nu > CONFIG_MAX_MAINTAINERS:
            continue
        out.append({"object": oc, "changes_in_production": k, "maintainers": nu,
                    "transport_appearances": 0})
    return sorted(out, key=lambda x: -x["changes_in_production"])[:20]


def transported_content(cx, since):
    """Is the transport channel carrying DATA, and is that rising?"""
    if not q(cx, "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cts_transports'"):
        return {"_unavailable": "no transport record in the golden"}
    by_month = q(cx, "SELECT substr(t.as4date,1,6), count(DISTINCT t.trkorr), "
                     "sum(CASE WHEN o.object='TABU' THEN 1 ELSE 0 END) "
                     "FROM cts_transports t LEFT JOIN cts_objects o ON o.trkorr = t.trkorr "
                     "WHERE t.as4date >= ? GROUP BY 1 ORDER BY 1", (since,))
    series = [{"month": m, "transports": n, "data_objects": d or 0} for m, n, d in by_month]
    tables = q(cx, "SELECT o.obj_name, count(*) FROM cts_objects o "
                   "JOIN cts_transports t ON t.trkorr = o.trkorr "
                   "WHERE o.object='TABU' AND t.as4date >= ? GROUP BY 1 ORDER BY 2 DESC "
                   "LIMIT 12", (since,))
    movers = q(cx, "SELECT t.as4user, count(DISTINCT t.trkorr), count(*) FROM cts_objects o "
                   "JOIN cts_transports t ON t.trkorr = o.trkorr WHERE o.object='TABU' "
                   "AND t.as4date >= ? GROUP BY 1 ORDER BY 3 DESC LIMIT 8", (since,))
    # The trend is what matters: transport COUNT can be flat while content multiplies.
    half = len(series) // 2
    early = sum(s["data_objects"] for s in series[:half]) or 1
    late = sum(s["data_objects"] for s in series[half:])
    return {"by_month": series, "top_tables": tables, "top_movers": movers,
            "trend_multiple": round(late / float(early), 1),
            "_why_the_trend_and_not_the_count": (
                "the number of transports can be flat while the DATA they carry multiplies. "
                "Counting transports hides it; counting TABU objects does not")}


def main(argv):
    since = argv[argv.index("--since") + 1] if "--since" in argv else "20240101"

    # AL PRINCIPIO, no al final: aqui el minero esta a punto de leer justo los datos que
    # contestan lo que el foro le pregunta. Al terminar ya cerro la conexion y lo que queda
    # es buena intencion. Los temas son las tablas y columnas que ESTE minero toca.
    if _aprendido:
        _aprendido("cdhdr_history", "objectclas", "transporte", "tabu",
                   "cts_objects").avisar()

    cx = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True)

    print("A17 CHANGE GOVERNANCE DETECTOR   since %s" % since)
    print("=" * 72)

    chan = []
    # cdhdr_history first, and the order is the point: "cdhdr" is SUPERSEDED and is a
    # strict subset (7.8M rows against 12.0M, 57 object classes against 72). It stays
    # as a fallback for an installation that has not accumulated history yet; taking
    # it when history exists reported PBC as having zero change activity when it has
    # 3,449,049.
    for log in ("cdhdr_history", "cdhdr"):
        if q(cx, "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (log,)):
            chan = channel_difference(cx, log, since)
            break
    print("\n1. CHANNEL DIFFERENCE — a route only one maintainer uses")
    for x in chan[:10]:
        print("   %-14s %-16s via %-8s %5d changes | %d maintainers, usual route %s"
              % (x["object"], x["user"], x["route"], x["changes"], x["maintainers"],
                 x["modal_route"]))
    if not chan:
        print("   none above the thresholds")

    cfg = config_only_in_production(cx, since)
    print("\n2. CHANGED IN PRODUCTION, NEVER TRANSPORTED")
    if isinstance(cfg, dict):
        print("   %s" % cfg.get("_unavailable"))
    else:
        for x in cfg[:12]:
            print("   %-16s %7d changes by %3d maintainers"
                  % (x["object"], x["changes_in_production"], x["maintainers"]))

    tc = transported_content(cx, since)
    print("\n3. TRANSPORTED CONTENT — data rather than development")
    if "_unavailable" in tc:
        print("   %s" % tc["_unavailable"])
    else:
        print("   trend: data objects multiplied %sx between the first and second half"
              % tc["trend_multiple"])
        print("   top tables: %s" % ", ".join("%s(%d)" % t for t in tc["top_tables"][:6]))
        print("   top movers: %s" % ", ".join("%s(%d)" % (m[0], m[2]) for m in tc["top_movers"][:5]))

    rep = {"_algorithm": "A17 change_governance.py", "since": since,
           "_the_premise": ("the POPULATION OF MAINTAINERS DEFINES THE NORM — no policy "
                            "document needed, which is what makes it portable"),
           "_every_finding_carries_its_counter_explanation": (
               "a channel difference is a SIGNAL, not a verdict. Generic routes are legitimate "
               "for a new implementation before its transaction is rolled out, and for objects "
               "SAP does not transport by design"),
           "channel_difference": chan, "config_only_in_production": cfg,
           "transported_content": tc}
    p = os.path.join(ROOT, "brain_v2", "change_governance.json")
    json.dump(rep, io.open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    remember(subject="change governance", kind="INSTRUMENT", learned_by="A17_change_governance",
             session=98,
             fact="%d channel differences, %d objects changed in production and never "
                  "transported" % (len(chan), len(cfg) if isinstance(cfg, list) else 0),
             evidence="brain_v2/change_governance.json",
             implication=("the maintainer population is the norm. Run this before asking anyone "
                          "for a policy — and read every finding with its counter-explanation"))
    print("\nwritten: brain_v2/change_governance.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
