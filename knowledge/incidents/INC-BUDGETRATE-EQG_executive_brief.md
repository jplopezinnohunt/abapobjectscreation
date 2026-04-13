# INC-BUDGETRATE-EQG — Executive Brief & Inventory of At-Risk FR Lines

**Status**: ROOT CAUSE CONFIRMED  ·  **Escalation owner**: Pablo Lopez  ·  **Date**: 2026-04-13

## 1. The bug in one sentence

The **Fund Reservation is valued at Budget Rate** (1.09529 EUR→USD via TCURR `EURX`), but the **Consumption posting is allowed in any currency** and is valued at OB08 `M` rate (or identity for USD). **No control prevents cross-currency consumption against an EUR BR-reserved fund.** The two ledgers diverge silently fund-by-fund until the AVC pool hits zero headroom — at which point any subsequent posting fires `FMAVC005 Annual budget exceeded by X.XX USD`.

## 2. How the bug manifests (Vonthron's case, P01 fund 3110111021 / PAX / TC, 2026)

- 6 EUR FR lines carried forward 2025→2026 (RFPOS 38, 39, 40, 41, 43, 45)
- AVC budget loaded at BR: **$12,897.80**
- Open FR commitments at BR: **$12,897.80**
- **AVC available: $0.00** — every dollar already reserved
- Vonthron attempts FB60 in USD against RFPOS 39 (the EqG ticket) → AVC engine sees zero headroom + ~0.87 USD residual from accumulated drift → FMAVC005 fires

## 3. Population at risk

Across P01 + ledger 9H + 2026, the BR-applicable cohort is:

- **64 open EUR Fund Reservation LINES** (TWAER=EUR + GSBER=GEF + authorized fund-type), spread across **26 distinct funds**
- **35 of those 64 lines** sit on (FONDS, FIPEX) cover groups that already have non-EUR consumption draining the AVC pool
- **~10 lines have AVC available ≤ $0** today — Vonthron-class latent failures (any USD posting will fire FMAVC005). Beyond fund 3110111021: 3110111061, 3230311031, 3230411011, 3230311021

Detailed inventory (all 64 lines with origRes, open, line consumption, fund pool consumption, currency breakdown, AVC budget, AVC available):
- **Excel**: [`Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx`](Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx)
- Markdown: [`Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL_table.md`](Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL_table.md)

## 4. Why it stayed hidden

- **Camp A enhancements** (CHECK_CONS, EF_FUND_RESERVATION, FUNDBLOCK) gate on the FR's own currency → fire correctly → FR-tracking ledger stays internally consistent (ratio 1.09529 across all FR lines)
- **Camp B enhancements** (NEW_ITEM, AVC, KBLEW, FI, PAYCOMMIT) gate on the per-row posting currency → silently skip when posting is non-EUR → identity persistence into FMIOI/FMIFIIT
- The two views diverge invisibly. FR reports show all clean. AVC pool drifts. Failure surface is binary: either the cover group has headroom (works fine) or it doesn't (FMAVC005)

## 5. Recommended fix (preventive validation)

Add a hard validation in `CL_FM_EF_POSITION->CHECK_CONSUMPTION` that blocks any consumption posting where:
- FR header currency = EUR **and** business area = GEF **and** fund-type ∈ authorized BR set
- AND consumption posting currency ≠ EUR

**Effect**: user receives a clear error and must convert the amount to EUR before posting (matches Konakov's already-validated workaround). No new drift can ever enter the AVC pool. Backward-fixing of the 26 funds with accumulated drift is then a one-time `FMAVCREINIT` exercise.

Alternative paths (corrective via `convert_to_currency_2` activation, or cleanup via FMN4N extension) carry more code risk and don't fully prevent recurrence.

## 6. Immediate workaround for Vonthron's specific case

**Post the EqG invoice in EUR** at the XOF→EUR rate. Already validated by Konakov on 2026-03-30 ("By the way, when I try to post the invoice in EUR instead of USD it works fine").

## 7. Related findings — landscape inconsistency to clean up

`ZFIX_BR_AVC_EXCLUSIONS` (BAdI implementing `FMAVC_ENTRY_FILTER`) was JP_LOPEZ's tcode-blacklist attempt at the same problem in May 2025. **Created 2025-05-14, deactivated 2025-05-15, never transported beyond V01.** Live in D01+V01 only; absent from TS1, TS3, P01. Tracked as PMO H38 (delete or repurpose).

## 8. Related artifacts

- Full incident analysis: [`knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md`](knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md)
- Solution autopsy (15-member enhancement breakdown): [`knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md`](knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md)
- Quality-check scripts (re-runnable):
  - [`Zagentexecution/quality_checks/br_line_level_inconsistency_check.py`](Zagentexecution/quality_checks/br_line_level_inconsistency_check.py)
  - [`Zagentexecution/quality_checks/budget_rate_consumption_audit.py`](Zagentexecution/quality_checks/budget_rate_consumption_audit.py)
