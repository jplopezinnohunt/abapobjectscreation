# Technical Autopsy: Fund & Account Assignment Validation (FM)

## Overview
- **Include**: [`ZXFMYU22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXFMYU22_RPY.abap)
- **Primary Objective**: Enforces organizational policy for budget consumption by validating the relationship between **Funds**, **Cost Centers**, **WBS Elements**, and **Business Areas**.

## 1. Budget Hierarchy Enforcement
The logic prevents users from using the wrong **Fund Center** based on the budget distributable sum (`RDSUM` from `BPJA` table).
- **Process**:
  1. Identifies the hierarchy level of the specified Fund Center (`FMHISV-HILEVEL`).
  2. Traverses the budget hierarchy to find the "Budget Carrying" node.
  3. If the user picks a Fund Center that has $0 available budget or is at the wrong hierarchy level, the system throws error `ZFI-009` and suggests the correct centers.

## 2. Fund Type & Object Restrictions
UNESCO uses a rigid mapping where certain Funds *only* allow WBS Elements, and others *only* allow Cost Centers.
- **WBS Only (Project-based)**:
  - Fund Types: `005`, `101` to `112`.
  - Constraint: Triggers error if `KOSTL` (Cost Center) is filled or `PS_PSP_PNR` (WBS) is empty.
- **Cost Center Only (Regular/Staff)**:
  - Fund Types: `099`, `299`, `399`.
  - Constraint: Triggers error if `PS_PSP_PNR` is filled or `KOSTL` is empty.

## 3. Business Area (GSBER) Hard-Wiring
The enhancement enforces a 1:1 relationship between Fund Groups and Business Areas:
- **`GEF`**: Required for Fund Types `001` - `099`.
- **`PFF`**: Required for Fund Types `100` - `199`.
- **`MBF`**: Required for Fund Types `200` - `299`.
- **`OPF`**: Required for Fund Types `300` - `399`.

## 4. Skip/Bypass Logic
The validation can be bypassed in specific scenarios:
- **User Parameters**: Users with PID `ZFMUCHK` = 'X' can skip these checks (for emergency adjustments).
- **Modules**: Travel (`TRVL`) and Asset Management (`AA`, `AF`) are explicitly checked for exclusion to allow their internal logic to handle assignments.

## 5. Metadata Dependencies
| Field | Table | Role |
| :--- | :--- | :--- |
| `FINCODE` | `FMFINCODE` | Source of the "Fund Type" classification. |
| `FIPEX` | `FMCI` | Identifies if the Commitment Item is a "30" (Expense) type. |
| `RDSUM` | `BPJA` | Provides the distributable budget amount for validation. |
| `HILEVEL` | `FMHISV` | Defines the position in the organizational hierarchy. |
