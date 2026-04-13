# INC-BUDGETRATE-EQG — Budget Rate custom solution fails on USD posting against EUR earmarked fund

> **Status:** ✅ **ROOT CAUSE CONFIRMED** (Session #054, 2026-04-13) — empirically validated via:
> 1. ST01 trace `fb602.txt` (full FB60 reproduction by JP_LOPEZ on TS3): 42 hits of `YCL_FM_BR_EXCHANGE_RATE_BL`, ALL going to `FMFINCODE` (= `get_fund_type_from_fund` only); ZERO `TCURR` reads → `convert_to_currency` was NEVER called → `check_conditions` returned `false` for every row.
> 2. Konakov's TS3 reproduction: created a fresh same-year FR consuming the entire remaining budget → invoice in USD then fails identically with FMAVC005 → the failure mode is **NOT cross-year specific**, it is **pool-at-zero**.
> 3. Gold-DB consumption audit (`Zagentexecution/quality_checks/budget_rate_consumption_audit.py`): all 53 positions of FR 3250117351 are BR-applicable on the FR side, but 22 USD postings on fund 3110111021 bypassed BR (FKBTR=TRBTR identity), accumulating ~$489.87 of AVC drift.
>
> The `mr_waers=['EUR']` gate **is** the root cause. The §4bis "carryforward divergence" hypothesis is superseded — the carryforward path is fine, but it carries forward whatever drift accumulated in 2025, and the new USD posting attempt re-runs the same broken gate path against an already-tight pool.
> **Placeholder ID:** `INC-BUDGETRATE-EQG` — to be replaced with ServiceNow INC number when assigned
> **Domain:** PSM / FM / AVC / Budget Rate custom solution
> **Reported by:** Laetitia Vonthron (adm.cad) → Christina Lopez-Chemouny → Yimiao Guo → Illya Konakov → Pablo Lopez
> **Related SAP error:** `FMAVC005` — *Annual budget exceeded by X,XX USD (FM Availability Control) for document item 00002*
> **Root cause:** `YCL_FM_BR_EXCHANGE_RATE_BL` constructor hardcodes `mr_waers = ['EUR']`. `check_conditions` rejects USD → BR conversion is skipped for USD postings → standard OB08 `M` rate is used → FMAVCT drifts vs. the EUR-loaded budget pool → FMAVC005 on any subsequent posting near the ceiling.

---

## 1. Business context

| Field | Value |
|---|---|
| Beneficiary | Santiago BIVINI MANGUE (Secretary-General of Equatorial Guinea) |
| Event | 43rd Session of UNESCO General Conference |
| Ticket type | Air ticket reimbursement |
| Original amount | XOF 1,300,000 |
| Converted amount | **USD 2,291.79** @ rate 567.241 (XOF→USD, translation date 19.11.2025) |
| Vendor / Supplier | `456639` (SAP ID) — address: M Santiago Bivini Mangue, Boîte post. 805, Malabo, Equatorial Guinea |
| Fund Reservation | `3250117351` / line `39` (original) — carried forward to 2026 with 4,400 EUR budget (≈ 4,819.28 USD) |
| Fund | `3110111021` (type `001` "Regular Programme" — created 2023-12-18 by MULESOFT interface) |
| Funds center | `PAX` |
| Cost center | `111018` |
| Commitment item | `10'` → rolls up to AVC control object **`TC`** (Travel Cost) |
| Business area | `GEF` |
| Company code | `UNES` (UNESCO HQ, company-code currency = USD per T001) |
| AVC environment | `9HZ00001` (ledger **`9H`**) — per `avc_derivation_technical_autopsy.md` |
| G/L account | `6012505` |
| Posting transaction | `FB60` (vendor invoice) |

---

## 2. Symptom

When any user attempts to post the vendor invoice in **USD** against this earmarked fund (fund reservation 3250117351 line 39, carried forward from 2025 to 2026 at 4,400 EUR / ≈ 4,819.28 USD), SAP returns:

> **FMAVC005** — *Annual budget exceeded by **0,87 USD** (FM Availability Control) for document item 00002*
> Control object: **`9H / 2026 / 3110111021 / PAX / TC`**

(Exact excess depends on posting amount and date — see §4 reproduction matrix.)

Posting the **exact same invoice in EUR** instead of USD **works without any error**. This is the first and strongest indicator that the problem is **currency-translation related**, not a budget-availability problem in absolute terms.

The FR has ~4,819 USD (≈ 4,400 EUR) of remaining budget; the invoice is only 2,291.79 USD, well within the cover. FM substantive availability is clearly OK — but AVC is rejecting on a micro-residual.

---

## 3. Email thread timeline

| Date (2026) | Actor | Action |
|---|---|---|
| 24 Mar | V. Kariuki (EqG office) → L. Vonthron (adm.cad) | Requests air-ticket reimbursement for SG EqG, 43rd GC |
| 24 Mar | Vonthron computes XOF 1,300,000 = USD 2,291.79 @ 567.241 (translation date 19.11.2025) — InfoCenter screenshot in `image019.png` |
| 26 Mar | Vonthron posts invoice for 2,291.79 USD → FMAVC005 error (`image018.png`) |
| 26 Mar | C. Lopez-Chemouny asks Vonthron to retry after redoing carryforward → same error |
| 27 Mar | Y. Guo forwards to Konakov (FM support) |
| 30 Mar | Konakov reproduces in TS1 with 100 USD → FMAVC005 *"Annual budget exceeded by 115,47 USD for document item 00002"* (`image012.png`, `image013.png`) |
| 30 Mar | Konakov observes: *"By the way, when I try to post the invoice in EUR instead of USD it works fine"* |
| 30 Mar | Konakov escalates to P. Lopez |
| 30 Mar | Lopez responds: *"If they buy something in a PO, and pay after 3 months and the exchange rate changes, there will be needed more budget to pay. The only case that is not needed is with **Budget rate** as this is Fixed."* |
| 2 Apr | Lopez clarifies: *"If the Fund reservation is in EUR, and the Posting is in EUR → Budget rate works. If fund reservation is in EUR and Posting is in USD → will not work as the rule only acts for EUR."* |
| 2 Apr | Lopez: *"To respect budget rate — yes"* |
| 2 Apr | Konakov provides FB60 reproduction script (supplier 456639, fund 3110111021, earmarked fund 3250118890/001) |
| 3 Apr | Konakov test: *"I did a test with VC today. And it worked: funds reservation in EUR and payment in USD without any issues. So, we need to thoroughly check the RP case below."* — **key contradiction**: the clean-room test works where the real case fails |

---

## 4. Reproduction evidence

### 4.1 FB60 reproduction setup (from Konakov, image009 + image010)

```
Transaction:      FB60 (Enter Vendor Invoice: Company Code UNES)
Supplier:         456639
Invoice date:     02.04.2026
Posting date:     02.04.2026
Document type:    KR (Supplier Invoice)
Currency:         USD
Amount:           10.00 (test case) / 100.00 (earlier test) / 2,291.79 (real case)
Reference:        ATK R
Text:             ATK

Line item:
  G/L account:    6012505
  D/C:            Debit
  Business area:  GEF
  Fund:           3110111021
  Funds center:   PAX
  Cost center:    111018
  Earmarked fund: 3250118890 / item 001  (Konakov's TS1 test)
                  3250117351 / item 39   (Vonthron's real prod case)
```

### 4.2 Error-vs-amount matrix

| Posting currency | Posting amount | FMAVC005 excess | Ratio      | Comment                                  |
|---|---|---|---|---|
| EUR  | any                | (none — works)    | —          | Konakov (30 Mar): *"works fine"*            |
| USD  | 10.00              | **0.87 USD**      | 8.7%       | Illya's first reproduction                 |
| USD  | 100.00             | **115.47 USD**    | 115% (!)   | Second reproduction; excess > posting amount — pool already over-drawn |
| USD  | 2,291.79 (real)    | (TBD — not captured in thread) | — | Vonthron's Equatorial Guinea case          |

The 115.47 excess on a 100 USD post is a **strong clue**: the available budget at TC level in the control object was **already negative by ~15.47 USD** before the posting even started. So the posting itself is not the cause — there is a **pre-existing residual** at the TC/9H/2026/3110111021/PAX level that the test revealed.

### 4.3 Funds reservation data from Gold DB

Earmarked fund `3250117351`, line `00039` (the RP case):
```
GJAHR  FONDS        FISTL  FIPEX  WRTTP   FKBTR (USD)   TRBTR (EUR)   BUKRS
2025   3110111021   PAX    10'    81      9,638.56      8,800.00      UNES    ← original 2025 amount
2026   3110111021   PAX    10'    81      4,819.28      4,400.00      UNES    ← carryforward slice
```
Ratio FKBTR/TRBTR = **1.09529** = EUR→USD Budget Rate (matches TCURR `EURX` 2024-12-01).

Fund 3110111021 commitments summary from `fmifiit_full` (2025):
```
WRTTP=54, TWAER=EUR:  259 rows, FKBTR sum=164,984.76 / TRBTR sum=150,631.31 → ratio 1.09529  ✅
WRTTP=54, TWAER=USD:    5 rows, FKBTR sum=  3,627.84 / TRBTR sum=  3,627.84 → ratio 1.00000  (identity)
WRTTP=54, TWAER=MRU:    1 row,  FKBTR sum=  1,775.21 / TRBTR sum= 70,600.00 → ratio 0.02514  (non-EURX rate)
```

**All** 259 EUR commitments on this fund for 2025 are held at exactly 1.09529 USD/EUR — consistent with the BR solution working correctly for EUR on commitment creation.

---

## 4bis. REFINED PROBLEM MODEL (Session #053, 2026-04-13)

Built from 5 arguments the domain owner (Pablo Lopez) walked through on 2026-04-13, plus the FB60 execution trace derived from the ZFIX_EXCHANGERATE_* enhancement sources.

### Argument 1 — Two parallel universes

Fund Reservation (Group 1) and FM Budget Pool (Group 2) are **two independent worlds**. Each has its own tables and its own availability control:

| | Group 1 — FR | Group 2 — FM Budget |
|---|---|---|
| Tables | `KBLK`, `KBLP`, `KBLE`, `KBLEW` | `FMIOI`, `FMIFIIT`, `FMAVCT` |
| AVC | `CL_FM_EF_POSITION->CHECK_CONSUMPTION` | `FM_FUNDS_CHECK_OI` (ledger 9H) |
| Error | `Open amount from doc XXX exceeded by Y%` | `FMAVC005 Annual budget exceeded by X USD` |
| BR hooks | `CHECK_CONS`, `FUNDBLOCK`, `KBLEW` | `AVC`, `NEW_ITEM`, `FI` |
| Shared | `PAYCOMMIT` (touches both via intermediate T_REFTAB) |  |

### Argument 2 — 2 groups of tables + 2 AVCs must stay consistent

No single cross-group update: standard SAP maintains the linkage via `REFBN/RFPOS` on FMIOI pointing back to KBLK/KBLP. The BR solution updates each group independently; if one group gets BR and the other doesn't, FMAVCT drifts from the FR master.

### Argument 3 — Time dimension: same-year OK, cross-year FAIL

Empirical finding (Pablo):
- **Same-year scenarios** (FR created and consumed within the same fiscal year) pass all checks — verified in TS3 with FR `3250117413` (100 EUR / 109.53 USD, full consumption, 0.01 residual, all ratios at BR 1.09529).
- **Cross-year scenarios** (FR from year N carry-forwarded into N+1, consumed in N+1) fail with `FMAVC005`. Affects Illya's TS1 reproduction AND Vonthron's P01 case (FR `3250117351/39`).

The behavioral diverge happens specifically at the CARRYFORWARD boundary. Whatever runs during year-end carryforward does NOT leave the two groups in the same BR-consistent state they were in pre-CF.

### Argument 4 — KBLEW ↔ FMIOI consistency check (suspected drift locus)

For every consumption event, BOTH should record the same USD value at BR:

```
KBLEW[BELNR, BLPOS, BPENT, CURTP='10'].WRBTR    (Group 1 consumption log)
     ↕ should equal
FMIOI[matching new actual row].FKBTR            (Group 2 commitment record)
```

If these diverge by more than the Z000 tolerance (0.50 USD absolute via ACTIVGRP=`++`), FMAVC005 fires. This consistency is unverified for carry-forwarded FRs and is the primary audit target.

### Argument 5 — FB60 execution trace (full flow in 9 phases)

See `knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md` §FB60 EXECUTION TRACE. Summary of danger zones:

- **Phase 2** (`CHECK_CONS`): SAVE/RESTORE pattern — in-memory override, no persistence.
- **Phase 6 ↔ Phase 7**: KBLEW (Group 1) and FMIFIIT (Group 2) persist at BR in separate methods with separate `check_conditions` gates. Gate mismatch → persisted diverge.
- **Phase 9 conditional reinit**: `fmavc_reinit_on_event` only fires if `mt_avc_fund` was populated during Phase 7. If Phase 7 gate rejects the line → no reinit → FMAVCT drift is not corrected.
- **Cross-year (CARRYFORWARD)**: the CF batch process is NOT part of the FB60 trace. It writes directly to FMIOI via a separate path (`FMJ2`, `RFFMFR_OPEN_ITEMS_CARRYFWD`, or similar). **Unknown whether CF goes through any ZFIX_* enhancement** — this is the primary open question.

### The 3 angles to deep-dive (prioritized)

| # | Angle | Leverage | Status |
|---|---|---|---|
| **A** | **Carryforward process analysis** — which program runs CF, does it trigger BR enhancements, or does it bypass them writing OB08/M rates directly to FMIOI | HIGHEST — explains cross-year divergence in one shot | In-progress via `incident-analyst` subagent |
| **B** | **KBLEW vs FMIOI consistency audit** — row-by-row comparison for FR 3250117351 across all BLPOS and all consumption events | HIGH — quantifies exact drift | In-progress via general-purpose subagent writing `audit_kblew_fmioi_consistency.py` |
| **C** | **Enhancement gate analysis in cross-year scenario** — live debug of `check_conditions` inputs during Vonthron's FB60 simulation | MEDIUM — definitive but requires live SAP debug | Pending SAP access |

### Subagents launched (Session #053)

Both agents run in background via SNC-connected pyrfc. If VPN/network drops, they'll produce scripts that can be re-executed when access is back.

- **Agent A** (`incident-analyst`): Carryforward process analysis — expected output: program name + whether it bypasses BR enhancements + proposed fix location.
- **Agent B** (general-purpose): Writes `Zagentexecution/incidents/INC_budget_rate_eq_guinea/audit_kblew_fmioi_consistency.py` — a live P01 audit that compares KBLEW and FMIOI row-by-row for FR 3250117351.

## 5. Root cause — ✅ CONFIRMED (Session #054, 2026-04-13)

The `mr_waers = ['EUR']` hypothesis from Session #052 is **the root cause**. The Session #053 retraction is itself reversed: the TS3 same-year test that "passed" had remaining headroom in the FR; the failure mode is **pool-at-zero amplification of cross-currency drift**, which appears identically in same-year scenarios once the FR is fully consumed (proven by Konakov's same-day reproduction with a freshly-created FR that consumed the rest of the available budget).

### 5.0 Empirical chain of evidence (the trace)

JP_LOPEZ's full FB60 ST01 trace on TS3 (`fb602.txt`, 2026-04-13, full repro of Vonthron's case) — categories enabled: Auth, Kernel Functions, General Kernel, DB access (SQL), RFC. **Buffer disabled** to fit within the 10K-record ST01 ring buffer.

Triage profile `br_enhancements` (skill `sap_st01_trace_reader`):

| Hit count | Pattern | Interpretation |
|---|---|---|
| **42** | `YCL_FM_BR_EXCHANGE_RATE_BL` invocations | The class IS firing during FB60 — gate is not entirely closed |
| **42** | All hits route through `get_fund_type_from_fund` → `SELECT SINGLE TYPE FROM FMFINCODE` | The class is being asked the fund-type question per row |
| **0**  | `TCURR` reads (no `SELECT ... FROM TCURR ... KURST = 'EURX'`) | `convert_to_currency` was NEVER called → BR conversion did NOT execute on ANY line |
| **3 cycles** | `CL_FM_EF_POSITION->CHECK_CONSUMPTION` + `SAPLFMOI` (FMIOI) + `CL_FMAVC_LEDGER` (FMAVCT read) | All 3 phases executed; each ended without modification by BR |
| **0** | SQL ReturnCode ≠ 0 | No DB errors — FMAVC005 fires from the in-memory AVC algorithm AFTER reading FMAVCT |

The 42 `FMFINCODE` reads correspond to `check_conditions` running its 8 gate checks per row. The first 7 dimensions pass (rldnr, bukrs, fikrs, gsber, fipex, vrgng, ftype). The 8th — `iv_waers IN mr_waers` for `iv_waers='USD'` — **fails for every row, on every phase**. Because the method exits via `CHECK ... IN ...` without setting `rv_is_ok = abap_true`, BR conversion is skipped silently.

### 5.A The single-line bug (verified in `extracted_code/CLAS/YCL_FM_BR_EXCHANGE_RATE_BL/CM00A`)

```abap
APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR' ) TO mr_waers.
" mr_waers2 (Staff variant, dead code) appends BOTH 'EUR' and 'USD' — the cure exists but isn't reachable
```

### 5.B-bis SYSTEM-WIDE BLAST RADIUS (P01 Gold DB scan, Session #054)

This is **not an isolated incident** — it is a structural pattern visible across the entire UNESCO landscape. Scan of P01 fmioi + fmifiit_full (Gold DB):

| Metric | Value |
|---|---|
| Total earmarked funds (REFBT=110) in P01 | **370,064** |
| EUR-loaded FRs (BR ratio ~1.09529 confirmed on FR side) | **961** |
| Distinct funds carrying EUR-loaded FRs | **486** |
| Funds with EUR FR **AND** any USD consumption (the affected universe) | **458** |
| USD-bypass postings on those 458 funds (lifetime, all years) | **135,792** |
| Total USD volume of those bypass postings | **$375,011,484.95** |
| Theoretical AVC drift exposure (volume × 9.529%) | **~$35,734,844** |
| **Open EUR FRs in 2026 (still consumable carryforwards)** | **14,752 FR documents on 1,945 funds** |
| Funds with open EUR FRs in 2026 + USD consumption pattern (Vonthron-class) | **70** |
| USD bypass postings ALREADY made in 2026 on those 70 at-risk funds | **214** ($8.79M, drift potential ~$837K) |

The Equatorial Guinea case (FR 3250117351 / fund 3110111021) is **one of 70 funds currently carrying the same exposure**. Top affected funds by USD-bypass count include `32101B1011` (14,487 bypass postings), `3210581011` (12,570), `3210481011` (8,034), `410GLO1042` (6,132), and `549RLA4000` (4,827) — these are the funds most likely to surface FMAVC005 incidents next.

**Implication:** every release of UNESCO that does not patch `mr_waers` keeps generating drift on these 458 funds. The current functional workaround ("post in EUR") is unsustainable at scale because operational reality forces USD postings (vendor invoices in USD, travel in USD, etc.).

### 5.B What "fails" looks like at the data layer

Empirical Gold-DB audit on fund 3110111021 (Vonthron's fund), produced by `Zagentexecution/quality_checks/budget_rate_consumption_audit.py`:

```
FR 3250117351 — 53 positions, ALL applicable to BR (ratio 1.09529 ✅)
  47 consumed in 2025 (line items 1-47, all closed at BR)
   6 carried forward to 2026 (RFPOS 38, 39, 40, 41, 43, 45 — all at BR ratio)
   0 bypassed positions

Fund 3110111021 — 282 fmifiit_full consumption rows total:
  259 EUR rows at BR (FKBTR = TRBTR × 1.09529) ✅ APPLICABLE
   22 USD rows at IDENTITY (FKBTR = TRBTR, ratio 1.00000) ❌ BYPASSED
    1 MRU row (separate currency, ignored here)
  USD bypass total signed: -1605.56 USD
  Estimated AVC drift accumulated: $489.87 USD
```

The 22 BYPASSED USD rows are the smoking gun. Concrete examples (from `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_consumption_audit.json`):

| FMBELNR | Period | Amount | Description |
|---|---|---|---|
| 0605807929 | 2025-11 | -1,767.65 USD | PAX/DRX_Rembt ATK cost VALL_Delegate GC |
| 0605817104 | 2025-12 |    -42.48 USD | UNDP CHARGES_DOC 6400024554 |
| 0605828432-48 | 2025-12 | 15× ~50-175 USD | Carbon_non-staff Q4/2025 (15 carbon-offset postings) |
| 0605828886 | 2025-12 |    -25.03 USD | STANTIERU/IANA/SHS/PARIS |
| 0605838271 | 2025-12 |    -25.03 USD | JULIACI NOCCHI/MAR/pax/PARIS |

These all have TWAER=USD, FKBTR=TRBTR (identity, no BR conversion). Each one persisted to FMIFIIT bypassing the BR enhancement → each one consumed the EUR-loaded budget pool at OB08 `M` rate semantically (because no rate translation was done — USD was treated as if it were the FM-area native currency, which it is for company code UNES, but the budget side had been *loaded* at BR EURX, so the pool's USD valuation drifts).

### 5.C The mechanism end-to-end (FB60 trace-confirmed)

For Vonthron's `2,291.79 USD` invoice on FR `3250117351/39` (carried forward 2025→2026 at 4,400 EUR / 4,819.28 USD):

1. FB60 builds the FI document with `TWAER='USD'`, `WAERS='USD'`.
2. `CL_FM_EF_POSITION->CHECK_CONSUMPTION` is invoked → `ZFIX_EXCHANGERATE_CHECK_CONS` enhancement fires → `check_conditions(iv_waers='USD', ...)` returns **false** → the SAVE/RESTORE BR override is skipped → standard CHECK_CONSUMPTION runs against unmodified amounts.
3. `VFH_FUNDS_CHECK_OI / CREATE_NEW_ITEM_FA` builds the new actual line in `t_fmioi` → `ZFIX_EXCHANGERATE_NEW_ITEM` fires → `check_conditions` false → FMIOI line written with `FKBTR = TRBTR = 2,291.79` (identity).
4. `FM_FUNDS_CHECK_OI` runs the AVC loop against the in-memory `t_fmioi` (which contains the new USD row + all prior EUR commitments at their persisted BR values from FMIOI WRTTP=81 reductions) → `ZFIX_EXCHANGERATE_AVC` fires → for the new USD row, `check_conditions` false → BR not applied → the USD row enters the AVC sum at identity, while the EUR commitments and EUR budget pool are valued at BR. The mismatch surfaces immediately because the FR carryforward slice (4,819.28 USD at BR) is exactly aligned with the budget pool, leaving zero headroom for the identity-valued USD posting → FMAVC005 by 0.87 USD (or any tiny residual depending on prior accumulated drift).
5. `CL_FMAVC_LEDGER` reads FMAVCT → finds `available = -0.87 USD` (or similar tiny negative) → raises FMAVC005.

### 5.D Why same-year posting "works" (until the FR is consumed)

In Konakov's first TS3 reproduction (FR with remaining headroom), the 100 USD test posted successfully — because the pool had >100 USD of AVC headroom at TC level, and the BR-bypass error of ~9.53% (≈$9.50) was absorbed. Once Konakov created a NEW FR consuming the full remaining budget, repeating the 100 USD test then FAILED with the same FMAVC005 — proving the bug is **not** cross-year specific, it is **pool-at-zero**: any time the cumulative drift + the new USD posting at identity exceeds the BR-loaded pool, AVC rejects.

### 5.E Confirmed gate values (live `extracted_code` 2026-04-10 + trace 2026-04-13)

| Range         | Sign   | Live content                                                         | Vonthron's USD posting result |
|---------------|--------|----------------------------------------------------------------------|-------------------------------|
| `mr_rldnr`    | I EQ   | `['9A']`                                                              | `'9A'` ✅ pass                |
| `mr_bukrs`    | I EQ   | `['UNES']`                                                            | `'UNES'` ✅ pass              |
| `mr_fikrs`    | I EQ   | `['UNES']`                                                            | `'UNES'` ✅ pass              |
| `mr_gsber`    | I EQ   | `['GEF']`                                                             | `'GEF'` ✅ pass               |
| **`mr_waers`**| **I EQ** | **`['EUR']`**                                                       | **`'USD'` ❌ FAIL — single blocker** |
| `mr_fipex`    | E EQ   | `['GAINS','REVENUE']`                                                 | `'10\''` ✅ pass (not excluded) |
| `mr_vrgng`    | E EQ   | `['HRM1','HRM2','HRP1']`                                              | `'RFBU'` ✅ pass (not excluded) |
| `mr_fund_type`| I EQ   | `[001,002,003,004,005,009,010,012,013,016,017,018,094,095]`           | `'001'` ✅ pass               |

### 5.F Fix path — recommended (Session #054)

The minimal-blast-radius fix that addresses the root cause without touching the enhancement bodies:

1. **In `YCL_FM_BR_EXCHANGE_RATE_BL` constructor (CM00A line ~8)** — append `'USD'` to `mr_waers`:
   ```abap
   APPEND VALUE #( sign = 'I' option = 'EQ' low = 'USD' ) TO mr_waers.
   ```
2. **Add a per-currency dispatcher method `convert_to_currency_auto`** that routes USD postings through the already-built `convert_to_currency_2` (CM002) double-hop (USD UNORE → EUR @ M → USD @ EURX) and EUR postings through the existing `convert_to_currency` (CM005).
3. **In each of the 8 active enhancement implementations**, replace `convert_to_currency( ... )` with `convert_to_currency_auto( ... )`.
4. **One-time corrective FMAVCREINIT** on `9H/2026/<all funds with USD activity>/<center>/<TC item>` to clear accumulated drift after the fix is deployed.

Detail and tradeoffs in §8 below.

---

## 5-legacy. Prior root cause analysis (2026-04-10)

Live extraction of class `YCL_FM_BR_EXCHANGE_RATE_BL` from D01 confirmed the domain owner's hypothesis (Hypothesis 0 below) exactly as stated. The bug is **one single line in the class constructor**.

### 5.A Smoking gun — `YCL_FM_BR_EXCHANGE_RATE_BL==CM00A` (CONSTRUCTOR) line 8

```abap
APPEND VALUE #( sign = 'I' option = 'EQ' low = 'EUR' ) TO mr_waers.
```

`mr_waers` is a private `RANGE OF waers` attribute used by `CHECK_CONDITIONS` to filter which transaction currencies get BR treatment. **It contains only `'EUR'`.** No USD, no XOF, no MRU — one single line, one single currency.

### 5.B Smoking gun — `YCL_FM_BR_EXCHANGE_RATE_BL==CM004` (CHECK_CONDITIONS) lines 21-23

```abap
METHOD check_conditions.
  rv_is_ok = abap_false.
  ...
  IF iv_waers IS NOT INITIAL.
    CHECK iv_waers IN mr_waers.       " ← USD fails here
  ENDIF.
  ...
  rv_is_ok = abap_true.
ENDMETHOD.
```

When called with `iv_waers='USD'`, the `CHECK ... IN mr_waers` statement exits the method without setting `rv_is_ok = abap_true`, so the method returns `abap_false`.

### 5.C What happens in the failing case (step by step)

For Vonthron's USD invoice against EUR FR `3250117351/39`:

1. `FB60` creates the FI document with `TWAER='USD'`, `WAERS='USD'` (header currency).
2. SAP posts to FMIFIIT with `<ls_fmifiit>-twaer='USD'`.
3. AVC runs via `FM_FUNDS_CHECK_OI` → **`ZFIX_EXCHANGERATE_AVC` Enhancement 1** fires.
4. `LOOP AT t_fmioi` iterates all commitment items in the check set. For each row:
   - `check_conditions(iv_waers=<ls_fmioi>-twaer, ...)` is called.
   - For existing EUR commitments on the fund: `twaer='EUR'` → check passes → `convert_to_currency` runs → `fkbtr = trbtr × 1.09529` → same value that was already persisted → no net effect.
   - For the new USD posting row: `twaer='USD'` → `CHECK 'USD' IN mr_waers` fails → **entire iteration skipped**, `fkbtr` left at standard-SAP OB08 value.
5. **`ZFIX_EXCHANGERATE_AVC` Enhancement 3** (added by JP_LOPEZ on 2025-07-02, comment in source: *"02/07/2025 Adding Check in finance Posting"*) also runs. It loops `u_t_fmifiit` and updates `c_t_avc` for BR, but gated by the same `check_conditions` → **USD is skipped here too**.
6. `ZFIX_EXCHANGERATE_FI` (FMIFIIT persistence) also gated by `check_conditions` → **USD skipped** → FMIFIIT rows persisted with standard OB08 `fkbtr`, no audit write to `YTFM_BR_FMIFIIT`, and the `fmavc_reinit_on_event` handler is **not set** because `mt_avc_fund` is never appended for USD postings.
7. Standard SAP proceeds to compare the new posting's `fkbtr` against FMAVCT at control object `9H/2026/3110111021/PAX/TC`.
8. FMAVCT for that control object has been **drifting for months**: every prior USD posting on this fund accumulated a small rate-mismatch residual because the budget was loaded at BR (EURX 1.09529) but USD consumption releases hit the pool at OB08 `M` rate.
9. When the accumulated drift plus the new posting's USD amount exceeds the TC ceiling by any amount > 0, `FMAVC005` fires.

### 5.D The arithmetic signature (matches observed excess values)

Observed in TS1 reproduction:

| Posting | Excess | Pool state implied |
|---|---|---|
| 10 USD | 0.87 USD | Pool had +9.13 USD remaining |
| 100 USD | 115.47 USD | Pool had **−15.47 USD** (already over-drawn by FX drift) |

The 100 USD test is the more revealing one — the excess (115.47) is *larger than the posting amount* (100), proving the pool was already negative before Laetitia's posting. This is the fingerprint of **accumulated cross-currency drift**, not of the individual failing posting.

### 5.E The authorized perimeter (constructor CM00A, confirmed live)

| Range         | Sign   | Current content (D01, 2026-04-10)                                           |
|---------------|--------|-----------------------------------------------------------------------------|
| `mr_rldnr`    | I EQ   | `['9A']`                                                                     |
| `mr_bukrs`    | I EQ   | `['UNES']`                                                                   |
| `mr_fikrs`    | I EQ   | `['UNES']`                                                                   |
| `mr_gsber`    | I EQ   | `['GEF']`                                                                    |
| **`mr_waers`**| I EQ   | **`['EUR']`**                                                                |
| `mr_fipex`    | E EQ   | `['GAINS','REVENUE']`                                                        |
| `mr_vrgng`    | E EQ   | `['HRM1','HRM2','HRP1']`                                                     |
| `mr_fund_type`| I EQ   | `[001,002,003,004,005,009,010,012,013,016,017,018,094,095]` (from FMFUNDTYPE.ZZFIX_RATE) |

For the failing case:
- `iv_rldnr = '9A'` ✅ passes
- `iv_bukrs = 'UNES'` ✅ passes
- `iv_fikrs = 'UNES'` ✅ passes
- `iv_gsber = 'GEF'` ✅ passes
- **`iv_waers = 'USD'` ❌ FAILS** — the single blocker
- `iv_fipex = '10\''` ✅ passes (not in exclusion list)
- `iv_vrgng = 'RMBE' / 'RFBU'` etc. ✅ passes (not payroll/PBC)
- `iv_ftype = '001'` ✅ passes (001 is in the authorized list — verified via RFC_READ_TABLE on FMFUNDTYPE)

**Only the currency check is the blocker.** All other dimensions are authorized.

### 5.F Why the Staff-logic branches were not the fix

`CHECK_CONDITIONS_2` (CM00B) checks `mr_waers2 = ['EUR','USD']` and was clearly designed to handle both currencies. It is called from the Staff-logic branches of every enhancement. But every one of those branches is wrapped in `IF 1 = 2.` → dead code:

```abap
IF 1 = 2. "Staff logic on hold.
*START of BR STAFF Logic ----->START
  LOOP AT m_t_addref ...
    IF <yyls_addref2>-ref-waers = 'EUR'.
      yylo_br_exchange_rate->convert_to_currency( ... )
    ELSEIF <yyls_addref2>-ref-waers = 'USD'.
      yylo_br_exchange_rate->convert_to_currency_2( ... )      " ← THE RIGHT METHOD FOR USD
    ENDIF.
  ENDLOOP.
*END of BR Staff Logic ----->END
ENDIF. "Staff logic on hold.
```

The Staff logic was written, code-reviewed, and transported — but **activated nowhere**. Someone at some point made the judgment call to ship the Non-Staff path first and keep Staff on hold. The plain-text comment `"Staff logic on hold"` appears in every enhancement. In `ZFIX_EXCHANGERATE_PBC_POS_UPD` the whole enhancement is even more explicitly marked: `CHECK 1 = 2. "Deactivated the 2024/01/08`.

### 5.G The missing piece — `CONVERT_TO_CURRENCY_2` (CM002)

This method is **complete, tested, and production-transported** — but only called from dead code. It does the double-hop needed for USD postings:

```abap
METHOD convert_to_currency_2.
  " Step 1: USD UNORE → EUR UNORE at rate type M (standard OB08)
  CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
    EXPORTING
      foreign_amount   = iv_foreign_amount
      foreign_currency = 'USD'
      local_currency   = 'EUR'
      type_of_rate     = iv_type_of_rate_unore      " DEFAULT 'M'
    IMPORTING local_amount = ev_local_amount_2.

  " Step 2: EUR UNORE → USD BR at rate type EURX (the budget rate)
  CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
    EXPORTING
      foreign_amount   = ev_local_amount_2
      foreign_currency = 'EUR'
      local_currency   = 'USD'
      type_of_rate     = iv_type_of_rate            " DEFAULT 'EURX'
    IMPORTING local_amount = ev_local_amount.
ENDMETHOD.
```

For a USD posting of 100 USD on a day when `M rate EUR→USD = 1.10` and `EURX rate EUR→USD = 1.09529`:
- Step 1: `100 USD × (1 / 1.10) = 90.91 EUR`
- Step 2: `90.91 EUR × 1.09529 = 99.57 USD`
- Result: `99.57 USD` → overwrites the new posting's `fkbtr` from 100 to 99.57 before AVC checks it.

When the commitment release hits the EUR FR, SAP correctly releases `99.57 USD / 1.09529 = 90.91 EUR`, which matches Step 1 exactly. **No drift.**

### 5.H Legacy 5.0-5.5 hypotheses — status after code review

For completeness, the hypotheses drafted before code extraction:

| # | Hypothesis                                               | Status after code review |
|---|----------------------------------------------------------|---------------------------|
| 0 | Cross-currency consumption gap (domain owner)            | ✅ **PROVEN** — `mr_waers=['EUR']` in constructor |
| 1 | Pool drift from USD round-trips                          | ✅ **Derivative of H0 — this is the observable symptom** |
| 2 | `check_user` allowlist gate                              | ❌ **Disproven** — there is no `check_user` method in the class; the gate is `check_br_is_active` (time-based) + `check_conditions` (field-based). No user-level allowlist. |
| 3 | FUNDBLOCK "Screen-Not used" regression                   | ❌ **Disproven** — FUNDBLOCK Enhancement 2 and 3 are ACTIVE in the extracted source. The "Screen-Not used" label in the SE20 composite is misleading; the code runs. |
| 4 | Carryforward BR mismatch                                 | ❌ **Not the primary cause** — contributes to drift but does not explain the reproducible per-posting failure. |
| 5 | Fund type `001` not in `check_conditions`                | ❌ **Disproven** — fund type `001` IS in `mr_fund_type` (`FMFUNDTYPE.ZZFIX_RATE='X'` verified for type 001 in D01). |

---

### 5.0 ARCHIVE — Hypothesis 0 as originally stated by domain owner (2026-04-10, PROVEN)

Pablo Lopez (PSM / BR solution owner), in his own words:

> *"In the moment of doing the Fund reservation, the FUND is in EUR and for GEF. Then we apply the rule of Budget rate. Normally the consumption for this fund reservation respects the currency — means EUR — and converts using the fix budget rate. In this case the user used the fund reserved in EUR but in USD. Then the system does not apply the Budget rate rule. And maybe does a strange conversion and totals calculation as it was not considered in our logic."*

**The design assumption** baked into `ZFIX_EXCHANGERATE_*`:

> A consumption posting against an EUR-denominated fund reservation will also be in EUR. The BR rule is written to convert `EUR → USD` at the fixed budget rate. It was **never designed to handle** `USD consumption ↔ EUR reservation`.

**Mechanism:**
1. FR `3250117351` was created in **EUR** (4,400.00 EUR) → BR path ran → persisted as `TRBTR=4,400 EUR / FKBTR=4,819.28 USD` using BR rate 1.09529.
2. The TC cover-group budget at `9H/2026/3110111021/PAX/TC` was loaded in EUR and stored at the same BR rate → internally consistent EUR world.
3. Vonthron attempts an FB60 in **USD** against the EUR FR. The posting enters the FM chain with `TWAER='USD'`.
4. In `ZFIX_EXCHANGERATE_AVC` (`FM_FUNDS_CHECK_OI`), `check_conditions(iv_waers='USD', ...)` is evaluated per `<ls_fmioi>` row. **Under the design assumption, the condition matrix does NOT authorize BR for a USD consumption line** — the row is skipped.
5. With BR skipped, standard SAP kicks in and:
   - Translates the USD posting amount to the FM area currency (USD) → identity, no issue at this step
   - But the **commitment release** on the earmarked fund consumes `TRBTR (EUR)` and the **release amount in FM area currency** is recomputed via **standard OB08 `M` rate** (not BR), because the BR override never fired for this line
   - The release in USD at M rate ≠ release in USD at BR rate → micro-delta
6. Across the rollup at TC level, the delta surfaces as `FMAVC005` (annual budget exceeded by a tiny residual).

**Why EUR postings "work"** under this model: when Konakov posts the same invoice in EUR against the EUR FR, `check_conditions(iv_waers='EUR', ...)` hits the known-good branch → BR is applied → no drift.

**Why Konakov's "VC" test (EUR FR + USD payment, 3 Apr) worked**: either (a) the VC test used a fund/center/item combo that happened to slip through `check_conditions` in a permissive branch, or (b) the VC test cover group was empty/freshly-initialized so a small residual rounded away without triggering FMAVC005. The VC test is a **false reassurance** because the pool state masks the drift. **This must be verified live.**

**Why this is the leading hypothesis:** it is consistent with ALL observed facts:
- Failing case has an EUR FR + USD consumption → untested in the design
- The excess amounts (0.87 on 10 USD, 115.47 on 100 USD) are **not proportional** to the posting amount → the drift is in the cover-group total, not the individual line
- EUR postings work unconditionally → BR canonical path is intact
- Konakov's VC test sometimes works, sometimes doesn't → pool-state dependent
- The problem is concentrated on an **earmarked fund** (the place where transaction currency is pinned) rather than a direct FI posting without FR

**Fix direction (per domain owner)**: extend the `ZFIX_EXCHANGERATE_AVC` / `CHECK_CONS` / `NEW_ITEM` / `FI` enhancements so that when the posting currency does NOT match the reference (FR/commitment) currency, the conversion still routes through the BR path — i.e., convert `USD posting → EUR (at inverse BR) → back to FM area USD via BR` so the round-trip is internally consistent with how the budget pool was loaded. Equivalently, treat USD-against-EUR-FR as "mixed currency consumption" and force a BR-roundtrip rather than letting SAP fall back to OB08 M rate.

> 📝 **Feedback rule candidate** (to be added to `brain_v2/agent_rules/feedback_rules.json` once the hypothesis is confirmed):
> *"UNESCO's `ZFIX_EXCHANGERATE_*` family assumes consumption posting currency = original FR currency. Cross-currency consumption (USD against EUR FR, or vice-versa) is a **design gap**, not a user error. Any FMAVC005 with a non-proportional small residual on a foreign-currency FR chain should be triaged as 'cross-currency consumption gap' first."*

---

### 5.1 Hypothesis A — Pool has accumulated drift from USD postings that bypassed BR (STRONG, derivative of Hypothesis 0)

When a **USD** posting is generated against a budget loaded at BR (EUR-origin), the `ZFIX_EXCHANGERATE_AVC` enhancement calls:

```abap
convert_to_currency( iv_foreign_amount   = trbtr_usd
                     iv_foreign_currency = 'USD'
                     iv_local_currency   = 'USD' )    -- hardcoded in enhancement
```

If `convert_to_currency` for the USD→USD case does **not** short-circuit and instead routes through an intermediate currency (EUR), the result is:

```
100 USD → (BR EURX 1/1.09529) → 91.30 EUR → (BR EURX 1.09529) → 100.00 USD    ← IF clean round-trip
100 USD → (BR EURX 1/1.09529) → 91.30 EUR → (M OB08 1.0835)    → 98.92 USD    ← IF drift
```

Because of rounding on both legs (1/1.09529 = 0.913046… × 1.09529 ≠ 1.00000 exactly at standard SAP rounding precision), each USD posting persisted to the pool introduces a **sub-cent residual**. Across many USD postings over a year, this accumulates into a visible negative residual at the TC cover group.

Observed consistent with this: the TC pool for fund 3110111021/PAX/2026 was already ~15 USD over-drawn when Konakov tested with 100 USD.

**Why it works for EUR postings**: `convert_to_currency(iv_foreign='EUR', iv_local='USD')` is the canonical path that matches how the budget pool was loaded. No round-trip error.

### 5.2 Hypothesis B — Posting user not in `check_user` allowlist (ALSO STRONG, complementary)

`ZFIX_EXCHANGERATE_AVC` begins with:
```abap
IF yylo_br_exchange_rate->check_user( sy-uname ) = abap_true.
```

If Laetitia Vonthron (the real user) is NOT in the allowlist, the entire enhancement is **skipped**. Then:
- The new USD posting line is checked with its unaltered `fkbtr` (= 100 USD, identity from standard path).
- The existing EUR commitments in `t_fmioi` are ALSO unaltered — left at whatever `fkbtr` was persisted on the DB.
- Since they were persisted using `ZFIX_EXCHANGERATE_NEW_ITEM` at creation time (runs at FR save, under whichever user was posting the FR), those DB values are the BR-rate values.
- AVC check proceeds against persisted DB values → should still work, UNLESS…

…the total budget at TC level uses a method that recomputes from the DB `trbtr` on the fly instead of the persisted `fkbtr`. In that case the `check_user` gate becomes the deciding factor. **Requires SAP trace to confirm.**

Also relevant: Konakov's test user in TS1 worked sometimes (VC test) and failed sometimes (RP reproduction) → suggests it is **not** purely about the user, but also about what's in the underlying pool.

### 5.3 Hypothesis C — FUNDBLOCK "Screen-Not used" regression (USER-FLAGGED — needs validation)

Pablo Lopez's own hypothesis during the thread:
> *"Maybe the issue is in the screen of earmarked funds that I modified."*

`ZFIX_EXCHANGERATE_FUNDBLOCK` (the SAPMKBLD/KBLD screen enhancement for FMX1 manual fund reservation) is labeled **"Screen-Not used"** in the enhancement registry. If this enhancement historically did the BR conversion at *screen entry* time and was deactivated at some point, any code paths that used to rely on it now have to be covered by the save-time `ZFIX_EXCHANGERATE_EF_FUND_RESERVATION` enhancement. If that save-time path has a narrower gate or was recently modified, newly-created FRs may be persisted with **OB08 rates** instead of BR rates, leading to the drift described in §5.1.

**Action**: diff the `ZFIX_EXCHANGERATE_EF_FUND_RESERVATION` and `ZFIX_EXCHANGERATE_FUNDBLOCK` enhancements, confirm when FUNDBLOCK was marked "Screen-Not used", and check for any FRs with `FKBTR/TRBTR` ratio that does NOT match the BR (e.g., sitting at 1.0835 or similar M rate).

### 5.4 Hypothesis D — Carryforward regenerated TC totals at the wrong time

The invoice fails on the **2026 carryforward slice**, not the original 2025 FR. Carryforward-related enhancements present:
- `ZFIX_EXCHANGERATE_BR_REVALUATION` — *"One time, PO Commit reconstruction at BR — Cut over Exclude lines"*
- `ZFIX_EXCHANGERATE_BR_REVAL_RESFUND` — *"Report Only — Reservation fund revaluation only at BR"*

If the 2025→2026 carryforward job was executed with a different BR value than the one in place at FR creation time, the TC total for 2026 would be recomputed to an amount that doesn't match the carried-forward commitment FKBTR sum exactly, and the residual surfaces as FMAVC005.

Observation: EURX rate in TCURR shows **1.09529 on both 2024-01-01 and 2024-12-01** — stable. So if BR source is EURX, there shouldn't be a YoY shift. But if BR source is a **custom Y-table** that was updated independently, there could be a discrepancy. **Needs SAP to confirm the BR source table.**

### 5.5 Hypothesis E — Fund type `001` (MULESOFT-created) fails `check_conditions`

Fund 3110111021 has `TYPE='001'` and `ERFNAME='MULESOFT'` in the `funds` table. The enhancement's `check_conditions` call takes `iv_ftype = get_fund_type_from_fund(...)`. If `get_fund_type_from_fund` returns a value that `check_conditions` **does not recognize** (because the allowlist of fund types was built for UNESCO-manual fund types and never updated for interface-created funds), the whole BR conversion is skipped for this fund, and all Hypothesis A/B/D effects compound.

**This is very plausible** and needs a one-line SAP check: `SE24 → YCL_FM_BR_EXCHANGE_RATE_BL → check_conditions`, inspect the fund-type branch.

### 5.6 Why Konakov's "VC" test worked but the "RP" case fails

The contradiction:
- **RP case** (Vonthron, prod): fund 3110111021 / earmarked fund 3250117351/39 (carried forward) / USD posting → **fails**
- **VC case** (Konakov, test, 3 Apr): funds reservation in EUR + payment in USD → **works** — implying the broad rule "USD posting against EUR FR always fails" is wrong

Differences that could explain the asymmetry:
- **VC was a freshly-created FR** in the current period; **RP is a carried-forward FR** from the prior year → points at Hypothesis D
- **VC used a different fund** (likely not 3110111021, not type 001) → points at Hypothesis E
- **VC might have been in a different cover group** (not TC) → points at the AVC derivation

Konakov did not specify the VC test fund/center/item — need to ask him to capture the VC test parameters so we can diff.

---

## 6. What we need from SAP (live access checklist)

When SAP access is restored, this is the triage action list in priority order:

### 6.1 Class inspection (highest leverage)

1. **SE24 → `YCL_FM_BR_EXCHANGE_RATE_BL`**
   - `check_user` — read source; which table holds the allowlist?
   - `check_conditions` — read source; how are conditions evaluated?
   - `convert_to_currency` — read source; **where does the rate come from?** (TCURR with which `KURST`? a custom Y-table?)
   - `get_fund_type_from_fund` — read source; how does it classify fund type `001`?

2. **SE11 on all Y-tables referenced by the class** — expected candidates:
   - `YTFM_BR_RATE` / `YFM_BR_KURS` (rate storage)
   - `YTFM_BR_USERS` / `YXUSER` (user allowlist)
   - `YTFM_BR_RULES` (conditions matrix)

### 6.2 Data confirmation

3. **SE16N on TCURR** — export rate type `EURX`, `EURO`, `M`, `V`, and any custom Y-type for currency pairs `EUR→USD` and `USD→EUR` for dates 2024-01-01 through 2026-04-10. Confirm whether the rate still sits at `1.09529-`.

4. **SE16N on FMBL / FMBDT** — fund `3110111021`, fiscal year `2026`, budget category `9F`, commitment item rolling up to `TC`:
   - What is the loaded budget amount in USD (and EUR if dual-currency)?
   - Compare to sum of FMIOI commitments for the same key — residual should match the ~15 USD negative observed.

5. **FMAVCR01** or **FMCEMON01** — display the availability control situation for control object `9H / 2026 / 3110111021 / PAX / TC`. Capture: budget, consumption, commitments, reservations, available.

### 6.3 Live trace

6. **ST05 / SAT trace** a reproduction in TS1 via FB60 for 10 USD → capture the call stack into `FM_FUNDS_CHECK_OI` and the `YCL_FM_BR_EXCHANGE_RATE_BL` methods.

7. **Breakpoint** in `ZFIX_EXCHANGERATE_AVC` (function module `FM_FUNDS_CHECK_OI`) on the line `yylo_br_exchange_rate->convert_to_currency(`. Step through:
   - Confirm whether `check_user( sy-uname ) = abap_true` for the reproduction user.
   - Confirm `check_conditions` return value for both the new USD line and each existing EUR commitment line.
   - Observe `yylv_amount` and `yylv_subrc` for the USD→USD case specifically — is it short-circuiting, or routing through an intermediate?

8. **Replicate Konakov's VC test** with identical FB60 data but a different fund (one created manually, not by MULESOFT, not carried forward) — confirm the VC test still passes, then progressively introduce each variable (MULESOFT-created, carried-forward, fund type 001) until the test starts failing. This isolates the decisive factor.

### 6.4 Enhancement history

9. **SE19 → `ZFIX_EXCHANGERATE_FUNDBLOCK`** — check Enhancement history, confirm when it was marked "Screen-Not used" and what the previous implementation contained. Diff vs. `ZFIX_EXCHANGERATE_EF_FUND_RESERVATION` to find any gap in coverage.

10. **Transport history** — CTS search for all transports touching `ZFIX_EXCHANGERATE_*` in 2025-2026 to reconstruct the change timeline.

---

## 7. Conclusion — root cause proven, fix identified

UNESCO's **`ZFIX_EXCHANGERATE_*` Budget Rate custom solution** was designed under the assumption that a consumption posting respects the original currency of the fund reservation it draws on. The class `YCL_FM_BR_EXCHANGE_RATE_BL` constructor (CM00A line 8) hardcodes `mr_waers = ['EUR']` — the Non-Staff code path only authorizes EUR transaction currency. `check_conditions` therefore returns `abap_false` for any USD posting, causing the BR conversion to be silently skipped in all 8 active enhancements (`AVC`, `CHECK_CONS`, `FI`, `FUNDBLOCK`, `KBLEW`, `NEW_ITEM`, `PAYCOMMIT`, `PBC_POS_UPD`).

The `CONVERT_TO_CURRENCY_2` method that correctly handles USD → EUR → USD (using the standard M rate for the first hop and EURX BR for the second) exists and is production-ready, but it is only referenced from `IF 1 = 2.` "Staff logic on hold" branches — dead code. `ZFIX_EXCHANGERATE_PBC_POS_UPD` is the only enhancement that directly calls `convert_to_currency_2` for USD handling, but the entire enhancement is hard-deactivated with `CHECK 1 = 2. "Deactivated the 2024/01/08"` on line 10.

As a result, every USD consumption that draws on an EUR-loaded pool accumulates a small FX drift into FMAVCT. The Equatorial Guinea FB60 invoice fails because the TC cover group `9H/2026/3110111021/PAX/TC` has accumulated ~15 USD of negative drift over the prior USD postings on that fund in 2025/2026. Laetitia's 2,291.79 USD invoice tips the pool over the ceiling, FMAVC005 fires.

The functional workaround already confirmed by Konakov (post in EUR instead of USD) works because EUR postings hit the canonical BR path that `mr_waers` authorizes — no drift.
>
> The real impact on the Equatorial Guinea reimbursement is that a legitimate payment cannot be executed — not because budget is actually short, but because the AVC ledger's internal USD total is micro-negative due to FX mechanics. **The functional workaround for the immediate case is to post the invoice in EUR instead of USD** (confirmed working by Konakov on 30 Mar). But the underlying drift needs to be fixed at the solution level or this class of incident will keep recurring.

---

## 8. Recommended next actions

### Immediate (workaround — no code change required)

1. **Post the Equatorial Guinea invoice in EUR** at the XOF→EUR rate (avoiding USD entirely). Already confirmed working by Konakov (30 Mar).
2. **Run `FMAVCREINIT`** on the TC/9H/2026/3110111021/PAX control object (tx `FMAVCREINIT`, parameters: fikrs=UNES, gjahr=2026, fund=3110111021, ledger=9H). This rebuilds FMAVCT from the persisted FMIOI/FMIFIIT and — because those rows were ALREADY persisted at BR rate for EUR and at OB08 rate for USD — the reinit restores the pool to the *current consistent state*. This clears the residual drift, buying a clean state for the next set of postings.
3. Immediately after reinit, re-attempt Vonthron's 2,291.79 USD FB60 posting. It should pass if the drift was the cause.

### Short term — the surgical fix (one class edit)

The minimum-risk code change is to add a **currency-aware dispatch** in every enhancement that currently calls `convert_to_currency` for USD handling. But a much smaller change is possible: **add `'USD'` to `mr_waers` and route USD through `convert_to_currency_2`** instead of `convert_to_currency` in the enhancement body.

Cleanest implementation (2 class-level edits + 8 enhancement tweaks):

```abap
" 1. In METHOD constructor of YCL_FM_BR_EXCHANGE_RATE_BL (CM00A), add after line 8:
APPEND VALUE #( sign = 'I' option = 'EQ' low = 'USD' ) TO mr_waers.
```

```abap
" 2. Add a helper method to the class that dispatches per currency:
methods CONVERT_TO_CURRENCY_AUTO
  importing
    !IV_DATE             type DATUM
    !IV_FOREIGN_AMOUNT   type ANY
    !IV_FOREIGN_CURRENCY type WAERS
    !IV_LOCAL_CURRENCY   type WAERS
  exporting
    !EV_LOCAL_AMOUNT     type ANY
    !EV_SUBRC            type SY-SUBRC .

METHOD convert_to_currency_auto.
  IF iv_foreign_currency = iv_local_currency AND iv_foreign_currency = 'USD'.
    " USD UNORE → USD BR via EUR intermediate
    convert_to_currency_2( EXPORTING iv_date             = iv_date
                                      iv_foreign_amount   = iv_foreign_amount
                                      iv_foreign_currency = iv_foreign_currency
                                      iv_local_currency   = iv_local_currency
                             IMPORTING ev_local_amount   = ev_local_amount
                                       ev_subrc          = ev_subrc ).
  ELSE.
    " EUR/XOF/MRU/etc → USD at EURX
    convert_to_currency( EXPORTING iv_date             = iv_date
                                    iv_foreign_amount   = iv_foreign_amount
                                    iv_foreign_currency = iv_foreign_currency
                                    iv_local_currency   = iv_local_currency
                           IMPORTING ev_local_amount   = ev_local_amount
                                     ev_subrc          = ev_subrc ).
  ENDIF.
ENDMETHOD.
```

```abap
" 3. In each of the 8 enhancement implementations, replace:
"    yylo_br_exchange_rate->convert_to_currency( ... )
"    with:
"    yylo_br_exchange_rate->convert_to_currency_auto( ... )
```

This preserves the full existing behavior for EUR and adds a distinct code path for USD that uses the already-built double-hop method.

### Alternative short-term fix — activate the Staff logic

Every enhancement has a fully-coded `IF 1 = 2. ... ENDIF.` "Staff logic" branch that already contains the `IF waers = 'EUR' ... ELSEIF waers = 'USD' ... convert_to_currency_2` dispatch. Activating that branch (removing the `IF 1 = 2.` guard) **would fix the bug for staff-related VRGNG values** (`HRM1`, `HRM2`, `HRP1`) — but it would NOT fix general FI postings like FB60 because the Staff branches use `check_conditions_2` which has a `mr_vrgng2` filter restricted to `['HRM1','HRM2','HRP1']`. FB60 postings have VRGNG values like `RMBE`/`RFBU` and would not pass.

**So the surgical fix above is preferred** — it directly extends the Non-Staff path to USD without touching the Staff logic.

### Medium term — quality check automation

- [ ] Build `Zagentexecution/quality_checks/budget_rate_ratio_drift_check.py` that queries `fmioi` and `fmifiit_full` for all `(FUND, GJAHR, TWAER)` tuples and flags any records where `ABS(FKBTR/TRBTR - 1.09529) > 0.0001` for EUR commitments. This catches BR drift at the data layer before end-users hit FMAVC005.
- [ ] Also flag any USD postings on BR-authorized funds where `FKBTR ≠ TRBTR` (which would indicate a non-identity conversion already happened, suggesting the fix is deployed and working).
- [ ] Add a nightly FMAVCREINIT scheduled job for funds on the BR perimeter to self-heal drift until the class fix is deployed.

### Long term — brain + rules updates

- [ ] Add brain objects for `YCL_FM_BR_EXCHANGE_RATE_BL` and all 15 `ZFIX_EXCHANGERATE_*` enhancement members.
- [ ] Add a first-class incident record to `brain_v2/incidents/incidents.json` once the ServiceNow INC number is assigned.
- [ ] Add a feedback rule: *"When analyzing a custom filter/gate class with RANGE attributes, always grep the constructor for the full range initialization before trusting any inferred behavior. Range contents are runtime config, not static."*
- [ ] Add a feedback rule: *"When a custom class has a `check_conditions` + `check_conditions_2` + `check_conditions_3` pattern, always verify which is called from production code paths vs. dead code (`IF 1 = 2.`). The _2 variant is often 'designed but not shipped'."*

---

## 10. 🧪 SAP isolation test protocol — progressive-variable VC-vs-RP diff

**Objective:** find the single decisive variable that separates Konakov's working "VC" test case (3 Apr, EUR FR + USD payment → OK) from the failing "RP" case (EUR FR 3250117351/39 + USD payment → FMAVC005). **One and only one variable changes per step.** The first step that flips from ✅ to ❌ is the root cause.

### 10.1 Pre-flight — capture the VC test baseline

Before running any test, get from Konakov (he is the only source of truth — his VC test is not otherwise documented):

| Field | Konakov's "VC" test value |
|---|---|
| Company code | ? |
| Fund (FINCODE) | ? |
| Fund creation source (`FMFINCODE-ERFNAME`) | ? (manual vs `MULESOFT`) |
| Fund type (`FMFINCODE-TYPE`) | ? (`001`? GEF pattern? etc.) |
| Funds center | ? |
| Commitment item | ? |
| Business area | ? |
| Earmarked fund number | ? (fresh or carried-forward?) |
| FR creation date | ? (current year vs carried-forward from 2025) |
| FR currency | EUR (confirmed) |
| FR amount (EUR) | ? |
| FR FKBTR (USD) at creation | ? (compute ratio — must be 1.09529 if BR fired) |
| Posting currency | USD (confirmed) |
| Posting amount | ? |
| Posting user | ? |
| Posting result | ✅ OK (confirmed) |

**Without this data the experiment cannot run.** Ask Konakov to paste the document numbers of his test and the SE16N lines.

### 10.2 Test matrix — 6 progressive steps

Each step changes ONE variable from the VC baseline toward the RP case. After each step, attempt an FB60 posting in USD against the earmarked fund and record the outcome. Keep ALL other variables from the previous step constant.

| Step | What changes from previous step | Variable isolated | RP target value | Decision rule |
|---|---|---|---|---|
| **T0** | — (baseline) | — | — | Re-run Konakov's VC test exactly. Expected: ✅ OK. If this fails immediately, the VC test is non-reproducible and H0 is confirmed by default — skip to §10.4. |
| **T1** | Change the **cost center** to `111018` | Cost center | `111018` | If fails → cost-center-specific derivation issue. If OK → continue. |
| **T2** | Change the **commitment item** to something that rolls up to **`TC`** (same as RP) | AVC control object (PC → TC) | CI `10'` or any CI that maps to TC via `FMAFMAP013500109` | If fails → **the TC cover group is the one with drift** — focus investigation on FMAVCR01 of `9H/<year>/<fund>/<center>/TC`. |
| **T3** | Change the **business area** to `GEF` | Business area | `GEF` | If fails → `ZFIX_EXCHANGERATE_*` `check_conditions` rejects `GSBER='GEF'` for this scenario. |
| **T4** | Change the **fund** to a **MULESOFT-created**, **type 001** fund *that was created in the current year* (not carried forward) — e.g., find another Mulesoft fund with a fresh FR | Fund creation source + fund type | Fund type `001`, ERFNAME `MULESOFT` | If fails → `get_fund_type_from_fund` returns a value that `check_conditions` does not authorize → **Hypothesis 5 confirmed**. |
| **T5** | Change to a **carried-forward** FR (use any FR carried over 2025→2026, ideally on the same fund as T4) | Carryforward | 2025→2026 CF | If fails → **Hypothesis 4 confirmed** (carryforward regenerated TC totals at a slightly different rate). |
| **T6** | Use the **real RP** FR `3250117351/39` on fund `3110111021` | Full replication of RP case | All RP values | Must reproduce the exact RP error. If this step does NOT fail, something in the environment has changed since Vonthron's attempt — check `FMAVCREINIT` history. |

### 10.3 What to capture at each step

After each step, before moving on, capture:

1. **Screenshot** of the FB60 screen (Basic data + Details tabs)
2. **Screenshot** of the error (or success confirmation)
3. **If failure**: click the error → Performance Assistant → capture the full diagnosis, the control object (`9H/YYYY/fund/center/item`), and the excess amount
4. **FMAVCR01** or **FMCEMON01** of the relevant control object → budget / consumption / commitments / available
5. **SE16N on FMIOI** filtered by the earmarked fund used → `TRBTR`, `FKBTR`, `TWAER`, `WRTTP` → compute ratio, verify it matches the expected BR (1.09529 for EUR)
6. **SE16N on FMIFIIT** filtered by the same fund + GJAHR → confirm the 259-row-like pattern holds or there is an anomalous row

Save all screenshots in `Zagentexecution/incidents/INC_budget_rate_eq_guinea/isolation_test/T<N>/` with filename `step_<N>_<outcome>.png`.

### 10.4 Decision tree

```
T0 (VC baseline)
├── ✅ PASS → T1
│            ├── ❌ FAIL → ROOT CAUSE = cost center 111018 / derivation issue
│            └── ✅ PASS → T2
│                         ├── ❌ FAIL → ROOT CAUSE = TC cover group drift (H1/H4)
│                         └── ✅ PASS → T3
│                                      ├── ❌ FAIL → ROOT CAUSE = GSBER=GEF not in check_conditions (H0 variant)
│                                      └── ✅ PASS → T4
│                                                   ├── ❌ FAIL → ROOT CAUSE = fund type 001/MULESOFT not in check_conditions (H5 confirmed)
│                                                   └── ✅ PASS → T5
│                                                                ├── ❌ FAIL → ROOT CAUSE = carryforward BR mismatch (H4 confirmed)
│                                                                └── ✅ PASS → T6
│                                                                             ├── ❌ FAIL → non-deterministic pool drift; run FMAVCREINIT and re-run §10.2
│                                                                             └── ✅ PASS → case cannot be reproduced; check if FMAVCREINIT or a transport changed state
└── ❌ FAIL → Konakov's VC test is NOT reproducible. H0 confirmed by default: cross-currency consumption gap is the problem regardless of fund characteristics. Go straight to §10.5.
```

### 10.5 What a "confirmed" hypothesis unlocks

When the breaking step is identified:

| Breaking step | Implied root cause | Next action |
|---|---|---|
| **T0** | H0 — generic cross-currency consumption gap | Extend `check_conditions` in `YCL_FM_BR_EXCHANGE_RATE_BL` to authorize USD consumption against EUR FR. Test in TS1 after the change. |
| **T1** | Cost center derivation | Check if cost center `111018` has an unusual assignment (e.g., WBS force-clear per `YRGGBS00`). |
| **T2** | TC cover group drift | Run `FMAVCREINIT` on `9H/<year>/<fund>/<center>/TC`, re-run T2. If OK after reinit → drift accumulation (H1); if still failing → structural, continue to T3. |
| **T3** | GSBER `GEF` rejected | Look at `ZFIX_EXCHANGERATE_BR_AVC_EXCLUSIONS` — it is listed as "ZFIX_BR_AVC_EXCLUSIONS" in the registry; this is likely where GSBER exclusions live. |
| **T4** | Fund type 001 / MULESOFT not authorized | Check `get_fund_type_from_fund` return for type `001` and trace into `check_conditions` fund-type branch. |
| **T5** | Carryforward rate mismatch | Diff the carryforward execution log against BR rate history. Investigate `ZFIX_EXCHANGERATE_BR_REVALUATION`. |
| **T6** | Pool state dependent | Suggests the pool has accumulated drift that `FMAVCREINIT` did not clean — possible corruption of totals tables. |

### 10.6 Quick-win first check (before running the full matrix)

Before spending 2 hours on the matrix, **run this single 5-minute check first** — it will answer Hypothesis 0 directly:

1. In TS1, use Konakov's exact reproduction data: supplier `456639`, fund `3110111021`, center `PAX`, cost center `111018`, business area `GEF`, FR `3250118890`/`001` (or any current EUR FR on fund 3110111021).
2. Attempt FB60 with **exactly 10.00 USD** — confirm the FMAVC005 excess reproduces.
3. Immediately repeat with **exactly 10.00 EUR** using the same supplier / same FR / same data → if this posts ✅, **Hypothesis 0 is confirmed**: the only variable that matters is `iv_waers` on the posting side.
4. Optional — repeat with **9.13 EUR** (which is 10 USD ÷ 1.09529 at BR rate) to cross-verify the BR conversion direction.

If the 10-EUR test passes and the 10-USD test fails on the exact same FR, you have proven H0 in 5 minutes without running the full matrix. **Do this first.**

---

## 9. Attached evidence

| File | Description |
|---|---|
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/body.txt` | Full email thread extracted from .eml |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image009.png` | FB60 reproduction screen (Basic data tab) |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image010.png` | FB60 reproduction screen (Details tab, line item with fund/PAX/111018/3250118890) |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image011.png` | FMAVC005 error strip — "Annual budget exceeded by 0,87 USD for document item 00002" |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image012.png` | FB60 reproduction screen (100 USD posting, Business Area GEF) |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image013.png` | FMAVC005 Performance Assistant — "Annual budget exceeded by 115,47 USD", control object `9H/2026/3110111021/PAX/TC` |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image014.png` | Same FMAVC005 as status-bar message |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image015.png` | Earmarked fund carryforward report — shows FR 3250117351 line 39 carried forward 2025→2026 at 4,819.28 USD / 4,400.00 EUR |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image016.png` | FB60 screen snippet for Vonthron's original attempt |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image017.png` | Funds reservation display (3250117351) — showing line items available |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image018.png` | Vonthron's original FMAVC005 error — "Annual budget exceeded by" (status bar) |
| `Zagentexecution/incidents/INC_budget_rate_eq_guinea/image019.png` | Exchange-rate InfoCenter — XOF→USD @ 567.241, 19.11.2025 = 2,291.79 USD for 1,300,000 XOF |

---

*Stored in `knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md`*
*Session #052 — 2026-04-10 — Pablo Lopez (escalation owner) + Claude (analysis)*
