---
name: Fund Management (PSM-FM / Public Sector) — the complete budget-execution process (our differentiator)
description: The COMPLETE public-sector Fund Management / Budget Control System (BCS) process — budget → commitment → actual → AVC → carry-forward — which mainstream process mining (Celonis/Signavio, the academic P2P/O2C work) does NOT cover. Public-sector budget execution is under-served; FM is UNESCO's largest domain. Designed s079 from our FM analysis + Gold DB. This is a process we can OWN.
type: project
---

# Fund Management (Public Sector) — the complete budget-execution process

User (s079): "el proceso completo de Fund Management para public sector — no lo veo. Deberíamos
buscar más." Correct: mainstream process mining covers PRIVATE-sector flows (P2P, O2C, AP/AR). The
PUBLIC-sector budget-execution / Fund Management process is NOT in the standard connectors, content,
or academic OCEL examples. It is under-served — and it is UNESCO's LARGEST domain (FMRESERV 6.4M change
events, the FM-AVC model gap, 2,005 buckets at risk). A public-sector FM process intelligence is a
genuinely differentiated capability we can own.

## The complete FM / BCS lifecycle (the process mainstream tools miss)
| Phase | Activity | SAP tcodes | Tables (Gold DB) |
|-------|----------|-----------|------------------|
| **1. Budget formulation & entry** | enter / supplement / transfer / return budget | FMBB, FR58, FMEDDW | **FMBH** (header) → **FMBL** (lines) → **FMBDT** (totals) |
| **2. Budget release** | release budget (if release procedure) | FMEP, FM9* | FMBH/FMBL (release status) |
| **3. Pre-commitment / earmarked funds** | reservation / pre-commitment / commitment / block | FMX1/FMX2 (reserv.), FMY1 (precommit), FMZ1 (commit) | **FMRESERV** (6.4M change events!), the earmarked-funds docs |
| **4. Commitment** | PR/PO consumes budget | ME51N/ME21N → FM update | **FMIOI** (commitment line items) |
| **5. Actual / expenditure** | GR/IR/invoice/payment | MIRO/F-43/F110 → FM update | **FMIFIIT** (actual FI-FM lines; WRTTP filter) ← FI bridge KNBELNR→BKPF.BELNR |
| **6. Availability Control (AVC)** | budget-availability check at each posting | (automatic) | **FMAVCT** (AVC ledger) ← rebuilt from **FMIT** (totals) via FMAF |
| **7. Period/Year-end** | commitment & budget carry-forward; closing | FMCF, FMJ2/FMJ3, F.05 | FMIFIIT (carry-forward value types), the closing domain |
| **8. Reporting / monitoring** | budget vs commitment vs actual vs available | FMRP_RW_BUDCON, FMAVCR | FMIT / FMAVCT |

## The object types (OCEL) for public-sector FM
Account-assignment DIMENSIONS (hierarchical, the "case notions"): **Fund** (FMFCT), **Funds Center**
(FMFCTR), **Commitment Item** (FMCI/FMFPO), **Funded Program** (FMFG), **Grant**. Plus the documents:
**FM document** (FMBELNR), **commitment line**, **actual line**, **earmarked-funds document**, **budget
document** (DOCNR). The AVC **control object** = the (Fund, FundsCenter, CommitmentItem-rolled, FundedProgram)
tuple — the unit budget availability is checked against (this is where the model gap lives).

## How to MINE it from our Gold DB (mostly local, now)
- **FMRESERV (6.4M change events)** = the reservation/budget object lifecycle (created→changed→...→consumed).
  Case = the FM object; activity = the change/status; the biggest single FM event source — UNBLOCKED.
- **FMBH→FMBL→FMBDT** = the budget-entry process (header/item/totals).
- **FMIOI (commitments) → FMIFIIT (actuals) → FMIT (totals) → FMAVCT (AVC)** = the consumption chain;
  the FI-FM bridge (FMIFIIT.KNBELNR = BKPF.BELNR) links it to the FI document process.
- **The cross-process OCEL**: one budget object flows Budget → Reservation → Commitment → Actual → AVC,
  touching Fund + FundsCenter + CommitmentItem + the FM document — a textbook OBJECT-CENTRIC process
  (multiple object types per event), which is exactly why OCEL fits public-sector FM.

## Why this is OUR differentiation (the gap = the opportunity)
1. Mainstream process mining (Celonis/Signavio, the van der Aalst OCEL examples) = P2P/O2C/AP/AR —
   PRIVATE sector. Public-sector budget execution / FM is NOT covered by standard content.
2. It is UNESCO's largest domain and our deepest analysis (FM-AVC model gap, FMRESERV, the AVC derivation).
3. Public-sector orgs (UN agencies, governments, NGOs) ALL run PSM-FM and have the SAME unmet need:
   "how does our budget execution ACTUALLY run, where does AVC block/leak, where is the commitment-to-
   actual gap?" — a process no commercial tool ships content for.
4. Combined with our moats (the brain / process↔code / custom-over-standard / deterministic), this is a
   defensible vertical: **public-sector budget-execution process intelligence.**

## Specific public-sector analyses (that P2P/O2C mining can't give)
- **Commitment-to-actual realization** (how much committed budget becomes actual, cycle time, leakage).
- **AVC block/override behavior** (where availability control blocks postings, who overrides, the model-gap exposure).
- **Budget transfer/supplement patterns** (the in-year re-budgeting process — a public-sector signature).
- **Carry-forward** (open commitments rolling year-to-year — the FMCF process).
- **Fund/grant lifecycle** (sponsored programs, donor funds — the YBANK/SETLEAF structures we have).

## Search more (the user's ask) — research angles to confirm/extend
Targeted research to add: (a) is there ANY academic/commercial public-sector FM / budget-execution
process mining (likely sparse → confirms the gap)? (b) SAP PSM-FM standard process / reference model
(for the custom-over-standard overlay applied to FM); (c) public-sector / government process mining
case studies. Fold into the running research or a dedicated FM/public-sector pass — mine exhaustively.

## Next
Mine FMRESERV now (local, 6.4M events) to discover the FM object lifecycle — the first public-sector
FM process from real data. Then the budget→commitment→actual→AVC OCEL across the FM tables.
