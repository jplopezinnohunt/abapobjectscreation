# INC-000006906 — Maputo MZN Bank Reconciliation: YTR3/YTBAE002 TIME_OUT

**Status:** `RESOLVED_FIX_PROPOSED` · TIER_1 (field-reproduced) · one-char fix written
**Received / Dump / Resolved:** 2026-04-16 · 2026-04-20 13:51:49 · Session #058
**Reporter = Affected user:** Josina Davane (`J_DAVANE`, FU/MAP, Maputo field office)
**Domain:** Treasury / Bank Reconciliation / ABAP Custom / Runtime Performance
**Full history (pivots, appendices, old §3 deep dive):** [INC-000006906_full_history.md](INC-000006906_full_history.md)

---

## Executive Summary

On 2026-04-20 13:51:49, P01 client 350, Maputo accountant `J_DAVANE` ran
transaction **`YTR3`** (custom bank-reconciliation posting program
**`YTBAE002`**, package `YA`, 3,422 lines). Her dialog aborted with runtime
error **`TIME_OUT`** at `SAPDBSDF:1983 form PUT_BSIS`. Root cause is
UNESCO-owned at `YTBAE002.abap:27`: `CONSTANTS: GC_MOD TYPE C VALUE 'E'`. The
program issues four `CALL TRANSACTION ... MODE GC_MOD` to `FB08` / `F-04` /
`FBRA` inside the `GET bsis` / `LDB_PROCESS` loop. MODE `'E'` means
"display on error — open SAPGUI". On the Maputo WAN each BDC-error handshake
consumes seconds; cumulative dialog time breaches `rdisp/max_wprun_time` and
SAP aborts the caller in its LDB fetch. From HQ (fast LAN) the same program
runs in ~2 s — user-reproduced three-path test (VPN OK / Paris OK / Maputo
TIMEOUT) isolates network as the decisive axis. **Fix: change `'E'` to
`'N'` at `YTBAE002.abap:27`.** Errors stay visible (see §3); no behavioral
regression. Fix file: `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`.

---

## §1. Dump Evidence

```
Runtime error ........ TIME_OUT
Program .............. YTBAE002
Include .............. SAPDBSDF  Line 1983  Form PUT_BSIS
User ................. J_DAVANE   Client 350 (P01)
Date / time .......... 2026-04-20 13:51:49
```

TIER_1 source: user-provided ST22 screenshot. The dump's "result set too large"
note text misleads — `PUT_BSIS:1983` is SAP-standard code; the caller
(YTBAE002) is what consumed the work-process clock.

---

## §2. Root Cause — MODE 'E' BDC + Slow WAN

- **Constant:** `YTBAE002.abap:27` — `CONSTANTS: GC_MOD TYPE C VALUE 'E'`.
- **Four BDC sites** (all inside the LDB_PROCESS iteration started at
  `:1509`): `FB08` `:723`, `F-04` `:771`, `FBRA` `:819`, `FB08` `:853`. Each
  uses `MODE GC_MOD` + `MESSAGES INTO Y_MESSTAB`.
- **Silent-capture path already wired:** `PROC_RECONCIL_MESS_ADD` at
  `:754 / :795 / :840 / :874` copies `Y_MESSTAB` into `GT_RECONCIL_MESS`.
  The `'E'` adds a GUI handshake on top of (redundant with) this capture.
- **Field reproduction (TIER_1):** VPN works, Paris HQ works, direct Maputo
  fails with TIME_OUT. Same program, same data, only network path differs.

Mechanism: per BDC error, SAPGUI opens on the user workstation → Maputo RTT
hundreds of ms per round-trip → cumulative dialog time > `rdisp/max_wprun_time`
→ dispatcher aborts at whatever SELECT the work-process is waiting in
(`SAPDBSDF:1983` here). The LDB stack frame is a symptom, not a cause.

Code anchors: `YTBAE002.abap:27, :723, :771, :819, :853, :754, :795, :840, :874, :1509`.

---

## §3. Fix

**Path:** `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap` · **Change:** `YTBAE002.abap:27` `'E'` → `'N'` (one character).

Rollout: (1) apply on D01 SE38 `YTBAE002:27`, activate, transport of copies pkg `YA`; (2) unit-test on D01 from VPN/slow-WAN — errors render in list output `YTBAE002.abap:2600-2616`; (3) release to P01, ask J_DAVANE to retry, monitor ST22 on `SAPDBSDF:1983` for one week.

**Error visibility preserved.** MODE `'N'` runs BDC silently; every message
previously shown in the pop-up is still captured in `Y_MESSTAB` →
`GT_RECONCIL_MESS` → list output lines `:2600-2616` with TCODE
(`FB08`/`F-04`/`FBRA`), severity (`E`/`W`/`S`), and full SAP message text.
Net delta: the only loss is the rarely-usable "fix-in-the-popup" workflow.

---

## §4. Latent Defects Preserved (NOT causal for this incident)

- **Empty-range → unbounded LDB scan** at `YTBAE002.abap:1366-1370`
  (`LOOP AT LR_SAKNR ... APPEND PT_COSEL` with no `IS NOT INITIAL` guard).
  Did not fire here because J_DAVANE's ECO09/MZN01 input returns a
  non-empty `GR_SAKNR_OI` from SKB1 at `:1098-1127`. Tracked as **Claim 53**.
- **Bank GL not in any YBANK_* set** — 233 of 383 distinct T012K HKONTs
  (60.8%) at UNESCO are outside `YBANK_*` SETLEAF coverage. Orthogonal
  to YTBAE002 (it resolves scope via SKB1, not Report-Painter sets).
  Preventive audit. Tracked as **Claim 52**.

---

## §5. Class Generalization

- **Class A — MODE 'E' BDC in network-sensitive loops** (PRIMARY, new,
  Claim 54). Canonical instance = this incident. Dormant siblings
  `YTBAE001.abap:118` + `YTBAE001_HR.abap:122` also carry the same pattern
  via `C_MOD='E'` but both are dormant TCODEs (YTR1/YTR2/YTR2_HR with
  zero recent executions). **User decision Session #058: do NOT spend a
  transport slot on dormant siblings today.** Retained as latent landmines
  — see H48/H53 in PMO.
- **Class B — YBANK set coverage audit** (PREVENTIVE, Claim 52). Check
  script: `Zagentexecution/quality_checks/ybank_set_coverage_check.py`.
- **Class C — empty-range → unbounded LDB scan** (LATENT, Claim 53).
  Check: `Zagentexecution/quality_checks/empty_range_ldb_scan_check.py`.

Full family inventory (15 programs, 3 families): see Treasury doc in §7.

---

## §6. Open Known-Unknowns

- **KU-2026-057-01** — YTBAI001 (SMARTLINK CMI940 → MT940): still in production?
  File paths point to `/usr/sap/D01/conversion/...`; TBTCO has zero runs.
- **KU-2026-057-02** — STAD trace for YTR1 / YTR2 / YTR2_HR to confirm zero
  interactive use before decommission proposal.
- **KU-2026-057-03** — Extract `YCL_FI_BANK_RECONCILIATION_BL` (2023 OOP
  class backing `YFI_BANK1`) for autopsy.
- **KU-2026-057-04** — `YTBAM002_HR_UBO` housekeeping: not included by any
  executable today; candidate for TADIR-delete.
- **KU-2026-058-01** — MT940 feed status for ECO09/MZ banks (BST01 stopped
  2025-04-17, ECO09/UBA01 zero FEBKO rows ever). Structural, preserved
  for Treasury business decision.

---

## §7. Artifacts Index

| Artifact | Path |
|---|---|
| Fix file (one-char change + rollout) | `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap` |
| Custom program source (3,422 lines) | `extracted_code/CUSTOM/YTBAE002/YTBAE002.abap` · mirror `extracted_code/CUSTOM/BANK_RECONCILIATION/YTBAE002/` |
| Bank recon family inventory (15 programs) | `knowledge/domains/Treasury/bank_reconciliation_program_inventory.md` |
| Bank recon skill (TCODE map, R1-R6 rules) | `.agents/skills/sap_bank_statement_recon/SKILL.md` |
| Brain claims | `brain_v2/claims/claims.json` — id 52 (YBANK coverage), 53 (empty-range), 54 (MODE 'E') |
| Brain incident record | `brain_v2/incidents/incidents.json` — `INC-000006906` |
| Intake JSON | `Zagentexecution/incidents/INC-000006906_intake.json` |
| Source email (user-provided) | `C:\Users\jp_lopez\Downloads\Ticket INC-000006906_ ...eml` |
| Full pivot history + appendices (this incident, pre-simplification) | `knowledge/incidents/INC-000006906_full_history.md` |

---

**Closure:** fix proposed, user-validated three-path reproduction, awaits
DBS transport and J_DAVANE P01 retest. Brain rebuild runs at session close.
