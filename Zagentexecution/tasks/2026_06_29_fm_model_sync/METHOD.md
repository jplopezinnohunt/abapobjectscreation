# FM Model Master-Data Sync — P01 → D01 / V01

Reusable method to align the Fund Management master model from P01 (production, read-only source)
to a target dev/validation system. Proven P01→D01 (s093, 2026-06-29). **Same scripts run P01→V01**
by changing the target argument (requires `SAP_V01_*` in the RFC `.env`).

## Run order (dependency-driven)

```bash
# 1) Fund centers FIRST — funds reference the funds-center addressing; create centers before funds.
python fund_center_sync.py D01        # or V01
# 2) Funds (scope = current biennium C5/43)
python fund_sync.py D01               # or V01
# 3) Z tables (YTFM_OUTPUT now; FUND_C5/CPL after funds load) — direct INSERT
python z_tables_sync.py D01 output      # then: fundc5 / cpl  (after funds done)
# 4) Field-level reconcile of biennium funds present in BOTH but drifted (make D01 == P01)
python fund_reconcile.py D01            # or V01  — uses FM_FUND_CHANGE_RFC
```

## Field reconciliation (make biennium data identical, not just present)

`fund_reconcile.py` compares all functional FMFINCODE fields for C5/43 funds in both systems and
updates D01 to match P01 via **`FM_FUND_CHANGE_RFC`** (same interface + TESTRUN-default gotcha as create).
Result P01→D01 s093: 113 drifted → **112 reconciled, 1 blocked**.

Reconcile-specific gotchas:
- **Source from RAW tables, not `FM_FUND_GET_DETAIL_RFC`.** GET_DETAIL needs `I_DATE` *within* the
  fund's validity; a hardcoded date past `DATBIS` returns an EMPTY record → CHANGE fails on required
  fields (DATAB/DATBIS/BEZEICH). Read FMFINCODE + FMFINT raw instead.
- **pyrfc rejects `'00000000'` for DATS fields.** Raw read returns empty dates as `'00000000'`; convert
  to `''` before the call (DATAB/DATBIS/DATE_EXP/DATE_CAN).
- **Budget-scope is locked once budget exists.** `FM_FUND_CHANGE_RFC` errors *"Change of budget scope
  from overall to annual is not allowed"* (1 fund, UNES 3210111232) — a genuine SAP business rule, not
  a tool limit. Leave as a justified exception.

## Verified write channels (NOT flat INSERT for standard master)

| Object | Read source (P01) | Write channel (target) |
|--------|-------------------|------------------------|
| FMFINCODE + FMFINT (funds) | `FM_FUND_GET_DETAIL_RFC` | `FM_FUND_CREATE_RFC` |
| FMFCTR + FMFCTRT + hierarchy | `FM_FUNDS_CTR_GET_DETAILS_RFC` | `FM_FUNDS_CTR_CREATE_RFC` |
| YTFM_* (own objects) | `RFC_READ_TABLE` full cols | `RFC_ABAP_INSTALL_AND_RUN` INSERT |

Standard API (not table writes) → does not violate never-modify-standard-objects; fills derivation,
validity, number ranges, hierarchy correctly.

## Gotchas (all empirically hit s093)

1. **`I_FLG_TESTRUN` defaults to `'X'`** on both create FMs. Omitting it = silent simulation, **zero
   rows written, ET_MESSAGES empty** (looks like success). Always pass `I_FLG_TESTRUN=' '` +
   `I_FLG_COMMIT='X'`.
2. **ET_MESSAGES is empty even on a real create** → "OK"/subrc proves nothing. **Raw read-back of the
   target table is mandatory** (same class as the MODIFY-vs-UPDATE persistence lesson).
3. **Fund-center hierarchy needs topological ordering.** A node can be created only after its
   `PARENT_ST` exists in target. Process in waves; some parents are themselves in the missing set
   (16/135 for D01 → 4 waves).
4. **BOSS gotcha.** Fund centers carry `BOSSID` (responsible person); if that user is absent in target
   the FM errors `User name X does not exist`. Strip `BOSS_CODE/BOSSID/BOSSNAME/BOSSOT` (cosmetic).
5. **Both P01 AND D01 reject ROWSKIPS** (SAIS secured wrapper) → read large FM tables `ROWCOUNT=0`
   partitioned by FIKRS, never paginate with ROWSKIPS.
6. **Gold cache is key-only** for funds/fund_centers → never a write source; re-read full-field live from P01.

## Scope lever — biennium C5/43

Biennium-linked dimensions (FMFINCODE/FMFINT, YTFM_FUND_C5, YTFM_FUND_CPL) scope to the active set
`YTFM_FUND_C5.C5_ID='43'` (2026-2027). Non-biennium dimensions (FMFCTR, YTFM_OUTPUT, TFKB) sync the
full current-master difference — **only the differences (P01 minus target)**, no usage filters.

## Result P01 → D01 (s093 2026-06-29) — biennium C5/43 COMPLETE

| Component | Result |
|-----------|--------|
| Fund centers FMFCTR + text + hierarchy | gap **0** (135 created, 4 topo waves) |
| Funds FMFINCODE + FMFINT (C5/43) | gap **0** (5,338 mass + 226 short-validity raw-sourced + 10 E2E) |
| Fund field reconciliation (make identical) | 113 drift → **112 fixed**, 1 SAP-blocked |
| YTFM_OUTPUT / OUTPUT_T | gap **0** (6+6) |
| YTFM_FUND_C5 (C5_ID=43) | gap **0** (5,579) |
| YTFM_FUND_CPL | gap **0** (241) |

**The 1 exception:** UNES `3210111232` — `FM_FUND_CHANGE_RFC` blocks the budget-scope change
(overall→annual) because budget exists. Genuine SAP business rule; left as a justified exception.

**Critical lesson — `created` counter ≠ persisted.** First fund_sync pass reported created=5,338/failed=0
but real gap was 226: GET_DETAIL at a fixed `I_DATE` returned EMPTY for funds whose validity ended
before that date → CREATE got blank required fields and the FM rejected (ET_MESSAGES not checked).
Fix: source from RAW FMFINCODE+FMFINT, sanitize '00000000' dates, and CHECK ET_MESSAGES (TYPE E/A/X).
Verification is by re-read gap, never by the create counter.
