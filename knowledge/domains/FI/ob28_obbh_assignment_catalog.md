# OB28 / OBBH Assignment Catalog — UNESCO

**Source:** D01 live extract 2026-04-15 via `RFC_READ_TABLE` on `T001D`, `GB92`, `GB93`, `GB90`, `GB901`, `GB921`, `GB922`.
**Purpose:** Single source of truth for *which* validation/substitution rule applies to *which* company code at *which* callup point — answers the question that arises whenever a new company code is created ("do we need to assign a validation or substitution?").

---

## Status of this document

**Partially verified. Correction posted 2026-04-15.** The initial version of this doc concluded both OB28 and OBBH assignments live in `T001D`. Subsequent OBBH screenshot review proved that incorrect: `T001D` holds validations only; OBBH substitution assignments live in a separate table not yet identified (DD03L cross-index search via field names `SUBSTID`/`VALID` did not surface it, suggesting the field has an SAP-internal alias). Sections below reflect the corrected understanding.

## 1. The VALIDATION assignment table — `T001D`

At UNESCO, **validation assignments (OB28) live in `T001D`**. **Substitution assignments (OBBH) do NOT live in `T001D`** — they are stored in a different table not yet identified via RFC_READ_TABLE probing.

| Col | Meaning |
|---|---|
| `MANDT` | Client |
| `BUKRS` | Company code |
| `EVENT` | Callup point (0001 Doc Header, 0002 Line Item, 0003 Complete Document) |
| `VALID` | Rule ID (name of a rule defined in `GB92` or `GB93`) |
| `ACTIV` | Activation level (0=inactive, 1=warning, 2=error, 3=error+cancel) |

---

## 2. Table 1 — Overview (what is assigned to each company code)

**Observed 2026-04-15 in D01** — full content of `T001D` (8 rows total, all validations, zero substitutions assigned):

| BUKRS | Callup (EVENT) | Type | Rule ID | Active | Activation Level |
|---|---|---|---|---|---|
| ICTP | 0001 Doc Header | Validation | ICTP_HE | ✅ | 1 |
| ICTP | 0002 Line Item | Validation | ICTP | ✅ | 1 |
| IIEP | 0002 Line Item | Validation | IIEP | ✅ | 1 |
| UBO | 0002 Line Item | Validation | UBO | ✅ | 1 |
| UIL | 0002 Line Item | Validation | UIL | ✅ | 1 |
| UIS | 0002 Line Item | Validation | UIS | ✅ | 1 |
| UNES | 0002 Line Item | Validation | UNES | ✅ | 1 |
| UNES | 0003 Complete Doc | Validation | ZZVFIDC | ❌ | 0 |

**Missing from T001D**: MGIE, ICBA, IBE, STEM — no validation or substitution assigned.

---

## 3. Table 2 — Rules defined in the system (but may not be assigned)

### 3.1 Validations (`GB93`) — 8 UNESCO-relevant

| Rule ID | BOOLCLASS | Msg Class | Assigned in T001D? |
|---|---|---|---|
| ICTP | 009 | ZFI | ✅ (ICTP, CP2) |
| ICTP_HE | 008 | ZFI | ✅ (ICTP, CP1) |
| IIEP | 009 | ZFI | ✅ (IIEP, CP2) |
| UBO | 009 | ZFI | ✅ (UBO, CP2) |
| UIL | 009 | ZFI | ✅ (UIL, CP2) |
| UIS | 009 | ZFI | ✅ (UIS, CP2) |
| UNES | 009 | ZFI | ✅ (UNES, CP2) |
| ZZVFIDC | 015 | ZFI | ✅ but INACTIVE (ACTIV=0) |

All UNESCO validation rules are assigned. GB93 also holds 9 non-institute rules (`AAMD*`, `ZAMR`, `0_CO_1`, `01-CS01`, etc.) that are not institute-specific.

### 3.2 Substitutions (`GB92`) — 10 UNESCO institute-named

| Rule ID | BOOLCLASS | Created by | Created on | Assigned in T001D? |
|---|---|---|---|---|
| IBE | 009 | M_SPRONK | 2009-11-03 | ❌ |
| ICBA | 009 | M_SPRONK | 2016-11-15 | ❌ |
| ICTP | 009 | R_ORSARIA | 2010-04-07 | ❌ |
| IIEP | 009 | B_GRUJIC | 2006-10-25 | ❌ |
| MGIE | 009 | M_SPRONK | 2013-01-14 | ❌ |
| UBO | 009 | A_CHAGAS-QUI | 2008-10-17 | ❌ |
| UIL | 009 | M_SPRONK | 2012-10-31 | ❌ |
| UIS | 009 | B_GRUJIC | 2006-10-25 | ❌ |
| UNESCH | 008 | FP_SPEZZANO | 2025-01-31 | ❌ |
| UNESCO | 009 | V.GUICHARD-D | 2001-09-24 | ❌ |

**Every institute has a substitution rule defined in `GB92`. Per OBBH screenshot (2026-04-15), all 9 institutes PLUS STEM are assigned at CallPnt 2 ActLvl 1** — contradicting the earlier claim that no substitutions were assigned. The OBBH assignment table itself has not been identified via RFC_READ_TABLE probing; confirmed via SAP GUI screen only.

The substitution logic is a blend: the OBBH-assigned GB92 rule executes, plus the `YRGGBS00` user exit intercepts via `EXITSUBST` hooks (U910, UXR1, UXR2, UZLS, UAEP, UATF per MGIE's rule). See [validation_substitution_matrix.md](../PSM/EXTENSIONS/validation_substitution_matrix.md).

### 3.3 MGIE substitution — actual content

For reference, MGIE's substitution rule has **8 steps** (`GB921`) calling **8 boolean prerequisites** (`GB90` IDs `3MGIE###001`..`###008`), with these substitution actions (`GB922`):

| Step | Prerequisite ID | Target table.field | Value / Exit |
|---|---|---|---|
| 001 | 3MGIE###002 | `BSEG-GSBER` | exit `U910` |
| 002 | 3MGIE###003 | `BSEG-GSBER` | constant `PFF` |
| 003 | 3MGIE###004 | `BSEG-XREF1` | exit `UXR1` |
| 004 | 3MGIE###005 | `BSEG-XREF2` | exit `UXR2` |
| 005 | 3MGIE###006 | `BSEG-ZLSCH` | exit `UZLS` |
| 006 | 3MGIE###007 | (exit only) | `UAEP` |
| 007.01 | 3MGIE###001 | `BSEG-FISTL` | constant `GEN` |
| 007.02 | 3MGIE###001 | `BSEG-GEBER` | constant `PFF` |
| 008 | 3MGIE###008 | (exit only) | `UATF` |

Same pattern applies to the other 9 institute substitutions (each with its own steps).

---

## 4. Decision tree for a new company code

```
Creating company code X
   │
   ├── Does X need a VALIDATION rule at callup 0001/0002/0003?
   │      NO  → precedent: MGIE, ICBA, IBE run without OB28 validation. Skip.
   │      YES → create rule in GGB0 + assign via OB28 (adds row to T001D).
   │
   ├── Does X need a SUBSTITUTION rule?
   │      YES — REQUIRED → precedent: ALL 9 institutes have a substitution
   │             assigned via OBBH at CallPnt 2 ActLvl 1 (per OBBH screenshot 2026-04-15).
   │             STEM was observed in the OBBH screen with Substitution=STEM.
   │             Action: create rule in GGB1 (typically named after BUKRS)
   │                   + assign via OBBH (CallPnt 2, ActLvl 1)
   │                   + add per-BUKRS branch to YRGGBS00 user exit (source code)
   │                     where derivation logic is encoded.
   │
   └── MANDATORY after any OB28/OBBH/GGB0/GGB1 change:
           → Run RGUGBR00 (or RGUGBR30 for FAGL New-GL) via SE38
             to regenerate the Boolean class code.
             Without this, the assignment exists but rules do NOT fire.
             Must be run separately in EACH environment (D01, P01) after
             every related transport import.
```

---

## 5. Key tables referenced

| Table | Purpose |
|---|---|
| **`T001D`** | **Assignment of validation/substitution to (BUKRS, EVENT, VALID, ACTIV)** |
| `GB92` | Substitution rule headers |
| `GB92T` | Substitution rule texts (multi-language) |
| `GB921` | Substitution step → condition (BOOLID in GB90) |
| `GB922` | Substitution action content (target table/field, value, exit) |
| `GB93` | Validation rule headers |
| `GB90` | Boolean rule headers (shared by validations & substitutions) |
| `GB901` | Boolean formula lines (prerequisite conditions) |
| `GB903` | Boolean short-names / set IDs |
| `GB90T` | Boolean rule texts |
| `GB01C` | Boolean class → (table, field) mapping |
| `GB02C` | Callup point → message ID |

---

## 6. Companion Excel

[`Zagentexecution/valsub_catalog_2026-04-15.xlsx`](../../../Zagentexecution/valsub_catalog_2026-04-15.xlsx) — two sheets:
- `1_Overview`: 26 rows (BUKRS × callup × rule — assigned and unassigned)
- `2_Detail`: 92+ steps with prerequisite formulas, target fields, exits

---

## 7. Related docs

- [validation_substitution_matrix.md](../PSM/EXTENSIONS/validation_substitution_matrix.md) — functional matrix of what each rule does
- [validation_substitution_autopsy.md](../PSM/EXTENSIONS/validation_substitution_autopsy.md) — technical deep-dive on YRGGBS00
- [ggb1_substitution_tables_distinction.md](ggb1_substitution_tables_distinction.md)
- [fm_validation_technical_autopsy.md](../PSM/EXTENSIONS/fm_validation_technical_autopsy.md)
