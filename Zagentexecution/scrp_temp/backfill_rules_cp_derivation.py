"""H51 Chunk F step 1: backfill `derives_from_core_principle` on all 86 feedback rules.

Heuristic mapping from rule id/severity/content to one of CP-001/002/003.
CP-001 (Knowledge over velocity): preservation, formalization, anti-regression, never-drop
CP-002 (Preserve first, context cheap): structure, append-only, no-compression, findability
CP-003 (Precision, evidence, facts): verify, brain-first, tier, exact-count, sample-first, cite-source

When ambiguous: severity CRITICAL default to CP-003 (precision gate), HIGH default to CP-001.
Rules already tagged (from chunk C) are skipped.
"""
import json
from pathlib import Path

RULES_PATH = Path("brain_v2/agent_rules/feedback_rules.json")

CP_KEYWORDS = {
    "CP-001": [
        "preserve", "never delete", "never drop", "formalize", "retro", "document",
        "archive", "superseded", "session close", "bridge", "pmo", "reconcile",
        "columns", "never overwrite", "extracted_code", "no compression",
    ],
    "CP-002": [
        "structure", "append", "schema", "lossless", "inline", "structure",
        "visjs", "no cdn", "context", "growth", "1M", "brain_state",
    ],
    "CP-003": [
        "verify", "sample", "precision", "evidence", "tier", "source code",
        "cite", "exact", "count", "brain first", "grep", "landscape", "check",
        "prerequisite", "gold db", "introspect", "gate", "guard", "assumption",
        "fact", "validate", "production", "adr", "spec", "trace", "empirical",
        "ry_stext", "rule_ry",
    ],
}


def infer_cp(rule):
    """Heuristic: pick the most-matching CP by keyword frequency."""
    if rule.get("derives_from_core_principle"):
        return rule["derives_from_core_principle"]

    text = " ".join([
        rule.get("id", ""),
        rule.get("rule", ""),
        rule.get("why", ""),
        rule.get("how_to_apply", ""),
    ]).lower()

    scores = {}
    for cp, kws in CP_KEYWORDS.items():
        scores[cp] = sum(1 for kw in kws if kw in text)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        sev = rule.get("severity", "MEDIUM")
        return "CP-003" if sev == "CRITICAL" else "CP-001"
    return best


def main():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        rules = json.load(f)

    already = 0
    added = 0
    dist = {"CP-001": 0, "CP-002": 0, "CP-003": 0}
    for r in rules:
        if r.get("derives_from_core_principle"):
            already += 1
            dist[r["derives_from_core_principle"]] += 1
            continue
        cp = infer_cp(r)
        r["derives_from_core_principle"] = cp
        r["cp_derivation_method"] = "heuristic_session_054"
        added += 1
        dist[cp] += 1

    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

    print(f"Already tagged: {already}")
    print(f"Newly tagged: {added}")
    print(f"Total rules: {len(rules)}")
    print(f"Distribution: {dist}")


if __name__ == "__main__":
    main()
