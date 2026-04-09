"""
Migrate feedback rules from ~/.claude/memory/ into project-internal feedback_rules.json.
One-time migration — after this, brain_v2/agent_rules/feedback_rules.json is the source of truth.

Usage: python brain_v2/migrate_memory.py
"""
import os, json, re, glob

MEMORY_DIR = os.path.expanduser(
    "~/.claude/projects/c--Users-jp-lopez-projects-abapobjectscreation/memory"
)
OUTPUT = os.path.join(os.path.dirname(__file__), "agent_rules", "feedback_rules.json")


def parse_frontmatter(text):
    """Extract YAML-like frontmatter from markdown."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    body = text[m.end():]
    return fm, body


def extract_why(body):
    """Extract **Why:** section from body."""
    m = re.search(r"\*\*Why[:\s]*\*\*\s*(.*?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_how(body):
    """Extract **How to apply:** section from body."""
    m = re.search(r"\*\*How to apply[:\s]*\*\*\s*(.*?)(?=\n\*\*|\n##|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_session(body):
    """Try to find session number in body."""
    m = re.search(r"[Ss]ession\s*#?(\d+)", body)
    return int(m.group(1)) if m else None


def classify_severity(rule_text, why_text):
    """Infer severity from content."""
    combined = (rule_text + " " + why_text).lower()
    if any(w in combined for w in ["never", "critical", "data loss", "wrong", "lost", "broke"]):
        return "CRITICAL"
    if any(w in combined for w in ["always", "must", "waste", "don't ask", "autonomous"]):
        return "HIGH"
    return "MEDIUM"


def migrate():
    pattern = os.path.join(MEMORY_DIR, "feedback_*.md")
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} feedback files in {MEMORY_DIR}")

    rules = []
    for fpath in files:
        fname = os.path.basename(fpath)
        rule_id = fname.replace(".md", "")

        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        # Strip system-reminder tags that Claude adds
        text = re.sub(r"<system-reminder>.*?</system-reminder>\s*", "", text, flags=re.DOTALL)

        fm, body = parse_frontmatter(text)

        # First non-empty line after frontmatter = the rule itself
        lines = [l.strip() for l in body.strip().split("\n") if l.strip()]
        rule_text = lines[0] if lines else fm.get("description", "")
        # Clean markdown formatting
        rule_text = re.sub(r"\*\*|##\s*", "", rule_text).strip()

        why = extract_why(body)
        how = extract_how(body)
        session = extract_session(body)

        rules.append({
            "id": rule_id,
            "rule": rule_text,
            "why": why if why else fm.get("description", ""),
            "how_to_apply": how,
            "severity": classify_severity(rule_text, why),
            "created_session": session,
            "source_file": fname,
        })

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

    print(f"Migrated {len(rules)} rules to {OUTPUT}")

    # Summary by severity
    for sev in ["CRITICAL", "HIGH", "MEDIUM"]:
        count = sum(1 for r in rules if r["severity"] == sev)
        print(f"  {sev}: {count}")

    return rules


if __name__ == "__main__":
    migrate()
