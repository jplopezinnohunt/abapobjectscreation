# Session #039 Retro — H18 DMEE Resolution + Skill Routing + Payment Companion Enhancement

**Date:** 2026-04-06
**Plan file:** `knowledge/session_plans/session_039_plan.md` (this retro diffs against it)
**Previous:** #038 (committed ae54fbe, 15/15 deliverables)
**Main agent:** Claude Opus 4.6 (1M context) via Claude Code

---

## Plan-vs-Retro Diff

### Hypotheses

| Plan Hypothesis | Status | Evidence |
|---|---|---|
| H1: 72-char ABAP truncation routes into sap_class_deployment skill | CONFIRMED | New "Common Failure Modes" subsection with SELECT SINGLE+UPDATE FROM ls pattern, raise SystemExit safety rail, reference to h29_skat_update.py. |
| H2: RECONNECTABLE_ERRORS routes into sap_data_extraction skill | CONFIRMED | New "Reconnect Patterns" subsection with 14-pattern table, rationale per pattern, validating case reference. |
| H3: SEPA `<Purp><Cd>` lives in DMEE_TREE_NODES, not ABAP | **CONFIRMED FROM P01** | `Purp > Cd` node (N_9662041050) in `/CGI_XML_CT_UNESCO` reads `FPAYP.XREF3` via BAdI `FI_CGI_DMEE_EXIT_W_BADI`. 13 UNESCO trees analyzed (8,308 nodes in P01). Not a static literal — runtime field mapping. |

### Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | sap_class_deployment SKILL.md — 72-char subsection | SHIPPED | `.agents/skills/sap_class_deployment/SKILL.md` |
| 2 | sap_data_extraction SKILL.md — reconnect patterns | SHIPPED | `.agents/skills/sap_data_extraction/SKILL.md` |
| 3 | h18_dmee_tree_probe.py | SHIPPED | `Zagentexecution/mcp-backend-server-python/` |
| 4 | h18_dmee_tree_findings.md | SHIPPED | `knowledge/domains/Payment/` |
| 5 | h18_dmee_trees.csv (13 trees, P01) | SHIPPED | `knowledge/domains/Payment/` |
| 6 | h18_dmee_tree_nodes.csv (8,308 nodes, P01) | SHIPPED | `knowledge/domains/Payment/` |
| 7 | h18_dmee_d01_vs_p01_comparison.csv | SHIPPED | `knowledge/domains/Payment/` |
| 8 | payment_bcm_companion.html — DMEE sections (E2E explanation, 3 banking channels, active/inactive classification, PurposeCode flow, D01 vs P01 comparison, new country checklist, T042Z FORMI mapping) | SHIPPED | `Zagentexecution/mcp-backend-server-python/` |
| 9 | PMO H18 struck | SHIPPED | `.agents/intelligence/PMO_BRAIN.md` |
| 10 | feedback_data_p01_code_d01.md strengthened | SHIPPED | Auto-memory |
| 11 | .session_state.json baseline | SHIPPED | `.agents/intelligence/` |
| 12 | session_039_plan.md | SHIPPED | `knowledge/session_plans/` |
| 13 | session_039_retro.md | SHIPPED | THIS FILE |

**13 / 13 deliverables shipped.** 3 hypotheses confirmed. H18 zombie closed after 13 sessions.

---

## Closure Math

- **Items at start:** B=0 H=7 G=21 = 28
- **Items struck:** H18 = 1
- **Items added:** 0
- **Items at end:** B=0 H=6 G=21 = 27
- **Net closure:** +1 (H18 shipped), 0 added
- **Result:** GREEN (items_shipped > items_added)

---

## Key Findings

### H18 — SEPA PurposeCode Resolution (13 sessions to close)

**Timeline:**
- #026: H18 raised — "read YCL_IDFI_CGI_DMEE_AE/BH source to find XML PurpCd value"
- #038: ABAP classes falsified — AE/BH don't exist, FR/FALLBACK/UTIL have zero Purp/Cd literals
- #039: DMEE tree confirmed — `Purp > Cd` node reads `FPAYP.XREF3` via BAdI, not a static literal

**Root cause of the 13-session delay:** The original PMO note named classes that don't exist (AE/BH) and assumed the PurposeCode would be a literal in ABAP source. It was never in ABAP — it's a DMEE tree field mapping processed by a BAdI. The wrong investigation vector cost 11 sessions of deferral before falsification in #038.

### DMEE Tree Active/Inactive Classification

Of 13 UNESCO DMEE trees in P01:
- **6 active** (referenced in T042Z.FORMI by at least one payment method)
- **7 inactive/legacy** (exist but not assigned — test variants, superseded formats, DD trees)

3 banking channels: CGI/SocGen (pain.001), Citibank (proprietary XML), SEPA CT (ISO 20022)

### D01 vs P01 Divergence

12/13 trees identical. `/CGI_XML_CT_UNESCO_1` diverges: D01 has 1 extra SCB node, P01 has 8 extra AdrLine nodes (address formatting applied directly in production).

Initial probe run showed D01 with 2× more nodes per tree than P01 — this was caused by the `VERSION` field in DMEE_TREE_NODE (D01 retains inactive versions). After filtering to comparable fields, node counts matched except the 1 divergent tree.

### P01 Connectivity Issue

P01 was initially unreachable via RFC (WSAETIMEDOUT on port 4800). VPN was connected (IP 172.16.190.5) but routing table lacked route to 172.16.4.0/24. D01 was reachable. Root cause: VPN split-tunnel policy change or user session state. P01 became reachable later in the session without any intervention.

**User correction applied:** Initial probe ran against D01 as fallback. User correctly rejected D01 results for config analysis — "solo sirven datos de P01". Feedback rule `feedback_data_p01_code_d01.md` strengthened to include ALL reads (not just data — config too). Probe re-ran against P01 and returned valid results.

---

## What Failed and Why

### 1. D01 fallback for config read (my error)

When P01 was unreachable, I ran the DMEE probe against D01 and presented results as valid. User correctly rejected this. The rule is: ALL reads from P01, not just transactional data. Config (DMEE trees, FBZP, T042*) must also come from P01. D01 may have untransported changes.

**Fix:** Updated `feedback_data_p01_code_d01.md` to make this explicit. If P01 is down, wait — don't fall back to D01 for reads.

### 2. Initial filter missed Purp/Cd nodes

The first probe searched for `Purp`/`Cd` in `TECH_NAME` — which matched many `Cd` nodes (87 in one tree). But the filter reported "0 Purp/Cd candidates" because it searched `MP_CONST` for SEPA code values, and all Cd nodes have empty `MP_CONST` (they use `MP_SC_TAB`/`MP_SC_FLD` field references instead). The second pass with explicit `TECH_NAME` + `MP_SC_TAB`/`MP_SC_FLD` fields found the answer immediately.

---

## Scope Expansion (user-requested, justified)

- **D01 vs P01 comparison** — user asked "para validar que sean iguales". Added as deliverable 7.
- **Payment companion enhancement** — user asked for DMEE config to be added to companion with E2E explanation and new country checklist. Added as deliverable 8.
- **T042Z FORMI mapping** — user asked "como podemos saber cual tree esta activo". Queried T042Z from P01, mapped all 27 DMEE-using payment methods.

All additions are directly related to H18 and add actionable value (new country configuration guide).

---

## BROADCAST-003 Acknowledgment

No ecosystem-coordinator edits in #039. Discipline acknowledged.

---

## AI Diligence

| Aspect | Detail |
|---|---|
| AI Role | Authored all 13 deliverables. 1 wrong turn (D01 fallback) caught by user pushback. |
| Model | Claude Opus 4.6 (1M context) |
| Human Role | JP Lopez caught D01 config read violation, directed P01-only policy, requested comparison + companion enhancement + active tree identification. |
| Verification | H18 answer verified from P01 production data. D01 vs P01 comparison verified node-by-node. T042Z mapping verified against 263 payment method entries. |
| Accountability | JP Lopez maintains full responsibility. |

---

## Verification Check (Principle 8)

- **Assumption challenged:** "D01 config = P01 config because it's transported" — **FALSIFIED.** `/CGI_XML_CT_UNESCO_1` diverges. D01 has draft versions. User's rule is correct: only P01 data matters.
- **Gap identified:** BAdI `FI_CGI_DMEE_EXIT_W_BADI` implementation source (`YCL_IDFI_CGI_DMEE_FR`, etc.) was extracted in #038 but the specific method that handles the `Purp > Cd` node was not traced. The `GET_CREDIT` method in these classes likely contains the PurposeCode transformation logic.
- **Claim probed:** "7 of 13 trees are inactive" — **VERIFIED** via T042Z.FORMI cross-reference. None of the 7 inactive trees appear in any T042Z entry.

---

## Claims Verification (Principle 10)

| Claim | Tag | Evidence |
|---|---|---|
| 8,308 nodes in P01 | [VERIFIED] | `h18_dmee_tree_nodes.csv` row count, probe stdout |
| 13 UNESCO trees analyzed | [VERIFIED] | `h18_dmee_trees.csv` has 13 rows |
| 12/13 trees identical D01 vs P01 | [VERIFIED] | `h18_dmee_d01_vs_p01_comparison.csv` — only `/CGI_XML_CT_UNESCO_1` has non-zero diffs |
| 7 of 13 trees inactive | [VERIFIED] | T042Z.FORMI query: 0 entries reference the 7 inactive trees |
| 6 active trees in production | [VERIFIED] | T042Z.FORMI cross-ref: `/CGI_XML_CT_UNESCO`, `/SEPA_CT_UNES`, `/CITI/XML/UNESCO/DC_V3_01`, `/SEPA_CT_ICTP_ISO`, `EXTRASEPA`, `EXTRASEPA_I` |
| 631 nodes in /CGI_XML_CT_UNESCO (P01) | [VERIFIED] | Probe stdout + CSV filter on TREE_ID |
| PurposeCode from FPAYP.XREF3 | [VERIFIED] | DMEE_TREE_NODE row N_9662041050: TECH_NAME=Cd, MP_SC_TAB=FPAYP, MP_SC_FLD=XREF3 |
| 27 PMO items at end | [VERIFIED] | Manual count of non-struck items in PMO body: 6H + 21G = 27 |
| 263 payment methods in T042Z | [VERIFIED] | RFC_READ_TABLE T042Z, 263 rows returned |
| 27 DMEE-using payment methods | [VERIFIED] | T042Z rows with non-empty FORMI field |
| 3 banking channels | [INFERRED] | Derived from T042Z.FORMI grouping — CGI/Citibank/SEPA. Actual bank relationships not confirmed beyond tree naming convention |

---

## What a New CTO Would Kill

- **payment_bcm_companion.html approaching 1MB** — adding sections to a growing HTML file without evidence anyone reads it or makes decisions from it
- **9 bank recon zombies (H19, H21-H26, H25, H26)** — partial data extractions sitting since #029-#030 with no analysis output. A CTO would ask: "Ship or kill the whole workstream?"
- **G28 (Fiori PA Mass Update, 37 sessions old)** — has a 5-session kill deadline from #037, 2 consumed

## Decisions Deferred Without Reason

- **PMO header reconciliation** — neither #038 nor #039 updated the PMO header until the AGI retro audit caught it. No reason given for the 2-session drift.
- **Bank recon workstream** — H19/H21/H22/H23/H25/H26 all declared HIGH but not touched in #039. Recommended for "next session" but that recommendation was also made in #030.
- **FPAYP.XREF3 population source** — the companion's new-country checklist says "XREF3 populated from vendor master or payment config" but this is [INFERRED], not verified.

## Unexplained Artifact

- **`payment_event_log.csv` (+413,323 lines in git diff)** — pre-existing file from Session #022, last committed as `8c5c333`. Modified at some point between #022 and now (likely during #028 payment event log rebuild) but never re-committed. NOT #039 work. Excluded from #039 commit scope. Should be committed in a future session with proper attribution or reverted to committed state.

## Claims That Failed Verification

- **PMO header said "10 High / 31 total"** — stale since #037. Actual: 6H / 27. Fixed in this retro cycle.
- **Initial D01 result presented as valid** — user caught that D01 config data is not trustworthy. `/CGI_XML_CT_UNESCO_1` proved the point: 9 nodes differ between systems.

---

## Recommended Next Session Focus

1. **Trace FPAYP.XREF3 population** — where does the PurposeCode value actually get set? Vendor master (LFB1.XREF3?), payment config, or F110 runtime? This is the missing link for the new-country guide.
2. **Kill or ship bank recon (H19/H21-H26)** — 6 items at 10-11 sessions old. Dedicate a session or kill the workstream.
3. **H19/H21/H22/H23 bank recon** — if not killed, finish FEBEP/FEBKO gaps + currency conversion
