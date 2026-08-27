"""interface_boundary.py — ALGORITHM F1: the integration boundary, discovered (s097).

Until now this was the one MISSING algorithm in the catalogue. The 37-flow integration map
was PROSE, written by hand. Good prose — but it cannot detect a new destination appearing,
cannot go stale visibly, and cannot be reproduced on a second installation.

The algorithm, as specified in the catalogue:

  1. ENUMERATE the boundary from every source that declares it:
        RFCDES      outbound/inbound RFC destinations (what is configured)
        EDIDC       IDoc traffic with partner, message type and direction (what flowed)
        TBTCP       scheduled jobs and their programs (file-based interfaces)
        ICFSERVICE  HTTP services (what is exposed)
  2. CORRELATE configuration against OBSERVED TRAFFIC. This is the core move and the one
     a hand-written map cannot make:
        configured + traffic       -> LIVE
        configured + no traffic    -> DEAD (a maintenance and attack surface nobody uses)
                                      ...but ONLY if this source could have seen the traffic
        transport we cannot see    -> UNOBSERVABLE (added s106, claim 620): the evidence base
                                      is the RFC audit log, and an HTTP destination driven by
                                      cl_http_client writes no row in it. Reporting those as
                                      DEAD published 38 verdicts the evidence never supported.
        traffic + not configured   -> UNDECLARED (something crosses the boundary off-map)

     The rule this encodes: an instrument states what it CAN see, and names what it cannot.
     A zero from a source that does not cover the case is not a finding — it is a blind spot
     wearing a finding's clothes.
  3. CLASSIFY direction and volume, and bind each flow to the process flows it serves.
  4. DIFF against the previous run — a new interface can CHANGE THE MEANING of a domain,
     which is exactly the interpretation trigger already declared in check_triggers.

Why correlation is the point: a destination list tells you what someone once configured.
Only the call stream tells you what is actually happening today. The gap between the two
IS the finding, in both directions.

Emits: brain_v2/interface_boundary.json   Run: python process_mining/interface_boundary.py
"""
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from component_map import domain_of_function_module  # noqa: E402
from caller_parse import parse as parse_caller, build_truncation_map, canonical  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "interface_boundary.json"
PREV = OUT

# RFC destination types, per SAP's own coding.
RFCTYPE = {"3": "ABAP (RFC)", "T": "TCP/IP (external program)", "H": "HTTP",
           "G": "HTTP external", "I": "internal", "L": "logical", "X": "driver",
           "2": "R/2", "S": "SNA/CPIC", "M": "CMC"}

# CAN THIS INSTRUMENT SEE A GIVEN DESTINATION AT ALL? (added s106, claim 620)
#
# Step 2 correlates configuration against rsau_audit_history.PARAMX — the SECURITY AUDIT
# LOG, which records RFC CALLS. That is the whole evidence base, and it does not cover
# every transport a destination can use:
#
#   OBSERVABLE   the destination is driven by the RFC runtime, so a call writes PARAMX.
#   UNOBSERVABLE the destination is driven by cl_http_client (HTTP), which is NOT RFC and
#                writes no audit row here. Zero observed calls therefore means WE CANNOT
#                SEE, not "nobody uses it" — calling those DEAD is a claim the evidence
#                cannot support. Measured case: svc-prod-role.hq.int.unesco.org (the
#                UNESCO RoleManagement service) sat in DEAD with 0 calls while a documented
#                caller reaches that host through cl_http_client=>create_by_destination.
#   UNCERTAIN    'L' is a POINTER to another destination (traffic is recorded under the
#                target, so 0 here can be correct AND meaningless) and 'X' is a driver
#                entry. Neither is confirmed to emit PARAMX, so neither earns a verdict.
#
# Removing the old 400,000-row sample fixed the COVERAGE of this source. It did not — and
# could not — fix its APPLICABILITY. Those are different properties, and conflating them is
# how a blind spot gets published as a finding.
OBSERVABILITY = {
    "3": "OBSERVABLE", "I": "OBSERVABLE", "T": "OBSERVABLE",
    "2": "OBSERVABLE", "S": "OBSERVABLE", "M": "OBSERVABLE",
    "G": "UNOBSERVABLE", "H": "UNOBSERVABLE",
    "L": "UNCERTAIN", "X": "UNCERTAIN",
}


def _rows(con, sql, params=()):
    try:
        return con.execute(sql, params).fetchall()
    except sqlite3.Error:
        return []


def main():
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)

    # ---- 1. ENUMERATE ----------------------------------------------------
    destinations = {}
    for dest, rtype, opts in _rows(con, "SELECT RFCDEST, RFCTYPE, RFCOPTIONS FROM rfcdes"):
        dest = (dest or "").strip()
        if not dest:
            continue
        host = None
        m = re.search(r"H=([^,]+)", opts or "")
        if m:
            host = m.group(1).strip()
        code = (rtype or "").strip()
        destinations[dest] = {"type": RFCTYPE.get(code, rtype), "host": host,
                              "configured": True,
                              "observability": OBSERVABILITY.get(code, "UNCERTAIN")}

    idocs = defaultdict(lambda: {"count": 0, "partners": set(), "direction": set()})
    for idoctp, mestyp, sndprn, rcvprn, status in _rows(
            con, "SELECT IDOCTP, MESTYP, SNDPRN, RCVPRN, STATUS FROM edidc"):
        key = (mestyp or idoctp or "?").strip()
        e = idocs[key]
        e["count"] += 1
        # SAP status: 01-49 outbound, 50-75 inbound
        try:
            e["direction"].add("outbound" if int(str(status).strip() or 0) < 50 else "inbound")
        except ValueError:
            pass
        for p in ((sndprn or "").strip(), (rcvprn or "").strip()):
            if p:
                e["partners"].add(p)

    jobs = defaultdict(lambda: {"runs": 0, "programs": set()})
    for jobname, prog in _rows(con, "SELECT p.JOBNAME, p.PROGNAME FROM tbtcp p"):
        j = (jobname or "").strip()
        if j:
            jobs[j]["runs"] += 1
            if prog:
                jobs[j]["programs"].add(prog.strip())

    http_active = sum(1 for (a,) in _rows(con, "SELECT ICFACTIVE FROM icfservice")
                      if (a or "").strip() in ("X", "A", "1"))

    # ---- 2. CORRELATE against observed traffic ---------------------------
    # The audit log records the DESTINATION and HOST of each RFC call in PARAMX.
    seen_dest, seen_host = defaultdict(int), defaultdict(int)
    fm_by_dest = defaultdict(lambda: defaultdict(int))

    # PATTERN D6 — aggregate in SQL before resolving in Python, and it fixes a declared
    # defect at the same time. The first version scanned a LIMIT of 400,000 rows out of
    # 8.7M, so every DEAD verdict carried sampling error: a destination could be reported
    # dead purely because its traffic fell outside the sample.
    #
    # 8,764,296 rows carry a PARAMX and only 11,936 are DISTINCT (734x). Grouping first
    # makes the FULL scan cheaper than the sample was, so the cap is gone and DEAD is now
    # a fact rather than an artefact.
    rows = con.execute(
        "SELECT PARAMX, PARAM3, COUNT(*) AS n FROM rsau_audit_history "
        "WHERE PARAMX IS NOT NULL AND PARAMX <> '' GROUP BY PARAMX, PARAM3").fetchall()
    # parse once per distinct string, then REPAIR the truncation SAP applies to PARAMX.
    # A truncated destination looked UNDECLARED because it matched no RFCDES entry — the
    # repair is therefore a correctness fix, not tidiness.
    parsed = {}
    for paramx, fm, n in rows:
        px = paramx or ""
        if px not in parsed:
            d, h, _u = parse_caller(px)
            parsed[px] = (d, h)
    observed = {v for pair in parsed.values() for v in pair if v}
    observed |= set(destinations)          # a fragment may complete to a CONFIGURED name
    repair, ambiguous = build_truncation_map(observed)
    print(f"  truncation repaired: {len(repair)} value(s); {len(ambiguous)} left ambiguous")

    for paramx, fm, n in rows:
        dd, hh = parsed[paramx or ""]
        dd = canonical(dd, repair) if dd else None
        hh = canonical(hh, repair) if hh else None
        if dd:
            seen_dest[dd] += n
            if fm:
                fm_by_dest[dd][fm.strip()] += n
        if hh:
            seen_host[hh] += n
    print(f"  FULL scan (no sampling): {len(rows):,} aggregated rows, "
          f"{len(parsed):,} distinct caller strings")

    live, dead, unobservable, undeclared = [], [], [], []
    for dest, meta in destinations.items():
        n = seen_dest.get(dest, 0)
        row = {"destination": dest, **meta, "observed_calls": n}
        if n:
            top = sorted(fm_by_dest[dest].items(), key=lambda x: -x[1])[:5]
            row["top_functions"] = [{"fm": f, "calls": c,
                                     "domain": domain_of_function_module(f)} for f, c in top]
            row["serves_domains"] = sorted({d for d in
                                            (domain_of_function_module(f) for f, _ in top) if d})
            live.append(row)
        elif meta["observability"] == "UNOBSERVABLE":
            # NOT dead — unseen. This source cannot record its transport at all.
            row["why"] = ("HTTP transport (cl_http_client), which writes no RFC audit row — "
                          "0 calls here is the instrument's blind spot, not a usage fact")
            unobservable.append(row)
        else:
            if meta["observability"] == "UNCERTAIN":
                row["caveat"] = ("transport not confirmed to emit PARAMX — treat DEAD as "
                                 "unproven for this type")
            dead.append(row)
    for dest, n in sorted(seen_dest.items(), key=lambda x: -x[1]):
        if dest not in destinations:
            undeclared.append({"destination": dest, "observed_calls": n,
                               "note": "traffic crossing the boundary with no RFCDES entry"})

    # ---- 3. CLASSIFY + bind ---------------------------------------------
    idoc_flows = [{"message_type": k, "documents": v["count"],
                   "direction": sorted(v["direction"]) or ["unknown"],
                   "partners": sorted(v["partners"])[:6]}
                  for k, v in sorted(idocs.items(), key=lambda x: -x[1]["count"])]

    file_jobs = [{"job": k, "runs": v["runs"], "programs": sorted(v["programs"])[:3]}
                 for k, v in sorted(jobs.items(), key=lambda x: -x[1]["runs"])[:40]]

    # ---- 4. DIFF against the previous run --------------------------------
    prev = {}
    if PREV.exists():
        try:
            prev = json.load(open(PREV, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev = {}
    # every bucket, or a destination that merely MOVED bucket reads as vanished/appeared
    prev_dests = {d["destination"] for d in
                  (prev.get("live", []) + prev.get("dead", [])
                   + prev.get("unobservable", []))} if prev else set()
    appeared = sorted(set(destinations) - prev_dests) if prev_dests else []
    vanished = sorted(prev_dests - set(destinations)) if prev_dests else []

    out = {
        "_generated_by": "process_mining/interface_boundary.py",
        "_algorithm": "F1 — interface boundary discovery",
        "_the_move": ("configuration tells you what someone once set up; the call stream "
                      "tells you what happens today. The GAP between them is the finding, "
                      "in both directions."),
        "summary": {
            "destinations_configured": len(destinations),
            "destinations_live": len(live),
            "destinations_dead": len(dead),
            "destinations_unobservable": len(unobservable),
            "destinations_undeclared": len(undeclared),
            "idoc_message_types": len(idocs),
            "idoc_documents": sum(v["count"] for v in idocs.values()),
            "scheduled_jobs": len(jobs),
            "http_services_active": http_active,
        },
        "findings": {
            "DEAD": ("configured destinations, driven by a transport this source CAN see, "
                     "with zero observed traffic — maintenance and attack surface that "
                     "nobody uses"),
            "UNOBSERVABLE": ("configured destinations whose transport writes no RFC audit "
                             "row (HTTP via cl_http_client). We CANNOT SEE them; this is "
                             "never evidence that nobody uses them. To decide live/dead "
                             "for these you need a different source than the RFC audit "
                             "log. Split out s106 — they used to be reported as DEAD"),
            "UNDECLARED": ("traffic crossing the boundary with no configuration entry — "
                           "something is talking to this system off-map"),
        },
        "_evidence_base": ("rsau_audit_history.PARAMX — the Security Audit Log, which "
                           "records RFC CALLS. Every live/dead verdict here is only as wide "
                           "as that source; see `observability` on each destination row."),
        "live": sorted(live, key=lambda x: -x["observed_calls"]),
        "dead": sorted(dead, key=lambda x: x["destination"]),
        "unobservable": sorted(unobservable, key=lambda x: x["destination"]),
        "undeclared": undeclared[:40],
        "idoc_flows": idoc_flows[:30],
        "batch_jobs": file_jobs,
        "diff_vs_previous_run": {"appeared": appeared, "vanished": vanished,
                                 "_why": ("a NEW interface can change the meaning of a "
                                          "domain, not merely add to it — this feeds the "
                                          "interpretation trigger")},
    }
    con.close()
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    s = out["summary"]
    print(f"wrote {OUT}")
    print(f"  destinations: {s['destinations_configured']} configured — "
          f"{s['destinations_live']} LIVE, {s['destinations_dead']} DEAD, "
          f"{s['destinations_unobservable']} UNOBSERVABLE, "
          f"{s['destinations_undeclared']} UNDECLARED")
    if s["destinations_unobservable"]:
        print(f"    ^ UNOBSERVABLE = HTTP transport, no RFC audit row. NOT a usage verdict.")
    print(f"  IDoc: {s['idoc_message_types']} message types, {s['idoc_documents']:,} documents")
    print(f"  jobs: {s['scheduled_jobs']:,} · HTTP services active: {s['http_services_active']:,}")
    if live:
        print("\n  LIVE destinations by observed traffic:")
        for d in out["live"][:8]:
            doms = ", ".join(d.get("serves_domains") or []) or "?"
            print(f"    {d['destination'][:34]:34s} {d['observed_calls']:>8,d} calls  [{doms}]")
    if undeclared:
        print(f"\n  UNDECLARED — crossing the boundary with no RFCDES entry:")
        for d in undeclared[:6]:
            print(f"    {d['destination'][:44]:44s} {d['observed_calls']:>8,d} calls")


if __name__ == "__main__":
    main()
