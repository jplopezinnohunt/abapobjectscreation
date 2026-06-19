# SAP Config-Frontier Extraction — closing the last brain hypotheses (2026-06-19)

**System:** P01 (production, client 350) · **Method:** `RFC_READ_TABLE` over SNC/SSO (read-only, compliant — no writes, no ADT) · **Sink:** `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` · **Manifest:** golden table `_config_frontier_manifest` (every probed table incl. empty/absent) · **Scripts:** `Zagentexecution/sap_data_extraction/scripts/{probe_config_tables,extract_config_frontier_tables,inspect_config_frontier,probe_config_supplement,extract_config_frontier_supplement}.py`

**Result:** 61 new config tables landed (~13,794 rows). Golden DB 225 → **286 tables**. Every figure below is **MEASURED** from P01 unless tagged otherwise. Emptiness/absence is recorded as first-class evidence.

> ⚠️ Two of the brain's assumed object names were **wrong for ECC 6.0 EHP8** and are corrected here: there is **no `FMDT_FIELD`/`FMDT_STEP`** (FM derivation lives in the generic Derivation-Tool `TABADR*` tables) and **no custom splitting method `Z000000012`** (only SAP-standard `0000000001`/`0000000012`, and splitting is off anyway).

---

## HYP-018 / CLM-012/024 — Is GMDERIVE activated? → **NO (GM not in productive use)**

- **No `GMDT_FIELD`/`GMDT_STEP`/`GMDS` tables exist** in the DD02L catalog (absent).
- The GM derivation strategy **`GMDT` IS registered** in the shared Derivation-Tool framework: `fmderivefuncid` has 5 `APPL='GM' STRATEGY_ID='GMDT'` rows (functions `FMDT_COMPARE_VALUES`, `FMDT_CONVERSION_EXIT_ALPHA_OUT`, `FMDT_CONVERSION_WBS_INT_TO_EXT`, `GMDT_READ_FMRE_ASSIGNMENT`, `GMDT_READ_PO_ASSIGNMENT`).
- **But Grants Management has zero master data: `GMGR` = 0 rows, `GMIA` = 0 rows.**

**Verdict:** GM derivation is *delivered/registered* but **effectively inactive** — there are no grants to derive for. GMDERIVE is not a productive engine at UNESCO. CLM-012/024 (GM-activation feasibility) should treat GM as greenfield, not "already running".

---

## HYP-008 / OI-FI-01 — Document-splitting impact (100K+ FI postings/yr) → **NO IMPACT (splitting OFF; classic G/L)**

Decisive activation probes (live, not persisted):
- **`FAGL_ACTIVEC` = TABLE_WITHOUT_DATA** → New G/L **not activated**.
- **`FAGL_SPLIT_ACTC` = TABLE_WITHOUT_DATA** → Document splitting **not activated** for any company code.
- **`FAGLFLEXT` = 0 rows**, **`FMGLFLEXT` = 0 rows** (new-G/L totals empty), while classic **`GLT0` is populated** (already in golden as `glt0_p01`).

Customizing reality:
- `t8g17` (splitting **methods**) = **empty**; `t8g40` (splitting **rules**) = **empty**.
- The populated `t8g20/t8g21/t8g21a` rows are **SAP-standard delivered** content for methods `0000000001` and `0000000012` — **method `Z000000012` does not exist** in P01.

**Verdict:** UNESCO runs **classic G/L** (GLT0). Document splitting is not active → there is **no doc-splitting impact** on the FI posting stream. HYP-008 is **refuted/closed**; OI-FI-01 (splitting criteria) is moot under classic G/L.

---

## F3 — New-G/L ledger / parallel-ledger backbone → **classic G/L + FI-SL special ledgers (no new-G/L postings)**

`t881` (44 ledger definitions) shows the FI-SL ledger landscape:

| Ledger | Totals table | App/Sub | Notes |
|---|---|---|---|
| `00` | **GLT0** | FI/GL | Classic G/L (the live one) |
| `0L` | FAGLFLEXT | FI/PSX | `XLEADING='X'`, `GLFLEX='1'` — leading new-G/L ledger **defined but empty** |
| `0D/0M/1D/1L` | FAGLFLEXT | FI/PSX | new-G/L ledgers, **all empty** |
| `3A/3B` | COFIT | CO/RCL | Reconciliation ledger (CO↔FI) |
| `8A/8C` | GLPCT | EC/PCA | Profit-center ledger |
| `10/1A` | FILCT | FI/LC | Consolidation prep |
| `1C/1M` | ECMCT | EC/CS | Consolidation |
| `09` | GLT3 | FI/LC | — |

`t882`/`t882c` = ledger↔company-code/control assignment. `t882g` (custom totals-table per ledger) = **empty** → no custom new-G/L totals table.

**Verdict:** The new-G/L leading ledger `0L`→FAGLFLEXT is *defined* (standard delivered) but carries **no postings**. The real parallel-ledger backbone is the **classic FI-SL set** (reconciliation `COFIT`, profit-center `GLPCT`, consolidation `FILCT/ECMCT`). The splitting/new-G/L premise behind F3 does not hold.

---

## CLM-036 / HYP-003 — Full FMDERIVE 26-step config → **step master captured; "26 steps" not matched by FMOA**

The real FM derivation config is the generic **Derivation-Tool (`TABADR*`)** framework, **not** `FMDT_*`:

| Golden table | Rows | Meaning |
|---|---|---|
| `tabadr` | 57 | Strategy registry (which methods each strategy uses) |
| `tabadrt` | 188 | Strategy texts |
| `tabadrh` | 32 | Strategy/environment headers (version, modified_by/on) |
| **`tabadrs`** | **170** | **STEP master** — STEP_NO, METHOD (MOVE/DRULE/FUNC/CLEAR), IS_SAP_STEP, MODIFIED_BY |
| `tabadrsf` | 3,627 | Step source/target fields |
| `tabadrst` | 253 | Step texts |
| `fmderivefunc` | 597 | Field-movement definitions per function |
| `fmderivefuncid` | 16 | Strategy → function registry (incl. GM/`GMDT`) |
| `fmderiveenvid` | 2 | Env → strategy binding (ICTP, UBO → strategy **FMOA**) |
| `fmderive_sets`/`_trigger` | 4 / 224 | Set-class steps / triggers |
| `fmderive002`/`003`/`007` | 2,714 / 6 / 3,482 | SAP-standard DRULE rule-value tables |
| `fmfmoap013500001/012/022/062`, `fmfmoad011300012` | 4/8/2/34/75 | **FMOA custom DRULE rule-values** (the rules the bridge owns) |

**Strategy FMOA** (the account-assignment derivation used by company codes **ICTP** and **UBO**) — MEASURED step structure:
- **14 step rows** across 3 environments: `SAP` (8 steps), `ICTP DERIVATION` (3), `UBO DERIVATION` (3).
- Of the 14, **12 are non-SAP (custom-modified)**; **5 are custom `DRULE` (table-rule) steps** (only 2 DRULE steps are SAP-delivered — `FMDERIVE002`/`FMDERIVE003`).
- Custom DRULE steps point to generated rule tables `FMFMOAD011300012`, `FMFMOAP013500001/012/022/062` (now extracted).

**Verdict:** The "**5 of 26 steps**" claim is only **half-confirmed**. The "**5**" matches exactly (5 custom DRULE steps in FMOA). The "**26**" does **not** match any single FMOA environment (FMOA = 8 in its base SAP env, 14 total). The largest derivation strategy is the **year-change `FMYC`** (env `UNESCO2025-26` = 22 steps; `EAHR` = 17). The brain should recompute "26" against the actual `tabadrs` counts — likely it conflated FMOA with FMYC or an aggregate.

---

## HYP-012 — AVC tolerance / control-ledger config → **captured; real limits are 80/90% Warning + 100–130% Error (no 50% threshold)**

BCS Availability Control is **active**:
- `fmavcldgract`: AVC ledger **`9H`, LDGRSTAT='S'** (active/statistical), **all 9 FM areas** (IBE, ICBA, ICTP, IIEP, MGIE, UBO, UIL, UIS, UNES), **from FY2001**, `IGNORE_REVENUES='X'`.
- `fmavcldgratt`: tolerance profile assigned per FM-area — **Z000** (default, 6 areas), **ZIT1** (ICTP), **Z002** (UBO), **Z001** (UIL).

Tolerance **limits** (`buavctolass`, 34 rows) — the actual usage-rate + action (`MSGTY` W=warn/E=error/I=info):

| Profile | Limit / action | Used by |
|---|---|---|
| `Z000` | 100% **Error** (+abs 0.50) | UNES, IBE, ICBA, IIEP, MGIE, UIS |
| `ZIT1` | **80% Warning** → **100% Error** | ICTP |
| `Z002` | 100% Error | UBO |
| `Z001` | 100% Error (+abs 0.50) | UIL |
| `ZIT2` | 80% Warning → **105% Error** ceiling | (unassigned) |
| `ZIT3` | 90% Warning → **130% Error** ceiling | (unassigned) |
| `1000` | 90% Warning → 100% Error | SAP standard |
| `Z200` | **deactivated** (`DEACTIVE='X'`) | — |

Supporting AVC config also landed: `fmavcldgrgat`, `fmavcbudfilth/b`, `fmavcatgr_001/002`, `fm01tol` (legacy former-budgeting tolerance), plus the former-budgeting profiles `fmup00/00t/01/02`.

**Verdict:** HYP-012 closed. AVC checks at **100% Error** for most areas; ICTP gets an **80% early-warning**; lenient-overrun profiles (105/130%) exist but are unassigned. **There is no 50% threshold** — that framing was imprecise.

---

## Where the brain reads this

All tables are in `p01_gold_master_data.db` with the standard bare-lowercase-name = P01 convention. Query `_config_frontier_manifest` for the full inventory with row counts (empty/absent rows included). The unesco-sap-brain consumes this golden DB read-only (ADR-007 / BROADCAST-005).

> Local-only durability note: the Golden DB (~6.4 GB) is **gitignored** — these 61 new tables are NOT protected by git. Durability = disk/offsite backup. The extraction scripts (git-tracked) can regenerate the tables from P01 on demand.
