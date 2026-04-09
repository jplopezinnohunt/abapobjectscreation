# Technical Autopsy: Finance Validations & Substitutions (Standard & Custom)

## 1. Overview
This autopsy documents the raw logic discovered within the `YRGGBS00` formpool and related configuration tables. It defines the "Logical Perimeter" of SAP Financial postings at UNESCO, focusing on how Business Areas, Funds, and Cost Centers are interconnected.

## 2. Core Routine Pool: `YRGGBS00`
The following logic has been extracted directly from the system source code.

### 2.1 Exit `UAEP`: Assets Expenses Posting
**Trigger**: Asset-related expenditure postings.
**Logic**: Forces a 1:1:1 mapping between Business Area, Fund, and Cost Center for specified company codes.

| BUKRS | GSBER | Resulting FISTL | Resulting GEBER | Resulting KOSTL |
| :--- | :--- | :--- | :--- | :--- |
| `UNES` | `GEF` | `UNESCO` | `GEF` | `111023` |
| `UNES` | `OPF` | `UNESCO` | `OPF` | `131023` |
| `UNES` | `PFF` | `UNESCO` | `PFF` | `121023` |
| `IBE` | (Any) | `IBE` | `PFF` | (N/A) |

### 2.2 Exit `UATF` / `NSAI`: Technical Fund & Object Clearance
**Trigger**: Technical fund substitution for Assets.
**Critical Logic**: 
- **Object Clearance**: If a WBS Element (`BSEG-PROJK`) is present during these technical substitutions, it is **FORCE-CLEARED** (`CLEAR bseg-projk`).
- **Purpose**: Prevents PS-PSM overlap errors where a project might belong to a different fund than the mandatory technical fund.

### 2.3 Exit `U904`: Payment Supplement Linkage
**Logic**: Connects the payment "flavor" to the reporting segment.
- `bseg-uzawe = 'PF'` -> `GSBER = 'PFF'`
- `bseg-uzawe = 'OP'` -> `GSBER = 'OPF'`
- `bseg-uzawe = 'GE'` -> `GSBER = 'GEF'`

### 2.4 Exit `U917`: Bank & SCB Indicator Validation
**Logic**: Validates the State Central Bank (SCB) indicator (`LZBKZ`) against the vendor's bank country (`BANKS`). 
- If `LZBKZ` is missing, it checks custom table `YTFI_PPC_STRUC`. If a record exists for the bank country with `PPC_VAR` or `PPC_DESCR`, the validation fails (`b_result = b_false`).
- **Registered as:** `VALID='UNES'` BOOLCLASS=009 VALSEQNR=012, CONDID=`1UNES###009` (invoice TCODE list + KOART='K'), CHECKID=`2UNES###009` (`=U917`)
- **Fires on:** invoice-entry TCODEs only (FB01, FB41, FB60, FB65, FBA6, FBR2, MIR7, MIRO, FBV0, FBVB, F-47) with invoice BLART (AP, CO, ER, IN, IT, KA, KR, KT, MF, MR, RE, RF, PS, PN) and vendor line (KOART='K'). **Does NOT fire on F-53 / FBZ2 manual payments, FB1K clearings, or SAPF124 auto clearings.**

### 2.5 Exit `U915`: Multi-Bank Vendor Validation
**Logic**: If the vendor has more than one bank account in `LFBK` and no partner bank type (`BVTYP`) is specified on the line, validation fails. Forces users to disambiguate which bank account to pay when a vendor has multiple. Skips BSCHL=26 and BSCHL=39 (down-payment clearing).
- **Registered as:** `VALID='UNES'` BOOLCLASS=009 VALSEQNR=011, CONDID=`1UNES###011` (same invoice TCODE list + KOART='K' as U917), CHECKID=`2UNES###011` (`=U915`)
- **Fires on:** same invoice-entry TCODEs as U917.
- **Does NOT check XREF fields.** This is a bank-account-mechanics validation, not an office-attribution validation.

### 2.6 Exit `U916`: Fund GL Restriction
**Logic**: Restricts which HKONT values are allowed when `FISTL='UNESCO'` (for most) or `GEBER='185GEF0006'` (for GEF fund). Returns `b_false` if the combination is not in the whitelist.
- **Registered as:** `VALID='UNES'` VALSEQNR=009, CHECKID=`2UNES###012` (`=U916`), severity `I` (information message only, not blocking)
- **Fires as an info message** — does not stop posting, just logs.

### 2.7 The XREF Office-Tagging trio: `UXR1` / `UXR2` / `UZLS` — *previously missing from this autopsy*

**Discovered during:** INC-000005240 (Session #051) investigation
**File range:** `YRGGBS00_SOURCE.txt:230-243` (exit registration), `:996-1119` (form bodies)

This trio implements the UNESCO **office-code tagging** on FI vendor lines — an independent mechanism from the BA/Fund derivation documented in §2.1-§2.3. The three exits form a chain:

```
Posting event (any FI TCODE in UNES)
  ↓
Step 005 — UXR1 writes BSEG-XREF1
  ↓
Step 006 — UXR2 writes BSEG-XREF2 (only when blank)
  ↓
Step 007 — UZLS reads BSEG-XREF2, writes BSEG-ZLSCH (payment method)
```

**All three are registered as GB922 steps of `SUBSTID='UNESCO'` (callpoint 3, complete document).**

#### 2.7.1 `UXR1`: Write `BSEG-XREF1` from user parameter

**Source (`YRGGBS00_SOURCE.txt:996-1016`):**

```abap
FORM uxr1 USING bseg_xref1 LIKE bseg-xref1.
*     if bseg_xref1 = space.        " GUARD COMMENTED OUT — UXR1 always overwrites
    CLEAR usr05.
    SELECT SINGLE * FROM usr05
           WHERE bname = sy-uname
             AND parid = 'Y_USERFO'.
    IF sy-subrc IS INITIAL.
        bseg_xref1 = usr05-parva.   " ← writes the posting user's office code
        SELECT SINGLE * FROM yfo_codes WHERE focod = bseg_xref1.
        IF sy-subrc <> 0.
            MESSAGE w018(zfi) WITH bseg_xref1.   " non-blocking warning
        ENDIF.
    ENDIF.
ENDFORM.
```

**Logic:**
- Reads `USR05.PARVA` WHERE `BNAME=SY-UNAME AND PARID='Y_USERFO'`
- **Unconditionally writes** the value to `BSEG-XREF1` (the original `IF bseg_xref1 = space` guard at line 998 is commented out — the form overwrites even user-typed values)
- Validates the written value against the `YFO_CODES.FOCOD` whitelist
- Raises `w018 ZFI` **warning** (non-blocking) if the code is not in the dictionary

**Empirical firing pattern (from INC-000005240):**
- Fires on EVERY BSEG line at callpoint 3 (complete doc), including both vendor lines AND bank GL lines. Proven via CDPOS on AL_JONATHAN's doc 3100003438 line 001 (BSAS bank GL) which had `VALUE_OLD='HQ'` at the moment of post-hoc FBL3N change, despite being a non-vendor line.
- On F110 automatic payment, UXR1 does NOT fire on the bank GL line (empirically observed — blank on 2 F110 clearing docs). The mechanism for this F-53 vs F110 asymmetry is NOT explained by standard GGB1 tables (GB905/GB921 are empty at UNESCO).

#### 2.7.2 `UXR2`: Write `BSEG-XREF2` (asymmetric: permissive auto-write, strict manual-input)

**Source (`YRGGBS00_SOURCE.txt:1024-1041`):**

```abap
FORM uxr2 USING bseg_xref2 LIKE bseg-xref2.
    IF bseg_xref2 = space.              " user did not type anything
        CLEAR usr05.
        SELECT SINGLE * FROM usr05
               WHERE bname = sy-uname
                 AND parid = 'Y_USERFO'.
        IF sy-subrc IS INITIAL.
            bseg_xref2 = usr05-parva.   " ← auto-write, NO validation
        ENDIF.
    ELSE.                               " user typed a value
        SELECT SINGLE * FROM yfo_codes WHERE focod = bseg_xref2.
        IF sy-subrc <> 0.
            MESSAGE e018(zfi) WITH bseg_xref2.  " ← HARD error, stops posting
        ENDIF.
    ENDIF.
ENDFORM.
```

**The asymmetry is critical:**
- **SPACE branch (auto-write from `USR05`):** no YFO_CODES validation → trusts USR05 value blindly. A bad `Y_USERFO` parameter in user master will be written to `XREF2` without any check.
- **ELSE branch (user manually typed):** hard error if the code is not in YFO_CODES → posting is blocked.

**Result:** UXR2 protects against manual typing errors but NOT against wrong master data. This is why AL_JONATHAN's wrong `Y_USERFO='HQ'` was silently propagated: F-53 hides XREF2 on the screen → UXR2 always takes the SPACE branch → no validation.

#### 2.7.3 `UZLS`: Derive `BSEG-ZLSCH` from `BSEG-XREF2` per company code

**Source (`YRGGBS00_SOURCE.txt:1090-1118`):**

```abap
IF bseg-xref2(4) <> 'UNDP'.
    CASE bseg-bukrs.
        WHEN 'UNES'.  IF bseg-xref2 <> 'HQ'        → bseg_zlsch = 'O'. ENDIF.
        WHEN 'UBO'.   IF bseg-xref2 <> 'BRZ'       → bseg_zlsch = 'O'. ENDIF.
        WHEN 'UIS'.   IF bseg-xref2 <> 'UIS'       → bseg_zlsch = 'O'. ENDIF.
        WHEN 'IBE'.   IF bseg-xref2 <> 'IBE'       → bseg_zlsch = 'O'. ENDIF.
        WHEN 'IIEP'.  IF bseg-xref2 <> 'IIEP_PAR'  → bseg_zlsch = 'O'. ENDIF.
    ENDCASE.
ELSE.
    bseg_zlsch = 'U'.      " UNDP transfers get ZLSCH='U'
ENDIF.
```

**Logic:**
- Reads `BSEG-XREF2` (already written by UXR2) and derives `BSEG-ZLSCH` (payment method)
- For UNES, `XREF2='HQ'` keeps ZLSCH at default; any non-HQ value forces `ZLSCH='O'` (field-office outbound)
- Special case: `XREF2(4)='UNDP'` (UNDP transfers) always get `ZLSCH='U'`

**Business impact:** UZLS is the **downstream consumer** of UXR2's output. Whatever office code is written to XREF2 drives payment method routing at F110/BCM time. A wrong XREF2 does not just mis-tag the line for reporting — it **mis-routes the payment** (HQ payment method vs field-office payment method).

#### 2.7.4 The `Y_USERFO` parameter and `YFO_CODES` dictionary

- **`USR05.PARID='Y_USERFO'`** — SU3 user parameter. Free-text, 20-char maximum. Contains the office code (2-4 chars typically: `HQ`, `JAK`, `YAO`, `KAB`, `DAK`, `BRZ`, `IIEP_PAR`, `UIS`, `IBE`). Maintained per-user via SU01/SU3. **Not synchronized with HR master** (`PA0001.WERKS/BTRTL`) — a user's office can drift from their HR-assigned personnel area.
- **`YFO_CODES`** — UNESCO custom table. Minimum fields: `FOCOD` (office code), `PAYMT` (payment method). Serves as the whitelist dictionary for YFO codes. Maintained by UNESCO BASIS via SM30.

#### 2.7.5 Validation gap — XREF is never checked

Of the 12 steps in `VALID='UNES'` (GB93/GB931), **NOT ONE references `BSEG-XREF1` or `BSEG-XREF2`** at either the CONDID or CHECKID level. The only XREF reference in the entire validation rule set is step 010 which checks `BSEG-XREF3` for customer expense-type memos (`OFFICE RENT`, `PARKING RENT`, `TELEPHONE`, ...).

**`U915` and `U917`** — the two validation exits that fire on invoice vendor lines — check bank account mechanics (multi-bank and SCB indicator), NOT XREF content.

**`F-53` and `FBZ2`** (manual outgoing payments) appear in ZERO UNES validation prerequisites. Manual outgoing payments pass through the UNES validation layer completely uncovered.

#### 2.7.6 Scale of the downstream manual workaround

Because no validation catches wrong XREF values, UNESCO users have adopted post-posting manual correction via `FBL3N` / `FBL1N` / `FB02` as a de-facto validation layer. Measured scale in Q1 2026:

- **21,754 manual edit events** on UNES BELEG documents
- **242 distinct users** performing the edits
- **24,597 distinct UNES FI documents** touched
- Top editor: `C_VINCENZI` 2,075 FBL1N edits. Other notable editors: `R_MUSAKWA` 1,422 (FBL3N + FB02), `M_AHMADI` 550 FBL3N, `A_HIZKIA` 932 FBL3N (known Jakarta user, manually fixing AL_JONATHAN's docs)

**This is the operational cost of the XREF validation gap** — the business has been absorbing it via human labor for years.

#### 2.7.7 Cross-references

- **Incident:** [INC-000005240](../../incidents/INC-000005240_xref_office_substitution.md) — AL_JONATHAN's Jakarta office case; fills the historical gap on UXR1/UXR2/UZLS knowledge
- **Related Treasury doc:** [xref_office_tagging_model.md](../../Treasury/xref_office_tagging_model.md) — end-to-end model, TCODE coverage matrix, Payment domain view
- **Related FI doc:** [ggb1_substitution_tables_distinction.md](../../FI/ggb1_substitution_tables_distinction.md) — GGB1 table distinctions, updated with GB93/GB931 findings
- **Feedback rule:** `feedback_psm_extensions_is_fi_substitution_home` — read this doc at the start of any FI substitution/validation incident

---

## 2.8 How this section relates to the older sections (§2.1-§2.6)

Sections §2.1-§2.6 cover the **BA / Fund / Cost-Center derivation** side of the YRGGBS00 form pool (UAEP, UATF, U904, U917, U915, U916). Section §2.7 covers the **XREF Office-Tagging** side (UXR1, UXR2, UZLS). Both families live in the same form pool and share the same USR05-based user parameter pattern, but they target different fields and have different consumers.

**If an incident touches any of: `BSEG-XREF1`, `BSEG-XREF2`, `BSEG-ZLSCH`, `Y_USERFO`, `YFO_CODES`, or office-code tagging → read §2.7 first, then §2.1-§2.6 for framework context.**

## 3. The Custom "BASU" Framework (`YFI_BASU_MOD`)
While standard substitutions use `GGB1`, Business Area mapping for G/L accounts is managed via **`YCL_FI_ACCOUNT_SUBST_READ`**.

### 3.1 Runtime Logic (Method `READ`)
```abap
SELECT DISTINCT bukrs, blart, gsber FROM ytfi_ba_subst
  WHERE bukrs = @iv_bukrs AND blart = @iv_blart AND sign <> @space ...
LOOP ...
  IF iv_hkont IN lt_hkont_range. 
    rv_gsber = ls_subst-gsber. EXIT.
  ENDIF.
ENDLOOP.
```
**Fallback Sequence**:
1. Search by `Company Code` + `Document Type` + `Account Range`.
2. Search by `Company Code` + `Global (Space)` + `Account Range`.

## 5. The "Super-User" Backdoor: `YXUSER` Exclusion
A critical architectural finding is the implementation of a "User-Level Bypass" mechanism. Many of the most restrictive force-mapping routines in `YRGGBS00` (specifically for Assets) start with a check against custom table **`YXUSER`**.

### 5.1 Bypass Mechanism
```abap
SELECT SINGLE * FROM yxuser
  WHERE xtype = 'AF'  " or 'AA'
  AND uname = sy-uname.
CHECK sy-subrc <> 0.  " If user found (subrc=0), SKIP the entire routine.
```

### 5.2 Categories of Exclusion (`XTYPE`)
| XTYPE | Context | Impact of Entry |
| :--- | :---: | :--- |
| **`AF`** | Assets Expenses (`UAEP`) | User can post asset expenses without mandatory Fund/CC force-mapping. |
| **`AA`** | Assets Technical (`UATF`, `NSAI`) | User can post technical asset documents **without clearing the WBS element**. |

### 5.3 Purpose & Risk
*   **Operational Context**: This is likely used for **Batch Users** or **Interface ID** (e.g., legacy migration tools or third-party integrations) that require the ability to post with specific, non-standard account assignments.
*   **Audit Risk**: This creates an "Open Door." Any user added to `YXUSER` by a functional administrator can bypass the hardcoded fiscal year and fund-center guardrails defined in the routine pool. In a "Headless" or "React-Clone" environment, this table must be monitored to determine which users can perform non-standard postings.

## 6. Conclusion
The UNESCO posting perimeter is defined by a mix of standard GGB0/GGB1 configurations and hardcoded ABAP exits. The most significant "dots" are the link between **Business Area and Fund** and the **Automatic Clearing of WBS Elements** for technical funds, unless the user is specifically exempted via **`YXUSER`**.
