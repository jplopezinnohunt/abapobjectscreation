# CONTRACTS — how a producer contributes to the core (peldaño 2)

> **Status:** normative, hand-versioned. `_version: 1.0` · created Ola 2 / T2 (2026-07-25).
> **Scope:** this file is the SINGLE source of the contribution contracts. `.claude/agents/brain-steward.md`
> POINTS here; it does not restate them. One source, not two.

## Contract registry

| id | contract | subject | gate today |
| --- | --- | --- | --- |
| **C-1** | canonical ontology | which `domain` / `dimension` keys are legal | `brain_v2/validate_ontology.py` — step 0 of `rebuild_all.py` (**EXECUTABLE**) |
| **C-2** | `submit_claim` | how a producer contributes a FACT to `brain_v2/claims/claims.json` | **NOT gated** — see §7. `claims_health.py` scores it after the fact |
| **C-3** | `cell-move` | how a capability-model cell may change value | **NOT gated** — see §7 |

C-1 already exists (`brain_v2/capability_model/ontology.json`, 17 canonical domains, 16 aliases,
12 cross-cutting keys, 11 dimensions). C-2 and C-3 are defined here and EXTEND it: they reuse its
vocabulary, they do not create one.

---

## 0. The founding asymmetry: evidence vs verdict

> **A producer contributes EVIDENCE. The steward JUDGES.**

This is not new policy — it is already the steward's written authority, and this file only makes it
executable-shaped:

- `.claude/agents/brain-steward.md` **L12-13**:
  *"It does NOT design code, does NOT write to SAP, does NOT invent a new schema — it writes into the
  EXISTING stores and triggers the rebuild."* — the steward is the **only** writer into the central stores.
- `.claude/agents/brain-steward.md` **L119-124** (Hard limits):
  *"NEVER invent a new knowledge schema or a parallel store"*, *"NEVER hand-edit `brain_state.json`"*,
  *"NEVER promote an unverified hunch as a fact. No evidence → it is a `known_unknown`, not a claim."*

Corollary, and the reason C-2/C-3 exist: **`HAVE` / `PARTIAL` / `NONE` is a steward verdict, never a
producer field.** Those three values are the capability-model cell vocabulary
(`ontology.json:_tier_legend`), i.e. an assessment of coverage across the WHOLE brain. A producer sees
one investigation; it cannot know whether the column is now HAVE. A producer that ships a verdict is
grading its own homework.

| | producer may send | steward alone decides |
| --- | --- | --- |
| C-2 claim | the fact + its evidence + its confidence **tier** | `status`, `superseded_*`, `verification_status`, whether it lands at all |
| C-3 cell | the claim ids that justify a move | the cell VALUE (`HAVE`/`PARTIAL`/`NONE`), maturity impact |

`confidence: TIER_1..3` is NOT the verdict. It states *the quality of the producer's own evidence*
(self-assessed, auditable against `evidence_for`). `HAVE/PARTIAL/NONE` states *the brain's coverage*
(cross-producer, only the steward has that view).

---

## 1. Contract C-2 — `submit_claim`

**Store:** `brain_v2/claims/claims.json` (a JSON array — NOT `brain_v2/claims.json`).
**Reference instance:** claim **#3**, `brain_v2/claims/claims.json` **L89-148** (`verification` block at
**L136-144**). The schema below is derived field-by-field from that record on disk, not from an idea of it.

### 1.1 REQUIRED (producer must send)

| field | type | rule | claim #3 |
| --- | --- | --- | --- |
| `claim` | string | one falsifiable assertion. Not a summary, not a plan. | `"FEBEP=0 was wrong — actual count is 223,710 items in FEBEP_2024_2026"` |
| `claim_type` | enum-ish string | see §1.5 — vocabulary is de-facto open today (52 distinct values in use) | `"superseded"` |
| `confidence` | `TIER_1` \| `TIER_2` \| `TIER_3` | evidence quality, self-assessed. See §1.5 for the 13 off-vocabulary legacy values. | `"TIER_1"` |
| `evidence_for` | array of evidence objects | **>= 2 DISTINCT `type` values** (§1.3). Never a list of bare strings. | 1 item, `type: "empirical"` — see §1.3 honesty note |
| `related_objects` | array of strings | the SAP/brain entities the claim is about; drives the graph cross-link | `["FEBEP","FEBEP_2024_2026"]` |
| `domain` | string | MUST be an exact `canonical_key` (or declared alias) of `ontology.json` (§1.4) | `"FI"` |
| `domain_axes` | object `{functional[], module[], process[]}` | the 3-axis L14 tagging. 312/351 claims carry it; `crosscheck_consistency.py` check #7 already asserts it. | `{"functional":["Treasury"],"module":["FI"],"process":["T2R"]}` |

### 1.2 OPTIONAL (producer may send)

| field | rule |
| --- | --- |
| `evidence_against` | same shape as `evidence_for`. `null` when none. Sending it is a QUALITY signal, not a weakness — claim #3 carries the falsifying evidence at **L102-110**. |
| `verification` | the machine re-derivation block (§1.6). **Strongly encouraged**: only **14 of 351** claims have one. |
| `created_session` | integer session number |
| `related_objects` extras: `cross_links`, `related_incident`, `related_claims`, `tags` | free cross-references |
| `resolution_notes` | how the claim was closed, if it is a correction |

### 1.3 `evidence_for` — item shape and the independence rule

Item shape as it exists on disk (claim #3, L93-101):

```json
{ "type": "empirical", "ref": null, "cite": "Re-extraction in Session #029 revealed 223K rows...",
  "added_session": 25 }
```

- `type` — REQUIRED. The evidence CLASS.
- `cite` — REQUIRED. Human-readable justification.
- `ref` — REQUIRED when the evidence is addressable (`FILE.abap:852`, a Gold DB table, a query).
  `null` is tolerated but weakens the claim: only **403 of 2706** evidence items carry a `ref`.
- `added_session` — recommended.

**Independence rule (already implemented, `brain_v2/claims_health.py:29-37`):** two evidence items of the
SAME `type` are corroboration, not independence. `>= 2 distinct types` = STRONG, `1` = WEAK,
`0` = UNSUPPORTED. A WEAK + TIER_1 claim is the dangerous kind.

> **HONEST BASELINE (measured 2026-07-25, do not hide it):** only **85 of 351 claims (24.2%)** meet the
> `>= 2 distinct types` bar. 188 have exactly one; **78 carry `evidence_for` as a list of bare strings**
> with no `type` at all (legacy, pre-s054 migration). `claims_health.json` reports 24.5% on live claims
> (78 STRONG / 240 WEAK of 318 live).
> **Therefore C-2 is FORWARD-ONLY.** It binds NEW submissions. It does not retro-invalidate the 266
> claims below the bar; those are the `claims_health.py` worklist (21 WEAK TIER_1 items queued today).

> **KNOWN WEAKNESS of the rule:** `type` is a free string — **111 distinct values in use**
> (`production_data` 68, `empirical` 64, `source_code` 48 … down to ~70 singletons like
> `empirical_http_probe`, `user_testimony`, `namespace_bug_source`). A producer can trivially satisfy
> "2 distinct types" by inventing a second label for the same source. Until an evidence-class vocabulary
> is frozen in `ontology.json` (pending, §8), the independence rule is a convention the steward must
> read, not a check the machine can trust.

### 1.4 `domain` — exactly one canonical key

`domain` MUST resolve by EXACT lookup in `ontology.json` (C-1 `_resolution_rules`: no token matching,
no fuzzy fallback). `validate_ontology.py` is the gate and it STOPS the rebuild on an unknown value.

- 17 `canonical_key`s + 16 aliases + `subdomain_aliases` (`Cost_Recovery_CRP`) all resolve.
- 12 `cross_cutting_keys` also resolve but are **NOT domains**; the list is FROZEN.

> **BUG FOUND ON DISK — dimensions are leaking into `domain`.** Four of the 12 registered
> `cross_cutting_keys` are actually **capability DIMENSIONS**: `D_DATA`, `F_INTERFACE_FILE`,
> `G_CONFORMANCE`, `H_IMPROVE`. **22 claims** use a dimension as their `domain`
> (`D_DATA` ×18 — ids 241-244, 247-248, 319-328, 335, 337-340, 347; `F_INTERFACE_FILE` ×2;
> `G_CONFORMANCE` ×1; `H_IMPROVE` ×1). The ontology currently LEGITIMIZES this by registering them as
> cross-cutting. This conflates the two axes of the model (`domain × dimension`) into one field.
> **C-2 rule:** a new claim MUST NOT use a dimension key as `domain`. The 22 legacy claims stay
> (CP-002 preserve-first) and are listed in §8 as a re-tagging backlog.

### 1.5 Vocabulary drift the producer must not add to

- `claim_type`: **52 distinct values** for 351 claims (`verified_fact` 248, `superseded` 16,
  `measured_fact` 10, then a long tail of one-offs: `substitution_third_actor`, `kernel_limitation`,
  `bug_pattern_and_mitigation`…). Producers SHOULD reuse an existing value; inventing one is a steward
  decision.
- `confidence`: 13 claims are off-vocabulary — `HIGH` (ids 31-41) and `VERIFIED` (ids 42-43). New
  submissions MUST use `TIER_1|TIER_2|TIER_3`.
- `status`: 21 claims have NO `status` (ids 27-43, 121-124). Producers do not set `status` at all (§1.7).

### 1.6 `verification` — the optional block that makes a claim re-derivable

Shape (claim #3, L136-144; executor `brain_v2/verify_claims.py`, run as step 2b of `rebuild_all.py`):

```json
"verification": {
  "source": "gold_db",
  "query":  "SELECT COUNT(*) FROM febep_2024_2026",
  "expect": { "op": "==", "value": 223710 },
  "note":   "FEBEP item count (reality, P01)"
}
```

- `source` must be `gold_db` (the only source `verify_claims.py` executes; anything else = NO_CHECK).
- `query` must start with `SELECT` (non-SELECT → `ERROR`).
- `expect.op` ∈ `== != > >= < <= nonzero between approx contains`.
- PROVENANCE GUARD (`verify_claims.py:72-80`): a query touching `d01_*`/`v01_*` tables is a CODE fact and
  must opt in via `system_invariant: true`; a reality fact must read bare-named (P01) tables. **No claim
  uses `system_invariant` today (0/351)** — the guard is written but never exercised.

### 1.7 FORBIDDEN — a producer that sends these is rejected

| field / value | why | who owns it |
| --- | --- | --- |
| **`verdict`** (any field) | not a field of the claim schema at all — no claim on disk has one | — |
| **`HAVE` / `PARTIAL` / `NONE`** as any value | that is the capability-model CELL vocabulary, a coverage verdict across the whole brain | steward, via C-3 |
| `status` | live/superseded is a brain-wide judgement | steward |
| `superseded_by_claim_id`, `superseded_reason`, `superseded_linked_session`, `supersedes*` | supersession is a relation the steward establishes after DEDUPE (`brain-steward.md` step 3) | steward |
| `verification_status`, `last_verified`, `verified_value` | written back by `verify_claims.py`, never by hand | the harness |
| `id` | assigned on landing (max+1) | steward |
| direct write to `brain_state.json` | GENERATED (`brain-steward.md` L121) | `rebuild_all.py` |

Rejection is not a discard: a submission carrying a forbidden field is returned to the producer with
the field stripped, and the underlying observation is still eligible to land as a claim — or, if it has
no evidence, as a `known_unknown` (`brain-steward.md` L122-123).

---

## 2. Contract C-3 — `cell-move`

A **cell-move** = changing one `domain × dimension` cell of
`brain_v2/capability_model/capability_model.json` (15 domains + 32 subdomain rows = **47 rows × 11
dimensions = 517 cells**). Moving one cell moves `maturity.json` and therefore the project's headline
number (32.1%). It is the single highest-leverage write in the brain.

### 2.1 The rule

> **A cell-move is REJECTED without `evidence_claim_ids`.**

`evidence_claim_ids` = a non-empty array of `claims.json` ids that (a) exist, (b) are `status: active`
(not superseded), and (c) carry a `domain` resolving to the row being moved. Prose is not evidence for a
cell; a claim id is, because a claim is itself evidence-bound by C-2 and re-derivable by §1.6.

Additional rules:
- **The producer never sends the target value.** It sends `evidence_claim_ids` + `dimension` + `row`.
  `HAVE/PARTIAL/NONE` is the steward's call (§0).
- **Downgrades need evidence too.** Moving a cell DOWN (e.g. after a refutation) requires the claim ids
  that refute the prior basis — an undocumented downgrade is indistinguishable from data loss (CP-002).
- **`dimension` must be one of the 11 canonical keys** (§3). No shorthand, no suffix.
- **`row` must be a `canonical_key`** of C-1, optionally `Domain/subdomain` for a subdomain row.

### 2.2 Where a cell-move is recorded

The ledger already exists: `brain_v2/capability_model/applied_models.json` →
`applied_by_domain[<domain>]`, keys `{applied, evidence, cells_moved, enrich_artifact, documented_method,
available_not_applied, note}`.

Target shape (EXTENDS the existing entry, renames nothing):

```json
"cells_moved": [
  { "dimension": "G_CONFORMANCE", "from": "NONE", "to": "PARTIAL",
    "evidence_claim_ids": [260, 262], "session": "s092",
    "why": "as-is vs standard 3-way conformance on P2P" }
]
```

> **HONEST STATE ON DISK:** `cells_moved` today is **free text on 1 of 7 entries** — Procurement_P2P:
> `"S_STANDARD_REF->PARTIAL, G_CONFORMANCE->PARTIAL (as-is vs standard 3-way); A_PROCESS stays HAVE"`.
> The other 6 have none. **Zero `evidence_claim_ids` exist anywhere in the file** (0 claim ids across
> all `cells_moved` + `evidence` strings). Claim traceability for cell values currently survives only in
> the free-text `note` of `capability_model.json`: **16 of 45 notes** cite a `#nnn` claim id
> (e.g. Payment_BCM `note` cites #216, #260/#262; `dual_control_gap` cites #237-240). So today
> **~34% of rows have any claim-level traceability at all, and it is unparseable prose.**
> C-3 does not claim this is enforced; it states the target and §7 states the gap.

### 2.3 No programmatic writer exists

`capability_model.json` cells are **hand-edited**. Verified by grep: every script that touches the file
(`build_brain_state.py:56`, `maturity_score.py:18`, `graph_queries.py:329`, `build_brain_index.py:31`,
`validate_ontology.py:51`, `scripts/build_maturity_dashboard.py:13`) is a **READER/SCORER** — none writes a
cell. Consequence: C-3 is a **procedural** contract enforced by the steward at review time until a
`validate_cell_moves.py` gate exists (§8). That is exactly why it must be written down.

---

## 3. Dimension vocabulary — the 11 canonical keys

Verbatim from `ontology.json:dimensions` (which is itself a verbatim copy of
`capability_model.json:dimensions`; `capability_model.json` remains the source of truth for cell VALUES,
`ontology.json` for which keys are LEGAL).

`S_STANDARD_REF` · `A_PROCESS` · `B_CODE` · `C_CONFIG` · `D_DATA` · `E_AUTH` · `F_INTERFACE_FILE` ·
`G_CONFORMANCE` · `H_IMPROVE` · `R_S4_READINESS` · `U_USAGE`

Any contribution naming a dimension MUST use one of these EXACT strings. Specifically:
- **No suffixes.** There is no `-write`, `-read`, or any other suffixed dimension. Verified by grep over
  the whole repo: **zero matches** for `<DIM>-<suffix>`.
- **No single-letter shorthand** (`E/F`, `F`) — see §3.1.
- **A dimension is not a domain** (§1.4).

### 3.1 The field is called `fills`, not `dimension_touched`

**`dimension_touched` does not exist in this repo** — zero matches, any case, any extension. The real
field by which a contribution declares which dimension it advances is **`fills`**, on the tasks of
`brain_v2/capability_model/execution_backlog.json`. It is FREE TEXT (`"E_AUTH (rank-1 — closes the
column…)"`), so it resolves only by substring. Full audit of the 24 tasks:

| `fills` value in use | resolves to | note |
| --- | --- | --- |
| `E_AUTH (rank-1 …)` | `E_AUTH` | EXT-AUTH |
| `R_S4_READINESS / BP_CVI factor …` | `R_S4_READINESS` | EXT-BPCVI; `BP_CVI` is a sub-factor, not a dimension |
| `A_PROCESS (field-level change events) …` | `A_PROCESS` | EXT-CDPOS |
| `F_INTERFACE_FILE (job intent …)` | `F_INTERFACE_FILE` | EXT-VARIANT |
| `F_INTERFACE_FILE (file system as OCEL object)` | `F_INTERFACE_FILE` | EXT-FILES |
| **`E/F + B_CODE (service & interface usage)`** | `B_CODE` only | **EXT-SERVICES — `E/F` is shorthand and does NOT resolve.** Intended: `E_AUTH` + `F_INTERFACE_FILE` |
| `B_CODE (used-vs-dead) + feeds R_S4 …` | `B_CODE` | EXT-USAGE; `R_S4` shorthand also fails to resolve |
| `A_PROCESS (breadth …)` | `A_PROCESS` | EXT-EVENTSOURCES |
| `R_S4_READINESS (SI / custom-code …)` | `R_S4_READINESS` | EXT-S4CHECKS |
| `D_DATA (text completeness …)` | `D_DATA` | EXT-STRG-ODESC |
| `A_PROCESS substrate` / `A_PROCESS` / `A_PROCESS (Procurement)` | `A_PROCESS` | AN-OCEL2, AN-PM4PY, AN-P2P |
| `S_STANDARD_REF (rank-0)` | `S_STANDARD_REF` | AN-STDREF |
| `G_CONFORMANCE (Procurement) — first x-ray` | `G_CONFORMANCE` | AN-G-P2P |
| `R_S4_READINESS / BP_CVI …` | `R_S4_READINESS` | AN-BPCVI-SCORE |
| `B_CODE` ×2 | `B_CODE` | AN-ABAPLINT, AN-DEPGRAPH |
| **`F (file design)`** | **UNRESOLVED** | **AN-OPENDATASET — bare `F`. Intended: `F_INTERFACE_FILE`** |
| **(field absent)** ×5 | **UNRESOLVED** | **RES-AUTH-SOD, RES-FINANCE-S4, RES-COMPETITORS, RES-S4-GREENFIELD, DSGN-S4-WEIGHTING** — `research_tasks_followups` carry `{id, for, do, status}` with no `fills` at all |

**Never used, in any store:** `C_CONFIG`, `H_IMPROVE`, `U_USAGE` — no task declares that it fills them.
`U_USAGE` is especially notable: it is a live dimension with PARTIAL cells and no backlog task pointing at it.

**C-2/C-3 rule:** a contribution declaring a dimension sends the CANONICAL KEY in its own field, and puts
the prose in a separate `why`. `fills` stays as the human label; the machine reads the key.

---

## 4. Producer checklist (paste into a submission)

```
C-2 submit_claim
[ ] claim         — one falsifiable sentence
[ ] claim_type    — reused from the existing vocabulary
[ ] confidence    — TIER_1|TIER_2|TIER_3 (evidence quality, NOT coverage)
[ ] evidence_for  — >=2 items with DISTINCT `type`, each with `cite`, `ref` when addressable
[ ] related_objects
[ ] domain        — exact canonical_key of ontology.json, and NOT a dimension key
[ ] domain_axes   — functional / module / process
[ ] verification  — optional but this is how the claim stays true (14/351 have it)
[ ] NO verdict, NO HAVE/PARTIAL/NONE, NO status, NO superseded_*, NO id

C-3 cell-move
[ ] row + dimension (canonical, no shorthand)
[ ] evidence_claim_ids — non-empty, active claims, domain matches the row
[ ] why
[ ] NO target value — the steward decides HAVE/PARTIAL/NONE
```

---

## 5. Consumers

- `brain_v2/validate_ontology.py` — enforces C-1 (the `domain` half of C-2 §1.4).
- `brain_v2/claims_health.py` — scores C-2 §1.3 after the fact; emits the WEAK-TIER_1 worklist.
- `brain_v2/verify_claims.py` — executes C-2 §1.6; writes back `verification_status`.
- `brain_v2/scripts/crosscheck_consistency.py` — check #7 asserts `domain_axes` presence.
- `.claude/agents/brain-steward.md` — the steward, sole writer; points HERE for the contract.

## 6. What is NOT in this file

Storage layout, rebuild order, and the maturity formula. Those live in `rebuild_all.py`,
`maturity_score.py` and `BRAIN_INDEX.md`. This file only answers: *what may a producer send, and what
may only the steward decide.*

## 7. Enforcement status — honest

| rule | gated by a script? |
| --- | --- |
| C-2 `domain` resolves to a canonical key | **YES** — `validate_ontology.py`, stops the rebuild |
| C-2 `domain` is not a DIMENSION key | **NO** — the ontology currently registers 4 dimensions as cross-cutting keys, so the gate passes |
| C-2 `>=2 distinct evidence types` | **NO** — `claims_health.py` reports, never blocks. 24.2% compliance |
| C-2 evidence `type` from a closed vocabulary | **NO** — 111 free-text values |
| C-2 `confidence` ∈ TIER_1..3 | **NO** — 13 off-vocabulary values on disk |
| C-2 no `verdict` / no `HAVE|PARTIAL|NONE` in a claim | **NO** gate; currently true by accident (0 violations found) |
| C-2 `verification` present | **NO** — 14/351 (4.0%) |
| C-3 `evidence_claim_ids` required | **NO** — the field does not exist yet; 0 occurrences |
| C-3 cell writes go through a writer | **NO** — cells are hand-edited, no writer exists |

## 7b. Inventory: producers currently out of contract (measured 2026-07-25)

**No producer emits a `HAVE`/`PARTIAL`/`NONE` verdict.** Full-repo grep for `verdict` in `*.py` returns
~70 hits, all in `Zagentexecution/` analysis scripts, and all of them are *domain* verdicts about SAP
objects (`DRIFT DETECTED`, `ORPHANS_FOUND`, `ESCRITOR_REAL`, `GO_WITH_CONSTRAINTS`, `IDENTICAL`), never a
capability-coverage verdict. Every file that mentions `HAVE`/`PARTIAL`/`NONE` in `brain_v2/` is a
**reader/scorer**, not a producer: `capability_model/maturity_score.py:21`, `build_brain_state.py:567-568`,
`build_brain_index.py:31`, `graph_queries.py:329`, `scripts/build_maturity_dashboard.py:17-18`.
**Nothing to clean on this axis** — the "producer emitting a verdict" risk is real but not yet realized in
code. It is prevented going forward by C-2 §1.7.

**The violation that DOES exist is different and larger: producers write claims directly, setting
steward-only fields.** There is no `submit_claim` entry point anywhere in the repo — 16 one-off scripts
append to `claims.json` themselves, each hardcoding `id` and `status` (both FORBIDDEN by C-2 §1.7):

| producer | first offending line |
| --- | --- |
| `scripts/backfill_closing_activities.py` | :18 (`"id": 209`), :23 (`"status": "active"`) |
| `scripts/ingest_fx_revaluation_structured.py` | :25 (`"id": 205`), :30 (`"status"`, and `domain_axes` as a **list**, not the 3-axis object) |
| `Zagentexecution/_applied/from_scratch/add_session076_to_brain.py` | :115 |
| `Zagentexecution/_applied/incidents/INC-000005240_brain_v2_updates.py` | :33 |
| `Zagentexecution/_applied/mcp-backend-server-python/phase0_brain_update.py` | :24 |
| `Zagentexecution/_applied/mcp-backend-server-python/phase1_brain_companion_update.py` | :42 |
| `Zagentexecution/_applied/mcp-backend-server-python/phase1_final_brain_update.py` | :21 |
| `Zagentexecution/_applied/py_finance_investigation/add_sfsf_context.py` | :28 |
| `Zagentexecution/_applied/py_finance_investigation/fix_hr_workflows.py` | :134 |
| `Zagentexecution/_applied/py_finance_investigation/register_hr_workflows.py` | :129 |
| `Zagentexecution/_applied/scrp_temp/h48_final_brain_update.py` | :16 |
| `Zagentexecution/_applied/scrp_temp/h48_findings_update.py` | :13 |
| `Zagentexecution/_applied/session074_brain_claims.py` | :12 (`"id": next_id`), :27 |
| `Zagentexecution/_applied/session078_odp_compliance_brain.py` | :22, :47 |
| `Zagentexecution/_applied/update_brain_inc6313.py` | :147 |
| `Zagentexecution/_applied/update_brain_inc_budgetrate.py` | :112 |

These are ALREADY-APPLIED, one-shot historical scripts (`_applied/`); rewriting them changes nothing in
the data and would rewrite history. They are listed as **evidence of the failure mode**, not as a cleanup
backlog. The fix is forward-looking: a single `submit_claim` entry point (§8 item 1) so the next producer
has no reason to hand-roll one.

## 8. Pending (owned by other files / other agents)

1. **`brain_v2/validate_contracts.py`** — the C-2/C-3 gate, to be added as step 0b of `rebuild_all.py`.
   `rebuild_all.py` is owned by another Ola-2 agent; not touched here.
2. **Freeze an evidence-class vocabulary** in `ontology.json` (it is the vocabulary file) and map the
   111 free-text `type` values onto it, so §1.3 becomes checkable instead of gameable.
3. **Split the 4 dimension keys out of `ontology.cross_cutting_keys`** (`D_DATA`, `F_INTERFACE_FILE`,
   `G_CONFORMANCE`, `H_IMPROVE`) and re-tag the 22 claims that use a dimension as `domain`
   (ids 241-244, 247-248, 319-328, 335, 337-340, 347) onto a real domain + a `dimension` field.
   Requires a claims migration — steward-owned, one writer at a time.
4. **Backfill `cells_moved` as structured objects with `evidence_claim_ids`** in `applied_models.json`,
   starting from the 16 `capability_model.json` notes that already cite claim ids.
5. **`execution_backlog.json`**: give the 5 `research_tasks_followups` a `fills` field and normalize the
   2 shorthand values (`"E/F + B_CODE"`, `"F (file design)"`) to canonical dimension keys.
6. **Normalize `confidence`** on ids 31-43 and add `status` to ids 27-43 / 121-124.
