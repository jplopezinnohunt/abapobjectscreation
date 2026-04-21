# Session #058 Retro — INC-000006906 Closure + Bank Reconciliation Family Inventory

**Session #:** 058
**Date:** 2026-04-20
**Topic:** INC-000006906 Maputo MZN bank reconciliation TIME_OUT — root cause
finalization, network-axis field reproduction, fix proposal, and full
inventory of UNESCO's custom bank-reconciliation program family (15 programs
across 3 families).
**Duration:** multi-session investigation across #056 → #057 → #058.
**Primary author:** main agent execution (no subagent delegation per
`feedback_main_agent_holds_incident_context`).

---

## 1. Outcomes

### Shipped
- **INC-000006906 resolved (fix proposed):** TIER_1 root cause identified at
  `YTBAE002.abap:27`. Fix file `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`
  (one-character change `'E'` → `'N'`). Blast radius: zero behavioral change
  on happy path.
- **Canonical incident doc simplified (#058):** reduced from 529 → 145 lines;
  full narrative preserved at `knowledge/incidents/INC-000006906_full_history.md`
  per CP-001 (nothing deleted, only relocated).
- **Treasury domain doc created:**
  `knowledge/domains/Treasury/bank_reconciliation_program_inventory.md` (287
  lines) — full 15-program inventory (YTBAI001 + YTBAE001/_HR/002 + YTBAM001-004
  + HR variants + _HR_UBO + YFI_BANK_RECONCILIATION + DATA + SEL), author
  history, TBTCO job evidence, MODE 'E' scan, empty-range scan, HR-fork
  explanation.
- **Bank recon skill upgraded:** `.agents/skills/sap_bank_statement_recon/SKILL.md`
  now includes "UNESCO Custom Recon Programs (Y-Stack)" section with TCODE
  map (YTR0/1/2/2_HR/3/YFI_BANK1) and 6 anti-pattern rules (R1-R6) for new
  recon programs — distilled from INC-000006906.
- **Extracted source preserved:** 15 folders in
  `extracted_code/CUSTOM/BANK_RECONCILIATION/` with per-program source +
  `_manifest.json` + top-level `_family_inventory.json`.

### Changed in brain
- **New incidents closed:** `INC-000006906` — status `RESOLVED_FIX_PROPOSED`,
  TIER_1 confirmed by three-path field reproduction (VPN / Paris / Maputo).
- **New claims:** 52 (YBANK set coverage gap, 233 of 383 HKONTs, PREVENTIVE),
  53 (empty-range → unbounded LDB scan, LATENT on YTBAE002), 54 (MODE 'E'
  BDC + slow WAN → network-coupled TIME_OUT, PRIMARY root cause).
- **New objects (~+30 across #056-#058):** `YTR3`, `YTBAE002` (was partial,
  now fully annotated), `YTBAE001`, `YTBAE001_HR`, `YTBAI001`,
  `YTBAM001/002/002_HR/002_HR_UBO/003/003_HR/004/004_HR`,
  `YFI_BANK_RECONCILIATION` (+ `_DATA` + `_SEL`), `YCL_FI_BANK_RECONCILIATION_BL`
  (referenced, not yet extracted — KU-2026-057-03), `SAPDBSDF`, `PUT_BSIS`,
  `SKB1`, `FB08`, `F-04`, `FBRA`, `YBANK_ACCOUNTS_FO_OTH` (+ the broader YBANK_*
  set family).

---

## 2. Root Cause Summary (for next-session context)

`YTBAE002.abap:27` declares `CONSTANTS: GC_MOD TYPE C VALUE 'E'`. The program
issues four `CALL TRANSACTION ... USING BDCDTAB MODE GC_MOD` to standard FI
clearing TCODEs `FB08` (`:723, :853`), `F-04` (`:771`), `FBRA` (`:819`)
inside the `GET bsis` / `LDB_PROCESS` loop started at `:1509`. MODE `'E'`
opens SAPGUI on BDC error. On slow WAN paths (Maputo), each handshake
consumes seconds; cumulative dialog time exceeds `rdisp/max_wprun_time`
and the dispatcher aborts the caller at `SAPDBSDF:1983 PUT_BSIS`. Fix:
change `'E'` → `'N'` at line 27. Errors already captured via
`MESSAGES INTO Y_MESSTAB` + `PROC_RECONCIL_MESS_ADD` (:754, :795, :840, :874)
→ rendered in list output at `:2600-2616`. No error visibility lost.

**Field reproduction (TIER_1 promotion evidence):** user ran same program
from (a) HQ corporate VPN — OK ~2 s; (b) Paris HQ LAN — OK ~2 s;
(c) Maputo direct — TIME_OUT. Binary correlation with network path.

---

## 3. Behavioral Learnings (Phase 4b — MANDATORY)

### What did we learn about SAP that the next agent needs to know?

1. **MODE 'E' CALL TRANSACTION inside an LDB / GET / recon loop is a new
   named anti-pattern at UNESCO ("MODE 'E' BDC + slow-WAN network coupling").**
   It is indistinguishable from a data-volume TIME_OUT in the ST22 stack —
   the dump points at the LDB's SELECT, not at the true consumer (the
   CALL TRANSACTION in the caller). This failure mode is silent on HQ/LAN
   and fatal on field-office WAN. Promote as Claim 54 (TIER_1). See
   `feedback_mode_e_bdc_is_network_coupling_risk` (new rule, added #058).

2. **D01 HTTP Basic ADT was locked for JP_LOPEZ during #057; the
   workaround was P01 SNC/SSO + `RPY_PROGRAM_READ`.** Same source code is
   visible in both systems (P01 and D01 stayed in sync via transport).
   When ADT 401s, fall back to P01 RFC — do NOT retry ADT in a loop.
   Promote as `feedback_d01_adt_locked_use_p01_rfc` (new rule).

3. **TIME_OUT stack frames often blame the LDB but the cumulative time is
   consumed elsewhere.** `PUT_BSIS:1983` is SAP-standard code. Before
   filing a "LDB performance bug" or a "result set too large" interpretation,
   look at what the CALLER was doing in the same work process: did it
   issue `CALL TRANSACTION ... MODE 'E'`? Did it `COMMIT WORK AND WAIT`?
   Did it hit an RFC that roundtripped? These all drain WP time while the
   stack sits idle in the LDB's SELECT. Promote as
   `feedback_time_out_stack_blames_ldb` (new rule).

4. **UNESCO has N custom recon programs across 3 families** (YTBAE/YTBAM
   action-stack from 2001, YFI_BANK_* read-only OOP view from 2023,
   YTBAI001 file converter from 2001). The YTBAE / YTBAM family has
   parallel HR forks from 2007 authored by A_AHOUNOU, and a second-order
   fork for UBO field office in 2008 by D_SIQUEIRA — 3 parallel copies of
   essentially-the-same BDC chain. Any defect in that chain needs to be
   fixed in up to 3 places.

5. **`YFI_BANK_RECONCILIATION` is NOT a superseder of YTBAE002.** Different
   design (read-only ALV OOP class, `P_DETAIL` / `P_DASH` modes, no BDC,
   no LDB). YTBAE002 still does the clearing actions; YFI_BANK1 shows
   status. They coexist.

6. **TCODE `YTR3` binds directly to `YTBAE002`** (no variant) per TSTC. The
   variant pattern on YTR1/YTR2 is a legacy style; YTR3 drops it.

7. **BSIS volume for J_DAVANE's plausible input was trivially small** (13
   rows on `0001194424`). Data volume was never the failure axis —
   network was. Falsified all 7 Pivot-2 hypotheses.

### Did any annotation contradict a previous one?

Yes — Claim 53 was initially promoted to "root cause" in Session #057,
then demoted to "latent defect" in Session #058 when field reproduction
isolated network as the decisive axis. Claim 53 record carries
`superseded_as_root_cause_by: claim-006906-mode-e-bdc-network-coupling`
but remains ACTIVE as a real code bug pattern.

### New SAP tables / classes cited but not yet extracted → KU

- `YCL_FI_BANK_RECONCILIATION_BL` — referenced but OOP source not extracted.
  **KU-2026-057-03.**
- `TSAKO` — config table driving YTBAE001's BSIS selection (`YTBAM003.abap:53-59`).
  Not in Gold DB. **KU-2026-058-02 (new).**
- `YFO_CODES` — confirmed present in P01 during H48, not yet in Gold DB.
  Pre-existing KU-027.

---

## 4. Pivot Mistakes (CP-001 — preserve the lesson)

The investigation pivoted 4 times before landing on the right mechanism.
Preserved verbatim so the next session sees the reasoning path, not just
the answer:

1. **Pivot 1 — "ALV download failure" hypothesis.** User said "downloading
   MZN bank reconciliation"; translated to ALV spool export. Falsified
   when dump arrived showing TIME_OUT in LDB, not a spool error.
2. **Pivot 2 — `YFI_BANK_RECONCILIATION` cluster.** Gold DB CTS suggested
   YFI_BANK1 as the most recent recon program. Ranked 7 dump candidates
   from its method names (GET_DELAY ZERODIVIDE, PREPARE_DETAILED_DATA
   memory, etc.). **All 7 falsified by the actual dump (YTBAE002, not
   YFI_BANK_RECONCILIATION).**
3. **Pivot 3 — "pull J_DAVANE execution logs."** Gold DB freshness gap
   disclosed: `BKPF.CPUDT` stops 2026-03-16, entire incident window is
   post-extract. Had to go to live RFC.
4. **Pivot 4 — ST22 screenshot arrived → correct TCODE (`YTR3`) and
   program (`YTBAE002`).** Falsified Pivot 2 entirely.
5. **Pivot 5 — YBANK set coverage hypothesis.** Claim 52 (233 HKONTs
   outside YBANK coverage) was initially promoted as causal. Grep of the
   3,422-line YTBAE002 corpus returned zero `RS_SET_VALUES_READ` /
   `G_SET_GET_ALL_VALUES` hits — YTBAE002 resolves scope via SKB1, not
   Report-Painter sets. Demoted to "preventive audit, orthogonal."
6. **Pivot 6 — empty-range latent (`:1366`).** Session #057 briefly
   treated this as root cause. Demoted #058 when SKB1 returned non-empty
   `GR_SAKNR_OI` for the user's actual input.
7. **Pivot 7 (final) — three-path field reproduction.** User ran
   same-program-same-data from VPN / Paris / Maputo. Binary correlation
   with network path isolated MODE 'E' network coupling as the decisive
   mechanism.

**Lesson:** when a stack frame points at SAP-standard code (`SAPDBSDF`,
`SAPLKKBL`, `CL_GUI_ALV_GRID`), resist the urge to treat the pointer as
the cause. Trace back to the WP's caller. This entire 4-pivot chain could
have been shortened if the pattern "MODE 'E' in BDC loop on WAN" were
already in the brain — now it is (Claim 54 + feedback rule).

---

## 5. SAP Learnings This Session (Phase 4b checklist)

- [x] Tables/classes where a prior assumption was wrong: yes — `PUT_BSIS`
      dump-hint text misleads; corrected in Claim 54.
- [x] UNESCO-specific behaviour not in rules/domains: yes — MODE 'E' BDC
      network coupling; promoted to new feedback rule.
- [x] Annotations that contradict previous ones: yes — Claim 53 demoted
      from root cause to latent (superseded_as_root_cause_by Claim 54).
- [x] Tables cited but not in Gold DB: `YFO_CODES`, `TSAKO`, `TSTC` (legacy).
      Already in existing KUs.
- [x] Classes cited but not extracted: `YCL_FI_BANK_RECONCILIATION_BL` — KU-057-03.
- [x] Missing feedback rule: yes — 3 added this session (see §7).
- [x] CLAUDE.md updates needed: **no** — the new rules are discoverable
      via the skill + brain_state. CLAUDE.md already references Phase 4b
      and the incident analyst pathway.

---

## 6. PMO Follow-ups (transferred to PMO_BRAIN.md)

- **KU-2026-057-01** — YTBAI001 (SMARTLINK) still in production?
- **KU-2026-057-02** — STAD trace YTR1 / YTR2 / YTR2_HR to propose
  decommission.
- **KU-2026-057-03** — Extract `YCL_FI_BANK_RECONCILIATION_BL`.
- **KU-2026-057-04** — `YTBAM002_HR_UBO` housekeeping TADIR-delete.
- **KU-2026-058-01** — MT940 feed status for ECO09/MZ banks (structural).
- **KU-2026-058-02** — `TSAKO` extraction to Gold DB.
- **Dormant MODE 'E' watch (latent):** `YTBAE001.abap:118` +
  `YTBAE001_HR.abap:122` carry the same `C_MOD='E'` pattern via
  includes YTBAM002 + YTBAM002_HR. User decision Session #058 was NOT to
  fix today (both executables dormant, no TBTCO runs). Preserved as
  landmine — if KU-2026-057-02 confirms zero interactive usage, propose
  decommission; if non-zero, apply the same one-char fix.

---

## 7. Feedback Rules Added This Session

1. `feedback_mode_e_bdc_is_network_coupling_risk` — severity HIGH. When
   encountering `CALL TRANSACTION ... MODE 'E'` in custom code, flag for
   field-office WAN risk; use MODE 'N' + `MESSAGES INTO` instead.
2. `feedback_d01_adt_locked_use_p01_rfc` — severity MEDIUM. When D01 ADT
   HTTP Basic 401s, don't retry — P01 SNC/SSO + `RPY_PROGRAM_READ` sees
   the same source.
3. `feedback_time_out_stack_blames_ldb` — severity MEDIUM. TIME_OUT dumps
   in SAPDBSDF / similar LDB callbacks often misdirect; inspect the
   caller's activity in the same WP before hypothesizing LDB tuning.

See `brain_v2/agent_rules/feedback_rules.json` for full definitions.

---

## 8. Closure State

- Canonical doc: 145 lines · ≤150 target · CP-001 preserved via
  full-history sibling (550 lines).
- Treasury inventory: 287 lines · full family table + anti-pattern scan.
- Skill: 677 lines · R1-R6 added, TCODE map present.
- Brain: 3 new claims (52, 53, 54) · +~30 objects across #056-#058 · 1
  incident RESOLVED_FIX_PROPOSED · 3 new feedback rules · 5 open KUs.
- Fix: written, awaiting user transport action.
- Next-session handoff: no code work pending on INC-000006906 until DBS
  transports the fix and J_DAVANE retests.
