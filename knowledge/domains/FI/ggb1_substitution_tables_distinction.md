# GGB1 Substitution at UNESCO — Tables Distinction

**Discovered:** Session #050 (2026-04-09)
**Trigger:** Re-investigating INC-000006073 with the integrity check, I confused the YFI_BASU_MOD persistence table with the actual GGB1 condition tables and built the wrong cross-check. This document fixes that confusion for the next agent.

## TL;DR

| Table | What it is | Source of truth for GGB1? | Where to look it up |
|---|---|---|---|
| **GB901** | SAP standard substitution **conditions** (BOOLCLAS / SEQNR / BOOLEXP) | **YES** — this is the rule body | Gold DB (583 rows, extracted Session #048 for INC-000006073) |
| **GB922** | SAP standard substitution **values** (substitution result fields, exit IDs) | **YES** — this is the action body | Gold DB (218 rows) |
| **GB02C** | SAP standard substitution header registry | **YES** — links rules to call point | Gold DB (10 rows) |
| **YTFI_BA_SUBST** | UNESCO **persistence layer** for the user-friendly maintenance transaction `YFI_BASU_MOD` | **NO** — only feeds the exit `YCL_FI_ACCOUNT_SUBST_READ` called from `YRGGBS00` form `U910` | Gold DB (129 rows) |
| **YBASUBST** | Legacy **flat mapping** table (BUKRS / BLART / HKONT / GSBER) | **NO** — historical, replaced by YTFI_BA_SUBST | Gold DB (752 rows) |
| **T077K** | Vendor **account group definitions** (field selection per group) | **NO** — does NOT carry AKONT mapping. AKONT is set on LFB1 manually at vendor creation | Gold DB (47 rows, 23 cols) |

## Why this matters

**INC-000006073 root cause cites GGB1 rule `3IIEP###002`** which only covers `HKONT=2021042` and `2021061` for `BLART=TV/TF` in IIEP. That rule lives in **GB901** (the condition) + **GB922** (the substitution value `GSBER=PAR`).

**It does NOT live in YTFI_BA_SUBST.** YTFI_BA_SUBST is a parallel UNESCO mechanism — it's the persistence layer for a user-friendly maintenance transaction (`YFI_BASU_MOD`) that lets functional consultants add range-based mappings without raising a transport. The `YFI_BASU_MOD` flow is read from a custom GGB1 substitution **exit** (`YCL_FI_ACCOUNT_SUBST_READ` called from `YRGGBS00` form `U910`), which acts as ONE step inside the GGB1 chain.

The GGB1 chain at UNESCO has multiple steps for travel posting:

```
GGB1 substitution for travel posting in IIEP (call point 0001 — Document Header / Line Item):
  Step 001: Exit U910 → reads YTFI_BA_SUBST via YCL_FI_ACCOUNT_SUBST_READ
            (UNESCO's "no-transport" range-based maintenance)
  Step 002: Standard rule 3IIEP###002 → GB901 condition + GB922 substitution
            (covers GL 2021042/2021061 → GSBER=PAR)
  Step 003: Standard rule 3IIEP###004 → GB901 + GB922
            (TV/TF → GSBER=PAR unconditional, but executes inside BAPI simulation
             AFTER mandatory field check, so may not rescue empty GSBER for vendor lines)
```

## Confusing the two will misdiagnose every BusA derivation incident

Cross-checking a vendor's AKONT against YTFI_BA_SUBST tells you whether the **YFI_BASU_MOD layer** would catch it. It does NOT tell you whether the **standard GGB1 rules** would catch it. To check the latter, query GB901 + GB922 in Gold DB by `BOOLID = '<3-digit step prefix><call point><company code><###><seq>'`.

For INC-000006073:
- `YTFI_BA_SUBST` has **0** entries for AKONT in the 2021xxx range — would suggest no UNESCO custom coverage exists.
- `GB901` has rule `3IIEP###002` which DOES cover 2021042 and 2021061 — that's why the 61 other IIEP travelers worked.
- The defect is that 2021011 is in NEITHER table.

## What the brain knows about each

| Table | In `brain_state.objects`? | Annotated? |
|---|---|---|
| GB901 | Was a blind spot (Session #050) — should be force-included via incidents.related_objects | TBD |
| GB922 | Was a blind spot (Session #050) — should be force-included via incidents.related_objects | TBD |
| YTFI_BA_SUBST | YES | YES (`COVERAGE_GAP` annotation: "IIEP has zero global rules. All 12 entries restricted to doc type Z1") |
| YBASUBST | Was a blind spot — referenced but not modeled | TBD |
| T077K | YES | YES (with the wrong claim "KTOKK=UNES maps to AKONT=2021042 (covered by GGB1)" — T077K does NOT store AKONT, this annotation should reference data observation, not a T077K column) |

## Action items

- [ ] Triage GB901 / GB922 / YBASUBST out of `brain_state.blind_spots` — they ARE in Gold DB and need first-class brain modeling (not just rows)
- [ ] Fix the T077K annotation to clarify that AKONT mapping is observed from LFB1 data, not stored in T077K
- [ ] When investigating any BusA / GSBER substitution issue, query **GB901 + GB922 first**, then YTFI_BA_SUBST as a secondary check

## Related

- Incident: [INC-000006073](../../incidents/INC-000006073_travel_busarea.md)
- Incident: [INC-000005240](../../incidents/INC-000005240_xref_office_substitution.md) — XREF office-tagging
- Domain: [Travel](../Travel/README.md)
- Vendor master: [BusinessPartner](../BusinessPartner/README.md)
- Quality check: [vendor_master_integrity_check.py](../../../Zagentexecution/quality_checks/vendor_master_integrity_check.py)

## Appendix A — GB93 + GB931 (Validation tables — discovered via RFC Session #051)

GB93 and GB931 were successfully extracted via `RFC_READ_TABLE` on 2026-04-09 and deserve their own section for future FI substitution/validation incidents.

### GB93 — Validation rule header (17 rows at UNESCO P01)

| Field | Meaning |
|---|---|
| `VALID` | Validation rule name (e.g., `UNES`, `IIEP`, `ICTP`, `01-CS01`, `0_CO_1`) |
| `BOOLCLASS` | Boolean class (`001`=CO, `008`=FI doc header, `009`=FI line item, `030`=Asset, `043`=?, `201`=FM) |
| `MSGID` | Message ID for validation failures (`ZFI`, `Z0`, `K2`, `ZFM`, etc.) |
| `GBOPCREATE` / `GBDTCREATE` | Creation user / date |
| `GBOPCHANGE` / `GBDTCHANGE` | Last-change user / date |
| `MULTILINE` | Indicates multi-line validation check |

**UNESCO-relevant row:**
```
VALID='UNES' BOOLCLASS='009' MSGID='ZFI' 
Created 2007-09-05 by M_SPRONK
Last changed 2026-10-11 by FP_SPEZZANO
```

### GB931 — Validation step header (12 rows for VALID='UNES')

| Field | Meaning |
|---|---|
| `VALID` | Validation rule name (parent) |
| `VALSEQNR` | Step sequence number (001, 002, …) |
| `CONDID` | CONDITION BOOLID — the prerequisite BOOLEXP that gates the check |
| `CHECKID` | CHECK BOOLID — the assertion that must evaluate TRUE |
| `VALSEVERE` | Severity: `E`=error (blocks posting), `W`=warning, `I`=information |
| `VALMSG` | Message number (lookup in MSGID from GB93) |
| `MSGTAB1..4` / `MSGFIELD1..4` | Table/field for error message context |
| `WORKFLOW` | Workflow trigger (if any) |

The 12 UNES validation steps are fully documented in [INC-000005240](../../incidents/INC-000005240_xref_office_substitution.md) §3.4.3.

### GB905 / GB921 — Substitution step linkage (EMPTY at UNESCO)

These tables are expected to link SUBSTID + step to a BOOLID prerequisite (for SUBSTITUTION, analogous to GB931 for VALIDATION), but both return **0 rows** via RFC_READ_TABLE at UNESCO P01. Two interpretations:

1. UNESCO's substitution runs through a custom path (not standard GGB1 UI maintenance)
2. The step prerequisites are implicit via naming convention: `3<SUBSTID>#<STEP>` maps to GB901 BOOLID

Empty GB901 entries for a step are interpreted as "empty prerequisite → fires unconditionally on every line at the callpoint".

## Appendix B — BOOLID naming convention (decoded Session #051)

GB901 BOOLIDs follow a `<prefix><name><separator><seq>` pattern at UNESCO:

| Prefix | Purpose | Example | Function |
|---|---|---|---|
| `1` | Validation **CONDID** (prerequisite) | `1UNES###005` | Gates WHEN to check at validation callpoint (stored in GB931.CONDID) |
| `2` | Validation **CHECKID** (assertion) | `2UNES###005` | The actual TRUE/FALSE check that must pass (stored in GB931.CHECKID) |
| `3` | Substitution step **prerequisite** | `3UNESCO#005` | Gates WHEN to fire a substitution step at callpoint 3 (implicit — GB905 empty) |
| `F` | (Rare) SAP standard | `FC` | 1 row, SAP-delivered |
| `0` | Asset/misc | `0S-10`, `0S-20` | SAP standard patterns |

**Separator rules:**
- 4-char names (e.g., `UNES`) use `###` padding: `1UNES###001`
- 6-char names (e.g., `UNESCO`) use `#` padding: `3UNESCO#001`

**Cross-reference:**
- For a validation step `VALID='UNES' VALSEQNR='012'`:
  - CONDID = `1UNES###009` (the prerequisite)
  - CHECKID = `2UNES###009` (the check)
  - These are NOT the same step number — VALSEQNR is the row index in GB931, while the BOOLID suffix (009 here) is the internal BOOLEXP identifier
- For a substitution step `SUBSTID='UNESCO' SUBSEQNR='005'`:
  - The prerequisite BOOLID is conventionally `3UNESCO#005`
  - If that BOOLID does not exist in GB901, the step has no prerequisite and fires unconditionally

## Appendix C — T80D form pool registration

T80D registers custom form pools for the GGB0 / GGB1 callpoint framework. UNESCO's relevant entries:

```
T80D  MANDT='350'  ARBGB='GBLR'  FORMPOOL='YRGGBS00'    ← GGB0 FI validation
T80D  MANDT='350'  ARBGB='GBLS'  FORMPOOL='YRGGBS00'    ← GGB1 FI substitution
```

Both the validation framework (GB93/GB931) and the substitution framework (GB922) dispatch their exit-call steps to `YRGGBS00` at UNESCO. This means forms like `U915`, `U916`, `U917` (validation) and `UXR1`, `UXR2`, `UZLS`, `UAEP`, `UATF`, `U910` (substitution) all live in the same ABAP include.
