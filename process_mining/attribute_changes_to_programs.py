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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from caller_parse import parse as parse_caller  # noqa: E402

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "process_mining"))
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except Exception:
    _aprendido = None
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
# The SHARED aggregate. Both streams this algorithm needs are pre-collapsed and INDEXED in
# brain_v2/build_audit_slots.py — 15.6M audit rows to 987K slots, 12M change rows to 507K
# groups. Reading it turns a full unindexed scan of a 13 GB database into a keyed lookup.
# The golden itself cannot be indexed: it is 13 GB, gitignored and UNBACKED, so an index
# write risks an extraction that cannot be reproduced.
SLOTS = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "derived_audit_slots.db"
OUT = REPO / "brain_v2" / "change_attribution.json"
# The DECLARED channel taxonomy — 48 flows across 8 channels, already documented and now
# structured (brain_v2/build_channel_registry.py). This algorithm DERIVES a channel from the
# logs; the registry says what we already documented. Comparing them is the point: agreement
# confirms, disagreement is a finding on one side. Re-deriving it in ignorance was the
# mistake this lookup prevents.
DECLARED = REPO / "brain_v2" / "integration_channels.json"

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

# The runtimes that PROCESS the other two write channels. Detecting them needs no new
# extraction — they run as ordinary programs and are already in the log.
BATCH_INPUT_PROGS = ("RSBDC", "SAPMSBDC")   # replay a recorded screen session (APQI/APQD)
WEBSERVICE_PROGS = ("SAPLSRT", "SOAP", "WSPROC")   # the SOAP runtime
# ...but NOT its housekeeping. The first version matched "SRT_" and immediately scored
# WEBSERVICE at 0.99 on two classes, naming SRT_CCMS_DATA_COLL_LOW_FREQ,
# SRT_SEQ_DELETE_BGRFC_QUEUES and SRT_UTIL_CLEANUP as the evidence. Those are CCMS
# monitoring and queue cleanup — they run constantly and process no inbound call. It is
# the dispatcher problem in SOAP clothing: detecting the plumbing and calling it the
# channel. A near-certain confidence built on housekeeping is worse than no detection,
# because it reads as proof.
WEBSERVICE_HOUSEKEEPING = ("SRT_CCMS", "SRT_SEQ_DELETE", "SRT_UTIL", "SRT_ADMIN")


def _profile(con, _derived=False):
    """Both streams, aggregated in SQL before anything reaches Python (pattern D6).

    12M change rows and 15.6M audit rows. Resolving either row by row is the defect this
    project already measured at 548x wasted work.
    """
    changes = defaultdict(lambda: defaultdict(set))    # class -> user -> {(day,hour)}
    volume = defaultdict(int)
    user_vol = defaultdict(lambda: defaultdict(int))
    tcodes = defaultdict(lambda: defaultdict(int))     # class -> tcode -> rows
    for cls, user, day, hh, tc, n in con.execute(
            "SELECT objectclas, username, day, hh, tcode, SUM(n) "
            "FROM changes GROUP BY 1,2,3,4,5" if _derived else
            "SELECT OBJECTCLAS, USERNAME, UDATE, substr(UTIME,1,2), TCODE, COUNT(*) "
            "FROM cdhdr_history WHERE UDATE <> '' GROUP BY 1,2,3,4,5"):
        changes[cls][user].add((day, hh))
        volume[cls] += n
        user_vol[cls][user] += n
        tcodes[cls][tc or ""] += n

    # ONE PASS over the audit log, not four.
    #
    # The channel evidence was first added as three extra full scans — an RFC probe, two
    # LIKE scans for file paths, and a PARAMX group-by over 8.7M rows — on top of the scan
    # that was already there. None of them can use an index, and the golden database is
    # READ-ONLY BY CONTRACT so an index cannot be added. The run went from minutes to over
    # an hour, and that is a correctness problem, not a comfort one: A SLOW ALGORITHM GETS
    # SKIPPED, AND A SKIPPED ALGORITHM IS DOCUMENTATION (pattern D6). A8 runs inside the
    # analysis cycle, so its cost is paid on every domain, every time.
    #
    # The fix is to ask for the SIGNALS in the same scan rather than the raw values: a
    # CASE per signal collapses to a flag inside the existing GROUP BY and costs nothing
    # extra. The raw values — which paths, which calling host — are only ever needed for the
    # handful of accounts that end up ranked first, so those became TARGETED lookups after
    # the ranking instead of full scans before it.
    rfc_slots = defaultdict(set)                       # user -> {(day,hour)} with an RFC call
    file_slots = defaultdict(set)                      # user -> {(day,hour)} touching a file
    runs = defaultdict(lambda: defaultdict(set))       # user -> program -> {(day,hour)}
    prog_slots = defaultdict(set)                      # program -> {(day,hour)}  BASE RATE
    all_slots = set()
    for user, prog, day, hh, is_rfc, is_file in con.execute(
            "SELECT user, prog, day, hh, is_rfc, is_file FROM slots" if _derived else
            "SELECT SLGUSER, SLGREPNA, SAL_DATE, substr(SAL_TIME,1,2), "
            "       MAX(CASE WHEN PARAM3 <> '' THEN 1 ELSE 0 END), "
            "       MAX(CASE WHEN PARAM3 LIKE '%/%' OR PARAM3 LIKE '%.XLS%' "
            "                  OR PARAM3 LIKE '%.CSV%' OR PARAM3 LIKE '%.TXT%' "
            "                  OR PARAM3 LIKE '%.DAT%' THEN 1 ELSE 0 END) "
            "FROM rsau_audit_history WHERE SAL_DATE <> '' GROUP BY 1,2,3,4"):
        slot = (day, hh)
        all_slots.add(slot)
        if is_rfc:
            rfc_slots[user].add(slot)
        if is_file:
            file_slots[user].add(slot)
        if prog:
            runs[user][prog].add(slot)
            prog_slots[prog].add(slot)

    # BATCH evidence. A job fires a program; the program writes. The user's concrete case:
    # Coupa drops a file in a folder, a scheduled job processes it, the program posts. Any
    # classification that stops at "a program wrote it" loses the three links outside SAP.
    #
    # This reads the GOLDEN directly even on the fast path. The first version returned an
    # empty map whenever the pre-aggregate was used, so BATCH_JOB evidence vanished — and
    # "no job channel" would have read as a fact about the tenant rather than as a fact
    # about which connection happened to be open. `tbtcp` is small; there is no reason to
    # trade the channel away for it. A faster path that silently answers a different
    # question is the failure this whole session has been chasing.
    jobs_of_prog = defaultdict(lambda: defaultdict(int))   # program -> job -> runs
    jcon = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True) if _derived else con
    try:
        for prog, job, n in jcon.execute(
                "SELECT p.PROGNAME, p.JOBNAME, COUNT(*) FROM tbtcp p "
                "WHERE p.PROGNAME <> '' GROUP BY 1,2"):
            jobs_of_prog[prog][job] += n
    except sqlite3.Error as e:
        print(f"  [A8] batch evidence unavailable: {e}")
    finally:
        if _derived:
            jcon.close()

    return (changes, volume, user_vol, tcodes, runs, prog_slots, rfc_slots, file_slots,
            jobs_of_prog, all_slots)


def phi(a, b, c, d):
    """Association over a 2x2 contingency table. 0 when any margin collapses."""
    den = ((a + b) * (c + d) * (a + c) * (b + d)) ** 0.5
    return ((a * d - b * c) / den) if den else 0.0


def _declared():
    """artifact -> the channel we already documented for it."""
    if not DECLARED.exists():
        return {}
    try:
        return (json.load(open(DECLARED, encoding="utf-8")).get("by_artifact") or {})
    except (json.JSONDecodeError, OSError):
        return {}


def resolve_channels(tc_hist, top_programs, ev):
    """How the writes ARRIVE — as a CHAIN, not a label.

    A single label loses the links outside SAP. The concrete case that forced this: bank
    statements and postings originate in COUPA, which writes a FILE into a folder; a
    scheduled JOB processes it; the PROGRAM posts. Stopping at "a program wrote it"
    discards three links and the whole external origin.

    So every channel with evidence is reported, each with what proves it:

        DIALOG        the change carries a transaction code — a person in a screen
        RFC_INBOUND   the account was making function calls in those hours; PARAMX names
                      the CALLING host/destination, which is the satellite
        FILE          a path appears where a function module should be — a program reading
                      a directory, which is how an external system delivers
        BATCH_JOB     a scheduled job runs the candidate program — the trigger, not the writer
        PROGRAM       none of the above: a report or engine run directly

    `ev` carries the measured shares and names. Returned newest-evidence-first, with the
    chain narrated when more than one link is present.
    """
    total = sum(tc_hist.values()) or 1
    blank = tc_hist.get("", 0) / total
    found = []

    if blank < 0.65:
        found.append({"channel": "DIALOG", "confidence": round(1 - blank, 2),
                      "evidence": f"{100 * (1 - blank):.0f}% of changes carry a transaction code"})
    if ev.get("rfc_share", 0) >= 0.35:
        origins = ev.get("origins") or []
        found.append({"channel": "RFC_INBOUND", "confidence": round(ev["rfc_share"], 2),
                      "evidence": (f"the responsible account was making function calls in "
                                   f"{100 * ev['rfc_share']:.0f}% of the hours this class "
                                   f"changed"),
                      "called_from": origins[:4],
                      "_why_it_matters": ("PARAMX names the calling host/destination — this "
                                          "is the satellite that owns the write")})
    if ev.get("file_share", 0) >= 0.15:
        found.append({"channel": "FILE", "confidence": round(ev["file_share"], 2),
                      "evidence": (f"file paths appear in {100 * ev['file_share']:.0f}% of the "
                                   f"hours this class changed — a program reading a directory"),
                      "paths": (ev.get("paths") or [])[:4],
                      "_why_it_matters": ("a file in a folder is how an external system "
                                          "delivers. Find who writes the folder")})
    if ev.get("jobs"):
        found.append({"channel": "BATCH_JOB", "confidence": 0.6,
                      "evidence": "a scheduled job runs the candidate program",
                      "jobs": ev["jobs"][:4],
                      "_why_it_matters": "the job is the TRIGGER; the program is the writer"})
    # BATCH INPUT and WEB SERVICE are write channels in their own right, and leaving them
    # out made this algorithm structurally blind to two of the ways a change actually
    # arrives. Neither needs a new extraction: the audit log already carries the runtime
    # that processes them — RSBDC*/SAPMSBDC* replay a recorded session, SRT_*/SAPLSRT* is
    # the SOAP runtime — so the same slots that prove an RFC channel prove these.
    #
    # Their detail lives elsewhere (APQI/APQD for the session, the SRT logs for the
    # message), which is why the DECLARED web services could not be found among programs
    # earlier. That was the wrong log, not an absent interface — and calling them unused
    # would have repeated the error that produced six wrong module answers this session.
    if ev.get("batch_input_share", 0) >= 0.10:
        found.append({"channel": "BATCH_INPUT", "confidence": round(ev["batch_input_share"], 2),
                      "evidence": (f"a batch-input processor ran in "
                                   f"{100 * ev['batch_input_share']:.0f}% of the hours this "
                                   f"class changed"),
                      "processors": (ev.get("batch_input_progs") or [])[:4],
                      "_why_it_matters": ("a recorded SCREEN SESSION replayed — it writes as "
                                          "if a person typed it, so it carries a transaction "
                                          "code and hides among dialog changes. The session "
                                          "detail is in APQI/APQD, not here")})
    if ev.get("webservice_share", 0) >= 0.10:
        found.append({"channel": "WEBSERVICE", "confidence": round(ev["webservice_share"], 2),
                      "evidence": (f"the SOAP runtime ran in "
                                   f"{100 * ev['webservice_share']:.0f}% of the hours this "
                                   f"class changed"),
                      "runtime": (ev.get("webservice_progs") or [])[:4],
                      "_why_it_matters": ("an inbound web service writes with no transaction "
                                          "and no RFC destination. Which SERVICE it was is in "
                                          "the SRT logs, which are NOT extracted — so this "
                                          "names the channel and cannot yet name the caller")})
    elif ev.get("webservice_housekeeping"):
        # Say what we CANNOT see, rather than let silence read as absence. Four declared
        # web services exist; this log cannot confirm or refute any of them.
        found.append({"channel": "WEBSERVICE_UNDETECTABLE", "confidence": 0.0,
                      "evidence": ("only SOAP HOUSEKEEPING ran in these hours (CCMS "
                                   "collection, queue cleanup) — that is the plumbing, not "
                                   "an inbound call"),
                      "_why_it_matters": ("this log answers for PROGRAMS. An inbound web "
                                          "service is processed by the ICF/SRT runtime and "
                                          "logged in SRT_UTIL / SRTUTIL, which are NOT "
                                          "extracted. UNVERIFIED is the honest verdict here, "
                                          "never 'not used' — that is the wrong-log error")})
    if not found:
        found.append({"channel": "PROGRAM", "confidence": round(blank, 2),
                      "evidence": (f"{100 * blank:.0f}% of changes have no transaction code and "
                                   f"no interface, file or job evidence — a report or engine "
                                   f"run directly")})

    # DECLARED is NOT resolved here. This function derives from the logs and nothing
    # else; testing the documented claim belongs in check_declared(), separately, so
    # that a sentence in a markdown table can never be laundered into a measurement.
    names = [f["channel"] for f in found]
    chain = None
    if "FILE" in names and "BATCH_JOB" in names:
        chain = ("EXTERNAL SYSTEM -> file in a folder -> scheduled job -> program -> SAP. "
                 "The origin is outside SAP: find who writes the folder.")
    elif "RFC_INBOUND" in names:
        chain = ("EXTERNAL CALLER -> RFC/BAPI -> SAP. The transaction code is empty because "
                 "the interface design never set one, not because it was a batch run.")
    elif "BATCH_INPUT" in names:
        chain = ("a RECORDED SCREEN SESSION replayed -> SAP. It writes as if a person typed "
                 "it, so it can carry a transaction code and pass for a dialog change. The "
                 "session and its source are in APQI/APQD.")
    elif "WEBSERVICE" in names:
        chain = ("EXTERNAL CALLER -> SOAP/HTTP -> SAP. No transaction and no RFC destination; "
                 "the caller is in the SRT logs, which are not extracted.")
    elif "BATCH_JOB" in names:
        chain = "scheduled job -> program -> SAP"
    return found, chain


def check_declared(top_programs, derived, declared, extra_names=None):
    """The documented channel is a HYPOTHESIS. This is where it gets tested.

    Prose on its own is worth nothing. The integration map says a given program carries a
    given channel from a given source; that is a claim to VERIFY against what the logs
    show, never evidence to add alongside it. Adding it would launder a document into a
    measurement and make the two impossible to tell apart afterwards.

    Three verdicts, and the middle one is the valuable one:

        CONFIRMED      the logs show the channel the map declares
        CONTRADICTED   the logs show a different channel — one of the two is wrong, and
                       until now there was no way to even have the disagreement
        UNVERIFIED     the map declares it and the logs are silent here; it stays a claim
    """
    got = {c["channel"] for c in derived}
    out = []
    # MATCH ON BOTH NAME SPACES. The first version compared only PROGRAM names against a
    # registry keyed on FUNCTION MODULES and JOB names, so nothing ever matched: 72 classes,
    # 72 NOT_DECLARED, a check that looked like it worked and verified nothing. That is
    # worse than having no check, because the green result is trusted.
    candidates = [p["program"] for p in top_programs[:5]] + list(extra_names or [])
    for prog in candidates:
        for d in (declared or {}).get(prog, []):
            verdict = ("CONFIRMED" if d["channel"] in got
                       else ("CONTRADICTED" if got else "UNVERIFIED"))
            out.append({
                "artifact": prog, "declared_channel": d["channel"],
                "declared_source": d.get("source"), "declared_status": d.get("status"),
                "derived_channels": sorted(got), "verdict": verdict,
                "_why": ("the map is a claim; the logs are the check. A CONTRADICTED row "
                         "means the documentation and the system disagree, which is a "
                         "finding on one side or the other"),
            })
    return out


def _interface_functions(con, user, slots, limit=6):
    """For an INTERFACE channel, name the function modules called in the same slots."""
    if not slots:
        return []
    # keyed lookup against the shared aggregate. This used to hit the golden with a
    # SAL_DATE IN (...) over 15.6M unindexed rows, once per interface class — ten
    # "targeted" lookups that were ten more full scans. Materialised is not lazy.
    rows = con.execute(
        "SELECT fm, n FROM calls WHERE user = ? ORDER BY n DESC LIMIT 40",
        (user,)).fetchall()
    # A read is not a writer. RFC_PING, RFC_READ_TABLE and the connection probes appeared at
    # the top of the first run because the query returned everything the account called,
    # not what could have written. Names shorter than 4 characters are PARAM3 truncation,
    # not function modules.
    # Reads are not writers, and neither is the RFC plumbing. ARFC_* is the asynchronous
    # transport layer, SBUF_* resets buffers, SALC_* is monitoring — all of them ride along
    # with any RFC call, so they surface for every INTERFACE class and name nothing.
    NOT_A_WRITER = ("RFC_PING", "RFC_READ_TABLE", "RFCPING", "SYSTEM_", "SXPG_", "TH_",
                    "RFC_GET", "BAPI_TRANSACTION", "DDIF_", "SEO_", "SVRS_",
                    "ARFC_", "SBUF_", "SALC_", "SWW_", "SX_OBJECTS", "RFC_FUNCTION")
    out = []
    for f, n in rows:
        f = (f or "").strip()
        if (len(f) < 4 or f.startswith(NOT_A_WRITER) or "_GET" in f or "_READ" in f
                or not f[0].isalpha() or f.islower()):
            continue
        out.append({"function_module": f, "calls": n})
        if len(out) >= limit:
            break
    return out


def attribute(changes, volume, user_vol, tcodes, runs, prog_slots, rfc_slots, file_slots,
              jobs_of_prog, all_slots, classes=None, lookup_paths=None, lookup_origins=None):
    lookup_paths = lookup_paths or (lambda _u: [])
    lookup_origins = lookup_origins or (lambda _u: [])
    horizon = len(all_slots) or 1
    wanted = classes or [c for c, _ in
                         sorted(volume.items(), key=lambda x: -x[1])[:TOP_CLASSES]]
    out, claimed = {}, defaultdict(set)
    declared = _declared()
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
        top_user = cands[0]["user"] if cands else None
        cs = (changes[cls].get(top_user) or set()) & all_slots if top_user else set()
        ev = {
            "rfc_share": (len(cs & rfc_slots.get(top_user, set())) / len(cs)) if cs else 0.0,
            "file_share": (len(cs & file_slots.get(top_user, set())) / len(cs)) if cs else 0.0,
            "paths": lookup_paths(top_user) if top_user else [],
            "origins": lookup_origins(top_user) if top_user else [],
            "jobs": sorted({j for c in cands[:4]
                            for j in (jobs_of_prog.get(c["program"]) or {})})[:6],
        }
        # BATCH_INPUT and WEBSERVICE, derived from what is already in memory — the same
        # runs[] map that scores the writers. No extra query, no extra scan.
        uruns = runs.get(top_user) or {}
        for key, prefixes in (("batch_input", BATCH_INPUT_PROGS),
                              ("webservice", WEBSERVICE_PROGS)):
            hit, names = set(), []
            for prog, pslots in uruns.items():
                if key == "webservice" and prog.startswith(WEBSERVICE_HOUSEKEEPING):
                    continue
                if prog.startswith(prefixes):
                    inter = cs & pslots
                    if inter:
                        hit |= inter
                        names.append(prog)
            ev[f"{key}_share"] = (len(hit) / len(cs)) if cs else 0.0
            ev[f"{key}_progs"] = sorted(names)
        ev["webservice_housekeeping"] = sorted(
            p for p in uruns if p.startswith(WEBSERVICE_HOUSEKEEPING) and (cs & uruns[p]))[:4]
        chans, chain = resolve_channels(tcodes.get(cls) or {}, cands, ev)
        # DERIVED and DECLARED stay in SEPARATE fields on purpose. Merging them would
        # launder a document into a measurement, and afterwards nobody could tell which was
        # which. The verdict is the third thing, and it is the one worth reading.
        checks = check_declared(cands, chans, declared)  # re-checked in main() with the
        # function modules, which live in a different name space than the programs
        verdicts = sorted({c["verdict"] for c in checks}) or ["NOT_DECLARED"]
        out[cls] = {
            "change_documents": volume[cls], "users": len(by_user),
            "channels_DERIVED_from_logs": chans,
            "channels_DECLARED_in_the_map": checks or None,
            "verdict": verdicts,
            "chain": chain,
            "channel": chans[0]["channel"],
            "channels": chans,
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
    # LO APRENDIDO, ANTES DE MINAR — no despues. Los temas son las dos corrientes que este
    # algoritmo cruza y los campos de los que cuelga su respuesta: cdhdr_history (el log de
    # cambios), rsau_audit_history (el de ejecucion), SLGREPNA (que la memoria dice que NO
    # lleva el modulo de funcion de una RFC: solo el despachador), TCODE (que NO distingue
    # batch input de job de fondo), OBJECTCLAS y SAPMSSY1. Un aviso que llega al final no
    # sirve: para entonces la conexion esta cerrada y lo que queda es buena intencion.
    if _aprendido:
        _aprendido("cdhdr_history", "rsau_audit_history", "slgrepna", "tcode",
                   "objectclas", "sapmssy1").avisar()
    if not GOLD.exists():
        print(f"golden not found: {GOLD}", file=sys.stderr)
        return 1
    # prefer the shared aggregate; fall back to the raw golden so the algorithm still works
    # on an installation where it has not been built yet
    derived = SLOTS.exists()
    con = sqlite3.connect(f"file:{SLOTS if derived else GOLD}?mode=ro", uri=True)
    print("  reading the SHARED AGGREGATE (indexed)" if derived else
          "  scanning the raw golden — run brain_v2/build_audit_slots.py to make this fast")
    (changes, volume, user_vol, tcodes, runs, prog_slots, rfc_slots, file_slots,
     jobs_of_prog, all_slots) = _profile(con, derived)
    # TWO connections on purpose. The bulk read comes from the shared aggregate; the
    # targeted lookups — which function modules, which calling host, which job — need the
    # raw values and run only for the handful of accounts that ranked first, so they stay
    # on the golden where those values live. Cheap because they are keyed, not scanned.
    gold = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True) if derived else con
    if derived:
        for prog, job, n in gold.execute(
                "SELECT p.PROGNAME, p.JOBNAME, COUNT(*) FROM tbtcp p "
                "WHERE p.PROGNAME <> '' GROUP BY 1,2"):
            jobs_of_prog[prog][job] += n
    print(f"  {len(volume)} object classes · {len(prog_slots):,} programs · "
          f"{len(all_slots):,} hour-slots in the shared window")

    declared_map = _declared()
    def _paths(u):
        return [r[0] for r in con.execute(
            "SELECT path FROM paths WHERE user = ? ORDER BY n DESC LIMIT 6", (u,))]             if derived else []

    def _origins(u):
        out = []
        for (px,) in con.execute(
                "SELECT origin FROM origins WHERE user = ? ORDER BY n DESC LIMIT 20", (u,))                 if derived else []:
            d, h, _u = parse_caller(px)
            tag = d if d and d != "NONE" else h
            if tag and tag not in out:
                out.append(tag)
        return out[:4]

    result = attribute(changes, volume, user_vol, tcodes, runs, prog_slots, rfc_slots,
                       file_slots, jobs_of_prog, all_slots,
                       lookup_paths=_paths, lookup_origins=_origins,
                       classes=sys.argv[1:] or None)

    # for every INTERFACE class, name the functions — this is the hand-off to F1/F2
    for cls, r in result.items():
        if (not any(c["channel"] == "RFC_INBOUND" for c in r["channels_DERIVED_from_logs"])
                or not r["candidate_writers"]):
            continue
        top = r["candidate_writers"][0]
        slots = (changes[cls].get(top["user"]) or set()) & all_slots
        r["interface_functions"] = _interface_functions(con, top["user"], slots)
    if derived:
        gold.close()
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
        chans = " + ".join(c["channel"] for c in r["channels_DERIVED_from_logs"])
        print(f"\n  {cls}  ({r['change_documents']:,} changes)  DERIVED: {chans}")
        if r.get("chain"):
            print(f"    chain: {r['chain']}")
        for c in r["channels_DERIVED_from_logs"]:
            extra = (c.get("called_from") or c.get("paths") or c.get("jobs") or [])
            if extra:
                print(f"      {c['channel']:12s} {', '.join(str(x)[:32] for x in extra[:3])}")
        for v in (r.get("channels_DECLARED_in_the_map") or [])[:3]:
            print(f"      MAP SAYS {v['declared_channel']} via {v['artifact'][:20]} "
                  f"({v['declared_source']})  ->  {v['verdict']}")
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
