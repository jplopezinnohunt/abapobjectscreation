"""
extract_bank_recon_family.py — D01 RFC+SNC extraction of the full UNESCO bank
reconciliation program family (YTBAE*, YTBAM*, YTBAI*, YFI_BANK_*).

Session #057 · 2026-04-20 — Follow-up to INC-000006906

Inputs:  list of candidate program names (from SE38 F4 screenshots + pattern expansion)
Outputs: extracted_code/CUSTOM/BANK_RECONCILIATION/{prog}/
         - {name}.abap
         - {name}.textelements.txt (if any)
         - {name}.includes.txt (if any)
         - _manifest.json
Plus a top-level _family_inventory.json with the classification per program.
"""
from __future__ import annotations

import io
import os
import re
import sys
import json
import datetime as _dt
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
OUT_ROOT = REPO / "extracted_code" / "CUSTOM" / "BANK_RECONCILIATION"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Candidate programs from SE38 F4 screenshots + HR-variant expansion
# ------------------------------------------------------------------
CANDIDATES = [
    # YT* family
    "YTBAE001", "YTBAE001_HR", "YTBAE002", "YTBAE002_HR",
    "YTBAI001", "YTBAI001_HR",
    "YTBAM001", "YTBAM001_HR",
    "YTBAM002", "YTBAM002_HR", "YTBAM002_HR_UBO",
    "YTBAM003", "YTBAM003_HR",
    "YTBAM004", "YTBAM004_HR",
    "YTBAM005", "YTBAM005_HR",
    # YFI_BANK_* family
    "YFI_BANK_RECONCILIATION",
    "YFI_BANK_RECONCILIATION_DATA",
    "YFI_BANK_RECONCILIATION_SEL",
    "YFI_BANK_RECONCILIATION_FORM",
    "YFI_BANK_RECONCILIATION_TOP",
    "YFI_BANK_RECONCILIATION_F01",
]


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
    return len(text_lines)


def extract_program(c: Connection, name: str, out_dir: Path) -> dict:
    try:
        r = c.call("RPY_PROGRAM_READ", PROGRAM_NAME=name)
    except Exception as e:
        return {"ok": False, "name": name, "error": f"{type(e).__name__}: {str(e)[:200]}"}

    src = r.get("SOURCE_EXTENDED") or r.get("SOURCE") or []
    if not src:
        return {"ok": False, "name": name, "error": "empty_source"}

    inc = r.get("INCLUDE_TAB") or []
    tel = r.get("TEXTELEMENTS") or []
    prog_inf = dict(r.get("PROG_INF") or {})

    out_dir.mkdir(parents=True, exist_ok=True)
    n = write_lines(out_dir / f"{name}.abap", src, "LINE")

    if inc:
        write_lines(out_dir / f"{name}.includes.txt", inc, "INCLUDE")
    if tel:
        (out_dir / f"{name}.textelements.txt").write_text(
            "\n".join(f"{row.get('NUM','')}\t{row.get('TEXT','')}" for row in tel),
            encoding="utf-8",
        )

    return {
        "ok": True,
        "name": name,
        "lines": n,
        "includes": [row.get("INCLUDE") for row in inc],
        "prog_inf": prog_inf,
    }


def get_tcode_for_program(c: Connection, program: str) -> list:
    """Lookup TSTC for TCODE bound to the program."""
    try:
        r = c.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TSTC",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"PGMNA = '{program}'"}],
            FIELDS=[{"FIELDNAME": "TCODE"}, {"FIELDNAME": "PGMNA"}],
        )
        rows = []
        for row in r.get("DATA", []) or []:
            wa = row.get("WA", "")
            parts = wa.split("|")
            if len(parts) >= 2:
                rows.append({"TCODE": parts[0].strip(), "PGMNA": parts[1].strip()})
        return rows
    except Exception as e:
        return [{"error": str(e)[:200]}]


def get_tadir(c: Connection, name: str) -> dict:
    """Lookup TADIR for authoring info (author, devclass, last change)."""
    try:
        r = c.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"OBJ_NAME = '{name}' AND OBJECT = 'PROG'"}],
            FIELDS=[
                {"FIELDNAME": "PGMID"},
                {"FIELDNAME": "OBJECT"},
                {"FIELDNAME": "OBJ_NAME"},
                {"FIELDNAME": "DEVCLASS"},
                {"FIELDNAME": "AUTHOR"},
                {"FIELDNAME": "SRCSYSTEM"},
                {"FIELDNAME": "MASTERLANG"},
            ],
        )
        for row in r.get("DATA", []) or []:
            wa = row.get("WA", "")
            parts = wa.split("|")
            if len(parts) >= 5:
                return {
                    "PGMID": parts[0].strip(),
                    "OBJECT": parts[1].strip(),
                    "OBJ_NAME": parts[2].strip(),
                    "DEVCLASS": parts[3].strip(),
                    "AUTHOR": parts[4].strip(),
                }
        return {}
    except Exception as e:
        return {"error": str(e)[:200]}


# ------------------------------------------------------------------
# Anti-pattern / classification scanners
# ------------------------------------------------------------------

# Loops: DO / LOOP (broad — we care about CALL TRANSACTION inside them)
LOOP_OPEN = re.compile(r"^\s*(LOOP\b|DO\b|WHILE\b)", re.IGNORECASE | re.MULTILINE)
LOOP_CLOSE = re.compile(r"^\s*(ENDLOOP|ENDDO|ENDWHILE)\b", re.IGNORECASE | re.MULTILINE)

# BDC / CALL TRANSACTION patterns
CALL_TX = re.compile(r"CALL\s+TRANSACTION\s+['\"]?([A-Z0-9_/\-]+)['\"]?(?:.*?MODE\s+([A-Z0-9_\-]+))?", re.IGNORECASE | re.DOTALL)
CONST_BDC_MODE = re.compile(
    r"(?:CONSTANTS?|DATA)\s*:?\s*([A-Z_][A-Z0-9_]*)\s+(?:TYPE\s+\S+)?\s*VALUE\s+['\"]([ANEP])['\"]",
    re.IGNORECASE,
)

SELECT_SINGLE_SKB1 = re.compile(r"SELECT\s+.*?FROM\s+SKB1", re.IGNORECASE | re.DOTALL)
RANGES_DECL = re.compile(r"RANGES?\s+([A-Z_][A-Z0-9_]*)\s+FOR\b", re.IGNORECASE)
IS_INITIAL_GUARD = re.compile(r"IF\s+([A-Z_][A-Z0-9_]*)(?:\[\])?\s+IS\s+NOT\s+INITIAL", re.IGNORECASE)

LDB_PATTERN = re.compile(r"(?:TABLES|NODES)\s*:?\s*(SDF|SAPDB\w+)", re.IGNORECASE)

def classify_source(abap_text: str, name: str) -> dict:
    """Return classification dict for a single .abap source blob."""
    lines = abap_text.splitlines()
    loc = len([l for l in lines if l.strip() and not l.strip().startswith("*")])

    # Find CALL TRANSACTION targets
    tx_hits = []
    for m in CALL_TX.finditer(abap_text):
        target = m.group(1).upper()
        mode_raw = m.group(2)
        tx_hits.append({"target": target, "mode_raw": (mode_raw or "").upper(), "offset": m.start()})

    # Find CONSTANTS / DATA ... VALUE 'X' for BDC mode
    const_hits = []
    for m in CONST_BDC_MODE.finditer(abap_text):
        cname = m.group(1).upper()
        cval = m.group(2).upper()
        # approximate line number
        line_no = abap_text[: m.start()].count("\n") + 1
        const_hits.append({"const": cname, "value": cval, "line": line_no})

    # Resolve BDC mode for each CALL TRANSACTION hit
    for hit in tx_hits:
        resolved = None
        # direct literal mode?
        if hit["mode_raw"] in ("'A'", "'E'", "'N'", "'P'", "A", "E", "N", "P"):
            resolved = hit["mode_raw"].strip("'")
        else:
            # If MODE is followed by a constant name, look it up in const_hits
            mr = hit["mode_raw"].strip("'")
            for c in const_hits:
                if c["const"] == mr:
                    resolved = c["value"]
                    break
        hit["resolved_mode"] = resolved
        # Approximate line no of the CALL TRANSACTION
        hit["line"] = abap_text[: hit["offset"]].count("\n") + 1

    # Anti-pattern: any CALL TRANSACTION with MODE 'E' somewhere in a loop body.
    # We approximate "inside a loop" by counting LOOP-open vs LOOP-close before offset.
    mode_e_in_loop = []
    # Build a sorted list of loop-open/close offsets
    opens = [m.start() for m in LOOP_OPEN.finditer(abap_text)]
    closes = [m.start() for m in LOOP_CLOSE.finditer(abap_text)]
    for hit in tx_hits:
        if hit["resolved_mode"] == "E":
            nop = sum(1 for o in opens if o < hit["offset"])
            ncl = sum(1 for c in closes if c < hit["offset"])
            if nop > ncl:
                mode_e_in_loop.append(hit)

    # Empty-range guard: find RANGES declarations and check for IS NOT INITIAL guards
    ranges_declared = [m.group(1).upper() for m in RANGES_DECL.finditer(abap_text)]
    guards = set(m.group(1).upper() for m in IS_INITIAL_GUARD.finditer(abap_text))
    unguarded_ranges = [r for r in ranges_declared if r not in guards]

    # LDB usage
    ldb_hits = [m.group(1).upper() for m in LDB_PATTERN.finditer(abap_text)]

    # SELECT from SKB1 (the source of bank GL for INC-000006906)
    uses_skb1 = bool(SELECT_SINGLE_SKB1.search(abap_text))

    # Type: EXECUTABLE vs INCLUDE vs MODULE_POOL — decided upstream from PROG_TYPE
    # but also from INCLUDE naming convention (ends in _DATA/_SEL/_FORM/_TOP/_F01 usually)

    return {
        "loc": loc,
        "call_transaction": tx_hits,
        "bdc_mode_constants": const_hits,
        "mode_e_in_loop_hits": mode_e_in_loop,
        "ranges_declared": ranges_declared,
        "unguarded_ranges": unguarded_ranges,
        "uses_ldb": ldb_hits,
        "uses_skb1_select": uses_skb1,
    }


def main() -> None:
    c = connect_d01()
    print("[OK] Connected to P01/D01 via SNC")

    family_inventory = {
        "_extracted_at": _dt.datetime.now().isoformat(),
        "programs": {},
        "summary": {},
    }

    success = []
    failed = []

    for name in CANDIDATES:
        print(f"\n====== {name} ======")
        out_dir = OUT_ROOT / name
        # 1) Extract source
        res = extract_program(c, name, out_dir)
        if not res.get("ok"):
            print(f"  [SKIP] {res.get('error')}")
            failed.append({"name": name, "reason": res.get("error")})
            family_inventory["programs"][name] = {"status": "missing", "error": res.get("error")}
            continue
        success.append(name)
        print(f"  [OK] {res['lines']} LOC, {len(res.get('includes') or [])} includes")

        # 2) TADIR + TSTC
        tadir = get_tadir(c, name)
        tcode_rows = get_tcode_for_program(c, name)

        # 3) Classification from source
        abap_text = (out_dir / f"{name}.abap").read_text(encoding="utf-8", errors="replace")
        clf = classify_source(abap_text, name)

        # 4) Recursively extract includes referenced by this program
        include_list = res.get("includes") or []
        include_results = []
        for inc_name in include_list:
            if not inc_name:
                continue
            inc_res = extract_program(c, inc_name, out_dir)
            include_results.append(inc_res)

        # 5) Manifest per program
        manifest = {
            "name": name,
            "prog_inf": res.get("prog_inf"),
            "tadir": tadir,
            "tcode_bindings": tcode_rows,
            "includes_directly_referenced": include_list,
            "include_extract_results": include_results,
            "classification": clf,
        }
        (out_dir / "_manifest.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8"
        )

        family_inventory["programs"][name] = {
            "status": "ok",
            "loc": clf["loc"],
            "author": tadir.get("AUTHOR"),
            "devclass": tadir.get("DEVCLASS"),
            "creat_user": res.get("prog_inf", {}).get("CREAT_USER"),
            "creat_date": res.get("prog_inf", {}).get("CREAT_DATE"),
            "mod_user": res.get("prog_inf", {}).get("MOD_USER"),
            "mod_date": res.get("prog_inf", {}).get("MOD_DATE"),
            "prog_type": res.get("prog_inf", {}).get("PROG_TYPE"),
            "tcode_bindings": tcode_rows,
            "includes_directly_referenced": include_list,
            "call_transaction_targets": [h["target"] for h in clf["call_transaction"]],
            "bdc_mode_constants": clf["bdc_mode_constants"],
            "mode_e_in_loop_count": len(clf["mode_e_in_loop_hits"]),
            "mode_e_in_loop_hits": [
                {"target": h["target"], "line": h["line"], "resolved_mode": h["resolved_mode"]}
                for h in clf["mode_e_in_loop_hits"]
            ],
            "ranges_declared": clf["ranges_declared"],
            "unguarded_ranges": clf["unguarded_ranges"],
            "uses_ldb": clf["uses_ldb"],
            "uses_skb1_select": clf["uses_skb1_select"],
        }

    family_inventory["summary"] = {
        "candidates_checked": len(CANDIDATES),
        "extracted_ok": len(success),
        "missing": len(failed),
        "missing_list": failed,
        "ok_list": success,
    }

    out_path = OUT_ROOT / "_family_inventory.json"
    out_path.write_text(json.dumps(family_inventory, indent=2, default=str), encoding="utf-8")
    print(f"\n[DONE] Family inventory written: {out_path.relative_to(REPO)}")
    print(f"[STATS] ok={len(success)}  missing={len(failed)}")


if __name__ == "__main__":
    main()
