---
name: PA0105-0001 SAP-user link sync (P01 -> D01/V01)
description: Replicate the PERNR->SAP-user communication infotype (PA0105 subtype 0001) from P01 into D01/V01 for employees that have a SAP user in production but are missing the link in the target. Fixes the staff-time-distribution "SaveFormData writes only if it finds the user" gap.
type: project
created: 2026-07-03
evidence_tier: TIER_1
domain: HCM / Integration / BCM staff-time-distribution
---

# PA0105 subtype 0001 (SAP system user link) sync — P01 -> D01/V01

## Problem
The staff-worktime-distribution upload (`YFMOUTPUT` / SaveFormData) looks up an employee's SAP
user from **PA0105 subtype 0001** (PERNR -> SY-UNAME / BNAME). When that infotype is absent in
D01/V01 the lookup fails and the slot never fills. Many D01/V01 employees that HAVE a SAP user in
P01 were missing this link.

## Ground truth (measured 2026-07-03, RFC over SNC SSO)
- P01 employees WITH PA0105-0001: **5,292** (source of truth).
- Field carrying the user = **USRID** (CHAR12, e.g. `A_COWLING`); `USRID_LONG` empty for these.
- The referenced SAP users already **exist in D01/V01 `USR02`** — only the infotype link was missing.
- Gap (exists in target, has P01 user, missing link): **D01 = 857/861 · V01 = 775**.

## Mechanism (reusable) — `pa0105_user_sync.py <D01|V01> <mode> [commit]`
Standard BAPI path (never direct table insert on HR infotypes):
`BAPI_EMPLOYEE_ENQUEUE` -> `BAPI_EMPLCOMM_CREATE`(SUBTYPE=`0001`, COMMUNICATIONID=`<P01 USRID>`,
VALIDITYBEGIN=`<P01 BEGDA>`, VALIDITYEND=`99991231`, NOCOMMIT=`X`) -> `BAPI_TRANSACTION_COMMIT` ->
`BAPI_EMPLOYEE_DEQUEUE`. Idempotent (skips PERNRs that already have the link); every write verified
by re-read. Source = P01 always; target parameterized. Modes: `golden` | `all` | `test:N` | `dry` |
explicit CSV of PERNRs.

## Result (executed 2026-07-03, commit=True)
- **D01: 855 created** (links 2,314 -> 3,173), remaining gap 2.
- **V01: 773 created** (links 4,267 -> 5,040), remaining gap 2.
- Golden 12: 12/12 in D01, 11/12 in V01 (`91036937` has no P01 source — `D_GRIGORIU` link exists only in D01).

## 4 non-copyable edge cases (real data conflicts, NOT tool failures)
A BNAME can be linked to only ONE PERNR. These users are already linked to a different employee in
the target, so the copy is refused by SAP — resolution is deciding which PERNR is correct, not copying:
- D01 `10005045` — `Y.BABIARD@GMAIL.COM` already used for another person number.
- D01 `10100301` — infotype UNCAUGHT_EXCEPTION (data-specific).
- V01 `10152769` — `X_LI` already used for PERNR 10052083.
- V01 `10158641` — `Z_LIU` already used for PERNR 10052474.

## Notes / constraints
- P01 is READ-ONLY (source). Writes only to D01/V01 (dev/validation).
- `FMFCTR` and some PA/OM tables are SAIS-wrapper-blocked via RFC (TABLE_WITHOUT_DATA / IN-clause
  parser errors) — read whole + filter in Python; avoid multi-condition/`IN` WHERE clauses.
