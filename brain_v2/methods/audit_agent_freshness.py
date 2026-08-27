"""audit_agent_freshness.py — do the agents still know what the model knows? (s097)

An agent or skill is FROZEN KNOWLEDGE. It was written on one day against one understanding,
and nothing tells it when that understanding moves. This session proved the cost twice: the
CHANGE-AUDIT skill was reading a scope-filtered copy of the change log — the one table its
whole purpose depends on — and the FI domain agent still said `cdhdr` "needs extraction"
when 12 million rows had been sitting in the golden database for months.

Neither was caught by anyone reading them. Both were caught by a check.

Three questions, all derived from disk rather than asserted:

    STALE            does it reference something the registry marks SUPERSEDED, or a table
                     whose catalogue entry carries a recorded TRAP it does not mention?
    MISSING METHOD   is it a domain skill whose tables are written with no maintenance
                     transaction, while it never mentions the write-path discovery that
                     answers exactly that?
    UNANCHORED       does it name gold tables at all, yet cite no claim and no catalogue?

**This is not a style check.** Every finding it reports is a case where an agent would give
a confident answer from knowledge the model has already superseded — which is worse than an
agent that says nothing, because it is trusted.

Run: python brain_v2/methods/audit_agent_freshness.py     (non-fatal: reports, never blocks)
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
AGENTS = [REPO / ".claude" / "agents", REPO / ".claude" / "skills"]
REGISTRY = REPO / "brain_v2" / "gold_table_registry.json"
CATALOGUE = REPO / "knowledge" / "gold_db_table_catalog.md"
ATTRIB = REPO / "brain_v2" / "change_attribution.json"
OUT = REPO / "brain_v2" / "methods" / "agent_freshness.json"

# the method that answers "what writes this", and the words that mean an agent knows it
WRITE_PATH_METHOD = ("attribute_changes_to_programs", "write path", "write-path",
                     "change_attribution", "A8")


def _superseded():
    """gold table -> its replacement, straight from the registry."""
    out = {}
    if not REGISTRY.exists():
        return out
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    for _dom, secs in (reg.get("domains") or {}).items():
        for _sec, items in (secs.items() if isinstance(secs, dict) else []):
            for it in (items if isinstance(items, list) else []):
                if isinstance(it, dict) and it.get("superseded_by"):
                    out[str(it["gold"]).lower()] = str(it["superseded_by"]).lower()
    return out


def _tables_with_traps():
    """Tables whose catalogue entry records a trap an agent must not omit."""
    if not CATALOGUE.exists():
        return {}
    txt = CATALOGUE.read_text(encoding="utf-8", errors="replace")
    traps = {}
    for m in re.finditer(r"\*\*([A-Z][A-Z0-9_]{2,})\s*·\s*([^*]+)\*\*", txt):
        traps.setdefault(m.group(1), []).append(m.group(2).strip())
    return traps


def _interface_written_classes():
    """Object classes A8 says are written with no transaction — the ones an agent
    cannot explain from transactions alone."""
    if not ATTRIB.exists():
        return set()
    try:
        d = json.load(open(ATTRIB, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return {c for c, r in (d.get("classes") or {}).items()
            if r.get("channel") in ("PROGRAM", "INTERFACE")}


def main():
    superseded, traps = _superseded(), _tables_with_traps()
    no_tcode = _interface_written_classes()

    files = []
    for root in AGENTS:
        if root.exists():
            files += sorted(root.rglob("SKILL.md")) + sorted(root.glob("*.md"))

    rows, stale, missing, unanchored = {}, [], [], []
    for f in files:
        rel = str(f.relative_to(REPO)).replace("\\", "/")
        txt = f.read_text(encoding="utf-8", errors="replace")
        issues = []

        # STALE — reads a superseded copy. Case-sensitive: lowercase is the gold table,
        # uppercase is the SAP table read over RFC, and they are different things.
        for old, new in superseded.items():
            if re.search(rf"\bFROM\s+{old}\b", txt) and "SUPERSEDED" not in txt:
                issues.append({"kind": "STALE", "detail":
                               f"reads `{old}`, superseded by `{new}`"})

        # STALE — names a table that carries a recorded trap, without carrying the warning
        for tbl, warn in traps.items():
            if re.search(rf"\b{tbl}\b", txt) and not any(
                    w.split()[0].lower() in txt.lower() for w in warn):
                issues.append({"kind": "STALE", "detail":
                               f"names {tbl} but omits its recorded trap: {warn[0][:70]}"})

        # MISSING METHOD — a domain agent that talks about object classes written with no
        # transaction, and does not know the method that explains them
        if ("domain_agent" in rel or "/coordinator/" in rel) and no_tcode:
            hits = sorted({c for c in no_tcode if re.search(rf"\b{c}\b", txt)})
            if hits and not any(k.lower() in txt.lower() for k in WRITE_PATH_METHOD):
                issues.append({"kind": "MISSING_METHOD", "detail":
                               f"covers {', '.join(hits[:4])} — written with no transaction "
                               f"code — but never reaches the write-path discovery (A8)"})

        # UNANCHORED — names gold tables, cites no claim and no catalogue
        names_tables = bool(re.search(r"\b(cdhdr_history|reguh|fmioi|bkpf|bseg)\b", txt))
        if names_tables and "claim" not in txt.lower() and "catalog" not in txt.lower():
            issues.append({"kind": "UNANCHORED", "detail":
                           "names gold tables but cites no claim and no catalogue entry"})

        if issues:
            rows[rel] = issues
            for i in issues:
                {"STALE": stale, "MISSING_METHOD": missing,
                 "UNANCHORED": unanchored}[i["kind"]].append(rel)

    json.dump({
        "_generated_by": "brain_v2/methods/audit_agent_freshness.py",
        "_question": "do the agents still know what the model knows?",
        "_why": ("an agent is frozen knowledge — written on one day, and nothing tells it "
                 "when the understanding moves. An agent answering confidently from a "
                 "superseded fact is worse than one that says nothing, because it is trusted."),
        "checked": len(files),
        "counts": {"stale": len(set(stale)), "missing_method": len(set(missing)),
                   "unanchored": len(set(unanchored))},
        "findings": rows,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"[agent freshness] {len(files)} agents and skills checked")
    print(f"  STALE          {len(set(stale))}")
    print(f"  MISSING METHOD {len(set(missing))}")
    print(f"  UNANCHORED     {len(set(unanchored))}")
    for rel, issues in sorted(rows.items()):
        print(f"\n  {rel}")
        for i in issues[:3]:
            print(f"     {i['kind']:15s} {i['detail']}")
    if not rows:
        print("  OK — no agent is carrying a superseded fact")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
