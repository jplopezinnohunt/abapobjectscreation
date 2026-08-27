# sap_master_data_sync — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

## Field-by-Field Verification Pattern

After test insert of 1 record, compare ALL fields between P01 and D01:

```python
for sys_id in ['P01', 'D01']:
    guard = get_connection(sys_id)
    result = guard.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|',
        FIELDS=[{'FIELDNAME': f} for f in all_fields],
        OPTIONS=[{'TEXT': f"SAKNR = '{test_saknr}'"}],
        ROWCOUNT=1)
    # Parse and compare field by field
    # Expected: all functional fields match, only ERDAT/ERNAM differ
```

**Expected differences (OK):**
- ERDAT: P01 shows original creation date, D01 shows today
- ERNAM: P01 shows original creator, D01 shows JP_LOPEZ

**Unexpected differences (NOT OK):**
- Any functional field mismatch = bug in INSERT logic

## UNESCO Context

- **Chart of Accounts:** UNES (single, shared across all company codes)
- **Controlling Areas:** IBE, ICBA, ICTP, IIEP, MGIE, UBO, UIL, UIS, UNES, US01
- **Company Codes:** 9 in P01, 10 in D01 (STEM is D01-only, new company code)
- **Account Groups:** BANK, COLL, OTHR, P&L, UNDP (T077S)
- **Typical gap:** ~50-70 GL accounts, ~25 cost elements accumulate in P01 between syncs

## Session Log

| Date | Tables | Records | Result |
|------|--------|---------|--------|
| 2026-04-03 | SKA1, SKAT, SKB1, CSKA, CSKU, CSKB | 880 | Gap = 0, all verified |
| 2026-06-29 | FMFINCODE, FMFINT, FMFCTR, FMFCTRT, FMCI, YTFM_FUND_C5, YTFM_FUND_CPL | ~63K gap counted (~16.7K scoped C5/43) | Gap analysis + write channels verified (claim #283/#284) |
| 2026-06-29 | FMFINCODE + FMFINT (E2E test) | 10 funds | E2E PROVEN: FM_FUND_CREATE_RFC (TESTRUN=' ') → 10/10 created in D01, verified field-by-field vs P01. Ready for mass C5/43 (5,349 funds) |

## FM Model Extension (PSM/FM domain) — Evaluated s093 2026-06-29

The proven GL/CE sync pattern extends to Fund Management master data, with **important differences
in write method** per SAP object type.

### Gap summary (claim #283, point-in-time 2026-06-29)

| SAP table | Gold DB table | P01 count | D01 count | GAP | Notes |
|-----------|--------------|-----------|-----------|-----|-------|
| FMFINCODE | funds | 67,408 | 47,885 | **19,523** | UNES=14,809 dominant |
| FMFINT | FMFINT | 67,410 | ~47,887 | **19,523** | mirrors FMFINCODE |
| FMFCTR | fund_centers | 787 | 655 | **135** | UNES=110; D01 has +3 dev-only |
| FMFCTRT | fund_centers_text | 787 | 655 | **135** | mirrors FMFCTR |
| FMCI | commitment_items | 205 | 232 | 0 P01-only | D01 has +27 dev-only |
| FMCIT | commitment_items_text | 205 | 232 | 0 P01-only | same |
| TFKB | functional_areas | 9 | 9 | 0 | identical |
| YTFM_FUND_C5 | ytfm_fund_c5 | 17,598 | 100 | **17,564** | UNES=14,214 dominant |
| YTFM_FUND_CPL | ytfm_fund_cpl | 6,368 | 24 | **6,345** | UNES=6,234 |
| YTFM_OUTPUT | ytfm_output | +6 gap | | 6 | low priority |
| YTFM_C5 | ytfm_c5 | — | — | 0 | no sync needed |
| YTFM_WRTTP_GR | ytfm_wrttp_gr | — | — | 0 | no sync needed |

### Write method by object type — VERIFIED EMPIRICALLY ON D01 (s093 2026-06-29)

**SUPERSEDES the earlier "direct INSERT for FMFINCODE" guess.** Standard FM master must use the
standard RFC-enabled create FMs (probed REMOTE-OK on D01) — NOT flat table INSERT, which would leave
the BCS model inconsistent (derivation, validity, number ranges, hierarchy). This does NOT violate the
never-modify-standard-objects rule: we call SAP's own API, we do not write standard tables by hand.

| Object | Write method (verified) | Why |
|--------|-------------|-----|
| FMFINCODE + FMFINT | **`FM_FUND_CREATE_RFC`** (one call: `IS_FUND_DATA`+`IS_FUND_TEXT`) | Read source via `FM_FUND_GET_DETAIL_RFC` (P01). Map `FMFINCODE`→`FMFUND_DATA`, `FMFINT`→`FMFUND_TEXT` by field name (subset). Key via `I_FM_AREA`+`I_FUND` (external assignment = same FINCODE as P01). |
| FMFCTR + FMFCTRT + hierarchy | **`FM_FUNDS_CTR_CREATE_RFC`** (`IT_FUNDS_CTR_DATA`+`IT_FUNDS_CTR_TEXT`+`IS_FUNDS_CTR_HIVARNT`) | Handles hierarchy variant natively. Read via `FM_FUNDS_CTR_GET_DETAILS_RFC`. **E2E not yet run — test before mass (hierarchy risk).** |
| YTFM_FUND_C5 / FUND_CPL / OUTPUT(_T) | Direct INSERT via `RFC_ABAP_INSTALL_AND_RUN` | Z/Y own objects — INSERT is the correct path |

#### ⛔ GOTCHA — `I_FLG_TESTRUN` defaults to `'X'` (false-positive create)

Both `FM_FUND_CREATE_RFC` and `FM_FUNDS_CTR_CREATE_RFC` have `I_FLG_TESTRUN` **default = `'X'`**. If you
pass only `I_FLG_COMMIT='X'` and omit TESTRUN, the FM **simulates and writes NOTHING** — yet returns
`ET_MESSAGES` EMPTY (no error, no success). Looks like success, persists zero rows.
- **To persist:** pass `I_FLG_TESTRUN=' '` AND `I_FLG_COMMIT='X'`.
- **ET_MESSAGES is empty even on a real create** → "OK"/subrc proves nothing. **Raw read-back of
  FMFINCODE is mandatory** (same class of defect as MODIFY-vs-UPDATE persistence lesson).
- E2E proven s093: 10/10 C5/43 funds created in D01 and verified field-by-field (TYPE/PROFIL/DATAB/
  DATBIS/FINUSE/ZZOUTPUT) + FMFINT text against P01.

#### Scope lever — biennium C5/43
Dimensions WITH a biennium link (FMFINCODE/FMFINT, YTFM_FUND_C5, YTFM_FUND_CPL) scope to the active
biennium via the YTFM_FUND_C5 `C5_ID='43'` (2026-2027) fund set → ~16.7K rows (−74% vs full 63K), and
D01 is near-empty for the current biennium (only 115 of 5,464 active funds present). Dimensions WITHOUT
a biennium (FMFCTR, YTFM_OUTPUT, TFKB) cannot be scoped — sync the full current-master gap.

### CRITICAL: Gold DB funds table is KEY-ONLY (claim #284)

The gold `funds` table has only 5 columns: FIKRS, FINCODE, TYPE, ERFDAT, ERFNAME.
Real FMFINCODE has ~30 fields. **DO NOT use the Gold DB cache as the write source.**
The write phase MUST re-extract FMFINCODE live from P01 with full field list before INSERT to D01.

### Extraction constraint (claim #244 — applies to BOTH P01 and D01)

Both P01 and D01 RFC_READ_TABLE are wrapped by class SAIS which **REJECTS ROWSKIPS** (rc=5,
OPTION_NOT_VALID). Confirmed empirically on D01 FMFINCODE/FMFINT during s093.

```python
# CORRECT pattern for FM tables on P01 or D01
for fikrs in ['IBE', 'ICBA', 'ICTP', 'IIEP', 'MGIE', 'UBO', 'UIL', 'UIS', 'UNES']:
    rows = guard.call('RFC_READ_TABLE',
        QUERY_TABLE='FMFINCODE',
        OPTIONS=[{'TEXT': f"FIKRS = '{fikrs}'"}],
        ROWCOUNT=0,       # ROWCOUNT=0 = all rows
        ROWSKIPS=0,       # NEVER set > 0
        FIELDS=[...])     # full field list from live extraction
```
