# DMEE Versioning Procedure — first-ever V001 bump at UNESCO

**Status**: Phase 2 Week 1 deliverable · Created 2026-04-30 · Brain anchor: claim 102 (TIER_1 — zero V001/V002 patterns in any of 44 historical transports). Reviewer: M_SPRONK + N_MENARD.

## Why this document exists

Per brain claim 102: across all 44 DMEE-touching transports by M_SPRONK / N_MENARD / FP_SPEZZANO 2017-2025, <strong>zero used DMEE native versioning</strong>. All 4 target trees today carry `DMEE_TREE_HEAD.VERSION = 000`. **V001 will be the first ever DMEE version bump at UNESCO**.

The 2-file + DMEE-versioning strategy (per user directive 2026-04-24, plan §Design recommendations L500) requires operational competence with three SAP standard transactions never previously exercised by the team: *Create Version*, *Activate Version*, *Deactivate Version*. This document captures the canonical procedure plus a dry-run protocol so Phase 2 Week 1 doesn't surprise anyone.

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

### Step A — CREATE V001 as a copy of V000

In Tx **DMEE**:

1. Open the tree (e.g. `/SEPA_CT_UNES`)
2. Menu: **Tree → Versions → Create Version**
3. Source version: 000 · Target version: 001
4. Confirm copy. SAP duplicates all `DMEE_TREE_NODE` rows for `VERSION = 001`
5. New version is created **INACTIVE** (`EX_STATUS` blank)
6. Save. Capture the transport prompt → assign to V001 transport (e.g. `D01K-V001-SEPA-01`)

**Verification after Step A**:
- `RFC_READ_TABLE DMEE_TREE_HEAD WHERE TREE_ID = '/SEPA_CT_UNES'` should return 2 rows: VERSION=000 EX_STATUS='A' AND VERSION=001 EX_STATUS=''
- `RFC_READ_TABLE DMEE_TREE_NODE WHERE TREE_ID = '/SEPA_CT_UNES' AND VERSION = '001'` should return the same node count as VERSION=000

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

Because this is the first ever DMEE version bump at UNESCO, run a **non-load-bearing dry run** to capture muscle memory:

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
