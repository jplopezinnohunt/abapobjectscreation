"""
domain_reorg.py
================
Reorganizes the knowledge/domains/ and extracted_code/ENHO/ folder trees
based on the 7 identified domains from the 27 composite enhancement extraction.

Creates:
  knowledge/domains/FI/             -- FI sub-domain docs
  knowledge/domains/PS/             -- PS analysis doc
  knowledge/domains/RE-FX/          -- RE-FX doc
  knowledge/domains/Procurement/    -- Procurement doc
  knowledge/domains/Output/         -- Output / Documents doc
  knowledge/domains/HCM/Payroll/    -- HCM Payroll sub-doc
  knowledge/domains/HCM/Benefits/   -- HCM Benefits sub-doc
  knowledge/domains/HCM/Infotypes/  -- HCM Infotypes sub-doc

  extracted_code/ENHO/_by_domain/<DOMAIN>/<ENHANCEMENT_NAME>/  (symlink-style copy index)

Also updates knowledge/knowledge_base_index.md.

Run from:  c:/Users/jp_lopez/projects/abapobjectscreation
"""

import os
import shutil
import json

BASE        = r"c:\Users\jp_lopez\projects\abapobjectscreation"
DOMAINS_DIR = os.path.join(BASE, "knowledge", "domains")
ENHO_DIR    = os.path.join(BASE, "Zagentexecution", "mcp-backend-server-python",
                            "extracted_code", "ENHO")
ENHO_BY_DOM = os.path.join(ENHO_DIR, "_by_domain")

# ─── Enhancement master list ─────────────────────────────────────────────────
# (name, domain_folder, sub_folder, fiori)
ENHANCEMENTS = [
    # HCM
    ("ZCL_HCMFAB_ASR_PROCESS",        "HCM", "ASR",            True),
    ("ZCOMP_ENH_SF",                   "HCM", "SFConnector",    True),
    ("ZENH_PAWF_INT_AGREE",            "HCM", "Workflow",       True),
    ("ZHR_FIORI_0021",                 "HCM", "Family",         True),
    ("ZHR_PENSION",                    "HCM", "Payroll",        True),
    ("ZHR_PERS_DATA",                  "HCM", "PersonalData",   True),
    ("ZHR_SPAU_PA",                    "HCM", "PA_SPAU",        False),
    ("ZHR_SPAU_PY_CPSIT_PGM_001",      "HCM", "Payroll",        False),
    ("Y_ENH_PRAA",                     "HCM", "Payroll",        False),
    ("YCL_HRPA_UI_CONVERT_0002_UN",    "HCM", "PersonalData",   True),
    ("YCL_HRPA_UI_CONVERT_0006_UN",    "HCM", "Address",        True),
    ("YENH_HRFPM_ARCH",                "HCM", "Archiving",      False),
    ("YENH_INFOTYPE",                  "HCM", "Infotypes",      True),
    ("YHR_ENH_HRCOREPLUS",             "HCM", "HRCore",         True),
    ("YHR_ENH_HRFIORI",                "HCM", "Benefits",       True),
    ("YHR_ENH_HUNCPFM0",               "HCM", "Payroll",        False),
    # FI
    ("YCEI_FI_SUPPLIERS_PAYMENT",      "FI",  "AP",             False),
    ("YENH_FI_DMEE",                   "FI",  "DMEE",           False),
    ("YENH_RFBIBL00",                  "FI",  "BatchInput",     False),
    ("YFI_ENH",                        "FI",  "General",        False),
    ("YFI_ENH_ARGA",                   "FI",  "ARGA",           False),
    ("ZFIX_EXCHANGERATE",              "FI",  "Treasury",       False),
    # PSM
    ("YFM_ENH",                        "PSM", "FundsManagement",False),
    # PS
    ("YPS_ENH",                        "PS",  "ProjectSystem",  False),
    # RE-FX
    ("ZENH_REFX_CONTRACT_UNESCO",      "RE-FX","ContractMgmt",  False),
    # Procurement
    ("Z_ICTP_PO_HOSTGUEST",            "Procurement","PO",      False),
    # Output
    ("ZENH_DOCX",                      "Output","Documents",    False),
]

# ─── Knowledge domain templates ───────────────────────────────────────────────

FI_DOC = """\
# UNESCO SAP Knowledge: Finance (FI) Domain — Enhancement Registry

> **Living Document** — populated from SE20 Composite Enhancement extraction 2026-03-12.

## Domain Overview
FI enhancements cover Accounts Payable, Treasury, DMEE payment media, batch input,
general ledger, and government-specific AR (ARGA).

## Identified Enhancements

| Enhancement | Sub-Domain | Fiori? | Key Finding |
|---|---|---|---|
| `YCEI_FI_SUPPLIERS_PAYMENT` | Accounts Payable | No | Supplier payment customization |
| `YENH_FI_DMEE` | Payment Medium (DMEE) | No | UN payment medium format override |
| `YENH_RFBIBL00` | Batch Input | No | Custom BDC logic for FI posting |
| `YFI_ENH` | General Ledger | No | General FI posting enhancements |
| `YFI_ENH_ARGA` | Gov. Accounts Receivable | No | UN-specific AR/government billing |
| `ZFIX_EXCHANGERATE` | Treasury | No | Exchange rate handling for UNESCO |

## Extracted Code Location
`extracted_code/ENHO/_by_domain/FI/<ENHANCEMENT_NAME>/`

## Cross-References
- [Enhancement Registry](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/sap_custom_enhancement_registry.md) — Sections 8, 9
- [Finance Validations Autopsy](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md)
"""

PS_DOC = """\
# UNESCO SAP Knowledge: Project System (PS) Domain — Enhancement Registry

> **Living Document** — populated from SE20 Composite Enhancement extraction 2026-03-12.

## Domain Overview
PS enhancements cover WBS element management, project validation, and PS-FM integration.

## Identified Enhancements

| Enhancement | Sub-Domain | Fiori? | Key Finding |
|---|---|---|---|
| `YPS_ENH` | Project System | No | WBS / Project-level PS enhancements |

## Extracted Code Location
`extracted_code/ENHO/_by_domain/PS/<ENHANCEMENT_NAME>/`

## Cross-References
- [Entity Brain Map — PS](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/entity_brain_map.md)
- [PSM-FM Hard Link](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md)
"""

REFX_DOC = """\
# UNESCO SAP Knowledge: Real Estate (RE-FX) Domain — Enhancement Registry

> **Living Document** — populated from SE20 Composite Enhancement extraction 2026-03-12.

## Domain Overview
RE-FX enhancements support UNESCO's contract and lease management for field offices.

## Identified Enhancements

| Enhancement | Sub-Domain | Package | Author | Created | Fiori? |
|---|---|---|---|---|---|
| `ZENH_REFX_CONTRACT_UNESCO` | Contract Management | `YA_FEX` | `JP_LOPEZ` | 2024-09-20 | No |

## Key Finding — ZENH_REFX_CONTRACT_UNESCO
- Author `JP_LOPEZ`, created Sep 2024 — recent custom enhancement
- Package `YA_FEX` (UNESCO Real Estate)
- Direct ENHO (not container-only) — has source includes to extract

## Extracted Code Location
`extracted_code/ENHO/_by_domain/RE-FX/ZENH_REFX_CONTRACT_UNESCO/`
"""

PROC_DOC = """\
# UNESCO SAP Knowledge: Procurement Domain — Enhancement Registry

> **Living Document** — populated from SE20 Composite Enhancement extraction 2026-03-12.

## Domain Overview
Procurement enhancements cover Purchase Order logic, host/guest scenarios at ICTP.

## Identified Enhancements

| Enhancement | Sub-Domain | Package | Fiori? | Key Finding |
|---|---|---|---|---|
| `Z_ICTP_PO_HOSTGUEST` | PO / Goods Receipt | `ZICTP` | No | Host-guest scenario PO logic for ICTP institute |

## Cross-References
- Enhancement Registry: PO Release Strategy (Section 2.3)
- ICTP is a UNESCO institute with custom company code rules
"""

OUTPUT_DOC = """\
# UNESCO SAP Knowledge: Output & Document Management Domain — Enhancement Registry

> **Living Document** — populated from SE20 Composite Enhancement extraction 2026-03-12.

## Domain Overview
Output enhancements cover DOCX/PDF generation and document output control for UNESCO.

## Identified Enhancements

| Enhancement | Package | Fiori? | Key Finding |
|---|---|---|---|
| `ZENH_DOCX` | `YU` | No | Custom DOCX document output enhancement |

## Notes
- Package `YU` is a generic UNESCO utility package
- No direct source includes found — logic likely in linked output classes

## Cross-References
- `ZCL_HR_DOCUMENT_MANAGER` (extracted class — `extracted_code/ZCL_HR_DOCUMENT_MANAGER/`)
"""

HCM_PAYROLL_DOC = """\
# UNESCO HCM: Payroll Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers UNJSPF pension, PRAA, SPAU payroll enhancements.

## Identified Enhancements

| Enhancement | Area | Fiori? | Key Finding |
|---|---|---|---|
| `ZHR_PENSION` | Pension / UNJSPF | YES | Pension infotype logic; may affect Fiori personal data/payroll apps |
| `ZHR_SPAU_PY_CPSIT_PGM_001` | Payroll SPAU | No | Screen exit for PITGPCODE payroll variant |
| `Y_ENH_PRAA` | Payroll PRAA | No | Payroll remuneration accounting enhancements |
| `YHR_ENH_HUNCPFM0` | Payroll / UNJSPF | No | UNJSPF participation date logic (3 E-includes extracted) |

## Extracted Code with Source
### YHR_ENH_HUNCPFM0 (3 includes extracted)
- `YHR_ENH_HUNCPFM0_CHECK========E.abap` (12 lines)
- `YHR_ENH_HUNCPFM0_PART_DATE====E.abap` (14 lines)
- `YHR_ENH_HUNCPFM0_START========E.abap` (8 lines)

Location: `extracted_code/ENHO/_by_domain/HCM/Payroll/`
"""

HCM_BENEFITS_DOC = """\
# UNESCO HCM: Benefits & Fiori Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers benefit enrollment, family benefits, Fiori generics.

## Identified Enhancements

| Enhancement | Package | Area | Fiori? | Key Finding |
|---|---|---|---|---|
| `YHR_ENH_HRFIORI` | `ZHRBENEFITS_FIORI` | Generic HCM Fiori | YES | Direct Fiori HCM enhancement in Benefits Fiori package |
| `YHR_ENH_HRCOREPLUS` | `ZHR_DEV` | HR Core+ | YES | HR Core+ Fiori Foundation integration |
| `ZCOMP_ENH_SF` | `ZHR_DEV` | SuccessFactors | YES | SF integration layer; may affect OData services for iFlow/BTP |

## Extracted Code
- All three are container-only ENHC wrappers
- Logic lives in linked BAdI/integration classes
- `YHR_ENH_HRFIORI` — package `ZHRBENEFITS_FIORI` is the key scope for benefits Fiori extraction

## Cross-References
- [Fiori App Analysis: Benefits Enrollment](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/HCM/Fiori%20Apps/hcm_family_management_analysis.md)
- Benefit enrollment OData: `ZHCMFAB_BEN_ENROLLMENT_SRV`
"""

HCM_INFOTYPES_DOC = """\
# UNESCO HCM: Infotypes & PA Screen Exits Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers IT0021 field control, PA screen exits, SPAU mods.

## Identified Enhancements

| Enhancement | Fiori? | Extracted Source | Key Finding |
|---|---|---|---|
| `ZHR_FIORI_0021` | YES | 44 lines (E-include) | Hides GOVAST/SPEMP/ERBNR on IT0021; makes WAERS read-only for Child/Spouse |
| `ZHR_SPAU_PA` | No | 2 ENHO children | Screen exits MP096200 + MP096500 for PA infotypes |
| `YENH_INFOTYPE` | YES | Container-only | Generic infotype screen exit — may affect PA26/PA30 Fiori |
| `YCL_HRPA_UI_CONVERT_0002_UN` | YES | Container-only | IT0002 UI field conversion for Fiori Personal Data |
| `YCL_HRPA_UI_CONVERT_0006_UN` | YES | Container-only | IT0006 UI field conversion for Fiori Address Management |

## Key Code: ZHR_FIORI_0021 Field Rules
| Field | Rule |
|---|---|
| `GOVAST` | Always INVISIBLE |
| `SPEMP` | Always INVISIBLE |
| `ERBNR` | Always INVISIBLE |
| `WAERS` | READ_ONLY when FAMSA='14' or '2' |

## Cross-References
- Family Management Analysis: Section 8
- Personal Data Analysis: Section 12
- Address Management Analysis: Section 6
"""

# ─── helper ───────────────────────────────────────────────────────────────────

def mkdir(path):
    os.makedirs(path, exist_ok=True)

def write(path, content, overwrite=False):
    if os.path.exists(path) and not overwrite:
        print(f"  [skip existing] {os.path.basename(path)}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [wrote] {os.path.relpath(path, BASE)}")

def copy_enho(name, domain, subdomain):
    """Copy ENHO folder into _by_domain/<DOMAIN>/<SUBDOMAIN>/<NAME>"""
    src = os.path.join(ENHO_DIR, name)
    dst = os.path.join(ENHO_BY_DOM, domain, subdomain, name)
    if not os.path.exists(src):
        print(f"  [missing ENHO] {name}")
        return
    if os.path.exists(dst):
        print(f"  [exists] {domain}/{subdomain}/{name}")
        return
    shutil.copytree(src, dst)
    print(f"  [copied] {name} -> _by_domain/{domain}/{subdomain}/")


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Phase 1: Create knowledge/domains/ structure ===")

    # FI domain
    fi_dir = os.path.join(DOMAINS_DIR, "FI")
    mkdir(fi_dir)
    write(os.path.join(fi_dir, "fi_enhancements_analysis.md"), FI_DOC)

    # PS domain
    ps_dir = os.path.join(DOMAINS_DIR, "PS")
    mkdir(ps_dir)
    write(os.path.join(ps_dir, "ps_enhancements_analysis.md"), PS_DOC)

    # RE-FX domain
    refx_dir = os.path.join(DOMAINS_DIR, "RE-FX")
    mkdir(refx_dir)
    write(os.path.join(refx_dir, "refx_enhancements_analysis.md"), REFX_DOC)

    # Procurement domain
    proc_dir = os.path.join(DOMAINS_DIR, "Procurement")
    mkdir(proc_dir)
    write(os.path.join(proc_dir, "procurement_enhancements_analysis.md"), PROC_DOC)

    # Output domain
    out_dir = os.path.join(DOMAINS_DIR, "Output")
    mkdir(out_dir)
    write(os.path.join(out_dir, "output_enhancements_analysis.md"), OUTPUT_DOC)

    # HCM sub-domains
    hcm_dir = os.path.join(DOMAINS_DIR, "HCM")
    mkdir(os.path.join(hcm_dir, "Payroll"))
    write(os.path.join(hcm_dir, "Payroll", "hcm_payroll_analysis.md"), HCM_PAYROLL_DOC)
    mkdir(os.path.join(hcm_dir, "Benefits"))
    write(os.path.join(hcm_dir, "Benefits", "hcm_benefits_analysis.md"), HCM_BENEFITS_DOC)
    mkdir(os.path.join(hcm_dir, "Infotypes"))
    write(os.path.join(hcm_dir, "Infotypes", "hcm_infotypes_analysis.md"), HCM_INFOTYPES_DOC)

    print("\n=== Phase 2: Organize extracted_code/ENHO/ by domain ===")
    mkdir(ENHO_BY_DOM)
    for name, domain, subdomain, fiori in ENHANCEMENTS:
        copy_enho(name, domain, subdomain)

    print("\n=== Phase 3: Generate domain index (_by_domain/DOMAIN_INDEX.md) ===")
    # Build a quick index per domain
    from collections import defaultdict
    dom_map = defaultdict(list)
    for name, domain, subdomain, fiori in ENHANCEMENTS:
        dom_map[domain].append((subdomain, name, fiori))

    lines = ["# Enhancement Code — Domain Index\n",
             "Auto-generated 2026-03-12. Maps all 27 enhancements to domain subfolders.\n",
             f"Base path: `extracted_code/ENHO/_by_domain/`\n\n"]
    for domain in sorted(dom_map.keys()):
        lines.append(f"## {domain}\n")
        lines.append("| Sub-Domain | Enhancement | Fiori? | Code |\n")
        lines.append("|---|---|---|---|\n")
        for subdomain, name, fiori in sorted(dom_map[domain]):
            fiori_str = "YES [!]" if fiori else "No"
            src = os.path.join(ENHO_DIR, name)
            has_code = "YES" if os.path.exists(src) and len(os.listdir(src)) > 1 else "metadata only"
            lines.append(f"| {subdomain} | `{name}` | {fiori_str} | {has_code} |\n")
        lines.append("\n")
    
    idx_path = os.path.join(ENHO_BY_DOM, "DOMAIN_INDEX.md")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  [wrote] _by_domain/DOMAIN_INDEX.md")

    print("\n=== Done ===")
    print(f"New knowledge folders: FI, PS, RE-FX, Procurement, Output")
    print(f"New HCM sub-folders:   Payroll, Benefits, Infotypes")
    print(f"ENHO organized under:  extracted_code/ENHO/_by_domain/")


if __name__ == "__main__":
    main()
