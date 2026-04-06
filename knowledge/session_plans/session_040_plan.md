# Session #040 Plan

**Date:** 2026-04-06
**Previous:** #039 (committed 5c989ec, H18 DMEE resolved, Brain v2 architecture approved)
**Main agent:** Claude Opus 4.6 (1M context)

---

## Hypothesis (what this session will prove)

- **H1:** Brain v2 can be implemented end-to-end (all 3 phases) in a single session from the approved architecture spec. Testable by: `python -m brain_v2 build` produces >50K nodes and >100K edges with working impact/dependency queries.
- **H2:** The project's code is scattered in too many locations and can be consolidated without losing any artifacts. Testable by: zero .abap/.py files at project root, zero duplicate ABAP files, clear module structure in extracted_code/.
- **H3:** The Brain v2 dual paradigm (existence + impact + discovery) produces actionable findings on first run. Testable by: gap analysis returns >0 configured-but-unused items AND >0 dead-code items.

## Deliverables (shippable artifacts, named)

1. `brain_v2/` — Full implementation (core, parsers, ingestors, queries, CLI)
2. `brain_v2/output/brain_v2_graph.json` — 52K+ nodes, 112K+ edges
3. Project reorganization — extracted_code/ in 4 clean modules
4. `extracted_code/CODE_INVENTORY.csv` — 1,065 files tracked
5. PMO H30/H31/H32 struck
6. BRAIN_V2_ARCHITECTURE.md updated with dual paradigm spec
7. `session_040_plan.md` + `session_040_retro.md`

## Out of scope (declared)

- Brain v2 Phase 4 (continuous evolution, session auto-ingest)
- 260 mcp-backend-server-python scripts reorganization (future session)
- CODE_INVENTORY enrichment with extraction provenance (future)
- H19-H26 bank recon work (different domain)

## Success criteria (testable at close)

- [x] H1: brain_v2 build produces 52,313 nodes and 111,719 edges
- [x] H2: zero .abap/.py at root, zero duplicates, 4 clean modules
- [x] H3: gap analysis returns 2,931 findings (61 unused config, 774 undocumented code)
- [x] items_shipped >= items_added (3 shipped H30/H31/H32, 3 added H30/H31/H32 = net 0 but all shipped same session)
