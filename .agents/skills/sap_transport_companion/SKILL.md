---
name: SAP Transport Companion Builder
description: >
  Generates interactive HTML companion pages that explain SAP transport order contents
  in user-friendly language. Reads E070/E071/E071K via RFC, classifies every object using
  the 21-module Transport Intelligence taxonomy, runs automated validations, and produces
  a self-contained HTML report with executive summary, risk assessment, and action items.
  Use this skill when someone needs to understand what a transport contains and what it does.
maturity: production
origin: Session #019 — built for D01K9B0CBF (company code copy analysis)
depends_on: sap_transport_intelligence, sap_company_code_copy
---

# SAP Transport Companion Builder Skill

> **Source authority**: Transport Intelligence 21-module knowledge base + live RFC validation.
> First companion built Session #019 (2026-03-26) for company code copy transport D01K9B0CBF.

---

## When to Use This Skill

- User provides transport order numbers and wants to understand the content
- Pre-import review requiring user-friendly explanation (not just raw E071 list)
- Documenting what a transport does for audit, handover, or training
- Any time someone says "explain this transport" or "what's in this order"

---

## How It Works

### Step 1 — Extract Transport Content

```python
# Connect to SAP via RFC (D01 or P01)
# Read E070 (header), E07T (description), E071 (objects), E071K (keys)
# Script: transport_adhoc_read.py
```

- E070: TRKORR, TRFUNCTION (K/W/T), TRSTATUS, AS4USER, AS4DATE, STRKORR
- E071: PGMID, OBJECT, OBJ_NAME, OBJFUNC, LOCKFLAG
- E071K: TABKEY (actual row keys for TABU objects)
- E07T: AS4TEXT (description) — note: E070T may not be readable, use E07T

### Step 2 — Classify Every Object

Use `knowledge/domains/Transport_Intelligence/transport_object_taxonomy.md` to classify:

| Classification | Source |
|---------------|--------|
| Functional area (FI, CO, MM, HR, etc.) | Table name → module mapping |
| Risk level (CRITICAL/HIGH/MEDIUM/LOW) | Object type + OBJFUNC |
| SAP artifact vs real config | TDAT/VDAT/CDAT = artifact, ADR* = artifact |
| ALARM detection | T001B, PROJ, PRPS, SWWWIHEAD, MHND, RBKP_BLOCKED, VICNCN |

### Step 3 — Explain User-Friendly

For every object, produce:
- **What this does** — plain language, not SAP jargon
- **Why it matters** — business impact
- **What fails without it** — concrete scenario
- **Risk if wrong** — what happens on bad import

### Step 3b — Multi-Transport Handling

When multiple transports form a logical package (e.g., FI + FM for company code creation):
- **Detect table conflicts** — find tables modified by multiple transports (e.g., T001, T882)
- **Determine import order** — FI before FM, FM before CO, etc.
- **Flag duplicates** — address data (ADR*) often duplicated across transports (harmless)
- **Generate import order diagram** — visual flow showing STEP 1 → STEP 2 → manual tasks
- **Re-read transports** — user may update transport content during the session. Always offer to re-extract.

### Step 4 — Run Automated Validations

Depending on transport type, run relevant checks:
- **Company code copy**: GL recon (SKA1↔SKB1), FBZP chain (6 levels), country match (T001.LAND1 vs T042E), NR gaps (NRIV comparison), bank accounts (T012K.BANKN empty?), T001A group currency
- **Workbench (K)**: XPRA check, FUGR overwrite risk, NROB presence
- **General**: OBJFUNC D/M detection, ALARM objects, cross-module patterns
- **Multi-transport**: table conflict detection, import order validation

### Step 5 — Generate HTML Companion

Self-contained HTML with:
- Dark theme, responsive, no external dependencies
- Collapsible sections for large tables
- Color-coded risk badges
- Flow diagrams for dependency chains (FBZP, account determination)
- Pass/fail validation results
- Actionable checklist with SAP transaction codes

---

## Template Structure

```
1. Header (transport IDs, type, owners, date, target, status)
2. Executive Summary (what does this transport package do, in plain language)
3. [If multi-transport] Import Order section with flow diagram + conflict table
4. Summary Cards (object count, key count, risk distribution, transport count)
5. Pre-Import Safety Checklist (covers ALL transports — 10 standard checks)
6. Functional Area Sections (one per area, with table + explanation)
   - Mark which transport each section comes from (color-coded border)
7. Complete Object Inventory (collapsible per transport, all objects classified)
8. Post-Import Actions (automated validation results + manual tasks table)
9. [If copy] Number Range gap table (OBH2 — compare against reference co code)
10. [If copy] Open Posting Periods checklist (FI/FM/CO/PS/AA with TCode)
11. [If copy] Complete 41-task manual checklist by module
12. [If copy] Copy Risk Validation + Inconsistency Analysis
13. [If copy] FBZP Chain Diagram (6 levels, OK/MISSING status)
14. [If copy] Mitigation Plan (prioritized fixes)
15. Footer (source, date, methodology, skills used)
```

---

## Key References

| Reference | Location |
|-----------|----------|
| Transport Object Taxonomy | `knowledge/domains/Transport_Intelligence/transport_object_taxonomy.md` |
| Company Code Copy Skill | `.agents/skills/sap_company_code_copy/SKILL.md` |
| Transport Intelligence Skill | `.agents/skills/sap_transport_intelligence/SKILL.md` |
| RFC extraction script | `Zagentexecution/mcp-backend-server-python/transport_adhoc_read.py` |
| Bank validation script | `Zagentexecution/mcp-backend-server-python/transport_bank_validate.py` |
| Example companion | `Zagentexecution/transport_companion_D01K9B0CBF.html` |

---

## Automation Scripts

| Script | Purpose |
|--------|---------|
| `transport_adhoc_read.py` | Reads E070 + E071 + E071K for specific transport orders, outputs JSON |
| `transport_bank_validate.py` | 6-check validation for bank/payment config (GL recon, FBZP chain, country, bank accounts) |
| `transport_bank_detail.py` | Reads actual config values (T012K, T042, T042E, etc.) for deep analysis |

---

## HTML Style Guide

- Background: `#0f172a` (dark navy)
- Surface: `#1e293b`
- Accent: `#38bdf8` (sky blue)
- Risk colors: red (#f87171), orange (#fb923c), yellow (#fbbf24), green (#4ade80)
- Font: Segoe UI / system-ui, monospace for technical values
- All CSS/JS inline — no external CDN (VSCode blocks CDNs)
- Area tags: colored pills per module (FI=blue, CO=green, MM=yellow, AA=orange, BANK=purple)
