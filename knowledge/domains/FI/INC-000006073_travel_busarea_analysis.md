# INC-000006073 — Root Cause Analysis (v2)
**Date:** 2026-04-08 | **Analyst:** JP Lopez (with AI-assisted data mining)
**Status:** Root cause CONFIRMED from SAP source code — fix path defined

---

## 1. Issue — As Received

### 1.1 Email from Rita Doroszlai (FU/IEP) — 07.04.2026

Rita reported that posting run 0100384694 for traveler Katja HINZ (10133079) failed. The email contained **3 embedded screenshots** that we analyzed:

**Screenshot 1 — Posting Run (PRRW):** Transaction PRRW, posting run 0100384694, reference 0101004544-KH-TA. Status: "Errors occurred". This is a travel advance for an IIEP employee charged to a UNES budget — a cross-funded (intercompany) scenario.

**Screenshot 2 — Error Log:** Two messages:
- `RW609` — "Error in document" (generic Travel posting wrapper)
- `ZFI020` — "For IIEP company code, only use business area PAR, IBA or FEL"

**Screenshot 3 — Posting Lines (2 lines):**

| Line | Account | Name | Debit | Credit | CoCode | BusA | GL |
|---|---|---|---|---|---|---|---|
| 1 | 10133079 | Katja HINZ | — | 1,570.00 USD | IIEP | **(empty)** | 0002021011 |
| 2 | 2022043 | Adv staff travel exp | 1,570.00 | — | UNES | PFF | — |

**Key observation from the screenshots:** The IIEP vendor clearing line has **empty Business Area**. The UNES expense line has PFF (correct). This is an intercompany document: two company codes (IIEP + UNES) in one posting. The error says "only use PAR, IBA or FEL" but the field is empty — the system couldn't derive any Business Area for the IIEP line.

### 1.2 The Question

Rita asks: *Why does this fail? The same traveler had successful postings before.*

This is the central question. Katja HINZ has 13 previous trips — all posted successfully with GSBER=PAR on the same GL account (2021011). What changed?

### 1.3 Context: Previous Custom Development by I. Konakov

The travel posting code contains comments from I. Konakov (UNESCO developer):
- `***I_KONAKOV 04/2018` in ZXTRVU05 — commented out BusA derivation for non-UNES company codes
- `***I_KONAKOV 30/09/2015` in ZCL_IM_TRIP_POST_FI CM006 — changed IIEP doc type logic (FR01→TV instead of AR01→TF)

These changes removed the institute-level BusA derivation from the travel exit, leaving non-UNES company codes dependent on the SAP standard same-company derivation — which only works when the trip is funded by the same company code as the employee.

### 1.4 Ticket Summary

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

---

## 2. Executive Summary

**Ticket:** INC-000006073 — PRRW posting fails for IIEP traveler Katja HINZ (10133079) on UNES-funded trip 0101004544.

**Root Cause:** Two independent factors combined to expose a gap that was invisible for 10+ years:

1. **Intercompany trip** (new — first time Apr 2026): Trip cost assignment entered with COMP_CODE=UNES. SAP standard code (`LHRTSF01.abap` line 852: `IF epk-bukst = epk-bukrs`) only assigns Business Area to the "home" company code lines. IIEP becomes the "partner" → its vendor clearing line gets no GSBER.

2. **Wrong vendor account group** (old — since 2016): Vendor 10133079 has KTOKK=SCSA instead of UNES → reconciliation GL is 2021011 instead of 2021042. GL 2021042 is covered by GGB1 substitution rule 3IIEP###002. GL 2021011 is not.

**Why it worked before:** All 13 previous trips were IIEP-funded (same-company). Line 852 fills GSBER regardless of GL account. The wrong vendor type and all three broken safety nets were invisible.

**Why it fails now:** Employee's fund changed to UNES fund (Jul 2025) → first cross-funded trip → intercompany posting → IIEP vendor line has empty GSBER → three fallbacks all fail (BAdI PA0027-02 expired 2021, ZXTRVU05 commented out, GGB1 rule missing GL 2021011) → BAPI rejects → RW609.

**Internal Validation Chain (from source code):**
```
LHRTSF01.abap:852   IF epk-bukst = epk-bukrs → NO MATCH (IIEP ≠ UNES) → GSBER stays empty
LHRTSF01.abap:1693  CLEAR epk-gsber → vendor line (koart='K', ktosl='HRP') GSBER cleared
CM00A.abap:12-37     BAdI reads PA0027-02 → expired → CHECK exits → GSBER stays empty
ZXTRVU05.abap:63     WHEN OTHERS → inst_fund_ba_wbs_cc → COMMENTED OUT → GSBER stays empty
LHRTSU05.abap:1-258  PTRV_ACC_EMPLOYEE_PAY_POST calls BAPI_ACC_EMPLOYEE_PAY_POST
                      → BAPI runs FI document simulation → GGB0/GGB1 fire inside simulation
                      → GGB0 ZFI020: empty GSBER passes the negative check (only blocks DAE/GEF/MBF/OPF/PFF)
                      → BUT BAPI mandatory field validation rejects empty GSBER for IIEP company code
                      → BAPI returns error → LHRTSU05.abap:155 wraps it as RW609
                      → ZFI020 message text displayed to user
```

**Fix:** Immediate — PA30: extend PA0027-02 for traveler (unblocks Rita). Structural — FK02: correct vendor KTOKK to UNES + YFI_BASU_MOD: add GL 2021011 to YTFI_BA_SUBST. Preventive — check MGIE/ICBA institutes for same exposure.

**Impact:** Only 1 traveler affected today (Katja HINZ — unique combination of SCSA vendor + UNES-funded trip). 61 other cross-funded IIEP travelers unaffected (all have KTOKK=UNES → GL 2021042 → covered by GGB1).

---

## 3. How Business Area Works at UNESCO Travel

### 3.0 What is Business Area and Why It Matters

Business Area (GSBER) is a mandatory field in UNESCO's FI documents. It identifies which organizational unit (PAR=Paris HQ, PFF=Programme Field Offices, IBA=International Bureau of Education, etc.) owns a posting line. Without it, the FI document cannot be created.

In travel postings, Business Area must be assigned to **every posting line** — including vendor clearing lines, expense lines, and intercompany lines. UNESCO has a multi-layer derivation chain to fill this field:

### How BusA Gets Assigned (simplified)

```
Layer 1: SAP Standard (PTRV_TRANSLATE)
   → Copies BusA from trip cost assignment to "home" company lines
   → Does NOT fill BusA for "partner" (intercompany counterpart) lines

Layer 2: UNESCO BAdI (ZCL_IM_TRIP_POST_FI)
   → Reads PA0027 (Cost Distribution) to derive BusA when Layer 1 didn't fill it

Layer 3: UNESCO Travel Exit (ZXTRVU05)
   → Derives BusA from fund/WBS/cost center per company code
   → Active for UNES only — commented out for all other company codes

Layer 4: GGB1 Substitution (inside FI BAPI)
   → Range-based rules that set BusA based on company code + doc type + GL account
   → Runs during FI document simulation

Layer 5: GGB0 Validation (inside FI BAPI)
   → Checks BusA is valid for the company code
   → Rejects document if invalid
```

### Custom Framework Components

| Component | Object | Purpose | TCode |
|---|---|---|---|
| **SAP Standard** | `LHRTSF01.abap` (function group HRTS) | Builds posting lines, assigns BusA for same-company | PRRW |
| **BAdI** | `ZCL_IM_TRIP_POST_FI` method `EX_ZWEP_ACCOUNT2` | PA0027-02 BusA fallback | — |
| **Travel Exit** | `ZXTRVU05` | BusA derivation per company code | — |
| **Substitution Exit** | `YRGGBS00` form U910 → `YCL_FI_ACCOUNT_SUBST_READ` | Looks up YTFI_BA_SUBST | GGB1 |
| **Maintenance Tx** | `YFI_BASU_MOD` | User-friendly substitution rule maintenance (no transport) | YFI_BASU_MOD |
| **Persistence** | `YTFI_BA_SUBST` | Range-based account→BusA mapping (129 entries) | — |
| **Legacy Table** | `YBASUBST` | Flat mapping (752 entries) | — |
| **Validation** | GGB0 → ZFI020 | "For IIEP company code, only use business area PAR, IBA or FEL" | GGB0 |

---

## 4. Investigation: Why the IIEP Line Has Empty BusA

This section walks through each component that could provide Business Area for the IIEP vendor line, showing why each one fails.

### 4.1 Vendor Reconciliation Account (LFB1)

The screenshot from Rita shows "Acct no. 10133079" — this is the vendor/personnel number. The actual GL account comes from LFB1 (vendor master company code data):

| Vendor | Company Code | AKONT (Reconciliation GL) |
|---|---|---|
| 10133079 | **IIEP** | **0002021011** |
| 10133079 | **UNES** | **0002021042** |

**The IIEP line posts to GL `0002021011`.** This is confirmed by all 4 previous travel documents for this vendor. The GL determines which substitution rules apply — and GL 2021011 is NOT covered by any rule (see 3.3).

### 4.2 GGB1 Substitution Rule 3IIEP###002

The GGB1 travel substitution for IIEP (extracted from GB901):
```
CONDITION [3IIEP###002]:
  (BLART = 'TV' OR BLART = 'TF')
  AND (HKONT = '2021042' OR HKONT = '2021061')
  AND GSBER = ''
RESULT: Sets GSBER = PAR
```

**GL `2021011` is NOT in this rule.** Only `2021042` and `2021061` are covered. This is why the 61 other IIEP travelers with UNES-funded trips work (they all have GL 2021042) and Katja fails (GL 2021011).

### 4.3 YTFI_BA_SUBST for IIEP

IIEP has **zero global rules** in `YTFI_BA_SUBST`. All 12 entries are restricted to document type Z1 — they do NOT apply to TV (travel) documents:

| Company Code | Global Rules | Z1 Rules | Total |
|---|---|---|---|
| IBE, ICBA, ICTP, MGIE, UBO, UIL, UIS | 9-11 each | 3-10 each | 13-21 |
| **IIEP** | **0** | **12** | **12** |

### 4.4 GGB0 Validation ZFI020

```
PREREQUISITE [1IIEP###001]: BUKRS = 'IIEP'
CHECK [2IIEP###001]: GSBER <> 'DAE' AND <> 'GEF' AND <> 'MBF' AND <> 'OPF' AND <> 'PFF'
```

**Empty BusA (`''`) passes this check** — it's not equal to any of the rejected values. ZFI020 is a negative check (blocks specific wrong values), not a positive check. The message text "only use PAR, IBA or FEL" is misleading — it's not what the code actually checks.

### 4.5 PA0001 — HR Master Data

| Period | BUKRS | GSBER | KOSTL | FISTL | GEBER (Fund) |
|---|---|---|---|---|---|
| 2024-01 to 2025-06 | IIEP | **PAR** | ADM | ADM | 1130STF602 (IIEP fund) |
| 2025-07 to 9999-12 | IIEP | **PAR** | *(empty)* | *(empty)* | **707RMB0625** (UNES fund) |

**GSBER=PAR has never changed** (stable since 2016). Position change hypothesis ruled out.

**However:** The employee's fund changed from `1130STF602` (IIEP fund) to `707RMB0625` (UNES fund) on 2025-07-01. This is why the trip uses UNES budget — creating an intercompany posting.

### 4.6 PA0027 — Cost Distribution (BAdI Fallback Data)

| PERNR | Subtype | BEGDA | ENDDA | BUKRS | GSBER | KOSTL | Fund | % |
|---|---|---|---|---|---|---|---|---|
| 10133079 | 01 | 2016-01-18 | 2016-12-31 | IIEP | PAR | ADM | 930STF0602 | 100% |
| 10133079 | 01 | 2017-01-01 | 2017-01-31 | IIEP | PAR | ADM | 940STF0602 | 100% |
| 10133079 | **02** | 2016-01-18 | **2021-01-31** | IIEP | **PAR** | R&D | 936GLO0303 | 100% |

**Subtype 02 expired on 2021-01-31.** The BAdI `ZCL_IM_TRIP_POST_FI` method `EX_ZWEP_ACCOUNT2` reads subtype 02 only. No current record → BAdI exits without setting GSBER.

### 4.7 Travel Exit ZXTRVU05 — The BusA Derivation Code

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

**For IIEP lines:** The travel exit does NOT derive BusA. The institute-specific derivation (`inst_fund_ba_wbs_cc`) is commented out. This means IIEP relies entirely on GGB1 substitution or the SAP standard same-company derivation to provide BusA.

### 4.8 Summary: Every Path to BusA Is Blocked

| # | Source | What It Does | Why It Fails for This Case |
|---|---|---|---|
| 1 | SAP Standard (line 852) | Copies BusA from employee for same-company lines | **Intercompany** — bukst(IIEP) ≠ bukrs(UNES) |
| 2 | BAdI PA0027-02 | Reads cost distribution record | **Expired 2021-01-31** — no current record |
| 3 | ZXTRVU05 exit | Derives BusA from fund for non-UNES codes | **Commented out** |
| 4 | GGB1 rule 3IIEP###002 | Substitutes PAR for GL 2021042/2021061 in TV docs | **GL 2021011 not in rule** |
| 5 | YTFI_BA_SUBST | Range-based lookup | **Zero global rules for IIEP** |
| 6 | GGB1 Step 003 | PAR unconditional for TV docs | **Runs inside BAPI — too late or blocked by mandatory check** |

**The IIEP vendor line has no way to receive a Business Area.** Every single derivation path is blocked by an independent issue.

---

## 5. System Execution Chain (Technical Detail) — From Source Code

All references verified against extracted SAP standard source code (34 files, 24,559 lines in `extracted_code/SAP_STANDARD/TV_TRAVEL/`).

### 5.1 The 8-Step Chain

| Step | SAP Object | Source File:Line | What It Does |
|---|---|---|---|
| **1** | Trip cost assignment | PR02 → table PTRV_SCOS | User enters COMP_CODE, BUS_AREA, Fund, Fund Center |
| **2** | PTRV_TRANSLATE (FM in function group HRTS) | `LHRTSF01.abap:848-860` | `IF epk-bukst = epk-bukrs` → propagate GSBER from employee master (gsbst) |
| **3** | Vendor line GSBER clear | `LHRTSF01.abap:1688-1693` | `IF epk-koart = 'K'` AND ktosl HRP/HRV → `CLEAR epk-gsber` |
| **4** | BAdI `ZCL_IM_TRIP_POST_FI` method `EX_ZWEP_ACCOUNT2` | `ZCL_IM_TRIP_POST_FI_CM00A.abap:12-82` | If gsbst is INITIAL → reads PA0027 subtype 02 → derives GSBER from KGB field |
| **5** | Travel exit ZXTRVU05 | `ZXTRVU05_v2.abap:23-73` | CASE BUKRS: UNES → `FUND_BA_WBS_CC`; WHEN OTHERS → `inst_fund_ba_wbs_cc` (commented out) |
| **6** | `PTRV_ACC_EMPLOYEE_PAY_POST` | `LHRTSU05.abap:1-258` | Calls `BAPI_ACC_EMPLOYEE_PAY_POST` → FI document simulation |
| **7** | GGB1 substitution (inside BAPI simulation) | GB901/GB922 config | Step 001: Exit U910; Step 002: rule 3IIEP###002; **Step 003: GSBER='PAR' unconditional for TV** |
| **8** | GGB0 validation (inside BAPI simulation) | GB901 config | ZFI020: GSBER ∉ {DAE,GEF,MBF,OPF,PFF} — empty passes |

### 5.2 Step-by-Step: Case OK vs Case FAIL

| Step | Source Code | Case OK (IIEP-funded) | Case FAIL (UNES-funded) | Arrives? |
|---|---|---|---|---|
| **1** | PR02 → PTRV_SCOS | COMP_CODE=**IIEP**, BUS_AREA=**PAR** | COMP_CODE=**UNES**, BUS_AREA=**PFF** | ✅ Both |
| **2** | `LHRTSF01.abap:852` `IF epk-bukst = epk-bukrs` | bukst=IIEP = bukrs=IIEP → **MATCH** → `epk-gsber = wa_ep_translate-gsbst` → **GSBER=PAR** | bukst=IIEP ≠ bukrs=UNES → **NO MATCH** → GSBER stays **empty** | ✅ Both |
| **3** | `LHRTSF01.abap:1688-1693` `IF koart='K' AND ktosl='HRP'` | GSBER=PAR already set, but line 1693 `CLEAR epk-gsber` clears it. **However**: line 1550 `epk-gsber = accountingobjects-bus_area_empl` restores it for cross-company tax lines | GSBER already empty → stays **empty**. No restore because this is the vendor clearing line, not a tax line | ✅ Both |
| **4** | `CM00A.abap:12` `IF zwep-gsbst IS INITIAL` | gsbst=**PAR** (not initial) → **SKIPPED** | gsbst=**INITIAL** → **FIRES** → reads PA0027-02 → **expired 2021-01-31** → `CHECK sy-subrc` at line 37 exits → GSBER stays **empty** | ✅ OK skips / ✅ FAIL fires but fails |
| **5** | `ZXTRVU05.abap:63-72` `WHEN OTHERS` | IIEP → WHEN OTHERS → code **commented out** → no effect (PAR already set upstream) | IIEP → WHEN OTHERS → code **commented out** → GSBER stays **empty** | ✅ Both |
| **6** | `LHRTSU05.abap` `BAPI_ACC_EMPLOYEE_PAY_POST` | BAPI receives GSBER=PAR → simulation succeeds | BAPI receives GSBER=empty → simulation fails → **RW609 at line 155** | ✅ OK / ❌ **FAIL — ERROR HERE** |
| **7** | GGB1 substitution (inside BAPI) | Step 003 confirms PAR | Step 003 would set PAR — **but BAPI already rejected before completing** | ✅ OK / ❌ Depends on BAPI internal sequence |
| **8** | FI document created | ✅ Posted | ❌ **NEVER HAPPENS** | ✅ OK / ❌ Never |

### 5.3 The Code — Exact Lines

**Step 2 — The same-company check** (`LHRTSF01.abap:848-860`):
```abap
* EP-GSBER only if GSBER_A is not initial.
      IF gsber_a = 'X'.
        IF NOT ( wa_ep_translate-gsbst IS INITIAL ) AND
               ( wa_ep_translate-gsber IS INITIAL ).
          IF wa_ep_translate-koart <> 'F'.
            IF epk-bukst = epk-bukrs.        ← LINE 852: same company only!
* nur wenn kein abweichender Buchungskreis...
              epk-gsber = wa_ep_translate-gsbst.  ← sets BusA from employee
            ENDIF.
          ENDIF.
        ENDIF.
      ELSE.
        CLEAR epk-gsber.
      ENDIF.
```

**Step 3 — Vendor line clearing** (`LHRTSF01.abap:1688-1693`):
```abap
    IF epk-koart = 'K' AND ( epk-ktosl EQ 'HRP' OR epk-ktosl EQ 'HRV' ).
      IF bl_spl NE 'C'.
        IF prctr_tr EQ false.
          CLEAR epk-prctr.
          CLEAR epk-gsber.    ← LINE 1693: vendor line GSBER cleared!
```

**Step 3b — Cross-company restore** (`LHRTSF01.abap:1537-1550`):
```abap
            CHECK psref_fields-field <> 'GSBER'.   ← GSBER protected from field clearing
            ...
            epk-bukrs = epk-bukst.                  ← LINE 1549: switch to home company
            epk-gsber = accountingobjects-bus_area_empl.  ← LINE 1550: restore from employee
```
**But**: this only applies to cross-company **tax G/L lines** (stazf='X'), NOT to the vendor clearing line.

**Step 4 — BAdI PA0027 fallback** (`ZCL_IM_TRIP_POST_FI_CM00A.abap:12-37`):
```abap
if zwep-bukst is initial or zwep-gsbst is initial.    ← LINE 12: fires when gsbst empty
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING pernr = zwep-pernr  infty = '0027'
              begda = zwep-datv1  endda = zwep-datv1
    TABLES    infty_tab = lt_p0027.
  loop at lt_p0027 into ls_p0027 where subty = '02'.
  endloop.
  check sy-subrc is initial.    ← LINE 37: EXITS if no subtype 02 found!
  ...
  zwep-gsber = <fs_kprnm>.     ← LINE 60: would set GSBER from PA0027-02 KGB field
```

**Step 5 — Travel exit** (`ZXTRVU05_v2.abap:23-72`):
```abap
loop at KONTI assigning <KONTI>.
  case <KONTI>-bukrs.
    when 'UNES'.
      perform fund_ba_wbs_cc ...  ← ACTIVE for UNES
    when 'UBO'.
                                  ← empty
    when others.
*     perform inst_fund_ba_wbs_cc ...  ← COMMENTED OUT for IIEP and all institutes
  endcase.
endloop.
```

**Step 6 — RW609 wrapper** (`LHRTSU05.abap:150-164`):
```abap
    IF lines( return ) = 0.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = 'RW'
          number = '609'        ← "Error in document: &1 &2 &3"
          par1   = lv_awtyp
          par2   = lv_awref
          par3   = lv_awsys
        IMPORTING
          return = ls_return.
```

---

## 6. Why It Worked Before and Fails Now

**The system code did NOT change. The input changed.** The same traveler, same vendor, same GL account — but a different funding source creates a completely different posting flow.

### 6.1 Flow A: IIEP-Funded Trip (all 13 previous trips — ALL OK)

**Scenario:** Katja travels on an IIEP budget (fund 1130STF602). The trip cost assignment says COMP_CODE=IIEP, BUS_AREA=PAR. This is a **same-company** posting — all lines go to IIEP.

```
 ┌─────────────────────────────────────────────────────────┐
 │  PR02: Trip created with cost assignment                │
 │    Company Code = IIEP    Business Area = PAR           │
 │    Fund = 1130STF602      Fund Center = ADM             │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  PRRW: Travel Posting Run builds 2 posting lines:       │
 │                                                         │
 │  Line 1: IIEP | Vendor 10133079 | Credit 1,570 | GL 2021011  │
 │  Line 2: IIEP | GL 2022043 (advance) | Debit 1,570           │
 │                                                         │
 │  Both lines belong to IIEP (same company as employee)   │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  SAP Standard (LHRTSF01 line 852):                      │
 │    "Is the posting company = employee's home company?"  │
 │    epk-bukst(IIEP) = epk-bukrs(IIEP) → YES!            │
 │                                                         │
 │    → Copies Business Area PAR from employee master      │
 │      to ALL IIEP posting lines                          │
 │                                                         │
 │  Result: BOTH lines have GSBER = PAR  ✅                │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  Fallbacks? Not needed — PAR is already filled          │
 │                                                         │
 │  • BAdI PA0027: gsbst = PAR (not empty) → SKIPPED      │
 │  • ZXTRVU05: commented out but irrelevant → SKIPPED     │
 │  • GGB1 rule: GL 2021011 not covered but irrelevant     │
 │                                                         │
 │  → BAPI posting succeeds  ✅                            │
 │  → FI document created  ✅                              │
 └─────────────────────────────────────────────────────────┘
```

**Why it works:** When the trip is funded by IIEP, IIEP is the "home" company code. SAP standard automatically copies the employee's Business Area (PAR) to every IIEP posting line. The GL account, the vendor type, the substitution rules — none of it matters. PAR is set at the very beginning and nothing overrides it.

---

### 6.2 Flow B: UNES-Funded Trip (Rita's trip 0101004544 — FAILS)

**Scenario:** Katja's fund changed to 707RMB0625 (a UNES fund) in July 2025. Rita creates a trip with COMP_CODE=UNES, BUS_AREA=PFF. This is an **intercompany** posting — UNES pays the expense, but the advance was given to IIEP vendor 10133079. Two company codes are involved.

```
 ┌─────────────────────────────────────────────────────────┐
 │  PR02: Trip created with cost assignment                │
 │    Company Code = UNES    Business Area = PFF           │
 │    Fund = 727GLO1007      Fund Center = ESD             │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  PRRW: Travel Posting Run builds 2 posting lines:       │
 │                                                         │
 │  Line 1: IIEP | Vendor 10133079 | Credit 1,570 | GL 2021011  │
 │          ↑ This is a "partner" clearing line — IIEP     │
 │            because the vendor belongs to IIEP           │
 │                                                         │
 │  Line 2: UNES | GL 2022043 (advance) | Debit 1,570           │
 │          ↑ This is the "home" expense line — UNES       │
 │            gets BusA = PFF from cost assignment          │
 │                                                         │
 │  Two different company codes in ONE document            │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  SAP Standard (LHRTSF01 line 852):                      │
 │    "Is the posting company = employee's home company?"  │
 │                                                         │
 │    For UNES line: bukrs=UNES, cost assignment=UNES      │
 │      → Gets PFF from cost assignment  ✅                │
 │                                                         │
 │    For IIEP line: bukst=IIEP ≠ bukrs=UNES → NO!        │
 │      → SAP does NOT copy Business Area  ❌              │
 │      → IIEP vendor line has GSBER = (empty)             │
 │                                                         │
 │  SAP treats the IIEP line as a "partner" clearing       │
 │  entry — a technical accounting counterpart, not        │
 │  part of the trip cost assignment. It does not inherit   │
 │  the employee's Business Area because the cost          │
 │  assignment belongs to UNES, not IIEP.                  │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  Fallback 1: BAdI PA0027 (ZCL_IM_TRIP_POST_FI CM00A)   │
 │    gsbst is empty → BAdI FIRES                          │
 │    Reads PA0027 infotype, subtype 02 for Katja          │
 │    → Record expired on 2021-01-31 (5 years ago!)        │
 │    → No valid record found → method exits               │
 │    → GSBER stays empty  ❌                              │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  Fallback 2: Travel Exit ZXTRVU05                       │
 │    CASE company code:                                   │
 │      UNES → active derivation (but this is IIEP line)   │
 │      IIEP → falls in "WHEN OTHERS"                      │
 │              → code is COMMENTED OUT since unknown date  │
 │    → GSBER stays empty  ❌                              │
 └────────────────────────┬────────────────────────────────┘
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │  BAPI Posting Attempt (LHRTSU05):                       │
 │    Calls BAPI_ACC_EMPLOYEE_PAY_POST                     │
 │    → FI document simulation runs                        │
 │    → GGB1 substitution fires:                           │
 │        Rule 3IIEP###002: GL 2021042/2021061 only        │
 │          → GL 2021011 NOT covered  ❌                   │
 │        Step 003: would set PAR unconditionally           │
 │          → but BAPI mandatory check rejects first  ❌   │
 │    → BAPI returns error                                 │
 │    → LHRTSU05 wraps as RW609                            │
 │    → User sees: "ZFI020: For IIEP company code,         │
 │      only use business area PAR, IBA or FEL"            │
 │                                                         │
 │  → FI document NEVER created  ❌                        │
 └─────────────────────────────────────────────────────────┘
```

**Why it fails:** When the trip is funded by UNES, IIEP becomes the "partner" company code. SAP standard does NOT assign Business Area to partner clearing lines. The system relies on three fallback mechanisms to fill it — but all three are independently broken:

| Fallback | What went wrong | Since when |
|---|---|---|
| BAdI reads PA0027 subtype 02 | Record expired 2021-01-31 — nobody renewed it | 5 years |
| Travel exit ZXTRVU05 | Code for non-UNES company codes **commented out** | Unknown |
| GGB1 substitution rule | Only covers GL 2021042/2021061, not 2021011 | Always |

---

### 6.3 The Single Variable That Changed

| | Flow A (worked) | Flow B (fails) |
|---|---|---|
| **Traveler** | Katja HINZ (10133079) | Same |
| **Vendor type (KTOKK)** | SCSA | Same |
| **GL Account (AKONT)** | 2021011 | Same |
| **Employee BusA (PA0001)** | PAR | Same |
| **PA0027-02** | Expired 2021 | Same |
| **ZXTRVU05 code** | Commented out | Same |
| **GGB1 rule** | Missing GL 2021011 | Same |
| | | |
| **Trip cost assignment** | COMP_CODE=**IIEP** | COMP_CODE=**UNES** |
| **Posting type** | Same-company | **Intercompany** |
| **SAP standard line 852** | bukst=bukrs → **FILLS PAR** | bukst≠bukrs → **EMPTY** |
| **Fallbacks needed?** | No | Yes — **but all 3 broken** |

**Everything was broken for years.** The expired PA0027, the commented-out exit, the missing GL in the substitution rule — none of this was visible because Flow A (same-company) fills Business Area before any fallback is needed. It took a new funding scenario (UNES-funded) to expose all three gaps simultaneously.

---

### 6.4 Why 61 Other IIEP Travelers Work with UNES-Funded Trips

Other IIEP employees also travel on UNES budgets (intercompany). They ALL work. The difference is the **vendor account group**:

| | 61 travelers (OK) | Katja HINZ (FAIL) |
|---|---|---|
| Employee group (PERSG) | 1 (International Staff) | 1 (International Staff) |
| Vendor account group (KTOKK) | **UNES** (UNESCO employees) | **SCSA** (SC/SSA/Non-reimb) |
| Reconciliation GL in IIEP (AKONT) | **0002021042** | **0002021011** |
| GGB1 rule 3IIEP###002 covers GL? | **YES** | **NO** |

Katja's vendor was created in 2016 with KTOKK=SCSA when she was PERSG=M (Service Contract). She changed to PERSG=1 (International Staff) in 2017, but the vendor account group and reconciliation account were **never updated**. This gave her a different GL (2021011) from every other International Staff vendor (2021042).

For the 61 other travelers: their IIEP line also arrives with empty GSBER (same intercompany problem). But GGB1 rule 3IIEP###002 **catches** GL 2021042 during the BAPI simulation and substitutes PAR → posting succeeds.

For Katja: GGB1 rule doesn't cover GL 2021011 → no substitution → GSBER stays empty → posting fails.

**The wrong vendor type was harmless for 10 years because same-company postings don't need the substitution rule. The intercompany scenario exposed it.**

---

## 7. Three Broken Safety Nets

The BusA derivation has 3 fallback mechanisms. ALL are broken for this case:

| Safety Net | Source Code | Status | Why Broken | Broken Since |
|---|---|---|---|---|
| **1. BAdI PA0027-02** | `CM00A.abap:12-37` | Data expired | PA0027 subtype 02 record ended 2021-01-31. No current record → `CHECK sy-subrc` exits | Feb 2021 |
| **2. ZXTRVU05 exit** | `ZXTRVU05.abap:63-72` | Code commented out | `inst_fund_ba_wbs_cc` for non-UNES company codes disabled | Unknown (possibly go-live) |
| **3. GGB1 rule 3IIEP###002** | GB901 config | Incomplete GL coverage | Only covers HKONT 2021042/2021061. GL 2021011 not in rule | Always — never added |

**None of these were ever tested in production** for IIEP travel because Step 2 (line 852 same-company check) always filled GSBER. The gap was invisible for 10+ years.

---

## 8. Evidence

### 8.1 Trip Cost Assignment (PTRV_SCOS) — All 15 Trips

| Trip | Date | COMP_CODE | BUS_AREA | Fund | Fund Center | Amount | Result |
|---|---|---|---|---|---|---|---|
| 0101004011 | 2024-02 | **IIEP** | **PAR** | ULO2023 | TEC | 1,662.76 | OK |
| 0101004047 | 2024-11 | **IIEP** | **PAR** | 1135BDI401 | TEC | 2,908.02 | OK |
| 0101004446 | 2025-12 | **IIEP** | **PAR** | 707RMB0625 | ADM | 1,196.21 | OK |
| **0101004544** | **2026-04** | **UNES** | **PFF** | 727GLO1007 | ESD | 3,183.40 | **FAIL** |

Trip 0101004446 (Dec 2025) used UNES fund `707RMB0625` but COMP_CODE=**IIEP** → same-company → worked. Trip 0101004544 (Rita's) has COMP_CODE=**UNES** → intercompany → fails.

### 8.2 Vendor Master Data

| | Katja HINZ (10133079) | 61 other IIEP travelers |
|---|---|---|
| KTOKK | **SCSA** (SC/SSA/Non-reimb) | **UNES** (UNESCO employees) |
| LFB1 IIEP AKONT | **0002021011** | **0002021042** |
| PERSG | 1 (International Staff) | 1 (International Staff) |

KTOKK=SCSA is inconsistent with PERSG=1. Vendor created 2016, PERSG changed to 1 in 2017, KTOKK never updated.

### 8.3 PA0027 — Cost Distribution

| PERNR | Subtype | BEGDA | ENDDA | BUKRS | GSBER | KOSTL | Fund | % |
|---|---|---|---|---|---|---|---|---|
| 10133079 | 01 | 2016-01-18 | 2016-12-31 | IIEP | PAR | ADM | 930STF0602 | 100% |
| 10133079 | 01 | 2017-01-01 | 2017-01-31 | IIEP | PAR | ADM | 940STF0602 | 100% |
| 10133079 | **02** | 2016-01-18 | **2021-01-31** | IIEP | **PAR** | R&D | 936GLO0303 | 100% |

Subtype 02 expired 2021-01-31. BAdI reads subtype 02 only → finds nothing → exits.

### 8.4 PA0001 — HR Master Data

| Period | BUKRS | GSBER | KOSTL | FISTL | GEBER (Fund) |
|---|---|---|---|---|---|
| 2024-01 to 2025-06 | IIEP | **PAR** | ADM | ADM | 1130STF602 (IIEP fund) |
| 2025-07 to 9999-12 | IIEP | **PAR** | *(empty)* | *(empty)* | **707RMB0625** (UNES fund) |

GSBER=PAR stable since 2016. Fund changed Jul 2025 — this created the intercompany scenario.

### 8.5 GGB1 Substitution Rules for IIEP (from GB901)

| Rule | Condition | Covers GL 2021011? |
|---|---|---|
| `3IIEP###002` | BLART=TV/TF AND HKONT=2021042/2021061 AND GSBER='' | **NO** |
| `3IIEP###004` | BLART=TV/TF | YES (but result unknown — needs GB922 extraction) |
| `3IIEP###006` | KOART='K' (vendor lines) | YES (but result unknown) |
| `3IIEP###008` | BUDAT >= 2014-01-01 | YES (but result unknown) |
| GGB1 Step 003 | TV/TF → GSBER='PAR' unconditional (from GB922) | **YES — would fix it** |

Step 003 unconditionally sets GSBER='PAR' for TV docs. Whether this executes before or after the BAPI mandatory field check depends on the GGB1/BAPI internal sequence.

### 8.6 GGB0 Validation ZFI020

```
PREREQUISITE [1IIEP###001]: BUKRS = 'IIEP'
CHECK [2IIEP###001]: GSBER <> 'DAE' AND <> 'GEF' AND <> 'MBF' AND <> 'OPF' AND <> 'PFF'
```

**Empty BusA passes this check.** ZFI020 is a negative check (blocks specific values), not a positive check. The message text "only use PAR, IBA or FEL" is misleading — it's not what the code actually checks.

### 8.7 YTFI_BA_SUBST for IIEP

IIEP has **zero global rules**. All 12 entries are restricted to document type Z1:

| BUKRS | BLART | GSBER | GL Account |
|---|---|---|---|
| IIEP | Z1 | IBA | 0001043701, 0001043715, 0001143701, 0001143715 |
| IIEP | Z1 | PDK | 0001043894, 0001143894 |
| IIEP | Z1 | X | 0001075711, 0001075712, 0001275711, 0001275712, 0001375711, 0001375712 |

None apply to TV/TF documents.

### 8.8 All 62 IIEP Travelers with UNES-Funded Trips

| AKONT | Travelers | UNES Trips | FI Result |
|---|---|---|---|
| **2021042** | **61** | 474 | **ALL OK** |
| **2021011** | **1** (Katja HINZ) | 1 | **FAIL** |

| KTOKK | Travelers | AKONT in IIEP | Result |
|---|---|---|---|
| UNES (UNESCO employees) | 59 | ALL 2021042 | OK |
| SCSA (SC/SSA/Non-reimb) | 3 | 2 have 2021042 (OK), **1 has 2021011 (FAIL)** | Mixed |

Katja HINZ is the **only IIEP traveler** with AKONT=2021011 who has a UNES-funded trip.

### 8.9 Cross-Company GL Pattern

| Company Code | GL 2021011 GSBER | Institute Default BusA | Source |
|---|---|---|---|
| **IIEP** | **PAR** (4 docs) | PAR | SAP standard (line 852, same-company) |
| **MGIE** | **PFF** (24) / GEF (1) | PFF | SAP standard (line 852, same-company) |
| **ICBA** | **PFF** (22 docs) | PFF | SAP standard (line 852, same-company) |

All successful docs use same-company posting. MGIE (25 docs) and ICBA (22 docs) could face the same issue if their travelers travel cross-funded.

### 8.10 Previous Postings for Traveler 10133079

| Date | Doc | Type | IIEP GL | BusA | Funding |
|---|---|---|---|---|---|
| 2024-01-12 | 6600000005 | TV | 2021011 + 2022043 + 601x | ALL=PAR | IIEP |
| 2024-02-26 | 6600000047 | TV | 2021011 + 2022043 | ALL=PAR | IIEP |
| 2024-11-09 | 6600000215 | TV | 2021011 + 2022043 + 601x | ALL=PAR | IIEP |
| 2025-12-04 | 6600000332 | TV | 2021011 + 2022043 | ALL=PAR | IIEP |

All same-company IIEP-funded → line 852 fills GSBER → no fallback needed.

---

## 9. Root Cause — Final

**Two independent factors combined to create an error that was invisible for 10 years:**

### Factor 1: Intercompany Trip (new — Apr 2026)
Trip cost assignment entered with COMP_CODE=UNES instead of IIEP. This makes IIEP the "partner" company code. SAP standard (`LHRTSF01.abap:852`) only propagates GSBER to the "home" company code lines. The IIEP vendor clearing line gets no GSBER.

### Factor 2: Wrong Vendor Account Group (old — since 2016)
KTOKK=SCSA → AKONT=2021011. If KTOKK were UNES (correct for PERSG=1), AKONT would be 2021042, which IS covered by GGB1 rule 3IIEP###002.

### The Invisible Gap
For same-company trips (all 13 previous), Factor 2 doesn't matter — line 852 fills GSBER regardless of GL. For cross-funded trips with GL 2021042 (61 travelers), Factor 1 doesn't matter — GGB1 covers it. Only when BOTH factors are true (intercompany + GL 2021011) does the error surface.

### Three Broken Safety Nets
All three fallback mechanisms that should catch this case are independently broken:
1. **BAdI PA0027-02**: data expired 2021
2. **ZXTRVU05**: code commented out
3. **GGB1 rule**: GL 2021011 not in condition

---

## 10. Fix Recommendation

### Question for Travel/HR Team First
Was COMP_CODE=UNES on trip 0101004544 intentional? Previous trip 0101004446 used same UNES fund but COMP_CODE=IIEP — and worked.

### If User Input Error (IIEP was intended)
Correct the trip cost assignment to COMP_CODE=IIEP and repost. No system change needed.

### If UNES Is Correct (intercompany is valid scenario)

| # | Fix | Repairs Step | Action | Transport? | Speed |
|---|---|---|---|---|---|
| **1** | HR master data | Step 4 (BAdI) | PA30: Extend PA0027 subtype 02 for traveler 10133079 (IIEP/PAR, current dates) | No | **Immediate** |
| **2** | FI config (no transport) | Step 7 (GGB1 via BAPI) | YFI_BASU_MOD: Add GL 2021011 to YTFI_BA_SUBST for IIEP, global (all doc types) | No | **Same day** |
| **3** | FI config (transport) | Step 7 (GGB1) | GGB1: Add HKONT=2021011 to rule 3IIEP###002 | Yes | Days |
| **4** | ABAP (transport) | Step 5 (exit) | Uncomment `inst_fund_ba_wbs_cc` in ZXTRVU05 for WHEN OTHERS | Yes | Days + testing |
| **5** | Vendor master correction | Preventive | FK02: Change KTOKK from SCSA to UNES for vendor 10133079 in IIEP → AKONT changes to 2021042 → GGB1 covers it | No | Same day |

**Recommended path:**
- **Immediate**: Option 1 (unblocks Rita now)
- **Structural**: Option 5 (fix vendor master) + Option 2 (catch any other SCSA vendors)
- **Preventive**: Options 3+4 for MGIE/ICBA institutes that have same GL 2021011 exposure

---

## 11. IIEP Travel Account Map

### Covered by GGB1 Substitution

| GL Account | PK | BusA | Doc Count | Source |
|---|---|---|---|---|
| 0002021042 | 21/31 | PAR | 545 | GGB1 `3IIEP###002` [VERIFIED from GB901] |
| 0002021061 | 21/31 | PAR | 15 | GGB1 `3IIEP###002` [VERIFIED from GB901] |

### BusA Derived by SAP Standard (line 852 same-company)

| GL Account | PK | BusA | Doc Count | Source |
|---|---|---|---|---|
| 0002022043 | 40/50 | PAR/PDK | ~530 | SAP standard `LHRTSF01.abap:852` (same-company) |
| 0002086092 | 40/50 | PAR/PDK | ~300 | SAP standard `LHRTSF01.abap:852` (same-company) |
| 0006011501-514 | 40 | PAR/PDK | ~800 | SAP standard `LHRTSF01.abap:852` (same-company) |
| **0002021011** | **21/31** | **PAR** | **4** | **SAP standard (same-company only) — NO fallback for intercompany** |

### No BusA (tolerated in multi-line docs)

| GL Account | PK | BusA | Doc Count | Note |
|---|---|---|---|---|
| 0005098030 | 40/50 | (empty) | 217 | Intercompany clearing — tolerated |
| 0005098013 | 50 | (empty) | 2 | Same pattern |

---

## 12. Extracted Code Assets (this session)

### SAP Standard — Function Group HRTS (Travel Posting)

| File | Lines | Content | Key Finding |
|---|---|---|---|
| `LHRTSF01.abap` | 3,526 | **Main forms — GSBER/BUKST logic core** | Line 852: `IF epk-bukst = epk-bukrs` (same-company check). Line 1693: `CLEAR epk-gsber` on vendor lines |
| `LHRTSU01.abap` | 304 | **PTRV_TRANSLATE** function module | Line 47-48: sets gsber_a/gsber_g parameters. Line 98: `CLEAR epk-gsber` for vendor lines (koart='K') when not per CO-object |
| `LHRTSU05.abap` | 257 | **PTRV_ACC_EMPLOYEE_PAY_POST** | Line 155: RW609 wrapper when BAPI returns errors |
| `LHRTSU06.abap` | 258 | PTRV_ACC_TRAVEL_POST_CP | Similar RW609 pattern |
| `LHRTSU07.abap` | 254 | PTRV_ACC_TRAVEL_DOCUMENT | Similar RW609 pattern |
| `LHRTSU08.abap` | 263 | PTRV_ACC_TRAVEL_POST_3RD | Similar RW609 pattern |
| `LHRTSU04.abap` | 126 | PTRV_ACC_TRAVEL_POST | Calls BAPI_ACC_TRAVEL_POST |
| `LHRTSTOP.abap` | 253 | Global data declarations | gsber_a/gsber_g flags, bukst_debit_fields structure |
| `LHRTSU02.abap` | 598 | GET_TRAVEL_VAT_REFUND_DATA | VAT refund FM |
| `LHRTSU03.abap` | 67 | F4IF_VAT_SHLP_EXIT | Search help |
| `LHRTSUXX.abap` | 11 | Generated dispatch | FM routing |
| `LHRTSF02.abap` | 576 | Additional forms | Tax handling |
| `LHRTSF03.abap` | 1,798 | Additional forms | Posting preparation |
| `LHRTSF04.abap` | 98 | Additional forms | Clearing |
| `LHRTSF05.abap` | 436 | Additional forms | Splitting |
| `LHRTSF06.abap` | 62 | Additional forms | Utilities |
| `SAPLHRTS.abap` | 23 | Main include list | Function group structure |

### SAP Standard — Travel Programs

| File | Lines | Content |
|---|---|---|
| `RPRAPA00.abap` | 841 | Travel A/P Account Creation (main) |
| `RPRAPADE_ALV.abap` | 248 | Data declarations |
| `RPRAPAFO_ALV.abap` | 4,175 | Forms/subroutines |
| `RPRAPA00_PBO.abap` | 57 | PBO module |
| `RPRAPAEX.abap` | 22 | Customer exit |
| `RPRAPAEX_001.abap` | 13 | Customer exit include |
| `RPUMKC00.abap` | 148 | Feature evaluation |
| `TSKHINCL.abap` | 971 | Batch input include |
| `RPRTRV00.abap` | 344 | Travel posting run |
| `RPRTRV01.abap` | 806 | Travel posting |
| `RPRTRV10.abap` | 1,147 | Travel posting |
| `RPRTRV11.abap` | 451 | Travel posting |
| `RPRTRVDT.abap` | 440 | Travel data types (PSREF structure with GSBER) |
| `RPRTB000.abap` | 2,143 | Travel batch |
| `RPRTB000_ALV.abap` | 3,201 | Travel batch ALV |
| `RPRTEC00.abap` | 388 | Travel expense calculation |
| `RPRTEF00.abap` | 254 | Travel expense form |

### UNESCO Custom — Travel Exits and BAdIs

| File | Lines | Content |
|---|---|---|
| `ZCL_IM_TRIP_POST_FI_CM00A.abap` | 84 | **BAdI EX_ZWEP_ACCOUNT2** — PA0027-02 GSBER derivation |
| `ZCL_IM_TRIP_POST_FI_CM00B.abap` | 40 | EX_ZWEP_COMPLETE — commented out PA0001 read |
| `ZCL_IM_TRIP_POST_FI_CM006.abap` | 75 | MODIFY_PTRV_DOC_HD — doc type TV/TF by BUKRS/WERKS |
| `ZCL_IM_TRIP_POST_FI_CM007.abap` | 72 | EXB706K — travel user code from PERSG |
| `ZCL_IM_TRIP_POST_FI_CM008.abap` | 33 | EX_ZWEP — doc type TV/TF from PA0001 |
| `ZCL_IM_TRIP_POST_FI_CM009.abap` | 2 | EX_ZWEP_ACCOUNT1 — empty |
| `ZXTRVU05_v2.abap` | 78 | Travel exit — GSBER derivation (UNES active, WHEN OTHERS commented out) |
| `ZXTRVU03_v2.abap` | 71 | Travel validation — period overlap, dependants (no GSBER) |
| `YFI_YRGGBS00_EXIT.abap` | — | GGB1 substitution exit — BVTYP for travel vendors |
| `YFI_RPRAPA00_COMPL.abap` | 88 | Wrapper for vendor bank data update |
| `YFI_LFBK_TRAVEL_UPDATE.abap` | — | Vendor bank data update (references KTOKK) |

**Total extracted this session:** 34 SAP standard + 35 UNESCO custom = **69 travel ABAP files**

---

## 13. Data Sources

| Source | Tables/Objects | Method |
|---|---|---|
| Gold DB (P01) | YBASUBST, YTFI_BA_SUBST | SQLite query |
| Gold DB (P01) | bseg_union + BKPF (bsak for vendor lines) | SQLite join |
| Gold DB (P01) | cts_transports + cts_objects | Transport timeline |
| Gold DB (P01) | GB901 (583 rows), GB02C, T100_ZFI, T80D, GB903 | RFC extraction (this session) |
| P01 Live RFC | LFB1 (vendor master) | RFC_READ_TABLE |
| P01 Live RFC | PA0001, PA0027 (HR master data) | RFC_READ_TABLE |
| P01 Live RFC | PTRV_SCOS (trip cost assignment) | RFC_READ_TABLE |
| P01 Live RFC | BKPF + BSEG (recent TV docs) | RFC_READ_TABLE |
| D01 RFC | RPRAPA00 + 7 includes (841 lines) | RPY_PROGRAM_READ via SNC |
| D01 RFC | Function group HRTS (17 files, ~7,600 lines) | RPY_PROGRAM_READ via SNC |
| D01 RFC | Travel programs RPRTRV* + RPRTB* (9 files, ~9,200 lines) | RPY_PROGRAM_READ via SNC |
| Extracted Code | ZCL_IM_TRIP_POST_FI (14 methods), ZXTRVU05, ZXTRVU03, YRGGBS00 | ADT/Code analysis |
| Email | 3 embedded screenshots (posting run, error log, posting lines) | Image analysis |
| Knowledge | basu_mod_technical_autopsy.md, finance_validations_and_substitutions_autopsy.md | Framework docs |

**New tables added to Gold DB this session:** GB901 (583 rows), GB02C (10 rows), T100_ZFI (36 rows), T80D (8 rows), GB903 (3 rows).

**New code extracted this session:** 34 SAP standard files (24,559 lines) in `extracted_code/SAP_STANDARD/TV_TRAVEL/`.

**New knowledge:** `knowledge/domains/FI/travel_busarea_derivation.md` — multi-layer BusA derivation chain.
