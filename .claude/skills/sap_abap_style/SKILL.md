---
name: UNESCO ABAP Style & Structure
description: >
  MANDATORY companion skill for any ABAP EXECUTION (create/modify/deploy code) or
  ANALYSIS (review/reverse-engineer/explain custom code) task. Applies the UNESCO
  ABAP standards codified from N_MENARD's reference codebase (740-object D01 scan,
  SEO anatomy census of 188 classes) + the CRP disaster catalogue. Defines how to
  structure classes/methods, name objects, shape signatures, and which template-method
  family a new piece of code belongs to. Invoke BEFORE writing the first line of ABAP
  and use its checklists BEFORE any deploy.
domains:
  functional: [Any]
  module: [BC, Any]
  process: [Development, Code Review, Deployment]
tier: project
maturity: production
origin_session: 81
last_updated_session: 81
triggers:
  - create ABAP class / report / FM / table
  - deploy ABAP
  - write ABAP code
  - ABAP code review
  - reverse engineer custom code
  - how should this class be structured
  - naming convention ABAP
  - new workflow type / notification / config catalog
  - style guide
  - N_MENARD pattern
subtopics:
  - class_method_anatomy
  - naming_conventions
  - template_method_families
  - disaster_catalogue
  - pre_deploy_checklist
---

# UNESCO ABAP Style & Structure

## When to Use This Skill (mandatory, not optional)

| Task type | Moment to invoke |
|---|---|
| **EXECUTION** — create/modify a class, report, FM, DDIC object; any ADT/abapGit/DDIF deploy | BEFORE writing code: pick the archetype + structure. BEFORE deploy: run the checklist. |
| **ANALYSIS** — code review, incident code-trace, reverse engineering, "explain this Z/Y object" | At the start: judge the object AGAINST the reference anatomy; report deviations as findings. |

If an agent writes or reviews ABAP in this project without loading this skill, that is a
process violation (same class as skipping the brain read).

## Knowledge base (read in this order)

1. `knowledge/abap-style-guide/UNESCO-ABAP-STYLE-GUIDE.md` — per-object-type rules (15 sections
   + 5 "Extended patterns (from full D01 scan)" subsections). §13 = disaster catalogue (NEVER repeat).
2. `knowledge/abap-style-guide/N_MENARD-CLASS-ANATOMY.md` — how to structure classes/methods
   (measured): size ~5 methods, visibility doctrine, empty-hook bases (no ABSTRACT), MR_/MP_
   selection binding, verb taxonomy, signature rules, the prescriptive 8-step synthesis (§8).
3. `knowledge/abap-style-guide/N_MENARD-OBJECT-INVENTORY.md` — what exists (740 objects) and the
   object kits per archetype.

## Decision protocol for EXECUTION

1. **Archetype first** — which kit is this? New WF type / notification event / validation check /
   config catalog / ALV report / bridge FM / OData extension. The kit dictates the object list
   (inventory doc + style guide extension sections). New standalone hierarchies need justification.
2. **Clone the golden exemplar**, never start blank: sources in `extracted_code/HCM/YHR_PA_WF/`,
   `extracted_code/CUSTOM/Y_CA_FRAMEWORKS/`, `unescrp/artifacts/reference/nmenard/` (READ-ONLY).
3. **Structure per anatomy §8**: public = orchestrators/contract only; protected = empty hooks +
   family state; private = one-job verb-named helpers; leaves FINAL; `super->` first; ≤3 params,
   RETURNING over CHANGING; typed RAISING from the shared YCX_* set.
4. **Catalog rows before code**: if behavior can be a row in YTHRWF_TYPE-style config + a dynamic
   `CREATE OBJECT TYPE (name)`, do NOT write a CASE/IF.
5. **Pre-deploy checklist**: §13 disaster scan (LIKE vs TYPE, EXT-struct superset, em-dashes,
   TR family, lock/unlock in finally, activation body check) + §14 pipeline rules + LF-only encoding.
   D01 only for new objects (never P01). Never touch SAP-standard objects.

## Verification (objects are data)

- Anatomy claims are queryable: Gold DB `d01_seo_classdf/compo/compodf/subcodf/metarel/redef`
  (e.g. "what must I redefine?" → `SELECT MTDNAME FROM d01_seo_redef WHERE REFCLSNAME='<base>'`).
- Kit completeness: `d01_tadir_yhr_pa_wf` / `d01_tadir_nmenard` / `d01_tfdir_nmenard_fugr`.
- After deploy: ADT readback + (for classes) re-extract SEO rows and diff structure.

## Known kernel constraints (do not re-discover)

- EhP8 D01: DDIC via `DDIF_*` RFC, not ADT (`/ddic/tables` 404s). ADT = source code only.
- `RFC_READ_TABLE` on D01/P01: no ROWSKIPS pagination — one `ROWCOUNT=0` call.
- Deploy priority: abapGit → ADT REST → DDIF wrapper → RFC/Playwright (rule
  `feedback_abapgit_is_the_standard_when_installed`).
