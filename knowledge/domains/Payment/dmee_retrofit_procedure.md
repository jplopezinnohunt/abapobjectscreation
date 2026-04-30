# DMEE D01-RETROFIT-01 Procedure — P01 source-of-truth alignment

**Status**: Phase 2 Step 0 prerequisite — TOP gating blocker · Created 2026-04-30 (Session #63) · Brain anchor: claim 108 (D01 2× cohabitation TIER_1) · CRITICAL feedback rule `feedback_p01_source_of_truth_retrofit_first_then_adjust`. Reviewer: Marlies Spronk + Pablo Lopez + Nicolas Ménard (ABAP retrofit row).

## Why this document exists

> **REVISED 2026-04-30 post-VPN restoration** — original framing of "draft cohabitation" (claim 108) was REPLACED by precise diagnosis after RFC verification (claims 109 + 111). The retrofit scope is much smaller than originally projected.

### Actual situation (Session #63 RFC verification)

D01 has explicit `DMEE_TREE_NODE.VERSION=001` rows on all 4 in-scope trees, byte-identical clones of D01 V000. Someone ran DMEE Tx → Create Version on each, then never edited or released them. P01 has only V000.

**D01 V001 vs D01 V000 (all 4 trees)**: zero NODE_ID differences, zero field differences in 7 sampled columns (TECH_NAME / MP_SC_TAB / MP_SC_FLD / MP_OFFSET / CV_RULE / MP_EXIT_FUNC). The dormant V001 is a clean clone.

**D01 V000 vs P01 V000 row-level diff**:

| Tree | D01 V000 | P01 V000 | ONLY_D01 | ONLY_P01 | CHANGED | Retrofit needed |
|---|---|---|---|---|---|---|
| `/SEPA_CT_UNES` | 95 | 95 | 0 | 0 | 0 | **NONE — byte-equal** |
| `/CITI/XML/UNESCO/DC_V3_01` | 610 | 610 | 0 | 0 | 0 | **NONE — byte-equal** |
| `/CGI_XML_CT_UNESCO` | 631 | 631 | 0 | 0 | 0 | **NONE — byte-equal** |
| `/CGI_XML_CT_UNESCO_1` | 632 | 639 | 1 | 8 | 3 | 12-node surgical |

3 of 4 trees are already byte-aligned. **Only CGI_1 needs retrofit** — 12 deltas.

### CGI_1 deltas (the only retrofit work needed at V000 level)

- **1 ONLY_D01 (purge)**: `N_6366307580` (TECH_NAME `SCB`)
- **8 ONLY_P01 (restore)**: 8 `AdrLine*` variants (these are the missing 7 from h18 + 1 extra)
- **3 CHANGED**:
  1. `N_0711160730 Nm` — D01 has `MP_SC_TAB=FPAYHX MP_SC_FLD=NAMEZ LENGTH=70`, P01 has empty TAB/FLD `LENGTH=35` (UNESCO custom Z-field experiment on `Nm`, **unrelated to PstlAdr V001 design**)
  2. `N_9432681780 Ctry` — only differs in `BROTHER_ID` (D01='', P01 points to one of the missing AdrLines) — consequential to ONLY_P01 #2 above, will resolve once AdrLines restored
  3. `N_9930896580 Ctry` — same pattern, consequential

### Net retrofit effort

Original "huge multi-tree retrofit" framing → revised to **~30 minutes of DMEE Tx work on CGI_1 + clean-slate dormant V001 cleanup**.

### SAP-standard trees match 1:1

`CGI_FICA_XML_CT`, `CGI_XML_CT` match 1:1 in both systems → the divergence is UNESCO-custom-only and version-creation-driven (not random drift accumulation).

## Two retrofit options — recommended choice (REVISED post-RFC 2026-04-30)

> **Original Option A vs Option B framing assumed full-tree retrofit. With node-level diff in hand, the surgical approach is now clearly cheapest.**

### Surgical retrofit (RECOMMENDED — replaces original Option A/B)

| Step | Action | T-code / RFC | Effort | Anchor |
|---|---|---|---|---|
| S.1 | **Purge dormant D01 V001 on all 4 trees** — DMEE Tx → Versions → Delete VERSION=001 | DMEE | ~5 min | claim 109 |
| S.2 | **CGI_1 V000 surgical alignment** — DMEE Tx /CGI_XML_CT_UNESCO_1 V000: delete node N_6366307580 (SCB), restore the 8 AdrLine nodes from P01 (transport from P01→D01 OR direct re-create), revert N_0711160730 (Nm) source from `FPAYHX-NAMEZ` to empty | DMEE | ~20 min | diff JSON |
| S.3 | **Verify CGI_1 V000 = P01 V000** — re-extract D01, count must be 639, all 8 AdrLine nodes must match P01 NODE_IDs + content | RFC | ~5 min | verification gate |
| S.4 | **Decide Nm Z-field experiment fate** — the D01 sourcing of `Nm` from `FPAYHX-NAMEZ` is a UNESCO custom edit unrelated to V001 PstlAdr design. Two choices: (a) revert Nm to P01 empty (recommended — keep retrofit truly surgical, defer Z-field experiment to a separate change), (b) keep Nm sourcing in D01 + promote to P01 via separate transport | DMEE | sí/no | claim 109 + Marlies decision |
| S.5 | **5 P01-only ABAP objects retrofit** (Finding I) — pull `YCL_IDFI_CGI_DMEE_DE`, `_IT` classes + 3 ENHO spots + `YCL_IDFI_CGI_DMEE_FR::CM002` method via P01→D01 transport | SE24 / SE19 | ~30 min | Finding I |
| S.6 | **Single retrofit transport** `D01K-RETROFIT-01` carries S.1 + S.2 + S.5 deltas | SE09 | atomic | brain rule CRITICAL |
| S.7 | **Now create FRESH V001** on all 4 trees (DMEE Tx → Create Version) — clean clone of aligned V000 | DMEE | ~10 min | versioning procedure Step A |
| S.8 | **Apply V001 change matrix** (27 rows) to fresh V001 | DMEE | per matrix | matrix CSV |

**Total ~1-2 hours Marlies + Pablo.** Zero risk to P01 (read-only extraction). D01 unmodified until single atomic transport.

### Original Option A — PURGE all D01 + RE-IMPORT from P01 (no longer needed)

| Step | Action | T-code / RFC | Risk |
|---|---|---|---|
| A.1 | In D01, DMEE Tx → delete entire UNESCO custom tree (all VERSION rows for `/SEPA_CT_UNES`) | DMEE | Loss of any unintentionally-retained draft — but draft was never transported, no production impact |
| A.2 | Same for `/CITI/XML/UNESCO/DC_V3_01`, `/CGI_XML_CT_UNESCO`, `/CGI_XML_CT_UNESCO_1` | DMEE | Same |
| A.3 | Repeat for the 5 P01-only ABAP objects (Finding I): delete D01-side stale shell if present (`YCL_IDFI_CGI_DMEE_DE` shell, `_IT` shell, 3 ENHO spots) | SE24 / SE19 | Same |
| A.4 | Transport request: `D01K-RETROFIT-01-PURGE` | SE09 | Atomic — release if all four trees + ABAP delete succeed |
| A.5 | In P01 (read-only via SNC/SSO), re-extract DMEE_TREE_HEAD + DMEE_TREE_NODE + DMEE_TREE_COND for all 4 trees | RFC RFC_READ_TABLE / RPY | Read-only, zero risk |
| A.6 | Build re-import transport `D01K-RETROFIT-01-IMPORT` from the P01 extract — DDIC-safe insert into DMEE_TREE_* tables in D01 | SE38 (custom utility) or RFC_ABAP_INSTALL_AND_RUN | DDIC inserts must respect FK constraints (NODE_ID → PARENT_ID) — verify ordering by LEV |
| A.7 | Re-import the 5 P01-only ABAP classes + 3 ENHO + the FR/CM002 method via P01→D01 transport (or RPY_CLASS_INSERT) | SE24 / SE19 | Standard SAP retrofit |
| A.8 | Re-extract D01 state, compute per-object byte hashes, must match P01 manifest | RFC | Verification gate |
| A.9 | Activate trees in D01 (DMEE_TREE_HEAD.EX_STATUS='A' for VERSION=000) | DMEE | Standard activate |

**Total Option A**: 2 transports (`PURGE` + `IMPORT`) + verification, ~1 day Pablo + Marlies if VPN healthy.

**Why Option A is recommended** (per claim 102 surgical-pattern + claim 105 V001 fully-structured + claim 108 protocol):
- Surgical-pattern philosophy: 81.8% of historical UNESCO transports touch ≤3 objects. Per-node Option-B classification of ~95+ delta nodes per tree is high effort. Mass-purge + re-import in Option A keeps the operational surface small (atomic delete + atomic re-import).
- V001 Fully-Structured commitment: the change matrix derives all 27 V001 rows from P01 NODE_IDs + claim-anchored source patterns. The D01 draft layer adds no design value we cannot reproduce from P01 + the matrix.
- Simulator validation: 794/794 PASS was performed on P01-derived data. Option A makes D01 == P01, so the simulator's PASS state is reproduced byte-for-byte in D01. Option B leaves D01 partially diverged → simulator results don't transfer.

### Option B — Surgical per-row reconciliation (only if Option A is rejected)

Per-tree, per-node classification:

| Class | Action | Examples |
|---|---|---|
| `ONLY_D01` | Decide PURGE vs PROMOTE-to-P01 with M_SPRONK | 1 SCB node + ~95 unidentified draft nodes per tree |
| `ONLY_P01` | RESTORE in D01 | 7 AdrLine* nodes per h18 sample on CGI_1 |
| `CHANGED` | Decide which side wins (default: P01) | Nm sourcing FPAYHX-NAMEZ in D01 vs empty in P01 |

**Rough effort**: ~95+ per-node decisions × 4 trees × involve M_SPRONK on each → ~1-2 weeks Phase 1 → Phase 2 W1.

**When Option B might be picked**: if any of the D01 draft nodes turn out to be intentional, valuable, and never-transported (e.g., a half-finished prior V001 attempt). Decision needs M_SPRONK input before retrofit kickoff.

## P01 snapshot manifest — what we extract

Per object, we record:
- DDIC fingerprint (`DD03L` for tables, `TADIR` for class headers, etc.)
- Row-level checksum (SHA-256 of each `DMEE_TREE_NODE.NODE_ID` + all field values, sorted by NODE_ID)
- ABAP source byte hash (`RPY_CLASS_READ` SOURCE_EXTENDED, SHA-256)

Manifest schema (saved to `Zagentexecution/incidents/xml_payment_structured_address/p01_snapshot_manifest.json`):

```json
{
  "snapshot_timestamp": "<ISO8601>",
  "trees": {
    "/SEPA_CT_UNES": {
      "node_count": 95,
      "head_hash": "<sha256>",
      "nodes_hash": "<sha256 sorted-by-id concatenation>",
      "cond_hash": "<sha256>",
      "version_active": "000"
    },
    ...
  },
  "abap": {
    "YCL_IDFI_CGI_DMEE_DE": {"hash": "...", "method_count": 7},
    "YCL_IDFI_CGI_DMEE_IT": {"hash": "..."},
    "YCL_IDFI_CGI_DMEE_FR_CM002": {"hash": "..."},
    "Y_IDFI_CGI_DMEE_COUNTRIES_DE": {"hash": "..."},
    "Y_IDFI_CGI_DMEE_COUNTRIES_FR": {"hash": "..."},
    "Y_IDFI_CGI_DMEE_COUNTRIES_IT": {"hash": "..."}
  },
  "customizing": {
    "TFPM042FB": {"row_count": 50, "hash": "..."}
  }
}
```

## Verification gate — what "byte-aligned" means

After retrofit, the D01 manifest must satisfy:
- Per tree: `node_count` matches P01 exactly (95, 631, 639, 610)
- Per tree: `nodes_hash`, `cond_hash` match P01
- Per ABAP class: `hash` matches P01
- Per customizing table: `row_count` and `hash` match P01 (allowing for D01 client-specific MANDT differences only)

If ANY hash mismatches → retrofit is incomplete → DO NOT apply V001 change matrix.

## Tool support

The Python tool `Zagentexecution/incidents/xml_payment_structured_address/p01_snapshot_d01_diff.py` (created Session #63) implements:
1. `extract_p01_snapshot()` — runs against P01 via RFC, produces manifest JSON
2. `extract_d01_snapshot()` — runs against D01 via RFC
3. `diff_snapshots(p01, d01)` — produces per-object delta classification
4. `propose_retrofit_transport(diff)` — outputs Option A purge+import spec OR Option B per-node spec

VPN-blocked currently (2026-04-30) — but the tool is staged. First action when network is restored: `python p01_snapshot_d01_diff.py --extract-p01 --output p01_snapshot_manifest.json`.

## Sequence with V001 deployment (the invariant)

```
Step 0a · P01 snapshot manifest (extract)     ← we are here pre-VPN
   ↓
Step 0b · D01 snapshot manifest (extract)     ← needs VPN
   ↓
Step 0c · Diff + classify deltas              ← offline once both manifests exist
   ↓
Step 0d · M_SPRONK + Pablo decide Option A or B
   ↓
Step 0e · D01-RETROFIT-01-PURGE transport     ← needs VPN + DMEE access
   ↓
Step 0f · D01-RETROFIT-01-IMPORT transport    ← P01→D01 import
   ↓
Step 0g · Verification — D01 manifest = P01 manifest by hash
   ↓
─────────────────────────────────────────────────────
   ↓ ONLY AFTER ABOVE GATES PASS
   ↓
Phase 2 Step 1 · BAdI Pattern A (D01K-BADI-FIX-01)
Phase 2 Step 2 · V001 SEPA tree + nodes (D01K-V001-SEPA-01)
Phase 2 Step 3 · V001 CITI tree + nodes (D01K-V001-CITI-01)
Phase 2 Step 4 · V001 CGI tree + nodes (D01K-V001-CGI-01)
Phase 2 Step 5 · V001 CGI_1 SYNC (D01K-V001-CGI1-01)
Phase 2 Step 6 · TFPM042FB +1 row for SEPA (D01K-V001-OBPM4-01)
Phase 5 cutover · D01K-V001-CUTOVER-01
```

## Brain anchors

- **claim 108 TIER_1** — D01 2× cohabitation pattern verified
- **claim 105 TIER_1** — V001 Fully-Structured commitment + 794/794 simulator PASS
- **claim 102 TIER_1** — surgical-pattern (81.8% transports ≤3 objects)
- **claim 99 TIER_1** — Q3 RESOLVED system-driven (UltmtCdtr unification)
- **plan §Finding I** — 5 P01-only ABAP objects (must retrofit)
- **`feedback_p01_source_of_truth_retrofit_first_then_adjust` CRITICAL** — the rule this procedure operationalizes
- **`feedback_companion_edits_must_be_brain_anchored` CRITICAL** — applies to this document

## Cross-references

- Companion **Current Solution tab** — visual evidence + risk callout
- Companion **V001 Change Matrix tab** — 27 rows that land AFTER retrofit
- `dmee_versioning_procedure.md` — Step A/B/C of V001 deployment, prerequisite block at top must reference this retrofit procedure
- `phase2_readiness_checklist.md` — Section G blocker #0 (TOP gating)

## Open items for review by Pablo + Marlies before kickoff

1. **Decision Option A vs Option B** — recommended A (purge + re-import). Pablo + Marlies sign-off needed.
2. **Was there an intentional draft V001 attempt in D01?** — h18 sample shows D01 attempting Z-field sourcing on `Nm` node. Marlies confirms whether to preserve it (Option B) or purge (Option A).
3. **`/CGI_XML_CT_UNESCO_1` reconciliation** — already documented in Current Solution tab as "double-orphan" (zero T042Z routes + 2× drift). Decision: keep as SYNC twin of `/CGI_XML_CT_UNESCO` for V001 (matrix row 25), or remove from V001 scope. Recommendation: keep — node-cost is zero (FIRSTNODE_ID shared) and any V001 fix on parent propagates automatically.
4. **CITI D01 extraction** — pending VPN. Predicted same 2× pattern. Action when VPN: extract first thing.
5. **N_MENARD review of ABAP retrofit row** — the 5 P01-only ABAP objects retrofit needs his sign-off (he is the code owner). Folds into the existing N_MENARD alignment call.
