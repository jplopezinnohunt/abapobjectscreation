# Domain Knowledge: Financials (FI)

## Overview
General Financial configuration providing master data for other domains (like CRP).

## Core Technical Objects

### Table: `T001` (Company Codes)
- **Purpose**: Defines the smallest organizational unit for which a complete self-contained set of accounts can be drawn up.
- **Key Fields**: `BUKRS` (Code), `BUTXT` (Name), `ORT01` (City), `WAERS` (Currency).
- **Usage**: Referenced by almost all business documents to identify the legal entity.

## Technical Integration
- **RFC Access**: Data is typically read using `RFC_READ_TABLE` or specialized BAPIs.
- **Python Utility**: Access is channeled through [sap_utils.py](file:///c:/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/mcp-backend-server-python/sap_utils.py).

## Relationships
- **CRP Integration**: `CrpCertificate` uses `CompanyCode` as a mandatory header field.
