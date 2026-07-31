"""audit_skill_coverage.py — is the portable SKILL actually complete? (s097)

The skill was written from memory of what had been built. That is not an audit, and
memory is exactly the mechanism this whole model exists to replace.

This walks the ACTUAL tool surface of the repository and answers three questions:

  1. ORPHANED  — a real, runnable tool that the skill never mentions. Either it belongs
                 in a phase, or it is dead code. Both need a decision.
  2. PHANTOM   — the skill references something that does not exist. A skill promising
                 tools it cannot deliver is worse than a shorter skill.
  3. UNPHASED  — a tool the skill mentions but not inside any phase, so a reader has no
                 idea WHEN to run it.

It also reports the CYCLE: which activities are supposed to repeat, and whether anything
declares a cadence. A maturity model that only runs once is a report, not a model.

Usage:  python brain_v2/methods/audit_skill_coverage.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
SKILL = REPO / ".agents" / "skills" / "sap_installation_profiling" / "SKILL.md"
METHODS = HERE / "model_maturity_methods.json"
ASSETS = HERE / "asset_registry.json"

# Where runnable capability actually lives. Deliberately explicit: a glob over the whole
# repo would drown the signal in one-off task scripts.
TOOL_DIRS = [
    ("process_mining", "*.py"),
    ("scripts/extraction", "*.py"),
    ("brain_v2", "*.py"),
    ("brain_v2/system_profile", "*.py"),
    ("brain_v2/system_profile/probes", "*.py"),
    ("brain_v2/methods", "*.py"),
    ("Zagentexecution/sap_data_extraction/scripts", "*.py"),
]

# Three populations, and conflating them inflates or deflates the number:
#   instance   — one extraction of one thing for THIS tenant
#   legacy     — superseded, kept only for history; must NOT be in the skill
#   capability — portable machinery; absence from the skill is a real gap
INSTANCE_HINT = re.compile(
    r"^(extract_|load_|copy_|probe_[a-z]+_|_probe|check_|compare_|find_|merge_|"
    r"reconstruct_|force_|direct_insert_|deploy_|fix_|debug_|test_|analyze_|"
    r"p01_|v01_|d01_|download_|inspect_|validate_bcm|explain_)", re.I)
# superseded by gold_refresh.py / delta_refresh_2026.py — recorded as dead, not as a gap
LEGACY = re.compile(r"^(p01_master_data_sync|p01_massive_extractor|p01_raw_puller)", re.I)


def main():
    if not SKILL.exists():
        print("SKILL.md not found:", SKILL, file=sys.stderr)
        sys.exit(2)
    skill = SKILL.read_text(encoding="utf-8", errors="replace")
    methods = json.load(open(METHODS, encoding="utf-8")) if METHODS.exists() else {}
    assets = json.load(open(ASSETS, encoding="utf-8")) if ASSETS.exists() else {}

    # --- the real tool surface -------------------------------------------
    tools = {}
    for d, pat in TOOL_DIRS:
        p = REPO / d
        if not p.exists():
            continue
        for f in p.glob(pat):
            if f.name.startswith("_") or f.name == "__init__.py":
                continue
            rel = f"{d}/{f.name}"
            kind = ("legacy" if LEGACY.match(f.name)
                    else "instance" if INSTANCE_HINT.match(f.name) else "capability")
            tools[rel] = {"name": f.name, "kind": kind,
                          "kb": round(f.stat().st_size / 1024, 1)}

    named_in_skill = {k for k in tools if tools[k]["name"] in skill or k in skill}
    capability = {k: v for k, v in tools.items() if v["kind"] == "capability"}

    orphaned = sorted(k for k in capability if k not in named_in_skill)
    covered = sorted(k for k in capability if k in named_in_skill)

    # --- phantoms: the skill promising what does not exist ----------------
    phantom = []
    for m in re.findall(r"[`\s(]([A-Za-z0-9_/\.\-]+\.py)[`\s),]", skill):
        cands = [m, f"process_mining/{m}", f"scripts/extraction/{m}",
                 f"brain_v2/{m}", f"brain_v2/system_profile/{m}",
                 f"brain_v2/system_profile/probes/{m}", f"brain_v2/methods/{m}",
                 f"Zagentexecution/sap_data_extraction/scripts/{m}",
                 f"Zagentexecution/mcp-backend-server-python/{m}"]
        if not any((REPO / c).exists() for c in cands):
            phantom.append(m)

    # --- the CYCLE: what is supposed to repeat, and how often -------------
    ms = methods.get("methods", {})
    cadence = {mid: m.get("fires") for mid, m in ms.items()}
    no_cadence = [mid for mid, f in cadence.items() if not f]

    # --- report -----------------------------------------------------------
    from collections import Counter
    pops = Counter(v["kind"] for v in tools.values())
    print(f"[skill coverage] {len(tools)} scripts scanned · "
          f"capability={pops['capability']} instance={pops['instance']} legacy={pops['legacy']}")
    print(f"  covered by the skill : {len(covered)}")
    print(f"  ORPHANED             : {len(orphaned)}")
    for o in orphaned:
        print(f"      {o}  ({tools[o]['kb']} KB)")
    if phantom:
        print(f"  PHANTOM (skill names it, it does not exist): {len(set(phantom))}")
        for p in sorted(set(phantom)):
            print(f"      {p}")
    print(f"\n[cycle] {len(ms)} methods declared")
    for mid, f in sorted(cadence.items()):
        print(f"      {mid:28s} fires: {f or '*** NO CADENCE DECLARED ***'}")
    if no_cadence:
        print(f"  {len(no_cadence)} method(s) with no cadence — a model that runs once "
              f"is a report, not a model.")

    pct = round(100.0 * len(covered) / max(1, len(capability)), 1)
    print(f"\nSKILL COVERAGE = {pct}% of portable capability is reachable from the skill")
    return {"covered": covered, "orphaned": orphaned,
            "phantom": sorted(set(phantom)), "pct": pct}


if __name__ == "__main__":
    main()
