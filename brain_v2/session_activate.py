"""
Session activation — deterministic domain routing at session start.

Reads an arbitrary text (typically the user's first prompt) and outputs an
activation manifest: which functional domains match, which skills/knowledge
docs/companions/KUs should be loaded, which blind-spots and incidents are
near.

Intended invocation by the agent at session start:

    python brain_v2/session_activate.py "<user's first substantive prompt>"

Or as a SessionStart hook (settings.json example):

    {
      "hooks": {
        "SessionStart": [
          {"type": "command",
           "command": "python brain_v2/session_activate.py \"$CLAUDE_FIRST_PROMPT\""}
        ]
      }
    }

Output format: human-readable block followed by a JSON tail (machine-readable).
The agent reads the human block for context; future tooling can parse the JSON.

CP-compliance:
  - CP-002: no compression — output includes all activated domains + full KU list
  - CP-003: uses regex keyword matching from domains.json session_activation_hints
    (precision, not guesses)
  - feedback_domain_activation_at_session_start (HIGH): this is the structural
    implementation of that rule
"""
import json
import re
import sys
from pathlib import Path

BRAIN_STATE = Path(__file__).parent / "brain_state.json"


def activate(prompt_text: str) -> dict:
    if not BRAIN_STATE.exists():
        return {"error": "brain_state.json missing — run rebuild_all.py"}
    with open(BRAIN_STATE, "r", encoding="utf-8") as f:
        bs = json.load(f)

    registry = bs.get("domains_layer", {})
    hints = registry.get("session_activation_hints", {})

    activated = []
    matched_patterns = []
    for pattern, domains in hints.items():
        if pattern.startswith("_"):
            continue
        if re.search(pattern, prompt_text, flags=re.IGNORECASE):
            matched_patterns.append(pattern)
            for d in domains:
                if d not in activated:
                    activated.append(d)

    manifest = {}
    domains_reg = registry.get("domains", {})
    all_companions = []
    all_skills = []
    all_kus = []
    for d in activated:
        entry = domains_reg.get(d, {})
        manifest[d] = {
            "description": entry.get("description", "")[:160],
            "knowledge_doc_path": entry.get("knowledge_doc_path"),
            "knowledge_docs": entry.get("knowledge_docs", []),
            "skills_to_load": entry.get("skills", []),
            "companions": entry.get("companions", []),
            "open_known_unknowns": entry.get("known_unknowns", []),
            "open_data_quality": entry.get("data_quality_open", []),
            "incidents": entry.get("incidents", []),
            "subtopics_available": list(entry.get("subtopics", {}).keys()),
            "coverage_pct": entry.get("coverage_pct"),
        }
        for c in entry.get("companions", []):
            if c not in all_companions:
                all_companions.append(c)
        for s in entry.get("skills", []):
            if s not in all_skills:
                all_skills.append(s)
        for k in entry.get("known_unknowns", []):
            if k not in all_kus:
                all_kus.append(k)

    result = {
        "prompt_preview": prompt_text[:200],
        "matched_patterns": matched_patterns,
        "activated_domains": activated,
        "unified_skills": all_skills,
        "unified_companions": all_companions,
        "unified_open_kus": all_kus,
        "activation_manifest": manifest,
    }
    if not activated:
        result["warning"] = (
            "No domain match. Scope UNCLASSIFIED. "
            "Either add the keyword to domains.json session_activation_hints "
            "or flag as blind_spot candidate (unclassified_session_scope)."
        )
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python brain_v2/session_activate.py \"<first user prompt>\"", file=sys.stderr)
        sys.exit(2)
    prompt = " ".join(sys.argv[1:])
    result = activate(prompt)

    # Human-readable block first
    print("=" * 60)
    print("SESSION ACTIVATION")
    print("=" * 60)
    print(f"Prompt: {result.get('prompt_preview', '')}")
    if "warning" in result:
        print(f"\n⚠  {result['warning']}")
        print()
    doms = result.get("activated_domains", [])
    print(f"\nActivated domains ({len(doms)}): {doms}")
    if result.get("matched_patterns"):
        print(f"Matched patterns: {len(result['matched_patterns'])}")
    if result.get("unified_skills"):
        print(f"\nSkills to load ({len(result['unified_skills'])}):")
        for s in result["unified_skills"]:
            print(f"  - {s}")
    if result.get("unified_companions"):
        print(f"\nCompanions available ({len(result['unified_companions'])}):")
        for c in result["unified_companions"]:
            print(f"  - {c}")
    if result.get("unified_open_kus"):
        print(f"\nOpen known_unknowns in scope ({len(result['unified_open_kus'])}):")
        for k in result["unified_open_kus"][:15]:
            print(f"  - {k}")
        if len(result["unified_open_kus"]) > 15:
            print(f"  ... and {len(result['unified_open_kus'])-15} more")
    print("\n" + "=" * 60)
    print("--- JSON manifest below (machine-readable) ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
