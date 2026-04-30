# DMEE Versioning Procedure — first-ever V001 bump at UNESCO

**Status**: Phase 2 Week 1 deliverable · Created 2026-04-30 · Brain anchor: claim 102 (TIER_1 — zero V001/V002 patterns in any of 44 historical transports). Reviewer: M_SPRONK + N_MENARD.

## Why this document exists

**REFINED 2026-04-30 post-VPN RFC verification (claims 109 + 111)**:

- **Released-transport scope** (claim 102 holds): zero V001 patterns in 44 released transports 2017-2024 — V001 has never been transport-shipped to V01/P01.
- **In-system D01 scope** (claim 109): D01 already has `DMEE_TREE_NODE.VERSION=001` rows on all 4 in-scope trees. Someone ran *DMEE Tx → Create Version* in D01, leaving V001 as byte-identical clone of V000, dormant since.
- **P01**: `VERSION=000` only on all 4 trees (production state).

So: **V001 will be the first ever transport-released V001 at UNESCO** — but it is NOT the first time V001 entries exist in D01. Step A (Create Version) of this procedure is already partially done in D01 from an undated past event; the recommended path is to PURGE the dormant V001 + recreate fresh from aligned V000 (so the deployed V001 has a clean transport-trail).

The 2-file + DMEE-versioning strategy (per user directive 2026-04-24, plan §Design recommendations L500) requires operational competence with three SAP standard transactions: *Create Version* (already exercised in D01 once dormantly), *Activate Version* (never exercised on UNESCO trees), *Deactivate Version* (never exercised). This document captures the canonical procedure plus a dry-run protocol so Phase 2 Week 1 doesn't surprise anyone.

## What "DMEE versioning" means in SAP

`DMEE_TREE_HEAD` and `DMEE_TREE_NODE` both carry a `VERSION` column. Multiple versions of the same tree (same `TREE_ID`) coexist as separate row sets; `DMEE_TREE_HEAD.EX_STATUS = 'A'` flags exactly one active version per tree. Activation is a single-row config flip — atomic from F110's perspective.

| Field | What it does |
|---|---|
| `DMEE_TREE_HEAD.VERSION` | Numeric tag per version. Today: 000 only |
| `DMEE_TREE_HEAD.EX_STATUS` | 'A' = active (used by F110); blank = dormant |
| `DMEE_TREE_NODE.VERSION` | Per-node version tag — version-scoped node rows |
| `DMEE_TREE_COND.VERSION` | Per-condition version tag |

Source: extraction in `knowledge/domains/Payment/phase0/dmee_full/dmee_tree_head_p01_full.csv`.

## The 3-step canonical procedure

### Step A — PURGE existing dormant V001 + CREATE fresh V001 as a copy of V000 (REVISED post-Session #63)

> **Important**: D01 already has dormant V001 entries on all 4 in-scope trees (claim 109 — byte-identical clone of V000, never released). Step A is therefore PURGE + CREATE, not just CREATE.

In Tx **DMEE**:

1. Open the tree (e.g. `/SEPA_CT_UNES`)
2. **First**: Menu → **Tree → Versions → Delete Version** → select VERSION=001 → confirm. Removes the dormant clone.
3. Save → captures DELETE in the transport prompt → assign to retrofit transport `D01K-RETROFIT-01-V001-PURGE`
4. **Then**: Menu → **Tree → Versions → Create Version**
5. Source version: 000 · Target version: 001
6. Confirm copy. SAP duplicates all `DMEE_TREE_NODE` rows for `VERSION = 001` (fresh, clean transport-trail)
7. New version is created **INACTIVE** (`EX_STATUS` blank)
8. Save → captures CREATE in transport prompt → assign to V001 transport (e.g. `D01K-V001-SEPA-01`)

**Verification after Step A**:
- `RFC_READ_TABLE DMEE_TREE_HEAD WHERE TREE_ID = '/SEPA_CT_UNES'` should return 2 rows: VERSION=000 EX_STATUS='A' AND VERSION=001 EX_STATUS=''
- `RFC_READ_TABLE DMEE_TREE_NODE WHERE TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001'` should return the same node count as VERSION=000
- The new V001 NODE_IDs should match V000's after the fresh CREATE (deterministic copy)

### Step B — EDIT V001 nodes per the V001 design

Still in Tx **DMEE**, switch to Edit mode on the V001 tree. The V001 deltas per tree (sourced from companion Scope tab + plan §Per-tree design L546-567):

| Tree | V001 deltas |
|---|---|
| `/SEPA_CT_UNES` | +5 Dbtr structured nodes (StrtNm/BldgNb/PstCd/TwnNm/Ctry from FPAYHX-REF01/06 with MP_OFFSET) + 5 empty-suppress conds in DMEE_TREE_COND |
| `/CITI/XML/UNESCO/DC_V3_01` | +5 Dbtr structured nodes (XSLT auto-removes empty) + 1 UltmtCdtr StrtNm node (FPAYH-ZSTRA, brain claim 99) |
| `/CGI_XML_CT_UNESCO` | Fix CdtrAgt PstlAdr — convert AdrLine to structured StrtNm/PstCd/TwnNm/Ctry from T012K/BNKA via existing SAP Event 05 wiring (~7 nodes) |
| `/CGI_XML_CT_UNESCO_1` | SYNC from parent — FIRSTNODE_ID identical to CGI_XML_CT_UNESCO, CdtrAgt fix propagates automatically |

Save the V001 edits. Each per-tree transport carries the new `DMEE_TREE_NODE` rows with `VERSION = 001`.

### Step C — ACTIVATE V001 (cutover, Phase 5)

In Tx **DMEE**:

1. Open the tree
2. Menu: **Tree → Versions → Activate Version**
3. Select VERSION=001
4. Confirm. SAP atomically flips `DMEE_TREE_HEAD.EX_STATUS`: VERSION=000 → blank, VERSION=001 → 'A'
5. Save → transport prompt → assign to cutover transport (e.g. `D01K-V001-CUTOVER-01`)

**From this moment, every F110 run produces V001 output for that tree.**

**Rollback** (if bank rejects V001 file): same dialog, activate VERSION=000. Atomic flip back. Zero data loss because F110 is idempotent on REGUH.

## Transport ID assignment table (to fill at Phase 2 Week 1)

| Transport purpose | TRKORR | Owner | Status | Notes |
|---|---|---|---|---|
| BAdI Pattern A 3-line guard | `D01K-BADI-FIX-01` | N_MENARD reviewer | TBD | YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT |
| SEPA V001 create + nodes | `D01K-V001-SEPA-01` | M_SPRONK | TBD | Step A + Step B for /SEPA_CT_UNES |
| CITI V001 create + nodes | `D01K-V001-CITI-01` | M_SPRONK | TBD | Step A + Step B for /CITI/XML/UNESCO/DC_V3_01 |
| CGI V001 create + nodes | `D01K-V001-CGI-01` | M_SPRONK | TBD | Step A + Step B for /CGI_XML_CT_UNESCO |
| CGI_1 V001 create + nodes | `D01K-V001-CGI1-01` | M_SPRONK | TBD | Step A only (SYNC from parent on Step B) |
| TFPM042FB +1 SEPA Event 05 row | `D01K-V001-OBPM4-01` | M_SPRONK | TBD | Sub-option A — try in D01 first |
| Vendor master fix (5 LIFNRs) | (DATA, no transport) | Master Data team | TBD | LFA1+ADRC manual fix |
| Phase 5 atomic cutover | `D01K-V001-CUTOVER-01` | Pablo | TBD | Step C — ACTIVATE V001 on all 4 trees |

## Dry-run protocol (mandatory before Phase 2)

Because this is the first ever transport-released DMEE V001 at UNESCO (Activate Version + atomic V000↔V001 rollback never exercised — even though Create Version was done dormantly in D01), run a **non-load-bearing dry run** to capture muscle memory on the steps that ARE genuinely first-time:

1. **Pick a sandbox tree** that's never been used in production (or create a Z-test-tree): e.g. `/Z_DMEE_VERSIONING_TEST`
2. Execute Step A (Create Version) on it — capture screenshots of the dialog flow
3. Execute Step B with one trivial node addition (e.g. add a fixed-text node) — capture the transport prompt UX
4. Execute Step C (Activate Version) — observe the atomic flip in the DMEE_TREE_HEAD entries
5. Execute reverse Step C (deactivate, reactivate V000) — confirm rollback works
6. **Document** any UX surprises: button placement, confirmation dialogs, transport-prompt timing, error messages
7. Delete the test tree

This dry run answers two questions before Phase 2 risk increases: (a) does our SAP authorization profile allow these menu actions in D01 (some installs lock Activate Version behind extra auth), and (b) are there any SAP standard validation checks that fire during version creation/activation that we haven't anticipated.

## Things that MUST be true after each step (verification queries)

After Step A on each tree:
```sql
-- Two rows, exactly one active
SELECT VERSION, EX_STATUS FROM DMEE_TREE_HEAD WHERE TREE_ID = '<tree>';
-- Expected: 000/A + 001/(blank)
```

After Step B (during Phase 3 testing, V001 still inactive):
```sql
-- V001 has the new structured nodes
SELECT NODE_ID, NODE_TYPE, MP_SC_FLD FROM DMEE_TREE_NODE
WHERE TREE_ID = '<tree>' AND VERSION = '001'
  AND NODE_ID IN (<new-V001-node-ids>);
```

After Step C (Phase 5 cutover):
```sql
-- V001 is active, V000 is dormant
SELECT VERSION, EX_STATUS FROM DMEE_TREE_HEAD WHERE TREE_ID = '<tree>';
-- Expected: 000/(blank) + 001/A
```

## Open items / follow-ups

| Item | Why | Resolution path |
|---|---|---|
| Authorization confirmation | Activate Version may require extra auth profile we don't have in D01 | Phase 2 Week 0 — dry-run protocol |
| Workbench vs Customizing transport type | DMEE tree edits are typically Customizing, but version-management may flag a Workbench transport | Verify on dry-run |
| BAdI version-awareness | `IF_IDFI_CGI_DMEE_COUNTRIES->GET_VALUE` does NOT receive a VERSION parameter (plan §Finding L L582-625) | Already mitigated by Pattern A guard — V001 BAdI sees the active version's nodes without explicit version context |
| XSLT version-dependence | `CGI_XML_CT_XSLT` is SAP-std; behavior on V001 output not verified | Phase 4 UAT must confirm — runs against the assembled XML, not the tree directly, so should be version-agnostic |
| Multi-tree atomicity at cutover | Step C activates one tree at a time. If we want all 4 trees to flip simultaneously, group them in one transport | Plan §Phase 5 cutover order: stagger one tree at a time with 14-day monitoring (per claim 102 surgical-pattern philosophy) |

## Brain anchors

- **claim 102 TIER_1** — zero V001/V002 patterns in any of 44 historical UNESCO transports; first-ever version bump
- **claim 99 TIER_1** — UltmtCdtr Q3 RESOLVED system-driven; included in V001 of CITI tree
- **claim 96 TIER_1** — Pattern A SocGen-mandated; the BAdI 3-line guard is required for V001 safety
- **plan §Design recommendations L500-580** — 2-file + DMEE versioning rationale, sub-option A/B/C decision tree for SEPA
- **plan §Finding J L500-545** — DMEE native versioning via VERSION column confirmed in `DMEE_TREE_NODE`
- **`feedback_companion_edits_must_be_brain_anchored` CRITICAL** — applies to this document

## Cross-references in the companion

- Scope tab — what changes per tree (the V001 deltas this procedure deploys)
- Change Strategy tab — why 2-file + DMEE versioning beats Hybrid (the operational reasoning)
- E2E Flow tab — how V001 nodes connect to buffers + BAdI
- Components Map ERM — the entities this procedure operates on
- Evolution tab — Pattern 2 panel (zero-versioning history that this procedure breaks)
- Phase 2 tab — the 17-step checklist that calls into this procedure at Steps 2-4 + 11
