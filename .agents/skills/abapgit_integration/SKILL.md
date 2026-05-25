---
name: abapGit Integration (redirect)
description: Thin redirect — abapGit capabilities are now integrated into the unified sap_adt_api skill (§16-§25). Read sap_adt_api/SKILL.md instead. This file exists only for projects that load the skill by the old name.
domains:
  functional: [*]
  module: [CTS, CUSTOM, BASIS]
  process: []
---

# abapGit Integration — MERGED INTO `sap_adt_api`

> [!IMPORTANT]
> **This skill has been merged into [`sap_adt_api/SKILL.md`](../sap_adt_api/SKILL.md) as §16-§25 (Session #76).**
>
> Read that skill — it now contains:
> - Full abapGit capability inventory (170+ object types) — §17
> - Decision matrix: when to use abapGit vs DDIF wrapper vs ADT REST vs RFC alternatives — §18
> - Install playbook + BASIS ticket draft — §19
> - Workflows: offline ZIP, RFC-headless, push/pull, branch switch — §20
> - Serialization format spec (`.abapgit.xml`, `.tabl.xml`, etc.) — §21
> - TADIR/CTS handling + EDTFLAG lesson — §22
> - Limitations + gotchas — §23
> - Python integration patterns + worked examples — §24
> - References (abapGit source, docs, SAP Notes) — §25
>
> **One skill, all deployment capabilities (ADT REST + DDIF wrapper + abapGit + RFC alternatives).** Used by abapobjectscreation, unescrp, and any UNESCO SAP project deploying Z code.

## Why merged

Earlier this skill was Playwright-UI-only (33 lines, only covered ZABAPGIT-transaction stage/commit). Session #76 added full abapGit mastery (~700 lines) but cross-project users were already loading `sap_adt_api` by name — needing them to discover and load a second skill split the knowledge unnecessarily. Decision: ONE skill, all capabilities, name stays `sap_adt_api`.

## Status quick reference (full status in sap_adt_api §16 + §19)

- **abapGit on D01**: ✅ **STANDALONE INSTALLED 2026-05-25** — `ZABAPGIT_STANDALONE` (PROG, `$TMP`, REPOSRC `r3state=A`, 151,660 lines, source verified by `READ REPORT`). Installed via workstation-bridge: workstation fetched `raw.githubusercontent.com/abapGit/build/main/zabapgit_standalone.prog.abap` (4.86 MB) and pushed via RFC `RPY_PROGRAM_INSERT` (`SOURCE_EXTENDED` ABAPTXT255). **NO BASIS ticket. NO STRUST. NO SICF changes.**
- **Use cases unblocked NOW** (human-driven via SAPGUI SE38 → `ZABAPGIT_STANDALONE`): create/maintain ANY of the 170+ object types abapGit supports — TABL, DTEL, DOMA, CLAS, INTF, FUGR/FUNC, PROG, INCLUDE, ENHO, MSAG, WAPA (BSP), IWSV/IWSG (OData), XSLT, NROB, WDYN, SUSO, AGR, etc.
- **Still pending** (for agent-driven RFC class-level API): dev edition install (~1000 `ZCL_ABAPGIT_*` objects) via offline-ZIP path through the running standalone. No BASIS needed for that either — same workstation-bridge architecture. See `sap_adt_api/SKILL.md` §19.2 for the playbook.
- **DDIF wrapper on D01**: ✅ Still works (verified end-to-end with ZADTPYTST DE + ZADTPYTBL/ZADTPYTB2 tables; EDTFLAG bug fixed, all SE11-editable). Use it for single-object DDIC where opening SAPGUI for abapGit UI is heavier than the wrapper.
- **ADT REST on D01**: ✅ Working for source code on most types; ❌ DDIC creation absent on EhP8 (NW 7.50+); ❌ source PUT for `$TMP` PROGs broken (lock semantics) — `RPY_PROGRAM_INSERT` is the working RFC path for PROG source uploads.

## What this unblocks for OTHER UNESCO SAP projects

Any project deploying or maintaining Z objects on D01 can now:

| Task | Tool today | Why abapGit is better |
|---|---|---|
| Create / modify a single Z table | DDIF wrapper (still fine) OR SE38 `ZABAPGIT_STANDALONE` → import a `.tabl.xml` from local | abapGit: full version history of structure changes, atomic with other dependent objects |
| Atomic deploy of 5+ DDIC objects (table + DE + domain + index + structure) | N× DDIF calls — lose atomicity if one fails mid-way | abapGit: 1 ZIP / 1 TR, all-or-nothing |
| Deploy a Z class with CCIMP/CCDEF/CCAU subincludes | ADT REST `set_class_include_source` (works but multi-step) | abapGit: single `.clas.abap` + auto-handling of all sub-includes |
| Deploy a FUGR with N FMs in one shot | ADT REST `write_function_source` (FG must exist; FMs sequential) | abapGit: FUGR + all FMs + all includes in one pull |
| Move a Z package from workstation → D01 (cross-system sync) | Manual SE38 re-keying, or copy through STMS forward | abapGit: ZIP via local Git, pull on D01 |
| Disaster recovery — rebuild Z package from external source | None (manual) | abapGit: offline ZIP import |
| Compare local source vs D01 active version (diff before push) | None | abapGit: built-in diff UI |
| Version control of Z code with PR-based review | None | abapGit + local Git (workstation handles GitHub side) |

**Important rule that remains in force:** only `Z*/Y*/customer-namespace` objects ever. abapGit can technically pull SAP-standard objects but UNESCO policy + [[feedback-never-modify-standard-objects]] forbids it. Pull only Z packages.

## How to use it in your project

1. Open SAPGUI → SE38 → `ZABAPGIT_STANDALONE` → F8.
2. abapGit UI opens. From there: "New Offline" repo, point at your Z package, import/export ZIPs.
3. For Git lifecycle: workstation has the GitHub clone; SAP only ever sees ZIPs. (Workstation-bridge architecture.)
4. For programmatic / Python-driven operations: wait for dev edition install (sap_adt_api §19.2) — it's the next step.

## Critical rules (full text in sap_adt_api §0)

- 🛑 NEVER modify standard SAP objects (anything not Z*/Y*/customer-ns) — [[feedback-never-modify-standard-objects]]
- 🛑 New object work = D01 only — [[feedback-new-objects-only-in-d01-never-p01]]
- 🛑 ADT-FIRST is qualified by kernel — [[feedback-adt-first-no-abap-program-generators]]
- 🛑 Verify capability before recommending — [[feedback-verify-capabilities-before-recommending]]
- 🛑 No menus when decision is clear — [[feedback-no-menus-when-decision-is-clear]]

---

**For everything else, see `sap_adt_api/SKILL.md`.**
