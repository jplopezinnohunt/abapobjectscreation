# INC — ABAP Class Loss / Corruption on D01 via ADT-over-RFC write client (June 2026)

**Status:** OPEN — forensic complete, recovery pending user scope confirmation
**System:** D01 (172.16.4.66, client 350) — dev. NO P01 impact found.
**Reported:** 2026-06-12 — "Claude processes deleted class definitions, at least 14 lost."
**Severity:** HIGH (custom Y*/Z* classes, some are active BAdI/exits → may break postings)

## Mechanism (root cause — evidence-based)

A write-capable ADT client was built on **2026-06-07** and used to write/activate
existing D01 classes:

- `Zagentexecution/mcp-backend-server-python/sap_adt_rfc_client.py` (created 2026-06-07 12:36)
  — `deploy()` = lock → **write_source(/source/main)** → syntax → unlock → **activate**.
- `probe_deploy_real_change.py` (2026-06-07 12:21) — read → modify → write → activate →
  **then "restore" original**. If restore fails (exception/conn drop/lossy read), the class
  is left modified/emptied.

Two corruption paths, both proven by the code itself:
1. **Lossy read → restore.** `read_source()` falls back to `CLIF_GET_SOURCE` via
   `RFC_ABAP_INSTALL_AND_RUN` with `WRITE: / lv` (lv = c(255)). That output is **truncated
   at 255 chars/line and includes report headings**. Writing that back as the "restore"
   **mangles the class definition**.
2. **Write to a class with missing/invalid metadata.** `deploy()`'s own docstring:
   *"Writing to a class with missing SEOCLASS leaves it in unrecoverable state
   (learned D01 2026-06-07)."* The SEOCLASS pre-flight guard was added AFTER the lesson —
   i.e. damage already occurred before the guard existed.

The `learning_summary.md` of the 2026-06-10 N_MENARD inventory task says "No SAP
writes/deploys" — that task was read-only; the damage came from the **separate Jun-7 probe
session**, not the inventory scan.

## DEFINITIVE SCOPE — CORRECTED (cross-checked with the CRP-session post-mortem)

**Cardinal-rule violation:** session `3d85c27e` (ADT-client dev / N_MENARD pattern study)
used **real N_MENARD classes as live ADT write-test targets** on D01 — never our objects.

**Authoritative victim set = 14 N_MENARD classes** — TADIR present, SEOCLASS/definition gone.
All 14 are N_MENARD-authored orphans in `orphan_scan_result.json` AND present in the Jun-10
TADIR inventory (`nmenard_inventory.json`). My earlier "6" was WRONG as a total: the
transport-footprint method (E071) only caught the 4 FI classes that landed in JP_LOPEZ
transports; the other 10 were corrupted by write attempts that errored (`ResourceNotFound`)
without transport assignment. The N_MENARD-author-orphan lens is the correct one.

| Domain | Classes (14) | in Jun-7 transport? |
|---|---|---|
| FI (5) | YCL_FI_ACCOUNT_SUBST_BL, YCL_FI_ACCOUNT_SUBST_READ, YCL_FI_ACC_DOCUMENT_ARGA, YCL_FI_BANK_RECONCILIATION_BL, YCL_FI_RFBIBL00_UTIL | 4 of 5 (FJQ/FJS/FJU/FJW) |
| HR (5) | YCL_HRPA_INFOTYPE_0021_UN, YCL_HR_ASSIGNMENT, YCL_HR_CONTENT_REPOSITORY_BL, YCL_HR_IMPL_FIORI_INBOX, ZCL_HRPA_INFOTYPE_0006_UN | no |
| RE (1) | YCL_RE_BADI_EX_FI | no |
| BC/ALV (2) | YCL_ALV_EDIT_CONTAINER, YCL_BC_DATA_CONTAINER | no |
| IM (1) | YCL_IM_IMP_FEB_BADI | no |

**Operational impact (CRP-session finding):** the FI substitution `YRGGBS00` references
`YCL_FI_ACCOUNT_SUBST_READ` → runtime "type unknown" → `BAPI_ACC_DOCUMENT_POST` dumps
SYNTAX_ERROR → **all JV posting in D01 is blocked** (incl. CRP AO-Approve).

**Production (P01) UNAFFECTED**; classes are **healthy in V01** (sibling system). Recovery is
by **transport from V01**, never by ADT write.

### Secondary (OUR OWN ZCRP objects — separate, lower severity, we own the source)
ZCL_CRP_CERT_READER, ZCL_ZPSM_PROC_FORMS_MPC_EXT read EMPTY (0 comp) — VERIFY against the CRP
session's `verify_mirror` (it reported 38 CRP objects intact, so these may be mid-dev/transient).
If genuinely lost, rebuild from our own git/extracts — NOT part of the N_MENARD violation.

### Containment (done 2026-06-12)
Write paths HARD-DISABLED in BOTH ADT clients (`sap_adt_rfc_client.py` write_source/activate;
`sap_adt_client.py` set_source) — raise unless `ALLOW_D01_WRITES=1`. Reads unaffected.

## Recovery — ALIGNED with the CRP-session plan (Basis, via V01 transport)

1. **V01:** `SE01` → Transport of Copies → the 14 classes (+ whatever a V01↔D01 comparison
   adds) → release.
2. **Import to D01:** `STMS` / `tp import` — recreates full definitions from the sibling system.
3. **Orphan TADIR:** if a TADIR-without-definition blocks import → `SE03` object-directory
   cleanup → reimport clean.
4. **Regenerate FI substitution:** `GGB1` / `OBBH` → regenerate `YRGGBS00`; confirm no syntax error.
5. **Complete the inventory (Basis):** full V01↔D01 comparison (`SE03`/`SCMP`) — catches any
   non-CLAS damage (PROG/DTEL/TABL) without the false positives external RFC probes give on
   generated objects.

NEVER recover via `write_source`/`deploy`/manual ADT — that was the cause.
Fallback if V01/Basis is slow (still SAP-native, traceable, NON-ADT): D01 version-management
retrieve (SE80 → Versions), VRSD holds 10–92 prior versions per class.

## Verification (read-only — Claude runs after restore)
- SEOCLASS populated for the 14 (ADT source GET = 200 with content).
- `YRGGBS00` compiles (no SYNTAX_ERROR).
- `BAPI_ACC_DOCUMENT_POST` test no longer dumps; CRP AO-Approve completes the JV.

## Forensic method (all READ-ONLY)

- `forensic_class_loss.py` — REPOSRC unreadable via RFC (`TABLE_WITHOUT_DATA`); switched to
  SEO change tables. SEOCLASSDF changed-by-jp_lopez in window = 0 (deletion erases the
  evidence row → change-table discovery is BLIND to deletions).
- `orphan_scan.py` — TADIR CLAS ∖ SEOCLASS = **45 orphans** (Y:20, Z:25); SEOCLASS ∖
  SEOCOMPO = **182 "empties"**. BUT census-diff shows the empties were already empty on
  Jun-10 (exit/BAdI classes legitimately carry 0 SEOCOMPO) → **not all incident damage**.
- `census_diff.py` — Jun-10 census vs now = **0 component regressions**. Census is
  **post-Jun-7-damage**, so it cannot serve as the pre-damage baseline. None of the 45
  orphans are in the census classdf (they were already broken when the census ran, or are
  ancient orphans unrelated to this).

## Key recoverability fact

`jp_lopez` created **0 new versions** in VRSD in the damage window → the writes did NOT
produce clean version snapshots; the **pre-damage versions (2024, by original authors)
survive in SAP version management**. That is the authoritative, exact restore source —
better than our lossy extracts.

## Recovery — DO NOT reuse the flawed write client

- Restore each confirmed-broken class from **SAP version management** (SE24 → Utilities →
  Versions → Retrieve last good version → activate), or our golden copies in
  `extracted_code/` + `Zagentexecution/tasks/2026_06_10_nmenard_inventory/readback/` + git.
- The write client `sap_adt_rfc_client.py` / `probe_deploy_real_change.py` must be
  **quarantined** until the lossy-restore and SEOCLASS-guard bugs are fixed.

## Open items

- Exact incident scope (the "14") — needs how the user observed it (list / SE80 / prior
  session report) to separate incident damage from the ~45 ancient orphans.
- Local-only assets at risk (always flag): Golden DB (~6.4GB, gitignored) + ~/.claude memory.
