# Session #65 Retro — DMEE Configuration restructure (per-tree submenus + V000/V001 split)

**Date:** 2026-04-30
**Duration:** Long working session (single context)
**Focus:** (1) Re-evaluate Marlies' XML Address Excel "File Analysis2" tab against SAP/bank ground truth. (2) Restructure the BCM_StructuredAddressChange.html companion to organize DMEE Configuration BY TREE with per-tree UI↔XML parallel bridges and dedicated sidebar sub-menus. (3) Split V000 baseline content (Current Solution) from V001 delta content (Change Strategy → DMEE Configuration). (4) Add PMW program retrofit scope. (5) Capture 4 TIER_1 claims, 2 feedback rules, 1 KU.

---

## 1. Context

User passed Marlies' updated `XML Address un structured.xlsx` (sheet "File Analysis2") with 11 production payment cases × 4 XML segments = 44 segment-level outcomes annotated with bank acceptance verdicts and suggested fixes. Initial agent response promoted the Excel to TIER_1 evidence; user pushed back twice (correctly):

- "BUT MARLIES!!! is just a comment" — Marlies' file is one expert interpretation, not bank-side ground truth
- "the simulators are Python, not ABAP" — the V000/V001 sample XML files in `simulator_output/` are Python reconstructions, not real F110 output

These corrections forced an AGI re-evaluation that re-tiered all evidence properly:
- TIER_1: pain.001.001.09 XSD (in `xsd_validators/`), N_MENARD's TS DMEE CGI 2024-02-29 doc, brain claims 67/68/69/70/71/73 (FPAYHX field catalog, no UNESCO custom writers, BAdI dispatch footprint, D01 incompleteness, vendor master CBPR+ readiness, byte-offset layout)
- TIER_3: Marlies' Excel commentary, Python simulator output

Then a deep dive into actual DMEE tree structure (tx DMEE Display Format Tree screenshots) exposed that the agent had been **flattening "segments" into a list when the actual tree is deeply nested** per ISO 20022 — `<PstlAdr>` lives at TWO different paths (PmtInf > Dbtr > PstlAdr at level 5 batch debtor; PmtInf > CdtTrfTxInf > Cdtr > PstlAdr at level 6 per-transaction beneficiary) and the path disambiguates everything. NODE_IDs are invisible to operators; path addressing is the right convention for operator-facing artifacts.

Then a series of user clarifications on the mental model:
- "if segment exists why I need to add?" → distinguished segment-tag (party wrapper, exists) from sub-node (child of PstlAdr, must be INSERTed if missing)
- "we have a lot of nodes but maybe are hierarchical" → 95-node SEPA tree stratifies to 2 INSERT targets at level 5/6
- "we have a total disconnection between the UI way of configurate levels and the XML emitted" → UI indentation in tx DMEE = nesting depth in XML (1:1, no transformation)
- "still does not allow me to connect with the formats produced" → the engine literally walks DMEE_TREE_NODE rows and emits one XML element per row
- "needs to be done by all trees with the changes required in each tree" → per-tree Step A/B/C + UI↔XML bridge for each of 4 trees
- "should be a way to understand that, ... will be very simple the configuration and future maintenance" → hierarchy collapse simplifies any future structured-address change to "find parent container at right level, INSERT children"
- "do for each Tree a submenu on the left" → 4 new sub-tabs in the sidebar
- "some information should be moved to Current Solution" → V000 baseline content split out of DMEE Configuration
- Plus: "PMW programs that use DME files in PMW configuration" → new PMW retrofit scope flagged

## 2. Delivered this session

### Companion BCM_StructuredAddressChange.html (+1332 lines)

**Before:** Single tab `tab-strategy-dmee-config` containing both V000 baseline content and V001 deltas, organized concept-first.

**After:**
- **Foundations sub-tab** (`tab-strategy-dmee-config`, 564 lines): cross-tree concepts — version mechanic, Active/Maintenance bridge table, Word-document-with-track-changes analogy, V000/V001 admin byte-equality proof (with V000+V001 admin screenshots side-by-side), three operations on V001 (INSERT/MODIFY/SYNC), bridge-in-one-sentence (UI=XML 1:1), per-target simplified mappings (7 targets across 4 trees), cross-tree summary table (Step B operations · ABAP code change · Customizing TR · Special considerations), PMW program retrofit (new), "config not code" headline, references.
- **Tree 1 · SEPA sub-tab** (`tab-dmee-tree-sepa`, 195 lines): SEPA bridge in parallel (V000 + V001 UI↔XML, aligned by level) + Step A/B/C + verification SQL + rollback note + code-change=NONE.
- **Tree 2 · CITI sub-tab** (`tab-dmee-tree-citi`, 208 lines): CITI bridge in parallel showing 4 INSERT entry points (Dbtr-primary, Dbtr-altMor, UltmtCdtr/StrtNm MODIFY, CdtrAgt) + Step A/B/C + 9-delta verification + rollback + code-change=NONE (XSLT auto-removal handles empty leaves).
- **Tree 3 · CGI sub-tab** (`tab-dmee-tree-cgi`, 130 lines): CGI bridge in parallel showing CdtrAgt INSERT entry point + Step A/B/C + Pattern A 3-line BAdI guard ABAP (only ABAP touch in V001) + PPC regression check requirement + rollback + code-change=YES.
- **Tree 4 · CGI_1 sub-tab** (`tab-dmee-tree-cgi1`, 81 lines): CGI_1 bridge showing SYNC propagation from CGI parent + Step A/B/C (post-D01-RETROFIT-01) + verification SQL + rollback + code-change=NONE.
- **4 new sidebar nav-subitems** under "DMEE Configuration · foundations": ↳ Tree 1 · SEPA, ↳ Tree 2 · CITI, ↳ Tree 3 · CGI, ↳ Tree 4 · CGI_1 (each with double-indent style `padding-left:54px` to nest under DMEE Configuration).
- **Current Solution → Per-tree current state section (NEW, +537 lines)**: V000 baseline organized per tree. SEPA section carries the full content (ASCII tree, 3 tree-pane screenshots, Dbtr highlighted screenshot, the 6 DMEE Display tabs with 5 SEPA tab screenshots, hierarchy-stratification table, same-TECH_NAME-at-different-levels disambiguation table). CITI/CGI/CGI_1 sections carry summary stubs flagging "Phase 2 capture pending" for tree-level tab settings + tree-pane screenshots. Cross-reference link to Change Strategy → DMEE Configuration for V001 deltas.
- **8 cross-references** between the two zones (DME Config ↔ Current Solution).
- **PMW program retrofit section** (NEW, in DMEE Configuration foundations): documents 8 SAP objects beyond the DMEE tree (T042Z, T042Y, TFPM042F, TFPM042FB, VARI/SAPFPAYM_*, OBPM2, YCL_IDFI_CGI_DMEE_*, YTFI_PPC_*) that need D01↔P01 alignment. Recommends D01-RETROFIT-02-PMW transport before Phase 3.
- **13 screenshots** saved to `knowledge/domains/Payment/sap_standard_reference/dme_screenshots/unesco_dmee_*.png`: Step A initial-screen popup, V000+V001 admin tabs, tree-top/mid/bottom, Dbtr/PstlAdr highlighted, format_attributes, levels, sort_key, file_data, post_processing, tree_top_alt. 11 embedded in companion (2 unused: tree_top_alt and step_a_01-orphan-after-restructure-now-re-embedded).
- **Plan-agent-flagged duplicates removed**: per-format V001 file deltas bullet list (overlapped with cross-tree summary table).

### Brain updates

**4 new TIER_1 claims (117-120):**
- **117** — DMEE tree node hierarchy collapses operationally: of 95 nodes in /SEPA_CT_UNES, only 2 are V001 INSERT targets. Generalises to all future bank-format changes.
- **118** — tx DMEE UI tree-pane indentation depth = XML output element nesting depth (1:1, no transformation). The DMEE tree IS the XML template.
- **119** — TECH_NAME values repeat across DMEE tree levels and identify different XML elements depending on parent path. Use path addressing in operator-facing artifacts; NODE_IDs reserved for technical reference.
- **120** — /SEPA_CT_UNES Post Processing tab settings verified: Empty Element Processing="Do Not Remove" + XSLT Program=(empty). Therefore V001 INSERTs (matrix rows 1-8) MUST carry DMEE_TREE_COND empty-suppress conditions.

**2 new feedback rules:**
- `feedback_dmee_path_addressing_in_operator_artifacts` (HIGH, derives CP-001) — In operator-facing artifacts, address DMEE tree nodes by full path (Document > CstmrCdtTrfInitn > PmtInf > ... > PstlAdr). NODE_IDs reserved for technical-reference channels (CSV columns, RFC verification SQL, brain claim evidence).
- `feedback_companion_split_v000_baseline_from_v001_changes` (HIGH, derives CP-001) — Split companion content into two clearly-distinct zones: Current Solution (V000 baseline, per object) + Change Strategy (V001 deltas, per object). Cross-reference between zones explicitly. Do not mix V000 baseline content with V001 delta content in the same section.

**1 new KU:**
- **KU-2026-PMW-D01-ALIGNMENT** (HIGH, blocks Phase 3 unit-test) — Are the PMW configuration tables and program variants invoked by F110 byte-equal between D01 and P01 for the 4 in-scope formats? Specifically T042Z, T042Y, TFPM042F, TFPM042FB, VARI/SAPFPAYM_*, OBPM2, YTFI_PPC_*. Owners: Pablo + N_MENARD + M_SPRONK.

**Brain stats post-rebuild:** 278 objects · 107 rules · 120 claims · 5 incident records · 14 domains · 42 known_unknowns · 7 data_quality_open · FRESH.

## 3. Phase 4b — SAP-itself learnings

**Four durable SAP learnings this session that the next agent needs:**

### Learning 1 — DMEE tree-level tab settings are load-bearing for V001 INSERT design

The DMEE Display Format Tree screen shows 6 tabs: Administrative data · Format attributes · Levels · Sort/key fields · File Data · **Post Processing**. The last one carries TWO settings that govern V001 INSERT viability:
- `Empty Element Processing` ∈ { "Do Not Remove", "Remove all" }
- `XSLT Program` (optional post-processor)

For `/SEPA_CT_UNES` (verified 2026-04-30 via screenshot): Empty Element Processing = **"Do Not Remove"**, XSLT Program = empty. Consequence: any V001 INSERT row whose source resolves to space at runtime emits empty `<Tag></Tag>` to the file, breaking pain.001.001.03 schema validation at the bank. **Therefore each V001 INSERT requires its own DMEE_TREE_COND empty-suppress condition** (matrix rows 1-8 specify exactly that). Implication for any UNESCO-like environment: **before designing INSERTs into a DMEE tree, check the Post Processing tab**. CITI uses XSLT post-processing instead (CGI_XML_CT_XSLT auto-removes empty leaves), so CITI INSERTs do NOT need DMEE_TREE_COND. CGI/CGI_1 settings TBD Phase 2 verification.

### Learning 2 — TFPM042FB Event-05 registration is per-tree, not automatic

F110 does not auto-fill `FPAYHX-FREF` (REF01..REF10 byte-packed structured-address buffer). The tree must have a row in TFPM042FB linking the format to a user-exit FM. For Event 05 (address fill), the FM is `FI_PAYMEDIUM_DMEE_CGI_05`. Today TFPM042FB has Event-05 rows registered for `/CITI/XML/UNESCO/DC_V3_01` and `/CGI_XML_CT_UNESCO`, **but NOT for `/SEPA_CT_UNES`**. v001_change_matrix.csv row 9 ADDS the missing TFPM042FB row for SEPA. Without it, the V001 INSERTs that bind to FPAYHX-REF01[0..60] etc. would emit empty tags because the buffer is never filled for SEPA payments. Implication: **registering Event 05 is part of the V001 work for SEPA**, not a precondition assumed to exist.

### Learning 3 — D01↔P01 retrofit scope must include PMW configuration tables and program variants

The current D01-RETROFIT-01 scope (claim 111) covers DMEE tree drift on `/CGI_XML_CT_UNESCO_1` + dormant V001 PURGE on all 4 trees + 5 P01-only BAdI classes (claim 70). It does **NOT** cover the PMW configuration tables and SAPFPAYM_* program variants invoked by F110:
- T042Z (payment routing per LAND1/ZLSCH/WAERS)
- T042Y (PMW format definition: FORMI → SAPFPAYM_<format> + format-spec structure)
- TFPM042F + TFPM042FB (Event registration)
- VARI/VARID (SAPFPAYM_* program variants used by F110 batch jobs in P01)
- OBPM2 / V_TFPM2 (print forms — usually empty for XML formats)
- YTFI_PPC_STRUC + YTFI_PPC_TAG + T015L (PPC dispatch tables for 9 PPC countries)

If any of these are missing or different in D01, V001 testing in D01 will produce different output from F110 in P01 even with identical DMEE trees. Implication: **before any DMEE-format migration, byte-compare the surrounding PMW infrastructure D01 vs P01**, not just the tree itself. Captured as KU-2026-PMW-D01-ALIGNMENT with Phase 2 Week 0 discovery + triage + retrofit transport plan.

### Learning 4 — DMEE versioning admin metadata is byte-equal except VERSION column

When tx DMEE → Tree → Versions → Create Version is executed (e.g. V000 → V001), SAP **copies the entire DMEE_TREE_HEAD row keeping every metadata field** — only the VERSION column changes. Visual confirmation 2026-04-30 via tx DMEE Display Format Tree screenshots on `/SEPA_CT_UNES`:

| Field | V000 | V001 |
|---|---|---|
| Tree type | PAYM | PAYM |
| Format tree | /SEPA_CT_UNES | /SEPA_CT_UNES |
| Short Description | SEPA Credit Transfer auf pain.001.001.03 UNESCO | SEPA Credit Transfer auf pain.001.001.03 UNESCO |
| Documentation | DMEE_SEPA_CT | DMEE_SEPA_CT |
| **Version** | **0** | **1** |
| Author | M_SPRONK | M_SPRONK |
| Created on / at | 27.11.2013 / 18:32:02 | 27.11.2013 / 18:32:02 |
| Last Changed By | M_SPRONK | M_SPRONK |
| Changed on / at | 23.11.2021 / 10:36:24 | 23.11.2021 / 10:36:24 |

Implication: **the dormant V001 in D01 of `/SEPA_CT_UNES` is byte-identical to V000 not just structurally but also at admin-metadata level (verified 2026-04-30 via tx DMEE screenshot)**. Two new facts specific to /SEPA_CT_UNES: (1) created 27.11.2013 by M_SPRONK — 12 years ago. (2) Both V000 and V001 share Last Changed timestamp 23.11.2021 — Create Version was executed on or before that date, consistent with claim 102 (zero V001 transports 2017-2024). This strengthens claim 109 visually for SEPA. **Generalisation to CITI/CGI/CGI_1 is asserted by claim 109 RFC count-equality (TIER_1) but admin-metadata visual confirmation for those 3 trees is pending Phase 2 capture** — flagged in the per-tree current-state stubs of Current Solution.

## 4. AGI properties this session

- **Knowledge over velocity (CP-001)**: when user pushed back on Marlies as authority, agent re-tiered evidence rather than defending. Re-tiered SAP V000/V001 sample files from "real samples" (TIER_1) to "Python simulator output" (TIER_3) when user clarified. Sustained the discipline through multiple correction rounds without abbreviation creep.
- **Preserve first (CP-002)**: the BIG companion restructure was done with a Python script (split_dmee_tabs.py — 145 lines) that performed atomic cut/paste with explicit start/end markers, not a series of fragile Edit operations. Script ran in one pass (post-rebuild stats verified: 4 sub-tabs created, foundations tab trimmed by ~580 lines, no content orphaned), then deleted. No content was lost; cross-references between zones preserved navigability.
- **Precision + evidence (CP-003)**: every claim 117-120 is anchored to specific RFC extractions or screenshot evidence (file paths cited in claim.evidence_for[]). The new feedback rule `feedback_dmee_path_addressing_in_operator_artifacts` includes the exact user-pushback quote that triggered it, ensuring future sessions can audit the rule's provenance.
- **Self-awareness via subagent**: when user requested a structural review of DMEE Configuration, agent invoked Plan subagent for a fresh-context audit (the agent's own narrative would have biased toward its existing structure). Plan agent produced a ~600-line restructure proposal mapping every existing block to a new location, with risk callouts. Agent then executed the proposal incrementally, not all-at-once.
- **Path addressing for operator artifacts**: codified as `feedback_dmee_path_addressing_in_operator_artifacts` after user said "you have multiple levels and names" + "screen is not correctly map". NODE_IDs in operator-facing artifacts → operators cannot navigate by them in tx DMEE; full XML path → matches what the operator sees on screen.

## 5. PMO / status

PMO not maintained in formal H/G items this session. The Phase 2 entry blockers list now stable at:

1. **D01-RETROFIT-01** (DMEE tree drift + dormant V001 PURGE + 5 P01-only BAdI classes) — claim 111 scope
2. **D01-RETROFIT-02-PMW** (NEW Session #65) — KU-2026-PMW-D01-ALIGNMENT scope: T042Z/T042Y/TFPM042F/TFPM042FB/VARI/OBPM2/YTFI_PPC_* alignment
3. PURGE-vs-REPURPOSE decision on dormant D01 V001 (recommend PURGE — Marlies + N_MENARD)
4. CGI_1 Nm Z-field experiment fate (revert to P01 vs keep+promote — Marlies)
5. LZBKZ validation Option A vs C (BAPI bypass verification needed — N_MENARD)
6. Pattern A guard ABAP review (N_MENARD)
7. TRM written acceptance from SocGen / Citi / CGI member banks for V001 Fully-Structured commitment

Phase 2 capture queue (Phase 0 Week 0):
- CITI 6-tabs screenshots (especially Post Processing — XSLT confirmation)
- CGI 6-tabs screenshots (especially Post Processing — TBD setting blocks DMEE_TREE_COND decision)
- CGI_1 6-tabs screenshots (expected identical to CGI parent — RFC byte-equality verification)
- 4 CITI tree-pane screenshots (one per V001 INSERT entry point highlighted)
- 1 CGI tree-pane screenshot (CdtrAgt highlighted)
- 1 CGI_1 tree-pane screenshot (post-retrofit only)
- 8-object PMW alignment RFC discovery (T042Z/T042Y/TFPM042F/TFPM042FB/VARI/OBPM2/YTFI_PPC_*)

## 6. Files changed this session

```
companions/BCM_StructuredAddressChange.html       +1,332 lines
brain_v2/agent_rules/feedback_rules.json           +50 lines (2 new rules: 105→107)
brain_v2/agi/known_unknowns.json                   +36 lines (1 new KU: 41→42)
brain_v2/claims/claims.json                       +115 lines (4 new claims: 116→120)
brain_v2/brain_state.json                         +231 lines (rebuilt)
knowledge/domains/Payment/sap_standard_reference/dme_screenshots/   +13 PNG files
knowledge/session_retros/session_065_retro.md     (this file)
Zagentexecution/incidents/xml_payment_structured_address/original_marlies/XML Address un structured.xlsx  Bin (USER INPUT — not session output)
```

Note on the Excel file: Marlies' v2 with the new "File Analysis2" tab is **user input opened during the session**; the Modified flag in `git status` is incidental Excel-on-close (Excel rewrites file metadata when reopened even with no edits). The session's deliverable from this file was the **brain re-tiering of its content from TIER_1 to TIER_3** (captured in §1 and now reflected via the path-addressing rule + the explicit AGI re-evaluation discipline). The Excel itself is not a session output and need not be committed if the user prefers to keep it local — but it is included here for traceability.

## 7. Next session entry points

1. **Phase 2 Week 0 — PMW alignment discovery**: write the 8 RFC_READ_TABLE comparisons; output `knowledge/domains/Payment/d01_p01_pmw_alignment_session65.json`. Owner: Pablo.
2. **Phase 2 Week 0 — CITI/CGI/CGI_1 tree-level tab settings capture**: 5 screenshots per tree × 3 trees = 15 screenshots. Owner: M_SPRONK (in tx DMEE on D01).
3. **Phase 2 Week 1 — D01-RETROFIT-01 execution**: claim 111 scope (CGI_1 12-delta surgical fix + dormant V001 PURGE on all 4 trees + 5 P01-only BAdI retrofit). Owner: Pablo + N_MENARD.
4. **Bank TRM outreach** (drafts already in `Zagentexecution/incidents/xml_payment_structured_address/trm_outreach_drafts/`): SocGen + Citi + CGI member banks for V001 Fully-Structured commitment.

## 8. Open items / follow-ups

| Item | Why | Resolution path |
|---|---|---|
| Phase 0 AGI retro audit subagent | Mandatory per session_close_protocol.md Phase 0 | Run as separate subagent in next session. This retro file is the input. |
| `unesco_dmee_tree_top_alt.png` (1 of 13) | unused, duplicates tree_top.png | Keep on disk for future reference (alternative top-of-tree expansion); not an embedding gap. |
| Fast-fail blockers | PMO Arithmetic Gate (Phase 0.75) — N/A this session (no formal PMO updates) | Skip; mark as not-applicable in next session preflight. |

## 9. Brain anchors created this session

- **claim 117** — Hierarchy collapse: 95 nodes → 2 INSERT targets (TIER_1)
- **claim 118** — UI indentation = XML nesting depth, 1:1 (TIER_1)
- **claim 119** — TECH_NAME path-disambiguation rule (TIER_1)
- **claim 120** — /SEPA_CT_UNES Post Processing settings + DMEE_TREE_COND mandatory (TIER_1)
- **rule** `feedback_dmee_path_addressing_in_operator_artifacts` (HIGH, CP-001)
- **rule** `feedback_companion_split_v000_baseline_from_v001_changes` (HIGH, CP-001)
- **KU-2026-PMW-D01-ALIGNMENT** (HIGH, blocks Phase 3 unit-test)

---

**Session #65 closed 2026-04-30. Companion ready for stakeholder review (Marlies, N_MENARD, Pablo). Brain rebuilt FRESH with 120 claims, 107 rules, 42 KUs.**
