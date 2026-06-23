---
name: U_USAGE — Execution & Usage Footprint (the AS-RUN object-usage discovery dimension)
description: The 11th capability dimension (added 2026-06-23 on user directive). Per domain — WHAT objects actually execute, WHO runs them, by which CHANNEL (dialog/batch/RFC-BAPI/BDC), WHEN, and at what VOLUME. The AS-RUN usage layer that bridges B_CODE (static) → A_PROCESS (flow) → E_AUTH (authorization).
type: project
---

# U_USAGE — Execution & Usage Footprint

> **Dimension #11 of the Capability Model (Layer 15).** Added 2026-06-23. User directive:
> "por cada dominio todo lo que se usa, quién lo usa, cómo lo usa y cuándo. Y el volumen … otra
> dimensión del process discovery, dale un nombre y un método … debe ser un item en la madurez."

## The question it answers
For a domain: **WHAT** objects actually execute · **WHO** runs them · **HOW** (which channel) ·
**WHEN** (time profile) · **how much** (VOLUME). The static catalog (TSTC/TFDIR) says what *can* run;
U_USAGE is the **AS-RUN reality** — what *does* run, by whom, and how often.

## Why it's a distinct dimension (not B_CODE / A_PROCESS / E_AUTH)
| Dim | Layer | What it captures |
|---|---|---|
| **B_CODE** | static | which programs/classes/exits/BDC *exist* |
| **A_PROCESS** | flow | the *sequence*/variants (DFG, OCEL) of a process |
| **E_AUTH** | potential | who *can* execute (roles, SoD) |
| **U_USAGE** | **actual** | who **actually** executes **what**, via which **channel**, **when**, **how much** |

U_USAGE is the bridge from static inventory → live reality. The **dead-vs-used** signal it produces
also feeds **R_S4_READINESS** (used-to-migrate vs dead-to-delete; 40-60% of custom code is typically dead).

## The method (4 execution channels → one census)
Source = the execution-evidence logs already in the Gold DB. For each object, attribute the channel:

| Channel | Source table | Object field | Actor |
|---|---|---|---|
| **dialog** (user tcode) | `rsau_audit_history` `TXSUBCLSID='Transaction Start'` | `PARAM1` (tcode) | `SLGUSER` |
| **report run** | `rsau_audit_history` `TXSUBCLSID='Report Start'` | `SLGREPNA` (program) | `SLGUSER` |
| **RFC / BAPI call** | `rsau_audit_history` `TXSUBCLSID='RFC Function Call'` | `PARAM3` (function) | `SLGUSER` (caller) |
| **batch job** | `tbtco`/`tbtcp` | `PROGNAME` (+`VARIANT`) | `JOBNAME`/`AUTHCKNAM` |
| **batch input (BDC)** | `apqi`/`apqd` (SM35) | program | session creator |

Per object the census records: `exec_count` (volume), `distinct_users`, `top_users`, channel(s), and
(extendable) time profile from `SAL_DATE`/`SAL_TIME`. Then **cross-reference the static catalog**
(`d01_tstc`, `tfdir_custom`) to split **EXECUTED vs CATALOG-ONLY** — the coverage truth.

**Builder:** `process_mining/fm_executed_census.py` (proven on PSM_FM). Generalize per domain by swapping
the object-name filter (`FM_RE`) for the domain's object patterns (or drive it from the domain's
`B_CODE` object set). Output: `brain_v2/<domain>_executed_census.json`.

> NOTE on the data window: `rsau_audit_history` = SM20/RSAU, a **~4-month** rolling window (P01
> 2026-02-21…06-21, 15.6M rows). So U_USAGE volume is "last ~4 months", not all-time — state the window.

## ⚠️ Object ↔ Process is MANY-TO-MANY (do not bake 1:1)
A transaction/report/FM is a **shared primitive** — the SAME object participates in **multiple
processes** (user directive 2026-06-23: "una transacción puede ser usada en múltiples procesos").
Example: `FMX3` (fund reservation) is used in budget-execution **and** project/grant funding **and**
closing/carryforward. Therefore:
- The census stores `object → processes` as a **SET**, never a single label. A `sub_area`/primary tag is
  a convenience, NOT an exclusive classification.
- **Volume must be split by process** when attributing — an object's 16k executions span N processes;
  the per-process share needs the context join below, not the raw object total.
- **How we discover the M:N** (the "cómo lo usa" axis = object × process × variant × actor):
  1. **U_USAGE × A_PROCESS** — the same object appears in multiple event-log variants/DFGs; each variant
     is a different process context.
  2. **DATA context** — what the execution touches (fund / WBS / grant / commitment item / doc type)
     determines which process it served (e.g. FMX3 against a project-WBS = project funding; against a
     budget object = budget execution).
  3. **ACTOR/role context** — the caller's role + channel narrows the process (MULESOFT C/5 sync vs a
     human reserving against a grant).
- Corollary for the deep-dive: each object card carries `processes[]` (a set), and the high-volume shared
  primitives (FMX1/2/3, FM5S, the YPS/YFM reports) get an explicit multi-process membership pass.

## Maturity scoring (per domain)
- **NONE** — no census built.
- **PARTIAL** — one channel only, or counts without actor/volume.
- **HAVE** — all available channels fused, with actor + volume (+ time), and executed-vs-catalog coverage.

Scored generically by `brain_v2/capability_model/maturity_score.py` (iterates `dimensions`). U_USAGE is
in `EXTRACTION_DIMS` (built from extracted logs). **Baseline 2026-06-23: U_USAGE = 6.7%** (PSM_FM=HAVE,
all other 14 domains = NONE). Building it per domain is the backlog (PMO).

## Status
- **PSM_FM = HAVE** — census `brain_v2/fm_executed_census.json` (322 tcodes, 114 reports, RFC/BAPI, batch).
- All other domains = NONE → backlog (one census per domain; the method is identical, only the filter changes).
- Next per object: the **deep dive** (what it does, who owns it, dead/used, S/4 disposition) — U_USAGE gives the prioritized, volume-ranked worklist.
