---
name: sap_custom_extensions
description: THE single entry point for UNESCO custom extensions of every kind — user-exits (CMOD/SMOD, ZX* includes), BAdIs and the Enhancement Framework (SE18/SE19/SE20, ENHO/ENHC), field-exits, and MODIFICATIONS to SAP standard code (SPAU/SE95/SMODILOG). Use whenever the question is "what custom logic runs at this point", "is this behavior standard or ours", "what extensions exist in module X", "was this standard object modified", or before creating ANY new exit/BAdI/enhancement. Consolidates the completed analysis (registry + 12 technical autopsies + Gold DB inventories) so no session re-derives it, and names what is still open.
domains:
  functional: [FI, PSM, HCM, MM, TV]
  module: [*]
  process: [enhancement, modification, exit]
---

# SAP Custom Extensions — UNESCO (unified skill, s111)

> **The heavy analysis is DONE** — a master registry, 12 technical autopsies, and three Gold DB
> inventories. This skill is the map, the discovery method, and the open frontier. Sibling skill:
> `sap_validation_substitution` (the GGB0/GGB1/YRGGBS00 perimeter — its own entry point).
>
> **Why this matters to process mining (JP, s111):** extensions are hidden actors IN THE MIDDLE
> of every process — the event log records outcomes, never the exit that derived, blocked, or
> rewrote a value mid-transaction. Without this inventory, process discovery attributes to users
> and standard SAP what custom code actually did.

## 1. The four extension classes and where each is discovered

| Class | Discovery TCODEs | Storage tables | Gold DB today |
|---|---|---|---|
| **User-exits (classic)** | `CMOD` (projects), `SMOD` (definitions) | `MODACT`, `MODSAP`, TADIR | ✅ `modact`/`modsap`/`modattr` — **21 projects → 27 SMOD enhancements** [claim 652] |
| **BAdIs (classic)** | `SE18`/`SE19` | `SXS_ATTR`/`SXC_*` (SXS_ATTR **blocked via RFC** — TABLE_WITHOUT_DATA) | via TADIR + ENHOBJ |
| **Enhancement Framework** | `SE20` (spots, implementations) | `ENHOBJ`, `ENHLOG`, TADIR (`ENHO`/`ENHC`) | ✅ `ENHOBJ` 78,807 rows — 25,887 enhancements, **234 Z*/Y* custom** |
| **Standard-code MODIFICATIONS** | `SPAU`/`SPDD`, `SE95` | `SMODILOG` | ✅ `smodilog` 9,852 rows (4,221 objects) + `spau_2024_objects` |

Extraction method (proven, incl. the composite-enhancement include trick): skill
`sap_enhancement_extraction`. Extracted source lives in `extracted_code/ENHO/` and
`extracted_code/UNESCO_CUSTOM_LOGIC/`.

## 2. The master registry — what each extension DOES

**`knowledge/sap_custom_enhancement_registry.md`** (11 sections) is the source of truth, with
living companion `companions/fi_substitutions_custom_code_companion_v1.html` (8 tabs). Highlights:

- **FM/posting**: `ZXFMDTU02` (FMDERIVE: GL→Fund/FC force-mapping, YFMXCHK/YFMXCHKP gates),
  `ZXFMYU22` (10-digit glue: `POSID(10)=GEBER` for funds 101–112), `ZXFMCU09/10/12/17`
  (FR header/tolerance caps), project `ZFMACCHK`.
- **PS/MM**: `YJWB001` (WBS user-field validation vs `YUSR00–04`), `YELAM001/003` (allotment),
  `ZXM06U22` (PO release bypass via MATKL manipulation + `Z_RFC_EXT_DEST_PO_RELEASE`).
- **Travel**: `ZXTRVU03` (overlap/dependant), `ZXTRVU05` (CC+WBS dual-assignment block).
- **BW**: `ZXRSAU01/02` (analytical posting dates, donors, sectors, support-cost %).
- **Fund master**: `ZXFMFUNDU01–04` + `YCL_FM_FUND_IBF_BL` (IBF metadata, `YTFM_FUND_C5`).
- **FI perimeter**: `YRGGBS00` 69 FORMs + `YFI_BASU_MOD`/`YTFI_BA_SUBST` (range-based business-area
  substitution maintained OUTSIDE transports) → detail in `sap_validation_substitution`.

The 12 technical autopsies live in `knowledge/domains/PSM/EXTENSIONS/` (posting derivation, FM
validation, AVC derivation, BASU, IBF, FM cockpit, BW logics, travel, budget-rate, validation
matrix…). Analysis status per object: `knowledge/code_analysis_control_matrix.md`.

## 3. Standard-code modifications — measured, and the rule

- `smodilog` (Gold DB): the SPAU/SPDD adjustment log. **HR/Payroll is the #1 modified domain**
  (see `knowledge/gold_db_table_catalog.md` §SMODILOG, upgrade-measurement companion).
- **Trap (claim 211)**: `CLS4SIC_*` classes in the SPAU set are SAP-delivered S/4 readiness
  checks, NOT UNESCO modifications — the SP stack ships them. Always split UNESCO-mods vs
  SAP-delivered before counting.
- **Rule going forward** (`feedback_never_modify_standard_objects`, CRITICAL): never modify
  SAP-delivered objects; extend via append/BAdI/ENHO/exits. Historic mods are inventory to
  understand, not precedent to follow.

## 4. Method — "what custom logic runs at this point?"

1. **Registry first** (§2): if the include/exit is named there, the analysis exists — read it,
   don't re-trace.
2. **Gold DB inventories**: `ENHOBJ` for enhancement→object mapping (`WHERE ENHNAME LIKE 'Y%' OR
   'Z%'`), `smodilog` for "was this standard object touched", `tadir_obj`/`tadir_prog` for
   ownership.
3. **Source**: `extracted_code/UNESCO_CUSTOM_LOGIC/<domain>/` (RPY extracts, D01) and
   `extracted_code/ENHO/`. P01 corpus: `extracted_sap_p01/`.
4. **New discovery** → register it in `sap_custom_enhancement_registry.md` + the filter registry
   if it carries filter logic, and land a claim (this is how YFMXCHK got landed — s111).
5. **Creating a new extension** → `sap_abap_style` skill first (mandatory), D01 only, released
   transport as the unit of change (BROADCAST-007).

## 5. Open frontier (measured s111 — "por ahí hay que seguir")

- ~~CMOD project census missing~~ **CLOSED s111**: `modact`/`modsap`/`modattr` extracted
  (refresher `extract_cmod_inventory.py`). **The census: 21 projects → 27 SMOD enhancements**,
  authors 2001–2015, 20/22 active; latest activation N_MENARD on YFUNDMD 2023-09-21. Financial
  hot points: `ZFMACCHK`→`SAPLFMDT` (=FMDERIVE, the YFMXCHK gates), `YTFBE001`→`FEB00001` (bank
  statement exit), `STEPS`→`ACBAPI01` (accounting BAPI). [claim 652]
  **Caveat**: `MODSAP` is SAP's full definition catalog (10,273 rows) — census on `MODACT` only.
- **19 of 21 CMOD projects unregistered** (only ZFMACCHK and STEPS were in the registry) and
  **209 of 234 Z*/Y* ENHOBJ enhancements unregistered**: the census miner
  (`custom_extension_census_check.py`) measures both and publishes to the bus. Triage priority:
  the ones hanging off posting/payment points.
- `SXS_ATTR` unreadable via RFC → classic-BAdI inventory needs the TADIR route.

## 6. Watchers (miners on the bus — run in `opportunity_watch --correr`)

- `Zagentexecution/quality_checks/custom_extension_census_check.py` — population vs registry
  coverage, unregistered custom enhancements, missing CMOD extraction.
- `Zagentexecution/quality_checks/validation_substitution_drift_check.py` — the posting-perimeter
  control tables vs their documented map (claims 648–650): a new YXUSER row or an activated
  YFMXCHKP variant is a RIESGO the moment it appears.
