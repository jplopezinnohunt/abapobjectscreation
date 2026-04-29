"""
extract_ytbae002.py — D01 RFC+SNC extraction of YTBAE002 + all dependencies.

Session #057 · 2026-04-20 — INC-000006906

Why RFC not ADT: D01 password is locked ("too many failed attempts"). SNC/SSO
via pyrfc works fine, so we use RPY_PROGRAM_READ / RPY_INCLUDE_READ (legacy but
SNC-safe) instead of ADT HTTP Basic.

Outputs to: extracted_code/CUSTOM/YTBAE002/
"""
from __future__ import annotations

import io
import os
import re
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, errors="replace", encoding="utf-8")

from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

from pyrfc import Connection  # noqa: E402

REPO = HERE.parent.parent
OUT = REPO / "extracted_code" / "CUSTOM" / "YTBAE002"
OUT.mkdir(parents=True, exist_ok=True)


def connect_d01() -> Connection:
    return Connection(
        ashost=os.getenv("SAP_ASHOST"),
        sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"),
        user=os.getenv("SAP_USER"),
        lang="EN",
        snc_mode=os.getenv("SAP_SNC_MODE", "1"),
        snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"),
        snc_qop=os.getenv("SAP_SNC_QOP", "9"),
    )


def write_lines(path: Path, lines: list, field: str = "LINE") -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text_lines = []
    for ln in lines:
        if isinstance(ln, dict):
            text_lines.append(ln.get(field, "") or "")
        else:
            text_lines.append(str(ln))
    text = "\n".join(text_lines)
    path.write_text(text, encoding="utf-8")
    print(f"  [OUT] {path.relative_to(REPO)}  ({len(text_lines)} lines, {len(text)} chars)")
    return len(text_lines)


def extract_program(c: Connection, name: str) -> dict:
    """Uses RPY_PROGRAM_READ. Returns {source_lines, include_tab, text_elements}."""
    print(f"\n=== PROG {name} ===")
    try:
        r = c.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__} {e}")
        return {"ok": False, "error": str(e)[:300]}

    src = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
    inc = r.get("INCLUDE_TAB") or []
    tel = r.get("TEXTELEMENTS") or []
    prog_inf = r.get("PROG_INF") or {}

    n = write_lines(OUT / f"{name}.abap", src, "LINE")
    if inc:
        write_lines(OUT / f"{name}.includes.txt", inc, "INCLUDE")
    if tel:
        # text elements have NUM + TEXT typically
        te_path = OUT / f"{name}.textelements.txt"
        te_path.write_text(
            "\n".join(f"{row.get('NUM','')}\t{row.get('TEXT','')}" for row in tel),
            encoding="utf-8",
        )
        print(f"  [OUT] {te_path.relative_to(REPO)}  ({len(tel)} text elements)")
    return {
        "ok": True,
        "name": name,
        "lines": n,
        "includes": [row.get("INCLUDE") for row in inc],
        "prog_inf": dict(prog_inf),
    }


def extract_include(c: Connection, name: str) -> dict:
    """RPY_PROGRAM_READ works on includes too. Fallback to REPOSRC if missing."""
    print(f"\n--- INCLUDE {name} ---")
    try:
        r = c.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
        src = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
        if not src:
            return {"ok": False, "name": name, "reason": "empty"}
        n = write_lines(OUT / f"{name}.abap", src, "LINE")
        return {"ok": True, "name": name, "lines": n}
    except Exception as e:
        print(f"  [FAIL] {name}: {type(e).__name__} {str(e)[:200]}")
        return {"ok": False, "name": name, "error": str(e)[:200]}


def main() -> None:
    c = connect_d01()
    print("Connected D01 via SNC")

    manifest = {"program": None, "includes": [], "custom_calls": {}, "tcode": None}

    # 1) Main program
    pr = extract_program(c, "YTBAE002")
    manifest["program"] = pr
    if not pr.get("ok"):
        sys.exit(1)

    # 2) Parse INCLUDE directives from main source (INCLUDE_TAB is best, but
    # fallback to regex for safety)
    includes_from_rfc = set(pr.get("includes") or [])
    main_src = (OUT / "YTBAE002.abap").read_text(encoding="utf-8")
    inc_pat = re.compile(r"^\s*INCLUDE\s+([A-Z0-9_/]+)\s*\.", re.IGNORECASE | re.MULTILINE)
    includes_from_regex = set(m.group(1).upper() for m in inc_pat.finditer(main_src))
    all_includes = sorted(includes_from_rfc | includes_from_regex)
    print(f"\n[INCLUDES] {len(all_includes)} unique includes to extract")
    print("  from RFC INCLUDE_TAB:", sorted(includes_from_rfc))
    print("  from regex:", sorted(includes_from_regex - includes_from_rfc))

    for inc_name in all_includes:
        # Skip SAP-standard includes (non-Y/Z namespace) unless user wants them.
        # For this task, keep Y*/Z* AND any include directly named in the program.
        res = extract_include(c, inc_name)
        manifest["includes"].append(res)

    # 3) Parse the full corpus (main + includes) for calls to Y/Z classes, FMs,
    # and interfaces. We do this AFTER all includes are downloaded so we see
    # the whole code.
    corpus_files = sorted(OUT.glob("*.abap"))
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in corpus_files)

    # Function module calls (CALL FUNCTION 'ZFOO' / 'YFOO')
    fm_pat = re.compile(r"CALL\s+FUNCTION\s+'([YZ][A-Z0-9_/]+)'", re.IGNORECASE)
    fms = sorted(set(m.group(1).upper() for m in fm_pat.finditer(corpus)))
    print(f"\n[CUSTOM FMs] {len(fms)} distinct")
    for fm in fms:
        print(f"  - {fm}")

    # Class static / instance method calls: Y*=>method( or Z*=>
    cls_pat = re.compile(r"\b([YZ][A-Z0-9_]+)=>", re.IGNORECASE)
    classes = sorted(set(m.group(1).upper() for m in cls_pat.finditer(corpus)))
    print(f"\n[CUSTOM CLASSES] {len(classes)} distinct (static refs)")
    for cls in classes:
        print(f"  - {cls}")

    # TYPE / CREATE OBJECT references to Y/Z classes
    type_pat = re.compile(r"\b(?:TYPE\s+REF\s+TO|CREATE\s+OBJECT)\s+([YZ][A-Z0-9_]+)", re.IGNORECASE)
    types = sorted(set(m.group(1).upper() for m in type_pat.finditer(corpus)))
    print(f"\n[CUSTOM TYPE REFs] {len(types)} distinct")

    # Interfaces (INTERFACE Y* or implementing)
    intf_pat = re.compile(r"\bINTERFACES\s+([YZ][A-Z0-9_]+)", re.IGNORECASE)
    intfs = sorted(set(m.group(1).upper() for m in intf_pat.finditer(corpus)))
    print(f"\n[CUSTOM INTERFACES] {len(intfs)} distinct")

    # SET reads — key for our investigation
    set_pat = re.compile(
        r"\b(?:RS_SET_VALUES_READ|G_SET_GET_ALL_VALUES|K_HIERARCHY_TABLES_READ|G_SET_LIST_READ|G_SET_FETCH)\b",
        re.IGNORECASE,
    )
    set_hits = [(m.group(0).upper(), corpus.count(m.group(0))) for m in set_pat.finditer(corpus)]
    set_unique = sorted(set(k for k, _ in set_hits))
    print(f"\n[SET-TABLE FMs] {set_unique}")

    # BSIS/BSAS SELECT patterns
    sel_bsis_pat = re.compile(r"(?:SELECT|FROM)\s+(?:BSIS|BSAS|BSEG|BSID|BSAD|BSIK|BSAK)\b", re.IGNORECASE)
    n_bsis = len(sel_bsis_pat.findall(corpus))
    print(f"\n[BSIS/BSAS/BSEG SELECTs] {n_bsis} hits")

    # LDB SELECTION-SCREEN references
    ldb_pat = re.compile(r"\bSELECTION-SCREEN\b|\bGET\s+(?:BKPF|BSEG|BSIS|BSAS)\b", re.IGNORECASE)
    n_ldb = len(ldb_pat.findall(corpus))
    print(f"\n[SELECTION-SCREEN / GET events] {n_ldb} hits")

    manifest["custom_calls"] = {
        "function_modules": fms,
        "classes_static": classes,
        "type_refs": types,
        "interfaces": intfs,
        "set_reads": set_unique,
        "bsis_selects": n_bsis,
        "selection_screen_hits": n_ldb,
    }

    # 4) Extract each Y/Z function module with RFC_READ_TABLE(TFDIR) + FUNCTION_IMPORT_INTERFACE or RPY_FUNCTIONMODULE_READ
    for fm in fms:
        print(f"\n--- FM {fm} ---")
        try:
            r = c.call("RPY_FUNCTIONMODULE_READ", FUNCTIONNAME=fm)
            src = r.get("SOURCE") or []
            if src:
                write_lines(OUT / f"FM_{fm}.abap", src, "LINE")
            else:
                print("  [EMPTY]")
        except Exception as e:
            print(f"  [FAIL] {type(e).__name__} {str(e)[:200]}")

    # 5) Extract each Y/Z class (via SEO_CLASS_GET_METHOD_INCLUDE or RPY_CLASS_READ)
    # Use SEO_CLASS_READ_ALL — legacy but works
    for cls in classes:
        print(f"\n--- CLASS {cls} ---")
        try:
            # Fallback to REPOSRC for class main section include <cls>==========CCDEF, CCIMP, CCMAC, CCAU, CM001..N, CP, CI
            # We'll just grab CL_<name> skeleton via SEO_CLIF_GET
            r = c.call("SEO_CLASS_READ", CLSKEY={"CLSNAME": cls})
            # If no SOURCE lines, try RPY_CLASS_READ_F30
            print(f"  info keys: {list(r.keys())[:6]}")
        except Exception:
            try:
                # Fallback: read main include <cls>==========CP and similar via RPY_PROGRAM_READ
                for suffix in ("CCDEF", "CCIMP", "CCMAC", "CCAU", "CP", "CI", "CS"):
                    incname = f"{cls}=={'=' * (30 - len(cls) - len(suffix))}{suffix}"
                    # name must be 30 chars: <cls>=<pad>==<suf>  actually "cls=========...=CP"
                    pad = 30 - len(cls) - len(suffix)
                    if pad < 1:
                        continue
                    incname = cls + "=" * pad + suffix
                    try:
                        rr = c.call("RPY_PROGRAM_READ", PROGRAM_NAME=incname)
                        src = rr.get("SOURCE_EXTENDED") or rr.get("SOURCE") or []
                        if src:
                            write_lines(OUT / f"CLS_{cls}_{suffix}.abap", src, "LINE")
                    except Exception as ie:
                        pass
            except Exception as e:
                print(f"  [FAIL] {type(e).__name__} {str(e)[:200]}")

    # 6) TCODE YTR3 binding (Gold DB or live TSTC via RFC_READ_TABLE)
    print("\n=== TCODE YTR3 ===")
    try:
        r = c.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TSTC",
            DELIMITER="|",
            OPTIONS=[{"TEXT": "TCODE = 'YTR3'"}],
            FIELDS=[{"FIELDNAME": "TCODE"}, {"FIELDNAME": "PGMNA"}, {"FIELDNAME": "DYPNO"}, {"FIELDNAME": "CINFO"}],
        )
        rows = r.get("DATA", [])
        for row in rows:
            print(f"  {row.get('WA','')}")
        manifest["tcode"] = rows
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__} {str(e)[:200]}")

    # 7) Manifest
    (OUT / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    print(f"\n[DONE] Manifest: {(OUT / '_manifest.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
