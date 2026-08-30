---
name: sap_validation_substitution
description: THE single entry point for UNESCO FI/FM validations and substitutions (OB28/GGB0, OBBH/GGB1, YRGGBS00, GB93*/GB92*, ZXFM* exits, YFMXCHK/YFMXCHKP/YXUSER control tables). Use whenever the question is "why was this posting blocked", "why did the account/field change by itself", "what validations exist", "can this fund post", or before touching ANY validation/substitution rule. Consolidates the completed analysis — the 12-step live validation map, the substitution steps that fire unconditionally, the 6-rule XCHECK multiplexer, and the bypass model — so no session re-derives it.
domains:
  functional: [FI, PSM]
  module: [FI-GL, FM]
  process: [posting, validation, substitution]
---

# SAP Validation & Substitution — UNESCO (unified skill, s111)

> **This analysis is DONE.** Everything below was measured live on P01 or read from extracted
> source. Do not re-derive; extend. Detail lives in the four source artifacts (§6); this skill
> is the map and the method.

## 1. Architecture — one form pool serves both mechanisms

```
T80D  ARBGB=GBLR  FORMPOOL=YRGGBS00   ← VALIDATION side (OB28/GGB0 rules)
T80D  ARBGB=GBLS  FORMPOOL=YRGGBS00   ← SUBSTITUTION side (OBBH/GGB1 rules)
```

- `YRGGBS00` = 1,592 lines, **69 FORMs** (`U100`–`U913` + `UXR1`/`UXR2`/`UZLS`/`UAEP`/`UIT1`/…).
  **8 FORMs can block a posting**; only `U913` carries a user bypass (YXUSER `XTYPE='BC'`).
  Full source: `Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt`.
- They are **independent**: a TCODE can trigger substitution without validation and vice versa
  (proven on F-53 in INC-000005240).
- On top of these, the **FM exits** (`ZXFM*` includes, FMDERIVE/account-assignment events) run
  their own validations/derivations inside the posting — invisible to GGB0/GGB1 analysis.

## 2. The VALIDATION side — VALID='UNES', BOOLCLASS 009 (12 live steps)

Mapped live from `GB93`/`GB931` (P01, 2026-04-09). Full table with prerequisites/checks/messages:
`knowledge/incidents/INC-000005240_xref_office_substitution.md` §3.4.3. The short version:

| Step | Fires on | Check | Msg |
|---|---|---|---|
| 001 | every UNES line | GSBER not in DAE/IBA/PAR/FEL/PDK | E ZFI 015 |
| 002 | **dead** (`BUDAT≤31.12.2011` + `=U913`) | constant FALSE | E ZFI 024 |
| 003 | GL ranges 6046/7034/7046 | `BLART='R1'` | E ZFI 021 |
| 004–008 | BLART/TCODE pairings (RE via MM, TV/TF via travel, ZP/CP via F110/F111, CA/CC via cash TCODEs) | TCODE whitelist | E ZFI 019/004 |
| 009 | `GEBER='185GEF0006'` | `=U916` | **I** ZFI 023 |
| 010 | RB/SR customer lines | XREF3 in expense-type list | E ZFI 011 |
| 011 | invoice-entry TCODEs + `KOART='K'` | `=U915` multi-bank | E ZFI 012 |
| 012 | invoice-entry TCODEs + `KOART='K'` | `=U917` SCB indicator | E ZFI 036 |

`U917` has **no** user bypass (zero `yxuser`/`xtype` in its body); of the 8 blocking routines only
`U913` does — and that bypass list is **empty** (claim 649).

## 3. The SUBSTITUTION side — SUBSTID='UNESCO'

- Step bodies in `GB922` (17 rows, Gold DB); booleans in `GB901`; **`GB905`/`GB921` come back
  EMPTY via RFC** — UNESCO does not use the standard step-header linking, so steps 005 (XREF1 via
  `UXR1`), 006 (XREF2 via `UXR2`), 007 (ZLSCH via `UZLS`) **fire unconditionally on every BSEG
  line at callpoint 3** (proven empirically via CDPOS).
- `UXR1` validates against `YFO_CODES.FOCOD` → **warning** ZFI w018. `UXR2` hard-errors only in
  the user-entered branch; its auto-write from `USR05` (`Y_USERFO` parameter) is **unvalidated**.
- FM derivations: `ZXFMDTU02` silently substitutes Fund/FundCenter for specific GLs (table in the
  autopsy §1); the 10-digit glue `ZXFMYU22` forces `POSID(10) = GEBER` for funds 101–112.

## 4. The control tables (extracted P01 2026-08-30 — Gold DB, bare-name = P01)

### `yfmxchk` (3,115 rows) — SIX rules multiplexed in the XCHECK letter [claim 648]
| XCHECK | Rows | Rule | Code |
| :---: | ---: | :--- | :--- |
| `Y` | 3,003 | **LIVE mass rule (11/2025, DBM):** fund blocked from FUTURE-year postings → E ZFI 009 | `ZXFMDTU02:320`, `YFM_ACCTCHK:112` |
| `T` | 38 | U913 special budget codes — **path dead** (step 002) | `YRGGBS00:961` |
| `F` | 35 | fund EXEMPT from remaining ZXFMDTU02 checks | `ZXFMDTU02:512` |
| `H` | 28 | fund exempt from TBP1C/BPJA budget-structure check | `ZXFMYU22:184` |
| `D` | 9 | **not funds**: FR/PO number thresholds (past-year commitment block) | `ZXFMDTU02:424` |
| `Z` | 2 | tech fund fully blocked (BFM 03/2024) | `ZXFMDTU02:306` |

### `yfmxchkp` (11 rows) — the FM fiscal gate, **currently OFF** [claim 650]
Readers only check CHTYP `FY`/`BB`/`BE` — all inactive. The 9 ACTIVE rows are `CHTYP='CM'`,
which **no code in the extracted corpus reads** (and `MONAT=00` would block nothing anyway).
Bypass = auth object `Y_FMUECLO` field `YFLAG`, **not** YXUSER.

### `yxuser` (1 row) — the bypass table [claim 649]
`FM`/`HIPER` only. Nobody holds `FRTL` (FR tolerance) or `BC` (U913). If a second row ever
appears, that is a control change worth an incident-grade look.

Refresher: `python Zagentexecution/sap_data_extraction/scripts/extract_yfmxchk_control_tables.py`

## 5. The method — "why was this posting blocked / changed?"

1. **Get the message class+number** from the user (ZFI nnn). ZFI 009 → FM exit (ZXFM*/YFM_ACCTCHK,
   §4); ZFI 015/019/021/004/011/012/036 → GB931 step (§2); ZFI w018/e018 → UXR1/UXR2 (§3).
2. **Check the control tables in the Gold DB first** (`yfmxchk`/`yfmxchkp`/`yxuser`) — most
   "mystery blocks" are a fund listed with the relevant XCHECK letter.
3. **Only then** read code: the exact FORM in `YRGGBS00_SOURCE.txt` or the ZXFM* include in
   `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/`.
4. For "field changed by itself": substitution side §3 — remember steps 005/006/007 fire on
   EVERY line; check `USR05` parameters (`Y_USERFO`) and `YFO_CODES`.
5. **Never modify OBBH/OB28 rules directly** — CTS + peer review; they hit ALL postings.

## 6. Source artifacts (the detail — load on demand)

1. `knowledge/incidents/INC-000005240_xref_office_substitution.md` §3.4 — full live rule map.
2. `knowledge/domains/PSM/EXTENSIONS/validation_substitution_autopsy.md` — ZXFM* business rules.
3. `knowledge/code_analysis_control_matrix.md` — per-object analysis status.
4. `.claude/skills/unesco_filter_registry/SKILL.md` — per-table filter semantics
   (YFMXCHK_XCHECK, YFMXCHKP_GATE, YXUSER_BYPASS entries).
5. Claims: 486 (YXUSER gates 5 routines), 648–650 (control tables), 651 (ZTHRFIORI_ATT_TY twin).
