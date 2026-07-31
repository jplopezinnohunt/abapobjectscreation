"""derive_satellites.py — ALGORITHM F2: interface → SATELLITE → origin → flow (s097).

The insight this implements: **each interface or connection DEFINES A SATELLITE, and the
satellite is the ORIGIN of the transaction, which is what associates it to a flow.**

Until now F1 (boundary discovery) and A3 (two-axis process × origin) ran independently.
F1 enumerated destinations; A3 parsed raw `host=` / `dest=` strings out of the call stream.
They never spoke. That is precisely why 174 middleware endpoints collapse into one label:
A3 had no catalogue of satellites, only strings.

Nesting them turns a string into an entity:

    raw host/dest string
        + F1 configuration (type, host, declared purpose)
        + observed traffic (volume, direction)
        + the function modules it actually calls
        + those FMs' components → domains        (via C1, the standard)
        = a SATELLITE with a resolved identity and the flows it participates in

A satellite is a first-class thing, not a caller ID. It has an identity, a technical
channel, a volume, a direction, the domains it touches and therefore the flows it drives.
In a system orchestrated 80% from outside, **the satellite catalogue IS the process map at
the boundary.**

Endpoint families: a fleet of GUID endpoints all calling the same function modules is ONE
satellite with many endpoints, not many satellites. Grouping by call signature recovers the
fleet that raw string matching splits apart.

Emits: brain_v2/satellites.json
"""
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# The artifact is written BEFORE this prints. A console that cannot encode an arrow must
# not turn a successful run into a failed one — which is exactly what happened in the
# first full cycle: both algorithms computed correctly and died displaying the result.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from component_map import domain_of_function_module  # noqa: E402
from caller_parse import parse as parse_caller, build_truncation_map, canonical  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
BOUNDARY = REPO / "brain_v2" / "interface_boundary.json"
FLOWS = REPO / "brain_v2" / "process_flows" / "process_flows.json"
OUT = REPO / "brain_v2" / "satellites.json"

GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}", re.I)
# Callers that are the system talking to itself, not an external satellite.
INTERNAL = re.compile(r"^(SAP[A-Z]*|WF-BATCH|DDIC|TMSADM|SM_[A-Z0-9]+|<unknown>|NONE)$", re.I)


def signature(fms):
    """A satellite's call signature: its top function modules, order-independent.

    Two endpoints calling the same functions are the same satellite wearing two names —
    which is what a GUID fleet is.
    """
    return tuple(sorted(f for f, _ in sorted(fms.items(), key=lambda x: -x[1])[:4]))


def main():
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)

    # ---- observe: who calls what, from where ----------------------------
    # PATTERN D6 — aggregate in SQL before resolving in Python.
    # 8,764,296 audit rows carry a PARAMX, but only 11,936 DISTINCT values: a 734x ratio.
    # Parsing per row ran the regex 8.7 million times to produce 11,936 answers. The
    # GROUP BY pushes the reduction to the database and the parse runs once per distinct
    # caller string.
    # See ecosystem-coordinator/.knowledge/way-of-working/sql-aggregate-before-resolve.md
    by_caller = defaultdict(lambda: {"calls": 0, "fms": defaultdict(int),
                                     "users": set(), "hosts": set(), "dests": set()})
    rows = con.execute(
        "SELECT PARAMX, PARAM3, SLGUSER, COUNT(*) AS n "
        "FROM rsau_audit_history "
        "WHERE PARAMX IS NOT NULL AND PARAMX <> '' "
        "GROUP BY PARAMX, PARAM3, SLGUSER").fetchall()

    # parse each distinct caller string ONCE, then REPAIR SAP's truncation.
    # PARAMX is a fixed-length field: SAP cuts the caller string when it does not fit, so
    # 'HQ-SAP-P01-1_P01_' and '328a121d-ba7a-4b84-b' are the same entities as their longer
    # twins. Without the repair one satellite appears as several — which is exactly why the
    # 17- and 21-endpoint fleets were suspected of being one.
    parsed = {}
    for paramx, fm, user, n in rows:
        px = paramx or ""
        if px not in parsed:
            d, h, _u = parse_caller(px)
            parsed[px] = (d, h)
    observed = {v for pair in parsed.values() for v in pair if v}
    repair, ambiguous = build_truncation_map(observed)
    print(f"  truncation repaired: {len(repair)} value(s); {len(ambiguous)} left ambiguous")

    for paramx, fm, user, n in rows:
        dest, host = parsed[paramx or ""]
        dest = canonical(dest, repair) if dest else None
        host = canonical(host, repair) if host else None
        key = dest or host or (user or "").strip()
        if not key or INTERNAL.match(key):
            continue
        e = by_caller[key]
        e["calls"] += n
        if fm:
            e["fms"][fm.strip()] += n
        if user:
            e["users"].add(user.strip())
        if host:
            e["hosts"].add(host)
        if dest:
            e["dests"].add(dest)
    print(f"  aggregated to {len(rows):,} rows; parsed {len(parsed):,} distinct caller strings")

    con.close()

    # ---- enrich with F1's configuration ----------------------------------
    configured = {}
    if BOUNDARY.exists():
        b = json.load(open(BOUNDARY, encoding="utf-8"))
        for d in b.get("live", []) + b.get("dead", []):
            configured[d["destination"]] = {"type": d.get("type"), "host": d.get("host")}

    # ---- group endpoints into satellite FLEETS by call signature ---------
    fleets = defaultdict(list)
    for key, e in by_caller.items():
        if e["calls"] < 20:
            continue
        fleets[signature(e["fms"])].append(key)

    flows = json.load(open(FLOWS, encoding="utf-8")).get("flows", {}) if FLOWS.exists() else {}
    dom_flows = defaultdict(list)
    for fname, f in flows.items():
        for dom in (f.get("domains") or []):
            dom_flows[dom].append(fname)

    satellites = []
    for sig, endpoints in fleets.items():
        if not sig:
            continue
        agg_fms, calls, users, hosts = defaultdict(int), 0, set(), set()
        for k in endpoints:
            e = by_caller[k]
            calls += e["calls"]
            users |= e["users"]
            hosts |= e["hosts"]
            for f, n in e["fms"].items():
                agg_fms[f] += n

        dom_calls = defaultdict(int)
        for f, n in agg_fms.items():
            d = domain_of_function_module(f)
            if d:
                dom_calls[d] += n
        served = sorted(dom_calls, key=lambda d: -dom_calls[d])
        drives = sorted({fl for d in served for fl in dom_flows.get(d, [])})

        guids = [e for e in endpoints if GUID.match(e)]
        name = (f"fleet of {len(endpoints)} endpoints" if len(endpoints) > 3
                else " / ".join(sorted(endpoints)[:3]))
        satellites.append({
            "satellite": name,
            "endpoints": len(endpoints),
            "endpoint_sample": sorted(endpoints)[:5],
            "is_guid_fleet": len(guids) > 1,
            "calls": calls,
            "named_users": sorted(users)[:5],
            "hosts": sorted(hosts)[:4],
            "configured_in_rfcdes": sum(1 for e in endpoints if e in configured),
            "top_functions": [{"fm": f, "calls": n, "domain": domain_of_function_module(f)}
                              for f, n in sorted(agg_fms.items(), key=lambda x: -x[1])[:6]],
            "serves_domains": served[:6],
            "drives_flows": drives,
        })
    satellites.sort(key=lambda s: -s["calls"])

    unresolved = [s for s in satellites if not s["serves_domains"]]
    out = {
        "_generated_by": "process_mining/derive_satellites.py",
        "_algorithm": "F2 — satellite derivation (nested: F1 boundary → satellite → origin → flow)",
        "_the_insight": ("each interface or connection DEFINES A SATELLITE; the satellite is "
                         "the ORIGIN of the transaction; the origin is what associates it to a "
                         "flow. In a system orchestrated 80% from outside, the satellite "
                         "catalogue IS the process map at the boundary."),
        "_why_nesting_matters": ("F1 and A3 ran independently — F1 enumerated destinations, A3 "
                                 "parsed raw host strings — which is why a fleet of GUID "
                                 "endpoints collapsed into one label. Grouping by CALL "
                                 "SIGNATURE recovers the fleet: endpoints calling the same "
                                 "functions are one satellite wearing many names."),
        "summary": {"satellites": len(satellites),
                    "guid_fleets": sum(1 for s in satellites if s["is_guid_fleet"]),
                    "with_resolved_domains": len(satellites) - len(unresolved),
                    "total_calls": sum(s["calls"] for s in satellites)},
        "satellites": satellites[:40],
        "unresolved": [{"satellite": s["satellite"], "calls": s["calls"],
                        "top_functions": [f["fm"] for f in s["top_functions"][:3]]}
                       for s in unresolved[:15]],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    sm = out["summary"]
    print(f"wrote {OUT}")
    print(f"  {sm['satellites']} satellites · {sm['guid_fleets']} GUID fleets recovered · "
          f"{sm['total_calls']:,} calls")
    print("\n  SATELLITE → DOMAINS → FLOWS:")
    for s in satellites[:10]:
        d = ", ".join(s["serves_domains"][:3]) or "?"
        fl = ", ".join(s["drives_flows"][:3]) or "-"
        print(f"    {s['satellite'][:34]:34s} {s['calls']:>8,d}  [{d}]")
        if s["drives_flows"]:
            print(f"        drives: {fl}")


if __name__ == "__main__":
    main()
