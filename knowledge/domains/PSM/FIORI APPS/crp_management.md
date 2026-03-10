# Domain Knowledge: CRP Certificate Management

## Overview
The **Certificate Request Process (CRP)** is a business domain focused on the lifecycle management of operational certificates. These certificates serve as authorization documents for financial and staff-related activities.

## Core Technical Objects

### OData Service: `Z_CRP_SRV`
- **Purpose**: Exposes certificate and budget data to frontend applications (e.g., Fiori).
- **Configuration**: [z_crp_srv_config.json](file:///c:/Users/jp_lopez/projects/abapobjectscreation/z_crp_srv_config.json)
- **Classes**: `ZCL_Z_CRP_SRV_DPC_EXT`, `ZCL_Z_CRP_SRV_MPC_EXT`.

### Key Entities
| Entity | Business Role | Mapping / SAP Table |
| :--- | :--- | :--- |
| `CrpCertificate` | Header-level document | Custom Header Table (likely `ZCRP_HDR`) |
| `CrpBudgetLine` | Financial allocation | Custom Item Table (likely `ZCRP_ITM`) |
| `CrpAttachment` | Supporting evidence | DMS or GOS (Generic Object Services) |

## Business Logic Patterns
1. **Approval Workflow**: Certificates move through states: `Draft` -> `Pending Approval` -> `Approved` -> `Posted`.
2. **Budget Reconciliation**: Every certificate must have a corresponding amount allocated to a `Fund` and `Funds Center`.
3. **Daily Rates**: Cost calculations are derived from the `CostRate` entity based on staff `Grade`.

## Domain Intersections
- **Financials (FI)**: Certificates require a valid `CompanyCode` from SAP Table `T001`.
- **Funds Management (FM)**: Integration via `CrpBudgetLine` (Fund, Commitment Item).
- **Personnel (HR)**: Staff IDs are validated against master data.
