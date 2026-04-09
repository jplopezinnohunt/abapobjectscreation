---
name: Discovery Patterns as Reusable Knowledge
description: Each E2E flow successfully mapped (Payment, P2P, Bank Statement, Integrations) is a discovery pattern replicable to new domains. The methodology of HOW we analyzed is as valuable as WHAT we found.
type: project
---

Each flow we mapped successfully created a **pattern of discovery** — a methodology for analyzing the next domain. These are SAP-specific expert knowledge earned through 39 sessions.

**Why:** The brain has data and edges. But the PROCESS of discovering those edges — reading config chains, tracing BAdIs, cross-referencing CTS with code — is expert methodology. When we need to analyze a new SAP domain (e.g., Real Estate, Asset Management), we follow the same discovery patterns.

**How to apply:** Before analyzing a new domain, review which existing discovery pattern applies. Don't start from scratch.

## Proven Discovery Patterns

### 1. Payment E2E (Sessions #019-#039)
Pattern: T042Z (payment methods) -> T042I (bank routing) -> DMEE_TREE_NODE (format tree) -> BAdI exit class -> FPAYP fields -> BCM validation -> Bank file
Result: 13 trees analyzed, 6 active identified, PurposeCode chain traced, 3 banking channels documented

### 2. P2P Process Mining (Sessions #009-#011)
Pattern: EBAN (PR) -> EKKO/EKPO (PO) -> EKBE (GR) -> ESSR/ESLL (SES) -> RBKP/RSEG (Invoice) -> F110 (Payment)
Result: 848K events, DFG visualization, bottleneck identification

### 3. Integration Discovery (Sessions #032-#035)
Pattern: RFCDES (RFC destinations) -> TFDIR_CUSTOM (RFC-enabled FMs) -> TBTCO/TBTCP (jobs) -> EDIDC (IDocs) -> file-based jobs (COUPA, SWIFT)
Result: 38 systems, 334 RFC FMs, 7 .NET apps, file-based integration layer discovered

### 4. Bank Statement Reconciliation (Sessions #028-#030)
Pattern: FEBKO (statement headers) -> FEBEP (posted items) -> FEBRE (search strings) -> T028A/T028E (account symbols) -> BKPF/BSIS (FI clearing)
Result: 223K events, 3 config tiers, 10xxxxx vs 11xxxxx architecture understood

### 5. Code Extraction + BAdI Tracing (Sessions #038-#039)
Pattern: TADIR (package objects) -> READ REPORT via RFC -> regex parse for SELECT/CALL FUNCTION -> DMEE_TREE_NODE for BAdI mapping
Result: 1,147 files extracted, H18 PurposeCode resolved via BAdI chain

### 6. Transport Impact (Sessions #004-#005)
Pattern: E070 (transports) -> E071 (objects) -> TADIR (object type) -> co-change coupling analysis
Result: 7,745 transports, 108K objects, co-change coupling graph

## Next Domains to Apply Patterns To
- **HCM/Payroll:** Follow Pattern #1 (config chain) for PA/OM infotypes -> Allos -> BDC sessions
- **CO/Controlling:** Follow Pattern #2 (process mining) for COEP/COOI event sequences
- **Real Estate:** Follow Pattern #3 (integration) for RE-FX interfaces
- **Workflow 90000003:** Follow Pattern #5 (BAdI tracing) for certifying officer logic in YWFI

## Track for #040+
Document each discovery pattern as a reusable skill. The pattern IS the expertise — not the data.
