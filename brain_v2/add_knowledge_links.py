"""Add knowledge doc links to brain_state.json objects."""
import json, re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_STATE = PROJECT_ROOT / "brain_v2" / "brain_state.json"
SCAN_DIRS = [
    PROJECT_ROOT / "knowledge",
    PROJECT_ROOT / "Brain_Architecture",
]


def main():
    brain = json.load(open(BRAIN_STATE, encoding="utf-8"))
    object_names = set(brain["objects"].keys())

    doc_refs = defaultdict(set)
    docs_to_scan = []
    for d in SCAN_DIRS:
        if d.exists():
            docs_to_scan.extend(d.rglob("*.md"))
    for doc in docs_to_scan:
        try:
            text = doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for name in object_names:
            if len(name) < 5:
                continue
            if re.search(r"\b" + re.escape(name) + r"\b", text, re.IGNORECASE):
                rel = str(doc.relative_to(PROJECT_ROOT)).replace("\\", "/")
                doc_refs[name].add(rel)

    added = 0
    objs_with_docs = 0
    for name, docs in doc_refs.items():
        if name in brain["objects"] and docs:
            brain["objects"][name]["knowledge_docs"] = sorted(docs)[:5]
            added += len(docs)
            objs_with_docs += 1

    out = json.dumps(brain, indent=2, ensure_ascii=False)
    BRAIN_STATE.write_text(out, encoding="utf-8")
    tokens = len(out) // 4
    print(f"Added {added} knowledge doc links to {objs_with_docs} objects")
    print(f"brain_state.json: {len(out):,} bytes, ~{tokens:,} tokens ({tokens/1000000*100:.1f}% of 1M)")


if __name__ == "__main__":
    main()
