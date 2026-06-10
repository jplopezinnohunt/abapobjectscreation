# ABAP Style Guide — Index

**Location:** `knowledge/abap-style-guide/`
**Project:** abapobjectscreation
**Created:** 2026-06-10

---

## Purpose

This style guide defines UNESCO SAP ABAP programming standards for all new development on the HQ SAP ECC 6.0 EhP8 system (D01, client 350). It combines:

1. Patterns extracted from Nicolas Menard's `YHR_PA_WF` package — the internal UNESCO reference for well-structured ABAP workflow objects.
2. Anti-patterns from the CRP project's 116-session history — four categories of failures that recurred and cost significant debugging time.

Use this guide when creating any new ABAP object for a UNESCO SAP project, or when reviewing existing objects for refactoring.

---

## Scope

| Dimension | Value |
|---|---|
| SAP system | HQ-SAP-D01, client 350 |
| Release | ECC 6.0 EhP8 |
| Namespaces | `Z*` (custom objects), `Y*` (HR-team reference) |
| Reference package | `YHR_PA_WF` (Nicolas Menard) |
| CRP package | `ZHR_CRP` |
| Deploy method | ADT REST API via Python scripts |

---

## Files

| File | Description |
|---|---|
| `UNESCO-ABAP-STYLE-GUIDE.md` | Main style guide — all object types, patterns, anti-patterns |
| `N_MENARD-OBJECT-INVENTORY.md` | Complete D01 catalog of package `YHR_PA_WF` (740 objects) + N_MENARD's 3,463 objects across 33 packages (s081 scan) |
| `N_MENARD-CLASS-ANATOMY.md` | How Nicolas structures classes/methods — measured from SEO catalog (188 classes, 7,451 components, 7,954 params): size, visibility doctrine, empty-hook bases, MR_/MP_ binding contract, verb taxonomy, signature rules |
| `README.md` | This file — index and how-to-use |

---

## Agent invocation

This knowledge is wired to the agent skill **`.agents/skills/sap_abap_style/SKILL.md`** — it MUST be
invoked for any ABAP **execution** (create/modify/deploy) or **analysis** (review/reverse-engineering)
task, before the first line of code and before any deploy.

## How to Use This Guide

### For new object creation

1. Identify the object type you need (class, interface, exception, BOR method, FM, report, DDIC).
2. Go to the corresponding section in `UNESCO-ABAP-STYLE-GUIDE.md`.
3. Copy the structure template for that object type.
4. Apply the naming conventions from §1.1.
5. Check §13 (anti-patterns) for traps specific to your object type.

### For code review

1. Verify naming prefixes match §1.1.
2. Verify the class section ordering follows §2.2 (PUBLIC → PROTECTED → PRIVATE).
3. Check for the 10 N_MENARD patterns (listed below).
4. Check the 4 failure categories in §13 — especially type system (Category B) and deploy pipeline (Category C) issues.

### For OData / DPC_EXT work

Read §15 entirely before touching any `*_MPC_EXT` or `*_DPC_EXT` class. The EXT struct superset rule (§15.2) and the et_entityset write patterns (§15.3) have each caused multi-session bugs.

---

## The 10 N_MENARD Patterns (Quick Reference)

| # | Pattern | Where in guide |
|---|---|---|
| 1 | Factory + Singleton + dynamic instantiation from catalog | §6 |
| 2 | Interface-first contract — callers only see the interface | §7 |
| 3 | Catalog-driven step navigation — no hardcoded CASE | §6, §13-A2 |
| 4 | Typed exception class with TEXTID constants | §8 |
| 5 | Lazy instance-level caching (`IF mt_xxx IS INITIAL`) | §2.2, §13-A5 |
| 6 | Container via SWC macros (`INCLUDE <cntain>`) | §9.4 |
| 7 | History + reason tracking (TAB_HIS_STEP append on every step) | §9.3 |
| 8 | Static utilities class — all `CLASS-METHODS`, no instance state | §5 |
| 9 | Sort + dedup every actor result table | §1.6 |
| 10 | Test-system shortcut via `IS_TEST_SYSTEM()` check | §5 |

---

## Source Material

The style guide was written from direct ADT readback of 18 objects in package `YHR_PA_WF`, extracted during CRP sessions S-63 and S-72:

- `YIF_HRWF_MAIN.intf.abap` — main workflow interface
- `YIF_HRWF_ACTORS.intf.abap` — actors interface
- `YCL_HRWF_FACTORY.clas.abap` — factory/singleton
- `YCL_HRWF_MAIN.clas.abap` — abstract base (main)
- `YCL_HRWF_ACTORS.clas.abap` — abstract base (actors)
- `YCL_HRWF_MAIN_S1.clas.abap` — concrete subclass (separation WF)
- `YCL_HRWF_MAIN_I1.clas.abap` — concrete subclass (intern WF)
- `YCL_HRWF_MAIN_LX.clas.abap` — concrete subclass (LWOP WF)
- `YCL_HRWF_MAIN_PX.clas.abap` — concrete subclass (SPA WF)
- `YCL_HRWF_ACTORS_S1.clas.abap` — concrete actors (separation WF)
- `YCL_HRWF_ACTORS_I1.clas.abap` — concrete actors (intern WF)
- `YCL_HRWF_ACTORS_LX.clas.abap` — concrete actors (LWOP WF)
- `YCL_HRWF_OPERATION.clas.abap` — WF operation (cancel/complete)
- `YCL_WF_UTILITIES.clas.abap` — static WF utilities
- `YCL_CA_UTILITIES.clas.abap` — static cross-application utilities
- `YCL_HR_WF_MAIL_FACTORY.clas.abap` — mail notification factory
- `YBUS1065.bor.abap` — BOR object (YBUS1065, subtype of BUS1065)
- `Y_HRPAWF_NEXT_ACTOR.abap` — FM for SWDD actor resolution

All source files are read-only references stored at:
`c:\Users\jp_lopez\projects\unescrp\artifacts\reference\nmenard\`

---

## Full D01 scan extension (2026-06-10, session #081)

The complete package was inventoried from D01 (read-only: RFC `TADIR`/`TFDIR` + ADT GET) —
see `N_MENARD-OBJECT-INVENTORY.md`. Key facts:

- `YHR_PA_WF` holds **740 objects** (41 classes — 19 of them mail classes, 11 interfaces, 37 FUGRs,
  16 programs, 193 tables/structures, 18 WF tasks, 9 WF templates, 9 WDA components, IMG + view
  maintenance for every catalog).
- The framework **spans 4 packages**: `YHR_PA_WF` (PA WF) + `YHR_OM_WF` (mail factory,
  `YCL_WF_UTILITIES`, `YTHRWF_NOTIF`) + `YBC` (`YCL_CA_UTILITIES`) + `ZHR_DEV` (LWOP main class,
  `YCL_HRWF_OPERATION`).
- 8 new objects were deep-read and 4 extension subsections appended to the guide, marked
  **"Extended patterns (from full D01 scan)"**: mail/notification class family (§6), FM roles (§10),
  report-as-thin-shell + `_BL` class (§11), DDIC assignment tables + name-prefix census (§12).
- Readback sources: `Zagentexecution/tasks/2026_06_10_nmenard_inventory/readback/` (abapobjectscreation
  project — the unescrp reference folder was NOT modified).

### New patterns added in s081 (quick reference, continues the v1 table)

| # | Pattern | Where in guide |
|---|---|---|
| 11 | Mail 3-level template-method hierarchy (engine → WF-type → event) | §6 ext |
| 12 | SO10 templates + placeholder container + `<VARIANT>` splice via HR feature | §6 ext |
| 13 | Non-prod email whitelist (`YTBC_MAIL_AUTH`, corrupt non-whitelisted addresses) | §6 ext |
| 14 | FM roles: SAP-contract / class-bridge / generated view-maintenance — nothing else | §10 ext |
| 15 | Report-as-thin-shell: 3-file split + `_BL` class + generic `set_selection_values` | §11 ext |
| 16 | Assignment table shape: both catalog keys + `SEQNR`, `GOABAP` escape-hatch flag | §12 ext |

---

## Maintenance

When a new failure pattern is discovered in any UNESCO SAP project, add it to `§13` of the main guide under the appropriate category (A/B/C/D or a new category E+). Include: what went wrong, how many sessions it cost, and the correct pattern.

When Nicolas Menard adds new objects to `YHR_PA_WF` that demonstrate a pattern not yet covered, extract via ADT readback and add a new section.
