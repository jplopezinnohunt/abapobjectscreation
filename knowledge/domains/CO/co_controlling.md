---
name: CO — Controlling
description: One controlling area, 688 cost centres, 2.63M CO line items — but only 3 of 9 company codes assigned. The real question is the FM x CO overlap: in a public-sector install, how much of cost accounting is genuine CO and how much is a shadow of Funds Management?
type: project
module: CO-OM
capability_domain: CO
status: PRODUCTIVE
claims: [279, 293]
---

# CO — Controlling

**Technical component:** `CO-OM` · **Capability row:** `capability_model.domains.CO`

## What is measured

| Signal | Measurement |
|---|---|
| Controlling areas (`TKA01`) | 1 |
| Company-code assignments (`TKA02`) | 3 |
| Cost centres (`CSKS`) | 688 |
| CO line items (`COEP`) | **2,634,984** |
| CO totals (`COSP`) 2025 | 92,640 |

Note the asymmetry: **one controlling area covering 3 assigned company codes, out of 9.** Either the
remaining six sit outside controlling, or the assignment is incomplete. That alone deserves a look.

## The question that matters: FM × CO overlap

UNESCO runs **Funds Management** as its primary financial control — 67,500 funds, 787 fund centres,
availability control active, 2.19M commitments. FM already answers *"was this spend authorised
against a budget?"*

CO answers a different question: *"what did this activity cost?"* In public-sector installations the
two overlap heavily, and the overlap is exactly where duplicated effort, contradictory reporting and
reconciliation work accumulate:

- Do cost centres mirror fund centres, or are they an independent hierarchy?
- Are CO postings a *by-product* of FM-derived account assignment, or entered on their own terms?
- Which of the two does management reporting actually consume?

2.63M CO line items is not a residue — something is genuinely posting here. Establishing whether
that is deliberate cost accounting or an automatic shadow of FM is the first real piece of work in
this domain.

## Open questions

1. The FM × CO overlap above — the priority.
2. Why only 3 of 9 company codes are assigned to the controlling area.
3. Internal orders (`AUFK`): used, and for what? Projects already live in PS.
4. Is any allocation/assessment cycle running, or is CO purely a posting collector? Indirect-cost
   allocation demonstrably happens (`YFM_OUTPUT_INDIRECT_COSTS_DH`) — **but in FM, not CO**, which
   is itself a piece of the answer.

## Relations

- **Capability:** `CO` (D_DATA HAVE · U_USAGE PARTIAL · rest NONE)
- **Module axis:** CO · **Process axis:** B2R
- **Adjacent:** [[PSM]] (the overlap) · [[FI]] · [[PS]] (project costing) ·
  [[PBC]] (staff cost is the largest line)
- **Claims:** #279, #293
