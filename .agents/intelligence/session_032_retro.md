# Session #032 Retrospective (2026-04-01 to 2026-04-03)

## Theme: Integration Archaeology + Knowledge Hub

## Deliverables

| # | Deliverable | Size | New/Updated |
|---|------------|------|-------------|
| 1 | Landing Page (`unesco_sap_landing.html`) | 23KB | NEW — 15 companions, 5 domains, search, filters |
| 2 | Connectivity Diagram v2 (pure CSS/SVG) | 36KB | REWRITE — 38 systems, 8 zones, hub-and-spoke |
| 3 | System Inventory (`system_inventory.html`) | 59KB | NEW — 31 system cards, direction map, 4 integration types |
| 4 | RFC Analysis (`rfc_analysis.html`) | 38KB | NEW — 239 destinations, 5 tabs |
| 5 | FI Maintenance (`fi_maintenance.html`) | 34KB | NEW — 6 tabs, support reference |
| 6 | Integration Diagram Skill | N/A | NEW — `.agents/skills/integration_diagram/SKILL.md` |
| 7 | Gold DB: `tfdir_custom` | 3,073 rows | NEW — 334 RFC-enabled, 21 domains |

## Key Discoveries

1. **7 UNESCO .NET Apps** — SISTER (47 FMs), HR Workflow (87), CMT (44), UBO (15), Travel (21), Mouv (12), Procurement (13) = 334 RFC-enabled custom FMs
2. **BCU = Budget Control System** (2018 project), not Business Connector
3. **MuleSoft = middleware** → target systems are Core Manager / Core Planner
4. **BizTalk = middleware** → target system is SuccessFactors Employee Central (not yet live)
5. **TULIP + UNESDIR** — SQL Server DBCON, both 93% job failure rate
6. **Direction map** — 14 BIDIR (trusted), 81 OUT, 50 IN, 94 SELF
7. **SAPBC → us0033** — legacy Business Connector, probably dead
8. **SuccessFactors** — PYC_SFEC_SRV inactive, EPI-USE class in transports, preparing migration
9. **SAPTO.NET / UNESCODL** — .NET program "UNESCO Download" on P01 app server 9

## Errors & Corrections

1. **4 diagram rebuilds** — built visual before completing data analysis. New rule: data first, visualization second.
2. **BCU misclassified** as Business Connector from hostname. New rule: always cross-reference CTS/jobs/code before naming.
3. **MuleSoft treated as system** instead of middleware. User corrected: middleware ≠ target system.
4. **SuccessFactors missed initially** — connects via HTTP/ICF not RFC, so RFCDES search missed it.

## New Rules

1. `feedback_data_before_visual.md` — extract ALL data before building visuals
2. `feedback_classify_systems_properly.md` — never guess system purpose from hostname
3. `feedback_diagram_layout_standard.md` — use integration_diagram skill for all connectivity diagrams

## Architecture Decisions

- Landing page = index of ALL companions across 5 domains
- Support & Maintenance = separate section from Knowledge (Finance/Process/Transport/Infrastructure)
- Finance Operations lives in BOTH Finance (knowledge) AND Support (operations)
- Companions link to each other (connectivity → system inventory → RFC analysis)
- vis.js removed from connectivity diagram — pure CSS/SVG now (36KB vs 648KB)

## Gold DB Changes

| Table | Rows | New |
|-------|------|-----|
| tfdir_custom | 3,073 | YES — all Z*/Y* function modules with RFC flag and app domain |

Total tables: 68 (was 52)

## Skills

- NEW: `integration_diagram` (#37) — container-based diagram template
- UPDATED: `sap_interface_intelligence` — references integration_diagram, expanded to 38 systems

## Pending for Next Session

- Build Basis Monitoring HTML companion from sap_system_monitor.py
- System inventory needs .NET apps + SuccessFactors cards
- RFC analysis needs tab 6 "RFC API Surface" with 334 FMs by domain
- FI maintenance companion will evolve with support tickets
- Future: FI Support Agent skill that orchestrates companions + brain + Gold DB
