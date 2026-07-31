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
        configured + no traffic  -> DEAD (a maintenance and attack surface nobody uses)
        traffic + not configured -> UNDECLARED (something crosses the boundary off-map)
        configured + traffic     -> LIVE
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
from component_map import domain_of_function_module  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "interface_boundary.json"
PREV = OUT

# RFC destination types, per SAP's own coding.
RFCTYPE = {"3": "ABAP (RFC)", "T": "TCP/IP (external program)", "H": "HTTP",
           "G": "HTTP external", "I": "internal", "L": "logical", "X": "driver",
           "2": "R/2", "S": "SNA/CPIC", "M": "CMC"}


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
        destinations[dest] = {"type": RFCTYPE.get((rtype or "").strip(), rtype),
                              "host": host, "configured": True}

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
    for paramx, fm in _rows(
            con, "SELECT PARAMX, PARAM3 FROM rsau_audit_history "
                 "WHERE PARAMX IS NOT NULL AND PARAMX <> '' LIMIT 400000"):
        px = paramx or ""
        d = re.search(r"dest=\s*([^\s,;]+)", px)
        h = re.search(r"host=\s*([^\s,;]+)", px)
        if d:
            dd = d.group(1).strip()
            seen_dest[dd] += 1
            if fm:
                fm_by_dest[dd][fm.strip()] += 1
        if h:
            seen_host[h.group(1).strip()] += 1

    live, dead, undeclared = [], [], []
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
        else:
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
    prev_dests = {d["destination"] for d in
                  (prev.get("live", []) + prev.get("dead", []))} if prev else set()
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
            "destinations_undeclared": len(undeclared),
            "idoc_message_types": len(idocs),
            "idoc_documents": sum(v["count"] for v in idocs.values()),
            "scheduled_jobs": len(jobs),
            "http_services_active": http_active,
        },
        "findings": {
            "DEAD": ("configured destinations with zero observed traffic — maintenance and "
                     "attack surface that nobody uses"),
            "UNDECLARED": ("traffic crossing the boundary with no configuration entry — "
                           "something is talking to this system off-map"),
        },
        "live": sorted(live, key=lambda x: -x["observed_calls"]),
        "dead": sorted(dead, key=lambda x: x["destination"]),
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
          f"{s['destinations_undeclared']} UNDECLARED")
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
