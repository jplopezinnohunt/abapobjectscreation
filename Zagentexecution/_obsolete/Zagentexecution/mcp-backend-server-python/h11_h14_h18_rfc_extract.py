"""
h11_h14_h18_rfc_extract.py — RFC-based source extraction (no ADT, no password)

Session #038 · 2026-04-05

Channel: RFC via SNC/SSO — the SAME channel that H29 used for 1,690 UPDATEs.
No .env password. No HTTP Basic Auth. No ADT. Just RFC_READ_TABLE + RFC_ABAP_INSTALL_AND_RUN.

Method
------
For each target object, run an ABAP program via RFC_ABAP_INSTALL_AND_RUN that:
  1. READ REPORT '<name>' INTO lt_source.
  2. LOOP AT lt_source. WRITE: / <line>. ENDLOOP.
The WRITES come back in the RFC response.

For function modules, use RPY_FUNCTIONMODULE_READ (direct RFC, simpler).

Targets (PMO names vs verified names via TADIR probe):
  H18 DMEE    — YCL_IDFI_CGI_DMEE_FR / _FALLBACK / _UTIL  (PMO said _AE/_BH; those don't exist)
  H14 YWFI    — 37 objects in DEVCLASS='YWFI' (verified via probe)
                key: ZWF_GET_CERTIFYING_OFFICER (FUGR, not Z_WF_* as PMO said)
  H11 HCMFAB  — ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT (correctly named in PMO)
                also sibling classes in DEVCLASS='ZFIORI'
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, errors="replace", encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa: E402

REPO = HERE.parent.parent
OUT = REPO / "extracted_code"


def parse_wa(data_rows, fields) -> list[dict]:
    out = []
    for row in data_rows:
        wa = row.get("WA", "")
        vals = {}
        for f in fields:
            off = int(f.get("OFFSET", 0))
            ln = int(f.get("LENGTH", 0))
            vals[f["FIELDNAME"]] = wa[off:off + ln].strip()
        out.append(vals)
    return out


def tadir_query(guard, where: str, max_rows: int = 200) -> list[dict]:
    """Search TADIR for objects matching a WHERE clause."""
    res = guard.call(
        "RFC_READ_TABLE",
        QUERY_TABLE="TADIR",
        FIELDS=[{"FIELDNAME": f} for f in ("PGMID", "OBJECT", "OBJ_NAME", "DEVCLASS")],
        OPTIONS=[{"TEXT": where}],
        ROWCOUNT=max_rows,
    )
    return parse_wa(res.get("DATA", []), res.get("FIELDS", []))


def read_report(guard, report_name: str) -> str | None:
    """Read an ABAP report/class-include source via RFC_ABAP_INSTALL_AND_RUN."""
    abap = [
        "REPORT Z_H11_RD.",
        "DATA: lt TYPE TABLE OF string, lw TYPE string.",
        f"READ REPORT '{report_name}' INTO lt.",
        "IF sy-subrc = 0.",
        "  LOOP AT lt INTO lw.",
        "    WRITE: / lw.",
        "  ENDLOOP.",
        "ELSE.",
        "  WRITE: / '*** NOT FOUND ***'.",
        "ENDIF.",
    ]
    src = [{"LINE": line[:72]} for line in abap]
    try:
        res = guard.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
    except Exception as e:
        print(f"    [ERROR] read_report({report_name}): {e}")
        return None
    writes = res.get("WRITES", [])
    if not writes:
        return None
    lines = [w.get("ZEILE", "") for w in writes]
    if lines and "*** NOT FOUND ***" in lines[0]:
        return None
    return "\n".join(lines)


def read_class_source(guard, class_name: str) -> dict:
    """Read all class source parts via READ REPORT on the class-pool includes.

    ABAP classes generate synthetic include names:
      CL_XXX==========CCDEF  (public section declarations / predefs)
      CL_XXX==========CCIMP  (implementation — the code)
      CL_XXX==========CCMAC  (macros)
      CL_XXX==========CCAU   (unit tests)
      CL_XXX==========CP     (class pool header)
      CL_XXX==========CO     (class-pool includes — attributes/consts)
      CL_XXX==========CU     (types/methods declarations)
    Class name is padded to 30 chars with '=' then followed by the suffix.
    """
    padded = class_name.ljust(30, "=")
    parts = {}
    for suffix in ("CCDEF", "CCIMP", "CCMAC", "CCAU", "CP", "CO", "CU"):
        include_name = padded + suffix
        src = read_report(guard, include_name)
        if src:
            parts[suffix] = src
    return parts


def extract_class(guard, class_name: str, outdir: Path) -> dict:
    print(f"\n--- CLASS {class_name} ---")
    outdir.mkdir(parents=True, exist_ok=True)
    parts = read_class_source(guard, class_name)
    if not parts:
        print(f"  [NOT FOUND] {class_name} (no class-pool includes readable)")
        return {"name": class_name, "parts": 0, "size": 0}
    total = 0
    for suffix, src in parts.items():
        fp = outdir / f"{class_name}_{suffix}.abap"
        fp.write_text(src, encoding="utf-8")
        total += len(src)
        print(f"  [OUT] {fp.relative_to(REPO)}  ({len(src)} chars)")
    return {"name": class_name, "parts": len(parts), "size": total}


def extract_program(guard, prog_name: str, outdir: Path) -> dict:
    print(f"\n--- PROG {prog_name} ---")
    outdir.mkdir(parents=True, exist_ok=True)
    src = read_report(guard, prog_name)
    if not src:
        print(f"  [NOT FOUND] {prog_name}")
        return {"name": prog_name, "size": 0}
    fp = outdir / f"{prog_name}.abap"
    fp.write_text(src, encoding="utf-8")
    print(f"  [OUT] {fp.relative_to(REPO)}  ({len(src)} chars)")
    return {"name": prog_name, "size": len(src)}


def extract_function_module(guard, fm_name: str, outdir: Path) -> dict:
    """Read a FM via RPY_FUNCTIONMODULE_READ (direct RFC, cleaner than READ REPORT)."""
    print(f"\n--- FM {fm_name} ---")
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        res = guard.call("RPY_FUNCTIONMODULE_READ", FUNCTIONNAME=fm_name)
    except Exception as e:
        print(f"  [ERROR] {e}")
        return {"name": fm_name, "size": 0}
    src_lines = [r.get("LINE", "") for r in res.get("INCLUDE_SRC", [])]
    if not src_lines:
        # Some FMs are in function-group main includes — try via READ REPORT on the FUGR include
        print(f"  [EMPTY INCLUDE_SRC] — FM may be in main LFxxxxxUXX include")
        return {"name": fm_name, "size": 0, "empty": True}
    src = "\n".join(src_lines)
    fp = outdir / f"{fm_name}.abap"
    fp.write_text(src, encoding="utf-8")
    print(f"  [OUT] {fp.relative_to(REPO)}  ({len(src)} chars)")
    return {"name": fm_name, "size": len(src)}


def read_function_group_mains(guard, fugr_name: str, outdir: Path) -> list[dict]:
    """A function group is stored as includes: LFUGR_NAMETOP, LFUGR_NAMEUXX, LFUGR_NAMEU01 etc.
    Read them via READ REPORT.
    """
    print(f"\n--- FUGR {fugr_name} (includes) ---")
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    # Common suffixes: TOP (data decl), UXX (FM function calls), U01..U99 (individual FMs), F01..F99 (forms)
    candidates = [f"L{fugr_name}TOP", f"L{fugr_name}UXX"] + \
                 [f"L{fugr_name}U{i:02d}" for i in range(1, 20)] + \
                 [f"L{fugr_name}F{i:02d}" for i in range(1, 10)]
    for inc in candidates:
        src = read_report(guard, inc)
        if src and "*** NOT FOUND ***" not in src:
            fp = outdir / f"{inc}.abap"
            fp.write_text(src, encoding="utf-8")
            results.append({"include": inc, "size": len(src)})
            print(f"  [OUT] {fp.relative_to(REPO)}  ({len(src)} chars)")
        time.sleep(0.3)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Block targets
# ═══════════════════════════════════════════════════════════════════════════


def run_h18(guard) -> dict:
    """H18: DMEE YCL_IDFI_CGI_DMEE_FR + _FALLBACK + _UTIL. Find <Purp><Cd> literal."""
    print("\n" + "=" * 60)
    print("  H18 — DMEE PPC XML Purp/Cd")
    print("=" * 60)
    out = OUT / "DMEE"
    results = []
    targets = ["YCL_IDFI_CGI_DMEE_FR", "YCL_IDFI_CGI_DMEE_FALLBACK", "YCL_IDFI_CGI_DMEE_UTIL"]
    for cls in targets:
        info = extract_class(guard, cls, out)
        results.append(info)
        # Grep for Purp/Cd literal in the extracted source
        if info["parts"] > 0:
            import re
            for suffix_file in out.glob(f"{cls}_*.abap"):
                text = suffix_file.read_text(encoding="utf-8", errors="replace")
                # Hunt for 3-5 char codes near Purp
                for pat in [
                    r"<Purp><Cd>([^<]+)</Cd></Purp>",
                    r"Purp[^\n]{0,200}?['\"]([A-Z][A-Z0-9]{2,4})['\"]",
                    r"cd_[a-z]+\s*=\s*['\"]([A-Z][A-Z0-9]{2,4})['\"]",
                ]:
                    for m in re.finditer(pat, text, re.IGNORECASE):
                        print(f"    [PPC HIT] {suffix_file.name}: {m.group(0)[:80]}")
    return {"classes": results}


def run_h14(guard) -> dict:
    """H14: YWFI package — extract all relevant objects."""
    print("\n" + "=" * 60)
    print("  H14 — YWFI package")
    print("=" * 60)
    out = OUT / "YWFI"
    objs = tadir_query(guard, "DEVCLASS = 'YWFI'", max_rows=100)
    print(f"  {len(objs)} objects in YWFI package")

    summary = {"classes": [], "programs": [], "fugrs": [], "skipped": []}

    for o in objs:
        obj_type = o["OBJECT"]
        name = o["OBJ_NAME"]
        if obj_type == "CLAS":
            info = extract_class(guard, name, out / "CLAS")
            summary["classes"].append(info)
        elif obj_type == "PROG":
            info = extract_program(guard, name, out / "PROG")
            summary["programs"].append(info)
        elif obj_type == "FUGR":
            includes = read_function_group_mains(guard, name, out / "FUGR" / name)
            summary["fugrs"].append({"name": name, "includes": len(includes)})
        else:
            summary["skipped"].append({"type": obj_type, "name": name})
    return summary


def run_h11(guard) -> dict:
    """H11: HCMFAB BSP + related HCM Z-reports."""
    print("\n" + "=" * 60)
    print("  H11 — HCMFAB Benefits + MyFamily + HCM Z-reports")
    print("=" * 60)
    out = OUT / "HCM"
    summary = {"classes": [], "bsps": [], "zreports": []}

    # Step 1: extract the key HCMFAB classes
    for cls in [
        "ZCL_ZHCMFAB_MYFAMILYME_DPC",
        "ZCL_ZHCMFAB_MYFAMILYME_DPC_EXT",
        "ZCL_ZHCMFAB_MYFAMILYME_MPC",
        "ZCL_ZHCMFAB_MYFAMILYME_MPC_EXT",
    ]:
        info = extract_class(guard, cls, out / "CLAS")
        summary["classes"].append(info)

    # Step 2: list BSP applications in ZFIORI / HCM-related packages
    print("\n--- BSP discovery ---")
    bsps = tadir_query(guard, "OBJECT = 'WAPA' AND DEVCLASS LIKE 'ZFIORI%'", max_rows=50)
    print(f"  {len(bsps)} BSP apps in ZFIORI* package")
    for b in bsps[:20]:
        print(f"    {b['OBJ_NAME']}  devclass={b['DEVCLASS']}")
    summary["bsps"] = bsps

    # Step 3: HCM Z-reports — discover Z* programs in HR-ish packages
    print("\n--- HCM Z-reports discovery ---")
    zprogs = tadir_query(
        guard,
        "OBJECT = 'PROG' AND (OBJ_NAME LIKE 'Z_HR%' OR OBJ_NAME LIKE 'ZHR%' OR OBJ_NAME LIKE 'Z_HCM%' OR OBJ_NAME LIKE 'ZHCM%')",
        max_rows=100,
    )
    print(f"  {len(zprogs)} HCM-namespace Z programs")
    # Extract first 10
    extracted = 0
    for p in zprogs:
        if extracted >= 10:
            break
        info = extract_program(guard, p["OBJ_NAME"], out / "Z_Reports")
        if info["size"] > 0:
            summary["zreports"].append(info)
            extracted += 1
    return summary


def main() -> int:
    print("=" * 60)
    print("  H11 / H14 / H18 — RFC Source Extraction")
    print("  Channel: RFC via SNC/SSO (no password)")
    print("=" * 60)

    guard = get_connection("D01")
    try:
        results = {}
        results["H18"] = run_h18(guard)
        results["H14"] = run_h14(guard)
        results["H11"] = run_h11(guard)
    finally:
        guard.close()

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"\nH18: {len(results['H18']['classes'])} DMEE classes probed")
    for c in results["H18"]["classes"]:
        print(f"  {c['name']:35s} parts={c['parts']}  size={c['size']}")
    print(f"\nH14: YWFI package")
    print(f"  CLASS : {len(results['H14']['classes'])}")
    print(f"  PROG  : {len(results['H14']['programs'])}")
    print(f"  FUGR  : {len(results['H14']['fugrs'])}")
    print(f"  skip  : {len(results['H14']['skipped'])}")
    print(f"\nH11:")
    print(f"  HCMFAB classes: {sum(1 for c in results['H11']['classes'] if c['parts']>0)} / {len(results['H11']['classes'])}")
    print(f"  BSP apps found: {len(results['H11']['bsps'])}")
    print(f"  Z-reports extracted: {len(results['H11']['zreports'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
