# Session #026 Retro — Critical Review: Process Mining Corrections + 6 Discoveries

**Date:** 2026-03-27
**Duration:** ~3h
**Type:** Critical Review + Knowledge Correction
**Session focus:** Full critical review across 3 lenses (process mining, real data vs docs, SAP AP/BCM specialist). Apply all fixes. Add Discoveries tab to companion.

---

## What Was Accomplished

| Area | Achievement |
|------|------------|
| **C3 fixed** | DMEE table row "Read from SGTXT" → `REGUP-LZBKZ`. SGTXT parsing prohibited (NEVER rule). |
| **S1 fixed** | IBE/MGIE/ICBA Tier 3 updated: F-53 (OP) docs confirmed in BSAK. "Outside SAP" = bank instruction only. |
| **S2 fixed** | Empty CUR_STS (15K batches) relabeled: Pre-TMS 2014–2021. Zero empty-status batches after 2021. |
| **S4 fixed** | Methods A/Q/R/W added to payment methods table. |
| **S5 fixed** | "9 company codes" → "9 operational + STEM (broken)" throughout. |
| **C1 fixed** | On-time 1.1% flagged as measurement artifact. Root cause: 73% ZTERM=0001 (ZFBDT=BUDAT). Real on-time for actual-terms = 4.6%. 43% are 100+ days late. |
| **C4 fixed** | PPC section: ⚠ UNVERIFIED PATH warning added. XML PurpCd value unknown, AE/BH not in P01. |
| **sap_payment_e2e** | Companion ref updated v4→v7. Known Gaps expanded with 3 new findings. |
| **Companion v7** | Discoveries tab added (14th tab). 6 discoveries with data tables. KPI bar updated. |
| **PMO** | 3 new HIGH items: H16 (229 payroll failures), H17 (rebuild event log), H18 (read BAdI source). |

---

## Key Intelligence Captured

| Finding | Significance |
|---------|-------------|
| UNES: OP (267K) > ZP (138K) clearing docs | F-53 payments exceed F110. Event log misses ~48% of actual payments. |
| 73% ZTERM=0001 → ZFBDT=BUDAT | "1.1% on-time" is artifact. Real finding: 43% of actual-terms invoices 100+ days late. |
| 229 PAYROLL IBC17 failures | Staff not paid on time. $1.2M avg failed batch. |
| IBE/MGIE/ICBA post OP docs | 9,637+3,376+2,044 cleared items confirmed. Accounting IS in SAP. |
| Pre-TMS legacy batches (2014–2021) | All 15K empty-CUR_STS are historical. Zero post-2021. |
| PPC XML value unknown | Configuration confirmed, output path unconfirmed. Needs BAdI source. |

---

## PMO Reconciliation
- +3 HIGH items: H16 (payroll failures), H17 (event log rebuild), H18 (BAdI source)
- **Total: 9 Blocking | 14 High | 40 Backlog = 63 items**

---

## Pending → Next Session
1. Fix companion Discovery #1 framing (OP = field office GLs, not BCM bypass)
2. Validate REGUH→BSAK link with live join
3. Add F_DERAKHSHAN finding to PMO and companion
4. H16: Investigate 229 PAYROLL IBC17 failures (VPN required)
5. H18: Read BAdI source (D01 password needed)
