---
name: SD — Sales & Distribution (billing-only)
description: 2,116 sales orders and 2,901 billing documents in 2024+ with ZERO deliveries. Order-to-invoice without logistics execution — the shape is the finding. Who is billed, and for what, is the open question, and it has budget consequences.
type: project
module: SD-SLS
capability_domain: SD
status: PRODUCTIVE
claims: [356]
---

# SD — Sales & Distribution (billing-only)

**Technical component:** `SD-SLS` · **Capability row:** `capability_model.domains.SD`

## The shape is the finding

| Signal | Measurement |
|---|---|
| Sales organisations (`TVKO`) | 1 |
| Sales orders (`VBAK`) 2024+ | 2,116 |
| Billing documents (`VBRK`) 2024+ | 2,901 |
| **Deliveries (`LIKP`) 2024+** | **0** |
| Customer master (`KNA1`) | 12,517 |
| Customer sales-area data (`KNVV`) | 3,204 |

**Zero deliveries against 2,901 billing documents.** This is not a broken process — it is a
deliberate configuration: *order → invoice*, no logistics execution. UNESCO is not shipping goods;
it is billing for something.

Note also that billing documents **outnumber** sales orders (2,901 vs 2,116) — either multiple
invoices per order, or billing documents created with no preceding order.

## Why it was wrongly called "not implemented"

The first scope answer stated SD was not implemented, reasoning from the absence of an SD bucket in
the execution map. `KNVV` was visible and should have been the tell: customers carry sales-area
assignments only when a sales organisation exists.

## The open question, and why it matters

**Who is billed, and for what?** Candidates, none verified:

- cost recovery between UNESCO entities and institutes
- billing external parties for services (publications, conference facilities, expertise)
- donor/partner invoicing sitting outside the Funds Management grant flow

This is not academic. Receivables that flow through SD rather than through FM are **revenue the
budget model may not see**. Anyone reviewing the finance process needs to know which of the three
this is.

## Open questions

1. Who are the 12,517 customers, and which 3,204 carry sales-area data?
2. What is billed — resolve item categories and material/service types on `VBRP`.
3. Where does the revenue post: which GL accounts, which funds, which company codes?
4. Is any of this the **Cost Recovery (CRP)** flow, which has its own domain and a Salesforce
   counterpart? If so the two models must be reconciled.

## Relations

- **Capability:** `SD` (D_DATA HAVE · A_PROCESS/U_USAGE PARTIAL · rest NONE)
- **Module axis:** SD · **Process axis:** O2C
- **Adjacent:** [[FI]] (accounts receivable) · [[PSM]] (does this revenue reach FM?) ·
  [[BusinessPartner]] (customer master) · Cost_Recovery_CRP
- **Claim:** #356 (TIER_1, measured)
