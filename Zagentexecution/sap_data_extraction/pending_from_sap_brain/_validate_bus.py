#!/usr/bin/env python3
"""Validate the REQUEST/DONE/FLAG/HANDOFF bus messages against contract C-4 v1.1.

C-4 is owned by C0 (see sapilot/analysis/arch/C0-C6-nucleo-bus.md). C1 retired its
divergent "Contrato D" — the messages on disk validate C0's header, not C1's.
Front-matter must be DERIVED from the prose. A field the prose never states is written
as the literal UNKNOWN -> WARN (visible gap), never guessed. A missing key -> ERROR.

Usage: python _validate_bus.py [dir]   # exit 1 if any ERROR
"""
import sys, pathlib, yaml

BASE = ["msg_type", "request_id", "from_project", "date"]
REQ = {
    "REQUEST": BASE + ["status", "why", "resource_requested", "extract_spec", "consumers", "resolve_via"],
    "DONE":    BASE + ["owner", "closes", "tables_landed", "how_to_consume"],
    "FLAG":    BASE + ["status", "why", "resolve_via"],
    "HANDOFF": BASE + ["to_project", "why", "how_to_consume"],
}
errors, warns = [], []


def check(path):
    txt = path.read_text(encoding="utf-8")
    tag = path.name
    if not txt.startswith("---\n"):
        return errors.append(f"{tag}: no YAML front-matter (C-4 v1.1 header missing)")
    _, fm, body = txt.split("---\n", 2)
    try:
        meta = yaml.safe_load(fm) or {}
    except yaml.YAMLError as e:
        return errors.append(f"{tag}: front-matter is not valid YAML: {e}")
    if not body.strip():
        errors.append(f"{tag}: prose body is empty (the markdown must stay human-readable)")

    mt = meta.get("msg_type")
    if mt not in REQ:
        return errors.append(f"{tag}: msg_type={mt!r} not in {sorted(REQ)}")
    if mt != path.stem.split("_")[0]:
        errors.append(f"{tag}: msg_type={mt} contradicts the filename prefix")

    for k in REQ[mt]:
        if k not in meta:
            errors.append(f"{tag}: missing required C-4 field '{k}' for {mt}")
        elif meta[k] in ("UNKNOWN", None, "", []):
            warns.append(f"{tag}: '{k}' is UNKNOWN/empty - not stated in the message prose")

    d = str(meta.get("date", ""))
    if len(d) != 10 or d[4] != "-" or d[7] != "-":
        errors.append(f"{tag}: date={d!r} is not ISO YYYY-MM-DD")
    if mt in ("REQUEST", "FLAG") and meta.get("status") not in ("OPEN", "RESOLVED", "UNKNOWN"):
        errors.append(f"{tag}: status={meta.get('status')!r} not in OPEN|RESOLVED")
    for i, s in enumerate(meta.get("extract_spec") or []):
        if not isinstance(s, dict) or not s.get("source_table"):
            errors.append(f"{tag}: extract_spec[{i}] has no source_table")
    if mt == "DONE" and not meta.get("closes"):
        errors.append(f"{tag}: DONE must declare what it closes")
    # tenant_id is optional in v1.1 (single-tenant bus today) but required once tenant #2 exists (D3)
    if "tenant_id" not in meta:
        warns.append(f"{tag}: no tenant_id (bus is structurally single-tenant - blocks D3 multi-tenant)")


root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else __file__).resolve()
root = root if root.is_dir() else root.parent
files = sorted(p for p in root.glob("*.md") if p.stem.split("_")[0] in REQ)
for f in files:
    check(f)
for w in warns:
    print(f"WARN  {w}")
for e in errors:
    print(f"ERROR {e}")
print(f"\n{len(files)} bus messages checked - {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
