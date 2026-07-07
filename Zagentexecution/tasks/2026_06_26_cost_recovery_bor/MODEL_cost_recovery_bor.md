---
name: Cost Recovery → BOR — General derivation model (applicable to all staff)
description: A model to derive the cost-recovery R1 + monthly BOR supplement for ANY staff. Feasibility-tested on 501 staff + live HR. Structural fields (funds center/fund) are HR-derivable; the project split/amount is NOT (no timesheet) — manual input.
type: project
created: 2026-06-26
---

# Cost Recovery → BOR — General Model (¿se puede hacer?)

## Verdict: PARTIALLY automatable
- ✅ **The BOR skeleton (account assignment) IS derivable** from HR + a mapping table.
- ❌ **The economic content (which project, how much, which months) is NOT derivable** — no timesheet / cost-distribution exists; it is a business decision keyed by the office.

## The 7 components of every cost recovery

| # | Field | Source | Automatable? |
|---|---|---|---|
| 1 | **Staff** (PERNR) | the employee (e.g. 10025831 = A. Dominguez) | ✅ given |
| 2 | **Recovery funds center** (office) | HR org assignment → duty station / sector → FISTL | ✅ via mapping (built below) |
| 3 | **Fund** `633CRP<cat><off>` | office (#2) + funding category | ⚠️ office=✅, category needs the source project's funding line |
| 4 | **Commitment item** | fixed `TC` | ✅ constant |
| 5 | **Pool (credit)** | fixed `633CRP9003` | ✅ constant |
| 6 | **Source project + amount** | business decision (how much of the staff's time each project used) | ❌ **manual** — no source data |
| 7 | **Period (months)** | the months the staff supported the project | ❌ **manual** |

## Feasibility evidence

### #2 Funds center — HR-derivable (tested on 14 live + 501 from data)
The recovery funds center is the staff's **duty station (field) or sector (HQ)**, which lives in HR — but it is **NOT a single field**; it needs the org-unit/personnel-area → FISTL mapping:
```
PERNR → PA0001 org unit → (org hierarchy / personnel area WERKS-BTRTL) → recovery FISTL
e.g.  10054992 → org unit 3012 "ADMIN/OPS & HR UNIT"      → OPC   (HQ sector)
      10078048 → org unit 50032847 "ADMINISTRATIVE UNIT"   → YAO   (field duty station)
      10145436 → org unit 50032843 "ADMINISTRATIVE UNIT"   → TAS   (field)
```
- Field staff → FISTL = duty station (≈ personnel area). HQ staff → FISTL = sector funds center.
- **90% of staff (449/501) map to ONE stable office** → the mapping is real and learnable.
- The 10% multi-office = mobility (use the assignment valid at the recovery date).
- **The mapping table is already BUILDABLE** from recovery history (`staff_office_map.json`, 501 entries) cross-checked with PA0001.

### #3 Fund — office=✅, category needs the project
`633CRP` + `[category 2d]` + `[office 2d]`. Office derives from #2. The **category** (funding line, dominant `73`) comes from the **source project's funding source** — derivable only once the project (#6) is known.

### #6/#7 The split — NOT derivable (the wall)
Checked all standard sources live for staff 10025831 — **all empty**:
- `PA0027` (Cost Distribution) — empty
- `CATSDB` (timesheets) — empty
- `PA0014` (recurring pay) — empty

⇒ There is **no system record of how the staff's time splits across projects monthly**. The recovery R1 (period lump) IS the finest granularity. The split is an **office estimate**, entered manually. Cannot be reconstructed from SAP.

## The model (pseudo)
```
FUNCTION build_recovery(PERNR, [(project, amount, period)...], date):   # the list = MANUAL input
    office = HR_office(PERNR, date)          # PA0001 org → mapping table   ✅ auto
    for (project, amount, period) in lines:
        category = funding_category(project)  # project funding line        ⚠️ from project master
        fund     = '633CRP' + category + office_code(office)                 ✅ auto
        # R1 (FI):
        post  Dr  GL 6046014/6046013  fund=project   FISTL=project_sector(project)   amount
              Cr  GL 7046013/7034011  fund=633CRP9003 FISTL=office              amount   # pool
        # accumulate for the monthly BOR:
        bor_line(fund=fund, FUNDS_CTR=office, CMMT_ITEM='TC', amount=amount, period=period)
    # monthly: Y_FMKU_0050_CREATE_WITH_COMMIT(PROCESS='SUPL', items=bor_lines, TESTRUN='X')
```

## What "se puede hacer" means concretely
| Part | Can we automate it? | How |
|---|---|---|
| Derive funds center / fund / cmmt item / pool | **YES** | HR org → mapping table (built from data) |
| Generate the R1 + BOR payload structure | **YES** | the pseudo above → `Y_FMKU_0050` (testrun) |
| Decide which project & how much & which months | **NO** | business input — no timesheet exists |
| Validate / reconcile the result | **YES** | the text key `CR <proj> ... <PERNR> <period>` ties R1↔BOR |

## Conclusion
**The model is buildable and worth building** as a *derivation + assembly engine*: feed it `(PERNR, project, amount, period)` and it derives the funds center (HR), the `633CRP` fund, and emits the R1 + monthly BOR for `Y_FMKU_0050`. The **only non-automatable input is the time-split** (which project / how much), because UNESCO records no timesheet for these staff — that stays a human decision. So it removes the manual re-keying of *account assignment* (the error-prone part), not the *allocation judgement*.

## Data products
- `staff_office_map.json` — 501 staff → recovery office (90% stable).
- Office → `633CRP` fund map (from the 28-fund supplement decode).
- Sibling: [CASE_staff_10025831_e2e.md](CASE_staff_10025831_e2e.md), [TECH_SPEC_Y_FMKU_0050.md](TECH_SPEC_Y_FMKU_0050.md).

## Open to fully close
- Build the `org-unit/personnel-area → FISTL` mapping table from PA0001 for all 501 (currently learned from recovery history; HR makes it forward-looking).
- The category (`#3`) → read the source project's funding-line attribute (project master / grant).
