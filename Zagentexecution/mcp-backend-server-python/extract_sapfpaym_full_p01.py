"""
extract_sapfpaym_full_p01.py
============================
RE-extraction of SAPFPAYM and ALL related code/structures from P01 (SNC/SSO).

Triggered Session #072 because the previous D01 ADT extraction wrote an
HTML logon-failure page into SAPFPAYM.abap (password locked, per
feedback_d01_adt_locked_use_p01_rfc).

Outputs:
  extracted_code/FI/SAPFPAYM/<NAME>.abap                — main + every include
  extracted_code/FI/SAPFPAYM/structures/<NAME>.json     — DDIC structures
  extracted_code/FI/SAPFPAYM/funcs/<FM>.abap            — RFC fetched FMs
  extracted_code/FI/SAPFPAYM/manifest.json              — full inventory

Targets:
  - PROG: SAPFPAYM (driver), RFFOAVIS_FPAYM (avis preview, alt entry point)
  - All includes recursively (depth unlimited; visited-set prevents loops)
  - Structures: FPAYH, FPAYHX, FPAYP, FPAYPX, FPAYHM, FPM_PAYTAB,
                FPAY_HEAD_KEY, FPAY_ITEM_KEY (best-effort, skip on missing)
  - Class CL_DMEE_CONVERSION (DMEE format engine master class)
  - Class CL_DMEE_FORMAT_INTERFACE (entry point used by SAPFPAYM)

NO INVENTING. If a name is not found in the SAP system, it gets logged in
manifest.json under "missing" — never fabricated content.
"""

import os
import sys
import json
import time
import re

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

OUT_BASE     = os.path.join(os.path.dirname(__file__), "..", "..", "extracted_code", "FI", "SAPFPAYM")
OUT_CODE     = OUT_BASE
OUT_STRUCT   = os.path.join(OUT_BASE, "structures")
OUT_FUNC     = os.path.join(OUT_BASE, "funcs")
OUT_CLASSES  = os.path.join(OUT_BASE, "classes")
MANIFEST     = os.path.join(OUT_BASE, "manifest.json")

for d in (OUT_CODE, OUT_STRUCT, OUT_FUNC, OUT_CLASSES):
    os.makedirs(d, exist_ok=True)

manifest = {
    "extraction_session": 72,
    "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "source_system": "P01",
    "method": "pyrfc + RPY_PROGRAM_READ + DDIF_FIELDINFO_GET + RPY_FUNCTIONMODULE_READ_NEW",
    "programs":   {},   # name -> {lines, includes_count, file}
    "includes":   {},   # name -> {parent, lines, file}
    "structures": {},   # name -> {fields_count, file}
    "functions":  {},   # name -> {lines, file}
    "missing":    [],   # any name we tried and could not fetch
}


def fetch_program(conn, name):
    """RPY_PROGRAM_READ — works for PROG and INCLUDE both. Returns (source, includes)."""
    try:
        r = conn.call("RPY_PROGRAM_READ",
                      PROGRAM_NAME=name,
                      WITH_INCLUDELIST='X',
                      WITH_LOWERCASE='X')
        # Source comes back as table of lines
        src_tab = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
        # SOURCE_EXTENDED is a table of rows like {'LINE': '   FORM xyz.'}
        if src_tab and isinstance(src_tab[0], dict):
            key = "LINE" if "LINE" in src_tab[0] else next(iter(src_tab[0].keys()))
            lines = [row[key] for row in src_tab]
        else:
            lines = list(src_tab)
        source = "\n".join(lines)

        # INCLUDETAB sometimes empty in this release — fall back to regex parse of source
        inctab = r.get("INCLUDETAB") or []
        includes = set()
        for row in inctab:
            inc_name = (row.get("INCLUDE") or row.get("INC_NAME") or "").strip()
            if inc_name:
                includes.add(inc_name.upper())
        # Regex fallback / supplement: every "INCLUDE <name>." statement
        for m in re.finditer(r'(?im)^\s*INCLUDE\s+([A-Z][A-Z0-9_/]*)\s*\.', source):
            includes.add(m.group(1).upper())
        return source, sorted(includes)
    except Exception as e:
        msg = str(e)
        return None, msg


def fetch_function(conn, fm_name):
    """RPY_FUNCTIONMODULE_READ_NEW — full FM source incl. interface."""
    try:
        r = conn.call("RPY_FUNCTIONMODULE_READ_NEW", FUNCTIONNAME=fm_name)
        # Returns multiple tables; we concatenate documentation + interface + source
        out = []
        for tabname in ("INCLUDE_TAB", "DOCUMENTATION", "EXCEPTION_LIST",
                        "EXPORT_PARAMETER", "IMPORT_PARAMETER",
                        "CHANGING_PARAMETER", "TABLES_PARAMETER",
                        "SOURCE", "GLOBAL_DATA"):
            tab = r.get(tabname)
            if tab:
                out.append(f"* === {tabname} ===")
                for row in tab:
                    if isinstance(row, dict):
                        out.append(" | ".join(f"{k}={v}" for k, v in row.items() if v))
                    else:
                        out.append(str(row))
        return "\n".join(out), None
    except Exception as e:
        return None, str(e)


def fetch_structure(conn, table_name):
    """DDIF_FIELDINFO_GET — works for tables, structures, views."""
    try:
        r = conn.call("DDIF_FIELDINFO_GET", TABNAME=table_name, ALL_TYPES='X')
        fields = r.get("DFIES_TAB") or []
        if not fields:
            return None, "DFIES_TAB empty"
        out = {
            "tabname": table_name,
            "tabkind": r.get("X030L_WA", {}).get("TABKIND") if r.get("X030L_WA") else None,
            "field_count": len(fields),
            "fields": [
                {
                    "fieldname": f.get("FIELDNAME"),
                    "position":  f.get("POSITION"),
                    "datatype":  f.get("DATATYPE"),
                    "inttype":   f.get("INTTYPE"),
                    "leng":      f.get("LENG"),
                    "decimals":  f.get("DECIMALS"),
                    "rollname":  f.get("ROLLNAME"),
                    "domname":   f.get("DOMNAME"),
                    "scrtext_l": f.get("SCRTEXT_L") or f.get("FIELDTEXT"),
                }
                for f in fields
            ],
        }
        return out, None
    except Exception as e:
        return None, str(e)


# === main ===
print(f"[{time.strftime('%H:%M:%S')}] Connecting to P01 (SNC/SSO)...")
guard = get_connection("P01")
print(f"[{time.strftime('%H:%M:%S')}] Connected.")

# 1) PROGRAMS — start with main drivers; recurse into all includes
seed_programs = ["SAPFPAYM", "RFFOAVIS_FPAYM"]
visited = set()
queue = list(seed_programs)

while queue:
    name = queue.pop(0).upper()
    if name in visited:
        continue
    visited.add(name)
    print(f"[{time.strftime('%H:%M:%S')}] PROG/INC: {name}")
    src, info = fetch_program(guard, name)
    if src is None:
        print(f"  [MISSING] {name}: {info}")
        manifest["missing"].append({"name": name, "kind": "PROG_OR_INC", "error": info})
        continue
    n_lines = src.count("\n") + 1
    fname = name.replace("/", "_")
    path = os.path.join(OUT_CODE, fname + ".abap")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    record = {
        "lines": n_lines, "bytes": len(src),
        "includes_count": len(info) if isinstance(info, list) else 0,
        "file": os.path.relpath(path, OUT_BASE),
    }
    if name in seed_programs:
        manifest["programs"][name] = record
    else:
        manifest["includes"][name] = record
    if isinstance(info, list):
        for inc in info:
            if inc not in visited:
                queue.append(inc)
    time.sleep(0.2)

print(f"\n[{time.strftime('%H:%M:%S')}] Programs+includes done: {len(visited)} fetched, {len(manifest['missing'])} missing.")

# 2) STRUCTURES — DDIC
struct_targets = [
    "FPAYH",        # Payment header (work area)
    "FPAYHX",       # Payment header extension (Z fields ZPFST/ZPLOR/ZLISO + AUSTO/AUST1-3)
    "FPAYP",        # Payment item (per vendor / per line)
    "FPAYPX",       # Payment item extension
    "FPAYHM",       # Header maintenance buffer
    "FPM_PAYTAB",   # Payment table interface
    "FPAY_HEAD_KEY",
    "FPAY_ITEM_KEY",
    "FPAYG",        # Grouping struct (referenced by SAPFPAYM)
    "REGUH",        # Run header (DB table; for cross-reference field list)
    "REGUP",        # Run position (DB table)
    "DMEE_TREE_HEAD",
    "DMEE_TREE_NODE",
    "DMEE_TREE_COND",
]
print(f"\n[{time.strftime('%H:%M:%S')}] Structures: fetching {len(struct_targets)}...")
for s in struct_targets:
    print(f"[{time.strftime('%H:%M:%S')}] STRUCT: {s}")
    out, err = fetch_structure(guard, s)
    if out is None:
        print(f"  [MISSING] {s}: {err}")
        manifest["missing"].append({"name": s, "kind": "DDIC", "error": err})
        continue
    path = os.path.join(OUT_STRUCT, s + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    manifest["structures"][s] = {
        "field_count": out["field_count"],
        "tabkind": out.get("tabkind"),
        "file": os.path.relpath(path, OUT_BASE),
    }
    time.sleep(0.2)

# 3) FUNCTIONS — DMEE engine + utilities (best-effort)
fm_targets = [
    "DMEE_API_GET_FILE_FROM_TREE",
    "DMEE_API_TREE_RUN",
    "DMEE_TREE_GET_INFO",
    "DMEE_GENERATE_FILE",
    "FI_PAYMEDIUM_DMEE_CGI_05",
    "FI_PAYMEDIUM_OPEN_FILE",
    "FI_PAYMEDIUM_CLOSE_FILE",
    "FI_PAYMEDIUM_GET_NEXT_DOC",
    "FI_PAYMEDIUM_INIT",
    "FI_PAYM_INIT_BUFFER",
    "FI_PAYM_BUFFER_FILL",
    "FI_PAYM_BUFFER_GET",
    "DMEE_INTERFACE_RUN_PARTNERID",
    "DMEE_INTERFACE_RUN_FORMAT_TREE",
    "DMEE_API_RUN_FORMAT_TREE",
]
print(f"\n[{time.strftime('%H:%M:%S')}] Function modules: probing {len(fm_targets)}...")
for fm in fm_targets:
    print(f"[{time.strftime('%H:%M:%S')}] FM: {fm}")
    out, err = fetch_function(guard, fm)
    if out is None:
        print(f"  [MISSING] {fm}: {err}")
        manifest["missing"].append({"name": fm, "kind": "FUNCTION", "error": err})
        continue
    path = os.path.join(OUT_FUNC, fm + ".abap")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    manifest["functions"][fm] = {
        "lines": out.count("\n") + 1,
        "file": os.path.relpath(path, OUT_BASE),
    }
    time.sleep(0.2)

# 4) Persist manifest
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\n[{time.strftime('%H:%M:%S')}] DONE.")
print(f"  Programs:   {len(manifest['programs'])}")
print(f"  Includes:   {len(manifest['includes'])}")
print(f"  Structures: {len(manifest['structures'])}")
print(f"  Functions:  {len(manifest['functions'])}")
print(f"  Missing:    {len(manifest['missing'])}")
print(f"  Manifest:   {MANIFEST}")
