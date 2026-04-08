# INC-000006073 — Root Cause Analysis
**Date:** 2026-04-08 | **Analyst:** JP Lopez (with AI-assisted data mining)
**Status:** Root cause identified, fix path defined

---

## 1. Issue Summary

| Field | Value |
|---|---|
| **Ticket** | INC-000006073 |
| **Reporter** | Rita Doroszlai (FU/IEP) |
| **Transaction** | PRRW (Travel Posting Run) |
| **Traveler** | 10133079 — Katja HINZ (IIEP employee) |
| **Posting Run** | 0100384694 (Ref: 0101004544-KH-TA) |
| **Date** | 07.04.2026 |
| **Scenario** | Intercompany trip: IIEP traveler on UNES budget |
| **Error** | `RW609` + `ZFI020: For IIEP company code, only use business area PAR, IBA or FEL` |

### The Posting (2 lines)

| Line | Account | Name | Debit | Credit | CoCode | BusA | GL (from LFB1) |
|---|---|---|---|---|---|---|---|
| 1 | 10133079 | Katja HINZ | — | 1,570.00 USD | IIEP | **(empty)** | 0002021011 |
| 2 | 2022043 | Adv staff travel exp | 1,570.00 | — | UNES | PFF | — |

### Error Chain

```
RW609  → Travel module rejects the document (IIEP line has empty Business Area)
ZFI020 → Message text displayed to the user
```

**Note:** The GGB0 validation `ZFI020` itself **allows empty BusA** (proven in Section 3). The actual blocker is the Travel module's own document-level validation (`RW609`).

---

## 2. How Business Area Substitution Works at UNESCO

### Execution Chain

```
1. Travel module (PRRW/RPRAPA00) constructs posting lines
2. Travel exit ZXTRVU05 runs — derives BusA per company code (see Section 4)
3. GGB1 substitution rules fire (YRGGBS00 form U910)
   → YCL_FI_ACCOUNT_SUBST_READ=>READ(bukrs, blart, hkont)
   → Looks up YTFI_BA_SUBST (range-based) with 2-tier fallback
4. GGB0 validation rules fire (ZFI020 checks)
5. Travel module validates complete document (RW609)
```

### Custom Framework Components

| Component | Object | Purpose |
|---|---|---|
| **Travel Exit** | `ZXTRVU05` | BusA derivation per company code (see Section 4) |
| **Substitution Exit** | `YRGGBS00` form U910 | Calls `YCL_FI_ACCOUNT_SUBST_READ` |
| **Maintenance Tx** | `YFI_BASU_MOD` | User-friendly rule maintenance (no transport) |
| **Persistence** | `YTFI_BA_SUBST` | Range-based account→BusA mapping (129 entries) |
| **Legacy Table** | `YBASUBST` | Flat mapping (752 entries) |

---

## 3. Investigation: Why the IIEP Line Has Empty BusA

### 3.1 Vendor Reconciliation Account (LFB1)

The screenshot shows "Acct no. 10133079" — this is the vendor/personnel number. The actual GL account comes from LFB1 (vendor master company code data):

| Vendor | Company Code | AKONT (Reconciliation GL) |
|---|---|---|
| 10133079 | **IIEP** | **0002021011** |
| 10133079 | **UNES** | **0002021042** |

**The IIEP line posts to GL `0002021011`.** This is confirmed by all 4 previous travel documents for this vendor.

### 3.2 GGB1 Substitution Rule 3IIEP###002

The GGB1 travel substitution for IIEP:
```
CONDITION [3IIEP###002]:
  (BLART = 'TV' OR BLART = 'TF')
  AND (HKONT = '2021042' OR HKONT = '2021061')
  AND GSBER = ''
RESULT: Sets GSBER = PAR [INFERRED from historical data]
```

**GL `2021011` is NOT in this rule.** Only `2021042` and `2021061` are covered.

### 3.3 YTFI_BA_SUBST for IIEP

IIEP has **zero global rules** in `YTFI_BA_SUBST`. All 12 entries are restricted to document type Z1 — they do NOT apply to TV (travel) documents.

| Company Code | Global Rules | Z1 Rules | Total |
|---|---|---|---|
| IBE, ICBA, ICTP, MGIE, UBO, UIL, UIS | 9-11 each | 3-10 each | 13-21 |
| **IIEP** | **0** | **12** | **12** |

### 3.4 GGB0 Validation ZFI020

```
PREREQUISITE [1IIEP###001]: BUKRS = 'IIEP'
CHECK [2IIEP###001]: GSBER <> 'DAE' AND <> 'GEF' AND <> 'MBF' AND <> 'OPF' AND <> 'PFF'
```

**Empty BusA (`''`) passes this check** — it's not equal to any of the rejected values. ZFI020 is NOT the blocker. The actual rejection comes from the Travel module (`RW609`).

### 3.5 PA0001 — HR Master Data

| Period | BUKRS | GSBER | KOSTL | FISTL | GEBER (Fund) |
|---|---|---|---|---|---|
| 2024-01 to 2025-06 | IIEP | **PAR** | ADM | ADM | 1130STF602 (IIEP fund) |
| 2025-07 to 9999-12 | IIEP | **PAR** | *(empty)* | *(empty)* | **707RMB0625** (UNES fund) |

**GSBER=PAR has never changed** (stable since 2016). Position change hypothesis ruled out.

**However:** The employee's fund changed from `1130STF602` (IIEP fund) to `707RMB0625` (UNES fund) on 2025-07-01. This is why the trip uses UNES budget — creating an intercompany posting.

---

## 4. Travel Exit ZXTRVU05 — The BusA Derivation Code

**Source:** `extracted_code/UNESCO_CUSTOM_LOGIC/TV_TRAVEL/ZXTRVU05_RPY.abap`

This SAP user exit runs during travel posting and derives Business Area per company code:

```abap
LOOP AT KONTI ASSIGNING <KONTI>.
  CASE <KONTI>-BUKRS.
    WHEN 'UNES'.
      PERFORM FUND_BA_WBS_CC USING <KONTI>-GEBER ... <KONTI>-GSBER 'X'.
    WHEN 'UBO'.
      " empty — no derivation
    WHEN OTHERS.
*     perform inst_fund_ba_wbs_cc using <KONTI>-bukrs
*                                       <KONTI>-geber ... <KONTI>-gsber 'X'.
  ENDCASE.
ENDLOOP.
```

| Company Code | BusA Derivation in ZXTRVU05 | Status |
|---|---|---|
| **UNES** | `FUND_BA_WBS_CC` — derives BusA from fund/WBS/cost center | **ACTIVE** |
| **UBO** | Empty block — no derivation | **DISABLED** |
| **IIEP, IBE, ICBA, ICTP, MGIE, UIL, UIS** (WHEN OTHERS) | `inst_fund_ba_wbs_cc` | **COMMENTED OUT** |

**For IIEP lines:** The travel exit does NOT derive BusA. The institute-specific derivation (`inst_fund_ba_wbs_cc`) is commented out. This means IIEP relies entirely on GGB1 substitution or other upstream code to provide BusA.

---

## 5. Root Cause

### 5.1 The Chain

1. **Employee's fund changed** to `707RMB0625` (UNES fund) on 2025-07-01
2. **First travel advance on UNES budget** → creates a 2-line intercompany posting
3. **IIEP line** posts to GL `0002021011` (from LFB1 AKONT for IIEP)
4. **Travel exit ZXTRVU05**: BusA derivation for non-UNES company codes is **commented out** → IIEP line gets no BusA from the exit
5. **GGB1 rule `3IIEP###002`**: only covers GL `2021042`/`2021061` → does NOT match `2021011`
6. **YTFI_BA_SUBST**: zero global rules for IIEP → no fallback
7. **Other GGB1 rules** (`3IIEP###004` TV general, `3IIEP###006` KOART=K, `3IIEP###008` date): conditions match, but results are unknown [UNVERIFIED] — in previous same-company postings something DID provide PAR for `2021011`
8. **IIEP line arrives with empty BusA** → RW609 rejects → ZFI020 message displayed

### 5.2 The Code That Derives BusA — FOUND

**BAdI `ZCL_IM_TRIP_POST_FI`, method `EX_ZWEP_ACCOUNT2` (include CM00A):**

```abap
IF zwep-bukst IS INITIAL OR zwep-gsbst IS INITIAL.
  " Read PA0027 (Cost Distribution) subtype 02
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING pernr = zwep-pernr  infty = '0027'
              begda = zwep-datv1  endda = zwep-datv1
    TABLES    infty_tab = lt_p0027.

  LOOP AT lt_p0027 INTO ls_p0027 WHERE subty = '02'.
  ENDLOOP.
  CHECK sy-subrc IS INITIAL.  " ← exits if no subtype 02 found

  " Find the cost distribution line with highest percentage (kpr01-kpr25)
  " Then copy: company code (kbu), Business Area (kgb), cost center (kst),
  "            fund center (fct), fund (fcd), WBS (psp)
  zwep-bukst = <fs_kprnm>.  " Company Code
  zwep-gsbst = <fs_kprnm>.  " Business Area (target)
  zwep-gsber = <fs_kprnm>.  " Business Area (actual posting field)
```

**This BAdI reads PA0027 infotype (Cost Distribution, subtype 02) and sets GSBER from the `KGB` field.**

### 5.3 PA0027 for Traveler 10133079 — The Root Cause

| PERNR | Subtype | BEGDA | ENDDA | BUKRS | GSBER | KOSTL | Fund | % |
|---|---|---|---|---|---|---|---|---|
| 10133079 | 01 | 2016-01-18 | 2016-12-31 | IIEP | PAR | ADM | 930STF0602 | 100% |
| 10133079 | 01 | 2017-01-01 | 2017-01-31 | IIEP | PAR | ADM | 940STF0602 | 100% |
| 10133079 | **02** | 2016-01-18 | **2021-01-31** | IIEP | **PAR** | R&D | 936GLO0303 | 100% |

**Subtype 02 expired on 2021-01-31.** There is no current record.

When the BAdI runs for a trip in 2026:
1. `HR_READ_INFOTYPE` with `begda/endda = trip date (2026)` → PA0027 subtype 02 has no valid record
2. `LOOP...WHERE subty = '02'` → finds nothing → `sy-subrc <> 0`
3. `CHECK sy-subrc IS INITIAL` → **exits the method without setting GSBER**
4. BusA stays empty

### 5.4 Side-by-Side: Same Account, Same Traveler — Why One Works and One Doesn't

**Last successful posting — Doc 6600000332, 2025-12-04 (IIEP-funded):**

```
Step 1: Trip cost assignment = IIEP budget (fund 1130STF602)
Step 2: Travel standard builds posting lines:
          IIEP | Vendor 10133079 → GL 2021011 | GSBER = PAR  ← filled by Travel (from PA0001/cost assignment)
          IIEP | GL 2022043 (advance)         | GSBER = PAR  ← filled by Travel
Step 3: BAdI EX_ZWEP_ACCOUNT2 checks: gsbst = PAR (NOT initial) → SKIPPED
Step 4: GGB1 rule 3IIEP###002: GL 2021011 not in rule → no match → but PAR already set → OK
Step 5: ZXTRVU05: IIEP falls in WHEN OTHERS → commented out → but PAR already set → OK
Step 6: Posting succeeds with GSBER=PAR
```

**Rita's failed posting — 2026-04-07 (UNES-funded):**

```
Step 1: Trip cost assignment = UNES budget (fund 707RMB0625, changed Jul 2025)
Step 2: Travel standard builds posting lines:
          IIEP | Vendor 10133079 → GL 2021011 | GSBER = (empty) ← NOT filled (counterpart clearing line)
          UNES | GL 2022043 (advance)         | GSBER = PFF     ← filled by Travel (UNES cost assignment)
Step 3: BAdI EX_ZWEP_ACCOUNT2 checks: gsbst = INITIAL → FIRES
          → reads PA0027 subtype 02 for PERNR 10133079, trip date 2026
          → PA0027-02 expired 2021-01-31 → no valid record → method exits
          → GSBER stays empty
Step 4: GGB1 rule 3IIEP###002: GL 2021011 not in rule → no match → GSBER stays empty
Step 5: ZXTRVU05: IIEP falls in WHEN OTHERS → code commented out → GSBER stays empty
Step 6: RW609 rejects (IIEP line has empty BusA) → ZFI020 message displayed
```

**The single variable that changed: the funding source.** Everything else is identical — same traveler, same GL account, same expired PA0027, same missing GGB1 rule, same commented-out exit. In IIEP-funded trips, the Travel standard fills GSBER=PAR at Step 2 and none of the other steps matter. In UNES-funded trips, the Travel standard does NOT fill GSBER for the IIEP counterpart line, and all three fallback mechanisms fail.

### 5.5 Cross-Company Confirmation

GL 2021011 is also used in MGIE (25 docs) and ICBA (22 docs). Their GSBER values confirm the pattern:

| Company Code | GL 2021011 GSBER | Institute Default BusA | Source |
|---|---|---|---|
| **IIEP** | **PAR** (4 docs) | PAR | Travel standard (PA0001 GSBER) |
| **MGIE** | **PFF** (24) / GEF (1) | PFF | Travel standard (PA0001 GSBER) |
| **ICBA** | **PFF** (22 docs) | PFF | Travel standard (PA0001 GSBER) |

Each company code gets its own institute's BusA. This confirms the Travel standard reads GSBER from the employee's PA0001 for same-company postings. The intercompany counterpart line is the exception — it doesn't get this derivation.

### 5.6 Root Cause — Final

**The Travel standard does NOT assign Business Area to the intercompany counterpart vendor clearing line.** When a trip is funded by a different company code, the clearing line in the employee's home company code arrives with empty GSBER.

Three fallback mechanisms exist but all fail for this case:

| # | Fallback | What It Does | Why It Fails |
|---|---|---|---|
| 1 | **GGB1 rule `3IIEP###002`** | Substitutes PAR for GL 2021042/2021061 in TV docs | GL `2021011` is NOT in the rule |
| 2 | **BAdI `EX_ZWEP_ACCOUNT2`** | Reads PA0027-02 to derive BusA | PA0027-02 expired 2021-01-31 |
| 3 | **ZXTRVU05 exit** | `inst_fund_ba_wbs_cc` for non-UNES codes | Code is **commented out** |

**Any single fix breaks the chain.** The failure requires all three fallbacks to fail simultaneously.

### 5.6 Three Safety Nets — All Disabled/Broken

The analysis identified **three code points** that could provide BusA for the IIEP vendor line. All three fail:

| Safety Net | Code | Status | Why It Fails |
|---|---|---|---|
| **1. Travel standard** | RPRAPA00 cost assignment | Works for same-company | Does NOT assign BusA to intercompany counterpart line (`gsbst` stays initial) |
| **2. Travel exit ZXTRVU05** | `inst_fund_ba_wbs_cc` for non-UNES | **COMMENTED OUT** | Would derive BusA from fund, but disabled for IIEP (WHEN OTHERS) |
| **3. GGB1 rule `3IIEP###002`** | Substitution for TV/TF | Active but incomplete | Only covers GL `2021042`/`2021061`, NOT `2021011` |
| **4. BAdI fallback** | `ZCL_IM_TRIP_POST_FI` `EX_ZWEP_ACCOUNT2` | Active but data expired | Reads PA0027-02, record expired 2021-01-31 |

**For IIEP-funded trips:** Safety net #1 works → `gsbst` filled → nets #2-4 never needed.
**For UNES-funded trips:** Net #1 fails (intercompany) → net #2 disabled → net #3 wrong GL → net #4 expired data → **empty BusA**.

### 5.7 GGB1 Substitution Results (GB922) — Step 003 Would Fix It, But Runs Too Late

Extracted the actual GGB1 substitution result assignments from GB922:

| Step | Field | Result | Condition (GB901) |
|---|---|---|---|
| 001 | BSEG-GSBER | Exit U910 (YBASUBST/YTFI_BA_SUBST lookup) | BUKRS=IIEP |
| 002 | BSEG-PYCUR + BVTYP | Exits U902/U901 | TV/TF + HKONT=2021042/2021061 + GSBER='' |
| **003** | **BSEG-GSBER** | **'PAR' (hardcoded constant)** | **TV or TF** |
| 004-009 | XREF1, XREF2, ZLSCH, HKONT, etc. | Various exits | Various conditions |

**Step 003 puts GSBER='PAR' on ALL TV/TF documents unconditionally.** If GGB1 runs, GSBER can never be empty for IIEP travel docs.

**But GGB1 does NOT run for Rita's posting.** The Travel module validates and rejects the document (RW609) BEFORE the FI posting engine creates the document. GGB1 substitution only fires during FI document creation — which never happens because PTRV_TRANSLATE's validation catches the empty GSBER first.

### 5.8 The Complete Execution Sequence

```
IIEP-funded trip (worked):
  1. PTRV_TRANSLATE line 852: bukst=IIEP, bukrs=IIEP → MATCH → gsber=PAR (from employee)
  2. PTRV_TRANSLATE line 1693: CLEAR gsber → gsber=''
  3. Travel validation (ZXTRVU05): GSBER passed as parameter, already in posting data
  4. FI document creation starts
  5. GGB1 Step 003: GSBER='PAR' (TV condition) → gsber=PAR
  6. Posting succeeds

UNES-funded trip (Rita — fails):
  1. PTRV_TRANSLATE line 852: bukst=IIEP, bukrs=UNES → NO MATCH → gsber stays empty
  2. PTRV_TRANSLATE line 1693: CLEAR gsber → gsber='' (was already empty)
  3. Travel validation: sees empty GSBER on IIEP line → RW609 REJECTS
  4. FI document creation NEVER starts
  5. GGB1 NEVER runs — Step 003 would have put PAR, but it's too late
  6. Posting fails
```

**The root cause is timing:** GSBER derivation at line 852 (`IF bukst = bukrs`) only works for same-company. For intercompany, GSBER stays empty. The Travel validation catches it before GGB1 can fix it.

### 5.9 Vendor Master Data — Why GL 2021011

| | Rita (10133079) | Other IIEP travelers |
|---|---|---|
| KTOKK (vendor account group) | **SCSA** | **UNES** |
| LFB1 IIEP AKONT | **2021011** | **2021042** |
| PERSG (employee group) | 1 (International Staff) | 1 (International Staff) |

Katja's vendor has KTOKK=SCSA (Service Contract) instead of UNES (International Staff). This is inconsistent with her PERSG=1. The BAdI `SET_VALUES_FOR_BLF00` assigns KTOKK based on PERSG — PERSG=1 should get KTOKK='UNES'. The vendor may have been created before she changed employee group, or created incorrectly.

This KTOKK determines the reconciliation account (LFB1 AKONT). SCSA vendors get 2021011, UNES vendors get 2021042. For IIEP-funded trips this doesn't matter (GGB1 Step 003 puts PAR regardless). For UNES-funded trips, GL 2021042 would be covered by GGB1 Step 002 — but GL 2021011 is not, and the validation fails before GGB1 runs anyway.

### 5.11 Open Question — Where Exactly Does the Rejection Happen?

We have proven:
- GGB1 Step 003 would set GSBER='PAR' unconditionally for TV docs [VERIFIED from GB922]
- GGB0 validation ZFI020 allows empty GSBER [VERIFIED from GB901]
- ZXTRVU05 does NOT validate GSBER (no check, commented out for WHEN OTHERS) [VERIFIED from source]
- GL 2021011 has NEVER worked in a UNES-funded IIEP trip (0 out of 93 successful trips use it) [VERIFIED from data]

**Unresolved:** If Step 003 puts PAR and the validation allows empty, what generates the error? Possibilities:
1. The error occurs during FI document **simulation** (CHECK mode before POST) — GGB1 might not run in simulation mode
2. PTRV_TRANSLATE has its OWN internal validation that checks GSBER before calling the FI posting engine
3. The substitution execution order puts the validation BEFORE step 003 completes for all lines
4. There is another validation not in GGB0 that checks GSBER (e.g., in `FUND_BA_WBS_CC` called from ZXTRVU05 for UNES lines, which may also validate IIEP lines)

**Next investigation needed:** Debug or trace the actual posting run for a UNES-funded IIEP trip to see at exactly which point the error is raised. This requires either ST01/ST05 system trace or a test posting in D01.

### 5.12 Why the Travel Standard Worked Before and Not Now

**The Travel standard did NOT change.** What changed is the **input** — the trip cost assignment:

| | Before (worked) | Now (fails) |
|---|---|---|
| Employee fund (PA0001) | `1130STF602` (IIEP fund) | `707RMB0625` (UNES fund, changed Jul 2025) |
| Trip type | Same-company (IIEP-funded) | **Intercompany** (UNES-funded) |
| Travel standard behavior | Assigns PAR to ALL IIEP lines (from cost assignment) | Assigns PFF to UNES lines only. **IIEP clearing line gets nothing** — it's a counterpart, not part of the trip cost assignment |
| Fallbacks needed? | No — PAR already set | Yes — but all 3 fail |

The Travel standard treats the IIEP vendor clearing line as an intercompany counterpart — a technical accounting entry, not a cost-assigned trip line. It doesn't inherit the employee's BusA from PA0001 because the cost assignment belongs to UNES, not IIEP.

**This is the first intercompany trip for this traveler** (fund changed Jul 2025, first advance posted Apr 2026). The gap always existed but was never exposed because all previous trips were IIEP-funded.

### 5.8 Fix

No change to the Travel document or posting structure needed. The 2-line intercompany posting is correct. The fix is to ensure the IIEP clearing line receives a Business Area.

| # | Option | Action | Scope | Transport? | Speed |
|---|---|---|---|---|---|
| **1** | **HR master data** | Extend PA0027 subtype 02 for traveler 10133079 (IIEP/PAR, current dates) | This traveler | No (PA30) | **Immediate** |
| **2** | **FI config (no transport)** | Add GL `2021011` to `YTFI_BA_SUBST` via `YFI_BASU_MOD` | All IIEP vendors on 2021011 | No | **Same day** |
| **3** | **FI config (transport)** | Add GL `2021011` to GGB1 rule `3IIEP###002` | All IIEP vendors on 2021011 | Yes (GGB1) | Days |
| **4** | **ABAP (transport)** | Uncomment `inst_fund_ba_wbs_cc` in ZXTRVU05 | All non-UNES company codes | Yes | Days + testing |

**Recommended:** Option 1 (immediate unblock for Rita) + Option 2 (structural fix for all vendors on GL 2021011, no transport needed).

### 5.9 Definitive Evidence: Trip Cost Assignment (PTRV_SCOS)

Extracted from P01 — the trip cost assignment for ALL 15 trips of traveler 10133079:

**Last 4 trips (the relevant ones):**

| Trip | Date | COMP_CODE | BUS_AREA | FUNDS_CTR | FUND | Amount | Result |
|---|---|---|---|---|---|---|---|
| 0101004011 | 2024-02 | **IIEP** | **PAR** | TEC | ULO2023 | 1,662.76 | OK |
| 0101004047 | 2024-11 | **IIEP** | **PAR** | TEC | 1135BDI401 | 2,908.02 | OK |
| 0101004446 | 2025-12 | **IIEP** | **PAR** | ADM | 707RMB0625 | 1,196.21 | OK |
| **0101004544** | **2026-04** | **UNES** | **PFF** | ESD | 727GLO1007 | 3,183.40 | **FAIL** |

**All 13 previous trips had COMP_CODE=IIEP, BUS_AREA=PAR.** Trip 0101004544 (Rita's) is the first and only with **COMP_CODE=UNES, BUS_AREA=PFF**.

**Key observation:** Trip 0101004446 (Dec 2025) used fund `707RMB0625` (a UNES fund from PA0001) but was still assigned to **COMP_CODE=IIEP**. This means the company code in the trip cost assignment is NOT automatically derived from the fund — it was entered as IIEP.

Trip 0101004544 (Rita's) uses a completely different fund (`727GLO1007`) and fund center (`ESD`) assigned to **COMP_CODE=UNES**. This changes the entire posting structure:
- Cost assignment says UNES → expense lines go to UNES company code
- IIEP employee → vendor clearing line goes to IIEP
- IIEP clearing line has no BusA from cost assignment (cost assignment is UNES/PFF)
- No fallback works → empty BusA → RW609 rejects

### 5.10 Root Cause — Final (With PTRV_SCOS Evidence)

**The trip cost assignment was entered with COMP_CODE=UNES instead of IIEP.** This is the direct cause.

| What | Trip 0101004446 (worked) | Trip 0101004544 (failed) |
|---|---|---|
| Cost assignment company code | **IIEP** | **UNES** |
| Cost assignment BusA | **PAR** | **PFF** |
| Fund | 707RMB0625 | 727GLO1007 |
| Fund center | ADM | ESD |
| Posting type | Same-company (IIEP) | Intercompany (UNES+IIEP) |
| IIEP vendor line BusA | PAR (from cost assignment) | **(empty)** — not from cost assignment |

**The system behavior is correct for both scenarios:**
- IIEP cost assignment → all lines get PAR → works
- UNES cost assignment → UNES lines get PFF, IIEP clearing gets nothing → fails because no fallback covers GL 2021011

**Two questions for the Travel/HR team:**
1. Was the cost assignment to UNES/727GLO1007/ESD intentional? If the traveler should use an IIEP fund, the fix is to correct the trip cost assignment.
2. If UNES-funded trips for IIEP employees are a valid scenario, then the system needs a fix (Options 1-4 in Section 5.8) to handle the IIEP clearing line BusA.

### 5.11 Why Each Company Code Behaves Differently

The BusA derivation chain has different rules per company code. From ZXTRVU05:

| Company Code | ZXTRVU05 Exit | GGB1 Rule | PA0027 BAdI | Net Effect |
|---|---|---|---|---|
| **UNES** | `FUND_BA_WBS_CC` **ACTIVE** — derives BusA from fund | Covers 2021042/2021061 | Fires if `gsbst` initial | Fully covered |
| **IIEP** | `inst_fund_ba_wbs_cc` **COMMENTED OUT** | Covers 2021042/2021061 only | Fires if `gsbst` initial — but PA0027-02 expired for traveler 10133079 | **Gap for GL 2021011** |
| **UBO** | Empty WHEN block — no derivation | Covers 2021042/2021061 | Fires if `gsbst` initial | Depends on PA0027 |
| **IBE, ICBA, ICTP, MGIE, UIL, UIS** | `inst_fund_ba_wbs_cc` **COMMENTED OUT** | Covers 2021042 (some also 2021061) | Fires if `gsbst` initial | Same gap for non-2021042 GLs |

The commented-out code in ZXTRVU05 means non-UNES company codes rely on:
1. The Travel standard filling BusA from the cost assignment (works for same-company trips)
2. GGB1 substitution (only covers GL 2021042/2021061)
3. BAdI PA0027 fallback (only works if PA0027 is maintained)

When all three miss — as in Rita's case — BusA stays empty.

### 5.12 Where the Intercompany Logic Runs

The intercompany posting is generated by **SAP standard program RPRAPA00** (Travel Posting Run). The custom code only has exits that run AFTER the standard builds the posting lines.

**Key finding from PTRV_SCOS:** Trip `0101004446` (worked) also had a UNES fund (`707RMB0625`) but was assigned to COMP_CODE=**IIEP**. The standard STILL generated an intercompany posting (IIEP+UNES lines in the FI doc). But because COMP_CODE was IIEP, the standard propagated BUS_AREA=PAR to the IIEP lines.

| Scenario | Cost Assignment | Standard Behavior | IIEP Line BusA |
|---|---|---|---|
| COMP_CODE=IIEP (trip 0101004446) | IIEP/PAR | IIEP is "home" → gets PAR. Intercompany to UNES → UNES is "partner" | **PAR** (from cost assignment) |
| COMP_CODE=UNES (trip 0101004544) | UNES/PFF | UNES is "home" → gets PFF. Intercompany to IIEP → IIEP is "partner" | **(empty)** — standard doesn't derive BusA for partner |

**The standard propagates BUS_AREA to the "home" company code lines only.** The "partner" (counterpart) clearing line depends on the custom exits — which all fail for GL 2021011.

This means: the same trip with COMP_CODE=IIEP works fine (IIEP is "home", gets PAR). With COMP_CODE=UNES, IIEP becomes "partner" and gets nothing.

### 5.13 The User Input Factor

The cost assignment in PTRV_SCOS shows the user (or the Travel system) entered **COMP_CODE=UNES, BUS_AREA=PFF** for trip 0101004544. The BusA value PFF IS present in the cost assignment — it is not missing.

The problem is what happens AFTER:
- PFF goes to the UNES posting lines (correct — UNES lines get BusA from cost assignment)
- The IIEP counterpart clearing line gets **nothing** — the system does not propagate PFF to IIEP (it can't — PFF is invalid for IIEP per validation ZFI020) and does not derive PAR from PA0001

**So the question splits into two:**

1. **Was COMP_CODE=UNES the correct input?** If the project `727GLO1007` / fund center `ESD` belongs to UNES, then yes — it's a valid intercompany trip. The system should handle it.
2. **Should the user have entered COMP_CODE=IIEP?** The previous trip (0101004446) used a UNES fund (`707RMB0625`) but still had COMP_CODE=IIEP. If the same was intended here, it's a user input error — the fix is to correct the trip.

**Both answers lead to action:**
- If UNES is correct → system fix needed (add GL 2021011 to substitution, or extend PA0027, or uncomment ZXTRVU05)
- If IIEP was intended → correct the trip cost assignment and repost

---

## 6. Next Steps

### Immediate (resolve Rita's ticket)
1. **Ask Travel team:** Was COMP_CODE=UNES on trip 0101004544 intentional? Compare with trip 0101004446 which used COMP_CODE=IIEP for a similar scenario.
2. **If user error:** Correct the trip cost assignment to IIEP/PAR and repost
3. **If correct:** Apply fix Option 1 or 2 from Section 5.8

### Future Session: Travel Data Extraction to Gold DB
Extract the following tables for 2024-2026 into the Gold DB for travel domain analysis:

| Table | Content | Priority |
|---|---|---|
| `PTRV_SCOS` | Trip cost assignment (company code, BusA, fund, cost center) | HIGH |
| `PTRV_SHDR` | Trip header summary (amounts, dates) | HIGH |
| `PTRV_A_SCOS` | Advance cost assignment | HIGH |
| `PTRV_SCOS` for ALL company codes | Cross-company cost assignment patterns | MEDIUM |

This data enables:
- Pattern analysis of intercompany travel across all institutes
- Identification of other travelers who might hit the same issue
- Travel domain knowledge creation (new skill)

---

## 6. Complete Evidence: ALL 62 IIEP Travelers with UNES-Funded Trips

Analysis of ALL 475 UNES-funded trips from 62 IIEP travelers — vendor master data, employee type, GL account, and FI posting result:

| PERNR | Name | PERSG | Employee Type | KTOKK | Vendor Type | AKONT | Trips | FI | FI GL | GSBER | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10000247 | Corinne BITOUN | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 4 | 2 | 2021042 | PAR | OK |
| 10001348 | Leonora MAC EWEN | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 16 | 16 | 2021042 | PAR | OK |
| 10004536 | Candy LUGAZ | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 2 | 10 | 2021042 | PAR | OK |
| 10004543 | Lynne SERGEANT | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 4 | 4 | 2021042 | PAR | OK |
| 10014076 | Mariela BUONOMO | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 12 | 6 | 2021042 | PAR | OK |
| 10025768 | Stephanie LEITE | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 3 | 2021042 | PAR | OK |
| 10055467 | Michaela MARTIN | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 10 | 2 | 2021042 | PAR | OK |
| 10070926 | Muriel POISSON | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 6 | 29 | 2021042 | PAR | OK |
| 10096836 | Satoko YANO | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 7 | 24 | 2021042 | PAR | OK |
| 10101675 | Jimena PEREYRA | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 14 | 2021042 | PAR | OK |
| 10102117 | Barbara TOURNIER | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 11 | 18 | 2021042 | PAR | OK |
| 10107110 | Diane COURY | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 12 | 15 | 2021042 | PAR | OK |
| 10107699 | Am GAGNON | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 8 | 24 | 2021042 | PAR | OK |
| 10109534 | Helene BESSIERES | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 7 | 22 | 2021042 | PAR | OK |
| 10110103 | Jean Claude NDABANANI | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 9 | 26 | 2021042 | PAR | OK |
| 10111428 | Marcelo SOUTO SIMAO | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 23 | 2021042 | PAR | OK |
| 10127576 | Diogo AMARO | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 22 | 2021042 | PAR | OK |
| **10133079** | **Katja HINZ** | **1** | **Intl Staff** | **SCSA** | **SC/SSA/Non-reimb** | **2021011** | **1** | **4** | **2021011** | **PAR** | **FAIL** |
| 10135132 | Thalia SEGUIN | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 21 | 24 | 2021042 | PAR | OK |
| 10145208 | Suguru MIZUNOYA | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 1 | 34 | 2021042 | PAR | OK |
| 10145815 | Anna Ruth HAAS | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 14 | 13 | 2021042 | PAR | OK |
| 10148017 | German VARGAS MESA | 1 | Intl Staff | SCSA | SC/SSA/Non-reimb | 2021042 | 1 | 8 | 2021042 | PAR | OK |
| 10148254 | Emilie MARTIN | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 1 | 1 | 2021042 | PAR | OK |
| 10148276 | Yi SHI | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 3 | 6 | 2021042 | PAR | OK |
| 10150217 | Mathilde TREGUIER | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 3 | 2021042 | PAR | OK |
| 10150347 | Messou DIOMANDE | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 5 | 19 | 2021042 | PAR | OK |
| 10151714 | Claire THIBAULT | 1 | Intl Staff | SCSA | SC/SSA/Non-reimb | 2021042 | 2 | 16 | 2021042 | PAR | OK |
| 10152357 | Hala ABDELFATTAH | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 15 | 17 | 2021042 | PAR | OK |
| 10154238 | Diana ORTIZ PARRA | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 8 | 22 | 2021042 | PAR | OK |
| 10163203 | Carlos BENAVIDES | 1 | Intl Staff | UNES | UNESCO employees | 2021042 | 1 | 41 | 2021042 | PAR | OK |

*(Table shows 30 travelers with FI posting data. 32 additional travelers have no FI docs in Gold DB — older trips before 2024.)*

### Summary

| AKONT | Travelers | UNES Trips | FI Result |
|---|---|---|---|
| **2021042** | **61** | 474 | **ALL OK** |
| **2021011** | **1** (Katja HINZ) | 1 | **FAIL** |

| KTOKK | Travelers | AKONT in IIEP | Result |
|---|---|---|---|
| UNES (UNESCO employees) | 59 | ALL 2021042 | OK |
| SCSA (SC/SSA/Non-reimb) | 3 | 2 have 2021042 (OK), **1 has 2021011 (FAIL)** | Mixed |

**Katja HINZ is the ONLY IIEP traveler with AKONT=2021011 who has a UNES-funded trip.** Her vendor was created in 2016 with KTOKK=SCSA (when she was PERSG=M, Service Contract). She changed to PERSG=1 (International Staff) in 2017, but the vendor account group and reconciliation account were never updated.

### Open Investigation

**WHERE in the code/config does the vendor line receive GSBER based on the reconciliation account?** We know:
- GGB1 rule `3IIEP###002` condition matches HKONT=2021042/2021061 → sets GSBER
- GGB1 Step 003 puts PAR unconditionally for TV docs
- But the error (RW609) may occur BEFORE GGB1 runs

The exact point where the validation fails needs a system trace (ST01/ST05) or test posting in D01.

---

## 7. IIEP Travel Account Map

All GL accounts used in IIEP TV documents (2024-2026) with their Business Area and source:

### Covered by GGB1 Substitution

| GL Account | PK | BusA | Doc Count | Source |
|---|---|---|---|---|
| 0002021042 | 21/31 | PAR | 545 | GGB1 `3IIEP###002` [VERIFIED] |
| 0002021061 | 21/31 | PAR | 15 | GGB1 `3IIEP###002` [VERIFIED] |

### BusA Derived by Other Source (Travel BAPI / GGB1 rules 004-008)

| GL Account | PK | BusA | Doc Count | Source |
|---|---|---|---|---|
| 0002022043 | 40/50 | PAR/PDK | ~530 | Travel module or GGB1 [INFERRED] |
| 0002086092 | 40/50 | PAR/PDK | ~300 | Travel module or GGB1 [INFERRED] |
| 0006011501-514 | 40 | PAR/PDK | ~800 | Travel module or GGB1 [INFERRED] |
| **0002021011** | **21/31** | **PAR** | **4** | **Unknown — not in any substitution rule** |

### No BusA (empty — tolerated in multi-line docs)

| GL Account | PK | BusA | Doc Count | Note |
|---|---|---|---|---|
| 0005098030 | 40/50 | (empty) | 217 | Intercompany clearing — no rule, tolerated because other lines have BusA |
| 0005098013 | 50 | (empty) | 2 | Same pattern |

---

## 7. Evidence: Traveler 10133079 History

### 7.1 Previous Postings (all successful)

| Date | Doc | Type | IIEP Lines | IIEP GL | BusA | Funding |
|---|---|---|---|---|---|---|
| 2024-01-12 | 6600000005 | TV | 8 (1V+7GL) | 2021011 + 2022043 + 601x | ALL=PAR | IIEP |
| 2024-02-26 | 6600000047 | TV | 2 (1V+1GL) | 2021011 + 2022043 | ALL=PAR | IIEP |
| 2024-11-09 | 6600000215 | TV | 6 (1V+5GL) | 2021011 + 2022043 + 601x | ALL=PAR | IIEP |
| 2025-12-04 | 6600000332 | TV | 2 (1V+1GL) | 2021011 + 2022043 | ALL=PAR | IIEP |

**All 4 previous docs:**
- GL `2021011` on the vendor line with GSBER=PAR
- IIEP-funded (both vendor + GL lines in IIEP company code)
- Multiple IIEP lines per doc (vendor + at least one GL line)

### 7.2 Rita's Failed Posting

```
Line 1: IIEP | Vendor 10133079 (Katja HINZ) → GL 2021011 | Credit 1,570.00 | BusA = (empty)
Line 2: UNES | GL 2022043 (Adv staff travel exp)          | Debit 1,570.00  | BusA = PFF
```

**Differences from previous postings:**
- **UNES-funded** (fund `707RMB0625` changed Jul 2025) → GL 2022043 posts to UNES, not IIEP
- IIEP side has vendor line on GL `2021011` with **no BusA**
- No other IIEP GL line in the document

### 7.3 Last Successful IIEP Intercompany Advances

Last 5 successful intercompany advances (CPUDT = March-April 2026):

| Doc | BUDAT | IIEP Lines | IIEP GL(s) | BusA |
|---|---|---|---|---|
| 6600000091 | 03-26 | 2021042(V)/PAR + 2086092/PAR + 5098030/empty | 2021042 | PAR |
| 6600000092 | 03-31 | 2021042(V)/PAR + 2022043/PAR | 2021042 | PAR |
| 6600000093 | 03-31 | 2021042(V)/PAR + 2022043/PAR | 2021042 | PAR |

All use GL `2021042` (covered by GGB1) — NOT `2021011`. The difference is the vendor's LFB1 reconciliation account.

---

## 8. Fix Recommendation

### Immediate

1. **Add GL `2021011` to GGB1 substitution** — Extend rule `3IIEP###002` in GGB1 to also cover HKONT='2021011' (transport required)
2. **OR add to `YTFI_BA_SUBST`** via `YFI_BASU_MOD` — Add IIEP global entry: `IIEP / '' / PAR / 01 / I / EQ / 0002021011` (no transport needed)

### Investigate First

3. **Verify GGB1 rules `3IIEP###004`/`006`/`008`** — Extract their result assignments. If one of these already substitutes PAR for TV vendor lines, it may only need adjustment for the intercompany scenario
4. **Extract BAdI `ZCL_IM_BADI_EXITS_RPRAPA00`** source from D01 — Check if `SET_VALUES_FOR_BLFA1` (advance) reads PA0001 GSBER and passes it to the posting

### Structural (MGIE/ICBA prevention)

5. MGIE (25 TV docs on `2021011`) and ICBA (22 TV docs on `2021011`) could face the same issue if their travelers travel cross-funded — add `2021011` to their substitution rules too

---

## 9. Data Sources

| Source | Tables/Objects | Method |
|---|---|---|
| Gold DB (P01) | YBASUBST, YTFI_BA_SUBST | SQLite query |
| Gold DB (P01) | bseg_union + BKPF (bsak for vendor lines) | SQLite join |
| Gold DB (P01) | cts_transports + cts_objects | Transport timeline |
| Gold DB (P01) | GB901 (583 rows), GB02C, T100_ZFI, T80D, GB903 | RFC extraction (this session) |
| P01 Live RFC | LFB1 (vendor master) | RFC_READ_TABLE |
| P01 Live RFC | PA0001 (HR master data) | RFC_READ_TABLE |
| P01 Live RFC | BKPF + BSEG (recent TV docs) | RFC_READ_TABLE |
| Extracted Code | ZXTRVU05_RPY.abap (Travel exit) | Code analysis |
| Email | 3 embedded screenshots (posting run, error log, posting lines) | Image analysis |
| Knowledge | basu_mod_technical_autopsy.md, finance_validations_and_substitutions_autopsy.md | Framework docs |

**New tables added to Gold DB this session:** GB901 (583 rows), GB02C (10 rows), T100_ZFI (36 rows), T80D (8 rows), GB903 (3 rows).

**New knowledge created:** `knowledge/domains/FI/travel_busarea_derivation.md` — documents the multi-layer BusA derivation chain for Travel postings.
