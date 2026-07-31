"""attribute_changes_to_programs.py — ALGORITHM A8: who WRITES this, and through which
channel (s097).

The model could say that an object class changed and who the user was. It could not say
**what did the writing** — and that is the question that turns a change log into behaviour.
93% of PBC's change documents carry an EMPTY transaction code: something wrote them, and no
field records what.

**The move.** Two streams the tenant already produces, joined on (user, day, HOUR):

    CHANGE STREAM     cdhdr_history   who changed WHICH OBJECT CLASS, when
    EXECUTION STREAM  rsau_audit      who ran WHICH PROGRAM, when

Nothing here is SAP-specific beyond the two table names. Any state-change log crossed with
any execution log yields the same attribution: which program sends this IDoc type, which
job produces this file, which process touches this interface.

---

## Three scoring attempts, because the first two were wrong

**1 · Raw coincidence.** Worthless. `SAPMSSY1`, the RFC dispatcher, runs constantly and
coincides with everything. It named a *spool artifact* as the writer of the largest object
class in the system.

**2 · Lift** — `P(ran | changed) / P(ran)` — removes that, and introduces the opposite
error. It ranked `HUNCALC0`, the actual PBC engine, below noise and filtered it out at a
1.5 threshold: `HUNCALC0` runs on 91 of 108 days, so its base rate is 0.84 and its lift
cannot exceed 1.19 however perfect the coincidence. **Lift rewards rarity, and a dedicated
engine is not rare — it runs whenever the class changes, which is what makes it the
engine.**

**3 · The φ coefficient** over the 2×2 contingency table of TIME SLOTS:

    a = slots where the class changed AND the program ran     c = changed, did not run
    b = ran, class did not change                             d = neither

    φ = (ad − bc) / √((a+b)(c+d)(a+c)(b+d))

φ is symmetric — it weighs how much of the change activity a program covers *and* how
specific it is — and corrects for both base rates at once. A program running in every slot
has `d = 0`, the denominator collapses, and it scores nothing.

## Two constraints that make the answer an assignment, not a ranking

**Time, not day.** At day granularity every program in the same nightly chain ties. The
slot is `(day, hour)`, which both logs carry, so a class that changes at 19h separates from
one that changes at 09h.

**Exclusivity.** A program that scores against forty classes has explained none of them.
After scoring, each program is counted across classes and carries `claimed_by_n_classes`;
one that is claimed broadly is reported as AMBIGUOUS. Attributing the same writer to every
table is the failure this constraint exists to prevent.

## The empty transaction code is a finding, not a gap

An empty `TCODE` does not mean batch. **It usually means the write came through a BAPI or
RFC, where the interface design never set one.** So the dispatcher appearing at the top is
not noise to filter — it is the signal that the channel is an INTERFACE, and the next
question (*which function?*) is answerable from `PARAM3` in the same audit rows. Each class
is therefore classified by CHANNEL — DIALOG · PROGRAM · INTERFACE — and for INTERFACE the
calling function modules are named, which is where this joins F1 (interface boundary) and
F2 (satellites).

**What it cannot do.** Co-occurrence is not causation, and this never claims it is. The
output is a ranked hypothesis with its evidence attached, for a human to confirm.

Emits: brain_v2/change_attribution.json
Run:   python process_mining/attribute_changes_to_programs.py [OBJECTCLAS ...]
"""
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = REPO / "brain_v2" / "change_attribution.json"

MIN_CHANGE_SLOTS = 8     # an association computed from a handful of slots is a coincidence
MIN_COINCIDENT = 5       # small-denominator ratios are noise with a decimal point (see D6)
MIN_PHI = 0.15
MIN_USER_SHARE = 0.02    # only users carrying weight in a class can testify about it
TOP_CLASSES = 999   # all of them: the trigger asks about every class that changes
AMBIGUOUS_AT = 5         # claimed by this many classes or more => explains none of them

# `SLGREPNA` is not always a program: spool and job artifacts land in it, and
# `!QGYAO==========A_SEFI0410` was once ranked first.
NOT_A_PROGRAM = ("!", "=", " ")

# The RFC/CPIC dispatchers. Their presence is EVIDENCE OF AN INTERFACE CHANNEL, not noise.
DISPATCHERS = {"SAPMSSY1", "SAPMSSY6", "SAPLSYST", "SAPMSSYD"}


def _profile(con):
    """Both streams, aggregated in SQL before anything reaches Python (pattern D6).

    12M change rows and 15.6M audit rows. Resolving either row by row is the defect this
    project already measured at 548x wasted work.
    """
    changes = defaultdict(lambda: defaultdict(set))    # class -> user -> {(day,hour)}
    volume = defaultdict(int)
    user_vol = defaultdict(lambda: defaultdict(int))
    tcodes = defaultdict(lambda: defaultdict(int))     # class -> tcode -> rows
    for cls, user, day, hh, tc, n in con.execute(
            "SELECT OBJECTCLAS, USERNAME, UDATE, substr(UTIME,1,2), TCODE, COUNT(*) "
            "FROM cdhdr_history WHERE UDATE <> '' GROUP BY 1,2,3,4,5"):
        changes[cls][user].add((day, hh))
        volume[cls] += n
        user_vol[cls][user] += n
        tcodes[cls][tc or ""] += n

    runs = defaultdict(lambda: defaultdict(set))       # user -> program -> {(day,hour)}
    prog_slots = defaultdict(set)                      # program -> {(day,hour)}  BASE RATE
    all_slots = set()
    for user, prog, day, hh in con.execute(
            "SELECT SLGUSER, SLGREPNA, SAL_DATE, substr(SAL_TIME,1,2) "
            "FROM rsau_audit_history WHERE SAL_DATE <> '' AND SLGREPNA <> '' GROUP BY 1,2,3,4"):
        slot = (day, hh)
        runs[user][prog].add(slot)
        prog_slots[prog].add(slot)
        all_slots.add(slot)
    return changes, volume, user_vol, tcodes, runs, prog_slots, all_slots


def phi(a, b, c, d):
    """Association over a 2x2 contingency table. 0 when any margin collapses."""
    den = ((a + b) * (c + d) * (a + c) * (b + d)) ** 0.5
    return ((a * d - b * c) / den) if den else 0.0


def _channel(tc_hist, top_programs):
    """DIALOG · PROGRAM · INTERFACE — how the writes actually arrive.

    An empty TCODE is not 'batch'. It usually means a BAPI or RFC whose interface design
    never set one, so the dispatcher ranking high is the evidence, not the noise.
    """
    total = sum(tc_hist.values()) or 1
    blank = tc_hist.get("", 0) / total
    dispatcher_led = bool(top_programs) and top_programs[0]["program"] in DISPATCHERS
    if blank < 0.35:
        return "DIALOG", f"{100 * (1 - blank):.0f}% of changes carry a transaction code"
    if dispatcher_led or any(p["program"] in DISPATCHERS for p in top_programs[:2]):
        return "INTERFACE", (f"{100 * blank:.0f}% of changes have NO transaction code and an "
                             f"RFC dispatcher is among the top associates — a BAPI/RFC whose "
                             f"design left the tcode empty")
    return "PROGRAM", (f"{100 * blank:.0f}% of changes have no transaction code and the top "
                       f"associates are named programs — written by a report or engine")


def _interface_functions(con, user, slots, limit=6):
    """For an INTERFACE channel, name the function modules called in the same slots."""
    if not slots:
        return []
    days = sorted({d for d, _ in slots})[:40]
    qs = ",".join("?" * len(days))
    rows = con.execute(
        f"SELECT PARAM3, COUNT(*) n FROM rsau_audit_history "
        f"WHERE SLGUSER = ? AND SAL_DATE IN ({qs}) AND PARAM3 <> '' "
        f"GROUP BY 1 ORDER BY n DESC LIMIT ?", [user] + days + [limit]).fetchall()
    return [{"function_module": f, "calls": n} for f, n in rows]


def attribute(changes, volume, user_vol, tcodes, runs, prog_slots, all_slots, classes=None):
    horizon = len(all_slots) or 1
    wanted = classes or [c for c, _ in
                         sorted(volume.items(), key=lambda x: -x[1])[:TOP_CLASSES]]
    out, claimed = {}, defaultdict(set)
    for cls in wanted:
        by_user = changes.get(cls) or {}
        if not by_user:
            continue
        total = volume[cls] or 1
        cands = []
        for user, cslots in by_user.items():
            share = user_vol[cls][user] / total
            if share < MIN_USER_SHARE:
                continue
            # only slots inside the window BOTH logs cover — otherwise a class that changed
            # before the audit log begins scores zero against everything, which reads as
            # "nothing wrote it" when it means "we cannot see"
            cslots = cslots & all_slots
            if len(cslots) < MIN_CHANGE_SLOTS:
                continue
            for prog, pslots in (runs.get(user) or {}).items():
                if prog.startswith(NOT_A_PROGRAM):
                    continue
                a = len(cslots & pslots)
                if a < MIN_COINCIDENT:
                    continue
                b, c = len(pslots - cslots), len(cslots - pslots)
                p = phi(a, b, c, horizon - a - b - c)
                if p < MIN_PHI:
                    continue
                cands.append({
                    "program": prog, "user": user,
                    "user_share_of_class": round(share, 3),
                    "phi": round(p, 3),
                    "change_slots": len(cslots), "coincident_slots": a,
                    "covers": round(a / len(cslots), 3),
                    "program_base_rate": round(len(pslots) / horizon, 4),
                    "_reads_as": (f"ran in {a} of the {len(cslots)} hours this class changed, "
                                  f"and in {b} hours it did not"),
                })
        # rank by association WEIGHTED BY the witness's share: a strong signal from the
        # account authoring 95% of the changes outranks the same signal from one authoring
        # 2%. phi asks "are these associated"; the weight asks "associated for the people
        # actually doing the work".
        cands.sort(key=lambda x: (-(x["phi"] * x["user_share_of_class"]),
                                  -x["coincident_slots"]))
        for c in cands[:8]:
            claimed[c["program"]].add(cls)
        ch, why = _channel(tcodes.get(cls) or {}, cands)
        out[cls] = {
            "change_documents": volume[cls], "users": len(by_user),
            "channel": ch, "channel_evidence": why,
            "candidate_writers": cands[:8],
        }

    # EXCLUSIVITY, applied after every class is scored: a program claimed by many classes
    # has explained none of them. This is what stops one writer being attributed to every
    # table — the answer has to behave like an assignment, not like N independent rankings.
    for cls, r in out.items():
        for c in r["candidate_writers"]:
            n = len(claimed[c["program"]])
            c["claimed_by_n_classes"] = n
            if n >= AMBIGUOUS_AT:
                c["verdict"] = "AMBIGUOUS — associated with many classes, explains none"
            elif c["program"] in DISPATCHERS:
                c["verdict"] = ("DISPATCHER — not the writer itself; evidence the write "
                                "arrived over RFC/BAPI. See the function modules below")
            else:
                c["verdict"] = "CANDIDATE WRITER"
        r["exclusive_candidates"] = [c["program"] for c in r["candidate_writers"]
                                     if c.get("verdict") == "CANDIDATE WRITER"]
    return out


def main():
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    print("  aggregating both streams in SQL, at (day, hour) ...")
    changes, volume, user_vol, tcodes, runs, prog_slots, all_slots = _profile(con)
    print(f"  {len(volume)} object classes · {len(prog_slots):,} programs · "
          f"{len(all_slots):,} hour-slots in the shared window")

    result = attribute(changes, volume, user_vol, tcodes, runs, prog_slots, all_slots,
                       classes=sys.argv[1:] or None)

    # for every INTERFACE class, name the functions — this is the hand-off to F1/F2
    for cls, r in result.items():
        if r["channel"] != "INTERFACE" or not r["candidate_writers"]:
            continue
        top = r["candidate_writers"][0]
        slots = (changes[cls].get(top["user"]) or set()) & all_slots
        r["interface_functions"] = _interface_functions(con, top["user"], slots)
    con.close()

    json.dump({
        "_generated_by": "process_mining/attribute_changes_to_programs.py",
        "_algorithm": "A8 — change-to-executor attribution, with channel",
        "_the_move": ("join a STATE-CHANGE stream to an EXECUTION stream on (user, day, "
                      "hour). Generic: any change log against any execution log."),
        "_the_score": ("phi over the 2x2 slot contingency table. Raw coincidence names the "
                       "dispatcher as the writer of everything; LIFT then buries the real "
                       "engine because an engine is not rare. phi is symmetric and corrects "
                       "for both base rates."),
        "_exclusivity": ("a program claimed by >= %d classes is AMBIGUOUS. Attributing one "
                         "writer to every table is the failure this prevents." % AMBIGUOUS_AT),
        "_channel": ("an empty TCODE usually means a BAPI/RFC whose interface design never "
                     "set one — so the dispatcher ranking high is EVIDENCE of an interface "
                     "channel, and the calling functions are named."),
        "_not_causation": "a ranked hypothesis with its evidence, for a human to confirm",
        "shared_window_slots": len(all_slots),
        "classes": result,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"wrote {OUT}")
    for cls, r in sorted(result.items(), key=lambda x: -x[1]["change_documents"])[:7]:
        print(f"\n  {cls}  ({r['change_documents']:,} changes)  channel={r['channel']}")
        print(f"    {r['channel_evidence']}")
        for c in r["candidate_writers"][:3]:
            tag = c["verdict"].split(" —")[0]
            print(f"    {c['program'][:26]:26s} phi {c['phi']:>6.3f}  "
                  f"{c['coincident_slots']:>4}/{c['change_slots']:<4} h  "
                  f"[{c['user']} {100 * c['user_share_of_class']:.0f}%]  {tag}")
        for f in (r.get("interface_functions") or [])[:3]:
            print(f"      via RFC: {f['function_module'][:40]:40s} {f['calls']:,}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
