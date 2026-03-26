# UNESCO HCM: Benefits & Fiori Sub-Domain Analysis

> Sub-domain of `knowledge/domains/HCM/`. Covers benefit enrollment, family benefits, Fiori generics.

## Identified Enhancements

| Enhancement | Package | Area | Fiori? | Key Finding |
|---|---|---|---|---|
| `YHR_ENH_HRFIORI` | `ZHRBENEFITS_FIORI` | Generic HCM Fiori | YES | Direct Fiori HCM enhancement in Benefits Fiori package |
| `YHR_ENH_HRCOREPLUS` | `ZHR_DEV` | HR Core+ | YES | HR Core+ Fiori Foundation integration |
| `ZCOMP_ENH_SF` | `ZHR_DEV` | SuccessFactors | YES | SF integration layer; may affect OData services for iFlow/BTP |

## Extracted Code
- All three are container-only ENHC wrappers
- Logic lives in linked BAdI/integration classes
- `YHR_ENH_HRFIORI` — package `ZHRBENEFITS_FIORI` is the key scope for benefits Fiori extraction

## Cross-References
- [Fiori App Analysis: Benefits Enrollment](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/HCM/Fiori%20Apps/hcm_family_management_analysis.md)
- Benefit enrollment OData: `ZHCMFAB_BEN_ENROLLMENT_SRV`
