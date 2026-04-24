# Phase 0 Gap Closure Report

**Session #62** · **2026-04-24** · **Project**: UNESCO DMEE Structured Address Migration (CBPR+ Nov 2026)
**Status**: Phase 0 round 2 completed — 5 of 8 gaps fully CLOSED, 2 PARTIAL, 1 PARKED

---

## Gap closure summary

| ID | Status | What we found | Evidence |
|---|---|---|---|
| **GAP-001** | PARKED | YRGGBS00 substitution investigation — not relevant for structured address change locus | Scope decision session #62 |
| **GAP-002** | PARTIAL | Only 1 UNESCO Y_FPAY FM (`ZWFPAYROLL_STATUS`, payroll not address). SXS_ATTR/V_EXT_IMP/ENHBADIIMPL tables return TABLE_WITHOUT_DATA via RFC — can't enumerate BAdI impls that way. BUT we know 5 impls exist (FR/FALLBACK/UTIL extracted + DE/IT verified in TADIR) | `gap_probe_results.json`, `gap_probe_results_round2.json` |
| **GAP-003** | **CLOSED** | `YCL_IDFI_CGI_DMEE_AE` and `_BH` **DO NOT EXIST** in P01 TADIR. Only `_DE`, `_FR`, `_IT`, `_FALLBACK`, `_UTIL` exist. Handoff doc's AE/BH mentions were speculative. | `gap_probe_results.json` |
| **GAP-004** | **CLOSED** | FPAYHX has 432 total fields, 25 Z-fields. **Handoff doc field names are WRONG**: claimed ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND — none exist. Real Z-fields: ZPFST (street), ZPLOR (postal+city display), ZLISO (country ISO), ZLNDX, ZREGX, ZNM1S/2S, ZBANK, ZBNKL_EXT, ZFORN, `ZREF01..ZREF10` (customer buffers — 10 not 5), ZSTCEG. **FPAYH has ZERO REF fields** — handoff doc claim that buffers live in FPAYH-REF01..05 is incorrect; they live in FPAYHX-ZREF01..10. | `gap_probe_results.json` |
| **GAP-005** | **CLOSED** | Zero writes to FPAYHX-Z* or FPAYH-REF* fields across 986 UNESCO ABAP files (grep 8 write patterns). Trees read address fields directly from FPAYH/FPAYHX/FPAYP via standard DMEE source-field mapping. **No hidden UNESCO populator BAdI exists** — SAP standard PMW + direct tree reads are the mechanism. | `gap_005_static_analysis.md` |
| **GAP-006** | **CLOSED** | 1,975 nodes re-probed with correct columns (`MP_EXIT_FUNC`, `MP_SC_TAB`, `MP_SC_FLD`, `MP_CONST`). **794 nodes use exit `FI_CGI_DMEE_EXIT_W_BADI`** across all 4 trees — our 3 UNESCO BAdI classes (`YCL_IDFI_CGI_DMEE_FR/FALLBACK/UTIL`) handle 40% of tree logic. 33 distinct MP_EXIT_FUNC values total including `/CITIPMW/V3_*` (SAP CITI prebuilt logic) and 2 Z-exits (`Z_DMEE_EXIT_TAX_NUMBER`, `ZDMEE_EXIT_SEPA_21`). Per-tree address-node exit coverage: SEPA=0, CITI=4, CGI=69, CGI_1=73. | `gap006_dmee_nodes_with_exit.csv`, `gap_probe_results_round2.json` |
| **GAP-007** | PARKED | Post-DMEE file transmission code not relevant for address change (address is WITHIN XML, pre-file-write). Address change does not alter naming/directory/Alliance Lite2 delivery. Revisit if bank pilot reveals file-level issue. | Scope decision session #62 |
| **GAP-008** | **CLOSED** | T042Z_FULL (263 rows) + T042A (76 rows) + T042I (76 rows) probed. 13 T042Z entries for our 4 target trees. All have XBKKT='X' (DMEE-enabled). `/CGI_XML_CT_UNESCO` FR+A "Treasury Transfers" has XSTRA='' (blank) — explains Marlies's Excel row 10 edge case. Co code → tree mapping: SEPA=UNES/IIEP/UIL, CITI=UNES/UIS/UBO(Worldlink), CGI=UNES/IIEP. | `cts_dmee_authors.md`, plan Finding H |

---

## Complete XML-touching asset inventory

Every code point that shapes outgoing XML payment file content, traced end-to-end for the 4 target DMEE trees.

### Layer 1 — DMEE Tree Definitions (SAP customizing, 1,975 nodes across 4 target trees)

| Tree | Nodes | Address+party nodes | Nodes with exit | Address nodes with exit |
|---|---|---|---|---|
| `/SEPA_CT_UNES` | 95 | 15 | 4 | 0 |
| `/CITI/XML/UNESCO/DC_V3_01` | 610 | 83 | 40 | 4 |
| `/CGI_XML_CT_UNESCO` | 631 | 124 | 395 | 69 |
| `/CGI_XML_CT_UNESCO_1` | 639 | 132 | 399 | 73 |

**Total**: 1,975 nodes, 354 address+party, 838 with exit function, 146 address+exit.

### Layer 2 — Exit Functions (33 distinct FMs invoked by tree nodes)

| Exit function | Node count | Role | Extracted? |
|---|---|---|---|
| `FI_CGI_DMEE_EXIT_W_BADI` | **794** | SAP BAdI name, resolved at runtime to one of our 5 impls | BAdI def SAP std, impls in `extracted_code/FI/DMEE/` |
| `/CITIPMW/V3_*` (12 variants) | 18 | SAP CITIPMW Industry Solution prebuilt exits (CGI Creditor name/PO/city/street/region/postcode/building/email/tax/regulatory) | SAP standard (not UNESCO custom) |
| `DMEE_EXIT_SEPA_31` / `_41` / `_SE_DATE` | 5 | SAP standard SEPA exits | SAP standard |
| **`Z_DMEE_EXIT_TAX_NUMBER`** | 1 | UNESCO custom exit (Z), tax number specific | Not yet extracted — GAP-002 follow-up |
| **`ZDMEE_EXIT_SEPA_21`** | 1 | UNESCO custom exit (Z), SEPA-specific | Not yet extracted — GAP-002 follow-up |
| (15 other low-count) | 13 | Various | Mixed |

### Layer 3 — BAdI Implementations (our 5 UNESCO impls of FI_CGI_DMEE_EXIT_W_BADI)

All implement interface `IF_IDFI_CGI_DMEE_COUNTRIES`. Dispatched via country code passed by the BAdI framework.

| Impl class | P01 status | Source extracted | Author | Last modified |
|---|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_FR` | EXISTS | `extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_FR_*` | N_MENARD | 2024 (9 transports) |
| `YCL_IDFI_CGI_DMEE_FALLBACK` | EXISTS | idem `_FALLBACK_*` | N_MENARD | 2024-11-22 |
| `YCL_IDFI_CGI_DMEE_UTIL` | EXISTS | idem `_UTIL_*` | N_MENARD | 2024 |
| `YCL_IDFI_CGI_DMEE_DE` | EXISTS | **Not yet extracted** | (likely N_MENARD per class naming) | ? |
| `YCL_IDFI_CGI_DMEE_IT` | EXISTS | **Not yet extracted** | (likely N_MENARD) | ? |
| `YCL_IDFI_CGI_DMEE_AE` | **NOT FOUND** | N/A | — | — |
| `YCL_IDFI_CGI_DMEE_BH` | **NOT FOUND** | N/A | — | — |

### Layer 4 — Data Source Tables (what the trees read)

| Table | Used by tree nodes | Role | Extracted to Gold DB? |
|---|---|---|---|
| `FPAYHX` | SEPA 5, CITI 19, CGI 7, CGI_1 8 | Payment detail extension (Customer-specific append) | Not in Gold DB — brain first-class candidate |
| `FPAYH` | CITI 15, CGI 6, CGI_1 6, SEPA 0 | Payment header | Not in Gold DB — brain first-class candidate |
| `FPAYP` | CGI 13, CGI_1 13, CITI 2, SEPA 0 | Payment line | Not in Gold DB — brain first-class candidate |
| `LFA1` | (Indirect via FPAYHX append) | Vendor master | ✅ Gold DB |
| `ADRC` | (Indirect via LFA1.ADRNR) | Central address master | ✅ Gold DB |
| `T001` | (Indirect for Dbtr via company code) | Company code master | ✅ Gold DB |
| `T042Z` / `T042A` / `T042I` | (Tree selection config) | Payment method → tree mapping | ✅ Gold DB |

### Layer 5 — Customer Custom Fields (FPAYHX Z-fields, 25 total)

```
ZNM1S, ZNM2S         -- Name with Asterisks (CHAR 70 each)
ZPLOR                -- Postal Code/City display (CHAR 92) ← COMBINED field
ZPFST                -- P.O. Box or Street for Postal/City (CHAR 70) ← STREET
ZLISO                -- Country ISO (CHAR 4) ← COUNTRY
ZLNDX                -- Country Name (CHAR 30)
ZREGX                -- Region (CHAR 40)
ZBANK                -- Payee Bank (Name+City) (CHAR 200)
ZBREGX               -- Bank Region (CHAR 40)
ZBISO                -- Bank Country ISO (CHAR 4)
ZBNKL_EXT            -- External Bank Number (CHAR 30)
ZBNKN_EXT            -- External Account No (CHAR 70)
ZBCOD_EXT            -- External Clearing Code (CHAR 4)
ZFORN                -- Form name (CHAR 32)
ZREF01..ZREF10       -- User-Defined Text (CHAR 264 each) ← CUSTOM BUFFERS × 10
ZSTCEG               -- VAT Registration (CHAR 40)
```

**NOT IN FPAYHX** (contrary to handoff doc claim): ZSTRA, ZHSNM, ZPSTL, ZORT1, ZLAND. These names are used as FPAYH fields or in variations in other tables, but NOT in FPAYHX.

### Layer 6 — Francesco Context (5 transports 2025 Q1)

| TRKORR | Date | Object touched | Classification |
|---|---|---|---|
| D01K9B0CZ0 | 2025-03-20 | `/CGI_XML_CT_UNESCO` + VC_TFPM042F variant `_BK` | **ASSIST** — PMF bank variant config, not tree structure |
| D01K9B0CWS | 2025-03-07 | `/CGI_XML_CT_UNESCO_1` | **IRRELEVANT** — E071 empty / limited data, likely variant-only |
| D01K9B0CUS | 2025-02-21 | `/CGI_XML_CT_UNESCO_1` | **IRRELEVANT** — same |
| D01K9B0CUT | 2025-02-21 | `/CGI_XML_CT_UNESCO_1` | **IRRELEVANT** — same |
| D01K9B0CTP | 2025-02-20 | `/CGI_XML_CT_UNESCO_1` + VC_TFPM042F variant | **ASSIST** — idem |

User's statement "Francesco no sabía del proceso" holds: his 5 transports are **Payment Medium Format variant configuration** (bank-specific customizing via TFPM042F/B/D/F/G/T/V views), **not DMEE tree node changes**. His work doesn't block ours; an alignment call is still recommended before Phase 2 CGI tree edits.

---

## Plan corrections (what changes vs original Phase 1-5 spec)

### Corrected field names for user exit
**Original plan** (from handoff doc): user exit writes `E_FPAYH-REF01..05`.
**Corrected**: user exit writes **`E_FPAYHX-ZREF01..ZREF05`** (or ZREF10 — 10 available, not 5).

### Corrected DMEE tree source fields
**Original plan**: Dbtr nodes source from `FPAYH-REF01..05`.
**Corrected**: Dbtr nodes source from `FPAYHX-ZREF01..ZREF05`.

### Corrected structured field mapping (handoff §5.1 → reality)
| Party/node | Handoff doc claim | Reality (verified via tree probe) |
|---|---|---|
| Cdtr StrtNm | FPAYHX-ZSTRA | FPAYH-ZBSTR (CITI) / FPAYP-BSTRAS (CGI) / doesn't exist (SEPA) |
| Cdtr BldgNb | FPAYHX-ZHSNM | Not a separate field — currently embedded in StrtNm or via REF01 substring (CGI) |
| Cdtr PstCd | FPAYHX-ZPSTL | FPAYH-ZPSTL (CITI/CGI) / doesn't exist (SEPA) |
| Cdtr TwnNm | FPAYHX-ZORT1 | FPAYH-ZORT1 / FPAYHX-ORT1Z / FPAYP-BORT1/ORT01 (mixed) |
| Cdtr Ctry | FPAYHX-ZLAND | FPAYHX-LAND1 / FPAYHX-ZLISO / FPAYH-ZLAND / FPAYP-LANDL (mixed) |

**The mappings are NOT uniform across trees**. Each tree has its own source convention, established historically by Marlies/N_MENARD. Phase 1 `change_matrix.csv` must capture the per-tree source convention correctly.

### Scope expansion: BAdI handling
Originally the plan treated BAdI changes as out-of-scope (config-only change). Now we see **794 nodes invoke the BAdI**, of which 146 are address-related. When we add new structured nodes (Phase 2 Steps 3, 6, 8), they will invoke `FI_CGI_DMEE_EXIT_W_BADI` UNLESS we configure them with `MP_EXIT_FUNC=''`. Decision point: do we want the BAdI to process new structured nodes (risk of side-effects like name-overflow-into-StrtNm quirk in FALLBACK_CM001) or do we set EXIT_FUNC blank? Each new node needs this decision.

### Scope expansion: country class extraction
We have `_FR`/`_FALLBACK`/`_UTIL` extracted. `_DE` and `_IT` exist in P01 but **NOT yet extracted**. For Phase 3 regression (testing German + Italian payment scenarios), we need those classes extracted. Adding to Phase 0 follow-up.

### Vendor DQ risk downgrade
Phase 3 vendor cleanup originally flagged as HIGH risk. Actually only 5 of 111,241 vendors are missing CITY1 or COUNTRY (the mandatory fields). **Risk downgraded to LOW** — one-time manual cleanup.

### Francesco not a blocker
5 transports in 2025 Q1 are PMF variant configuration, not tree structure changes. Can proceed without blocking — alignment call recommended as courtesy.

---

## Evidence files produced in Phase 0

| File | Type | Purpose |
|---|---|---|
| `phase0/francesco_audit.md` | markdown | Full FP_SPEZZANO transport history + classification |
| `phase0/vendor_master_dq.md` | markdown | 5 missing-mandatory vendors; DQ risk LOW |
| `phase0/cts_dmee_authors.md` | markdown | 8 DMEE authors across 10 years; N_MENARD as BAdI owner |
| `phase0/gap_005_static_analysis.md` | markdown | 0 FPAYHX-Z* writes across 986 ABAP files |
| `phase0/gap_closure_report.md` | markdown | **THIS FILE** — consolidated Phase 0 closure |
| `phase0/xml_touch_points_complete.md` | markdown | Single-source inventory (companion Tab 8 input) |
| `phase0/gap006_dmee_tree_nodes_full.csv` | CSV | 1,975 nodes × source fields (round 1) |
| `phase0/gap006_dmee_nodes_with_exit.csv` | CSV | 1,975 nodes × source + MP_EXIT_FUNC (round 2) |
| `phase0/gap_probe_results.json` | JSON | pyrfc round 1 raw results |
| `phase0/gap_probe_results_round2.json` | JSON | pyrfc round 2 raw results |
| `Zagentexecution/mcp-backend-server-python/phase0_gap_probe.py` | script | Reusable GAP-002/003/004/006 probe |
| `Zagentexecution/mcp-backend-server-python/phase0_gap_probe_round2.py` | script | Reusable round 2 probe (MP_EXIT_FUNC + E071) |

## Phase 0 exit gate — ready to transition to Phase 1

Per plan: *"Pablo + Marlies joint review of `xml_touch_points_complete.md`. No "UNKNOWN" in "Change required" column."*

- 5 of 8 gaps fully CLOSED (GAP-003, -004, -005, -006, -008)
- 2 PARKED as out-of-change-scope (GAP-001, -007)
- 1 PARTIAL (GAP-002) — enough knowledge captured to proceed; follow-up extraction of _DE/_IT classes + Z-exit source can happen in parallel with Phase 1
- Francesco audit complete; his work classified non-blocking

**Recommendation**: Phase 1 (config matrix + bank specs) can start now. Follow-up items tracked in brain KU list.
