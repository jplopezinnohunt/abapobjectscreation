"""Session #054 Chunk D (H42): Migrate claims.evidence_for/evidence_against from str to list[{type,ref,cite}].

Follows CP-001 (Knowledge over velocity): preserve original text in `evidence_legacy_text` field.
Follows CP-002 (Preserve first): no info loss; wrap existing str as single-item list.
Follows CP-003 (Precision): infer type from content patterns (source_code, production_data, empirical, config, other).

Original -> migrated structure:
  "evidence_for": "some text..."
becomes:
  "evidence_for": [
    {"type": "empirical", "ref": null, "cite": "some text...", "added_session": <created_session>, "migrated_from_legacy": true}
  ],
  "evidence_legacy_text_for": "some text..."   # preserved verbatim for audit
"""
import json
import re
from pathlib import Path

CLAIMS_PATH = Path("brain_v2/claims/claims.json")
BACKUP_PATH = Path("brain_v2/claims/claims.json.pre_session054_backup")


def infer_evidence_type(text):
    """Classify a legacy evidence string into a structured type. Conservative — unknown defaults to 'empirical'."""
    if not text or not isinstance(text, str):
        return "empirical"
    t = text.lower()
    # Source code signals
    if re.search(r'\.(abap|py|js)[:\b]', text) or re.search(r'line\s+\d+', t) or 'extracted_code/' in text or 'class ' in t and 'method' in t:
        return "source_code"
    # SQL / production data
    if re.search(r'select\s+', t) or re.search(r'\bfrom\s+\w+', t) or 'gold db' in t or 'rows' in t and re.search(r'\d+\s*rows', t):
        return "production_data"
    # Config / customizing
    if any(k in t for k in ['tadir', 't012', 't030', 'fbzp', 'ob08', 'customizing', 'sap note']):
        return "config"
    # Tables with specific keys
    if any(k in text for k in ['HBKID', 'BUKRS', 'PERNR', 'FIKRS', 'FONDS']):
        return "production_data"
    return "empirical"


def infer_ref(text):
    """Extract file:line or table:field pattern if present. Returns None if not detectable."""
    if not text:
        return None
    # file path with line
    m = re.search(r'(\S+\.(?:abap|py|js|md|json))[:\s]+(?:line\s+)?(\d+)', text)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    # file path only
    m = re.search(r'((?:extracted_code|knowledge|brain_v2|Zagentexecution)/\S+)', text)
    if m:
        return m.group(1)
    # SAP table reference
    m = re.search(r'\b([A-Z][A-Z0-9_]{2,})\.([A-Z][A-Z0-9_]+)', text)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return None


def migrate_evidence_field(value, created_session):
    """Convert str evidence into structured list. None stays None. Already-list stays list."""
    if value is None:
        return None
    if isinstance(value, list):
        return value  # already migrated
    if isinstance(value, str):
        if not value.strip():
            return None
        return [{
            "type": infer_evidence_type(value),
            "ref": infer_ref(value),
            "cite": value,
            "added_session": created_session,
            "migrated_from_legacy": True
        }]
    return None


def main():
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        claims = json.load(f)

    # Backup first — CP-001 preserve
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)
    print(f"Backup written: {BACKUP_PATH}")

    migrated = 0
    skipped = 0
    for c in claims:
        cs = c.get("created_session", 0)
        ef = c.get("evidence_for")
        ea = c.get("evidence_against")

        if isinstance(ef, str) and ef.strip():
            c["evidence_legacy_text_for"] = ef  # preserve verbatim
            c["evidence_for"] = migrate_evidence_field(ef, cs)
            migrated += 1
        elif isinstance(ef, list):
            skipped += 1

        if isinstance(ea, str) and ea.strip():
            c["evidence_legacy_text_against"] = ea
            c["evidence_against"] = migrate_evidence_field(ea, cs)

    # Write back
    with open(CLAIMS_PATH, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)

    # Stats by type
    from collections import Counter
    types_for = Counter()
    types_against = Counter()
    for c in claims:
        ef = c.get("evidence_for") or []
        for e in ef:
            types_for[e.get("type")] += 1
        ea = c.get("evidence_against") or []
        for e in ea:
            types_against[e.get("type")] += 1

    print(f"\nMigrated: {migrated} claims (evidence_for str -> list)")
    print(f"Already list: {skipped}")
    print(f"Total claims: {len(claims)}")
    print(f"\nevidence_for types after migration: {dict(types_for)}")
    print(f"evidence_against types after migration: {dict(types_against)}")
    print(f"\nLegacy text preserved in: evidence_legacy_text_for / evidence_legacy_text_against (CP-001)")


if __name__ == "__main__":
    main()
