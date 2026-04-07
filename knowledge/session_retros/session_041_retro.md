# Session #041 Retro — Brain v2 Completion: Impact Chain Operational

**Date:** 2026-04-06
**Previous:** #040 (Brain v2 3 phases shipped, but impact chain broken)
**Main agent:** Claude Opus 4.6 (1M context) via Claude Code

---

## Plan-vs-Retro Diff

### Hypotheses

| Plan Hypothesis | Status | Evidence |
|---|---|---|
| H1: Impact chain FPAYP.XREF3→banks can work with existing data | **CONFIRMED** | 32 objects affected across 5 depths. No new SAP extraction needed — used T042A bank routing + Session #039 knowledge. |
| H2: SQL alias resolution is the READS_FIELD bug | **CONFIRMED** | Parser generated `FIELD:A.LAND1` instead of `FIELD:YTFI_PPC_TAG.LAND1`. Fixed by parsing FROM clause AS aliases. |
| H3: Missing edges (not missing nodes) was the core issue | **CONFIRMED** | Only +107 behavioral edges transformed brain from broken to operational. Node count unchanged (52,478). |

### Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | USES_DMEE_TREE edges (36) from T042A-verified mappings | SHIPPED | `brain_v2/ingestors/config_ingestor.py` `_ingest_dmee_payment_links()` |
| 2 | SQL alias resolution in ABAP parser | SHIPPED | `brain_v2/parsers/abap_parser.py` `_parse_from_clause()` |
| 3 | Domain knowledge ingestor (88 expert edges) | SHIPPED | `brain_v2/ingestors/domain_knowledge_ingestor.py` (NEW) |
| 4 | Session ingestor for continuous enrichment | SHIPPED | `brain_v2/ingestors/session_ingestor.py` (NEW) |
| 5 | Community detection (Louvain) in CLI | SHIPPED | `brain_v2/cli.py` `cmd_communities()` |
| 6 | MCP integration (4 brain tools) | SHIPPED | `Zagentexecution/mcp-backend-server-python/sap_mcp_server.py` |
| 7 | Dependency query fix (PROCESS_CONTAINS) | SHIPPED | `brain_v2/queries/dependency.py` |
| 8 | ROUTES_TO_BANK → bidirectional impact | SHIPPED | `brain_v2/core/schema.py` |

**Closure math:** 8 deliverables shipped, 0 new items added. Net closure: +8. Session gate: PASS.

---

## Discoveries

1. **Gold DB T042Z is the wrong table** — Our T042Z has LAND1+ZLSCH (country-level payment method descriptions), NOT ZBUKR+ZLSCH+DTFOR (DMEE format assignment). The DMEE mapping had to come from domain knowledge + T042A bank routing, not from a single config table.

2. **107 edges changed everything** — The brain had 112,956 edges but impact analysis was dead because zero USES_DMEE_TREE and zero DMEE-class→table behavioral edges existed. Adding just 107 edges (36 USES_DMEE_TREE + 88 domain knowledge) made the full chain work.

3. **BAdI parameters are invisible to static analysis** — DMEE exit classes receive FPAYP and REGUH as method parameters from the BAdI framework, not via SELECT. A "domain knowledge ingestor" is the right pattern for encoding what humans know but parsers can't find.

4. **CO_TRANSPORTED_WITH is anti-pattern** — Architecture doc estimated 50K co-transport edges but they're redundant (already implicit via TR→object) and would explode the graph. Skipping was correct.

5. **ROUTES_TO_BANK must be bidirectional** — Forward-only meant the cascade stopped at payment methods. Banks are downstream receivers that NEED to know about format changes. Bidirectional fixed it.

6. **Community detection validates the graph** — DMEE cluster (community 6: all 3 DMEE classes + fields) and payment config cluster (community 7: 22 pay methods + 8 banks + 3 CoCodes) emerged naturally from Louvain. The graph structure reflects the real architecture.

---

## Failures/Corrections

1. **Initial DMEE_COMPANY_MAP used wrong payment method codes** — First attempt used `["T", "U"]` as payment methods for UNES. Actual T042A shows UNES uses `["4", "5", "H", "I", "J", "N", "O", "S"]`. Fixed by querying T042A directly and mapping SOG* banks → CGI trees.

2. **Dependency query had PROCESS_CONTAINS in wrong direction** — Initially in REVERSE_DEPENDENCY_EDGES (target depends on source), but process→step means process depends on its steps (forward dependency).

---

## Verification Check

| Claim | Verification | Result |
|---|---|---|
| Impact FPAYP.XREF3 returns 32 objects | `python -m brain_v2.cli impact "FIELD:FPAYP.XREF3" 6` | 32 objects: 3 classes, 3 trees, 20 pay methods, 6 banks |
| Dependency Payment_E2E returns 15 deps | `python -m brain_v2.cli depends "PROCESS:Payment_E2E"` | 15 deps: 7 steps + 8 tables |
| Community detection works | `python -m brain_v2.cli communities` | 10,916 communities, DMEE cluster at #6 |
| Session ingestor finds refs | `python -m brain_v2.cli ingest-session 39` | 14 findings, +14 edges |
| MCP tools added | Inspected sap_mcp_server.py | 4 tools: brain_impact, brain_depends, brain_search, brain_stats |

**AI Diligence Statement:** Claude diagnosed 5 bugs (missing USES_DMEE_TREE edges, SQL aliases, missing BAdI param edges, wrong impact direction for ROUTES_TO_BANK, wrong dependency direction for PROCESS_CONTAINS), implemented fixes in 8 files, and validated all changes via CLI. Human approved the approach after seeing the before/after comparison.

---

## PMO Reconciliation

### Items to strike:
- **G61** (Brain v2: fix impact query direction) — DONE this session. Impact direction model correct, ROUTES_TO_BANK→bidirectional, full chain works.
- **G62** (Brain v2: ingest DMEE→FPAYP.XREF3 edge) — DONE this session. Domain knowledge ingestor + USES_DMEE_TREE edges from T042A.

### Items unchanged:
- H19, H21, H22, H23, H25, H26 (all bank recon / data extraction — not touched)
- All other backlog items unchanged

### Net: 2 items struck, 0 added = net closure +2

---

## What Could Be Better (Retrospective)

1. **Should have queried T042A first** — Lost time creating wrong payment method mappings (["T", "U"]) when a simple SQL query would have shown the real codes immediately. **Rule: always query the data before hardcoding mappings.**

2. **Domain knowledge ingestor is powerful but manual** — Every expert-verified edge requires human knowledge. Consider: can we extract BAdI interface signatures from ABAP source to INFER which tables are passed as parameters? This would be semi-automatic.

3. **Gap analysis results are noisy** — 2,929 findings but 2,069 are "isolated nodes" (mostly background jobs with no code link). Need a severity filter or "interesting gaps only" mode.

4. **No HTML companion for Brain v2** — The brain has 11 CLI commands but no visual companion. A brain explorer HTML (interactive graph with vis.js, search, click-to-impact) would be the killer app.
