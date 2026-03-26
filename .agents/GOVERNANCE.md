# .agents/ — Internal Governance Index
*Authority: .agents/ (internal coordinator) | Version: 1.0 | 2026-03-26*

---

## Purpose

`.agents/` is the **internal coordinator** of the SAP Intelligence Platform. It governs skills, rules, workflows, and intelligence artifacts — mirroring the ecosystem-coordinator pattern at project level.

---

## Two-Tier Model

| Tier | Location | Role | Count |
|------|----------|------|-------|
| **Tier 1: Skills** | `.agents/skills/` + `lib/` | Reusable knowledge & framework modules | 31 skills + 8 lib modules |
| **Tier 2: Execution** | `Zagentexecution/` | Scripts that consume skills | 228+ scripts |

**Rule:** Execution scripts (`Zagentexecution/`) consume skill knowledge. They do NOT define patterns — skills do.

---

## Directory Structure

```
.agents/
├── GOVERNANCE.md              ← This file (internal coordinator index)
├── SKILL_MATURITY.md          ← Companion: maturity scores for all 31 skills
├── intelligence/              ← Brain, session log, PMO, architecture docs
│   ├── SESSION_LOG.md         ← One entry per session
│   ├── PMO_BRAIN.md           ← Task prioritization
│   ├── PROJECT_MEMORY.md      ← System architecture facts
│   ├── sap_brain.json         ← Knowledge graph (73.9K nodes)
│   └── sap_knowledge_graph.html ← Visual brain explorer
├── skills/                    ← 31 skills (SKILL.md each)
│   ├── coordinator/           ← Master routing agent (B2R/H2R/P2P/T2R/P2D)
│   ├── psm_domain_agent/      ← FM/Budget specialist
│   ├── hcm_domain_agent/      ← HR lifecycle specialist
│   ├── fi_domain_agent/       ← FI/GL specialist
│   ├── sap_data_extraction/   ← RFC extraction pipeline
│   ├── sap_class_deployment/  ← ABAP class creation
│   ├── sap_transport_intelligence/ ← CTS forensics
│   ├── sap_system_monitor/    ← SM04/SM35/SM37/ST22
│   └── ... (27 more)
├── rules/                     ← Hard constraints (6 files)
│   ├── sapwebgui_framework_findings.md  ← 103 experiments
│   ├── multi_agent_architecture.md      ← Agent design
│   ├── security_guardrails.md           ← Security rules
│   └── ...
└── workflows/                 ← Execution patterns (5 files)
    ├── hybrid_orchestration.md  ← WebGUI vs BAPI decision tree
    ├── session_start.md         ← Session protocol
    ├── session_retro.md         ← Retro template
    └── ...
```

---

## Skill Tiers by Maturity

| Maturity | Label | Count | Meaning |
|----------|-------|-------|---------|
| 4 | **Production** | 13 | Battle-tested, comprehensive docs, used in real sessions |
| 3 | **Functional** | 10 | Reliable, some polish needed |
| 2 | **Draft** | 4 | Framework present, incomplete |
| 1 | **Stub** | 4 | Placeholder, needs development |

Full scores: see [SKILL_MATURITY.md](SKILL_MATURITY.md)

---

## Model Routing

| Model | When to Use | Skills |
|-------|-------------|--------|
| **Opus** | Cross-domain synthesis, architecture, brain design | coordinator, GOVERNANCE |
| **Sonnet** | Domain analysis, knowledge writing, Fiori dev | domain agents, sap_fiori_tools, sap_transport_intelligence |
| **Haiku** | Data extraction, SQLite loading, batch ops | sap_data_extraction, parallel_html_build |

**Rule:** Loop + known pattern = Haiku. Judgment + synthesis = Opus. Everything else = Sonnet.

---

## Published Capabilities

This project publishes to the ecosystem:
- `sap-intelligence` skill (extraction, brain, transport analysis)
- `sap-gui-automation` skill (WebGUI + native desktop patterns)

Consumed from ecosystem:
- `session-start.md` / `session-end.md` (way-of-working)
- `collaboration-terms.md` (AI behavior)

---

## Governance Rules

1. **Skills define patterns** — execution scripts consume them
2. **SKILL.md is mandatory** — no skill directory without a SKILL.md
3. **Maturity review every 5 sessions** — promote or deprecate
4. **Memory ≠ Skills** — memory is context (for Claude), skills are instructions (for agents)
5. **Rules are hard constraints** — rules/ files override skill suggestions
6. **Session log is append-only** — one entry per session, never edit past entries
7. **Brain rebuild after extraction** — `sap_brain.py --build --html` after new data

---

## AI Diligence Statement

| Field | Value |
|-------|-------|
| AI Role | Designed governance structure, two-tier model, directory documentation based on existing project artifacts |
| Model | Claude Opus 4.6 (1M context) via Claude Code CLI |
| Human Role | JP Lopez directed creation per BROADCAST-001 from ecosystem-coordinator |
| Verification | Directory structure [VERIFIED] via filesystem reads. Skill count [VERIFIED]. Model routing rules [REPORTED] from MEMORY.md. Two-tier model [INFERRED] from existing project organization. |
| Accountability | JP Lopez maintains full responsibility |
