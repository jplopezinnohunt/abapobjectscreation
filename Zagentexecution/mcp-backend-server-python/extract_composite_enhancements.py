# -*- coding: utf-8 -*-
"""
extract_composite_enhancements.py
==================================
Extracts all composite enhancement implementations (ENHO) from SAP,
using RFC_READ_TABLE and SIW_RFC_READ_REPORT. 

Targets the 12 composite enhancements visible in SE20:
  Z_ICTP_PO_HOSTGUEST, ZCL_HCMFAB_ASR_PROCESS, ZCOMP_ENH_SF,
  ZENH_DOCX, ZENH_PAWF_INT_AGREE, ZENH_REFX_CONTRACT_UNESCO,
  ZFIX_EXCHANGERATE, ZHR_FIORI_0021, ZHR_PENSION, ZHR_PERS_DATA,
  ZHR_SPAU_PA, ZHR_SPAU_PY_CPSIT_PGM_001

For each enhancement it:
  1. Reads SXS_ATTR (ENHO header + description)
  2. Reads ENHLOG / TADIR to resolve the implementing class or program
  3. Reads ENHO source via SIW_RFC_READ_REPORT on the ABAP include
  4. Reads all method CM-includes when the implementation is a class
  5. Saves all code to extracted_code/ENHO/<ENHANCEMENT_NAME>/
  6. Prints a domain + Fiori impact summary

Usage:
  python extract_composite_enhancements.py            # extracts all 12
  python extract_composite_enhancements.py ZHR_PENSION  # single one
"""

import os
import sys
import json
from sap_utils import get_sap_connection

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "extracted_code", "ENHO")

# ──────────────────────────────────────────────────────────────────────────────
# TARGET LIST  (from SE20 screenshot)
# ──────────────────────────────────────────────────────────────────────────────
ENHANCEMENTS = [
    {
        "name":        "Z_ICTP_PO_HOSTGUEST",
        "description": "New page host guest po printing",
        "domain":      "Procurement / PO",
        "fiori_impact": False,
        "notes":       "ICTP = inter-company purchase order; likely MM/SD"
    },
    {
        "name":        "ZCL_HCMFAB_ASR_PROCESS",
        "description": "Change attributes of process",
        "domain":      "HCM / ASR",
        "fiori_impact": True,
        "notes":       "HCMFAB ASR = Fiori HR Forms-based process; affects Fiori HR apps"
    },
    {
        "name":        "ZCOMP_ENH_SF",
        "description": "Composite enhancement Imp for SuccessFactor",
        "domain":      "HCM / SuccessFactors Integration",
        "fiori_impact": True,
        "notes":       "SF integration layer; may affect OData services for iFlow/BTP"
    },
    {
        "name":        "ZENH_DOCX",
        "description": "Enhancement for DOCX",
        "domain":      "Output / Documents",
        "fiori_impact": False,
        "notes":       "DOCX generation / Smart Forms / Adobe Forms output"
    },
    {
        "name":        "ZENH_PAWF_INT_AGREE",
        "description": "Enhancement WF Internship agreement",
        "domain":      "HCM / Workflow",
        "fiori_impact": True,
        "notes":       "PA Workflow for internship agreement — may touch Fiori Inbox / ASR"
    },
    {
        "name":        "ZENH_REFX_CONTRACT_UNESCO",
        "description": "Contract Validations and Substitutions",
        "domain":      "RE-FX / Contract Management",
        "fiori_impact": False,
        "notes":       "RE-FX custom UNESCO contract logic; classic Dynpro likely"
    },
    {
        "name":        "ZFIX_EXCHANGERATE",
        "description": "FIX Exchange rate",
        "domain":      "FI / Treasury",
        "fiori_impact": False,
        "notes":       "FI exchange rate fix; OB07/OB08 area"
    },
    {
        "name":        "ZHR_FIORI_0021",
        "description": "Enhancement composite family member app",
        "domain":      "HCM / Fiori Family Members",
        "fiori_impact": True,
        "notes":       "Direct Fiori app enhancement — HCMFAB_MYFAMILYMEMBERS service"
    },
    {
        "name":        "ZHR_PENSION",
        "description": "Enhancement implementation Pension",
        "domain":      "HCM / Payroll / Pension",
        "fiori_impact": True,
        "notes":       "Pension infotype logic; may affect Fiori personal data/payroll apps"
    },
    {
        "name":        "ZHR_PERS_DATA",
        "description": "Composite Enhancement impl personal data",
        "domain":      "HCM / Personal Data",
        "fiori_impact": True,
        "notes":       "HCMFAB_B_MYPERSONALDATA BAdI area; impacts My Personal Data Fiori app"
    },
    {
        "name":        "ZHR_SPAU_PA",
        "description": "Personal Administration",
        "domain":      "HCM / PA (SPAU)",
        "fiori_impact": False,
        "notes":       "SPAU adjustment for PA; standard infotype screen adaptation"
    },
    {
        "name":        "ZHR_SPAU_PY_CPSIT_PGM_001",
        "description": "Composite Enh. Implementation - Upgrade - SPAU",
        "domain":      "HCM / Payroll (SPAU)",
        "fiori_impact": False,
        "notes":       "SPAU payroll upgrade adjustment; CPSIT = Country-Specific Payroll Italy?"
    },
    # ── Y* enhancements (second SE20 screenshot) ──────────────────────────
    {
        "name":        "Y_ENH_PRAA",
        "description": "PRAA extensions",
        "domain":      "HCM / Payroll (PRAA)",
        "fiori_impact": False,
        "notes":       "PRAA = Payment Run program; payroll payment posting enhancements"
    },
    {
        "name":        "YCEI_FI_SUPPLIERS_PAYMENT",
        "description": "Suppliers Payments",
        "domain":      "FI / Accounts Payable",
        "fiori_impact": False,
        "notes":       "Custom FI supplier payment process; F110 / F-53 area; CEI = vendor"
    },
    {
        "name":        "YCL_HRPA_UI_CONVERT_0002_UN",
        "description": "Composite",
        "domain":      "HCM / PA / UI Conversion",
        "fiori_impact": True,
        "notes":       "HRPA UI conversion infotype 0002 (Personal Data) — likely Fiori My Data"
    },
    {
        "name":        "YCL_HRPA_UI_CONVERT_0006_UN",
        "description": "Composite Enhancement impl.",
        "domain":      "HCM / PA / UI Conversion",
        "fiori_impact": True,
        "notes":       "HRPA UI conversion infotype 0006 (Address) — Fiori Address Management"
    },
    {
        "name":        "YENH_FI_DMEE",
        "description": "Enhancement for DMEE",
        "domain":      "FI / Payment Medium (DMEE)",
        "fiori_impact": False,
        "notes":       "DMEE = Data Medium Exchange Engine; payment file format customization"
    },
    {
        "name":        "YENH_HRFPM_ARCH",
        "description": "PBC archiving enhancement",
        "domain":      "HCM / Archiving",
        "fiori_impact": False,
        "notes":       "HRFPM = HR Forms Process Management; archiving of HR forms/workflows"
    },
    {
        "name":        "YENH_INFOTYPE",
        "description": "Infotypes extensions",
        "domain":      "HCM / PA Infotypes",
        "fiori_impact": True,
        "notes":       "Generic infotype screen exit — may affect Fiori PA26/PA30 apps"
    },
    {
        "name":        "YENH_RFBIBL00",
        "description": "Enhancement implementation for RFBIBL00",
        "domain":      "FI / Batch Input",
        "fiori_impact": False,
        "notes":       "RFBIBL00 = FI batch input program; posting enhancements via BADI"
    },
    {
        "name":        "YFI_ENH",
        "description": "Enhancement for FI",
        "domain":      "FI / General",
        "fiori_impact": False,
        "notes":       "Generic FI enhancement implementation; likely FI substitutions / exits"
    },
    {
        "name":        "YFI_ENH_ARGA",
        "description": "Extensions for ARGA",
        "domain":      "FI / ARGA (Accounts Receivable / Government)",
        "fiori_impact": False,
        "notes":       "ARGA = Accounts Receivable Government Accounting; UN-specific AR logic"
    },
    {
        "name":        "YFM_ENH",
        "description": "FM extensions",
        "domain":      "PSM / Funds Management",
        "fiori_impact": False,
        "notes":       "Funds Management exits/BAdIs; budget availability, commitments"
    },
    {
        "name":        "YHR_ENH_HRCOREPLUS",
        "description": "Extension for HR Core plus",
        "domain":      "HCM / HR Core",
        "fiori_impact": True,
        "notes":       "HRCoreplus = SAP HR Core+ integration; affects Fiori HR Foundation apps"
    },
    {
        "name":        "YHR_ENH_HRFIORI",
        "description": "Fiori enhancement",
        "domain":      "HCM / Fiori (generic)",
        "fiori_impact": True,
        "notes":       "Direct Fiori HCM enhancement — high priority for Fiori service impact"
    },
    {
        "name":        "YHR_ENH_HUNCPFM0",
        "description": "Extensions for UNJSPF financial interface",
        "domain":      "HCM / Payroll / UNJSPF",
        "fiori_impact": False,
        "notes":       "UNJSPF = UN Joint Staff Pension Fund; pension financial interface logic"
    },
    {
        "name":        "YPS_ENH",
        "description": "PS extensions",
        "domain":      "PS / Project System",
        "fiori_impact": False,
        "notes":       "Project System enhancements; project/WBS element logic extensions"
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def safe_rfc_read_table(conn, table, where, fields=None, max_rows=1000):
    """Wrapper around RFC_READ_TABLE with error handling."""
    rfc_fields = [{"FIELDNAME": f} for f in (fields or [])]
    rfc_options = [{"TEXT": line} for line in where] if where else []
    try:
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table,
            DELIMITER="|",
            ROWCOUNT=max_rows,
            OPTIONS=rfc_options,
            FIELDS=rfc_fields,
        )
        headers = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            values = row["WA"].split("|")
            rows.append(dict(zip(headers, [v.strip() for v in values])))
        return rows
    except Exception as e:
        print(f"    [RFC_READ_TABLE error on {table}]: {e}")
        return []


def read_report_source(conn, prog_name):
    """Read ABAP source using SIW_RFC_READ_REPORT."""
    try:
        result = conn.call("SIW_RFC_READ_REPORT", I_NAME=prog_name)
        return result.get("E_TAB_CODE", [])
    except Exception as e:
        print(f"    [SIW_RFC_READ_REPORT error on {prog_name}]: {e}")
        return []


def save_source(path, filename, lines):
    """Save a list of source lines to a file."""
    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"    -> Saved {filename} ({len(lines)} lines)")
    return full_path


def get_enho_include_name(enh_name):
    """
    For classic ENHO source code the include is usually:
      ZENH_<NAME>  (for function module / program enhancements)
    We will probe TADIR for ENHO object and cross to REPOSRC.
    """
    return enh_name  # fallback: try the name itself


# ──────────────────────────────────────────────────────────────────────────────
# CORE EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

def extract_one(conn, enh_meta, out_root):
    name = enh_meta["name"]
    print(f"\n{'='*70}")
    print(f" EXTRACTING: {name}")
    print(f" Domain    : {enh_meta['domain']}")
    print(f" Fiori     : {'YES [!]' if enh_meta['fiori_impact'] else 'No'}")
    print(f"{'='*70}")

    enh_dir = os.path.join(out_root, name)
    os.makedirs(enh_dir, exist_ok=True)
    summary = {
        "name": name,
        "description": enh_meta["description"],
        "domain": enh_meta["domain"],
        "fiori_impact": enh_meta["fiori_impact"],
        "notes": enh_meta["notes"],
        "extracted_objects": []
    }

    # ── 1. TADIR lookup ──────────────────────────────────────────────────────
    print("  [1] TADIR lookup...")
    tadir_rows = safe_rfc_read_table(
        conn, "TADIR",
        [f"OBJ_NAME = '{name}'", " AND OBJECT = 'ENHO'"],
        fields=["OBJECT", "OBJ_NAME", "DEVCLASS", "SRCSYSTEM", "AUTHOR", "CREATED_ON"]
    )
    if tadir_rows:
        print(f"    Found in TADIR: {tadir_rows[0]}")
        td = tadir_rows[0]
        summary["package"] = td.get("DEVCLASS", "?")
        summary["created_on"] = td.get("CREATED_ON", "?")
        summary["author"] = td.get("AUTHOR", "?")
    else:
        # try broader — object type may differ
        tadir_rows2 = safe_rfc_read_table(
            conn, "TADIR",
            [f"OBJ_NAME LIKE '{name}%'"],
            fields=["OBJECT", "OBJ_NAME", "DEVCLASS"]
        )
        if tadir_rows2:
            print(f"    TADIR (broad): {tadir_rows2}")

    # ── 2. TADIR for ENHO object type ────────────────────────────────────────
    print("  [2] TADIR ENHO type check...")
    enho_rows = safe_rfc_read_table(
        conn, "TADIR",
        [f"OBJ_NAME = '{name}'", " AND OBJECT = 'ENHC'"],
        fields=["OBJECT", "OBJ_NAME", "DEVCLASS"]
    )
    if enho_rows:
        print(f"    TADIR ENHC: {enho_rows[0]}")
        summary["enhtype"] = "ENHC"
    else:
        print("    (not found as ENHC in TADIR)")

    # ── 3. ENHLOG — find implementation link ─────────────────────────────────
    print("  [3] ENHLOG (implementation linkage)...")
    enhlog_rows = safe_rfc_read_table(
        conn, "ENHLOG",
        [f"ENHNAME = '{name}'"],
    )
    impl_classes = []
    for row in enhlog_rows:
        print(f"    Impl: {row}")
        cls = row.get("CLASSNAME") or row.get("IMPLNAME", "")
        if cls:
            impl_classes.append(cls)

    # ── 4. Try reading ENHO source directly ──────────────────────────────────
    print("  [4] ENHO direct source read...")

    # Try reading the ENHO source directly as a program
    src_lines = read_report_source(conn, name)
    if src_lines:
        save_source(enh_dir, f"{name}_ENHO.abap", src_lines)
        summary["extracted_objects"].append(f"{name}_ENHO.abap")
    else:
        print("    (direct SIW_RFC_READ_REPORT returned nothing — trying includes)")

    # ── 5. TRDIR scan for includes of this enhancement ───────────────────────
    print("  [5] TRDIR scan for related includes...")
    trdir_rows = safe_rfc_read_table(
        conn, "TRDIR",
        [f"NAME LIKE '{name}%'"],
        fields=["NAME", "SUBC"]
    )
    found_includes = [r["NAME"] for r in trdir_rows if r.get("NAME")]
    print(f"    Found {len(found_includes)} entries: {found_includes}")

    for inc in found_includes:
        if inc == name:
            continue  # already tried above
        inc_lines = read_report_source(conn, inc)
        if inc_lines:
            save_source(enh_dir, f"{inc}.abap", inc_lines)
            summary["extracted_objects"].append(f"{inc}.abap")

    # ── 6. Class method CM-includes ──────────────────────────────────────────
    all_classes = set(impl_classes)
    # Also look for class-based implementations named like the enhancement
    for prefix in [name, name.replace("_", "")]:
        cls_trdir = safe_rfc_read_table(
            conn, "TRDIR",
            [f"NAME LIKE '{prefix}%CM%'"],
            fields=["NAME"]
        )
        for r in cls_trdir:
            n = r.get("NAME", "")
            # Derive class name from CM include (e.g. ZCL_FOO=========CM001)
            if "CM" in n:
                cls_name = n.split("=")[0] if "=" in n else n[:30]
                all_classes.add(cls_name)

    for cls in all_classes:
        print(f"  [6] Extracting class {cls} (CM includes)...")
        cls_dir = os.path.join(enh_dir, cls)
        cm_rows = safe_rfc_read_table(
            conn, "TRDIR",
            [f"NAME LIKE '{cls}%CM%'"],
            fields=["NAME"]
        )
        for r in cm_rows:
            inc = r.get("NAME", "")
            cm_lines = read_report_source(conn, inc)
            if cm_lines:
                save_source(cls_dir, f"{inc}.abap", cm_lines)
                summary["extracted_objects"].append(f"{cls}/{inc}.abap")

    # ── 7. Save summary JSON ─────────────────────────────────────────────────
    summary_path = os.path.join(enh_dir, "_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  [DONE] {len(summary['extracted_objects'])} objects saved -> {enh_dir}")
    return summary


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    filter_name = sys.argv[1].upper() if len(sys.argv) > 1 else None
    targets = ENHANCEMENTS if not filter_name else [
        e for e in ENHANCEMENTS if e["name"] == filter_name
    ]

    if not targets:
        print(f"Enhancement '{filter_name}' not found in target list.")
        sys.exit(1)

    print(f"\n{'#'*70}")
    print(f" SE20 Composite Enhancement Extractor")
    print(f" Targets: {len(targets)}")
    print(f"{'#'*70}")

    conn = get_sap_connection()
    print("Connected to SAP system.\n")

    os.makedirs(OUTPUT_BASE, exist_ok=True)
    all_summaries = []

    for enh in targets:
        s = extract_one(conn, enh, OUTPUT_BASE)
        all_summaries.append(s)

    conn.close()

    # ── Final Domain/Fiori Mapping Report ────────────────────────────────────
    print(f"\n\n{'#'*70}")
    print(" DOMAIN & FIORI IMPACT REPORT")
    print(f"{'#'*70}")
    print(f"{'Enhancement':<35} {'Domain':<30} {'Fiori?'}")
    print("-" * 80)

    fiori_hits = []
    for s in all_summaries:
        fiori_flag = "[!] YES" if s["fiori_impact"] else "  No "
        print(f"{s['name']:<35} {s['domain']:<30} {fiori_flag}")
        if s["fiori_impact"]:
            fiori_hits.append(s)

    print(f"\n>> {len(fiori_hits)} enhancements likely affect Fiori services/apps:")
    for h in fiori_hits:
        print(f"   * {h['name']} -- {h['notes']}")

    # Save master report
    report_path = os.path.join(OUTPUT_BASE, "_COMPOSITE_ENH_REPORT.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)
    print(f"\nMaster report: {report_path}")


if __name__ == "__main__":
    main()
