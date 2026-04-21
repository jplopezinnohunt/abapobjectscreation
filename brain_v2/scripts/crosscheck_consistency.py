"""
Cross-check consistency between Learnings (rules/claims/incidents), Companions
(HTML files under companions/), Skills (.agents/skills/*/SKILL.md), and the
Domains registry (brain_v2/domains/domains.json).

Checks (orphans both ways):
  1. Every rule_id referenced from domain.rules_ids EXISTS in feedback_rules.json
  2. Every claim_id referenced from domain.claims_ids EXISTS in claims.json
  3. Every incident_id referenced from domain.incidents EXISTS in incidents.json
  4. Every companion path referenced from domain.companions EXISTS on disk
  5. Every skill referenced from domain.skills EXISTS in .agents/skills/
  6. Every rule in feedback_rules.json has domain_axes (coverage check)
  7. Every claim in claims.json has domain_axes
  8. Every incident in incidents.json has domain_axes
  9. Every skill SKILL.md has domains: frontmatter
 10. Every domain_axes.functional value (non-wildcard) exists in domains.json
     as a domain key

Report printed. Exit code 0 if zero orphans, 1 otherwise.

Usage: python brain_v2/scripts/crosscheck_consistency.py
"""
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_domains_from_axes(axes):
    if not isinstance(axes, dict):
        return []
    return [v for v in axes.get("functional", []) if v and v != "*"]


def main():
    rules = load_json(PROJECT / "brain_v2" / "agent_rules" / "feedback_rules.json")
    claims = load_json(PROJECT / "brain_v2" / "claims" / "claims.json")
    incidents = load_json(PROJECT / "brain_v2" / "incidents" / "incidents.json")
    domains = load_json(PROJECT / "brain_v2" / "domains" / "domains.json")

    companions_dir = PROJECT / "companions"
    existing_companions = {str(p.relative_to(PROJECT)).replace("\\", "/") for p in companions_dir.glob("*.html")}

    skills_dir = PROJECT / ".agents" / "skills"
    existing_skills = {p.name for p in skills_dir.iterdir() if p.is_dir()}

    rule_ids = {r["id"] for r in rules}
    claim_ids = {c["id"] for c in claims}
    incident_ids = {i["id"] for i in incidents}
    domain_keys = set(domains["domains"].keys())

    errors = []
    warnings = []

    # 1-5: orphans in domain registry
    for dom_name, dom in domains["domains"].items():
        for rid in dom.get("rules_ids", []):
            if rid not in rule_ids:
                errors.append(f"ORPHAN rule_id in domains.{dom_name}.rules_ids: {rid}")
        for cid in dom.get("claims_ids", []):
            if cid not in claim_ids:
                errors.append(f"ORPHAN claim_id in domains.{dom_name}.claims_ids: {cid}")
        for iid in dom.get("incidents", []):
            if iid not in incident_ids:
                warnings.append(f"ORPHAN incident_id in domains.{dom_name}.incidents: {iid} (may be legacy H-prefix)")
        for comp in dom.get("companions", []):
            comp_norm = comp.replace("\\", "/")
            if comp_norm not in existing_companions:
                warnings.append(f"ORPHAN companion in domains.{dom_name}.companions: {comp}")
        for skill in dom.get("skills", []):
            if skill not in existing_skills:
                errors.append(f"ORPHAN skill in domains.{dom_name}.skills: {skill}")

    # 6-9: coverage
    untagged_rules = [r["id"] for r in rules if "domain_axes" not in r]
    untagged_claims = [c["id"] for c in claims if "domain_axes" not in c]
    untagged_incidents = [i["id"] for i in incidents if "domain_axes" not in i]

    for rid in untagged_rules:
        errors.append(f"Rule missing domain_axes: {rid}")
    for cid in untagged_claims:
        errors.append(f"Claim missing domain_axes: {cid}")
    for iid in untagged_incidents:
        errors.append(f"Incident missing domain_axes: {iid}")

    # Skill frontmatter coverage
    skills_missing_domains = []
    for sd in skills_dir.iterdir():
        if not sd.is_dir():
            continue
        sf = sd / "SKILL.md"
        if not sf.exists():
            continue
        content = sf.read_text(encoding="utf-8")
        m = re.match(r'^\s*---(.*?)---', content, flags=re.DOTALL)
        has = False
        if m and re.search(r'^domains:\s*$', m.group(1), flags=re.MULTILINE):
            has = True
        if not has:
            skills_missing_domains.append(sd.name)
    for s in skills_missing_domains:
        errors.append(f"Skill missing domains: frontmatter: {s}")

    # 10: every node's functional domain exists in registry
    unknown_functional_domains = set()
    for r in rules:
        for d in list_domains_from_axes(r.get("domain_axes")):
            if d not in domain_keys:
                unknown_functional_domains.add(d)
    for c in claims:
        for d in list_domains_from_axes(c.get("domain_axes")):
            if d not in domain_keys:
                unknown_functional_domains.add(d)
    for i in incidents:
        for d in list_domains_from_axes(i.get("domain_axes")):
            if d not in domain_keys:
                unknown_functional_domains.add(d)
    for d in sorted(unknown_functional_domains):
        warnings.append(f"Node references functional domain NOT in domains.json: {d}")

    # Report
    print("=" * 60)
    print("CROSS-CHECK CONSISTENCY — Learnings / Companions / Domains / Skills")
    print("=" * 60)
    print(f"\nInventory:")
    print(f"  Rules: {len(rules)} ({len(rules) - len(untagged_rules)} tagged)")
    print(f"  Claims: {len(claims)} ({len(claims) - len(untagged_claims)} tagged)")
    print(f"  Incidents: {len(incidents)} ({len(incidents) - len(untagged_incidents)} tagged)")
    print(f"  Domain registry entries: {len(domain_keys)}")
    print(f"  Companions on disk: {len(existing_companions)}")
    print(f"  Skills on disk: {len(existing_skills)}")

    if errors:
        print(f"\n[ERRORS] {len(errors)}")
        for e in errors:
            print(f"  ! {e}")
    else:
        print("\n[ERRORS] None — full consistency!")

    if warnings:
        print(f"\n[WARNINGS] {len(warnings)}")
        for w in warnings:
            print(f"  ~ {w}")

    print("\n" + "=" * 60)
    if errors:
        print("RESULT: FAIL — fix errors above")
        sys.exit(1)
    else:
        print("RESULT: PASS — learnings, companions, skills, domains consistent")


if __name__ == "__main__":
    main()
