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
# 3) Z tables (YTFM_FUND_C5 / FUND_CPL / OUTPUT) — direct INSERT via RFC_ABAP_INSTALL_AND_RUN  [pending]
```

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

## Result P01 → D01 (s093 2026-06-29)

- Fund centers: 135 created (5 E2E + 130 mass, 4 waves), **gap = 0** verified.
- Funds C5/43: 5,349 (+ 10 E2E) — see `fund_sync_D01.log`.
