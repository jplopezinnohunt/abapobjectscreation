"""build_channel_registry.py — the write-channel taxonomy, lifted out of prose (s097).

**The knowledge already existed and could not be used.** `knowledge/domains/Integration/
integration_map_complete.md` classifies every integration into eight channels — RFC, IDoc,
middleware, file-based jobs, batch input, LSMW, DBCON, HTTP/SOAP — with the source system,
the artifact that carries it, the volume and a verification status. It even records that
TULIP and UNESDIR arrive over a direct database connection and fail 93% of the time.

All of it in **markdown tables**. So:

- `brain_v2/interface_boundary.json` (F1) contains the string "channel" **zero times**. It
  discovers destinations and marks them LIVE / DEAD / UNDECLARED, and never says what KIND
  of channel any of them is.
- algorithm A8 was about to re-derive the same taxonomy from the audit log, from scratch,
  while the answer sat in a document nobody could query.

That is the failure this repository keeps re-committing: an analysis is done, written up
well, and never becomes structured — so the next question re-derives it, and the two answers
drift apart with no way to notice.

**This does not re-analyse anything.** It parses what is already written into records the
algorithms can consume, keyed by the ARTIFACT that carries the channel — a program, function
module or job name — because that is the key A8 has in hand when it asks "what wrote this,
and how did it arrive".

The derived and the declared then CHECK EACH OTHER: A8 says what the logs show, this says
what we documented. Disagreement is a finding on one side or the other, and until now there
was no way to have the disagreement at all.

Emits: brain_v2/integration_channels.json
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "knowledge" / "domains" / "Integration" / "integration_map_complete.md"
OUT = REPO / "brain_v2" / "integration_channels.json"

# the eight section headings, mapped to a canonical channel the algorithms can switch on
SECTION_CHANNEL = [
    (r"RFC", "RFC_INBOUND"),
    (r"IDoc", "IDOC"),
    (r"Middleware", "MIDDLEWARE"),
    (r"File-?Based", "FILE"),
    (r"Human-Uploaded|Batch-Input", "BATCH_INPUT"),
    (r"BDC", "BATCH_INPUT"),
    (r"LSMW", "LSMW"),
    (r"DBCON", "DBCON"),
    (r"HTTP|SOAP", "WEBSERVICE"),
]
# artifact names: ABAP objects, not prose
ARTIFACT = re.compile(r"`([A-Z_][A-Z0-9_/]{3,})`")


def channel_of(heading):
    for pat, ch in SECTION_CHANNEL:
        if re.search(pat, heading, re.I):
            return ch
    return None


def main():
    if not SRC.exists():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()

    flows, by_artifact, current = [], {}, None
    for ln in lines:
        if ln.startswith("### "):
            current = channel_of(ln)
            continue
        if not current or not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].lower() in ("#", "---") or set(cells[0]) <= set("-: "):
            continue
        row = {"channel": current, "row": cells[0]}
        # the table shape is consistent: # | Source | Target | Channel | Artifact | ...
        keys = ["source", "target", "declared_channel", "artifact", "what_it_does",
                "volume", "status"]
        for i, k in enumerate(keys, start=1):
            if i < len(cells):
                row[k] = re.sub(r"\*\*|`", "", cells[i]).strip()
        arts = ARTIFACT.findall(ln)
        row["artifacts"] = sorted(set(arts))
        if not row.get("source") or row["source"].lower() in ("source", ""):
            continue
        flows.append(row)
        for a in arts:
            by_artifact.setdefault(a, []).append(
                {"channel": current, "source": row.get("source"),
                 "status": row.get("status"), "what_it_does": row.get("what_it_does")})

    counts = {}
    for f in flows:
        counts[f["channel"]] = counts.get(f["channel"], 0) + 1

    json.dump({
        "_generated_by": "brain_v2/build_channel_registry.py",
        "_what_this_is": ("the write-CHANNEL taxonomy, parsed out of the integration map. "
                          "Not a new analysis — the same knowledge, made queryable."),
        "_why": ("the classification existed only in markdown tables, so F1 carried no "
                 "channel at all and A8 was about to re-derive it from the logs. An analysis "
                 "that never becomes structured gets re-derived, and the two answers drift "
                 "apart with nothing to notice the drift."),
        "_how_to_use": ("look up the writing artifact (program, function module or job) in "
                        "`by_artifact` to get its DECLARED channel, then compare against the "
                        "channel A8 DERIVED from the logs. Agreement is confirmation; "
                        "disagreement is a finding on one side or the other."),
        "_source": "knowledge/domains/Integration/integration_map_complete.md",
        "channels": sorted(counts, key=lambda c: -counts[c]),
        "counts": counts,
        "flows": flows,
        "by_artifact": by_artifact,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[channel registry] {len(flows)} flows across {len(counts)} channels, "
          f"{len(by_artifact)} artifacts keyed")
    for ch, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {ch:14s} {n}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
