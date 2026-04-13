# UNESCO Budget Rate (BR) Custom Solution — Technical Autopsy

> **Status:** ✅ Complete — built from **live extraction** of class `YCL_FM_BR_EXCHANGE_RATE_BL` + all 8 enhancement implementations of `ZFIX_EXCHANGERATE` composite from D01 (2026-04-10). FB60 execution trace added Session #053. **Empirically confirmed Session #054** via JP_LOPEZ ST01 trace `fb602.txt` (TS3, 2026-04-13): 42 hits of `YCL_FM_BR_EXCHANGE_RATE_BL`, ALL going to `FMFINCODE` only, ZERO `TCURR` reads → `convert_to_currency` never invoked → `check_conditions` rejects USD on every line via the `mr_waers=['EUR']` gate. The hardcoded EUR-only currency range is the live root cause.

## 🔍 GATE ASYMMETRY — FULL 15-MEMBER MAP (Session #054, debugger-confirmed)

The composite `ENHC ZFIX_EXCHANGERATE` has **15 active members** + 1 BAdI implementation, NOT 8. They split into
**three camps** based on what `iv_waers` (or equivalent filter) is keyed on. The cross-currency bug is the
result of these camps disagreeing about what the "consumption currency" is.

### Camp A — FR-currency-anchored (key on the FR's OWN currency, ignore posting currency)

These fire whenever the underlying Fund Reservation is in EUR, regardless of how it is being consumed.

| # | Enhancement (and ENH block) | Hook / where it fires | `iv_waers` sourced from | What it modifies |
|---|---|---|---|---|
| 1a | `ZFIX_EF_FUND_RESERVATION` Enh 2 | KBLP/KBLK update during FMX1/FMX2 (FR create/change transaction execution) | `t_kblk-waers` (**FR header**) | `t_kblp-hwges`, `-hwgesapp` (the local-currency amount on each FR line — this is what writes the FR positions to FMIOI at BR ratio 1.09529 that we see in Gold-DB) |
| 1b | `ZFIX_EF_FUND_RESERVATION` Enh 3 | KBLP update during `RFFMREPO` (FM data **reconstruction** program — used by carryforward and recovery) | `t_kblk-waers` | First DELETES non-applicable rows (`loekz='X'` OR `gsber<>'GEF'` OR fipex/vrgng excluded OR ftype not authorized), then recomputes survivors at BR. **This is the carryforward branch that determines how 2025 FR balances arrive in 2026** |
| 2  | `ZFIX_EXCHANGERATE_CHECK_CONS` Enh 1+2 | `CL_FM_EF_POSITION->CHECK_CONSUMPTION` (EF availability check at consumption time) | `m_r_doc->m_f_kblk-waers` (**FR header**) | **SAVE/RESTORE pattern**: temporarily overwrites `m_t_addref-ref-hwges` with BR value during the standard EF check, then restores the original. **Nothing persisted** — only used to make the EF check pass. *(This is what your debugger captured: 100.00 → 96.06 USD)* |
| —  | `ZFIX_EXCHANGERATE_FUNDBLOCK` Enh 2 | `SAPMKBLD` (FMX1/FMX2 manual screen entry) | `kbld-waers` (**FR being maintained**) | `kbld-hwgesapp` |
| —  | `ZFIX_EXCHANGERATE_FUNDBLOCK` Enh 3 | `SAPMKBLD` | `kbld-waers` | `kbld-kursf` (the exchange-rate factor) |

### Camp B — Posting-currency-anchored (key on the per-row currency of what is being persisted)

These fire only when the row being processed is EUR. For a USD posting against an EUR FR, **all of these silently skip** because `iv_waers='USD'` fails the gate.

| # | Enhancement (and ENH block) | Hook | `iv_waers` sourced from | What it modifies |
|---|---|---|---|---|
| 1c | `ZFIX_EXCHANGERATE_PAYCOMMIT` | `SAPLMR1M / GET_FA_COMMIT_DATA` | `<yyls_reftab>-waers` (per-row reftab TX currency) | `<yyls_reftab>-hwges`, `-hwgesapp` (intermediate commitment data) |
| 3a | `ZFIX_EXCHANGERATE_NEW_ITEM` | `VFH_FUNDS_CHECK_OI / CREATE_NEW_ITEM_FA` | `c_f_fmoi-twaer` (**new commitment row**) | `c_f_fmoi-fkbtrorig`, `-fkbtrorig_max`, `-fkbtrredu`, `-fkbtradjst`, `-trbtrredu` (the new commitment line BEFORE persistence to FMIOI) |
| 3b | `ZFIX_EXCHANGERATE_AVC` Enh 1 | `FM_FUNDS_CHECK_OI` (loops `t_fmioi`) | `<ls_fmioi>-twaer` (per-row, mixed) | `<ls_fmioi>-fkbtr` (in-memory AVC working copy) |
| 3c | `ZFIX_EXCHANGERATE_AVC` Enh 3 | `FM_FUNDS_CHECK_OI` (loops `u_t_fmifiit`) | `<ls_fmifiit>-twaer` (per-row FMIFIIT) | `<ls_c_t_avc>-fkbtr` (AVC accumulator) |
| 5  | `ZFIX_EXCHANGERATE_KBLEW` | `CL_FM_EF_POSITION->CREATE_KBLEW_ENTRIES` | `ls_tr_kblew-waers` (the curtp=00 KBLEW row's TX currency) | `<ls_cc_kblew>-wrbtr`, `-wrbtrapp` (the curtp=10 local-currency KBLEW line — persisted to DB) |
| 6  | `ZFIX_EXCHANGERATE_FI` | FI doc → FM doc generation | `<ls_fmifiit>-twaer` (per-row FMIFIIT) | `<ls_fmifiit>-fkbtr` (persisted to DB) + `Y_FM_UPDATE_BR_FMIFIIT` audit + INSERT into `mt_avc_fund` + `SET HANDLER fmavc_reinit_on_event` |

### Camp C — Filter / exclusion (no gate, just deletion of non-applicable rows)

These do not call `check_conditions`+`convert_to_currency`. They prune rows from working tables so the standard SAP code never sees them.

| # | Enhancement | Hook | Filter logic | Effect |
|---|---|---|---|---|
| 9a | `ZFIX_BR_REVALUATION` Enh 2 | `FMN4N` (PO commitment recalc) — only when `sy-tcode='FMN4N'` | DELETE rows from `c_t_fmoi` where `fikrs<>'UNES'` OR `twaer<>'EUR'` OR `bus_area<>'GEF'` OR ftype not in `mr_fund_type` | Revaluation operates **only** on EUR+GEF+UNES rows. Any USD row on the same fund is silently skipped from revaluation cleanup |
| 9b | `ZFIX_BR_REVALUATION` Enh 3 | Same hook, applied to `u_t_fmioi_buf` (FMIOI buffer) | Same filter | Same effect on the buffer |
| 9c | `ZFIX_BR_REVAL_RESFUND` | `FMZZ` (Reservation Fund Revaluation report) | Sets `testlauf='X'` (TEST RUN ONLY!) + DELETE rows where `bukrs='UNES'` AND `waers<>'EUR'` OR `gsber<>'GEF'` OR ftype not in `mr_fund_type3` | Report-only; **never persists changes** |
| —  | **`ZFIX_BR_AVC_EXCLUSIONS`** (BAdI `IF_EX_FMAVC_ENTRY_FILTER~BUDGET_FILTER`) | All AVC entry points | `IF sy-tcode = 'MIRO' OR sy-tcode = 'F110' THEN E_FLG_SKIP_ENTRY = 'X'` | **Skips AVC entirely** for MIRO and F110 — **but NOT for FB60** (Vonthron's tcode!) |

### Camp D — Auxiliary / orchestration

| Enhancement | Purpose | Status |
|---|---|---|
| `ZFIX_FM_BR_POST_FROM_PY_AUTO` | After payroll posting (`p_rev = abap_false`), submits `submit_br_posting_in_fm` | Active — payroll bridge |
| `ZFIX_BR_BAPI_EMPLOYEE_POST` | Sets account data on `ycl_fm_br_payroll_posting_bl` for BAPI employee posting | Active — payroll bridge |
| `ZFIX_BRCHECKFUNDS` | (Source extraction returned 0 lines — likely empty/stub) | Unknown |
| `ZFIX_EXCHANGERATE_PBC_POS_UPD` | PBC HR amount conversion — has `CHECK 1=2` deactivation | **DEAD** |
| `ZFIX_EXCHANGERATE_FM_DOC_UPD`, `_FM_POS_UPD`, `_POPOST`, `_REDUCE`, `_REDUCE_1` | (Various) | DELETED or ORPHANED — no runtime effect |

### Why FB60 specifically blows up

The BAdI `ZFIX_BR_AVC_EXCLUSIONS` was UNESCO's escape hatch for the cross-currency mismatch — it skips AVC entirely when the transaction is **MIRO** (PO invoice) or **F110** (payment run). Both of those are downstream FI flows where the BR mismatch is known to surface, and skipping AVC there sweeps it under the rug.

**FB60 is not in that list.** FB60 is a direct vendor-invoice posting (no PO reference), and it goes through the standard AVC path — which evaluates the cover group at FMAVCT level and trips on the accumulated drift. So the AVC-skip "patch" leaves FB60 (and any other tcode not in {`MIRO`,`F110`}) as the visible failure surface for the underlying gate asymmetry.

This also means the bug surface is **wider than FB60**: any non-MIRO / non-F110 transaction that posts USD against an EUR-loaded BR pool will eventually hit FMAVC005 once the cover group tightens. Candidate tcodes: `FB65` (credit memo), `FB01` (general posting), `FB70` (customer invoice with FM consumption), `FBV1` (parked doc), `FBV0` (post parked).

### The SAVE/RESTORE pattern in CHECK_CONS — why "the EF check passes but persistence still drifts"

`CHECK_CONS` is split into **two ENHANCEMENT blocks** at the same hook:

```abap
ENHANCEMENT 1.   " Pre-check
  yylt_addref_save = m_t_addref.                   " ← SAVE original M-rate values
  ...
  LOOP AT m_t_addref ...
    " gate uses kblk-waers (FR's currency = EUR) → PASSES
    yylo_br_exchange_rate->convert_to_currency( ... )   " recalc HWGES at BR
    <yyls_addref>-ref-hwges = yylv_amount.         " 100.00 → 96.06 USD
    yylv_upd_done = abap_true.
  ENDLOOP.
ENDENHANCEMENT.
" ... CL_FM_EF_POSITION->CHECK_CONSUMPTION runs the standard EF check on the BR values ...
ENHANCEMENT 2.   " Post-check
  IF yylt_addref_save IS NOT INITIAL AND yylv_upd_done = abap_true.
    m_t_addref = yylt_addref_save.                 " ← RESTORE original M-rate values
  ENDIF.
ENDENHANCEMENT.
```

**This is intentional**: the BR values are visible **only during** the standard `CHECK_CONSUMPTION` call so the EF availability check passes at BR. As soon as the check returns, the original (M-rate) values are put back. **Nothing is persisted by CHECK_CONS** — it is a temporary in-memory override of the EF check, nothing more.

**The user's debugger screenshot captured this in flight**: `YYLT_ADDREF_SAVE` shows the saved 100.00 USD (M rate), `<YYLS_ADDREF>` shows the recalculated 96.06 USD (BR rate). The screen shows the moment between Enh 1 (recalc) and Enh 2 (restore).

### Why this design produces silent inconsistency

For a USD posting against an EUR FR (Vonthron's case):

1. **CHECK_CONS Enh 1** fires → recalculates the consumption to 96.06 USD at BR → standard `CHECK_CONSUMPTION` evaluates EF availability against this BR-consistent value → ✅ passes (FR has 4,400 EUR ≈ 4,819.28 USD at BR, posting is 96.06 USD → fits) → then **CHECK_CONS Enh 2** restores the original 100.00 USD.
2. **NEW_ITEM** fires for the new commitment item → gate `iv_waers = c_f_fmoi-twaer = 'USD'` → ❌ **FAILS** → standard SAP persists the commitment in `t_fmioi` at `FKBTR = TRBTR = 100.00 USD` (identity, no BR).
3. **AVC Enh 1** loops `t_fmioi` mix → existing EUR commitments recalc at BR; new USD commitment row's gate fails → **MIXED state** in the AVC working copy.
4. **AVC Enh 3** loops new FMIFIIT items → twaer='USD' → ❌ **FAILS** → c_t_avc accumulator gets the USD row at identity.
5. **KBLEW** fires for the consumption log → ls_tr_kblew-waers='USD' → ❌ **FAILS** → KBLEW curtp=10 (local-currency line) is left at standard SAP M-rate value, not BR.
6. **FI** writes FMIFIIT → twaer='USD' → ❌ **FAILS** → FMIFIIT.fkbtr persisted at identity (100 USD), no audit row in YTFM_BR_FMIFIIT, no fund inserted into `mt_avc_fund`.
7. **Phase 9 (event handler)** → `mt_avc_fund` is empty → `fmavc_reinit_on_event` is **never registered** → no `RFFMAVC_REINIT` runs at COMMIT_WORK → FMAVCT carries the discrepancy.

**Net effect**: CHECK_CONS made the consumption "look fine" to standard SAP at the EF level. Everything else persisted at identity / M rate. The two views diverge. Next time AVC reads FMAVCT (any subsequent posting near the cover-group ceiling), the discrepancy surfaces as `FMAVC005`.

### What the missing control would need to do

There is **no enhancement that BLOCKS the cross-currency consumption with an explicit error**. There is no "you cannot post in USD against an EUR-reserved Budget Rate fund" message. The 15 active enhancements collectively do the following for a USD posting on an EUR FR:

- **Camp A** (FR-currency-anchored) → fires → either (i) writes the FR side at BR (FUND_RESERVATION, FUNDBLOCK) which is fine, or (ii) does an in-memory SAVE/RESTORE recalc to make the EF check pass (CHECK_CONS) which is also fine in isolation
- **Camp B** (posting-currency-anchored) → SKIPS → lets standard SAP persist FMIOI / FMIFIIT / KBLEW at identity (FKBTR=TRBTR for USD) → drift enters the database
- **Camp C** (filters) → skips USD rows from revaluation tools → drift cannot be cleaned up by the existing reval programs (FMN4N, FMZZ)
- **Camp C BAdI** → AVC skip applies only to MIRO/F110 → FB60 (and other non-listed tcodes) exposes the underlying drift

What is missing:
1. **Preventive control**: a hard validation in the enhancement family that rejects USD-against-EUR-FR posting with a user-visible error message. **Currently absent.**
2. **Corrective control**: a cross-currency persistence path (in NEW_ITEM, AVC, KBLEW, FI) that uses `convert_to_currency_2` (USD UNORE → EUR @ M → USD @ EURX double hop) instead of silently skipping. The method is built and transported but only referenced from `IF 1 = 2.` "Staff logic on hold" branches — never runs.
3. **Cleanup control**: extend `BR_REVALUATION` (FMN4N) and `BR_REVAL_RESFUND` (FMZZ) to *include* USD rows on EUR-loaded funds, with a forced double-hop revaluation, so accumulated drift can be cleared post-hoc.
4. **AVC skip parity**: extend `ZFIX_BR_AVC_EXCLUSIONS` to cover FB60/FB65/FB70/FB01/FBV0 — not as a fix (still wrong) but as a stop-gap consistent with the existing MIRO/F110 treatment.

The asymmetry has been latent since the design first shipped (Jan 2024). It only becomes visible when a cover group tightens — which is happening now as the carryforward from 2025 puts many EUR-loaded pools at near-zero headroom for 2026.

---

## ⚡ TRACE-CONFIRMED MECHANISM (Session #054)

For a USD posting against an EUR-loaded fund (Vonthron's case + Konakov's TS3 reproduction):

```
   FB60 USD posting
        │
        ▼
   YCL_FM_BR_EXCHANGE_RATE_BL invoked  (42 times in trace — ONE per row across all phases)
        │
        ├─ check_br_is_active  → TVARVC.Y_FM_FIXED_RATE_START='20240101' ✅ pass
        ├─ get_fund_type_from_fund → SELECT FROM FMFINCODE → returns '001' ✅ in mr_fund_type
        └─ check_conditions(iv_waers='USD', ...) :
              ├─ rldnr='9A'   IN mr_rldnr      ✅
              ├─ bukrs='UNES' IN mr_bukrs      ✅
              ├─ fikrs='UNES' IN mr_fikrs      ✅
              ├─ gsber='GEF'  IN mr_gsber      ✅
              ├─ waers='USD'  IN mr_waers      ❌ ← single blocker, mr_waers = ['EUR']
              └─ method exits → returns abap_false
        │
        ▼
   convert_to_currency NEVER CALLED  (0 TCURR reads in entire trace)
        │
        ▼
   Standard SAP path takes over
        │
        ▼
   FMIOI persisted at FKBTR=TRBTR (identity)
   FMIFIIT persisted at FKBTR=TRBTR (identity)
   FMAVCT NOT reinitialized (mt_avc_fund stayed empty → handler never fires)
        │
        ▼
   AVC algorithm reads pool valued at BR (loaded EUR×1.09529)
   compares to USD posting valued at identity (USD=USD)
        │
        ▼
   Mismatch surfaces as FMAVC005 the moment the FR is at zero headroom
   (verified empirically by Konakov in TS3 with fresh same-year FR consuming
    full budget — fails identically to Vonthron's cross-year case)
```

**Falsified hypotheses superseded by the trace:**
- ❌ "Carryforward path bypasses BR" — false; CF carries the BR-correct FR position forward; the failure is at consumption time on USD postings, regardless of year.
- ❌ "Cross-year is required for the bug to fire" — false; same-year reproduces identically when the FR is at zero headroom (Konakov 2026-04-13).
- ✅ "`mr_waers=['EUR']` gate excludes USD" — confirmed live; this single line, combined with no per-currency dispatcher in the enhancement bodies, is the entire bug.

**Confirmed by data (Gold-DB audit, `Zagentexecution/quality_checks/budget_rate_consumption_audit.py`):**
- Fund 3110111021, fmifiit_full: 259 EUR rows BR-applied (ratio 1.09529) vs 22 USD rows BR-bypassed (ratio 1.00000 identity). The 22 bypassed rows quantitatively explain the cumulative AVC drift (~$489.87 estimated drift contribution).
- FR 3250117351, fmioi: all 53 positions (47 consumed in 2025 + 6 carried-forward to 2026) at BR ratio 1.09529 — the FR side is consistent. The drift is *not* in the FR, it's in the gap between FR-side BR and consumption-side identity for USD postings on the same fund.

---

## 🧬 UNIFIED PROCESS VIEW (added Session #053, 2026-04-13)

**The 8 enhancements are NOT 8 independent features. They are 8 phases of a single coherent process** whose invariant is:

> *Every amount that enters any phase of the transaction must be transformed to USD-at-BR and persisted with that transformation. If ANY phase is skipped while others fire, the process produces hybrid state → drift → AVC rejection.*

**Shared state across all enhancements (via singleton `YCL_FM_BR_EXCHANGE_RATE_BL`):**

| Attribute | Purpose | Used by |
|---|---|---|
| `mv_start_date` | Activation gate (`check_br_is_active`) | ALL phases |
| `mr_waers = ['EUR']` | Authorized transaction currencies | ALL phases via `check_conditions` |
| `mr_bukrs`, `mr_fikrs`, `mr_gsber`, `mr_fund_type` | Perimeter filters | ALL phases |
| `mt_avc_fund` | Runtime accumulator of funds to reinit | Populated in Phase 7 (FI), consumed in Phase 9 (reinit) |
| Event handler `fmavc_reinit_on_event` | Post-commit reinit trigger | Registered in Phase 7, fires after `COMMIT_WORK` |

**Implicit design assumption that breaks under cross-currency:**

The process was implicitly designed assuming that all `iv_waers` inputs across all phases for a single transaction are the SAME currency. That is true when the transaction is EUR-native (posting + FR + reference all in EUR) or USD-native. It is NOT true for cross-currency scenarios where, e.g., a USD posting consumes an EUR FR.

**The cross-currency quiebre — phase gate matrix for USD posting against EUR FR:**

| Phase | Enhancement | Source of `iv_waers` | Value | Gate | BR applies? |
|---|---|---|---|---|---|
| 2 | CHECK_CONS | `m_r_doc->m_f_kblk-waers` (header) | 'USD' | ❌ FAIL | No |
| 3 | NEW_ITEM (new USD actual) | `c_f_fmoi-twaer` | 'USD' | ❌ FAIL | No |
| 3 | NEW_ITEM (EUR release row) | `c_f_fmoi-twaer` (inherited FR) | 'EUR' | ✅ PASS | Yes |
| 4 | AVC per-row loop | `<ls_fmioi>-twaer` | mixed | ⚠ hybrid | Partial |
| 6 | KBLEW | `ls_tr_kblew-waers` | 'USD' | ❌ FAIL | No |
| 7 | FI | `<ls_fmifiit>-twaer` | 'USD' | ❌ FAIL | No |
| 9 | REINIT | — | — | ❌ (mt_avc_fund empty) | Not fired |

**Result: hybrid state** — some phases fire (EUR-inherited rows), others skip (USD-native rows). Group 1 and Group 2 tables end up with amounts computed under TWO different rate regimes for the same transaction. The AVC check then compares amounts from the two regimes and finds a mismatch → FMAVC005.

**The `convert_to_currency_2` method** (CM002) exists specifically to handle this cross-currency case (USD UNORE → EUR UNORE @ M → USD BR @ EURX — double hop). It is complete, tested, and transported — but referenced only from `IF 1 = 2.` "Staff logic on hold" branches. It is the unactivated half of the intended cross-currency solution.

**Testable predictions from this unified view:**

- EUR posting against EUR FR → all phases PASS → consistent → works (confirmed by Konakov)
- USD posting against USD FR → all phases SKIP → standard SAP end-to-end → works (never tested explicitly but predicted)
- **USD posting against EUR FR → hybrid state → FMAVC005** (reproduced in Vonthron's case and Konakov's TS1 tests)

---

## 🧭 FUNDAMENTAL MODEL (added Session #053)

The BR solution operates across **two parallel universes** that must stay consistent:

```
GROUP 1 — FUND RESERVATION WORLD     GROUP 2 — FM BUDGET POOL WORLD
├── Tables: KBLK/KBLP/KBLE/KBLEW     ├── Tables: FMIOI/FMIFIIT/FMAVCT
├── AVC:    CL_FM_EF_POSITION         ├── AVC:    FM_FUNDS_CHECK_OI
│           ->CHECK_CONSUMPTION       │           (FM Area AVC ledger 9H)
├── Error:  "Open amount from doc    ├── Error:  FMAVC005 "Annual budget
│           XXX exceeded by Y%"      │           exceeded by X USD"
└── BR hooks:                        └── BR hooks:
     CHECK_CONS, FUNDBLOCK,                AVC, NEW_ITEM, FI,
     KBLEW                                 PAYCOMMIT
```

**Key invariants the BR solution must maintain:**

1. **Same-year FR create+consume**: both groups updated at BR consistently ✅ (verified empirically)
2. **Cross-year (carryforward)**: FR from year N used in year N+1 — **diverges** in practice (Illya/Vonthron cases fail) ⚠
3. **KBLEW-FMIOI consistency at consumption moment**: `KBLEW[curtp=10].wrbtr` must equal `FMIOI[new actual].fkbtr` for the same consumption event. If they diverge, the AVC pool accumulates drift.
4. **Phase 9 post-commit reinit** is the safety net — but only fires if `mt_avc_fund` was populated during Phase 7 (FI enhancement), which requires `check_conditions` to have passed.

## 🔬 FB60 EXECUTION TRACE — enhancement firing order (added Session #053)

This is the canonical execution flow of a vendor invoice with EF reference through the ZFIX_EXCHANGERATE_* family. Use this as the reference when reasoning about which enhancement runs at which phase and what tables are touched.

| Phase | Step | Layer | Hook / Method | Enhancement | Tables updated | Key logic |
|---|---|---|---|---|---|---|
| 0 | — | User entry | `SAPMF05A` | — | memory (BKPF/BSEG proto) | User enters header + line with EF ref |
| 1 | — | Derivation | `FMDERIVE` strategy | `ZXFMDTU02_RPY` (non-BR) | memory (T_FMDERIVE_TARGET) | Fund/FC/FIPEX derivation |
| 2 | **2** | Group 1 | `CL_FM_EF_POSITION->CHECK_CONSUMPTION` | `ZFIX_EXCHANGERATE_CHECK_CONS` | memory only (SAVE/RESTORE pattern) | Override `hwges/hwgesapp` at BR, run standard check, restore |
| 3 | **3** | Group 2 | `VFH_FUNDS_CHECK_OI / CREATE_NEW_ITEM_FA` | `ZFIX_EXCHANGERATE_NEW_ITEM` | memory (FMIOI item) | Recalc `trbtrredu`/`fkbtrorig`/`fkbtrredu`/`fkbtradjst` at BR; conv factor from orig ratio |
| 4 | **3** | Group 2 | `FM_FUNDS_CHECK_OI` | `ZFIX_EXCHANGERATE_AVC` (Enh 1 + Enh 3) | memory (t_fmioi / c_t_avc) | Loop and convert `trbtr→USD@BR` → overwrite `fkbtr`; evaluate AVC |
| 5 | **1** | Group 1 | `SAPLMR1M / GET_FA_COMMIT_DATA` | `ZFIX_EXCHANGERATE_PAYCOMMIT` | memory (T_REFTAB) | Convert `wtges/wtgesapp → hwges/hwgesapp` at BR for intermediate commitment data |
| 6 | **5** | Group 1 | `CL_FM_EF_POSITION->CREATE_KBLEW_ENTRIES` | `ZFIX_EXCHANGERATE_KBLEW` | **DB**: KBLEW (curtp=10), KBLE, KBLP | Convert `curtp=00 wrbtr → curtp=10 wrbtr` at BR |
| 7 | **6** | Group 2 | FI doc → FM doc generation | `ZFIX_EXCHANGERATE_FI` | **DB**: FMIFIIT, YTFM_BR_FMIFIIT (audit), registers event handler | Save pre-BR to audit, convert `trbtr→USD@BR` → overwrite `fkbtr`, INSERT fund to `mt_avc_fund` |
| 8 | — | Group 2 | `COMMIT WORK` | — | Persist all DB writes | Fires event `TRANSACTION_FINISHED` |
| 9 | — | Group 2 | Event handler | `fmavc_reinit_on_event` (method) | **DB**: FMAVCT | SUBMIT `RFFMAVC_REINIT` on `ALDNR=9H` for affected funds — rebuilds FMAVCT from FMIOI+FMIFIIT |

**Enhancements NOT in the FB60 flow:**
- `ZFIX_EXCHANGERATE_FUNDBLOCK` — only for `SAPMKBLD` (FMX1/FMX2 manual FR entry)
- `ZFIX_EXCHANGERATE_PBC_POS_UPD` — hard-deactivated (`CHECK 1 = 2. "Deactivated the 2024/01/08"`)

**Danger zones in the trace:**

- **Phase 2 SAVE/RESTORE**: the override is in-memory only and rolled back at end of method. No persistence. If standard CHECK_CONSUMPTION relied on the modified hwgesapp for downstream logic in the same LUW, the restore undoes it.
- **Phase 6 ↔ Phase 7 consistency**: KBLEW (curtp=10) and FMIFIIT.fkbtr are BOTH supposed to be at BR for the same consumption event, but fire in different methods with different `check_conditions` inputs. If one fires and the other doesn't (because of a gate difference), Group 1 and Group 2 diverge.
- **Phase 9 conditional fire**: `fmavc_reinit_on_event` only runs if `mt_avc_fund` was populated during Phase 7. If Phase 7 skipped (check_conditions returned false for the line, e.g., for USD where `mr_waers = ['EUR']`), no reinit → FMAVCT is not reconstructed → drift persists.
- **Cross-year (CARRYFORWARD)**: the CF batch process writes directly to FMIOI with WRTTP=81 for the carried commitments. If that write path does NOT go through any BR enhancement (because it's not FB60/FI posting but a standalone CF job), the carried FMIOI rows reflect whatever ratio SAP standard computed — which may differ from the BR ratio used on original creation + KBLEW log.

---


> **Extracted sources:**
> - Class: `extracted_code/CLAS/YCL_FM_BR_EXCHANGE_RATE_BL/` (21 include files: CO/CP/CT/CU/CI + 13 CM method includes + CCDEF/CCIMP/CCMAC)
> - Enhancements: `extracted_code/ENHO/ZFIX_EXCHANGERATE/` (8 ABAP includes)
> - Authors: `JP_LOPEZ` (enhancements + composite container, 2024-06-28) + `N_MENARD` (class + 6 of the 15 enhancement members)

---

## 1. Functional Context

UNESCO operates company code `UNES` in **USD** (`T001.WAERS='USD'`). The FM area `UNES` holds budget, commitments, and actuals in USD as the FM area currency (`FKBTR`). However, many operational transactions (payroll, fund reservations, vendor invoices) are natively denominated in **EUR** or local currencies (XOF, MRU, etc.) and enter the chain as transaction currency (`TRBTR`) in the ledger tables.

To insulate the **budget envelope** from daily FX volatility, UNESCO applies a **fixed "Budget Rate"** (BR) via TCURR rate type `'EURX'` whenever an FM-relevant EUR posting hits the chain. This replaces SAP's default path, which would use the standard OB08 daily average rate (`KURST='M'`) and introduce FX drift between commitments and actuals.

The business rationale (Pablo Lopez, 2026-03-30):

> *"If they buy something in a PO, and pay after 3 months and the exchange rate changes, there will be needed more budget to pay. The only case that is not needed is with **Budget rate** as this is **Fixed**."*

---

## 2. Architecture — `ZFIX_EXCHANGERATE_*` Enhancement Family

### 2.1 Composite container

```
TADIR entries in D01:
  ENHC  ZFIX_EXCHANGERATE                 DEVCLASS=YA  AUTHOR=JP_LOPEZ  2024-06-28
  ENHO  ZFIX_EXCHANGERATE                 DEVCLASS=YA  AUTHOR=JP_LOPEZ  2024-06-28
```

### 2.2 Member enhancement implementations (15 total)

| Enhancement Implementation              | Author     | Created    | Step | Short Text                                                  | Extracted |
|------------------------------------------|------------|------------|------|-------------------------------------------------------------|-----------|
| `ZFIX_EXCHANGERATE_AVC`                  | JP_LOPEZ   | 2025-06-30 | 3    | AVC at BR FMIOI                                             | ✅        |
| `ZFIX_EXCHANGERATE_CHECK_CONS`           | N_MENARD   | 2024-10-04 | 2    | AVC Earmarked Funds Fund Reservation for EF postings         | ✅        |
| `ZFIX_EXCHANGERATE_FI`                   | JP_LOPEZ   | 2024-06-28 | 6    | Generate new item FMIFIIT FMAVC Finance Postings            | ✅        |
| `ZFIX_EXCHANGERATE_FM_DOC_UPD`           | N_MENARD   | 2024-11-08 | —    | FM document update at BR                                    | 🗑 **DELETED** 2024-12-19 by JP_LOPEZ (ENHLOG LOGACTION=DELETED) |
| `ZFIX_EXCHANGERATE_FM_POS_UPD`           | N_MENARD   | 2024-11-08 | —    | FM position update at BR                                    | ☠ **ORPHANED** — TADIR active but `cl_enh_factory=>get_enhancement` returns *"cannot be read"*. No runtime effect. |
| `ZFIX_EXCHANGERATE_FUNDBLOCK`            | JP_LOPEZ   | 2024-07-15 | 99   | Manual reduction Fund reservation — Screen-Not used         | ✅        |
| `ZFIX_EXCHANGERATE_KBLEW`                | JP_LOPEZ   | 2024-07-16 | 5    | Consumptions Update KBLEW multiple Currencies                | ✅        |
| `ZFIX_EXCHANGERATE_NEW_ITEM`             | N_MENARD   | 2024-09-26 | 3    | New item FMIO Commitments                                   | ✅        |
| `ZFIX_EXCHANGERATE_PAYCOMMIT`            | N_MENARD   | 2024-10-08 | 1    | Create Commitments intermediate value                        | ✅        |
| `ZFIX_EXCHANGERATE_PBC_POS_UPD`          | N_MENARD   | 2024-11-13 | 0    | PBC HR Change Amount before transfer to FM posting          | ✅ (**deactivated** via `CHECK 1 = 2` line 10) |
| `ZFIX_EXCHANGERATE_POPOST`               | JP_LOPEZ   | 2024-07-01 | —    | Post PO at BR                                               | ☠ **ORPHANED** — TADIR active but cannot be loaded via `cl_enh_factory`. No runtime effect. |
| `ZFIX_EXCHANGERATE_REDUCE`               | N_MENARD   | 2024-09-27 | —    | Reduction at BR                                             | ☠ **ORPHANED** — TADIR active but cannot be loaded via `cl_enh_factory`. No runtime effect. |
| `ZFIX_EXCHANGERATE_REDUCE_1`             | N_MENARD   | 2024-09-27 | —    | Reduction at BR (variant 1)                                 | 🗑 **DELETED** 2024-09-27 by N_MENARD (ENHLOG LOGACTION=DELETED, same day as create) |

### 2.3 Data persistence tables (confirmed from source code)

| Table / FM                   | Purpose                                                                                   |
|------------------------------|-------------------------------------------------------------------------------------------|
| `YTFM_BR_FMIFIIT`            | Pre-conversion FMIFIIT snapshot. Every item the FI enhancement BR-overwrites is first saved here for audit. |
| `Y_FM_UPDATE_BR_FMIFIIT` (FM)| Inserts into `YTFM_BR_FMIFIIT`. Called from `ZFIX_EXCHANGERATE_FI`.                        |
| `Y_FM_UPDATE_BR_FM_POS` (FM) | Inserts into a PBC position audit table. Called from `ZFIX_EXCHANGERATE_PBC_POS_UPD`.     |
| `TVARVC` `Y_FM_FIXED_RATE_START`  (P) | BR activation date. **Current value: `20240101`** → BR has been active since Jan 1 2024.  |
| `FMFUNDTYPE.ZZFIX_RATE`      | Custom column — fund types with `ZZFIX_RATE='X'` are authorized for BR. Constructor reads this into `mr_fund_type` at startup. |

### 2.4 Current authorized fund types (live D01 query, 2026-04-10)

```
FMFUNDTYPE WHERE FM_AREA = 'UNES' AND ZZFIX_RATE = 'X':
  001, 002, 003, 004, 005, 009, 010, 012, 013, 016, 017, 018, 094, 095
```

**Fund type `019` is explicitly excluded.** Fund type `001` (Regular Programme — the type of fund 3110111021) is authorized. The inverted list (same types) is also loaded into `mr_fund_type3` for the revaluation exclusion path.

---

## 3. Central class: `YCL_FM_BR_EXCHANGE_RATE_BL`

**Package:** `YA` • **Author:** `N_MENARD` • **Created:** `2024-08-06` • **Pattern:** Singleton (`GET_INSTANCE` → `MO_INSTANCE`).

### 3.1 Complete method inventory

| CM #  | Method                             | Lines | Role |
|-------|------------------------------------|-------|------|
| CM001 | `GET_INSTANCE`                     | 9     | Singleton factory |
| CM002 | `CONVERT_TO_CURRENCY_2`            | 47    | Double-hop USD → EUR @ M → USD @ EURX |
| CM004 | `CHECK_CONDITIONS`                 | 39    | **Main gate** — checks `mr_waers` etc. |
| CM005 | `CONVERT_TO_CURRENCY`              | 32    | Wraps standard `CONVERT_TO_LOCAL_CURRENCY` with rate type `'EURX'` |
| CM006 | `GET_EXCHANGE_RATE`                | 30    | Wraps `READ_EXCHANGE_RATE` with rate type `'EURX'` |
| CM007 | `FMAVC_REINIT_ON_EVENT`            | 26    | Event handler — after `COMMIT_WORK`, submits `RFFMAVC_REINIT` for affected funds on `ALDNR='9H'` |
| CM008 | `GET_FUND_TYPE_FROM_FUND`          | 10    | `SELECT SINGLE type FROM fmfincode WHERE fikrs AND fincode` |
| CM009 | `GET_FM_AREA_FROM_COMPANY_CODE`    | 11    | `SELECT SINGLE fikrs FROM t001 WHERE bukrs` with caching |
| CM00A | `CONSTRUCTOR`                      | 47    | **Initializes all filter ranges** |
| CM00B | `CHECK_CONDITIONS_2`               | 45    | Staff-logic variant — uses `mr_waers2`, adds HKONT check |
| CM00C | `CHECK_CONDITIONS_3`               | 36    | Revaluation/deletion variant — uses `NOT IN` for ranges, `IN` for `mr_*3` |
| CM00D | `CHECK_BR_IS_ACTIVE`               | 9     | Simple: `sy-datum >= mv_start_date` |
| CM00E | `GET_BR_IMPACT`                    | 69    | Computes `ZZAMOUNTBRLC` / `ZZAMOUNTBRDIFF` for extension fields (for BR impact reporting per doc) |

### 3.2 CONSTRUCTOR (CM00A) — the range initialization

```abap
METHOD constructor.

  "Set values for ranges
  APPEND VALUE #( sign = 'I' option = 'EQ' low = '9A'   ) TO mr_rldnr.
  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'UNES' ) TO mr_bukrs.
  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'UNES' ) TO mr_fikrs.
  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'GEF'  ) TO mr_gsber.
  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR'  ) TO mr_waers.       " ⭐⭐⭐ ONLY EUR

  mr_fipex = VALUE #( ( sign = 'E' option = 'EQ' low = 'GAINS'   )
                      ( sign = 'E' option = 'EQ' low = 'REVENUE' ) ).

  mr_vrgng = VALUE #( ( sign = 'E' option = 'EQ' low = 'HRM1' )   "PBC pre-commitment
                      ( sign = 'E' option = 'EQ' low = 'HRM2' )   "PBC commitment
                      ( sign = 'E' option = 'EQ' low = 'HRP1' ) ). "Payroll posting

  "Set fund types perimeters from FMFUNDTYPE custom column ZZFIX_RATE
  SELECT 'I', 'EQ', fund_type AS low FROM fmfundtype
    WHERE fm_area IN @mr_fikrs AND zzfix_rate = @abap_true
    INTO TABLE @mr_fund_type.

  "For revaluation exclusion (same types but exclude)
  SELECT 'E', 'EQ', fund_type AS low FROM fmfundtype
    WHERE fm_area IN @mr_fikrs AND zzfix_rate = @abap_true
    INTO TABLE @mr_fund_type3.

  mr_fipex3 = VALUE #( ( sign = 'I' option = 'EQ' low = 'GAINS'   )
                       ( sign = 'I' option = 'EQ' low = 'REVENUE' ) ).

  mr_vrgng3 = VALUE #( ( sign = 'I' option = 'EQ' low = 'HRM1' )
                       ( sign = 'I' option = 'EQ' low = 'HRM2' )
                       ( sign = 'I' option = 'EQ' low = 'HRP1' ) ).

  "Get start date for fixed rate — from TVARVC
  SELECT SINGLE CAST( low AS DATS ) INTO @mv_start_date
    FROM tvarvc WHERE name = 'Y_FM_FIXED_RATE_START' AND type = 'P'.
  IF mv_start_date IS INITIAL OR mv_start_date = space.
    mv_start_date = '99991231'.
  ENDIF.

  "Staff logic ranges (dead code everywhere — IF 1 = 2 gated)
  mr_vrgng2 = VALUE #( ( sign = 'I' option = 'EQ' low = 'HRM1' )
                       ( sign = 'I' option = 'EQ' low = 'HRM2' )
                       ( sign = 'I' option = 'EQ' low = 'HRP1' ) ).

  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR' ) TO mr_waers2.        " Staff
  APPEND VALUE #( sign = 'I' option = 'EQ' low = 'USD' ) TO mr_waers2.        " Staff — USD included here!

ENDMETHOD.
```

### 3.3 The active perimeter — summary table

| Range         | Sign   | Content                                                             | Purpose                                       |
|---------------|--------|---------------------------------------------------------------------|-----------------------------------------------|
| `mr_rldnr`    | `I EQ` | `['9A']`                                                            | FM reconciliation ledger (FMIOI/FMIFIIT)      |
| `mr_bukrs`    | `I EQ` | `['UNES']`                                                          | Company code                                   |
| `mr_fikrs`    | `I EQ` | `['UNES']`                                                          | FM area                                        |
| `mr_gsber`    | `I EQ` | `['GEF']`                                                           | Business area (only GEF!)                      |
| **`mr_waers`**| **`I EQ`** | **`['EUR']`**                                                  | **⭐ Authorized transaction currency — EUR ONLY** |
| `mr_fipex`    | `E EQ` | `['GAINS','REVENUE']`                                               | Commitment items to exclude                    |
| `mr_vrgng`    | `E EQ` | `['HRM1','HRM2','HRP1']`                                            | VRGNG to exclude (payroll/PBC handled elsewhere) |
| `mr_fund_type`| `I EQ` | `[001,002,003,004,005,009,010,012,013,016,017,018,094,095]`          | From `FMFUNDTYPE.ZZFIX_RATE='X'` — 14 types    |
| `mr_waers2`   | `I EQ` | `['EUR','USD']` *(Staff logic — dead code)*                          | Would authorize both currencies — unused       |
| `mr_hkont`    |   (empty)  | Staff logic range for HKONT — never populated                       |                                                |

### 3.4 CHECK_CONDITIONS (CM004) — the Non-Staff gate

```abap
METHOD check_conditions.
  rv_is_ok = abap_false.

  IF iv_rldnr IS NOT INITIAL. CHECK iv_rldnr IN mr_rldnr.       ENDIF.
  IF iv_bukrs IS NOT INITIAL. CHECK iv_bukrs IN mr_bukrs.       ENDIF.
  IF iv_fikrs IS NOT INITIAL. CHECK iv_fikrs IN mr_fikrs.       ENDIF.
  IF iv_gsber IS NOT INITIAL. CHECK iv_gsber IN mr_gsber.       ENDIF.
  IF iv_waers IS NOT INITIAL. CHECK iv_waers IN mr_waers.       ENDIF.   " ⭐ Blocks everything except EUR
  IF iv_fipex IS NOT INITIAL. CHECK iv_fipex IN mr_fipex.       ENDIF.
  IF iv_vrgng IS NOT INITIAL. CHECK iv_vrgng IN mr_vrgng.       ENDIF.
  IF iv_ftype IS NOT INITIAL. CHECK iv_ftype IN mr_fund_type.   ENDIF.

  rv_is_ok = abap_true.
ENDMETHOD.
```

Note: `mr_fipex` and `mr_vrgng` are **exclusion** ranges — `CHECK iv_fipex IN mr_fipex` with an E/EQ range means "pass only if NOT in the exclusion list". Same for `mr_vrgng`. The other ranges are inclusion.

### 3.5 CHECK_CONDITIONS_2 (CM00B) — the Staff variant (dead code)

```abap
METHOD check_conditions_2.
* Check Staff Conditions
  rv_is_ok = abap_false.
  ...
  IF iv_waers IS NOT INITIAL. CHECK iv_waers IN mr_waers2. ENDIF.   " ← EUR + USD
  ...
  IF iv_vrgng IS NOT INITIAL. CHECK iv_vrgng IN mr_vrgng2. ENDIF.   " ← HRM*/HRP* (Staff only)
  ...
  IF iv_hkont IS NOT INITIAL. CHECK iv_hkont IN mr_hkont.  ENDIF.
  ...
  rv_is_ok = abap_true.
ENDMETHOD.
```

**Called only from `IF 1 = 2.` branches** in all 8 enhancements → **this code is entirely dead**.

### 3.6 CONVERT_TO_CURRENCY (CM005) — the main BR call

```abap
METHOD convert_to_currency.
  CLEAR ev_local_amount.
  CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
    EXPORTING
      date             = iv_date
      foreign_amount   = iv_foreign_amount
      foreign_currency = iv_foreign_currency
      local_currency   = iv_local_currency
      type_of_rate     = iv_type_of_rate                  " DEFAULT 'EURX'  ⭐
    IMPORTING
      local_amount     = ev_local_amount
    EXCEPTIONS
      no_rate_found    = 1
      overflow         = 2
      no_factors_found = 3
      no_spread_found  = 4
      derived_2_times  = 5
      OTHERS           = 6.
  ev_subrc = sy-subrc.
ENDMETHOD.
```

**Confirmed: budget rate = TCURR rate type `EURX`.** The method signature declares `IV_TYPE_OF_RATE TYPE KURST_CURR DEFAULT 'EURX'` — so callers that don't specify get EURX by default. Every enhancement calls it without overriding the rate type, so they all use EURX.

### 3.7 CONVERT_TO_CURRENCY_2 (CM002) — the double-hop for USD

```abap
METHOD convert_to_currency_2.
  DATA: ev_local_amount_2 TYPE bseg-dmbtr.

  "Step 1: Convert USD UNORE to EUR UNORE (at standard 'M' rate)
  CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
    EXPORTING
      date             = iv_date
      foreign_amount   = iv_foreign_amount
      foreign_currency = 'USD'                 " USD UNORE
      local_currency   = 'EUR'                 " EUR UNORE
      type_of_rate     = iv_type_of_rate_unore " M  (default 'M')
    IMPORTING
      local_amount     = ev_local_amount_2
    ...
  ev_subrc = sy-subrc.

  "Step 2: Convert EUR UNORE to USD BR (at 'EURX' budget rate)
  CLEAR ev_local_amount.
  CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
    EXPORTING
      date             = iv_date
      foreign_amount   = ev_local_amount_2
      foreign_currency = 'EUR'
      local_currency   = 'USD'
      type_of_rate     = iv_type_of_rate       " EURX (default)
    IMPORTING
      local_amount     = ev_local_amount
    ...
  ev_subrc = sy-subrc.
ENDMETHOD.
```

**Purpose**: given a USD amount at UN Operational Rate (UNORE = M rate), return the equivalent USD amount at Budget Rate (via EUR intermediate). This is the "USD UNORE → USD BR" double conversion.

**Status**: exists and is complete, but **is only called from `IF 1 = 2.` Staff-logic branches in the 8 enhancements** → **never runs in production**.

### 3.8 FMAVC_REINIT_ON_EVENT (CM007) — the "INCREDIBLE SOLUTION"

```abap
METHOD fmavc_reinit_on_event.
  DATA lt_fund  TYPE RANGE OF bp_geber.
  DATA lt_aldnr TYPE RANGE OF buavc_aldnr.

  CHECK kind = cl_system_transaction_state=>commit_work.

  APPEND VALUE #( sign = 'I' option = 'EQ' low = '9H' ) TO lt_aldnr.

  LOOP AT mt_avc_fund INTO DATA(ls_avc_fund).
    APPEND VALUE #( sign = 'I' option = 'EQ' low = ls_avc_fund-fonds ) TO lt_fund.
    AT END OF fikrs.
      SET PARAMETER ID 'FIK' FIELD ls_avc_fund-fikrs.
      SUBMIT rffmavc_reinit EXPORTING LIST TO MEMORY
                            WITH p_fikrs = ls_avc_fund-fikrs
                            WITH p_gjahr = ls_avc_fund-gjahr
                            WITH s_fund IN lt_fund
                            WITH s_aldnr IN lt_aldnr
                            AND  RETURN.
      CLEAR lt_fund.
    ENDAT.
  ENDLOOP.

  CLEAR mt_avc_fund.
ENDMETHOD.
```

Mechanism:
1. `ZFIX_EXCHANGERATE_FI` enhancement populates `mt_avc_fund` with each fund whose FMIFIIT it has just BR-overwritten, then does `SET HANDLER yylo_br_exchange_rate->fmavc_reinit_on_event`.
2. At the end of the LUW, SAP fires `CL_SYSTEM_TRANSACTION_STATE~TRANSACTION_FINISHED`.
3. This handler runs, filters on `KIND = COMMIT_WORK` (ignoring ROLLBACK), and `SUBMIT RFFMAVC_REINIT` for each affected fund on ALDNR `9H` (the UNESCO AVC ledger).
4. The reinit re-builds FMAVCT from the underlying persisted FMIOI/FMIFIIT which now have BR-corrected FKBTR values.

This is the post-event recovery that keeps FMAVCT in sync with BR — **but it only fires for the Non-Staff path, which only processes EUR**. USD postings never trigger the reinit, so the FMAVCT for funds with USD activity drifts over time.

### 3.9 Supporting methods

```abap
METHOD check_br_is_active.
  rv_is_ok = abap_false.
  IF sy-datum >= mv_start_date.         " mv_start_date = TVARVC Y_FM_FIXED_RATE_START, today = 2024-01-01
    rv_is_ok = abap_true.
  ENDIF.
ENDMETHOD.

METHOD get_instance.
  IF mo_instance IS INITIAL.
    mo_instance = NEW ycl_fm_br_exchange_rate_bl( ).
  ENDIF.
  ro_instance = mo_instance.
ENDMETHOD.

METHOD get_fund_type_from_fund.
  SELECT SINGLE type FROM fmfincode
    WHERE fikrs = @iv_fikrs AND fincode = @iv_fincode
    INTO @rv_ftype.
  IF sy-subrc <> 0. CLEAR rv_ftype. ENDIF.
ENDMETHOD.

METHOD get_fm_area_from_company_code.
  IF iv_bukrs <> mv_bukrs.
    CLEAR mv_fikrs.
    SELECT SINGLE fikrs FROM t001 WHERE bukrs = @iv_bukrs INTO @mv_fikrs.
    mv_bukrs = iv_bukrs.
  ENDIF.
  rv_fikrs = mv_fikrs.
ENDMETHOD.

METHOD get_exchange_rate.
  CALL FUNCTION 'READ_EXCHANGE_RATE'
    EXPORTING
      date             = iv_date
      foreign_currency = iv_foreign_currency
      local_currency   = iv_local_currency
      type_of_rate     = 'EURX'                    " ⭐ Hardcoded (no default param)
    IMPORTING
      exchange_rate    = ev_exchange_rate
    EXCEPTIONS ...
  ev_subrc = sy-subrc.
ENDMETHOD.
```

---

## 4. Enhancement-by-enhancement behavior (live source code)

All 8 active enhancement members follow the **same pattern**:

```
1. Get singleton: yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
2. [Optional] Master gate: IF check_br_is_active( ) = abap_true.
3. Per-item loop:
   a. CHECK check_conditions( iv_waers = <row>.twaer, ... ) = abap_true.
   b. convert_to_currency( foreign = <row>.trbtr, foreign_currency = <row>.twaer, local_currency = 'USD' ).
   c. Overwrite <row>.fkbtr with converted value.
4. [Optional Staff logic block]: IF 1 = 2. ... ENDIF.     ← ALL DEAD CODE
```

### 4.1 `ZFIX_EXCHANGERATE_AVC` — Enhancement 1 (AVC commitment check)

- **Hook:** `FM_FUNDS_CHECK_OI` (function module) — start section
- **Master gate:** ❌ none (`check_br_is_active` NOT called here)
- **Loop:** `LOOP AT t_fmioi`
- **Per-row gate:** `check_conditions(iv_waers=<ls_fmioi>-twaer, ...)`
- **Conversion:** `convert_to_currency(foreign=<trbtr>, foreign_currency=<twaer>, local_currency='USD')`
- **Target:** `<ls_fmioi>-fkbtr`
- **Authorship:** Added/updated by **JP_LOPEZ on 2025-06-30** — the most recent edit

### 4.2 `ZFIX_EXCHANGERATE_AVC` — Enhancement 3 (finance posting AVC, added 2025-07-02)

Runs on `u_t_fmifiit` (the new FI items being posted) and `c_t_avc` (the AVC totals being computed). For each new item whose `check_conditions` passes, finds the matching `c_t_avc` row via `rfpos = knbuzei` and overwrites its `fkbtr` with the BR-converted value.

Explicit comment in source: `*02/07/2025 Adding Check in finance Posting.` — this was **your own fix** on 2025-07-02, presumably in response to a prior incident.

### 4.3 `ZFIX_EXCHANGERATE_CHECK_CONS` — Enhancement 1 & 2 (earmarked-fund availability check)

- **Hook:** Class `CL_FM_EF_POSITION` method `CHECK_CONSUMPTION` (enhancement 1 = Start, 2 = End)
- **Master gate:** ✅ `check_br_is_active`
- **Loop:** `LOOP AT m_t_addref`
- **Per-row gate:** `check_conditions(iv_waers = m_r_doc->m_f_kblk-waers, ...)` ⚠ Note: this is the **consumption document header currency**, not the FR reference currency!
- **Conversion:** `convert_to_currency(foreign = <yyls_addref>-ref-wtges, foreign_currency = <yyls_addref>-ref-waers, local_currency='USD')`
- **Save/restore pattern:** Enhancement 1 saves `m_t_addref` to `yylt_addref_save`, overrides `hwges`/`hwgesapp`, then Enhancement 2 restores the original if `yylv_upd_done = abap_true`. So the override is **in-memory for the duration of the standard `CHECK_CONSUMPTION` check, then rolled back**. The persisted data is never touched here.

### 4.4 `ZFIX_EXCHANGERATE_NEW_ITEM` (FMIOI item creation)

- **Hook:** `VFH_FUNDS_CHECK_OI` enhancement spot → `CREATE_NEW_ITEM_FA`
- **Master gate:** ✅ `check_br_is_active`
- **Per-item gate:** `check_conditions(iv_waers=c_f_fmoi-twaer, ...)`
- **Conversion targets (ALL at `iv_local_currency='USD'` using default EURX):** `c_f_fmoi-fkbtrorig`, `c_f_fmoi-fkbtrorig_max`, `c_f_fmoi-fkbtrredu`, `c_f_fmoi-fkbtradjst`, `c_f_fmoi-split`
- **Extra logic (line 22-26, dated 11/08/2025):** merges `TRBTRREDU` with `TRBTRADJST` before recalculation — this is an absorption fix for transaction reductions from cross-period adjustments.
- **Reduction recalculation (line 32-37):** `i_convfactor = trbtrorig / fkbtrorig; i_trbtrredu = (fkbtrredu + revsum + fkbtradjst) × i_convfactor`. This backs out the reduction EUR value from the USD values using the ratio of the original amounts — ensures the ratio stays consistent.

### 4.5 `ZFIX_EXCHANGERATE_FI` — Enhancement 2 (actual FI posting → FMIFIIT)

- **Hook:** `SAPLF*` (not confirmed from extract path) → `GENERATE_FM_DOC` or similar
- **Master gate:** ✅ `check_br_is_active`
- **Loop:** `LOOP AT u_t_fmifihd ... LOOP AT u_t_fmifiit WHERE fmbelnr = ...`
- **Per-item gate:** `check_conditions(iv_waers=<ls_fmifiit>-twaer, ...)`
- **Audit write:** `CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT'` — stores the pre-BR `fmifiit` row in `YTFM_BR_FMIFIIT` (either inline if `u_flg_update = con_off`, or in update task otherwise)
- **Conversion:** `convert_to_currency(foreign=<trbtr>, foreign_currency=<twaer>, local_currency='USD')` → `<ls_fmifiit>-fkbtr = yylv_amount`
- **Reinit trigger:** `INSERT yyls_avc_fund INTO TABLE yylo_br_exchange_rate->mt_avc_fund.` then `SET HANDLER yylo_br_exchange_rate->fmavc_reinit_on_event.` → the "INCREDIBLE SOLUTION" (see §3.8)

### 4.6 `ZFIX_EXCHANGERATE_KBLEW`

- **Hook:** `CL_FM_EF_POSITION → CREATE_KBLEW_ENTRIES`
- **Master gate:** ✅ `check_br_is_active`
- **Logic:** find the curtype-00 (transaction currency) row in `c_t_kblew`, if `check_conditions` passes, find the matching curtype-10 (local currency = USD) row and overwrite `wrbtr`/`wrbtrapp` with the BR-converted value via `convert_to_currency(..., iv_local_currency = <ls_cc_kblew>-waers)`.
- Note: this is the only enhancement that **does not hardcode `'USD'`** for `iv_local_currency` — it uses the target KBLEW row's `waers` field, which happens to be USD at UNES.

### 4.7 `ZFIX_EXCHANGERATE_PAYCOMMIT`

- **Hook:** `SAPLMR1M → GET_FA_COMMIT_DATA`
- **Master gate:** ✅ `check_br_is_active`
- **Loop:** `LOOP AT t_reftab` (the reference/commitment data table for intermediate commitments)
- **Per-row gate:** `check_conditions(iv_waers = <yyls_reftab>-waers, ...)`
- **Conversion:** `convert_to_currency(foreign = <wtges>, foreign_currency = <waers>, local_currency = <hwaer>)` → `<hwges>` (uses the row's own local currency, not hardcoded USD)

### 4.8 `ZFIX_EXCHANGERATE_FUNDBLOCK` — Enhancements 2 & 3 (KBLD screen for FR manual entry)

- **Hook:** `SAPMKBLD` — dynpro for FMX1/FMX2 manual fund reservation
- **Master gate:** ✅ `check_br_is_active`
- **Per-screen gate:** `check_conditions(iv_waers = kbld-waers, ...)`
- **Enhancement 2:** `convert_to_currency(foreign = kbld-wtges, ...)` → `kbld-hwgesapp = yylv_amount` ⚠ **Only updates `hwgesapp`, not `hwges`.** Potential inconsistency between these two screen fields if standard SAP populates `hwges` separately.
- **Enhancement 3:** `get_exchange_rate(iv_date = kbld-wwert, ...)` → `kbld-kursf = yylv_exchange_rate` — pushes the BR rate into the screen `kursf` (exchange rate) field for display.

Despite the "Screen-Not used" label in the composite short text (step 99), the code is alive and active.

### 4.9 `ZFIX_EXCHANGERATE_PBC_POS_UPD` — **explicitly deactivated**

```abap
CHECK 1 = 2.   "Deactivated the 2024/01/08
```

Line 10 — hard deactivation. Everything after is dead code. Comment documents the deactivation date. The code that follows handles PBC (Personnel Budget Control) posting conversion to BR, including a USD-handling branch at line 57:

```abap
IF cs_pos-waers = 'USD'.
  yylo_br_exchange_rate->convert_to_currency_2( ... ).
ENDIF.
```

This is the **only place in the entire enhancement family** where `convert_to_currency_2` is called without being wrapped in `IF 1 = 2.` — and the whole enhancement is deactivated via `CHECK 1 = 2.` on line 10 before it reaches that point.

---

## 5. Known failure modes

| # | Failure mode                                                                                                  | Evidence                                                                                                           |
|---|---------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| 1 | **USD consumption postings bypass BR entirely** (Hypothesis 0 — **proven**).                                   | `mr_waers` contains only `'EUR'`; `check_conditions` rejects `iv_waers='USD'` → enhancement is skipped for USD.   |
| 2 | All Staff-logic USD-handling branches are **dead code** (`IF 1 = 2.` guards in AVC/CHECK_CONS/NEW_ITEM/FI/KBLEW/PAYCOMMIT). | Inline `IF 1 = 2.` in every enhancement; explicit comment `"Staff logic on hold"` throughout.                     |
| 3 | `ZFIX_EXCHANGERATE_PBC_POS_UPD` (the only enhancement with active USD handling) is **hard-deactivated** since 2024/01/08. | `CHECK 1 = 2.   "Deactivated the 2024/01/08` on line 10.                                                          |
| 4 | `ZFIX_EXCHANGERATE_FUNDBLOCK` Enhancement 2 only updates `kbld-hwgesapp`, not `kbld-hwges`.                    | Line 24 of FUNDBLOCK === E.                                                                                        |
| 5 | Five enhancement members (`FM_DOC_UPD`, `FM_POS_UPD`, `POPOST`, `REDUCE`, `REDUCE_1`) appear in TADIR but are NOT loadable at runtime. `FM_DOC_UPD` + `REDUCE_1` have explicit `DELETED` entries in ENHLOG. `FM_POS_UPD`, `POPOST`, `REDUCE` return *"ENHO cannot be read"* when accessed via `cl_enh_factory=>get_enhancement`. **They are zombie entries with no runtime effect.** The live BR behavior is entirely driven by the 8 enhancements extracted in §4 + the class in §3. |

---

## 6. The budget rate source — **confirmed TCURR `EURX`**

`CONVERT_TO_CURRENCY` default parameter:
```abap
methods CONVERT_TO_CURRENCY importing !IV_TYPE_OF_RATE type KURST_CURR default 'EURX' .
```

`GET_EXCHANGE_RATE` hardcodes it:
```abap
CALL FUNCTION 'READ_EXCHANGE_RATE'
  EXPORTING type_of_rate = 'EURX'.
```

No callers override the default. **The Budget Rate = TCURR[KURST='EURX']**. Rate maintenance is an independent UNESCO process (TVARVC activation date is `20240101`, but that only toggles the gate — the actual rates are maintained directly in TCURR via OB08 or an update job).

---

## 7. Related artifacts

- **Class source:** `extracted_code/CLAS/YCL_FM_BR_EXCHANGE_RATE_BL/` (21 files)
- **Enhancement sources:** `extracted_code/ENHO/ZFIX_EXCHANGERATE/` (8 files)
- **Live incident using this solution:** `knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md`
- **Legacy archaeology (4.6 era, all commented out):** `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU09/10/12_RPY.abap` — reference to a historic "dollar constant" validation that was replaced by this class-based solution.
- **AVC derivation side (orthogonal):** `knowledge/domains/PSM/EXTENSIONS/avc_derivation_technical_autopsy.md`

---

*Stored in `knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md`*
*Session #052 — 2026-04-10 — live extraction from D01 + code review*
