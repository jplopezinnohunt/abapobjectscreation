---
name: Technical Spec — Y_FMKU_0050_CREATE_WITH_COMMIT (CRP cost-recovery budget posting)
description: Verified RFC interface (read live from P01) of the custom FM that creates FM budget entry documents (object 0050). Function group Y_FM_BAPI. Maps the CRP monthly supplement (SUPL/9F/B1/TC) to the call.
type: project
created: 2026-06-26
source: P01 live RFC (RFC_GET_FUNCTION_INTERFACE + DD03L), read-only
---

# Y_FMKU_0050_CREATE_WITH_COMMIT — Technical Specification

## 1. Identity (verified live on P01)
| | |
|---|---|
| Function module | `Y_FMKU_0050_CREATE_WITH_COMMIT` |
| Program | `SAPLY_FM_BAPI` |
| **Function group** | **`Y_FM_BAPI`** |
| RFC-enabled | **Yes** (`TFDIR-FMODE = 'R'`) |
| Wraps | standard **`BAPI_0050_CREATE`** (FM Budgeting: create budgeting/entry document, object type 0050) + `BAPI_TRANSACTION_COMMIT` (the `_WITH_COMMIT`) |

It creates **FM budget documents** (FMBH header + FMBL lines). Process (ENTR/SUPL/TRAN/RETN) is driven by `HEADER_DATA-PROCESS`, so the *same* FM posts an original budget (ENTR) **or** the CRP monthly supplement (SUPL).

## 2. Full interface (RFC_GET_FUNCTION_INTERFACE)
| Class | Parameter | Type/Table | Opt | Notes |
|---|---|---|---|---|
| IMPORTING | `HEADER_DATA` | `BAPI_0050_HEADER` | no | document header |
| IMPORTING | `HEADER_DATA_ADD` | `BAPI_0050_HEADER_ADD` | yes | extra header attrs |
| IMPORTING | `LANGUAGE` | `BAPI_0050_FIELDS` | yes | |
| IMPORTING | `TESTRUN` | `BAPI_0050_FIELDS` | yes | **DEFAULT `'X'` ⇒ simulation. Set to `' '` to really post.** |
| TABLES | `ITEM_DATA` | `BAPI_0050_ITEM` | no | one row per budget line |
| TABLES | `PERIOD_DATA` | `BAPI_0050_PERIOD` | yes | amount per budgeting period |
| TABLES | `LONG_TEXT` | `BAPI_0050_LONGTEXT` | yes | |
| TABLES | `SENDER_ITEM_DATA` | `BAPI_0050_ITEM` | yes | transfers only (TRAN) |
| TABLES | `SENDER_PERIOD_DATA` | `BAPI_0050_PERIOD` | yes | transfers only |
| TABLES | `EXTENSION_IN` | `BAPIPAREX` | yes | |
| TABLES | `RETURN` | `BAPIRET2` | no | **check: type E/A = failure** |
| EXPORTING | `DOCUMENTNUMBER` | `BAPI_0050_FIELDS` | | created doc no |
| EXPORTING | `DOCUMENTYEAR` | `BAPI_0050_FIELDS` | | |
| EXPORTING | `FMAREA` | `BAPI_0050_FIELDS` | | |

## 3. Structure field lists (DD03L, verified)

### HEADER_DATA — `BAPI_0050_HEADER`
| Field | Data elem | Type | Len | CRP value |
|---|---|---|---|---|
| `FM_AREA` | FIKRS | CHAR | 4 | `UNES` |
| `VERSION` | BUKU_VERSION | CHAR | 3 | `000` |
| `DOCDATE` | BP_BLDAT | DATS | 8 | month-end e.g. `20250131` |
| `PSTNG_DATE` | BUDAT | DATS | 8 | month-end |
| `DOCTYPE` | BUED_DOCTYPE | CHAR | 4 | `1000` |
| `DOCSTATE` | BUED_DOCSTATE | CHAR | 1 | `1` (posted) |
| `PROCESS` | BUKU_PROCESS_UI | CHAR | 4 | **`SUPL`** (supplement) — `ENTR` for original |
| `EXTERNAL_NUMBER` | BUED_EXT_DOCNR | CHAR | 10 | optional |

### ITEM_DATA — `BAPI_0050_ITEM` (one row per office/fund line)
| Field | Data elem | Type | Len | CRP value |
|---|---|---|---|---|
| `ITEM_NUM` | BUED_DOCLN | CHAR | 6 | `000001`, `000002`… |
| `FISC_YEAR` | GJAHR | NUMC | 4 | `2025` |
| `FUND` | BP_GEBER | CHAR | 10 | `633CRP****` |
| `FUNDS_CTR` | FISTL | CHAR | 16 | office, e.g. `DAK` |
| `CMMT_ITEM` | FM_FIPEX | CHAR | 24 | `TC` |
| `FUNC_AREA` | FM_FAREA | CHAR | 16 | blank |
| `GRANT_NBR` | GM_GRANT_NBR | CHAR | 20 | blank |
| `MEASURE` | FM_MEASURE | CHAR | 24 | blank |
| `BUDCAT` | BUKU_BUDCAT | CHAR | 2 | `9F` (payment budget) |
| `BUDTYPE` | BUKU_BUDTYPE | CHAR | 4 | budget type (per config) |
| `VALTYPE` | BUKU_VALTYPE | CHAR | 2 | `B1` |
| `BUDGET_PERIOD` | FM_BUDGET_PERIOD | CHAR | 10 | per config (often blank) |
| `TOTAL_AMOUNT` | BAPICURR_D | DEC | 23 | recovered amount (= Σ FI `WRTTP=66`) |
| `TRANS_CURR` | TWAER | CUKY | 5 | `USD` |
| `TRANS_CURR_ISO` | ISOCD | CHAR | 3 | `USD` |
| `DISTKEY` | BUKU_SPRED | CHAR | 4 | blank (amount given by period) |
| `ITEM_TEXT` | SGTXT | CHAR | 50 | optional |

### PERIOD_DATA — `BAPI_0050_PERIOD` (amount by period)
| Field | Data elem | Type | Len | CRP value |
|---|---|---|---|---|
| `ITEM_NUM` | BUED_DOCLN | CHAR | 6 | matches the item |
| `BUDGETING_PERIOD` | BUKU_PERIOD | NUMC | 3 | **`016`** (annual bucket, per real FMBL) |
| `PERIOD_AMOUNT` | BAPICURR_D | DEC | 23 | same as `TOTAL_AMOUNT` |

## 3a. What the wrapper actually does (verified source, `RPY_PROGRAM_READ`)
The Z/Y function is a **thin pass-through to standard `BAPI_0050_CREATE`** plus 3 things:
```abap
FUNCTION Y_FMKU_0050_CREATE_WITH_COMMIT.
  " (1) YEAR-CLOSE GUARD — read the budget checkpoint year for this FM area
  SELECT SINGLE GJAHR INTO W_FYEAR FROM YFMXCHKP
    WHERE BUKRS = HEADER_DATA-FM_AREA AND CHTYP = 'CM' AND ACTIV = 'X'.
  IF sy-subrc = 0.
    LOOP AT ITEM_DATA WHERE FISC_YEAR <= W_FYEAR.  W_STOP = 'X'.  ENDLOOP.
  ENDIF.

  IF W_STOP IS INITIAL.
    CALL FUNCTION 'BAPI_0050_CREATE'          " (2) pass EVERYTHING through 1:1
      EXPORTING LANGUAGE=LANGUAGE HEADER_DATA=HEADER_DATA
                HEADER_DATA_ADD=HEADER_DATA_ADD TESTRUN=TESTRUN
      IMPORTING FMAREA=.. DOCUMENTYEAR=.. DOCUMENTNUMBER=..
      TABLES ITEM_DATA=.. SENDER_ITEM_DATA=.. PERIOD_DATA=..
             SENDER_PERIOD_DATA=.. LONG_TEXT=.. EXTENSION_IN=.. RETURN=RETURN.
  ELSE.
    RETURN += "Impossible to create budget documents in Fiscal Year <W_FYEAR> (and earlier)".
  ENDIF.

  IF DOCUMENTNUMBER IS NOT INITIAL.  COMMIT WORK.  ENDIF.   " (3) the _WITH_COMMIT
  CALL FUNCTION 'DEQUEUE_ALL' EXPORTING _SYNCHRON='X'.       "     + release locks
ENDFUNCTION.
```
**Conclusion: the value-feeding rules are 100% the standard `BAPI_0050_CREATE` rules** — the wrapper adds no field mapping, only a guard + commit + dequeue.

**Year-close guard (live `YFMXCHKP`, CHTYP='CM', ACTIV='X' — read 2026-06-26):** GJAHR = **2025** for ALL FM areas (UNES, IIEP, ICTP, IBE, ICBA, MGIE, UBO, UIL, UIS). ⇒ **today this FM rejects any line with `FISC_YEAR ≤ 2025`** ("Impossible to create budget documents in Fiscal Year 2025 and earlier"). Only **FY2026+** is postable. You cannot backfill the 2025 CRP supplements through this FM anymore — that window is closed.

## 3b. Standard `BAPI_0050_CREATE` mapping rules (how to feed values)
- **PROCESS** (header) = the budget process UI code: `ENTR` enter/original · `SUPL` supplement · `RETN` return · `TRAN` transfer (transfer also needs the `SENDER_*` tables). This single field switches the whole semantic.
- **BUDCAT** (item) = budget category: `9F` payment budget (UNESCO uses this for CRP) · `9G`/other = commitment budget. **BUDTYPE** = the budget type within the category (config-driven; can be left to the document type default).
- **VALTYPE** (item) = value type: `B1` (the released/original value used here).
- **Amount feed — two mutually consistent ways:**
  1. **Explicit period** (what CRP uses): set `ITEM-TOTAL_AMOUNT` AND give `PERIOD_DATA` rows (`ITEM_NUM` + `BUDGETING_PERIOD='016'` + `PERIOD_AMOUNT`). `TOTAL_AMOUNT` must equal Σ `PERIOD_AMOUNT` for that item.
  2. **Distribution key**: set only `ITEM-TOTAL_AMOUNT` + `ITEM-DISTKEY` (`BUKU_SPRED`) and let SAP spread across periods. Leave `PERIOD_DATA` empty.
- **ITEM ↔ PERIOD link** is by `ITEM_NUM` — keep them identical across the two tables.
- **Currency**: `TRANS_CURR` + `TRANS_CURR_ISO` (`USD`). Sign: supplement positive, return negative.
- **Address** = `FUND` + `FUNDS_CTR` + `CMMT_ITEM` (+ `FUNC_AREA`/`GRANT_NBR`/`MEASURE`/`BUDGET_PERIOD` if used). Must be a valid budget address in FMDERIVE/master data or the BAPI returns an error in `RETURN`.
- Standard callers to study for examples: tcode **`FMBBC`/`FMBB`** (Budgeting Workbench), program **`RFFMB_BUDGET_TRANSFER`**, and the standard BAPI test in SE37 (F8) — all populate the same `BAPI_0050_HEADER`/`_ITEM`/`_PERIOD`.

## 4. Call pattern — CRP monthly supplement (pyrfc)
```python
header = {
    'FM_AREA':'UNES', 'VERSION':'000', 'PROCESS':'SUPL',
    'DOCTYPE':'1000', 'DOCDATE':'20250131', 'PSTNG_DATE':'20250131',
}
items, periods = [], []
for i,(fund,office,amount) in enumerate(month_lines, start=1):       # from FI WRTTP=66 agg
    ln = '%06d'%i
    items.append({'ITEM_NUM':ln,'FISC_YEAR':'2025','FUND':fund,'FUNDS_CTR':office,
                  'CMMT_ITEM':'TC','BUDCAT':'9F','VALTYPE':'B1',
                  'TOTAL_AMOUNT':amount,'TRANS_CURR':'USD','TRANS_CURR_ISO':'USD'})
    periods.append({'ITEM_NUM':ln,'BUDGETING_PERIOD':'016','PERIOD_AMOUNT':amount})

r = conn.call('Y_FMKU_0050_CREATE_WITH_COMMIT',
    HEADER_DATA=header, ITEM_DATA=items, PERIOD_DATA=periods,
    TESTRUN='X')                       # 'X' = simulate; '' = post for real
ret = [x for x in r['RETURN'] if x['TYPE'] in ('E','A')]
assert not ret, ret                    # any E/A = rejected
print(r['DOCUMENTNUMBER'], r['DOCUMENTYEAR'])
```

## 5. Rules / gotchas
1. **`TESTRUN` defaults to `'X'`** — without explicitly passing `''` you only simulate. Always simulate first, inspect `RETURN`, then post.
2. **A real posting is a WRITE.** Per project rules: **never post on P01**; budget docs are created only on **D01** and only through the gated path (`Zagentexecution/abap_deploy/deploy_object.py` discipline) with PRE/POST readback. Today these CRP docs are posted by the budget office via **FMBB (TECHORG=BWB)**; this FM is the *programmatic* equivalent.
3. `RETURN` must be checked for `TYPE in (E,A)`; the commit is internal, so a failed call may still have side effects — always testrun first.
4. `PROCESS='SUPL'` for the monthly recovery supplement; `ENTR` for original budget; `TRAN` uses the `SENDER_*` tables.
5. Amount sign: supplements are positive; returns (`RETN`) negative.

## 6. Evidence
- Live P01 RFC: `RFC_GET_FUNCTION_INTERFACE` (FM=Y_FMKU_0050_CREATE_WITH_COMMIT) + `DD03L` for the 3 structures, read-only, 2026-06-26.
- `read_fm_interface.py` (this task folder).
- Confirms KU-2026-094: the FM = standard `BAPI_0050_CREATE` wrapper that writes FMBH/FMBL.
