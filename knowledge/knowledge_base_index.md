# Domain Knowledge Base: SAP Configuration & Objects

This knowledge base organizes SAP objects, OData services, and ABAP logic by their business business domains.

## 🧠 Entity Brain Map
A living visual map connecting all analyzed SAP objects (programs, tables, filters, services) into a unified knowledge graph.
- **Reference**: [Entity Brain Map](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/entity_brain_map.md)

## 🔍 Filter Logic Registry (Skill)
Reusable database of all filter/grouping logic discovered inside UNESCO SAP programs.
- **Reference**: [UNESCO Filter Registry](file:///c:/Users/jp_lopez/projects/abapobjectscreation/.agents/skills/unesco_filter_registry/SKILL.md)

---

## Business Domains

### [HR] HCM & Personal Data
Management of employee profiles, organizational structure, and HR workflows (ASR).
- **Reference**: [HCM Fiori Architecture](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/hcm_personal_data_analysis.md)
- **Manage Address**: [Manage Address Data Analysis](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/HCM/Fiori%20Apps/hcm_address_management_analysis.md)
- **NGO Specifics**: [UNESCO NGO Infotypes & Extraction](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/hcm_ngo_specifics.md)
- **Primary Services**: `Z_HCMFAB_MYPERSONALDATA_SRV`, `ZHR_PROCESS_AND_FORMS_SRV`
- **Key Pattern**: ASR Scenario Routing for Action-based Workflows.

---

### [[PSM] Public Sector Management](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/)
Fund management, budget control, and organizational certifications.

#### Fiori Applications
- [CRP Certificate Management](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/FIORI APPS/crp_management.md)

#### Reports
- [YFM1 Technical Analysis (Regular Budget)](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/REPORTS/yfm1_technical_analysis.md)
- [YPS8 Technical Analysis (Integrated PS/FM)](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/PSM/REPORTS/yps8_technical_analysis.md)

---

### [[FI] Financials](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/financials.md)
Core financial configuration (Company Codes, COA).

---

### [[BC] Basis & Connectivity](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/domains/connectivity.md)
RFC configuration and technical system parameters.

---
> [!TIP]
> Use these documents to understand the "Why" behind the "What" in the codebase.
