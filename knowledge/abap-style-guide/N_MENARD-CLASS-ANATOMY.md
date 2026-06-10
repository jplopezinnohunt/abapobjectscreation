# N_MENARD Class & Method Anatomy — How Nicolas Structures OO Code

**Created:** 2026-06-10 (session #081)
**Data basis (CP-003 — everything below is measured, not opined):**
- SEO catalog tables extracted from D01 into Gold DB: `d01_seo_classdf` (395 Y* classes),
  `d01_seo_compo`/`d01_seo_compodf` (7,451 components), `d01_seo_subcodf` (7,954 parameters),
  `d01_seo_metarel` (217 relations), `d01_seo_redef` (269 redefinitions).
- Analysis scope: **188 HR-WF-framework classes** (N_MENARD TADIR author).
- Source deep-reads: 11 classes total (8 s081 + 18 v1 refs + 3 framework bases in
  `extracted_code/CUSTOM/Y_CA_FRAMEWORKS/`).

This document answers ONE question: **what does a well-formed N_MENARD class look like inside** —
size, sections, visibility, attribute/method/parameter shape. The macro architecture (kits,
factories, packages) is in the style guide and `N_MENARD-OBJECT-INVENTORY.md`.

---

## 1. Class size: small domain classes, fat UI-assist classes (and only those)

| Metric (methods per class, 141 classes with methods) | Value |
|---|---|
| Median | **5** |
| Mean | 7.9 |
| Min / Max | 1 / 165 |

The only classes above ~40 methods are **Web Dynpro assistance classes** (`YCL_HR_PA_WF_ASSIST` 165,
`YCL_HR_INT_WF_ASSIST` 98, `YCL_HR_OM_WF_ASSIST` 54) and report BL classes (`YCL_HRWF_REPORT_2_BL` 47).
UI-binding classes are allowed to be wide (they mirror the screen); **domain classes stay at ~5 methods**.
If a domain class crosses ~15 methods, he splits it (the 19 mail classes instead of one mailer).

## 2. He never writes `ABSTRACT` — bases are concrete with empty hooks

Measured: **0 of 183** framework classes carry the ABSTRACT flag; **160 of 183 (87%) are FINAL**.
Non-FINAL = exactly the framework bases + per-type middle layers.

The "abstract base" of the style guide §3 is in reality a **concrete, instantiable default**:
hook methods have an empty implementation (`METHOD get_and_check_data. ENDMETHOD.`), so the base IS
the default behavior and a subclass overrides only what differs. Consequences:
- No `ABSTRACT METHODS` compile-time forcing — the framework still runs if a subclass forgets a hook.
- A "default" concrete class is possible without an extra layer (cf. `YCL_HRWF_CONCRETE_DEFAULT` in v1 refs).

Empty hooks observed in every base: `FILTER_AUTHORIZED_EMAIL`, `SET_ATTACHMENT`, `INITIALIZE_DATA`
(mail engine); `GET_AND_CHECK_DATA`, `GET_SELECTION_DATA` (check framework); `SET_ALV_OTHERS` (report base).

## 3. Inheritance is the main axis; interfaces only at framework boundaries

Measured: **80 inheritance relations vs 14 interface implementations** in the framework set.

He builds **deep template-method families** (5 confirmed, all same shape):

| Framework base | Subclasses | Hook surface (most-redefined methods) |
|---|---|---|
| `YCL_HR_WF_MAIL_GENERATOR` (+`_S`, `_O`, `_PA_*` middles) | 7+7+6+9... | `GET_DATA` (34 redefs!), `REPLACE_IN_HEADER` (16), `INITIALIZE_DATA` (9) |
| `YCL_CA_NOTIFICATION_GENERATOR` → `YCL_HR_NOTIFICATION_GENERATOR` | 11 leaves (CONTR_END, RETIREMENT, SPA_END...) | `YIF_CA_NOTIFICATION~GET_NOTIFICATION_LIST/GET_PERIMETER/DISPLAY_LIST`, `NOTIFICATION_SENT/NOT_SENT` (11 each) |
| `YCL_WF_CHECK_DATA` → `YCL_WF_CHECK_DATA_WF` | 10 leaves — **one class per validation rule** | `GET_AND_CHECK_DATA` (11), `SET_HEADER/SET_FOOTER` |
| `YCL_CA_REPORT_SHARE_STATEMENTS` (cross-app ALV report base) | 9+ across FI/FM/HR/BC | `SET_ALV_COLUMNS` (17), `INIT_ALV` (16) |
| `YCL_HRWF_MAIN` / `YCL_HRWF_ACTORS` (WF engine) | 3-4 per WF type | `STEP_FOR_USER_SPECIFIC`, perimeter checks |

Interfaces (`YIF_HRWF_MAIN`, `YIF_WF_CHECK_DATA`, `YIF_CA_NOTIFICATION`, `YIF_HR_WF_MAIL`) sit ONLY at
the top of each family = the contract callers/factories see. Subclassing happens behind the interface.

**Strategy-by-classname**: every family root has `GET_INSTANCE( iv_class_name )` doing
`CREATE OBJECT mo_instance TYPE (iv_class_name)` — the concrete class is chosen by a string from a
catalog table or a DEFAULT param (`YCL_WF_CHECK_DATA=>GET_INSTANCE( 'YCL_WF_CHECK_IT1008' )`).

## 4. Visibility doctrine (measured on 1,115 methods / 913 attributes)

| | PUBLIC | PROTECTED | PRIVATE |
|---|---|---|---|
| Methods | 518 (46%) | 91 (8%) | 506 (45%) |
| Attributes | 122 (13%) | 148 (16%) | 643 (70%) |

- **Public methods** = the contract: interface implementations + the 2-4 entry points of standalone
  classes (report base public API is exactly `INIT_ALV` + `DISPLAY_ALV` + `SET_SELECTION_VALUES`).
- **Protected** = hooks for subclasses + shared state of a family. Small on purpose (8%).
- **Private** = the helpers — half of all methods. He decomposes aggressively into private/protected
  one-job methods rather than long bodies.
- Attributes are 70% private; public attributes appear almost only via interface `DATA` + `ALIASES`
  (factory handles `MO_MAIN_CLASS`, `MV_WFTYPE` etc.).
- **875 instance vs 38 static attributes** — state is per-instance; `CLASS-DATA` only for singletons
  (`MO_INSTANCE`) and cross-call caches.

## 5. Attribute naming — prefixes are CONTRACTS, not decoration

Census of 913 attributes: `MT_` 439 · `MV_` 225 · `MO_` 135 · **`MR_` 60** · `MS_` 22 · **`MP_` 18** ·
unprefixed 8 (0.9% violation rate).

The two prefixes NOT in style guide v1:

| Prefix | Meaning | The contract |
|---|---|---|
| `MR_<name>` | Member **R**ange (SELECT-OPTIONS mirror) | `SET_SELECTION_VALUES` does `REPLACE 'S_' WITH 'MR_'` + dynamic `ASSIGN (name)` — screen `S_PERNR` binds to attribute `MR_PERNR` **by name computation**. Get the prefix wrong and the binding silently fails. |
| `MP_<name>` | Member **P**arameter (PARAMETERS mirror) | Same mechanism: `P_DATE` → `MP_DATE`. |

```abap
" YCL_CA_REPORT_SHARE_STATEMENTS=>SET_SELECTION_VALUES — the binding engine
CASE iv_kind.
  WHEN 'S'.  REPLACE 'S_' IN lv_selname WITH 'MR_'.
             ASSIGN (lv_selname) TO <lt_range>.  CHECK <lt_range> IS ASSIGNED.
             <lt_range> = it_value.
  WHEN 'P'.  REPLACE 'P_' IN lv_selname WITH 'MP_'.
             ASSIGN (lv_selname) TO <lv_param>.  CHECK <lv_param> IS ASSIGNED.
             <lv_param> = iv_value.
ENDCASE.
```

So a report BL subclass declares `DATA MR_PERNR TYPE <range type>` / `DATA MP_DATE TYPE datum` for every
screen field, and never parses the screen itself. (`YCL_WF_CHECK_DATA` shows the alternative: store the
whole selection as an `RSPARAMS` table via `SET_PARAMS` — used when checks need to forward selections.)

## 6. Method design

### 6.1 Verb taxonomy (1,144 non-interface method names)

`GET_` **529 (46%)** · `SET_` 110 · `CHECK_` 41 · `READ_` 36 · `DISPLAY_` 31 · `PREPARE_` 24 ·
`UPDATE_` 20 · `INIT_` 16 · `DELETE_` 15 · `IS_` 14 · `COMPARE_` 13 · `FILL_` 10 · `ADD_` 10 ·
`CREATE_` 9 · `SEND_` 9.

Semantics are consistent: `GET_` returns/derives data (no side effects on DB), `READ_` wraps an
infotype/table read, `IS_`/`CHECK_` predicates (`IS_` returns boolean, `CHECK_` exports `EV_IS_OK` +
`EV_RETURN`), `FILL_`/`PREPARE_` build internal state, `SET_` writes state, `DISPLAY_` UI.

### 6.2 Granularity: one job, one method, named for the job

`YCL_HR_NOTIFICATION_GENERATOR`'s protected section is the signature example — atomic getters
`GET_PERNR_MAIL`, `GET_PERNR_NAME`, `GET_PERNR_LANGUAGE`, `IS_PERNR_ACTIVE_AT_DATE`,
`KEEP_ONLY_ACTIVE_PERNR`, `GET_URL_LAUNCHPAD`, `INSERT_NOTIF_TRACE`... Each body is one SELECT/FM call
plus guards. Nothing is inlined twice.

The SALV setup is the cleanest illustration — **one method per ALV aspect**, each 2-6 lines:
`SET_ALV_FUNCTIONS` / `SET_ALV_COLUMNS` / `SET_ALV_LAYOUT` / `SET_DISPLAY_SETTINGS` / `SET_ALV_OTHERS`
(empty hook). Subclasses redefine exactly the aspect they need (`SET_ALV_COLUMNS` = 17 redefs).

### 6.3 Orchestrator methods read as a table of contents

Public entry points contain NO logic — only ordered calls to named steps, each prefixed with a
one-line `"comment`:

```abap
METHOD init_alv.                          " base class — verbatim shape
  mv_repid = iv_repid.
  TRY. cl_salv_table=>factory( IMPORTING r_salv_table = mo_salv_table
                               CHANGING  t_table      = ct_table ).
  CATCH cx_salv_msg. ENDTRY.
  "ALV functions activation
  me->set_alv_functions( ).
  "ALV columns
  me->set_alv_columns( ).
  "ALV layout
  me->set_alv_layout( ).
  "Display settings
  me->set_display_settings( ).
  "Others ALV proprties
  me->set_alv_others( ).
ENDMETHOD.
```

Same shape in `SEND_WI_NOTIFICATION` (mail engine), `YIF_WF_CHECK_DATA~CHECK_DATA`
(`get_selection_data` → `get_and_check_data`), `YIF_WF_CHECK_DATA~DISPLAY_ALV`
(`init_alv` → `set_alv_attributes` → `display`). **The orchestrator is the documentation.**

### 6.4 Other body idioms (from the 11 deep-read sources)

- `me->` is written explicitly for own-method calls (visual marker: "this is a step, not an FM").
- Guard clauses: `CHECK <cond>.` early-exit at the top; `CHECK sy-subrc = 0.` after reads.
- Redefinitions call `super-><method>( )` FIRST, then add deltas (mail leaves, perimeter checks).
- `READ TABLE ... WITH KEY langu = 'EN'` then FR with EN fallback — bilingual reads always paired.
- Every multi-row producer ends `SORT` + `DELETE ADJACENT DUPLICATES` (rule §1.6 — also in
  `GET_1000_DATA`-style helpers).

## 7. Signatures (7,954 parameters measured)

| Kind | Count | Share | Dominant prefix (compliance) |
|---|---|---|---|
| IMPORTING | 1,981 | 68% | `IV_` 1,603 / `IT_` 131 / `IS_` 90 / `IO_` 10 |
| EXPORTING | 555 | 19% | `EV_` 388 / `ET_` 119 / `ES_` 45 |
| RETURNING | 311 | 11% | `RV_` 188 / `RT_` 61 / `RS_` 24 / `RO_` 22 |
| CHANGING | 76 | **3%** | `CT_` 30 / `CS_` 27 / `CV_` 18 |

Rules he actually follows:
- **Params per method: median 3** (mean 3.3). Methods needing >6 inputs get a structure (`IS_`).
- **RETURNING for single results** (enables chaining/inline `DATA(x) = ...`); EXPORTING only for
  multi-output methods (`EV_IS_OK` + `EV_RETURN` pairs).
- **CHANGING is exceptional** (3%) — used only for in-place table mutation hooks
  (`CT_EMAIL`, `CT_STEPS`, `CV_STRING` in REPLACE_IN_HEADER).
- **OPTIONAL is rare** (14% of importing) and used for true alternatives (`IV_UNAME` vs `IV_PERNR`),
  often with `DEFAULT` (`IV_DATE TYPE datum DEFAULT sy-datum`, `GET_INSTANCE` class-name default).
- **Typed RAISING is part of the signature**: 107 `YCX_*`/`CX_*` declarations. The exception classes are
  **reusable technical ones**, not per-class: `YCX_DATA_ACCESS` (53 methods), `YCX_FILE_ACCESS` (26),
  `YCX_COMMUNICATION_CHECK` (13), `YCX_HRWF` (7, the domain one). One domain exception per framework +
  shared technical exceptions for cross-cutting failure kinds.

## 8. The prescriptive synthesis — structuring a new class his way

1. **Decide the family first.** New behavior = new LEAF in an existing family (mail event, check rule,
   report BL, WF type) before it is ever a new class hierarchy.
2. **Public section = contract only**: interface + aliases, or ≤4 entry-point methods. Entry points are
   orchestrators (named steps, one-line comments, zero logic).
3. **Protected section = the hook surface + family state.** Design hooks as EMPTY concrete methods
   (never ABSTRACT). Name them for the variation point (`GET_DATA`, `SET_ALV_COLUMNS`,
   `FILTER_AUTHORIZED_EMAIL`).
4. **Private section = one-job helpers**, verb-prefixed, each wrapping exactly one read/FM/derivation.
   Expect ~half of your methods to be private.
5. **Leaves are FINAL, redefine narrowly, call `super->` first.**
6. **Attributes**: instance, private by default; `MT_/MV_/MO_/MS_` + `MR_/MP_` when mirroring a
   selection screen (the name IS the binding). Static only for singleton/caches.
7. **Signatures**: ≤3 params typical; RETURNING for the single result; CHANGING only for in-place hooks;
   `DEFAULT sy-datum`/`sy-repid` for context params; typed RAISING using the shared `YCX_*` set.
8. **Target size: ~5 methods.** A domain class at 15+ methods means a family or a split is missing
   (UI-assist classes are the sanctioned exception).

---

*Queryable basis: all numbers reproducible from Gold DB `d01_seo_*` tables (joins on CLSNAME/CMPNAME).
Sources: `extracted_code/HCM/YHR_PA_WF/` + `extracted_code/CUSTOM/Y_CA_FRAMEWORKS/` +
`unescrp/artifacts/reference/nmenard/` (read-only).*
