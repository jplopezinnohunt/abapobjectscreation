# Session Retro — 2026-03-15: Brain Progressive Disclosure + Infrastructure Cleanup

**Duration**: ~90 min | **Session**: #007 | **Systems**: Local only (no SAP connection)

---

## What Was Done

| Area | Achievement |
|------|------------|
| Brain full ingestion | Removed all SQL LIMIT caps — 760 nodes -> **73,381 nodes** (100% of funds, fund centers, transports) |
| Progressive Disclosure | 3-level access: L1 BRAIN_SUMMARY.md, L2 `--focus`, L3 full JSON |
| BRAIN_SUMMARY.md | Auto-generated ~150 line index — stats, join map, aggregates, structural nodes |
| `--focus` CLI mode | JIT domain loading — `--focus HCM` loads 75 nodes instead of 73K |
| `--summary` CLI mode | Regenerate L1 summary without full rebuild |
| Fund area aggregates | Each FM Area enriched with fmifiit_docs, active_funds, active_fund_centers counts |
| Smart HTML sampling | vis-network gets ~200 sampled nodes, legend shows `(viz/total)` ratio |
| SQLite consolidation | Deleted 4 stale DB copies (0B ghost + 5.8MB v2 x2 + 18MB partial gold) |
| Brain candidate_paths | Simplified to single canonical path — no fallback to stale copies |
| JOINS_VIA edge type | 8 new edges modeling table-to-table foreign keys (FMIFIIT->FMFCT, FMIFIIT->BKPF, etc.) |
| Deprecated tables dropped | `fmifiit_raw_data`, `projects`, `wbs_elements` dropped + VACUUM |
| L2 Skill created | `.agents/skills/sap_data_extraction/SKILL.md` — extraction protocol, schemas, join docs |
| meta.sources fixed | 5 -> 6 (process model was uncounted) |
| Model routing | Coordinator updated: Opus/Sonnet/Haiku routing by task complexity |
| Coordinator update | Session Start Protocol now uses progressive disclosure + auto-detection |

## Key Discoveries

| Discovery | Impact |
|-----------|--------|
| Brain was loading <5% of actual data (300/64K funds) | Fixed — now 100% in JSON, sampled for HTML |
| Anthropic's 3 papers converge on tiered memory + JIT loading | Implemented as L1/L2/L3 pattern |
| Agent Skills open standard uses same SKILL.md format we already have | Our skills are already compatible |
| MCP = infrastructure, Skills = procedural knowledge — complementary not competing | Architecture validated |
| Model routing saves tokens: Haiku for loops, Opus for synthesis | Added to coordinator |

## Anthropic Research Applied

| Paper | Pattern Applied |
|-------|----------------|
| [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Tiered memory, JIT loading, progressive disclosure |
| [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Artifact-based continuity (BRAIN_SUMMARY.md), session handoff |
| [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) | Orchestrator-worker, model routing by complexity |

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Brain nodes | 748 | 73,381 |
| Brain edges | 564 | 65,776 |
| SQLite DB copies | 5 | 1 |
| Skills with SKILL.md | 22 | 23 (+sap_data_extraction) |
| Brain access levels | 1 (all-or-nothing) | 3 (L1/L2/L3) |
| Edge types | 10 | 11 (+JOINS_VIA) |

## Next Critical (for Session #008)

1. Extract BKPF + BSEG — `run_overnight_extraction.py` is ready
2. Extract EKKO + EKPO — procurement data script ready
3. Evaluate `agentskills.io` open standard for portability
4. Fix RFC_SYSTEM_INFO parsing (P01 health shows `?`)
5. Design PRAAUNESC_SC Fiori replacement
