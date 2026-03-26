# UNESCO HCM: Infotypes & PA Screen Exits Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers IT0021 field control, PA screen exits, SPAU mods.

## Identified Enhancements

| Enhancement | Fiori? | Extracted Source | Key Finding |
|---|---|---|---|
| `ZHR_FIORI_0021` | YES | 44 lines (E-include) | Hides GOVAST/SPEMP/ERBNR on IT0021; makes WAERS read-only for Child/Spouse |
| `ZHR_SPAU_PA` | No | 2 ENHO children | Screen exits MP096200 + MP096500 for PA infotypes |
| `YENH_INFOTYPE` | YES | Container-only | Generic infotype screen exit — may affect PA26/PA30 Fiori |
| `YCL_HRPA_UI_CONVERT_0002_UN` | YES | Container-only | IT0002 UI field conversion for Fiori Personal Data |
| `YCL_HRPA_UI_CONVERT_0006_UN` | YES | Container-only | IT0006 UI field conversion for Fiori Address Management |

## Key Code: ZHR_FIORI_0021 Field Rules
| Field | Rule |
|---|---|
| `GOVAST` | Always INVISIBLE |
| `SPEMP` | Always INVISIBLE |
| `ERBNR` | Always INVISIBLE |
| `WAERS` | READ_ONLY when FAMSA='14' or '2' |

## Cross-References
- Family Management Analysis: Section 8
- Personal Data Analysis: Section 12
- Address Management Analysis: Section 6
