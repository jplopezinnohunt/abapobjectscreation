# UNESCO HCM: Payroll Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers UNJSPF pension, PRAA, SPAU payroll enhancements.

## Identified Enhancements

| Enhancement | Area | Fiori? | Key Finding |
|---|---|---|---|
| `ZHR_PENSION` | Pension / UNJSPF | YES | Pension infotype logic; may affect Fiori personal data/payroll apps |
| `ZHR_SPAU_PY_CPSIT_PGM_001` | Payroll SPAU | No | Screen exit for PITGPCODE payroll variant |
| `Y_ENH_PRAA` | Payroll PRAA | No | Payroll remuneration accounting enhancements |
| `YHR_ENH_HUNCPFM0` | Payroll / UNJSPF | No | UNJSPF participation date logic (3 E-includes extracted) |

## Extracted Code with Source
### YHR_ENH_HUNCPFM0 (3 includes extracted)
- `YHR_ENH_HUNCPFM0_CHECK========E.abap` (12 lines)
- `YHR_ENH_HUNCPFM0_PART_DATE====E.abap` (14 lines)
- `YHR_ENH_HUNCPFM0_START========E.abap` (8 lines)

Location: `extracted_code/ENHO/_by_domain/HCM/Payroll/`
