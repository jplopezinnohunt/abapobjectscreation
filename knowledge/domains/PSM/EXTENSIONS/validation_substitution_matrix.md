# UNESCO Finance Validation & Substitution Matrix

This matrix provides a high-level technical summary of the rules governing financial postings, derived from the `YRGGBS00` exit pool and `YFI_BASU_MOD` framework.

| Object ID | Type | Intent / Business Purpose | Condition (Apply If...) | Result / Effect | Technical Object |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BA_SUBST** | Sub | **Custom BA Derivation** | G/L Account falls in range defined for BUKRS/BLART. | Substitutes `GSBER` (Business Area). | `YCL_FI_ACCOUNT_SUBST_READ` |
| **UAEP** | Sub | **Asset Expense Alignment** | Asset-related expense posting in `UNES`, `IBE`, `IIEP`. | Forces mapping of `GEBER` (Fund) and `KOSTL` (Cost Center) based on BA. | `YRGGBS00 -> FORM UAEP` |
| **UATF / NSAI**| Sub | **Technical Fund Isolation** | Technical fund substitution for Assets. | **Clears WBS Element (`PROJK`)** to avoid module conflicts. | `YRGGBS00 -> FORM UATF` |
| **U904** | Sub | **Payment Reporting link** | Payment Supplement (`UZAWE`) is PF, OP, or GE. | Forces `GSBER` to `PFF`, `OPF`, or `GEF`. | `YRGGBS00 -> FORM U904` |
| **U917** | Val | **SCB Indicator Compliance** | Vendor payment to specific countries. | Blocks posting if SCB indicator is missing/mismatched. | `YRGGBS00 -> FORM U917` |
| **UNES_GSBER** | Val | **Segment Integrity** | Company Code = `UNES`. | Restricts `GSBER` to `GEF`, `MBF`, `OPF`, `PFF`. | `GGB0 -> VALID ID: UNES` |
| **ICTP_BA** | Sub | **ICTP Localization** | Company Code = `ICTP`. | Forces `GSBER = PFF` and `FISTL = ICTP`. | `GGB1 -> SUBST ID: ICTP` |
| **IIEP_BA** | Sub | **IIEP Area Control** | Company Code = `IIEP`. | Forces `GSBER` to `PAR`, `IBA`, or `FEL` based on logic. | `GGB1 -> SUBST ID: IIEP` |
| **Bypass** | Excl| **The "Open Door"** | User ID exists in `YXUSER` for specific `XTYPE`. | **Skips all above technical substitutions/validations**. | `Table: YXUSER` |

## Master Data Dependencies
1.  **Fund Center (`FISTL`)**: Usually hardcoded to the Institute name (e.g., `ICTP`, `UIS`, `IIEP`) or `UNESCO` for headquarters.
2.  **Fund (`GEBER`)**: Derived from the Business Area for technical funds, or from the G/L for specific grants.
3.  **Cost Center (`KOSTL`)**: Hardcoded to `ADM` or specific technical IDs (`111023`, etc.) in the force-mapping routines.
