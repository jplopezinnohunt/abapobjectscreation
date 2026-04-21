"""
Inject `domains:` frontmatter into SKILL.md files across .agents/skills/.

Strategy: if the file already has YAML frontmatter (starts with ---), inject
into it. Otherwise prepend a new frontmatter block. Infer domain from skill
name + first-paragraph keyword match.

Idempotent: if a `domains:` block already exists, skip (no duplicate).
Prints a report at end. CP-002 compliant — no content deletion.

Usage: python brain_v2/scripts/inject_skill_domains.py
"""
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent
SKILLS_DIR = PROJECT / ".agents" / "skills"

# Skill name keyword -> 3-axis domain (conservative, skills already have clear scope)
SKILL_DOMAIN_MAP = {
    "coordinator": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "skill_coordinator": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "skill_creator": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "agi_retro_agent": {"functional": ["*"], "module": ["*"], "process": ["*"]},

    "fi_domain_agent": {"functional": ["FI"], "module": ["FI"], "process": ["B2R", "P2P", "T2R"]},
    "hcm_domain_agent": {"functional": ["HCM"], "module": ["HCM", "PD"], "process": ["H2R"]},
    "psm_domain_agent": {"functional": ["PSM"], "module": ["FM"], "process": ["B2R"]},

    "sap_data_extraction": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "sap_adt_api": {"functional": ["*"], "module": ["BASIS", "CTS"], "process": []},
    "sap_master_data_sync": {"functional": ["FI"], "module": ["FI", "CTS"], "process": ["P2D"]},
    "sap_st01_trace_reader": {"functional": ["Support"], "module": ["BASIS"], "process": []},

    "sap_incident_analyst": {"functional": ["Support"], "module": ["*"], "process": ["*"]},
    "sap_debugging_and_healing": {"functional": ["Support"], "module": ["BASIS", "CUSTOM"], "process": []},
    "sap_change_audit": {"functional": ["Support", "FI"], "module": ["*"], "process": []},
    "sap_account_comparison": {"functional": ["FI"], "module": ["FI"], "process": ["B2R"]},

    "sap_transport_intelligence": {"functional": ["Transport_Intelligence"], "module": ["CTS", "BASIS"], "process": []},
    "sap_transport_companion": {"functional": ["Transport_Intelligence"], "module": ["CTS"], "process": []},
    "sap_company_code_copy": {"functional": ["FI", "Treasury"], "module": ["FI", "CTS"], "process": ["P2D"]},
    "sap_reverse_engineering": {"functional": ["*"], "module": ["CUSTOM"], "process": []},
    "sap_enhancement_extraction": {"functional": ["*"], "module": ["CUSTOM"], "process": []},
    "sap_system_monitor": {"functional": ["Support"], "module": ["BASIS"], "process": []},
    "sap_bdc_intelligence": {"functional": ["HCM", "Support"], "module": ["HCM", "CUSTOM"], "process": ["H2R"]},
    "sap_job_intelligence": {"functional": ["Support"], "module": ["BASIS"], "process": []},
    "sap_interface_intelligence": {"functional": ["Integration"], "module": ["BASIS"], "process": []},
    "sap_process_mining": {"functional": ["*"], "module": ["*"], "process": ["*"]},

    "sap_class_deployment": {"functional": ["*"], "module": ["CUSTOM", "CTS"], "process": []},
    "sap_fiori_tools": {"functional": ["*"], "module": ["*"], "process": []},
    "sap_fiori_extension_architecture": {"functional": ["*"], "module": ["*"], "process": []},
    "sap_segw": {"functional": ["*"], "module": ["*"], "process": []},
    "segw_automation": {"functional": ["*"], "module": ["*"], "process": []},
    "sap_webgui": {"functional": ["*"], "module": ["*"], "process": []},
    "sap_native_desktop": {"functional": ["*"], "module": ["*"], "process": []},
    "sap_automated_testing": {"functional": ["*"], "module": ["*"], "process": []},
    "crp_fiori_app": {"functional": ["FI", "PSM"], "module": ["FI", "FM"], "process": ["B2R"]},
    "abapgit_integration": {"functional": ["*"], "module": ["CTS", "CUSTOM"], "process": []},

    "sap_expert_core": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "unesco_filter_registry": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    "integration_diagram": {"functional": ["Integration"], "module": ["BASIS"], "process": []},
    "parallel_html_build": {"functional": ["*"], "module": ["*"], "process": []},
    "notion_integration": {"functional": ["*"], "module": ["*"], "process": []},
}


def has_yaml_frontmatter(content: str) -> bool:
    return content.lstrip().startswith("---")


def has_domains_block(content: str) -> bool:
    # look for 'domains:' within the first frontmatter block (first ---...--- pair)
    if not has_yaml_frontmatter(content):
        return False
    m = re.match(r'^\s*---(.*?)---', content, flags=re.DOTALL)
    if not m:
        return False
    return bool(re.search(r'^domains:\s*$', m.group(1), flags=re.MULTILINE))


def format_domains_yaml(axes: dict) -> str:
    f = ", ".join(axes.get("functional", []))
    m = ", ".join(axes.get("module", []))
    p = ", ".join(axes.get("process", []))
    return (f"domains:\n"
            f"  functional: [{f}]\n"
            f"  module: [{m}]\n"
            f"  process: [{p}]\n")


def inject_into_existing_frontmatter(content: str, domains_block: str) -> str:
    # Insert before closing ---
    pattern = r'^\s*---(.*?)---'
    m = re.match(pattern, content, flags=re.DOTALL)
    if not m:
        return content
    fm_body = m.group(1)
    new_fm = "---" + fm_body.rstrip() + "\n" + domains_block + "---"
    return new_fm + content[m.end():]


def prepend_frontmatter(content: str, name: str, domains_block: str) -> str:
    fm = (f"---\n"
          f"name: {name}\n"
          f"{domains_block}"
          f"---\n\n")
    return fm + content


def main():
    updated = []
    skipped_already_tagged = []
    no_domain_mapping = []
    errors = []

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        name = skill_dir.name

        try:
            content = skill_file.read_text(encoding="utf-8")
        except Exception as e:
            errors.append((name, str(e)))
            continue

        if has_domains_block(content):
            skipped_already_tagged.append(name)
            continue

        axes = SKILL_DOMAIN_MAP.get(name)
        if not axes:
            no_domain_mapping.append(name)
            continue

        domains_block = format_domains_yaml(axes)

        if has_yaml_frontmatter(content):
            new_content = inject_into_existing_frontmatter(content, domains_block)
        else:
            new_content = prepend_frontmatter(content, name, domains_block)

        skill_file.write_text(new_content, encoding="utf-8")
        updated.append(name)

    print("=" * 60)
    print("SKILL DOMAINS INJECTION")
    print("=" * 60)
    print(f"\n[UPDATED] {len(updated)} skills")
    for n in updated:
        print(f"  + {n}")
    print(f"\n[SKIPPED — already tagged] {len(skipped_already_tagged)}")
    for n in skipped_already_tagged:
        print(f"  = {n}")
    if no_domain_mapping:
        print(f"\n[NO MAPPING — needs manual tagging] {len(no_domain_mapping)}")
        for n in no_domain_mapping:
            print(f"  ? {n}")
    if errors:
        print(f"\n[ERRORS] {len(errors)}")
        for n, e in errors:
            print(f"  ! {n}: {e}")

    total = len(updated) + len(skipped_already_tagged)
    all_skills = total + len(no_domain_mapping)
    print(f"\nCoverage: {total}/{all_skills} ({round(100*total/all_skills, 1) if all_skills else 0}%)")


if __name__ == "__main__":
    main()
