# UNESCO SAP ABAP Style Guide

**Scope:** ECC 6.0 EhP8, UNESCO HQ SAP (system D01, client 350)
**Namespace:** `Z*` (CRP project), `Y*` (HR-team reference — Nicolas Menard)
**Package reference:** `YHR_PA_WF` (N_MENARD), `ZHR_CRP` (CRP)
**Last updated:** 2026-06-10
**Source:** 18 ADT readback files from package `YHR_PA_WF` (S-63 / S-72 extraction)
**Extended:** 2026-06-10 (s081) — full D01 package scan (740 objects) + 8 new deep-reads. See
`N_MENARD-OBJECT-INVENTORY.md` for the complete object catalog. Extension subsections are marked
"Extended patterns (from full D01 scan)" and never replace v1 content.

---

## Table of Contents

1. [Universal Rules](#1-universal-rules)
2. [ABAP Class — Standard](#2-abap-class--standard)
3. [ABAP Class — Abstract Base](#3-abap-class--abstract-base)
4. [ABAP Class — Concrete Subclass](#4-abap-class--concrete-subclass)
5. [ABAP Class — Static Utility](#5-abap-class--static-utility)
6. [ABAP Class — Factory / Singleton](#6-abap-class--factory--singleton)
7. [ABAP Interface](#7-abap-interface)
8. [Exception Class](#8-exception-class)
9. [BOR Object Methods](#9-bor-object-methods)
10. [Function Module (inside Function Group)](#10-function-module-inside-function-group)
11. [Report / Program](#11-report--program)
12. [Data Dictionary Objects](#12-data-dictionary-objects)
13. [What NOT To Do — CRP Disaster Catalogue](#13-what-not-to-do--crp-disaster-catalogue)
14. [ADT Deploy Pipeline Rules](#14-adt-deploy-pipeline-rules)
15. [OData / DPC_EXT Rules](#15-odata--dpc_ext-rules)

---

## 1. Universal Rules

These apply to **every** object type in the UNESCO SAP landscape.

### 1.1 Naming conventions

| Object type | Prefix | Example |
|---|---|---|
| Instance attribute | `MO_` (object ref), `MV_` (value), `MS_` (structure), `MT_` (table) | `MO_FACTORY`, `MV_WFTYPE`, `MT_ACT_DEF` |
| Class-level attribute | `MO_` / `MV_` same prefixes, in `class-data` | `class-data MO_FACTORY_INSTANCE` |
| Local variable | `LO_` (object), `LV_` (value), `LS_` (structure), `LT_` (table), `LR_` (range) | `lv_pernr`, `lt_actors` |
| Import param | `IV_` (value), `IS_` (structure), `IT_` (table), `IO_` (object) | `iv_wftype`, `it_rsparams` |
| Export param | `EV_`, `ES_`, `ET_`, `EO_` | `ev_is_ok`, `et_actors` |
| Changing param | `CV_`, `CS_`, `CT_`, `CO_` | `ct_actors` |
| Return param | `RV_`, `RS_`, `RT_`, `RO_` | `rv_is_ok`, `rt_actors`, `ro_instance` |
| Field-symbol | `<LS_>`, `<LT_>` (local) | `<ls_step>`, `<ls_actor>` |
| Constants | `LC_` (local), `C_` (class) | `lc_cancel`, `C_RANGE_SIGN_I` |
| Type (local in method) | `LTY_`, `LTTY_` | `lty_act`, `ltty_act_def` |
| Type (class-level protected/private) | `TY_`, `TTY_` | `ty_actty_email`, `tty_act_def` |

All names are **UPPER_SNAKE_CASE** in definitions, **lower_snake_case** acceptable in implementation bodies (SAP is case-insensitive). N_MENARD mixes both — choose consistency within a class.

### 1.2 Language and encoding

- Source language: **English** for code, comments, and method names.
- **Never use em-dashes (`–`) or curly quotes in comments.** They deploy as `?` via `read_ascii()` in the ADT pipeline. Use ASCII hyphens (`-`) only.
- All string literals in ABAP source must be plain ASCII or use message classes for multilingual text.

### 1.3 SELECT style — always use inline host variables

```abap
" Correct (ECC 6.0 EhP8 open SQL)
SELECT SINGLE * FROM ythrwf_type INTO @DATA(ls_hrwf_type) WHERE wftype = @mv_wftype.

SELECT s~step_seq, s~wfstep, t~wfstept
  FROM ythrwf_step AS s
  LEFT OUTER JOIN ythrwf_stept AS t
  ON t~spras = @sy-langu AND t~wftype = s~wftype AND t~wfstep = s~wfstep
  WHERE s~wftype = @mv_wftype
  INTO CORRESPONDING FIELDS OF TABLE @rt_steps.
```

- Always use `@variable` syntax for host variables.
- Use `INTO TABLE` not `INTO CORRESPONDING FIELDS OF TABLE` when field names match exactly — but prefer the explicit form for clarity on JOIN results.
- `TYPE table-field` for SELECT targets, never `LIKE field` (see §13, Category B).

### 1.4 Error handling — exceptions, not return codes

```abap
" Correct
RAISE EXCEPTION TYPE ycx_hrwf
  EXPORTING
    textid = ycx_hrwf=>step_not_exists
    wfstep = iv_current_step
    pernr  = iv_pernr.

" In callers
TRY.
  ls_actor_last_next-wfstep_next = lo_factory->mo_main_class->get_next_step( ... ).
CATCH ycx_hrwf.
ENDTRY.
```

Never use `sy-subrc` as a return code out of a method boundary. `sy-subrc` is for built-in operations (SELECT, READ TABLE, CALL FUNCTION) only within the method body.

### 1.5 Boolean usage

```abap
" Always use abap_true / abap_false constants (type abap_bool = c length 1)
rv_is_ok = abap_true.
IF lv_p = abap_true AND iv_stop_if_found = abap_true.
```

Never use `'X'` / `' '` for boolean logic. Use `abap_true` / `abap_false`.

### 1.6 Sort and deduplicate result tables

Every method that builds an actor list or any aggregate result **must** end with:

```abap
SORT rt_actors BY objid email.
DELETE ADJACENT DUPLICATES FROM rt_actors COMPARING objid email.
```

Source: `YCL_HRWF_ACTORS.yif_hrwf_actors~get_actors_for_step` (line 805-806),
`YCL_WF_UTILITIES.get_dialog_users_for_wf` (line 163-164),
`YCL_HRWF_ACTORS_LX.yif_hrwf_actors~get_signatories` (line 43-44).

---

## 2. ABAP Class — Standard

### 2.1 File naming

`ZCL_<DOMAIN>_<PURPOSE>.clas.abap`

Examples: `ZCL_CRP_WF_MAIN.clas.abap`, `ZCL_CRP_WF_ACTORS.clas.abap`

### 2.2 Structure template

```abap
CLASS zcl_<domain>_<purpose> DEFINITION
  PUBLIC
  [INHERITING FROM zcl_<parent>]
  [FINAL]
  CREATE PUBLIC.

PUBLIC SECTION.
  " 1. Interface declarations (implements the contract)
  INTERFACES zif_<domain>_<purpose>.

  " 2. Aliases — expose interface members as direct names
  ALIASES mv_wftype   FOR zif_<domain>_<purpose>~mv_wftype.
  ALIASES mo_factory  FOR zif_<domain>_<purpose>~mo_factory.

  " 3. Constructor (if needed)
  METHODS constructor
    IMPORTING !iv_wftype TYPE ze_<domain>_type.

PROTECTED SECTION.
  " 4. Types used by subclasses
  TYPES: tty_act_def TYPE TABLE OF zthrwf_act_def.

  " 5. Protected instance data (subclass-visible state)
  DATA mt_act_def         TYPE tty_act_def.
  DATA mt_act_type_ident  TYPE tty_act_type_ident.

  " 6. Protected methods (helpers for subclasses)
  METHODS get_actor_determination_data.
  METHODS get_email
    IMPORTING !iv_pernr TYPE p_pernr
              !iv_date  TYPE datum DEFAULT sy-datum
    RETURNING VALUE(rv_email) TYPE comm_id_long.

PRIVATE SECTION.
  " Only truly internal state here.
ENDCLASS.


CLASS zcl_<domain>_<purpose> IMPLEMENTATION.

  METHOD constructor.
    mv_wftype = iv_wftype.
  ENDMETHOD.

  METHOD zif_<domain>_<purpose>~<method_name>.
    " Interface method implementations use the full qualified name
    " zif_<domain>_<purpose>~<method_name>
  ENDMETHOD.

  METHOD get_actor_determination_data.
    " Lazy cache pattern (Pattern 5)
    IF mt_act_def IS INITIAL.
      SELECT * FROM zthrwf_act_def INTO TABLE mt_act_def
        WHERE actty IN (SELECT DISTINCT actty FROM zthrwf_step_act WHERE wftype = mo_factory->mo_main_class->mv_wftype).
    ENDIF.
  ENDMETHOD.

ENDCLASS.
```

### 2.3 Section ordering rules

1. `PUBLIC SECTION` first: interfaces, aliases, constructor, any public methods.
2. `PROTECTED SECTION` second: types (that subclasses need), protected data, protected methods.
3. `PRIVATE SECTION` last: purely internal.
4. **Types belong in the section that needs them**, not always in PUBLIC. Put `TYPES` statements at the top of their section.
5. `INTERFACES` declaration goes in PUBLIC SECTION — the only place SAP allows it.
6. Callers reference the interface type (`zif_crp_wf_main`), never the concrete class type (`zcl_crp_wf_main`).

### 2.4 What goes where

| Element | Section |
|---|---|
| Interface implementation | PUBLIC |
| Aliases for interface members | PUBLIC |
| Constructor | PUBLIC |
| Types shared with subclasses | PROTECTED |
| Cached instance tables (`mt_*`) | PROTECTED |
| Helper methods used by subclasses | PROTECTED |
| Pure internals, never subclassed | PRIVATE |

### Class internals — Extended patterns (from full D01 scan)

> Source: SEO catalog census of 188 N_MENARD framework classes (Gold DB `d01_seo_*`) — N_MENARD D01 scan

The measured micro-anatomy (class size ~5 methods, 46/8/45 public/protected/private method split,
empty-hook bases instead of ABSTRACT, `MR_`/`MP_` selection-binding attribute prefixes, GET-dominant
verb taxonomy, RETURNING-over-CHANGING signatures, the 5 template-method families and their
redefinition hook surface) is codified in **`N_MENARD-CLASS-ANATOMY.md`** — read it before designing
any new class. Key additions to §1.1 naming: `MR_<name>` = member range bound to screen `S_<name>`,
`MP_<name>` = member parameter bound to screen `P_<name>` (dynamic-ASSIGN contract — the prefix is the
binding mechanism, not decoration).

---

## 3. ABAP Class — Abstract Base

The abstract base holds the generic algorithm. Subclasses provide workflow-type-specific behaviour.

### 3.1 Pattern (from `YCL_HRWF_MAIN`)

```abap
CLASS zcl_crp_wf_main DEFINITION
  PUBLIC
  CREATE PUBLIC.       " NOT FINAL — subclasses must be possible

PUBLIC SECTION.
  INTERFACES zif_crp_wf_main.
  ALIASES mo_factory  FOR zif_crp_wf_main~mo_factory.
  ALIASES mv_wftype   FOR zif_crp_wf_main~mv_wftype.

  METHODS constructor IMPORTING !iv_wftype TYPE ze_crp_wf_type.

PROTECTED SECTION.
  " Hook method — empty default, subclasses override
  METHODS step_for_user_specific
    CHANGING !ct_steps TYPE ytthrwf_steps.

  " Shared utility method
  METHODS get_pers_data
    IMPORTING !iv_uname TYPE uname    OPTIONAL
              !iv_pernr TYPE p_pernr  OPTIONAL
              !iv_date  TYPE datum    DEFAULT sy-datum
    CHANGING  !cs_data  TYPE yshrwf_user_data.

PRIVATE SECTION.
ENDCLASS.
```

Key rules for abstract bases:
- **Not `FINAL`** — that would block subclassing.
- Shared algorithm in base, hook methods (empty by default) in `PROTECTED` for subclass customisation.
- `METHODS step_for_user_specific` is empty in the base (`METHOD step_for_user_specific. ENDMETHOD.`) — subclasses redeclare it as `REDEFINITION`.
- Base constructor stores `mv_wftype = iv_wftype` and nothing more.

---

## 4. ABAP Class — Concrete Subclass

One subclass per workflow type. Naming pattern: append the workflow type code.

```
ZCL_CRP_WF_MAIN     -- base
ZCL_CRP_WF_MAIN_C1  -- concrete for workflow type 'C1'
```

Source pattern from `YCL_HRWF_MAIN_S1` (separation WF), `YCL_HRWF_MAIN_I1` (intern WF):

```abap
CLASS zcl_crp_wf_main_c1 DEFINITION
  PUBLIC
  INHERITING FROM zcl_crp_wf_main
  FINAL                              " Concrete classes are FINAL
  CREATE PUBLIC.

PUBLIC SECTION.
  " Only redeclare methods that this subclass overrides
  METHODS zif_crp_wf_main~get_wf_steps      REDEFINITION.
  METHODS zif_crp_wf_main~check_in_actor_type_perimeter REDEFINITION.

PROTECTED SECTION.
  " Subclass-specific protected state
  DATA mt_special_units TYPE ytthr_orgeh.

  " Subclass-specific helpers
  METHODS get_special_units.
  METHODS step_for_user_specific   REDEFINITION.

PRIVATE SECTION.
ENDCLASS.


CLASS zcl_crp_wf_main_c1 IMPLEMENTATION.

  METHOD zif_crp_wf_main~get_wf_steps.
    " Always call super first, then adjust
    DATA(lt_steps) = super->zif_crp_wf_main~get_wf_steps(
      EXPORTING iv_pernr       = iv_pernr
                iv_action_date = iv_action_date
                iv_substep     = iv_substep ).

    " Workflow-type-specific step adjustments here
    LOOP AT lt_steps INTO DATA(ls_step).
      " ...
    ENDLOOP.
  ENDMETHOD.

  METHOD zif_crp_wf_main~check_in_actor_type_perimeter.
    " Always call super first
    super->zif_crp_wf_main~check_in_actor_type_perimeter(
      EXPORTING iv_pernr       = iv_pernr
                iv_action_date = iv_action_date
                iv_actty       = iv_actty
                iv_uname       = iv_uname
      IMPORTING ev_is_ok       = ev_is_ok
                ev_return      = ev_return ).

    " Then add workflow-type-specific checks
    CHECK ev_is_ok = abap_true.   " Stop if super already rejected
    " ...
  ENDMETHOD.

ENDCLASS.
```

Rules:
- Concrete classes are `FINAL`.
- Always call `super->` before adding logic in redefined methods.
- After calling super in `check_in_actor_type_perimeter`, guard with `CHECK ev_is_ok = abap_true` before adding more checks — do not overwrite a super rejection.
- `REDEFINITION` keyword must appear in the same visibility section as the original declaration (usually PUBLIC for interface methods).

---

## 5. ABAP Class — Static Utility

No instance. All methods are `CLASS-METHODS`. `FINAL` always. `CREATE PUBLIC` (SAP requires it even for utility classes).

Source: `YCL_WF_UTILITIES` and `YCL_CA_UTILITIES`.

```abap
CLASS zcl_crp_utilities DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

PUBLIC SECTION.
  " All methods are class-methods
  CLASS-METHODS get_objects_with_eval_path
    IMPORTING !iv_otype   TYPE otype
              !iv_objid_c TYPE any
              !iv_wegid   TYPE wegid
              !iv_date    TYPE datum
    EXPORTING !et_object  TYPE objec_t.

  CLASS-METHODS is_test_system
    RETURNING VALUE(rv_is_ok) TYPE boolean.

  CLASS-METHODS get_username
    IMPORTING !iv_uname       TYPE uname
    RETURNING VALUE(rs_full_name) TYPE ad_namtext.

PROTECTED SECTION.
PRIVATE SECTION.
ENDCLASS.


CLASS zcl_crp_utilities IMPLEMENTATION.

  METHOD is_test_system.
    rv_is_ok = abap_false.

    " Check T000 for production category
    SELECT SINGLE cccategory INTO @DATA(lv_cccategory)
      FROM t000 WHERE mandt = @sy-mandt.
    IF lv_cccategory = 'P'.
      EXIT.  " Production: not a test system
    ENDIF.

    " Check TVARVC exclusion table
    DATA lt_syst TYPE RANGE OF sy-sysid.
    SELECT sign, opti, low, high INTO TABLE @lt_syst FROM tvarvc
      WHERE name = 'Z_WF_SYST_LIKE_PROD' AND type = 'S'.
    IF lt_syst IS NOT INITIAL AND sy-sysid IN lt_syst.
      EXIT.
    ENDIF.

    rv_is_ok = abap_true.
  ENDMETHOD.

ENDCLASS.
```

Rules:
- No `DATA` declarations (instance data) — only `CLASS-DATA` if shared state is truly needed.
- No `CONSTRUCTOR`.
- Every method: `CLASS-METHODS`, called as `zcl_crp_utilities=>method_name(...)`.
- Common pattern: wrap standard FMs (`RH_STRUC_GET`, `SO_DOCUMENT_READ_API1`) in a static utility so callers don't need to know the FM name.

---

## 6. ABAP Class — Factory / Singleton

One factory per domain. Returns the concrete implementation chosen from a config table. Controls singleton lifecycle.

Source: `YCL_HRWF_FACTORY` and `YCL_HR_WF_MAIL_FACTORY`.

```abap
CLASS zcl_crp_wf_factory DEFINITION
  PUBLIC
  FINAL
  CREATE PUBLIC.

PUBLIC SECTION.
  " Public handles to the resolved sub-objects
  DATA mo_main_class    TYPE REF TO zif_crp_wf_main.
  DATA mo_actors_class  TYPE REF TO zif_crp_wf_actors.

  METHODS constructor.

  CLASS-METHODS get_instance
    IMPORTING !iv_wftype       TYPE ze_crp_wf_type
    RETURNING VALUE(ro_instance) TYPE REF TO zcl_crp_wf_factory.

PROTECTED SECTION.
PRIVATE SECTION.
  " Singleton state
  CLASS-DATA mo_factory_instance TYPE REF TO zcl_crp_wf_factory.
  CLASS-DATA mv_wftype           TYPE ze_crp_wf_type.
ENDCLASS.


CLASS zcl_crp_wf_factory IMPLEMENTATION.

  METHOD get_instance.
    " Recreate only when wftype changes
    IF mo_factory_instance IS INITIAL OR mv_wftype <> iv_wftype.
      mv_wftype = iv_wftype.
      CREATE OBJECT mo_factory_instance.
    ENDIF.
    ro_instance = mo_factory_instance.
  ENDMETHOD.

  METHOD constructor.
    " Read config table to resolve concrete class names
    SELECT SINGLE * FROM zthrwf_type INTO @DATA(ls_type)
      WHERE wftype = @mv_wftype.
    CHECK sy-subrc = 0.

    " Dynamic instantiation — class name comes from config table
    FREE mo_main_class.
    IF ls_type-main_class IS NOT INITIAL.
      CREATE OBJECT mo_main_class TYPE (ls_type-main_class)
        EXPORTING iv_wftype = mv_wftype.
      mo_main_class->mo_factory = mo_factory_instance.
    ENDIF.

    FREE mo_actors_class.
    IF ls_type-actors_class IS NOT INITIAL.
      CREATE OBJECT mo_actors_class TYPE (ls_type-actors_class).
      mo_actors_class->mo_factory = mo_factory_instance.
    ENDIF.
  ENDMETHOD.

ENDCLASS.
```

Rules:
- `GET_INSTANCE` is a `CLASS-METHODS` static method.
- Singleton check: `IF mo_factory_instance IS INITIAL OR mv_wftype <> iv_wftype`.
- Dynamic instantiation: `CREATE OBJECT mo_main_class TYPE (ls_type-main_class)`. The class name is a string read from a config table (`zthrwf_type-main_class`). This is the catalog-driven pattern — adding a new workflow type never touches factory code.
- After creation, inject the factory back-reference: `mo_main_class->mo_factory = mo_factory_instance.`
- Config table `zthrwf_type` must exist with at minimum: `wftype`, `main_class`, `actors_class`, `wfid` columns.

### Mail / notification class family — Extended patterns (from full D01 scan)

> Source: `YCL_HR_WF_MAIL_GENERATOR` (base, package YHR_OM_WF), `YCL_HR_WF_MAIL_GENERATOR_PA_S1`,
> `YCL_HR_WF_MAIL_PA_S1_ACTION` — N_MENARD D01 scan

The package contains **19 mail classes** organized as a strict **3-level template-method hierarchy**
(this is the structure to copy for any notification subsystem):

```
YCL_HR_WF_MAIL_GENERATOR                 " Level 1: abstract engine (NOT final)
  └─ YCL_HR_WF_MAIL_GENERATOR_PA_S1     " Level 2: per-WF-type data provider (NOT final)
       └─ YCL_HR_WF_MAIL_PA_S1_ACTION   " Level 3: per-notification-event (FINAL)
       └─ YCL_HR_WF_MAIL_PA_S1_CHECK
       └─ YCL_HR_WF_MAIL_PA_S1_FINAL
```

**Level 1 — the engine** (`YCL_HR_WF_MAIL_GENERATOR`):
- Implements the public contract `YIF_HR_WF_MAIL` (`send_wi_notification`, `send_wi_notification_pa`).
- The interface method IS the template method — fixed orchestration sequence:
  `initialize_data()` → `get_template(header)` → `convert_to_table_string()` → `replace_in_header()`
  → subject; then `get_template(body)` → `add_template_variant()` → `set_attachment()` →
  `replace_in_body()` (= `get_data()` + `replace_data_from_container()`) → `put_format()` → `send_mail()`.
- Hook methods are **empty in the base** (`initialize_data`, `filter_authorized_email`, `set_attachment`)
  — same hook-method idiom as §3.
- Constructor takes the notification CATALOG keys (`iv_notif_type/header/body/istat`) — templates are
  data, never hardcoded.

**Level 2 — per-WF-type data provider**: redefines `initialize_data` (gets its own
`ycl_hrwf_factory=>get_instance( ypawf_c_wftype_s1 )` and reads employee/org data through the factory),
`get_data` (fills placeholders), `replace_in_header`, `filter_authorized_email`. Not final.

**Level 3 — per-event class**: FINAL; redefines `get_data`/`replace_in_header` and **always calls
`super->` first**, then adds only event-specific placeholders (e.g. the inbox `<URL>`).

Supporting patterns (each is a rule):

1. **Templates are SO10 standard texts** read via `READ_TEXT` (`ID 'ST'`, `OBJECT 'TEXT'`), maintained
   bilingual (EN + FR read separately, FR falls back to EN). No email body strings in ABAP code.
2. **Placeholder container**: every dynamic value goes through `put_to_container( iv_field = '<TOKEN>'
   iv_value = ... )` into a field/value table; one generic `replace_data_from_container` does
   `REPLACE ALL OCCURRENCES` over the text stream. Adding a placeholder never touches the engine.
3. **Template variants via HR feature**: `HR_FEATURE_BACKFIELD` on feature `YWFNF` returns a variant key;
   `YTHRWF_NOTIF_VAR` (catalog table) maps it to the variant text block, spliced at `<VARIANT_EN>` /
   `<VARIANT_FR>` markers. Catalog-driven, like Pattern 3.
4. **Pseudo-markup in templates**: authors write `<BOLD>`,`<ITALIC>`,`<ULINE>`; `put_format()` converts
   to HTML `<b>/<i>/<u>`. Templates stay readable for functional staff.
5. **Non-prod email guard** (the mail-side complement of Pattern 10): when `T000-CCCATEGORY <> 'P'`,
   `filter_authorized_email` checks each recipient against whitelist table `YTBC_MAIL_AUTH`
   (keyed by application, e.g. `YAPPL = 'PA_WF'`) and corrupts non-whitelisted addresses
   (`CONCATENATE <email> 'TEST'`) so test systems can never mail real staff. The hook is empty in the
   base and redefined per application.
6. **Substitution awareness**: `add_subsituted_mail` reads `HRUS_D2` (active SAP substitutes) →
   `PA0105` subty 0001→0010 chain, and adds delegates' emails to the recipient list.
7. **BCS send**: `cl_bcs=>create_persistent` + `cl_document_bcs=>create_document( i_type = 'HTM' )` +
   `set_send_immediately( 'X' )` + `COMMIT WORK`; every `cx_*_bcs` caught, mapped to an `ev_subrc`
   export. The mail boundary uses subrc-style returns (it is called from WF/BOR contexts that cannot
   propagate class exceptions).

---

## 7. ABAP Interface

All public methods that callers need go in the interface. The concrete class never adds public methods that bypass the interface.

Source: `YIF_HRWF_MAIN`, `YIF_HRWF_ACTORS`.

```abap
INTERFACE zif_crp_wf_main
  PUBLIC.

  " 1. Public data (state that callers or the factory need to read/set)
  DATA mv_wftype   TYPE ze_crp_wf_type.
  DATA mo_factory  TYPE REF TO zcl_crp_wf_factory.
  DATA ms_employee_data TYPE zshrwf_user_data.

  " 2. Methods — all PUBLIC by definition in an interface
  METHODS get_wf_steps
    IMPORTING !iv_pernr        TYPE p_pernr   OPTIONAL
              !iv_action_date  TYPE datum
              !iv_substep      TYPE ze_hrwf_substep DEFAULT 'ACTION'
    RETURNING VALUE(rt_steps)  TYPE ytthrwf_steps.

  METHODS get_next_step
    IMPORTING !iv_current_step TYPE ze_hrwf_step
              !iv_pernr        TYPE p_pernr
              !iv_action_date  TYPE datum
    RETURNING VALUE(rv_next_step) TYPE ze_hrwf_step
    RAISING zcx_crp_wf.

  METHODS check_in_actor_type_perimeter
    IMPORTING !iv_pernr        TYPE p_pernr
              !iv_action_date  TYPE datum
              !iv_actty        TYPE ze_hrwf_actor_type
              !iv_uname        TYPE uname
    EXPORTING !ev_is_ok        TYPE boolean
              !ev_return       TYPE bapireturn1.

ENDINTERFACE.
```

Rules:
- Interface file naming: `ZIF_<DOMAIN>_<PURPOSE>.intf.abap`.
- Interfaces have **no implementation** block.
- Use `RAISING` for typed exceptions in interface method signatures — callers see the contract.
- `DATA` declarations in the interface are instance data that the implementing class exposes through aliases.
- After `INTERFACES zif_crp_wf_main.` in the implementing class, create `ALIASES` for every interface data member that external code needs to read directly (e.g. `mo_factory`, `mv_wftype`).

---

## 8. Exception Class

One exception class per domain. Multiple `TEXTID` constants for different error conditions.

Source: `YCX_HRWF` (referenced throughout the N_MENARD codebase — raising pattern at `YCL_HRWF_MAIN.yif_hrwf_main~get_next_step:254-258`, `YCL_HRWF_OPERATION.cancel:69-73`).

```abap
CLASS zcx_crp_wf DEFINITION
  PUBLIC
  INHERITING FROM cx_static_check
  FINAL
  CREATE PUBLIC.

PUBLIC SECTION.
  " One constant per error condition — use descriptive names
  CONSTANTS step_not_exists      TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS final_step_reached   TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS user_not_wf_actor    TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS user_not_authorized  TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS action_not_possible  TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS error_during_action  TYPE sotr_conc VALUE '...' ##NO_TEXT.
  CONSTANTS no_wf_found          TYPE sotr_conc VALUE '...' ##NO_TEXT.

  " Attributes for error context
  DATA wfstep TYPE ze_hrwf_step.
  DATA pernr  TYPE p_pernr.
  DATA uname  TYPE uname.
  DATA action TYPE text20.
  DATA status TYPE sww_wistat.
  DATA wi_id  TYPE sww_wiid.

  METHODS constructor
    IMPORTING !textid LIKE textid OPTIONAL
              !previous LIKE previous OPTIONAL
              !wfstep TYPE ze_hrwf_step OPTIONAL
              !pernr  TYPE p_pernr     OPTIONAL
              !uname  TYPE uname       OPTIONAL
              !action TYPE text20      OPTIONAL
              !status TYPE sww_wistat  OPTIONAL
              !wi_id  TYPE sww_wiid    OPTIONAL.

PROTECTED SECTION.
PRIVATE SECTION.
ENDCLASS.
```

Raising pattern — always supply `textid` and the relevant context attributes:

```abap
RAISE EXCEPTION TYPE zcx_crp_wf
  EXPORTING
    textid = zcx_crp_wf=>step_not_exists
    wfstep = iv_current_step
    pernr  = iv_pernr.

RAISE EXCEPTION TYPE zcx_crp_wf
  EXPORTING
    textid = zcx_crp_wf=>user_not_authorized
    uname  = iv_uname.

RAISE EXCEPTION TYPE zcx_crp_wf
  EXPORTING
    textid = zcx_crp_wf=>error_during_action
    action = lc_cancel
    wi_id  = iv_wiid.
```

Rules:
- Inherit from `CX_STATIC_CHECK` for checked exceptions (callers must declare `RAISING` or `TRY/CATCH`).
- Never use `cx_sy_no_handler` or `cx_root` — those are system exceptions not domain exceptions.
- Never use `RAISE EXCEPTION TYPE cx_sy_no_handler` as a "todo" placeholder — it causes ST22 dumps in SWDD Method step contexts (CRP S-110 disaster). Use `RETURN` instead when you need a silent early exit.
- Name constants after the condition, not after the message number.

---

## 9. BOR Object Methods

BOR objects use a procedural dialect (no `CLASS ... ENDCLASS`). The include `<object>` and `INCLUDE <cntain>` provide the macro API.

Source: `YBUS1065.bor.abap` (package `YHR_PA_WF`, object type `YBUS1065`).

### 9.1 File structure

```abap
*&----------------------------------------------------------------------*
*& Object Type: ZCRP_CERT
*& Subtype of:  BUS2012 (or standalone BO)
*& Key:         CERT_ID TYPE ZCRP_DE_CERT_ID
*&----------------------------------------------------------------------*
INCLUDE <object>.
BEGIN_DATA OBJECT.
DATA:
  BEGIN OF KEY,
    CERT_ID LIKE ZCRP_CERT-CERT_ID,
  END OF KEY,
  " Private attributes
  _ZCRP_CERT LIKE ZCRP_CERT.
END_DATA OBJECT.
```

### 9.2 Method implementation

```abap
begin_method <methodname> changing container.

" 1. Declare all local data at top (BOR methods have no inline DATA)
DATA: lo_factory    TYPE REF TO zcl_crp_wf_factory,
      ls_actor_next TYPE zshr_wf_step_last_next,
      lt_actors     TYPE ytthrwf_actors.

" 2. Read container elements
INCLUDE <cntain>.
swc_get_element container 'WFTYPE'       lv_wftype.
swc_get_element container 'ACTOR_LAST_NEXT' ls_actor_next.
swc_get_table   container 'TAB_HIS_STEP'    lt_his_wfstep.

" 3. Business logic — use factory pattern
lo_factory = zcl_crp_wf_factory=>get_instance( iv_wftype = lv_wftype ).
lt_actors  = lo_factory->mo_actors_class->get_actors_for_step( ... ).

" 4. Write container elements back
swc_set_table   container 'ACTORS'          lt_actors.
swc_set_element container 'ACTOR_LAST_NEXT' ls_actor_next.

end_method.
```

### 9.3 History tracking pattern

Every state-change method must append a history row before returning:

```abap
" Standard history structure fields
ls_his_wfstep-wstep  = ls_his_wfstep-wstep + 1.   " Sequential step number
ls_his_wfstep-datum  = sy-datum.
GET TIME.
ls_his_wfstep-uzeit  = sy-uzeit.
ls_his_wfstep-actty  = ls_actor_next-actty_last.   " Actor type who acted
ls_his_wfstep-wfstep = ls_actor_next-wfstep_last.  " Step identifier
ls_his_wfstep-uname  = lv_uname.                   " Username who acted
APPEND ls_his_wfstep TO lt_his_wfstep.
swc_set_table container 'TAB_HIS_STEP' lt_his_wfstep.
```

### 9.4 Container macros — use SWC macros, not FMs

```abap
" CORRECT — SWC macros (fast, no FM overhead)
INCLUDE <cntain>.
swc_get_element container 'ELEMENT_NAME' lv_variable.
swc_set_element container 'ELEMENT_NAME' lv_variable.
swc_get_table   container 'TABLE_NAME'   lt_table.
swc_set_table   container 'TABLE_NAME'   lt_table.

" AVOID unless utility layer needed
CALL FUNCTION 'SAP_WAPI_READ_CONTAINER' ...   " Use only in static utility classes
```

### 9.5 Standard BOR method set

Every workflow BO should implement this minimum set:

| Method | Purpose |
|---|---|
| `GETDATAFROMINITIATORSTEP` | Initial setup: read WFTYPE, set `ACTOR_LAST_NEXT`, write first `TAB_HIS_STEP` row |
| `DETERMINENEXTACTOR` | Navigate to next step via factory; populate `ACTORS` table container element |
| `SETRESULTNEXTSTEP` | Advance: set `NEXT_STEP=true`, update `ACTOR_LAST_NEXT`, append history row |
| `SETRESULTRETURN` | Return/reject: set `NEXT_STEP=false`, set `WFSTEP_RETURN`, append history row |
| `SENDNOTIFICATION` | Email to relevant actors |

---

## 10. Function Module (inside Function Group)

Function modules are legacy. New code should be ABAP OO classes. FMs are acceptable for: SWDD actor resolution exit (`ACTOR_TAB` parameter), BOR adapter bridge, and backward-compatible interfaces.

Source: `Y_HRPAWF_NEXT_ACTOR.abap`.

### 10.1 Required structure

```abap
FUNCTION z_crp_next_actor
  TABLES
    ac_container LIKE swcont       " WF container
    actor_tab    LIKE swhactor     " Output: actor list
  EXCEPTIONS
    nobody_found
    incorrect_input.

  " 1. Include container macros
  INCLUDE <cntain>.
  CLEAR actor_tab[]. CLEAR actor_tab.

  " 2. Declare local data
  DATA: ls_actor   TYPE swhactor,
        lt_actors  TYPE ytthrwf_actors,
        ls_actors  TYPE LINE OF ytthrwf_actors.

  " 3. Read from container
  swc_get_table ac_container 'ACTORS' lt_actors.

  " 4. Map to SWHACTOR output format
  LOOP AT lt_actors INTO ls_actors.
    ls_actor-otype = ls_actors-otype.
    ls_actor-objid = ls_actors-objid.
    IF ls_actor-otype IS NOT INITIAL.
      APPEND ls_actor TO actor_tab.
    ENDIF.
  ENDLOOP.

  " 5. Always sort and deduplicate
  SORT actor_tab.
  DELETE ADJACENT DUPLICATES FROM actor_tab.

ENDFUNCTION.
```

Rules:
- FM signature: `TABLES` parameter for `swcont` container (not `CHANGING`) — that is the SWDD contract.
- Always `CLEAR actor_tab[]` at the start.
- All `DATA` declarations at the top of the FM body (before any logic).
- No inline `DATA(...)` declarations inside FMs on ECC 6.0 — inline declarations work in methods and reports but are unreliable inside function module bodies on older kernel levels.
- EXCEPTIONS list must include all conditions the caller might need to handle.

### Function Module — Extended patterns (from full D01 scan)

> Source: `Y_HRPAWF_EVENT_RULES_PA0000`, `Y_HR_PAWF_FILL_REQUEST` (FUGR `YHRPAWF1`) — N_MENARD D01 scan

`YHRPAWF1` holds **9 FMs** falling into exactly three roles — and only these three justify a new FM
(everything else is a class method):

**Role A — SAP-contract FMs** (signature dictated by a framework, you cannot choose it):
`Y_HRPAWF_EVENT_RULES_PA0000` implements the HR workflow-event-rule contract (registered in `T779W`/SWEC):
`AFTER_IMAGE`/`BEFORE_IMAGE LIKE PRELP`, `EVENT LIKE SWETYPECOU-EVENT`. Rules:
- Keep it THIN: cast images to `P0000`, compare status fields, map to an event name. Nothing else.
- `LIKE` in the signature is ACCEPTABLE here (the SAP template uses it) — the §13-B1 ban applies to
  your own declarations, not to framework-dictated signatures.
- Guard against unwanted trigger contexts at the top: `CHECK sy-cprog <> 'SAPMHTTP'` (suppresses the
  event when the change comes from the web WF itself — prevents event loops).
- `CHECK beforeimage-stat2 NE afterimage-stat2` — fire only on a real state change.

**Role B — bridge FMs** (RFC/Fiori/WF entry point delegating to a class):
`Y_HR_PAWF_FILL_REQUEST` is the WF→Fiori-dashboard bridge. Rules:
- First statement of logic: get the singleton (`zcl_hr_fiori_offboarding_req=>get_instance( )`) —
  the FM owns NO business logic.
- `CASE iv_step` on a step keyword (`REQUEST_INIT` / `UPDATE_DATA` / `CLOSED`), one class-method call
  per branch.
- Exports are `EV_IS_OK TYPE XFELD` + `ES_RETURN TYPE BAPIRET2`; build the message with
  `MESSAGE ID ... INTO es_return-message` (fills the text without raising).
- Resolve the acting user once at the top (`ycl_bc_user_info=>get_pernr_from_user`) and pass the PERNR
  down — classes never read `sy-uname` themselves.

**Role C — view-maintenance FMs** (generated): ~120 of N_MENARD's function groups are SE54-generated
`TABLEPROC_*`/`TABLEFRAME_*` pairs for the `YV*`/`YT*` maintenance views. Never hand-edit these; regenerate
from SE54. One FUGR per maintained view, named after the view.

Anti-pattern observed (do not copy): commented-out trace scaffolding (`ycl_bc_trace_file` block) left in
the FM body. Delete debug scaffolding before transport.

---

## 11. Report / Program

Reports are used for: batch jobs, admin utilities, data migration. NOT for business logic (that goes in classes).

### 11.1 Structure

```abap
REPORT z_crp_<purpose>.

*&----------------------------------------------------------------------*
*& Purpose: <one-line description>
*& Package: ZHR_CRP
*& Author:  <author> / <date>
*& Scope:   <what this report does and doesn't do>
*&----------------------------------------------------------------------*

" 1. Type declarations
TYPES: BEGIN OF lty_output,
         cert_id   TYPE zcrp_de_cert_id,
         status    TYPE zcrp_de_status,
         step_name TYPE text60,
       END OF lty_output.

" 2. Selection screen (if needed)
SELECTION-SCREEN BEGIN OF BLOCK b1 WITH FRAME TITLE TEXT-001.
  PARAMETERS: p_date TYPE datum DEFAULT sy-datum.
  SELECT-OPTIONS: s_certid FOR zcrp_cert-cert_id.
SELECTION-SCREEN END OF BLOCK b1.

" 3. Global data
DATA: lt_output TYPE TABLE OF lty_output.

" 4. START-OF-SELECTION
START-OF-SELECTION.
  PERFORM fill_data.
  PERFORM display_output.

*&----------------------------------------------------------------------*
*& Form  FILL_DATA
*&----------------------------------------------------------------------*
FORM fill_data.
  SELECT cert_id, status FROM zcrp_cert
    WHERE cert_id IN s_certid
    INTO CORRESPONDING FIELDS OF TABLE lt_output.
ENDFORM.

*&----------------------------------------------------------------------*
*& Form  DISPLAY_OUTPUT
*&----------------------------------------------------------------------*
FORM display_output.
  " Use ALV for output
  CALL FUNCTION 'REUSE_ALV_GRID_DISPLAY' ...
ENDFORM.
```

Rules:
- Business logic lives in classes, not FORMs. FORMs only orchestrate calls to class methods.
- Always use `SELECTION-SCREEN` for user inputs — never hardcoded values in report body.
- No `SELECT` statements in `START-OF-SELECTION` inline — encapsulate in FORMs or class method calls.
- Test-system check at the top of destructive reports: `IF zcl_crp_utilities=>is_test_system( ) = abap_false. RETURN. ENDIF.`

### Report / Program — Extended patterns (from full D01 scan)

> Source: `YHR_WF_PA_LIST_1` + `YHR_WF_PA_LIST_1_DATA` + `YHR_WF_PA_LIST_1_SEL`, `YCL_HRWF_REPORT_2_BL` —
> N_MENARD D01 scan

N_MENARD's production reports do NOT use the FORM-based skeleton of §11 — they use a stricter
**report-as-thin-shell** pattern. Prefer this for any new ALV report:

**1. Three-file split** (fixed naming):

```
YHR_WF_PA_LIST_1        " main: REPORT + 2 INCLUDEs + START-OF-SELECTION only (43 lines total)
YHR_WF_PA_LIST_1_DATA   " include: TABLES / TYPE-POOLS / TYPES / global DATA only
YHR_WF_PA_LIST_1_SEL    " include: SELECTION-SCREEN + INITIALIZATION + all AT SELECTION-SCREEN events
```

**2. All logic in a business-logic class** (`YCL_HRWF_REPORT_2_BL`, suffix `_BL`). The report's whole
`START-OF-SELECTION` is:

```abap
go_hrwf_report = NEW ycl_hrwf_report_2_bl( ).
go_hrwf_report->set_selection_values( iv_selname = 'P_SPA'  iv_kind = 'P' iv_value = p_spa ).
go_hrwf_report->set_selection_values( iv_selname = 'S_PERNR' iv_kind = 'S' it_value = s_pernr[] ).
" ... one line per parameter / select-option ...
go_hrwf_report->get_data( ).
go_hrwf_report->mv_repid = sy-repid.
go_hrwf_report->init_alv( ).
go_hrwf_report->set_alv_status( 'SALV_TABLE_STANDARD' ).
go_hrwf_report->mv_layout = p_layout.
go_hrwf_report->display_alv( ).
```

The generic `set_selection_values( iv_selname, iv_kind = 'P'|'S', iv_value|it_value )` hands the
selection screen to the class as named values — the class never references screen fields, so it is
callable (and testable) without the screen.

**3. Selection-screen idioms** (from `_SEL` include):
- `SELECT-OPTIONS s_x FOR <ddic_structure>-field` against a dedicated DDIC structure
  (`YSHR_WF_REPORT_2`, declared with `TABLES:` in `_DATA`) — typed F1/F4 without a DB table.
- Centralized F4: `ycl_hrwf_report_utilities=>value_request_popup( iv_retfield / iv_repid /
  iv_dynprofield / it_value_tab )` for every custom value help — never inline `F4IF_INT_TABLE_VALUE_REQUEST`.
- ALV layout param: `PARAMETERS p_layout LIKE disvariant-variant` + F4 via
  `cl_salv_layout_service=>f4_layouts( )`.
- Dynamic screen: radio buttons with `USER-COMMAND` + `AT SELECTION-SCREEN OUTPUT` looping `SCREEN`
  on `MODIF ID` groups (`screen-active = 0/1`).
- Block-level validation in `AT SELECTION-SCREEN ON BLOCK bNN` raising `MESSAGE Exxx(<msgclass>)`,
  including auto-correcting defaults instead of erroring when a default is safe.
- `INITIALIZATION` pre-loads F4 value tables once (via the utilities class / direct SELECT).

The §11 FORM skeleton remains valid for small admin utilities; for anything with an ALV and a real
selection screen, the `_BL`-class pattern above is the house style.

---

## 12. Data Dictionary Objects

### 12.1 Transparent Table (`TABL`)

Naming: `Z<DOMAIN>_<PURPOSE>` (max 16 chars)

```
ZCRP_CERT        -- main certificate table
ZCRP_WFT_STEP    -- workflow step catalog
ZCRP_WFT_ACT_TY  -- actor type catalog
ZCRP_APRVL_HIST  -- approval history log
```

Design rules:
- Always include `MANDT` (client) as first key field for client-dependent tables.
- Primary key fields last in the key definition where possible (follow SAP conventions).
- Use **data elements** (`DTEL`) for every field — never raw types. This gives F1 help and consistent labels across all UIs.
- Use **domains** (`DOMA`) for fields with a fixed value set. Domain values auto-populate search help.
- All text tables have the same name with `T` appended: `ZCRP_WFT_STEPT` for `ZCRP_WFT_STEP`.

### 12.2 Catalog table pattern (from N_MENARD `YTHRWF_STEP` + `YTHRWF_STEPT`)

```
ZCRP_WFT_STEP        -- step definitions (step_seq, wfstep, wftype, ...)
ZCRP_WFT_STEPT       -- step text table (wftype, wfstep, spras, wfstept)
ZCRP_WFT_ACT_DEF     -- actor determination rules (actty, actca, whoou, objid, ...)
ZCRP_WFT_ACT_TY      -- actor type master (actty, email)
ZCRP_WFT_ACT_TYT     -- actor type text (actty, spras, actty_txt)
```

The text table always has `SPRAS` as a key field and exactly one text field. This enables `LEFT OUTER JOIN ... AND t~spras = @sy-langu` in step navigation queries.

### 12.3 Data element (`DTEL`) rules

- Name: `Z<DOMAIN>_DE_<FIELD>` or `ZE_<DOMAIN>_<FIELD>` for domain-backed elements.
- For fields that are keys in multiple tables (e.g., step identifier, actor type), create ONE data element and reference it everywhere.
- Never use `CHAR N` inline in a table definition — always go through a DTEL.
- `TYPE` references to standard SAP types (`P_PERNR`, `DATUM`, `UNAME`, `ORGEH`) are acceptable for standard HR/WF fields.

### 12.4 Domain (`DOMA`) rules

- Name: `ZD_<DOMAIN>_<FIELD>` or `ZE_<DOMAIN>_<PURPOSE>` (for enum-like domains).
- Domains with fixed values: add all values in SE11 → Values tab. Never hard-code the values in ABAP code — always SELECT from domain values or use a constant.
- `CHECK` constraint on table field = use domain fixed values, not a WHEN list in the DPC_EXT method.

### Data Dictionary — Extended patterns (from full D01 scan)

> Source: `YTHRWF_STEP_ACT` (DDIF_FIELDINFO_GET readback) + 193-TABL package census — N_MENARD D01 scan

**1. Assignment (N:M) table pattern.** Between two catalogs, the link table repeats both catalog keys
plus a sequence number, with the payload as non-key fields:

```
YTHRWF_STEP_ACT (actors per step)
  Key : MANDT + WFTYPE + WFSTEP + WFSUBSTEP + SEQNR (SEQN3, NUMC 3)
  Data: ACTTY  (YE_HRWF_ACTOR_TYPE)   " which actor type acts
        ACTCA  (YE_HRWF_ACTOR_CASE)   " actor case
        GOABAP (YE_HRWF_ABAP_DET)     " flag: actor resolved by ABAP code instead of catalog
```

Rules: `SEQNR` is part of the key (multiple actor assignments per step, ordered); every field is a
`YE_*` data element; the `GOABAP` boolean is the **catalog escape hatch** — config says "this one is
ABAP-determined", keeping the 99% declarative while allowing code for the hard 1%. Copy this shape for
any step/actor, doc/condition, type/attachment link table.

**2. Name prefixes carry the object kind** (census of the 193 TABL entries — this is the convention):

| Prefix | Kind | Example |
|---|---|---|
| `YT<domain>_*` | Transparent table (catalog/config/temp-save) | `YTHRWF_STEP`, `YTHRPAWF_DRAFT` |
| `YS<domain>_*` | Structure (no DB) | `YSHRWF_ACTORS`, `YSHR_PDF_PAF` |
| `YSHR_DD_*` | Web Dynpro dropdown structure (one per dropdown) | `YSHR_DD_MASSN` |
| `YSHR_WD_*` | Web Dynpro context-node structure (one per infotype/view) | `YSHR_WD_0001` |
| `YSHR_R_*` | Range structure | `YSHR_R_ASTXT` |
| `ZSHR_JSON_*` | External JSON interface structures (SuccessFactors) | `ZSHR_JSON_CAND` |
| `YV*` | Maintenance view (paired with SE54-generated FUGR of the same name) | `YVHRWF_ACT_DEF` |
| `YE_*` | Data element | `YE_HRWF_ACTOR_TYPE` |

**3. Text-table suffix is `T` appended to the full name** (`YTHRWF_STEPT`, `YTHRWF_ACT_TYT`), or `_T`
when the bare `T` would collide (`YTHRINT_S` → `YTHRINT_S_T`). Both observed; prefer plain `T`.

**4. Temp-save / draft tables are first-class**: multi-screen WDA/Fiori flows persist intermediate state
in dedicated tables (`YTHRPAWF_TMP1..TMP4`, `YTHRPAWF_DRAFT`, `YTHRINT_T1..T3`) instead of holding it in
session memory — a numbered `TMPn` table per logical screen/topic.

**5. Every config table gets a maintenance view + SE54 dialog + IMG activity** — the package carries 33
`CUS0`/`CUS1` IMG objects and 33 `TOBJ` view-maintenance objects for its catalogs: config is maintained
via SM30/IMG by functional staff, never by direct table edits or code.

---

## 13. What NOT To Do — CRP Disaster Catalogue

These failures each cost multiple sessions of wasted effort on the CRP project. Each has a real incident reference.

### Category A — Architecture failures

**A1: Monolith class** — `ZCL_ZPSM_PROC_FORMS_DPC_EXT` grew to ~3870 lines with all business logic inside OData handler methods. Result: impossible to unit-test, impossible to reuse, impossible to extend without merge conflicts.

> Do: Move business logic into domain classes (`ZCL_CRP_WF_MAIN`, `ZCL_CRP_CERT_READER`, etc.). DPC_EXT methods should be 10-30 lines of orchestration.

**A2: Hardcoded CASE on step numbers** — original BOR `ADVANCESTEP` had `CASE CRP_CURRENT_STEP. WHEN '01'. WHEN '02'. ...`. Adding a step required touching the code.

> Do: Use catalog-driven step navigation (Pattern 3). Read step sequence from `ZCRP_WFT_STEP`. Next step = `step_seq + 1`. Zero hardcoded CASE blocks on step identifiers.

**A3: No factory pattern** — `ZCL_ZPSM_PROC_FORMS_DPC_EXT` directly instantiated concrete classes (`CREATE OBJECT lo_cert TYPE zcl_crp_cert_reader`). Every caller bound to the concrete type.

> Do: All object creation goes through factory. Callers receive `TYPE REF TO zif_crp_*` interfaces.

**A4: No interface contracts** — methods declared `PUBLIC` in concrete classes, callers use `zcl_crp_wf_main=>` prefix. Interface change = all callers break.

> Do: Callers reference only `zif_crp_wf_main` type. Factory returns interface references.

**A5: No lazy caching** — every `GetActorsForStep` call re-read all actor definition tables even when the wftype hadn't changed.

> Do: Pattern 5 — check `IF mt_act_def IS INITIAL` before SELECT.

### Category B — Type system failures

**B1: `LIKE field` instead of `TYPE table-field`** — `HRP1001-SOBID` is `CHAR 8` on ECC 6.0. If you declare `lv_objid LIKE hrp1001-sobid` on a system where the type maps differently, you get silent truncation. (S-40: `HROBJID` is `NUMC 8`, not `CHAR 8`.)

> Do: Always `lv_objid TYPE hrp1001-sobid` (uses the actual DDIC type). If you need to assign to a different field, use explicit type-casting or an intermediate variable.

**B2: EXT struct missing BASE fields** — if `TY_MYENTITY_EXT` does not include all fields of `TS_MYENTITY` (the SEGW-generated base struct), IWBEP property metadata serializes every property using offsets computed at metadata-build time. A missing BASE field shifts all subsequent fields by that field's byte width. Result: `StepName='y'`, `Status='13820000005'` (garbled fragments). (S-74/S-77.)

> Do: `TY_MYENTITY_EXT` must contain every field of `TS_MYENTITY` in the same order with the same lengths. Append new fields only at the end.

**B3: EXT-only fields silently dropped on APPEND** — `et_entityset` in a redefined `*_GET_ENTITYSET` method has the BASE type. `APPEND ls_item TO et_entityset` does name-based copy — EXT-only fields are dropped silently. (S-74/S-77.)

> Do: Either (A) write EXT-only data to a BASE field that has sufficient length (e.g., write cert request number to `requestid CHAR 20`), or (B) accumulate in a local `STANDARD TABLE OF TY_MYENTITY_EXT` then use `copy_data_to_ref` to bypass the APPEND truncation.

**B4: Em-dash in comments** — `–` (Unicode em-dash) in ABAP source deploys as `?` through ADT `read_ascii()` pipeline. Syntax check passes but the comment is corrupted in the repository and on D01. (S-114.)

> Do: Use only ASCII hyphens `-` in all ABAP source files.

**B5: Method name truncation** — SEGW-generated `*_GET_ENTITYSET` method names are computed as the first 16 characters of the entity set name + `_GET_ENTITYSET`. If the entity set name exceeds 16 chars, the method name is truncated. (S-77 latent bug.)

> Do: Verify the actual method name in the DPC_EXT class before coding. Do not assume the entity set name maps directly.

### Category C — ADT deploy pipeline failures

**C1: Wrong corrNr** — using a released transport request as `corrNr` in a PUT operation returns `ExceptionResourceSaveFailure 500`. Only an open (unreleased) workbench TR works. (S-110.)

> Do: Before any deploy script run, verify the TR is open: SE09 → own TRs, status = modifiable.

**C2: Activation response interpretation** — `POST ?method=activate` returns HTTP 200 even when activation failed. The body contains the error. An empty body = success.

> Do: Check `len(response.text) == 0` after activation. Any non-empty body = error, log and stop.

**C3: Missing UNLOCK in try/finally** — if a PUT operation throws and the UNLOCK call is not in a `finally` block, a stale `ENQUEUE` lock remains. The next deploy attempt will fail with "object locked". User must clear via SM12. (S-110.)

> Do: Always wrap ADT lock/unlock in try/finally. The UNLOCK call must execute even on exception.

**C4: Forgetting to redeploy DPC_EXT after "Generate Runtime Objects"** — SEGW "Generate" overwrites the DPC_EXT class. Any hand-edits to DPC_EXT are lost. (SKILL.md §6.)

> Do: Immediately after SEGW generate, redeploy DPC_EXT from source. Treat "Generate" as destructive.

**C5: Wrong TR family** — DDIC objects (tables, structures, data elements) belong in a DDIC transport request. Workbench objects (classes, FMs, programs) belong in a workbench TR. Mixing them causes activation order problems.

> Do: One DDIC TR, one workbench TR. Know which is which before creating objects.

**C6: Editing local file without reading D01 first** — the local `artifacts/custom-objects/` copy may be stale. Encoding issues, prior session changes, or out-of-band modifications on D01 make the local copy diverge. Editing stale local and deploying overwrites the live version with the old one. (S-113/S-114.)

> Do: ADT GET before any Edit. Save the readback to `artifacts/readback/sNN/`. Edit the readback copy, then deploy.

**C7: Touching `_MPC` / `_DPC` base class** — these are auto-generated by SEGW. Any edit is overwritten on the next "Generate". Only `_MPC_EXT` and `_DPC_EXT` are hand-editable.

> Do: Never modify `_MPC` or `_DPC`. All customization goes in `_MPC_EXT` and `_DPC_EXT`.

**C8: POST `?method=activate` format** — the activation call is a POST with query parameter `method=activate` and an XML body listing the objects. Getting the URL format wrong produces cryptic 400 errors.

> Do: Copy the proven activation format from `deploy_final.py` line by line. Do not reconstruct from documentation.

**C9: Not verifying activation response body** — HTTP 200 from activation does not mean the object activated successfully. SAP returns 200 with an error XML body on many activation failures.

> Do: Log and inspect `response.text`. Any non-whitespace content = activation error.

### Category D — OData / DPC_EXT failures

**D1: FunctionImport HTTP method mismatch** — a FunctionImport declared as `HttpMethod="GET"` in SEGW but called with POST (or vice versa) returns HTTP 405. This was misdiagnosed as a JSON encoding bug for 6 sessions (S-38→S-43).

> Do: Read `$metadata` first. Confirm `HttpMethod` for every FI. `GET` FIs use query string params. `POST` FIs use request body.

**D2: SAP reserved parameter names** — parameters named `ValidFrom`, `ValidTo`, `Filter`, `Top`, `Skip`, `Format`, `Expand`, `Select`, `OrderBy` conflict with OData system query options. SAP Gateway returns HTTP 404 for FIs with these param names. (S-41.)

> Do: Rename to `DateFrom`, `DateTo`, or any non-reserved name in SEGW.

**D3: All declared FI params must be sent** — on ECC 6.0, omitting a declared FunctionImport parameter (even if optional) causes HTTP 404. Send `''` (empty string) for unused optional params.

**D4: JSON params must not be percent-encoded** — the ABAP `extract_json_field` helper cannot parse `%22value%22`. Params must arrive as raw JSON (`"value"`). Vite proxy or fetch encoding can silently encode quotes.

> Do: In React, pass JSON-serialized params as raw strings. Check Network tab URL/body if a param is not arriving correctly.

**D5: CSRF token before GET** — fetching a CSRF token (`x-csrf-token: Fetch`) contaminates the session cookie. Subsequent GETs that expect no session state can return 400.

> Do: Fetch CSRF token only before POST/PUT/DELETE operations.

**D6: REDEFINITION in wrong visibility section** — a method declared in `PUBLIC SECTION` of the interface must be redefined in `PUBLIC SECTION` of the implementing class. Putting `REDEFINITION` in `PROTECTED SECTION` causes an activation error.

> Do: `METHODS zif_xxx~method_name REDEFINITION.` must appear in the same visibility section as the original declaration. For interface methods: always PUBLIC.

---

## 14. ADT Deploy Pipeline Rules

These rules govern the Python-based ADT deployment used in the UNESCO CRP project.

### 14.1 Deploy order (frozen sequence)

1. Lock object (`PUT /source/main?lockHandle=...` first requires a lock token from `POST /adtcore/locks`)
2. PUT source (upload `.clas.abap` or equivalent)
3. Activate (`POST ?method=activate` with XML body listing the object)
4. **Check activation response body** — empty = success, any content = error
5. Unlock (must be in `finally` block)
6. Readback verify (ADT GET of the deployed source to confirm content matches)

### 14.2 ABAP source file encoding requirements

- Line endings: **LF only** (Unix). Windows CRLF causes SAP save failures.
- Encoding: **ASCII** (UTF-8 with no non-ASCII characters). Em-dashes, curly quotes, accented characters in comments all deploy as `?`.
- Git `autocrlf` on Windows: set to `false` for `artifacts/` directories, or use `.gitattributes` with `* text=auto eol=lf` for ABAP files.

### 14.3 TR selection rules

```
DDIC objects  → use DDIC transport request (category: Workbench/Customizing, object type: TABL/DTEL/DOMA/...)
Class/FM/BOR  → use workbench transport request (category: Workbench, object type: CLAS/FUGR/PDTS/...)
```

Never mix. If unsure: SE09 → open TR → check contained objects → infer category.

---

## 15. OData / DPC_EXT Rules

### 15.1 DPC_EXT method naming formula

SEGW generates `*_GET_ENTITYSET` method names as: first 16 characters of entity set name + `_GET_ENTITYSET`.

Example: entity set `WORKTASKITEMCOLL` (16 chars) → method `WORKTASKITEMCOLL_GET_ENTITYSET`.

If the entity set name is longer than 16 chars, the method name is truncated at 16. Always verify the actual method name via ADT before redeclaring.

### 15.2 EXT struct superset rule

When extending an entity with additional fields:

```abap
" BASE struct (from SEGW generated MPC)
TYPES: BEGIN OF ts_worktaskitem.
  INCLUDE TYPE zcl_z_crp_srv_mpc=>ts_worktaskitem.  " All base fields
  request_number TYPE char7.   " WRONG — EXT-only field
TYPES: END OF ts_worktaskitem_ext.

" CORRECT:
TYPES: BEGIN OF ts_worktaskitem_ext.
  " First: every BASE field in exact same order and length
  requestid     TYPE char20.   " BASE field 1
  stepname      TYPE text60.   " BASE field 2
  status        TYPE char20.   " BASE field 3
  " ...all remaining BASE fields...
  request_number TYPE char7.   " NEW field appended at end
TYPES: END OF ts_worktaskitem_ext.
```

### 15.3 Writing to et_entityset safely

```abap
" SAFE pattern A: write EXT-only data into a BASE field of sufficient length
ls_item-requestid = lv_cert_request_number.  " requestid is CHAR 20, cert# is CHAR 7 — fits

" SAFE pattern B: accumulate locally as EXT type, then copy_data_to_ref
DATA lt_local TYPE STANDARD TABLE OF ts_worktaskitem_ext.
" ... fill lt_local ...
copy_data_to_ref( EXPORTING is_data = lt_local CHANGING cr_data = er_data ).
" IWBEP serializes via the bound EXT type directly — no truncation
```

### 15.4 FunctionImport parameter checklist

Before deploying any FunctionImport change, verify:

- [ ] HTTP method in SEGW matches frontend fetch method
- [ ] All frontend-sent param names match SEGW declarations (case-sensitive)
- [ ] No SAP reserved param names (ValidFrom, ValidTo, Filter, Top, Skip, etc.)
- [ ] All declared params are sent from frontend, even if empty string
- [ ] `$metadata` reflects the change after activate+redeploy

---

*End of guide. For session-specific findings and pattern evolution, see `brain/sessions/` in the CRP project.*
