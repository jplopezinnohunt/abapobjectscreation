"""
Extract SAPFPAYM and its include chain from D01 via ADT.
Goal: trace where FPAYHX-ZPFST/ZPLOR/ZLISO/AUSTO/AUST1-3 get populated.

Outputs:
  extracted_code/FI/SAPFPAYM/<name>.abap  for SAPFPAYM + each include
  fpayhx_writers_report.txt              with grep results across the chain
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from sap_adt_client import from_env

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "extracted_code", "FI", "SAPFPAYM")
os.makedirs(OUT_DIR, exist_ok=True)

WANTED_FIELDS = ["zpfst", "zplor", "zliso", "austo", "aust1", "aust2", "aust3", "zbiso"]

client = from_env("D01")
print("Fetching CSRF...")
client.fetch_csrf()

def fetch_program(name, kind="PROG"):
    """Try PROG first, then INCLUDE."""
    name_upper = name.upper()
    for typ, uri_template in [
        ("PROG", "/sap/bc/adt/programs/programs/{}"),
        ("INCLUDE", "/sap/bc/adt/programs/includes/{}"),
    ]:
        if kind != "ANY" and kind != typ:
            continue
        uri = uri_template.format(name_upper.lower())
        try:
            src = client.get_source(uri)
            if src and not src.lstrip().startswith("<?xml"):
                return typ, src
        except Exception as e:
            pass
    return None, None

def save(name, src):
    path = os.path.join(OUT_DIR, name.upper() + ".abap")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    return path

def find_includes(src):
    return re.findall(r"^\s*INCLUDE\s+([A-Z][A-Z0-9_/]+)\s*\.", src, re.IGNORECASE | re.MULTILINE)

# Step 1: SAPFPAYM
print("Fetching SAPFPAYM...")
typ, src = fetch_program("SAPFPAYM", "PROG")
if not src:
    print("  FAILED to fetch SAPFPAYM as PROG")
    sys.exit(1)
print(f"  Got {typ} {len(src)} chars")
path = save("SAPFPAYM", src)
print(f"  Saved {path}")

# Step 2: top-level includes
visited = {"SAPFPAYM"}
queue = find_includes(src)
print(f"\nTop-level includes in SAPFPAYM: {queue}")

all_sources = {"SAPFPAYM": src}
while queue:
    inc = queue.pop(0).upper()
    if inc in visited:
        continue
    visited.add(inc)
    typ, isrc = fetch_program(inc, "ANY")
    if not isrc:
        print(f"  [skip] could not fetch {inc}")
        continue
    save(inc, isrc)
    all_sources[inc] = isrc
    sub = find_includes(isrc)
    print(f"  {inc} ({typ}, {len(isrc)} chars) -> {len(sub)} sub-includes")
    queue.extend(sub)

print(f"\nTotal extracted: {len(all_sources)}")

# Step 3: grep FPAYHX field writers across the chain
print("\n=== FPAYHX-Z writers across chain ===")
report_lines = []
for name, src in all_sources.items():
    for f in WANTED_FIELDS:
        # Match: fpayhx-FIELD = ...   OR   fpayhx-FIELD+offset(len) = ...
        for m in re.finditer(r'(?i)fpayhx-' + f + r'\b[^=\n]*=', src):
            line_no = src[:m.start()].count("\n") + 1
            line_text = src.splitlines()[line_no - 1].strip() if line_no <= len(src.splitlines()) else ""
            entry = f"{name}:{line_no}:  {line_text[:200]}"
            print(entry)
            report_lines.append(entry)

report_path = os.path.join(OUT_DIR, "fpayhx_z_writers_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"\nReport written: {report_path}")
print(f"Total writes found: {len(report_lines)}")
