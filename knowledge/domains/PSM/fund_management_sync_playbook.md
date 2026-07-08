---
name: Fund Management Sync Playbook — Master Data + Budget Envelope (P01 → D01/V01)
description: Canonical, empirically-verified playbook for replicating the SAP Fund Management model from P01 (source of truth) to a non-prod target (D01 dev / V01 validation). Covers BOTH FM master data (funds, fund centers, commitment items, functional areas, UNESCO Z tables) AND the budget envelope (the ENTR/B1 disponible assignment that makes a project spendable). Verified P01→D01 on 2026-06-29.
type: project
domain: PSM / Fund_Management
evidence_tier: TIER_1
created_session: s-2026-06-29
cross_links:
  - knowledge/domains/PSM/cost_recovery_avc_disponible_model.md      # the AVC/Disponible model (the "why")
  - knowledge/gold_db_table_catalog.md                                # gold table contract
  - Zagentexecution/tasks/2026_06_29_fm_model_sync/METHOD.md          # task-level run notes
  - .agents/skills/sap_master_data_sync/SKILL.md                      # FM extension of the master-sync skill
  - claims: [#283, #284, #286, #287, #288, #289, #290, #291, #292, #347, #348, #349, #350]
---

# Fund Management Sync Playbook — Master Data + Budget Envelope

> One reference for "bring a Fund Management area up to date in a non-prod system". Two halves:
> **(A) master data** (the objects exist) and **(B) budget envelope** (the objects have disponible to
> spend). Source = P01 (read-only). Target = D01 or V01. **Never write P01.**
> Reusable scripts: `Zagentexecution/tasks/2026_06_29_fm_model_sync/` (all `<TARGET>`-parameterized).

## Direction & ground rules
- P01 → target only. Read source via RFC over SNC/SSO.
- **Both P01 and D01/V01 reject ROWSKIPS** (SAIS secured wrapper) → read large FM tables `ROWCOUNT=0`
  partitioned by FIKRS; never paginate with ROWSKIPS. **The same SAIS wrapper also rejects `IN (...)`**
  (rc=5 OPTION_NOT_VALID "suspicious WHERE condition", confirmed live on P01 FMFINCODE 2026-07-07,
  claim #347) — use `LIKE` + client-side filter, or OR-chained equality, never a SQL `IN(...)` list.
- **"Active fund" = `DATBIS >= today`** (not a filter on one specific DATBIS literal; `31.12.9999` =
  permanent). Compute at query time — claim #350.
- **Reconcile writes should be SURGICAL, not full-field, when the target may carry its own legitimate
  test data.** Read the target's own current record first, override ONLY the drifted field(s) — see
  the `reconcile_633crp_v01.py` pattern below (claim #349). The generic `fund_reconcile.py` full-field
  copy remains valid where no target-local divergence exists (verified for D01).
- **Standard API, not table writes** — use SAP's own create/change FMs and the budget BAPI; never INSERT
  standard tables by hand (does not violate never-modify-standard-objects).
- **Verify by re-read, never by the return code.** Several FMs return empty messages / default-TESTRUN and
  silently no-op. Gold cache is key-only for some tables → not a valid write source; re-extract full-field live.
- **Gotcha — SAP amounts use TRAILING minus** (`75695.67-`); parse with sign-strip.

---

## PART A — Master data

Run order is dependency-driven: **fund centers → funds → Z tables** (funds reference the funds-center
addressing; create centers first).

| Object | Read (P01) | Write (target) | Script |
|--------|-----------|----------------|--------|
| FMFCTR + FMFCTRT + hierarchy | `FM_FUNDS_CTR_GET_DETAILS_RFC` | `FM_FUNDS_CTR_CREATE_RFC` | `fund_center_sync.py <TGT>` |
| FMFINCODE + FMFINT | `FM_FUND_GET_DETAIL_RFC` (or raw FMFINCODE) | `FM_FUND_CREATE_RFC` | `fund_sync.py <TGT>` |
| field reconcile (make identical) | raw FMFINCODE+FMFINT | `FM_FUND_CHANGE_RFC` | `fund_reconcile.py <TGT>` |
| fund family by prefix (e.g. CRP credit 633CRP9*) | raw | CREATE/CHANGE | `fund_family_sync.py <TGT> <prefix>` |
| YTFM_FUND_C5 / FUND_CPL / OUTPUT(_T) (own Z) | raw `RFC_READ_TABLE` | `RFC_ABAP_INSTALL_AND_RUN` INSERT | `z_tables_sync.py <TGT> <which>` |

**Critical gotchas (Part A):**
- **`FM_FUND_CREATE_RFC` / `FM_FUNDS_CTR_CREATE_RFC`: `I_FLG_TESTRUN` defaults to `'X'`.** Omitting it =
  silent simulation, zero rows written, `ET_MESSAGES` empty (looks like success). Always pass
  `I_FLG_TESTRUN=' '` + `I_FLG_COMMIT='X'`. ET_MESSAGES is empty even on a real create → raw read-back mandatory.
- **Fund-center hierarchy needs topological ordering** (`IS_FUNDS_CTR_HIVARNT` PARENT_ST must already exist
  in target) — process in waves (parents before children).
- **BOSS gotcha**: strip `BOSS_CODE/BOSSID/BOSSNAME/BOSSOT` — the responsible-person user may not exist in
  target → FM errors `User name X does not exist`.
- **`created` counter ≠ persisted**: `FM_FUND_GET_DETAIL_RFC` at a fixed `I_DATE` returns EMPTY for funds
  whose validity ends before that date → CREATE/CHANGE gets blank required fields and the FM rejects. Source
  from RAW FMFINCODE+FMFINT, sanitize `'00000000'` dates to `''`, check ET_MESSAGES (TYPE E/A/X), verify gap.
- **Budget-scope / validity locks**: `FM_FUND_CHANGE_RFC` refuses to shorten validity or change budget scope
  (overall↔annual) when budget exists — benign, leave as a justified exception.

**Scope lever — biennium C5/43**: biennium-linked dimensions (FMFINCODE/FMFINT, YTFM_FUND_C5, YTFM_FUND_CPL)
scope to the active set `YTFM_FUND_C5.C5_ID='43'` (2026-2027). Non-biennium dimensions (FMFCTR, YTFM_OUTPUT,
TFKB) sync the full current-master difference. **Only the differences (P01 minus target).**

**Result P01→D01 (s093):** biennium C5/43 complete — fund centers 135 (gap 0), funds 5,564 (gap 0), Z gaps 0,
field reconciliation 112/113 (1 SAP-blocked). See METHOD.md.

---

## PART B — Budget envelope (the disponible)

Master data alone does NOT make a project spendable. To spend, it needs **disponible** (AVC available).
The "why" is in `cost_recovery_avc_disponible_model.md`; the "how to load" is here.

**Two DISTINCT processes — do not conflate:**
1. **Assignment** (creates the disponible — "cuánto puede gastar"): `PROCESS=ENTR`, `VALTYPE=B1`,
   `BUDTYPE=3000`, at the control fund center + the fund's real commitment item(s) (usually **TC**+80, but
   some funds spread across detailed CIs/PC). Posted via **FMBB** / `BAPI_0050_CREATE`.
2. **Recovery** (separate, downstream): `COSD`/`CORV` (`BUDTYPE=4000`) + FI revenue postings (R1/JV).
   These MOVE against the disponible — they do NOT create it.

**Budget is ANNUAL** — each fiscal year needs its own disponible. A 2025 ENTR gives FMAVCT only RYEAR=2025;
it does NOT make the fund spendable in 2026. In P01 the next year arrives via **budget carryforward**
(residual prior→current). For a target, post the ENTR with `FISC_YEAR=<year>` (the active posting/test year).

**Where to read the source amount:** P01 FMBL where `PROCESS='ENTR' AND VALTYPE='B1' AND BUDTYPE='3000'`,
per fund (sum TVAL01..16 per address; trailing-minus → magnitude). Note BPGE/BPJA WRTTP43 = 0 for these
CR/cover funds (false-negative trap). Regular (non-CR) funds DO use WRTTP43 overall budget at the control
fund center (e.g. NAI ~93.8M across FP000001-FP000011) — a separate concern (claim #283).

**VERIFIED `BAPI_0050_CREATE` recipe** (script `budget_assign_entr.py <TGT> <test|commit> [FUND] [YEAR]`):
- HEADER: `FM_AREA='UNES', VERSION='000', DOCTYPE='2000', PROCESS='ENTR', DOCSTATE='1', DOCDATE=today` —
  **omit PSTNG_DATE** (budgetary ledger inactive → FMKU020).
- ITEM: `ITEM_NUM` (string `'001'`..), `FISC_YEAR`, `BUDCAT='9F'`, `BUDTYPE='3000'`, `FUND`, `FUNDS_CTR`,
  `CMMT_ITEM`, `FUNC_AREA`, `VALTYPE='B1'`, `TRANS_CURR='USD'`, `TOTAL_AMOUNT` (positive), `DISTKEY='1'`.
- Then `BAPI_TRANSACTION_COMMIT(WAIT='X')` (BAPI does not auto-commit). `TESTRUN='X'` first.
- Required-field gotchas in order: ITEM_NUM string → DOCSTATE='1' (FMKU048) → DISTKEY='1' (FMBAPI010) →
  no PSTNG_DATE (FMKU020).
- **Verify**: FMBL has the ENTR lines AND FMAVCT has rows for `RFUND`/`RYEAR` → disponible exists.

**Result P01→D01 (s093):** 5 CR test funds assigned for FY2025 (docs 2000000250-254) and FY2026
(docs 2000000255-259), 3,638,028 USD each year (567KEN2000 990,099 / 537RAF4006 450,000 / 218MAR2000 500,000 /
263KEN5000 1,120,400 / 235MAG5003 577,529). FMAVCT RYEAR=2026 now present → spendable in 2026. Full envelope
used (vs P01's carryforward residual) — the dev-enablement choice. Cover/credit funds 633CRP9* validity fixed
first (`fund_family_sync.py`).

---

## PART C — Refresh the gold (after the work)
Gold tracks **P01**, not the target. Refresh the FM master from P01 (delta-aware, registry-driven):
`python scripts/extraction/gold_refresh.py PSM_FM master_data` (also `text` / `totals` for budget tables).
pk-upsert for master/text, value-compare for totals. Audited in `_gold_sync_log`. Gold is LOCAL-ONLY
(~6.4GB, gitignored) — protected only by disk/offsite backup, never by git.

## Reusability for V01
Every script is `<TARGET>`-parameterized. For V01: add `SAP_V01_*` to the RFC `.env`, then run the same
sequence: `fund_center_sync.py V01` → `fund_sync.py V01` → `z_tables_sync.py V01 all` →
`fund_reconcile.py V01` → `fund_family_sync.py V01 633CRP9` → `budget_assign_entr.py V01 commit 2026`.

## V01 633CRP* validity alignment — result (2026-07-07, claims #347-#350)
Ran a SURGICAL validity-only variant instead of the generic full-field `fund_reconcile.py` for this
target: `Zagentexecution/tasks/2026_06_29_fm_model_sync/reconcile_633crp_v01.py` (+ diff probe
`Zagentexecution/mcp-backend-server-python/probe_633crp_p01_vs_v01.py`). Full-field would have
overwritten V01's own `ZZOUTPUT`/`ZZIBF` test-fixture values with P01's — those are deliberate V01
test data, not drift. Pattern: base = V01's own current FMFINCODE row, override ONLY DATAB/DATBIS from
P01, verify by raw re-read (never trust `ET_MESSAGES`, per the `FM_FUND_CREATE_RFC`/`FM_FUND_CHANGE_RFC`
TESTRUN-default gotcha above).
- **Before**: P01 282 funds 633CRP* (280 UNES + 1 ICBA 633CRP9003 + 1 MGIE 633CRP9100) vs V01 203 —
  9 identical, 194 differ (validity, mostly the 2026-2027 biennium DATBIS extension not replicated),
  79 only-in-P01 (not created — user choice), 0 only-in-V01.
- **After**: 194 updated, still-drift=0, fm-errors=0. The 79 P01-only funds remain uncreated (deliberate).
- **Active-fund gap** (DATBIS>=today definition, claim #350): P01 254 active vs V01 185 active; 69 of the
  79 P01-only funds are themselves still active (the other 10 are already expired) — user chose not to
  create them this session.
- Recommend this surgical pattern as the DEFAULT for any future V01 reconcile where target-local test
  data may exist; keep full-field for D01 unless a similar case is found there.
