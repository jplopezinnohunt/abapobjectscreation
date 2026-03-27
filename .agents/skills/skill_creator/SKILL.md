---
name: Skill Creator (Anthropic Framework)
description: >
  Meta-skill for CREATING, IMPROVING, and EVALUATING new agent skills.
  Applies Anthropic's Constitutional AI and prompt engineering best practices
  to produce effective, testable, and maintainable SKILL.md files for this project.
  Use this skill before writing any new SKILL.md, or when improving an existing one.
---

# Skill Creator — Anthropic Framework

## When To Create a New Skill

Create a SKILL.md when **the agent does the same complex, multi-step task repeatedly** and you want to:
- Guarantee consistency across sessions
- Share institutional knowledge (confirmed endpoints, working auth, known gotchas)
- Reduce trial-and-error by encoding what has been learned

**Do NOT create a skill** for one-off tasks, or things fully coverable in a single prompt.

---

## Anthropic Design Principles Applied Here

These come from Anthropic's research on effective AI prompting and Constitutional AI:

### 1. Be Specific, Not Generic
```
BAD:  "Connect to SAP"
GOOD: "Connect to D01 with HTTP Basic to HQ-SAP-D01.HQ.INT.UNESCO.ORG:80
       or to P01 with SNC/SSO (p:CN=P01) — never use password for P01"
```

### 2. Encode Hard-Won Knowledge (Tribal Knowledge Capture)
Every skill should answer: *"What would a junior dev get wrong on their first try?"*
- Known broken endpoints
- Auth order (CSRF before write)
- Windows encoding pitfalls
- SAP release quirks

### 3. Define Success Criteria
Each skill must state: *"You know this worked when..."*
- HTTP 200 / specific response format
- File created at exact path
- SAP transaction shows the result

### 4. Provide Examples (Few-Shot Pattern)
Concrete examples beat abstract descriptions every time:
```python
# Good example in a skill:
result = client.get_source('/sap/bc/adt/oo/classes/ZCL_HR_FIORI_REQUEST')
# Expected: ABAP source starting with "CLASS ZCL_HR_FIORI_REQUEST..."
```

### 5. State Constraints First
Put **what NOT to do** before **what to do** when constraints are safety-critical:
```
NEVER write directly to P01. Always go D01 → CTS → P01.
NEVER store passwords in code. Use .env with SAP_PASSWORD=
```

### 6. Self-Healing Instructions
Tell the agent how to diagnose failures:
```
If HTTP 403 → CSRF token missing, call fetch_csrf() first
If RFC error "NOT_FOUND" → object doesn't exist in that client
If SNC error → check SAP_SNC_PARTNERNAME matches SM59 configuration
```

---

## SKILL.md Template

Use this exact structure when creating a new skill:

```markdown
---
name: [Short skill name]
description: >
  [1-2 sentence description. When should the agent USE this skill?]
---

# [Skill Name]

## Prerequisites
- [Tool / library / connection already working]
- [Env var or config required]

## NEVER Do This
> [!CAUTION]
> [The most dangerous mistake for this skill]

## Step-by-Step

### Step 1: [Action]
[Exact code or command]
[Expected output]

### Step 2: [Action]
...

## You Know It Worked When
- [Observable success signal 1]
- [Observable success signal 2]

## Known Failures & Self-Healing
| Error | Cause | Fix |
|-------|-------|-----|
| [message] | [why] | [exact fix] |

## Examples
[Working, tested code snippet]
```

---

## Skill Quality Checklist

Before saving a SKILL.md, verify:

- [ ] **Specific**: Contains exact URLs, field names, command flags (not "use the API")
- [ ] **Example-driven**: At least one working code/command example
- [ ] **Failure-aware**: Documents at least 2 known failure modes with fixes
- [ ] **Success-defined**: States exactly what "done correctly" looks like
- [ ] **Constraint-first**: Safety rules appear before instructions
- [ ] **Tribal knowledge**: Encodes at least one non-obvious thing learned from experience
- [ ] **Tested**: Was validated against the real system (not theoretical)

---

## This Project's Skill Hierarchy (33 Skills — Session #022)

**Orchestration**
- `coordinator` — Master router (B2R/H2R/P2P/T2R/P2D), model routing, brain query
- `skill_creator` — THIS SKILL: meta-skill for creating/evaluating skills

**Domain Agents**
- `psm_domain_agent` — FM/budget/fund management
- `hcm_domain_agent` — HR lifecycle, infotypes, payroll, Fiori
- `fi_domain_agent` — GL, validations, substitutions, FM-FI bridge
- `sap_payment_bcm_agent` — F110/BCM/DMEE/SWIFT/FBZP chain, full payment domain
- `sap_payment_e2e` — Payment process mining, E2E cycle times, FBZP validation

**Data & Extraction**
- `sap_data_extraction` — RFC extraction pipeline, Gold DB (24M+ rows, 42 tables)
- `sap_adt_api` — ADT REST API: read/write/activate 14 ABAP object types

**Intelligence & Analysis**
- `sap_transport_intelligence` — CTS forensics, 7,745 transports, risk taxonomy
- `sap_transport_companion` — Interactive HTML companion builder for transport contents
- `sap_company_code_copy` — EC01 copy: 41-task checklist, FBZP chain, 6 validations
- `sap_reverse_engineering` — OData service logic extraction, 5-phase protocol
- `sap_enhancement_extraction` — BAdI/Enhancement mining
- `sap_system_monitor` — SM04/SM35/SM37/ST22 operational dashboard
- `sap_bdc_intelligence` — Batch input forensics (Allos vs Y1 payroll)
- `sap_job_intelligence` — SM37 deep analysis, 228 programs/18 domains
- `sap_interface_intelligence` — 239 RFC destinations, 19 systems, 19.4K IDocs
- `sap_process_mining` — pm4py engine, 8 CLI commands, CTS/FM/P2P mining
- `sap_change_audit` — CDHDR/CDPOS 7.8M rows, 100+ TCODE mappings

**Development & Deployment**
- `sap_class_deployment` — ABAP class creation via RFC/ADT, 6 CCIMP strategies
- `sap_fiori_tools` — Fiori CLI, manifest editing, BSP extraction
- `sap_fiori_extension_architecture` — Extension discovery, BAdI vs ENHO vs clone
- `sap_segw` — SEGW OData builder (merged with segw_automation)
- `sap_webgui` — Playwright browser automation (103 experiments, Select-Then-Toolbar)
- `sap_native_desktop` — SAP GUI Scripting fallback (win32com)

**Infrastructure**
- `sap_expert_core` — Deep SAP knowledge (FI/PSM/ABAP/Workflow/OData)
- `sap_debugging_and_healing` — Triple Threat: ST22 + SU53 + SM21
- `sap_automated_testing` — OData HTTP validation
- `abapgit_integration` — abapGit CI/CD workflow
- `parallel_html_build` — vis.js dashboard generation
- `unesco_filter_registry` — UNESCO-specific ABAP filter patterns
- `notion_integration` — Notion API integration
- `crp_fiori_app` — CRP architecture, 3-stream posting, 19 open items

### When to Use Which Skill

| Task | Skill |
|------|-------|
| F110/BCM/payment question | `sap_payment_bcm_agent` |
| Payment process mining / cycle times | `sap_payment_e2e` |
| Read/write ABAP source code | `sap_adt_api` |
| Monitor P01 production data | `sap_system_monitor` |
| Build new OData service | `sap_segw` |
| Modify Fiori app UI | `sap_fiori_tools` |
| Automate SAP via browser | `sap_webgui` |
| Something fails unexpectedly | `sap_debugging_and_healing` |
| Need to understand existing code | `sap_reverse_engineering` |
| Creating a new skill | THIS SKILL |

---

## Growing a Skill Over Time

Skills are **living documents**. After each session:

1. **Add to "Known Failures"** any new error you encountered and fixed
2. **Update examples** with better, more realistic code
3. **Expand tribal knowledge** with anything non-obvious discovered
4. **Add endpoint** if a new ADT/RFC endpoint was confirmed working

This is how the agent gets smarter over sessions — not just from conversation history, but from **encoded, structured knowledge** that survives conversation resets.

---

## Maturity Framework (Session #018)

Every new SKILL.md should target a maturity level. See `.agents/SKILL_MATURITY.md` for the full rubric.

| Score | Label | When to create at this level |
|-------|-------|------------------------------|
| 4 | Production | Only after real session usage + comprehensive docs |
| 3 | Functional | Working skill, tested in at least 1 session |
| 2 | Draft | Framework defined, not yet validated |
| 1 | Stub | Placeholder for future work — avoid creating these |

**Rule:** Don't create Stub skills. If you can't write at least Draft-level content, the skill isn't ready to exist yet.

---

## Session Retrospective Protocol

At end of each session, run `/session_retro` and ask:
1. What new thing did I learn that isn't in any skill yet?
2. Which skill would have helped me avoid the biggest mistake?
3. Did I discover a new API endpoint, table, or RFC that should be documented?
4. Is there a pattern I repeated 3+ times that should become a skill?
