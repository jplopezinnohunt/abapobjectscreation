"""derive_object_roles.py — what each object IS FOR, not just where it belongs (s097).

The model could say which DOMAIN an object belongs to and which COMPONENT it comes from.
It could not say what the object *does*. "PBC has 33 objects" is not knowledge; "PBC has 2
posting engines, 14 reports and 1 interface, and one operator runs the worklist" is.

The role is DERIVABLE from signals we already hold — no new extraction:

    edges       reads only -> it informs;  writes -> it changes the system of record
    channel     dialog / report / batch / rfc — how it is reached
    audience    one user is automation or a key person; many users is a shared tool
    volume      a handful of calls a month is not the same object as 40,000
    text        what a human named it

**Why the role matters more than the count.** A domain with many readers and no writer is
consumed, not operated. A writer with one operator is a key-person risk. An interface with
high volume and no configured destination is a governance finding. None of those questions
can be asked of a list of names.

**The role is a HYPOTHESIS with a confidence**, like every other derived answer here. A
report that writes a log table looks like a writer; the confidence and the evidence are
returned so a reader can disagree.

Emits: brain_v2/object_roles.json
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
from component_map import resolve_domain  # noqa: E402

STATE = REPO / "brain_v2" / "brain_state.json"
EMAP = REPO / "brain_v2" / "executed_objects_domain_map.json"
TEXTS = REPO / "brain_v2" / "executed_objects_text.json"
OUT = REPO / "brain_v2" / "object_roles.json"

ROLES = {
    "POSTING_ENGINE": "changes the system of record — writes business data",
    "REPORT": "informs — reads and presents, changes nothing",
    "INTERFACE": "carries data across the system boundary",
    "WORKLIST": "an operator works items through it, repeatedly",
    "MASTER_DATA_MAINTENANCE": "creates or changes master data",
    "CHECKER": "validates or derives without persisting",
    "BATCH_ENGINE": "runs unattended on a schedule",
    "TECHNICAL": "infrastructure — connectivity, session, monitoring",
    "UNKNOWN": "not enough signal",
}


def load(p):
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}


def derive(name, obj, exec_info, text):
    """Return (role, confidence, evidence). Confidence reflects how many signals agree."""
    ev, score = [], {}

    reads = obj.get("reads_tables") or []
    writes = obj.get("writes_tables") or []
    calls = obj.get("calls_fms") or []
    channel = (exec_info or {}).get("channel")
    users = (exec_info or {}).get("users") or 0
    execs = (exec_info or {}).get("execs") or 0
    t = (text or "").upper()

    if writes:
        score["POSTING_ENGINE"] = score.get("POSTING_ENGINE", 0) + 2
        ev.append(f"writes {len(writes)} table(s)")
    if reads and not writes:
        score["REPORT"] = score.get("REPORT", 0) + 2
        ev.append(f"reads {len(reads)} table(s), writes none")
    if channel == "rfc_bapi":
        score["INTERFACE"] = score.get("INTERFACE", 0) + 3
        ev.append("reached over RFC — it is called from outside")
    if channel == "batch_job":
        score["BATCH_ENGINE"] = score.get("BATCH_ENGINE", 0) + 3
        ev.append("runs as a scheduled job")
    if channel == "dialog_tcode" and users >= 20:
        score["WORKLIST"] = score.get("WORKLIST", 0) + 2
        ev.append(f"{users} people use it interactively")
    if channel == "dialog_tcode" and 0 < users <= 2 and execs > 500:
        score["WORKLIST"] = score.get("WORKLIST", 0) + 2
        ev.append(f"{execs:,} runs by {users} operator(s) — concentrated, key-person shaped")

    for kw, role, why in (
            ("CHECK", "CHECKER", "named as a check"),
            ("VALID", "CHECKER", "named as a validation"),
            ("DERIV", "CHECKER", "named as a derivation"),
            ("CREATE", "MASTER_DATA_MAINTENANCE", "named as a create"),
            ("CHANGE", "MASTER_DATA_MAINTENANCE", "named as a change"),
            ("MAINTAIN", "MASTER_DATA_MAINTENANCE", "named as maintenance"),
            ("DISPLAY", "REPORT", "named as a display"),
            ("LIST", "REPORT", "named as a list"),
            ("GET", "REPORT", "named as a getter"),
            ("POST", "POSTING_ENGINE", "named as a posting"),
            ("PING", "TECHNICAL", "connectivity probe"),
            ("SESSION", "TECHNICAL", "session handling"),
            ("COMMIT", "TECHNICAL", "transaction control")):
        if kw in name.upper() or kw in t:
            score[role] = score.get(role, 0) + 1
            ev.append(why)

    if not score:
        return "UNKNOWN", 0.0, ["no signal"]
    role = max(score, key=score.get)
    top = score[role]
    rival = sorted(score.values(), reverse=True)
    margin = top - (rival[1] if len(rival) > 1 else 0)
    conf = min(0.95, 0.4 + 0.15 * top + 0.1 * margin)
    return role, round(conf, 2), ev[:4]


def main():
    state = load(STATE)
    objects = state.get("objects", {})
    emap = load(EMAP)
    texts = (load(TEXTS) or {}).get("objects", {})

    exec_by_obj = {}
    for dom, lst in emap.get("top_objects_by_domain", {}).items():
        for o in lst:
            exec_by_obj[o["object"]] = {**o, "domain": dom}

    roles, by_domain = {}, defaultdict(Counter)
    for name, obj in objects.items():
        ex = exec_by_obj.get(name)
        txt = (texts.get(name) or {}).get("text")
        role, conf, ev = derive(name, obj, ex, txt)
        if role == "UNKNOWN":
            continue
        dom = (ex or {}).get("domain") or resolve_domain(name).get("domain")
        roles[name] = {"role": role, "confidence": conf, "evidence": ev,
                       "domain": dom, "execs": (ex or {}).get("execs"),
                       "users": (ex or {}).get("users"), "text": txt}
        if dom:
            by_domain[dom][role] += 1

    # the reading that a list of names cannot give
    findings = []
    for dom, c in by_domain.items():
        if c["REPORT"] and not (c["POSTING_ENGINE"] or c["MASTER_DATA_MAINTENANCE"]):
            findings.append({"domain": dom, "finding": "CONSUMED, NOT OPERATED",
                             "detail": f"{c['REPORT']} reader(s), no writer — the data is "
                                       f"produced somewhere else"})
        if c["INTERFACE"] and c["INTERFACE"] >= max(c.values()):
            findings.append({"domain": dom, "finding": "DRIVEN FROM OUTSIDE",
                             "detail": f"{c['INTERFACE']} interface object(s) dominate — this "
                                       f"domain is operated by a satellite, not by people here"})
    for name, r in roles.items():
        if r["role"] == "WORKLIST" and (r.get("users") or 99) <= 2 and (r.get("execs") or 0) > 1000:
            findings.append({"domain": r["domain"], "finding": "KEY-PERSON RISK",
                             "detail": f"{name}: {r['execs']:,} runs by {r['users']} operator(s)"})

    out = {
        "_generated_by": "process_mining/derive_object_roles.py",
        "_question": "what is each object FOR — not just where does it belong",
        "_why": ("'PBC has 33 objects' is not knowledge. 'PBC has 2 posting engines, 14 "
                 "reports and one operator running the worklist' is. A domain with readers "
                 "and no writer is CONSUMED, not operated — and no list of names can say that."),
        "_roles": ROLES,
        "_caveat": ("a role is a HYPOTHESIS with a confidence, like every derived answer "
                    "here. A report that writes a log table looks like a writer; the "
                    "evidence is returned so a reader can disagree."),
        "coverage": {"objects_with_a_role": len(roles),
                     "by_role": dict(Counter(r["role"] for r in roles.values()))},
        "findings": findings[:20],
        "by_domain": {d: dict(c) for d, c in sorted(
            by_domain.items(), key=lambda x: -sum(x[1].values()))},
        "objects": roles,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"  {len(roles)} objects now carry a role")
    for r, n in Counter(x["role"] for x in roles.values()).most_common():
        print(f"    {r:26s} {n}")
    if findings:
        print("\n  WHAT THE ROLES REVEAL:")
        seen = set()
        for f in findings:
            k = (f["domain"], f["finding"])
            if k in seen:
                continue
            seen.add(k)
            print(f"    [{f['finding']}] {f['domain']}: {f['detail'][:78]}")


if __name__ == "__main__":
    main()
