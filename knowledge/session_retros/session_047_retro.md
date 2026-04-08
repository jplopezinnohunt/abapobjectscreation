# Session #047 Retro — INC-000006073 Travel Business Area Root Cause Analysis

**Date:** 2026-04-08
**Duration:** Extended session (full day)
**Previous:** #046 (Upgrade 2026 open customizing requests)

## What We Did

### 1. Ticket Analysis
- Parsed EML email with 3 embedded screenshots (posting run, error log, posting lines)
- Identified: PRRW posting run for IIEP traveler 10133079 (Katja HINZ) on UNES budget
- Error: RW609 + ZFI020 "For IIEP company code, only use business area PAR, IBA or FEL"

### 2. Substitution/Validation Framework Analysis
- Mapped the complete BusA substitution chain: YRGGBS00 → U910 → YCL_FI_ACCOUNT_SUBST_READ → YTFI_BA_SUBST/YBASUBST
- Extracted GB901 (583 rows), GB02C, GB903, T100_ZFI, T80D from P01 → saved to Gold DB
- Discovered IIEP has ZERO global rules in YTFI_BA_SUBST (only Z1 entries)
- Proved ZFI020 validation ALLOWS empty BusA (the `<>` checks pass for empty string)

### 3. GGB1 Substitution Results (GB922)
- Extracted GB922 — the actual result assignments for IIEP substitution
- Found 9 steps: Step 001 (U910 lookup), Step 002 (PYCUR/BVTYP for 2021042/2021061), **Step 003 (GSBER='PAR' unconditional for TV)**
- Step 003 would fix the problem — but the error occurs BEFORE GGB1 runs

### 4. Travel Exit Code Analysis
- Extracted ZXTRVU05 — the Travel validation exit. BusA derivation for non-UNES company codes is **commented out**
- Extracted ZCL_IM_TRIP_POST_FI (14 methods) — BAdI for Travel FI posting. Method CM00A reads PA0027 subtype 02 for BusA fallback
- PA0027-02 for traveler 10133079: **expired 2021-01-31**
- Extracted RPRFIN00_40 (posting run) and RPRMR010_40 (main routines) — traced GSBER flow
- Extracted LHRTSF01 (3,527 lines) via agent — found vendor GSBER clearing at line 1693 and intercompany clearing creation at lines 2479-2512

### 5. Travel Document Pattern Analysis
- Extracted PTRV_SCOS (trip cost assignment) — 2,972 IIEP trips total
- Found 475 UNES-funded IIEP trips across 62 unique travelers
- ALL 61 travelers with AKONT=2021042 → successful postings
- Only 1 traveler (Katja HINZ) with AKONT=2021011 → FAIL

### 6. Vendor Master Data Discovery
- LFB1 comparison: Katja has AKONT=2021011 in IIEP (different from UNES=2021042) — UNIQUE among 62 travelers
- LFA1: Katja has KTOKK=SCSA (Service Contract), created 2016-11-24 when PERSG=M
- Changed to PERSG=1 (International Staff) in 2017-02 but vendor KTOKK/AKONT never updated
- Other 2 SCSA vendors (10148017, 10151714) have AKONT=2021042 — they work fine

### 7. 180 Custom Travel Objects Discovered
- TADIR search found 180 Z/Y objects in Travel domain
- Key: ZCL_IM_TRIP_POST_FI, ZENH_UNES_CALL_TRIP_BAPI2, YHRTRV_IF, YPR_TRIP_COST_ASSIGNMENT_DATA2
- Extracted 20+ source files via RPY_PROGRAM_READ

### 8. Source Code Extracted (20+ files)
All saved to `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/`:
- ZCL_IM_TRIP_POST_FI (14 methods)
- ZXTRVU05, ZXTRVU03
- YFI_RPRAPA00_COMPL, YFI_YRGGBS00_EXIT, YFI_LFBK_TRAVEL_UPDATE
- YPR_TRIP_COST_ASSIGNMENT_DATA2, YPR_TRIP_DATA_FORM_ROUTINES, YPR_TRIP_DATA_TOP, YPR_TRIP_ROUT_1_4
- ZENH_UNES_CALL_TRIP_BAPI2, ZENH_UNES_GET_TRIP_BAPI
- ZCL_IM_BADI_EXITS_RPRAPA00 (6 methods)

## What We Found (Root Cause)

**Identified:** Vendor 10133079 (Katja HINZ) has a unique AKONT=2021011 in IIEP (all other 61 IIEP travelers with UNES-funded trips have AKONT=2021042). GL 2021011 is NOT in any GGB1 substitution rule.

**NOT yet identified:** WHERE exactly in the code the GSBER becomes blank for the IIEP vendor line. We know:
- PTRV_TRANSLATE line 852: only sets GSBER when bukst=bukrs (same company) — doesn't apply for intercompany
- PTRV_TRANSLATE line 1693: clears GSBER on vendor lines
- GGB1 Step 003 would put PAR unconditionally for TV — but error occurs BEFORE GGB1 runs
- The exact validation point that generates RW609 is unknown

## What We Should Have Done Better

### 1. Jumped to conclusions too early
Multiple times we declared "root cause found" prematurely:
- First: "missing substitution rule for 0005098030" — wrong account
- Then: "source system (DUO) changed the document structure" — wrong, it was always intercompany
- Then: "vendor-only pattern never existed" — incorrect framing, the posting has 2 lines
- Then: "PA0027 expired is the cause" — partially right but not the full picture
- Then: "GGB1 Step 003 puts PAR unconditionally" — true but error occurs before GGB1

### 2. "Vendor-only" terminology was wrong
The posting has 2 lines (IIEP + UNES). Calling it "vendor-only" confused the analysis for several iterations. Should have always described it as "2-line intercompany document where the IIEP line has empty BusA."

### 3. Did not correlate by same GL account early enough
Should have immediately filtered for GL 2021011 across all company codes and all funding types. Instead we analyzed 12,552 docs broadly before narrowing down.

### 4. Agent results accepted without verification
The code analysis agent claimed GGB1 Step 003 exists with unconditional PAR. GB901 confirmed the condition exists but the agent invented a "Step 003" numbering that didn't match GB901 data. Had to re-verify from GB922 (which confirmed the step EXISTS but the numbering was different).

### 5. Did not read the PTRV tables early
PTRV_SCOS was the definitive evidence. If we had extracted it in the first hour, we would have seen COMP_CODE=UNES immediately and saved 3+ hours of hypothesis testing.

## Open Questions for Next Session

1. **WHERE does GSBER become blank?** — Need ST01/ST05 trace or test posting in D01
2. **Why does RW609 fire before GGB1?** — Is it the Travel module's internal validation or the FI simulation?
3. **Should AKONT be corrected for vendor 10133079?** — Change from 2021011 to 2021042 via FK02
4. **Are there other vendors with inconsistent KTOKK/AKONT?** — 7,609 IIEP vendors with AKONT=2021011, how many have wrong KTOKK?

## Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | Root cause analysis document (rewritten 3x) | `knowledge/domains/FI/INC-000006073_travel_busarea_analysis.md` |
| 2 | Travel BusA derivation knowledge | `knowledge/domains/FI/travel_busarea_derivation.md` |
| 3 | HTML companion (regenerated 2x) | `companions/inc6073_travel_busarea_rca.html` |
| 4 | 20+ Travel source code files | `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/` |
| 5 | GB901 + GB922 + GB02C + T100_ZFI + T80D + GB903 in Gold DB | Gold DB (6 new tables) |

## New Knowledge Created

- **Travel domain:** First systematic analysis of UNESCO Travel posting architecture
- **PTRV_SCOS patterns:** 2,972 IIEP trips classified by funding type
- **180 custom Travel objects catalogued** in `travel_busarea_derivation.md`
- **GGB1 IIEP substitution fully mapped:** 9 steps with conditions and results (GB901 + GB922)
- **PTRV_TRANSLATE/LHRTSF01 GSBER flow traced:** Lines 852, 1693, 2479-2512

## PMO Updates

| Action | Item |
|---|---|
| ADD | H34: INC-000006073 — Vendor 10133079 AKONT=2021011 not in GGB1 rule. Fix: correct AKONT or extend GGB1. Open: find exact validation rejection point. |
| ADD | G55: Extract PTRV_SCOS/PTRV_SHDR 2024-2026 to Gold DB for Travel domain |
| ADD | G56: Create Travel domain knowledge (`knowledge/domains/Travel/`) |
| ADD | G57: Scan 7,609 IIEP vendors with AKONT=2021011 for KTOKK inconsistencies |
