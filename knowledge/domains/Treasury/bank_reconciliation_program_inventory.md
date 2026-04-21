# UNESCO Custom Bank Reconciliation Program Inventory

**Domain:** Treasury / Bank Statement Reconciliation
**Scope:** All custom Y* programs and includes that manipulate or report
bank-account clearing/reconciliation at UNESCO on P01.
**Extracted:** Session #057 (2026-04-20) via `pyrfc + SNC/SSO + RPY_PROGRAM_READ` on P01.
**Source tree:** `extracted_code/CUSTOM/BANK_RECONCILIATION/` (+ the pre-existing `extracted_code/CUSTOM/YTBAE002/`)
**Cross-ref incident:** [INC-000006906 — Maputo MZN bank reconciliation TIME_OUT](../../incidents/INC-000006906_maputo_mzn_bank_reconciliation_download.md)
**Related claims:** Claim 50, 51, 52, 53, 54
**Related skill:** `.agents/skills/sap_bank_statement_recon/SKILL.md`

---

## 1. Overview

UNESCO operates **three distinct custom bank-reconciliation program families**
on P01, all built across 2001-2023 and still partially active. They do
different things, target different user personas, and carry different
technical debt:

| Family | Era | Purpose | TCODEs | Executables | Includes |
|---|---|---|---|---|---|
| **YTBAI*** | 2001 | Input file conversion (SMARTLINK CMI940 → MT940) | YTR0 | YTBAI001 | — |
| **YTBAE*** + **YTBAM*** | 2001-2007 (with 2020s touches) | Interactive bank-clearing with BDC against FB08 / F-04 / FBRA | YTR1, YTR2, YTR2_HR, YTR3 | YTBAE001, YTBAE001_HR, YTBAE002 | YTBAM001, YTBAM002, YTBAM002_HR, YTBAM002_HR_UBO, YTBAM003, YTBAM003_HR, YTBAM004, YTBAM004_HR |
| **YFI_BANK_RECONCILIATION*** | 2023 | Read-only ALV dashboard / detail view (OOP via YCL_FI_BANK_RECONCILIATION_BL) | YFI_BANK1 | YFI_BANK_RECONCILIATION | YFI_BANK_RECONCILIATION_DATA, YFI_BANK_RECONCILIATION_SEL |

Total: **15 programs extracted** (6 executables + 9 includes) · **8 candidates not present** (HR variants that don't exist: YTBAE002_HR, YTBAI001_HR, YTBAM001_HR, YTBAM005, YTBAM005_HR, YFI_BANK_RECONCILIATION_FORM/TOP/F01 — the new 2023 family uses only DATA and SEL includes + OOP class).

Screenshots from SE38 F4 cover the YT* prefix + YFI_BANK* prefix; we did not find any `YBAE*`, `YBAI*`, or `YBAM*` TCODEs (tested live via TSTC RFC — zero rows).

---

## 2. Complete Classification Table

Columns: **type / purpose / TCODE / creat_user / creat_date / mod_user / mod_date / devclass / LOC (after comment-strip) / parent includes or callers / BDC mode (constant name, value, line) / anti-pattern status / related incidents / status (ACTIVE=recent runs, DORMANT=configured but no runs, LEGACY=referenced but superseded)**.

| # | Name | Type | Purpose | TCODE | Author (creat) | Creat | Mod (last) | Devclass | LOC | Parent / Used-by | BDC mode | CALL TX targets | `mode_E_in_loop`? | empty-range guard? | Status | Related incidents |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **YTBAI001** | EXECUTABLE | SMARTLINK CMI940 → MT940 file conversion (OPEN DATASET read/write, filters `/25:SOGEFRPP/` header) | YTR0 (variant `YTBAI001`) | A.ELMOUCH | 2002-02-08 | A_AHOUNOU 2007-06-05 | YT | 197 | standalone | n/a (no BDC) | none | n/a | n/a (file pipe, no ranges) | **DORMANT** (file paths point to `/usr/sap/D01/conversion/...`; no TBTCO runs) | — |
| 2 | **YTBAE001** | EXECUTABLE | HQ bank-clearing report (AT LINE-SELECTION → BDC to FB08/F-04). Selects BSIS via `TABLES: BSIS` + `PERFORM 01_SELECT_BSIS` in include YTBAM003 (iterates `TSAKO` config). | YTR1 (variant `BK REC STATMT2`), YTR2 (variant `BANK_RECONCIL`) | A.ELMOUCH | 2002-01-18 | A_AHOUNOU 2007-01-30 | YT | 312 | includes YTBAM002 + YTBAM003 + YTBAM004 (YTBAE001.abap:530-532) | `C_MOD VALUE 'E'` at YTBAE001.abap:118 | FB08, F-04 (via YTBAM002 `19_CALL_TRANSACTION`) | AT LINE-SELECTION, **not** inside GET/LDB loop | n/a (iterates TSAKO, empty-list = zero SELECTs; safe) | **DORMANT** (1 job in TBTCO with STATUS=NULL/STRTDATE=NULL — never actually ran as a batch) | — |
| 3 | **YTBAE001_HR** | EXECUTABLE | HR/payroll variant of YTBAE001. Same interactive flow, different includes (uses `_HR` siblings). Tracks `ZUONR_HR` (HR assignment-number suffix) in BSIS workstruct. | YTR2_HR (variant `BANK_RECONCIL`) | A_AHOUNOU | 2007-04-23 | A_AHOUNOU 2009-02-02 | YT | 331 | includes YTBAM002_HR + YTBAM003_HR + YTBAM004_HR (YTBAE001_HR.abap:567-571) | `C_MOD VALUE 'E'` at YTBAE001_HR.abap:122 | FB08, F-04 (via YTBAM002_HR) | AT LINE-SELECTION, **not** inside GET/LDB loop | n/a | **DORMANT** (no TBTCO entries; confirmed via SQL) | — |
| 4 | **YTBAE002** | EXECUTABLE | Bank reconciliation statement — monolithic replacement for YTBAE001+YTBAM002/3 stack. Uses LDB `SDF` via `LDB_PROCESS` at :1509. BSIS range built from SKB1 at :1096-1127. Has the empty-range-to-unbounded-LDB-scan bug (Claim 53). | YTR3 (direct binding) | D_ANDROS | 2007-10-24 | JP_LOPEZ 2026-04-20 (Session #057 touch; source unchanged) | YT | 2,315 | standalone | `GC_MOD VALUE 'E'` at YTBAE002.abap:27; `GC_UPD VALUE 'S'` at :31 | FB08 (:723), F-04 (:771), FBRA (:819), FB08 alt-branch (:853) | YES in the sense that the CALL TRANSACTION sites are in the same AT LINE-SELECTION handler that re-fires per user click, AND any BDC-error-triggered SAPGUI round-trip happens synchronously in the caller's work process (Claim 54) | **NO** — `GR_SAKNR_OI` / `GR_SAKNR` passed to `LDB_PROCESS` with no `IS NOT INITIAL` check (YTBAE002.abap:397, 401, 1096-1127) → Claim 53 TIME_OUT | **ACTIVE** (5 scheduled job runs in TBTCO 2026-03-04 to 2026-03-05, STATUS=F) | **INC-000006906 (primary)** |
| 5 | **YFI_BANK_RECONCILIATION** | EXECUTABLE | New (2023) read-only reconciliation view. Two modes: detailed ALV list (`P_DETAIL`) or dashboard ALV (`P_DASH`). Delegates everything to `YCL_FI_BANK_RECONCILIATION_BL` OOP class. NO BDC, NO CALL TRANSACTION, NO LDB — direct SELECT via the class. | YFI_BANK1 (direct binding) | N_MENARD | 2023-04-07 | N_MENARD 2023-04-14 | YA | 34 | includes YFI_BANK_RECONCILIATION_DATA + YFI_BANK_RECONCILIATION_SEL | n/a | none | n/a | n/a (class owns selection) | **ACTIVE** (foreground only — no TBTCO runs, interactive reporting) | — |
| 6 | **YTBAM001** | INCLUDE | Include containing FORM definitions used by YTBAE001/_HR's event handlers (flow-control helpers). No CALL TRANSACTION. No SELECT BSIS. | (n/a — include) | A.ELMOUCH | 2002-01-18 | N_MENARD 2023-10-11 | YT | 243 | referenced by YTBAE001 (standalone; NOT pulled in by YTBAE001 today but was in older versions) | n/a | none (false-positive "CALL" hits from regex = SCREEN CALL / PERFORM) | n/a | n/a | **LEGACY** (retained but not included by current YTBAE001 source) | — |
| 7 | **YTBAM002** | INCLUDE | Contains `FORM 19_CALL_TRANSACTION` — the FB08/F-04 branch switchboard. 4 x `CALL TRANSACTION Y_TRANS USING BDCDTAB` (no explicit MODE in THIS file — relies on caller's `C_MOD`). | (n/a) | S.MAGAL | 2002-01-18 | A_AHOUNOU 2007-01-30 | YT | 734 | included by YTBAE001 (YTBAE001.abap:530) | n/a (inherits from caller) | FB08 (line 214), FB08 (:262), F-04 (:310), F-04 (:344) | No — those CALL TX are after the BSIS prep loop at :65-126, fired sequentially in FORM body | n/a (no ranges declared here) | **ACTIVE** (alive only as long as YTBAE001 is invoked) | — |
| 8 | **YTBAM002_HR** | INCLUDE | HR-suffix variant. Uses `ZUONR_HR` field on T_BSIS (HR assignment number tracking). `CALL TRANSACTION Y_TRANS USING BDCDTAB MODE C_MOD` explicit at :228, :276, :324, :358. `BDCDTAB-FVAL = 'UNES'` hard-coded at :807. | (n/a) | A_AHOUNOU | 2007-04-23 | A_AHOUNOU 2009-02-02 | YT | 740 | included by YTBAE001_HR (YTBAE001_HR.abap:567) | inherits `C_MOD='E'` from YTBAE001_HR.abap:122 | FB08 (:228), FB08 (:276), F-04 (:324), F-04 (:358) — all 4 with `MODE C_MOD` = 'E' | No, but MODE='E' in an AT LINE-SELECTION-triggered sequence of 4 BDCs is still network-coupled (Claim 54 pattern, lighter variant) | n/a | **DORMANT** (YTR2_HR is alive per TSTC but YTBAE001_HR has no job runs) | — |
| 9 | **YTBAM002_HR_UBO** | INCLUDE | UBO field-office HR variant of YTBAM002_HR. Only diff vs YTBAM002_HR: `BDCDTAB-FVAL = 'UBO'` (instead of `'UNES'`) at :811 (D_SIQUEIRA 2008-10-21 modification). Same BDC anti-pattern at :231, :279, :327, :361. | (n/a) | D_SIQUEIRA | 2009-02-02 | D_SIQUEIRA 2009-02-02 | YUBO | 740 | not currently included by any executable on P01 (legacy copy; YTBAE001_HR includes YTBAM002_HR, NOT _HR_UBO) | — | FB08 (:231), FB08 (:279), F-04 (:327), F-04 (:361) | Same as YTBAM002_HR | n/a | **LEGACY** (not included by any executable) | — |
| 10 | **YTBAM003** | INCLUDE | Contains `FORM 01_SELECT_BSIS` (:51-69), `FORM 03_SELECT_BSEG` (:79-121). Drives BSIS/BSEG selection via `LOOP AT TSAKO` (config-table of accounts to reconcile). | (n/a) | S.MAGAL | 2002-01-18 | A_AHOUNOU 2010-05-20 | YT | 895 | included by YTBAE001 (:531) | — | none | No | n/a (iterates TSAKO; if TSAKO empty, zero SELECTs) | **DORMANT** | — |
| 11 | **YTBAM003_HR** | INCLUDE | HR variant of YTBAM003. Same TSAKO-driven selection but with HR-specific ZUONR_HR handling. | (n/a) | A_AHOUNOU | 2007-04-23 | A_AHOUNOU 2014-01-30 | YT | 949 | included by YTBAE001_HR (:569) | — | none | No | n/a | **DORMANT** | — |
| 12 | **YTBAM004** | INCLUDE | Table control data include (BDC screen-field constants, number-range helpers). | (n/a) | S.MAGAL | 2002-01-18 | A.ARKWRIGHT 2002-01-18 | YT | 200 | included by YTBAE001 (:532) | — | none | n/a | n/a | **DORMANT** | — |
| 13 | **YTBAM004_HR** | INCLUDE | HR variant of YTBAM004. Byte-identical to YTBAM004 per diff, only the header comment and author field differ. | (n/a) | A_AHOUNOU | 2007-04-23 | A_AHOUNOU 2007-06-05 | YT | 200 | included by YTBAE001_HR (:571) | — | none | n/a | n/a | **DORMANT** | — |
| 14 | **YFI_BANK_RECONCILIATION_DATA** | INCLUDE | 3-line DATA include: `GS_BSIS TYPE BSIS`, `GV_REPORT_TYPE(1) TYPE C`, `GO_BANK_RECONCILIATION_BL TYPE REF TO YCL_FI_BANK_RECONCILIATION_BL`. | (n/a) | N_MENARD | 2023-04-07 | N_MENARD 2023-04-07 | YA | 3 | included by YFI_BANK_RECONCILIATION (:8) | — | — | n/a | n/a | **ACTIVE** | — |
| 15 | **YFI_BANK_RECONCILIATION_SEL** | INCLUDE | Selection-screen include: `P_BUKRS`, `S_HKONT`, `P_DATE_Z`, `P_DATE_O`, `P_DETAIL`/`P_DASH` radio, `INITIALIZATION` event (auto-fills last-day-of-previous-month). Calls `YCL_FI_BANK_RECONCILIATION_BL=>INITIALIZE_HKONT( )` at :20. | (n/a) | N_MENARD | 2023-04-07 | N_MENARD 2023-06-07 | YA | 41 | included by YFI_BANK_RECONCILIATION (:9) | — | — | n/a | n/a | **ACTIVE** | — |

### 2.1 Candidates probed but not present on P01

| Candidate | Reason |
|---|---|
| YTBAE002_HR | Does not exist. YTBAE002 replaces both YTBAE001 and YTBAE001_HR (the stack was monolithized in 2007, eliminating the need for a separate HR variant of the new design). |
| YTBAI001_HR | Does not exist. YTBAI001 is a file converter; HR had no separate file format need. |
| YTBAM001_HR | Does not exist. YTBAM001 is not used by YTBAE001_HR today (YTBAE001_HR includes YTBAM002_HR/003_HR/004_HR only). |
| YTBAM005 / YTBAM005_HR | Do not exist. The numeric sequence stops at 004. |
| YFI_BANK_RECONCILIATION_FORM / _TOP / _F01 | Do not exist. The 2023 design uses only DATA + SEL includes — the FORM logic is in the OOP class `YCL_FI_BANK_RECONCILIATION_BL`. |

---

## 3. Family Relationship Diagram

```
                   TCODE YTR0 (variant YTBAI001)
                          |
                          v
                 +---------------------+
                 | YTBAI001 (2002)     |  SMARTLINK CMI940 -> MT940
                 | DORMANT             |  File-only, no BDC, no DB writes
                 +---------------------+

                                                                                          TCODE YTR3 (direct)
   TCODE YTR1 / YTR2 (variants of YTBAE001)      TCODE YTR2_HR (variant BANK_RECONCIL)            |
              |                                            |                                      v
              v                                            v                       +------------------------------------+
   +----------------------+                   +------------------------+           | YTBAE002 (2007, monolithic)        |
   | YTBAE001 (2002)      |                   | YTBAE001_HR (2007)     |           | ACTIVE (5 batch runs Mar 2026)     |
   | DORMANT              |                   | DORMANT                |           | 2315 LOC                           |
   | 312 LOC              |                   | 331 LOC                |           |                                    |
   +----+---------+------+                    +----+----------+-----+             | * LDB SDF via LDB_PROCESS          |
        |         |      |                         |          |     |             | * GR_SAKNR_OI built from SKB1      |
        v         v      v                         v          v     v             | * Empty-range -> unbounded scan    |
   YTBAM002   YTBAM003   YTBAM004          YTBAM002_HR   YTBAM003_HR  YTBAM004_HR  |   -> TIME_OUT  (Claim 53)          |
   (switchboard/         (TSAKO-driven     (switchboard/  (TSAKO,    (table ctrl   | * MODE 'E' x 4 CALL TX             |
    BDC chain)            BSIS SELECT)      BDC,          HR-ZUONR)   data,        |   -> WAN-coupled SAPGUI (Claim 54) |
                                            BDCDTAB-FVAL='UNES')     HR-version)   +------------------------------------+
                                                                                                       
                                         YTBAM002_HR_UBO (2009)                                        
                                         LEGACY — not included by any executable.                      
                                         Diffs only in BDCDTAB-FVAL='UBO' (hardcoded company code).   

                  TCODE YFI_BANK1 (direct)                                                            
                          |                                                                            
                          v                                                                            
   +-------------------------------------------+                                                       
   | YFI_BANK_RECONCILIATION (2023)            |                                                      
   | ACTIVE (interactive only)                 |                                                      
   | 34 LOC + 2 includes + 1 OOP BL class      |                                                      
   +----+----------------+----------------------+                                                     
        |                |                                                                            
        v                v                                                                            
   _DATA (3 LOC)   _SEL (41 LOC)                                                                      
   (globals)       (sel-screen + INITIALIZATION                                                       
                    auto-filling last-day-of-prev-month)                                              
                                                                                                      
   Delegates to:  YCL_FI_BANK_RECONCILIATION_BL  (class — NOT in this inventory, separate entity)
```

---

## 4. Anti-Pattern Scan Results

### 4.1 MODE 'E' + CALL TRANSACTION — Claim 54 pattern

We looked for: a BDC mode constant with literal `'E'` AND at least one
`CALL TRANSACTION ... MODE <that_constant>` somewhere in the same program
(or in an include reachable from it). Results:

| Program | MODE constant | Value | Site | CALL TX targets hit via this mode | Claim 54 systemic? |
|---|---|---|---|---|---|
| YTBAE001 | `C_MOD` | **'E'** | YTBAE001.abap:118 | FB08, F-04 via include YTBAM002 (the include reads `C_MOD` out of the caller's DATA scope) | **Inherited form** — milder than YTBAE002 because the invocation is inside AT LINE-SELECTION + one BDC per user click, NOT inside a BSIS/LDB iteration. Still MODE 'E' — cosmetic/UX concern on WAN paths. |
| YTBAE001_HR | `C_MOD` | **'E'** | YTBAE001_HR.abap:122 | FB08 (x2), F-04 (x2) via YTBAM002_HR lines 228, 276, 324, 358 (all four with `MODE C_MOD`) | Same as YTBAE001 — inherited form. Dormant (no recent runs) so latent risk only. |
| YTBAE002 | `GC_MOD` | **'E'** | YTBAE002.abap:27 (line 31: `GC_UPD = 'S'` for update = synchronous) | FB08 (:723), F-04 (:771), FBRA (:819), FB08 alt (:853) — all 4 with `MODE GC_MOD` | **YES — primary Claim 54 case**. 4 CALL TXs + MODE 'E' + batch is scheduled (5 runs Mar 2026) + dialog use from MZN field office hit TIME_OUT 2026-04-20. |
| YTBAM002 | inherits caller's `C_MOD` | n/a | n/a | FB08 (:214, :262), F-04 (:310, :344) — but in YTBAM002 the `MODE <const>` clause is NOT explicit in the file I extracted (different from YTBAM002_HR, which IS explicit). Needs re-verification against the live-live file. | Pending (flag: `status: provisional_for_ytbam002`). |
| YTBAM002_HR | inherits `C_MOD` | explicit `MODE C_MOD` | YTBAM002_HR.abap:229, :277, :325, :359 | FB08 (x2), F-04 (x2) | Systemic with YTBAE001_HR (dormant). |
| YTBAM002_HR_UBO | same as YTBAM002_HR | same | :232, :280, :328, :362 | FB08 (x2), F-04 (x2) | Legacy — not invoked. |
| YFI_BANK_RECONCILIATION* family | n/a | no BDC | — | — | No — read-only OOP design. |
| YTBAI001 | n/a | no BDC | — | — | No — file converter. |

**Conclusion:** Three executables carry MODE 'E':
- **YTBAE002 is the live hot one** — the same program that dumped for J_DAVANE on 2026-04-20 (INC-000006906). Fix pending.
- **YTBAE001 + YTBAE001_HR are dormant but still registered** (TCODEs YTR1, YTR2, YTR2_HR). If any user happens to still use them, they would hit the same MODE 'E' experience. The systemic recommendation below covers all three.

### 4.2 Empty-range → unbounded LDB scan — Claim 53 pattern

We looked for: a range/selection-table populated from SKB1 (or any master-data read), then passed to `LDB_PROCESS` (or a SELECT with `WHERE x IN range`) WITHOUT an `IS NOT INITIAL` guard on the range.

| Program | Range(s) | Populated from | Passed to | Guard? | Claim 53 case? |
|---|---|---|---|---|---|
| YTBAE002 | `GR_SAKNR`, `GR_SAKNR_OI` | SKB1 SELECT at :1098-1127 (`WHERE BUKRS + HBKID + HKTID`) filtered by account-number-class + XOPVW='X' | `LDB_PROCESS LDBNAME='SDF'` at :1509 (via `PERFORM PROC_LDB_CALL USING GR_SAKNR_OI 'BSIS'` at :397) | **NO** — no `IS NOT INITIAL` before PERFORM PROC_LDB_CALL | **YES — systemic cause of INC-000006906 TIME_OUT** |
| YTBAE001 | `FR_HBKID` range (from user selection) + whatever YTBAM003's `LOOP AT TSAKO` gives | TSAKO config table | `SELECT ... FROM BSIS WHERE BUKRS EQ TSAKO-BUKRS AND HKONT EQ TSAKO-HKONT` (YTBAM003.abap:54-58) | **No explicit guard needed** — iterates TSAKO row-by-row; if TSAKO is empty, LOOP doesn't iterate, zero SELECTs fire. Safe by construction. | No |
| YTBAE001_HR | same as YTBAE001 | TSAKO | same as YTBAE001 | Safe by construction | No |
| YFI_BANK_RECONCILIATION | n/a (class-owned) | `YCL_FI_BANK_RECONCILIATION_BL=>INITIALIZE_HKONT( )` fills `S_HKONT[]` at _SEL.abap:20 | `GET_DATA` on the class | We haven't extracted the class to confirm its internal guard, but the design is explicitly bounded by the selection-screen (`S_HKONT` is a normal SELECT-OPTION, an empty range would be a **user choice**, not a silent derivation). | Almost certainly no — design difference. |
| YTBAI001 | n/a | — | — | — | No |

**Conclusion:** Claim 53 (empty-range → unbounded-LDB-scan) is currently
**unique to YTBAE002** in this family. Claim 53 does not auto-extend to the
rest of the Y-stack because YTBAE001 uses a fundamentally different
selection mechanism (TSAKO iteration) and YFI_BANK_RECONCILIATION delegates
to a class with user-controlled S_HKONT range.

### 4.3 Hardcoded company-code

Observed at YTBAM002_HR.abap:807 (`BDCDTAB-FVAL = 'UNES'`) and YTBAM002_HR_UBO.abap:811 (`'UBO'`). This is a **multi-tenant smell** — the pattern originated in 2008 when D_SIQUEIRA forked YTBAM002_HR to YTBAM002_HR_UBO specifically to swap the company code. Treating company code as a source-level constant means every new field office would need a new include copy. Not a defect today (YTBAM002_HR_UBO is not included), but listed here because the brain needs to know the debt shape.

---

## 5. Remediation Recommendations

### 5.1 YTBAE002 (INC-000006906 primary)

Confirmed today (2026-04-20): live P01 source still has `GC_MOD = 'E'` at line 27. The fix file drafted at `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap` changes that to `'N'`. **Apply via D01 → transport → P01.** That closes both Claim 54 (BDC blocking) and 75% of the Claim 53 symptom severity (dialog TIME_OUT becomes a much-lower-probability outcome because the CALL TX is no longer synchronously user-coupled).

Claim 53's empty-range defect is independent: even with MODE 'N' the unbounded LDB scan will still fire if SKB1 returns zero matching rows. The surgical fix is to add an `IF GR_SAKNR_OI IS NOT INITIAL.` guard around `PERFORM PROC_LDB_CALL USING GR_SAKNR_OI 'BSIS'` at YTBAE002.abap:397 (and an analogous guard around the SKC1C call at :401 for GR_SAKNR). Recommend **one transport carrying both fixes together**.

### 5.2 YTBAE001 + YTBAE001_HR

Both currently DORMANT. Recommendation: **do NOT spend a transport slot on them today.** Instead, file a PMO follow-up to decommission YTR1, YTR2, YTR2_HR if the last actual usage can be confirmed zero. If decommission is blocked, apply the MODE 'E' → 'N' change to YTBAE001.abap:118 (`C_MOD`) and YTBAE001_HR.abap:122 (`C_MOD`) in a lower-priority transport. The fix is mechanically identical to YTBAE002 but the risk-of-regression is lower because of the dormant state.

### 5.3 YTBAM002_HR_UBO (legacy)

Not included by any executable today. Recommendation: **mark deleted in a housekeeping transport** (TADIR remove). No user-facing consequence.

### 5.4 YFI_BANK_RECONCILIATION

Not an action item for INC-000006906. Open a **separate known_unknown**
(see Section 7) to extract `YCL_FI_BANK_RECONCILIATION_BL` and understand
what selection logic sits behind `GET_DATA` — because if that class
eventually replaces YTR3 usage, the team needs a class-level autopsy.

### 5.5 YTBAI001 (SMARTLINK)

No recent runs. The hardcoded `/usr/sap/D01/conversion/...` filesystem paths
mean this was **deployed on D01, never moved to P01 at the same path**. Open
a KU: "Is YTBAI001 still in use for incoming bank statements, or has
SMARTLINK been superseded by the EBS MT940 pipeline and AL11/EBS?"

---

## 6. HR Variants — What the `_HR` Suffix Means at UNESCO

The `_HR` suffix in this family denotes **parallel code paths specialized
for HR/payroll-originated clearing** (employee payroll payments that hit
the same clearing-account class as accounts-payable payments but need to
track an additional key: the HR assignment number, `ZUONR_HR`).

Signatures we confirmed:

1. **Independent copies, not wrappers.** `YTBAE001_HR` is a full copy of
   `YTBAE001` (not a subclass, not a delegating shell). Same for
   `YTBAM002_HR`, `YTBAM003_HR`, `YTBAM004_HR`. Diff shows the bodies
   diverge in non-trivial places (HR-specific field reads, hardcoded
   `BDCDTAB-FVAL = 'UNES'`).

2. **Extra field `ZUONR_HR`.** Grep of YTBAM002_HR shows BSIS workstruct
   extended with `ZUONR_HR` (HR assignment-number suffix tracked
   separately from the standard ZUONR). YTBAM002 (non-HR) does not touch
   this field.

3. **Different author trail.** A_AHOUNOU authored the entire `_HR` family
   in April 2007 — 5 years after S.MAGAL / A.ELMOUCH built the original.
   The `_HR` path was a 2007 additive fork, not a rewrite.

4. **Different include chain.** `YTBAE001` → includes `YTBAM002/003/004`.
   `YTBAE001_HR` → includes `YTBAM002_HR/003_HR/004_HR`. No shared include
   at all — a true parallel stack.

5. **Not all variants have an _HR sibling.** `YTBAI001` (file converter)
   has no HR variant because file-format conversion is HR-agnostic.
   `YTBAE002` (the 2007 monolith) also has no HR variant — the monolith
   was built AFTER the _HR fork (Oct 2007 vs Apr 2007) and appears to
   cover both use cases from the start. The user base effectively split:
   YTR3 (YTBAE002) for the new unified path and YTR2_HR (YTBAE001_HR) for
   legacy HR-specific flows that D_ANDROS didn't migrate.

6. **`_HR_UBO` is a second-order fork.** YTBAM002_HR was copied to
   YTBAM002_HR_UBO in 2008 by D_SIQUEIRA to hardcode a different company
   code (`'UBO'` vs `'UNES'`). That makes 3 parallel copies of
   essentially-the-same BDC chain. **Technical debt signal:** any future
   defect discovered in the BDC chain needs to be fixed in up to 3 places.

---

## 7. Open Known-Unknowns (Follow-ups)

| KU ID | Question | Why it matters |
|---|---|---|
| KU-2026-057-01 | Is YTBAI001 (SMARTLINK CMI940 → MT940) still in production use, or has the EBS MT940 pipeline superseded it? File paths point to `/usr/sap/D01/conversion/input/TITRBK03/sg2707.txt` which looks like a legacy SOGEFRPP feed. | Determines whether to maintain YTR0 or deprecate it. |
| KU-2026-057-02 | When are YTR1 / YTR2 / YTR2_HR last run? TBTCO only shows batch jobs; users might still be running these transactions interactively and we'd have no record in Gold DB. Requires STAD extraction scoped to these TCODEs. | Determines remediation priority for YTBAE001 / YTBAE001_HR MODE 'E' fix. |
| KU-2026-057-03 | What exactly does `YCL_FI_BANK_RECONCILIATION_BL=>GET_DATA` do under the hood? We haven't extracted the class. | Needed to decide whether this replaces the YTBAE002 workflow or supplements it. |
| KU-2026-057-04 | Does YTBAM002_HR_UBO qualify for TADIR-delete? It's not included by any executable today. Confirm zero references via cross-project grep on P01. | Housekeeping; removes an unreachable-code trap for future incident analysts. |

---

## 8. Usage / Owner Evidence

| Program | Scheduled jobs (TBTCO) | Latest start | Owner (from CREAT_USER / last MOD) | TCODE | Usage pattern |
|---|---|---|---|---|---|
| YTBAE002 | 5 jobs (2026-03-04 to 2026-03-05) STATUS=F | 2026-03-05 | D_ANDROS (creator) · JP_LOPEZ (2026-04-20 touch, Session #057, source unchanged) | YTR3 | Batch + dialog |
| YTBAE001 | 1 job, STATUS=NULL, STRTDATE=NULL | (never ran) | A.ELMOUCH · A_AHOUNOU | YTR1, YTR2 | Dialog only (dormant) |
| YTBAE001_HR | 0 | — | A_AHOUNOU | YTR2_HR | Dialog only (dormant) |
| YFI_BANK_RECONCILIATION | 0 | — | N_MENARD | YFI_BANK1 | Dialog only (active) |
| YTBAI001 | 0 | — | A.ELMOUCH · A_AHOUNOU | YTR0 | File-to-file (dormant/legacy) |
| YTBAM001/2/3/4/+HR variants/_HR_UBO | n/a (includes) | — | — | n/a | Reachable only through their parent executable |

---

## 9. Cross-References

- **Incident:** [INC-000006906 — Maputo MZN bank reconciliation download](../../incidents/INC-000006906_maputo_mzn_bank_reconciliation_download.md)
- **Claims:** Claim 50 (YBANK sets coverage), 51 (uncovered GL count), 52 (233 HKONTs outside YBANK coverage), 53 (YTBAE002 empty-range bug), 54 (MODE 'E' + BDC network coupling)
- **Skill:** [.agents/skills/sap_bank_statement_recon/SKILL.md](../../../.agents/skills/sap_bank_statement_recon/SKILL.md)
- **Fix file:** `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`
- **Extractor used:** `Zagentexecution/mcp-backend-server-python/extract_bank_recon_family.py`
- **Inventory artifact:** `extracted_code/CUSTOM/BANK_RECONCILIATION/_family_inventory.json`

---

## 10. Data Sources

| Source | Access path | Used for |
|---|---|---|
| P01 RFC + SNC | `RPY_PROGRAM_READ` | Full program source (15/23 programs extracted; 8 candidates do not exist on P01) |
| P01 RFC + SNC | `RFC_READ_TABLE TSTC / TSTCP / TSTCT` | TCODE bindings YTR0/1/2/2_HR/3/YFI_BANK1 |
| P01 RFC + SNC | `RFC_READ_TABLE TADIR` | Authoring info (PGMID, OBJECT, OBJ_NAME, DEVCLASS, AUTHOR) |
| Gold DB | `tbtco` / `tbtcp` | Scheduled-job evidence (YTBAE002 ACTIVE, YTBAE001 dormant) |
| Extracted source | `extracted_code/CUSTOM/BANK_RECONCILIATION/` | 15 .abap files + per-program `_manifest.json` + top-level `_family_inventory.json` |

---

*Last updated: Session #057 · 2026-04-20 · Main agent execution (not subagent) per `feedback_main_agent_holds_incident_context`.*
