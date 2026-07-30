---
name: TRM — Treasury & Risk Management (deal management)
description: 1,835 financial deals in the Transaction Manager. Distinct from the Electronic Bank Statement flow — the two were being conflated under the single word "Treasury". Instruments, counterparties and hedging policy are all unknown.
type: project
module: FIN-FSCM-TRM-TM
capability_domain: TRM
status: PRODUCTIVE
claims: [356]
---

# TRM — Treasury & Risk Management

**Technical component:** `FIN-FSCM-TRM-TM` (Transaction Manager; classic name `TR-TM`)
**Capability row:** `capability_model.domains.TRM`

## Distinct from Treasury_EBS — this is the correction

"Treasury" in this brain has meant **bank statement processing** (`FI-BL-PT-BS-EL`, MT940 import,
211 house banks, daily reconciliation). That is cash *operations*.

`VTBFHA` holds **1,835 financial transactions** — deal management: instruments, counterparties,
positions. That is treasury *front office*: a different discipline, with different risk, different
authorisations and different accounting.

Conflating the two under one word hid an entire capability. They are now separate domains:
`Treasury_EBS` and `TRM`.

## What is measured

| Signal | Measurement |
|---|---|
| Financial transactions (`VTBFHA`) | **1,835** |
| Enterprise extension `EA-FS` (Financial Services) | **ON** |
| House banks / accounts | 211 / 402 — *that is `Treasury_EBS`, shown for contrast* |

## Open questions — all of them; this domain is barely opened

1. **Which instruments?** Money market, foreign exchange, securities, derivatives? Product types on
   `VTBFHA` will say. For a multi-currency UN agency, FX hedging is the likely core.
2. **Which counterparties**, and is limit management (`FIN-FSCM-TRM-CR`) configured?
3. **Valuation and position management** — is the analyzer (`FIN-FSCM-TRM-AN`) in use, or are deals
   recorded without market valuation?
4. **Who transacts?** Authorisation and four-eyes on deals is a classic audit finding. We have
   measured nothing here.
5. **The FX link.** An `fx_revaluation_f05` companion already exists, and exchange rates are
   broadcast from P01 by IDoc with an unknown upstream source. TRM may be that source — worth
   closing, since it is an open question in the integration map (Q1).

## Relations

- **Capability:** `TRM` (D_DATA HAVE · U_USAGE PARTIAL · rest NONE)
- **Parent domain:** `Treasury_EBS` (sibling, not container) · **Module axis:** FI ·
  **Process axis:** T2R
- **Adjacent:** [[Treasury]] (bank statements, cash ops) · [[Payment]] (settlement) ·
  [[FI]] (posting, FX revaluation)
- **Claim:** #356 (TIER_1, measured)
