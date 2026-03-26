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
