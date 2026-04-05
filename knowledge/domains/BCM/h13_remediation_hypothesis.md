# H13 — BCM Dual-Control Gap Remediation

**Type:** Hypothesis-grounded action plan
**Author:** Session #036 (2026-04-05)
**Status:** READY TO SHIP
**Owner:** Next session
**Deadline:** 1 session or escalate scope cut

---

## Why this document exists

H13 has existed as a PMO item for 15 sessions (raised #021, reframed #027, dormant ever since). It is the highest-business-value finding in the entire 35-session project. The reason it hasn't shipped is not complexity — it's the absence of a **pre-declared hypothesis and a bounded deliverable**.

This document closes that gap. It states the hypothesis, defines the minimum shippable artifact, and makes the deliverable testable BEFORE execution.

---

## Business Context

UNESCO operates payment runs through BCM (Bank Communication Management). BCM is designed for **dual control**: a different user must approve a batch than the one who created it. Without dual control, a single person can move money from create → send.

**Session #027 forensics established:**

| Metric | Value |
|--------|-------|
| Total batches where CRUSR = CHUSR | **3,394** |
| Average batch value | ~$514K |
| Total value processed without dual control | **~$1,745,516,000 (~$1.7B)** |
| Exception-list batches (AE/JO/embargo) with single user | **317 (UNES_AP_EX)** |
| Payroll batches by single user F_DERAKHSHAN | **259** |

**Breakdown by process:**

| Batch type | Count | Notes |
|-----------|-------|-------|
| UNES_AP_10 | 1,754 | Standard AP |
| UBO_AP_MAX | 627 | Field office max |
| UNES_AP_EX | 317 | 🔴 Exception-list countries (highest risk) |
| UNES_AP_ST | 299 | Standing instructions |
| PAYROLL | 276 | F_DERAKHSHAN alone = 259 |
| UNES_AP_IK | 119 | In-kind |
| IIEP | 2 | |

Source table: `BNK_BATCH_HEADER` with CRUSR/CHUSR columns. Data in Gold DB.

---

## Hypothesis

**H1 — Detection**
If we run a SQL query over `BNK_BATCH_HEADER` filtering `CRUSR = CHUSR AND STATUS IN ('COMPLETED','SENT')` and group by batch type + year + user, we will reproduce the 3,394 number within ±5% tolerance. This confirms the finding is reproducible and data-current.

**H2 — Exposure Projection**
If we rank same-user batches by `CURRENT_AMOUNT` DESC and cumulative-sum the top 20 users, we will find that fewer than 10 users account for >70% of the $1.7B. This identifies the remediation scope as "a handful of accounts," not "change the whole process."

**H3 — Remediation Paths**
There are exactly 3 remediation patterns:
- **(a) Detective** — nightly report sent to internal audit listing all same-user batches from the last 24h. Zero code in SAP. Fastest to ship.
- **(b) Preventive** — workflow 90000003 modification to enforce different approver. Requires YWFI package source (H14) and dev cycle in D01.
- **(c) Policy** — AE/JO/embargo batches (UNES_AP_EX=317) blocked from single-user approval via BCM config change (FBZP chain).

Path (a) is the minimum viable deliverable. Paths (b) and (c) require D01 dev access + Finance director sign-off and are out of scope for this session.

---

## Minimum Shippable Artifact (this session)

**Deliverable 1: BCM Dual-Control Monitoring Report**
- Python script: `Zagentexecution/bcm_dual_control_monitor.py`
- Inputs: Gold DB (`BNK_BATCH_HEADER`, `BNK_BATCH_ITEM`, `USR02` if present)
- Output: CSV + HTML companion at `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.html`
- Contents:
  1. Summary cards: total same-user batches, total $ exposure, top 5 users by $
  2. Table: all 3,394 batches with created_by, approved_by, type, date, amount, currency
  3. Filter by: batch type, date range, user
  4. Top-10 user exposure chart
  5. AE/JO exception-list highlight (UNES_AP_EX rows in red)
  6. Timeline: same-user batches by month 2024-2026

**Deliverable 2: Executive summary (one page)**
- Markdown: `knowledge/domains/BCM/h13_executive_summary.md`
- Sections: finding, exposure, named individuals with >50 batches, 3 remediation paths, recommended next step
- Intended reader: Finance Director / CFO

**Deliverable 3: PMO closure**
- Mark H13 as closed with evidence (the companion + summary)
- Add follow-up items: `H13a` (workflow mod, needs D01), `H13b` (BCM config for exception-list), `H13c` (policy doc draft for internal audit)

---

## Pre-Execution Checklist (Principle 4 — Hypothesis Grounding)

- [x] Hypothesis stated (H1, H2, H3)
- [x] Bounded deliverable defined (3 artifacts)
- [x] Input data identified (Gold DB tables named)
- [x] Output location specified
- [x] Success criteria: H1 must reproduce 3,394 ± 5%; companion must load in browser; summary fits on one page
- [x] Failure mode: if H1 fails (numbers diverge >5%), STOP and investigate data drift before continuing
- [x] Out-of-scope declared (D01 dev work, workflow mod, policy signoff)
- [x] Decision the artifact enables: "Should internal audit receive this report nightly?" (yes/no, answerable in one meeting)

---

## What a new CTO would ask

> "You've known about a $1.7B control gap for 15 sessions. Why isn't there a daily report on the CFO's desk?"

There isn't a good answer. The only answer is: **ship the report this session.**

---

## Links

- Source finding: `knowledge/session_retros/session_021_retro.md` (#021 original), #027 reframe
- Related: H14 (YWFI source, needed for path b)
- Skill: `sap_payment_bcm_agent` (should be invoked for data queries)
- Gold DB: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`

---

## AI Diligence

| Aspect | Detail |
|--------|--------|
| AI Role | Synthesized hypothesis from Session #021/#027 forensics. Proposed minimum shippable artifact. |
| Model | Claude Opus 4.6 (1M context) |
| Human Role | JP Lopez owns decision to ship and to approach Finance Director. |
| Verification | All numeric claims traceable to PMO_BRAIN.md H13 entry. No new facts introduced. |
| Accountability | JP Lopez maintains full responsibility. |
