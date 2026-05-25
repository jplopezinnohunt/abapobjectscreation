---
title: abapGit on UNESCO D01 — operational state
status: ACTIVE (standalone only — dev edition NOT installed)
verified_date: 2026-05-25
verified_session: 76
verified_by: jp_lopez + agent
canonical_source: true
reverify_command: python Zagentexecution/mcp-backend-server-python/check_abapgit_installed.py
runtime_check_command: python Zagentexecution/abapgit_install/verify_abapgit_state.py
ui_check_path: SAPGUI -> SE38 -> ZABAPGIT_STANDALONE -> F8
---

# abapGit on UNESCO D01 — what is actually operational

This file is the **single source of truth** for what abapGit on D01 can and cannot do as of 2026-05-25. Other agents and projects should consult this file BEFORE assuming any abapGit capability. Re-run the verification commands at session start; if they disagree with this file, the system has changed — update this file rather than acting on stale assumptions.

## ✅ ACTIVE on D01 (verified runtime, not just static checks)

| Artifact | State | Evidence |
|---|---|---|
| `ZABAPGIT_STANDALONE` PROG in `$TMP` | Active, executable | `R3TR PROG ZABAPGIT_STANDALONE` in TADIR; `SUBC=1` in TRDIR; REPOSRC `r3state='A'`; `READ REPORT ... INTO tab` returns 151,660 lines; first line `REPORT zabapgit_standalone LINE-SIZE 100.` |
| abapGit standalone UI 1.133.0 | Launches via SE38 F8 | User screenshot 2026-05-25: title bar "abapGit standalone bootstrap", nav Repository List / + New Online / + New Offline, footer "1.133.0 - Standalone Version - Win - IE", status `js: OK` |
| Internal config tables | Created on first repo create | `TADIR R3TR ENQU EZABAPGIT` (lock), `TADIR R3TR TABL ZABAPGIT` (repo registry) — both in `$TMP`, AUTHOR=JP_LOPEZ |

**Verification commands** (read-only, copy-paste-runnable from any UNESCO project):
```powershell
# Static TADIR/TRDIR/TDEVC/TFDIR probe — 10 queries, ~5s
python C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python\check_abapgit_installed.py

# Runtime probe — REPOSRC r3state + READ REPORT line count
python C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\abapgit_install\verify_abapgit_state.py

# Active vs inactive version diagnostic (run if SE38 shows confusing state)
python C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\abapgit_install\diag3.py
```

Expected output when healthy: `TADIR ZABAPGIT*=1, TRDIR=1, REPOSRC r3state=A, READ REPORT=151,660 lines, STATE 'I' subrc=4 (no orphan inactive)`.

## ✅ What ANY UNESCO agent / project can do TODAY

All via **SAPGUI** (no BASIS, no STRUST, no SICF, no API client needed):

| Use case | How |
|---|---|
| Create or modify ANY of the 170+ object types abapGit supports (TABL, DTEL, DOMA, TTYP, VIEW, INDX, CLAS, INTF, FUGR/FUNC, PROG, INCLUDE, ENHO, ENHS, MSAG, WAPA/BSP, IWSV/IWSG, XSLT, NROB, WDYN, SUSO, AGR, etc.) | SE38 → `ZABAPGIT_STANDALONE` → F8 → `+ New Offline` → choose `$DEV_ABAPGIT` or any **non-existing** Z-prefix package name → Import ZIP → Pull |
| Atomic multi-object deploy (5+ objects, all-or-nothing) | Build a ZIP on workstation containing all objects → Import → Pull in one shot |
| Export a Z package as ZIP (for sharing / backup / version control on workstation) | Open repo in abapGit → Export ZIP → save locally |
| Diff local source vs D01 active version | abapGit UI → Diff button on the repo |
| Version control of Z code with Git | Workstation has the local Git clone; export ZIPs from abapGit; commit/push to GitHub from workstation — abapGit on SAP never talks to GitHub directly |
| Cross-system sync (D01 → another system, e.g. P01 when applicable) | Export ZIP from D01 abapGit; import on the other system (workstation as the bridge) |
| Disaster recovery — rebuild a Z package from external source | Same import-ZIP flow |

**Rule: only `Z*/Y*/customer-namespace` objects.** abapGit can technically serialize SAP-standard objects but UNESCO policy + [[feedback_never_modify_standard_objects]] forbids it. Pull Z packages only.

## ❌ What is NOT available (and why)

| Capability | Status | Reason |
|---|---|---|
| Agent (Python) calling `cl_abapgit_objects=>serialize` directly via RFC | NOT POSSIBLE today | The standalone bundles ~1000 classes as private `LCL_*` inside the REPORT — not exposed as global `ZCL_ABAPGIT_*` TADIR objects. Requires dev edition install (see below) |
| The 4-FM Z wrappers (`Z_ABAPGIT_SERIALIZE`, `Z_ABAPGIT_DESERIALIZE`, `Z_ABAPGIT_ZIP_PACKAGE`, `Z_ABAPGIT_UNZIP_TO_PACKAGE`) | NOT BUILT | Depend on dev edition's global classes — pending dev edition install |
| `ZABAPGIT_API_RFC_*` FMs (PULL/LINK/SWITCHBRANCH from Python) | NOT INSTALLED | Third-party add-on; same dependency chain |
| Direct GitHub HTTPS pull from SAP | NOT ENABLED | Would require STRUST cert for github.com. We chose the workstation-bridge architecture instead — workstation is the GitHub side, SAP only sees ZIPs |
| Modifying SAP-standard (non-Z/Y) objects | FORBIDDEN | Hard rule [[feedback_never_modify_standard_objects]] |

## ⚠️ Why dev edition install was attempted today but NOT completed

| Attempted | Outcome |
|---|---|
| Download `abapGit/abapGit/main` ZIP (1.94 MB, 1,576 files) on workstation | ✅ |
| Repack ZIP without GitHub wrapper folder | ✅ — at `Zagentexecution/abapgit_install/abapgit_dev_2026-05-25.zip` |
| SAPGUI: `+ New Offline` → package `$DEV_ABAPGIT` → Import ZIP | ✅ |
| Pull zip (deserialize ~1000 objects) | ❌ **ABORTED** with ABAP runtime dump `SAPSQL_DATA_LOSS` in generated program `%_T000MZ` at 2026-05-25 16:30:09 |

**Root cause hypothesis (not fully verified):** abapGit `main` branch uses field definitions that exceed NW 7.40 EhP8 column lengths somewhere in its DDIC layer. Known compatibility class of issue with abapGit on older NW kernels — the project promises 7.02+ support but the `main` branch occasionally regresses on field lengths. The fix would be to install a tested release tag (e.g. `v1.130.0` from 2023) instead of `main`.

**State after the failure:**
- The ZIP and prepared scripts remain archived in `Zagentexecution/abapgit_install/` for re-attempt
- Repo `abapgit_dev` exists in abapGit's internal registry pointing to package `$DEV_ABAPGIT` (which itself was not fully created)
- 0 `ZCL_ABAPGIT_*` / `ZIF_ABAPGIT_*` / `ZCX_ABAPGIT_*` objects in TADIR (confirmed by re-probe)
- No partial-deserialize objects in `$DEV_ABAPGIT` — TADIR shows 0 rows in that package

**Decision (2026-05-25, user + agent):** stop. The standalone covers the actual operational need (human-driven SAPGUI workflows for any object type). The dev edition is a future optimization for agent automation — not a blocker.

## 👥 Who is expected to use this (cross-project register)

These projects' agents should consult THIS file at session start whenever they consider abapGit operations on D01:

| Project | Why they care |
|---|---|
| `abapobjectscreation` (this project) | Source — owns the install, governance, brain claims |
| `FINCLOSSING` | Consumes `sap_adt_api` skill (per `FINCLOSSING/brain_v2/refs_external.json`). Greenfield ABAP for financial closing — will create many Z objects. abapGit is now the recommended path for any multi-object work |
| `unescrp` | Has been using ADT REST + DDIF wrapper for Z deployments. Can migrate to abapGit for object types where bridges are incomplete (FUGR, ENHO, BSP) |
| `ecosystem-coordinator` | Coordinates broadcasts — BROADCAST-004 already notifies all consumers. This file is the linked source of truth |
| Future UNESCO SAP projects | Will load `sap_adt_api/SKILL.md` at session start; that skill links here |

## 🔗 Where this is referenced

- `.agents/skills/sap_adt_api/SKILL.md` §16 status block
- `.agents/skills/abapgit_integration/SKILL.md` (redirect skill quick reference)
- `ecosystem-coordinator/ecosystem/priority-actions.md` BROADCAST-004
- `brain_v2/claims/claims.json` claim #201 (active install) + #202 (kernel limitation)

## 📅 Next steps (not urgent, no blockers)

1. **(when needed)** Retry dev edition install with a release tag instead of `main` (e.g. `https://github.com/abapGit/abapGit/archive/refs/tags/v1.130.0.zip`) — should fix the `SAPSQL_DATA_LOSS` if the cause is `main`-branch-specific field lengths
2. **(when dev edition lands)** Build the 4-FM Z wrappers documented in `sap_adt_api/SKILL.md` §19.4
3. **(when wrappers land)** `Z_ABAPGIT_*` FMs become callable from `sap_adt_client.py`, completing the workstation-bridge automation architecture

## 🧹 Cleanup note (the orphan repo in abapGit's registry)

The `abapgit_dev` offline repo exists in abapGit's internal table `ZABAPGIT` (the registry, not the dev edition) pointing to package `$DEV_ABAPGIT` that was never fully created. This is **harmless** — it consumes ~1 row in `ZABAPGIT` table and a few KB. If you want to clean it: open abapGit UI → Repository List → remove "abapgit_dev". Not required.

---

**Reverify before relying on anything here:**

```powershell
python C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python\check_abapgit_installed.py
python C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\abapgit_install\verify_abapgit_state.py
```

Last full verify: 2026-05-25 14:44 (Session #76).
