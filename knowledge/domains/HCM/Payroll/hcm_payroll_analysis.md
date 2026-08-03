# UNESCO HCM: Payroll Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers UNJSPF pension, PRAA, SPAU payroll enhancements
> (§1 below, extracted 2026-03-12), and — added s098 — the **payroll CALCULATION ENGINE itself**
> (§2): schemas, rules, wage types, features/gates, master data, and the posting path. §2 is
> sourced from `brain_v2/payroll_discovery.json` (ALGORITHM A16, `process_mining/payroll_discovery.py`)
> and claims #454–#464. Capability model: `brain_v2/capability_model/capability_model.json` →
> `HCM.subdomains.Payroll_Calculation`.

## 1. Custom code inventory (SPAU / UNJSPF / PRAA)

### 1.1 Identified Enhancements

| Enhancement | Area | Fiori? | Key Finding |
|---|---|---|---|
| `ZHR_PENSION` | Pension / UNJSPF | YES | Pension infotype logic; may affect Fiori personal data/payroll apps |
| `ZHR_SPAU_PY_CPSIT_PGM_001` | Payroll SPAU | No | Screen exit for PITGPCODE payroll variant |
| `Y_ENH_PRAA` | Payroll PRAA | No | Payroll remuneration accounting enhancements |
| `YHR_ENH_HUNCPFM0` | Payroll / UNJSPF | No | UNJSPF participation date logic (3 E-includes extracted) |

### 1.2 Extracted Code with Source
**YHR_ENH_HUNCPFM0 (3 includes extracted)**
- `YHR_ENH_HUNCPFM0_CHECK========E.abap` (12 lines)
- `YHR_ENH_HUNCPFM0_PART_DATE====E.abap` (14 lines)
- `YHR_ENH_HUNCPFM0_START========E.abap` (8 lines)

Location: `extracted_code/ENHO/_by_domain/HCM/Payroll/`

---

## 2. The payroll CALCULATION ENGINE (opened s098, ALGORITHM A16)

**Why this section exists:** before s098 the payroll engine was configuration that read like data —
neither a code search nor a table search reaches it, and no HR table at all was in the Gold DB (only
`PA0001` was extracted this session). It was a black box despite computing UNESCO's largest spend
category (staff cost). `A16_payroll_end_to_end` (`brain_v2/methods/algorithms.json`) discovers it in
7 parts: ENGINE (schemas) → LOGIC (rules) → OUTPUT (wage types) → GATES (features) → MASTER DATA →
POSTING path → RESOLVED POSTING (account determination from documents, added s098 mid-session after
3 failed configuration-based extractions). **The premise that makes it portable to any installation:**
payroll logic is named after WHAT IT PRODUCES, so the discovery runs from the output backwards as
well as from the driver forwards — a family of wage types sharing a stem and a phrase in their text
is a mechanism the schema layer will never mention.

Country grouping (MOLGA): **UN**. Raw inventory: `brain_v2/payroll_discovery.json`.

### 2.1 The engine (schemas)
**67 schemas, 45 custom.** Custom schemas run from a small set of country-specific drivers up through
a large ZN/ZC family: `YR00` (**the main driver**, 122 steps/111 active, calling YR2Q/YR3Q/YR67/YR68/YRPF),
`YN00`, `YN04`, `YN60`, `YR02`, `YR21`, `YR70`, the `ZN00`–`ZN90` series (largest: `ZN31` 91 steps,
`ZN60` 80 steps, `ZN70` 65 steps, `ZN00` 60 steps), `ZNFR`, `ZCCO`, `ZCN0`, `ZCN1`, `ZM01`, `ZT00`,
`ZTPF`, `ZRE1`, `ZRE2`, `ZREP`, `ZRET`, `ZSIS`, `ZNH3`, `ZNHC`, `ZNMH`, `ZNP4`, `ZNPB`, `ZNPO`, `ZP31`,
`ZP90`. Standard drivers underneath: `9SLD`, `PP00`, `UN00`, `UN01`–`UN70`, `XTBL`, `XTBS`.
Gold DB tables: **`T52C0`** (68,767 schema steps), **`T52C1`** (2,064 schema rows / 67 schemas).

### 2.2 The logic (rules)
**11,742 rules, 166,453 rule lines, 307 custom.** Largest custom rules: `YVAM` (224 lines), `ZN75`
(195), `ZP02` (170), `ZTPV` (144), `ZN76` (140), `YVAL` (136). Gold DB table: **`T52C5`**.
**Failure mode recorded (rule `feedback_compare_field_widths_before_more_extraction`):** searching
these 166,453 rule lines and the schema names for `EURX`/`BUDGET`/`CDR` returned **one false positive**
(`ABR` = the payroll program indicator, not a hit) — the mechanism is not visible from the rule layer.

### 2.3 The output (wage types) — where BR for Staff surfaced
**1,641 wage types, 0 custom** (all standard-namespace, grouped by stem). Gold DB tables:
**`T512T`** (182,899 rows, wage-type texts) and **`T512W`** (68,081 rows, processing classes).
Families with a **named mechanism** (grouping by stem + a shared phrase in the text — this is the
technique, not a one-off): stem `1` (267 members, "PROVISION"), stem `3` (14, "BUDGET"/"RESERVE"),
stem `6` (63, "BUDGET"/"RESERVE"), **stem `9` (99 members: 2 "PBC", 72 "CONSTANT DOLLAR")**.
**BR for Staff is exactly those 72 "Constant Dollar" wage types under MOLGA UN** (claim #454) —
invisible in both the schema and rule layers, found only by grouping wage types by stem.

### 2.4 The gates (features)
**2,888 features, 19 custom.** Each feature compiles to a generated program
`/1PAPA/FEAT<client><NAME>`, readable via `RPY_PROGRAM_READ` — a PE03 decision tree is not invisible,
it is just not where anyone looks. Gold DB tables: **`T549D`** (2,888, feature directory) and
**`T549B`** (112,366, decision-tree nodes). Custom feature names: `YCSIG`, `YFM01`, `YMBF1`, `YMBF2`,
`YPAAP`, `YPAF2`, `YWFNF`, **`YYCDR`**, `YYLGM`, `YYSAL`, `ZHL04`, `ZLSCH`, `ZP021`, `ZPREA`, `ZTRIF`,
`ZTVCK`, `ZVDTA`, `ZWTYP`. **`YYCDR` is the personnel budget-rate perimeter gate** — evaluated against
`PA0001` fields `PERSG`/`GSBER`/`WERKS` — and decodes to **2,086 employees, 8.8% of the workforce,
almost all in Paris** (claim #451).

### 2.5 Master data
**`PA0001`** (HR Org Assignment, 121,606 rows — the only HR table in the Gold DB before this session)
carries the fields feature `YYCDR` gates on. **Maintenance ratio (BY-HAND vs FED):** a change document
(`CDHDR`) carrying a transaction code was made by a person in a screen; a **blank** transaction code is
the signature of a BAPI/interface/batch. Measured on the accumulated history: `HR_IT1001` (org
assignment) **33.9% fed with no transaction**, `HR_IT1005` **65.9% fed**, `HR_IT1018` **46.9% fed**,
`HR_IT1000` **24.9% fed** — HR master data at UNESCO is fed as much as it is typed (claim #456).

### 2.6 The posting path — 11 custom enhancements
The posting program is the seam between payroll and accounting, and the seam is where an
installation reaches for an enhancement (claim #456). Hooked on the posting path:

| Hooked object | Enhancement | Type |
|---|---|---|
| `RPCIPE00` | `ZHR_SPAU_PY_IMPL_PGM_013` | PROG + REPS |
| `RPCIPE00_OLD` | `ZHR_POSTING_ACCOUNTS_PAYABLE` | PROG |
| `RPCIPE00_OLD` | `ZHR_POSTING_ACCOUNTS_PAYABLE_2` | PROG |
| `RPCIPE00_OLD` | `ZHR_POSTING_ACCOUNTS_PAYABLE_D` | PROG |
| `RPCIPE00_OLD` | **`ZHR_POSTING_ACCOUNTS_RETRO`** | PROG (retro posting — sits exactly where the account determination is decided, claim #464) |
| `HRPAD00INFTYUI` | `YENH_HRPAD00INFTYUI_0002` / `_0006` / `_0021` | ENHS (screen exits) |
| `HRBEN00PAYROLL` | `YHR_ENH_PAY_PROCESS_HEAL_PLANS` | FUGR |
| `HR_BEN_PAY_PROCESS_HEAL_PLANS` | `YHR_ENH_PAY_PROCESS_HEAL_PLANS` | FUNC |

**Registered in the master enhancement registry:** `knowledge/sap_custom_enhancement_registry.md` §16
(added s098 — this list previously existed only here and in `brain_v2/payroll_discovery.json`).

### 2.7 The account determination — read from the documents, not the configuration
**Why the configuration search structurally cannot work:** `T030-KTOSL` (FI account-determination
transaction key) is **CHAR(3)**; a payroll symbolic account (`T52EK-SYMKO`) is **CHAR(4)**. Two
different keys wearing the same field name — no join between them can ever succeed. This cost **three
extractions** before the field widths were compared (`DDIF_FIELDINFO_GET`) — see rule
`feedback_compare_field_widths_before_more_extraction`.

**Where the answer actually is: `PPDIT`** (payroll posting document items — NOT yet in the Gold DB,
read live via RFC, 4,000-row BUKRS=UNES sample). `PPDIT-KTOSL` carries the FI transaction key
(`HRA`/`HRC`/`HRF`/`HRK`, 3 characters — **do not read it as a symbolic account**, claim #463) and
`PPDIT-HKONT` the resolved GL account on the same row. Cardinality: **2 of 4 keys fan out to several
GL accounts** (HRC→5, HRF→5); **28 of 28 GL accounts belong to exactly one key**. One-to-many
forward, one-to-one back ⇒ the account is decided **beyond** the key — the transaction key is the
coarse FI bucket (from the employee's master data), the **wage type** picks the account inside it
(claim #464). Method generalization: rule `feedback_read_posted_documents_when_config_wont_yield`.

**The custom payroll-to-FM bridge: `T9POST`** (customer-range table, 2,673 rows / 133 symbolic
accounts). Shape: `SYMKO` (symbolic account) × `MOMAG` (employee grouping) → `BUKRS`, `GSBER`,
`KOSTL`, position, **`FISTL`** (fund centre), **`FINCODE`** (fund). It does **not** map to a GL
account at all — it maps to an **FM account assignment**, which is why every search through FI's
account determination (`T030`) could never find it (claim #463). Companion custom table:
**`T9FUND`** (payroll symbolic account → fund).

### 2.8 BR for Staff — the mechanism, closed; the amount, open
**The mechanism (claim #462):** of the 72 Constant Dollar wage types, 58 have both a base wage type
and the Constant Dollar twin configured, and **all 58 pairs post to the SAME symbolic account as
their base, with the sign reversed** — e.g. `0020`/`9020` → `+SPAL`/`-SPAL`, `0400`/`9400` →
`+HOUS`/`-HOUS`, `0050`/`9050` → `+PADJ`/`-PADJ`. `T512W` confirms this is **one uniform mechanism,
not 72 separate decisions** — all 72 share the identical processing-class chain and accumulation
wage type `800000000000`. The base posts the operational-rate value, the twin posts the fixed-rate
value against the same account with the sign inverted, so they net — the **same design as the
non-personnel side (A14) in a different language**, except here the difference is POSTED, not
computed by a report. Real volume: **49,577 HRPAY FI headers over 1,732,526 line items**.

**Why it ran only once:** gated by feature `YYCDR` (2,086 employees, 8.8% of workforce, mostly
Paris — §2.4), it ran for **one month, January 2025, and has not run since** (claims #452/#453,
user-confirmed: built, piloted, never put into production).

**What remains open — `AN-BR-STAFF-AMOUNT` (amount-open, see
`brain_v2/capability_model/execution_backlog.json`):** to turn the mechanism into a number, the
symbolic account has to resolve to a GL account, and **no table checked carries that link** — not
`T030B` (209 rows), not `T52EZ` (5,751 rows, confirmed a validity table not an assignment table), not
the custom `T9POST` (the 24 Constant Dollar symbolic accounts appear in NONE of its 2,673 rows,
consistent with the twin inheriting its base's assignment). On the FM side (A14) both valuations sit
on the same LINE so the difference was directly measurable; here they sit on the same ACCOUNT, and
until the account is named the netting cannot be separated from ordinary payroll movement. **This is
a genuine open gap, not an estimate** — no figure should be quoted for the staff-side BR amount.

### 2.9 Cross-references
- Claims: `brain_v2/claims/claims.json` #454–#464.
- Graph: `brain_v2/budget_rate_graph.json` (payroll node set, 11 nodes / 13 edges — A15 subject graph).
- Mechanism detail: `brain_v2/budget_rate_enhancements.json` (staff-side section).
- Shared method memory: `brain_v2/methods/algorithm_memory.json` subjects `_field_width`, `T9POST`,
  `PPDIT`, `_persistence`, `_read_the_documents_not_the_configuration`.
- Capability model: `brain_v2/capability_model/capability_model.json` → `HCM.subdomains.Payroll_Calculation`.
- Enhancement registry: `knowledge/sap_custom_enhancement_registry.md` §16.
- Gold DB catalog: `knowledge/gold_db_table_catalog.md` (payroll-engine tables section, added s098).
- **Known gap:** `PPDIT` and `PPDIX` (posting run index) are **read live only** — not yet persisted
  to the Gold DB, unlike their siblings `PPDHD` (2,868,628 rows), `T9POST`, `T9FUND`, `T52EL`,
  `T512W`, `T52EK` which ARE persisted. Any repeat query against the account determination needs a
  live P01 connection until `PPDIT`/`PPDIX` are loaded (`scripts/extraction/load_wide_tables.py` PLAN
  already declares them; the load has not yet completed for these two).
