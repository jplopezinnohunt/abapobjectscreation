"""SHARED MEMORY BETWEEN ALGORITHMS — what one of them learned, all of them know.

THE PROBLEM IT SOLVES
    Every algorithm here discovers something about the SUBSTRATE it runs on: that a log is
    a filtered subset, that a connection dies after a dozen calls, that a designed column
    is blank in every row, that a custom table has a custom change-document object. Those
    discoveries used to live in whichever script found them — so the next algorithm
    rediscovered them, or worse, did not, and quietly drew a conclusion from an instrument
    it did not know was partial.

    `algorithms.json` records what each algorithm IS. This records what each algorithm
    LEARNED. They are different things and only the second one compounds.

THE RULE THAT MAKES IT TRUSTWORTHY
    A memory is an OBSERVATION WITH PROVENANCE, never an opinion: who learned it, from
    what evidence, in which session, and — the field that makes it useful to a machine
    rather than to a reader — what OTHER algorithms should do differently because of it.
    A memory with no `implication` is a note, and notes belong in prose.

USE
    from algorithm_memory import recall, remember
    for m in recall(subject="cdhdr_history"):  # what do we know about this instrument?
        ...
    remember(subject="fmifiit_full.MEASURE", fact="...", learned_by="A10",
             evidence="0 of 2,308,814 rows", implication="...")
"""

import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "algorithm_memory.json")

# A memory nobody can act on is a note. These are the fields that make it actionable.
REQUIRED = ("subject", "fact", "learned_by", "evidence", "implication")


def _load():
    if not os.path.exists(STORE):
        return {
            "_what_this_is": (
                "What the algorithms learned about the substrate they run on. Written by any "
                "algorithm, read by all of them. algorithms.json says what each algorithm IS; "
                "this says what each one LEARNED."),
            "_the_rule": (
                "every memory carries who learned it, from what evidence, and what other "
                "algorithms should do differently because of it. A memory with no implication "
                "is a note, and notes are not machine-actionable."),
            "_kinds": {
                "INSTRUMENT": "a log, table or channel and how far it can actually see",
                "SUBSTRATE": "how the system behaves under load — timeouts, drops, limits",
                "CARRIER": "a column or object that does or does not carry what it claims",
                "TRAP": "a way of reading the data that produces a confident wrong answer",
            },
            "memories": [],
        }
    return json.load(io.open(STORE, encoding="utf-8"))


def _save(d):
    json.dump(d, io.open(STORE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def remember(subject, fact, learned_by, evidence, implication, kind="INSTRUMENT",
             session=None, confidence="MEASURED"):
    """Record one observation. Re-learning the same thing UPDATES rather than duplicates."""
    d = _load()
    rec = {"subject": subject, "kind": kind, "fact": fact, "learned_by": learned_by,
           "evidence": evidence, "implication": implication, "confidence": confidence,
           "session": session}
    for i, m in enumerate(d["memories"]):
        if m["subject"] == subject and m["learned_by"] == learned_by:
            # A later run of the same algorithm on the same subject supersedes the earlier
            # one — the substrate changes, and a stale memory is worse than none.
            rec["supersedes_earlier_run"] = True
            d["memories"][i] = rec
            _save(d)
            return rec
    d["memories"].append(rec)
    _save(d)
    return rec


def recall(subject=None, kind=None, learned_by=None):
    """Everything known about a subject. Substring match — subjects are dotted paths."""
    out = []
    for m in _load()["memories"]:
        if subject and subject.lower() not in m["subject"].lower():
            continue
        if kind and m.get("kind") != kind:
            continue
        if learned_by and m.get("learned_by") != learned_by:
            continue
        out.append(m)
    return out


def instruments_for(kind_of_log):
    """Every store known to carry a given kind of evidence, and how far each one sees.

    This is what lets an algorithm stop hard-coding which log to read. It asks the memory
    which stores carry change evidence, and gets back the partial ones flagged as partial.
    """
    out = []
    for m in recall(kind="INSTRUMENT"):
        if kind_of_log.lower() in (m.get("carries") or m["subject"]).lower():
            out.append(m)
    return out


def summary():
    d = _load()
    by = {}
    for m in d["memories"]:
        by.setdefault(m.get("learned_by", "?"), []).append(m["subject"])
    return {"total": len(d["memories"]), "by_algorithm": {k: len(v) for k, v in by.items()}}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for m in recall(subject=sys.argv[1]):
            print("[%s] %s\n   %s\n   -> %s\n" % (m["learned_by"], m["subject"], m["fact"],
                                                  m["implication"]))
    else:
        s = summary()
        print("algorithm memory: %d observations" % s["total"])
        for k, n in sorted(s["by_algorithm"].items(), key=lambda x: -x[1]):
            print("   %-28s %d" % (k, n))
