---
name: Multi-Agent Hub Architecture
description: Defines the roles and responsibilities of the various AI Agents operating within this SAP framework.
---

# Multi-Agent Hub Architecture

To ensure enterprise-grade reliability and scalability, this SAP Automation Framework relies on a **Multi-Agent Architecture**. Rather than a single monolithic AI attempting to do everything, tasks are divided among specialized agents operating in parallel or in sequence.

## 1. The Orchestrator Agent (The Brain)
**Role:** Master Planner & Delegator
- **Responsibilities:**
  - Interfaces directly with the human user and reads business requirements (e.g., pulling data via the Notion MCP Server).
  - Drafts the central `implementation_plan.md` and maintains the `task.md`.
  - Executes the `.agents/workflows/hybrid_orchestration.md` evaluation to decide *which* specific tools and execution agents are required for the job.
  - Provisions the appropriate `Zagentexecution/tasks/` folder and `config/` files.
  - Dispatches instructions to the specific Worker Agents and reviews their output before reporting back to the user.

## 2. Subject Matter Expert (SME) Agents (The Architects)
While the executing agents physically move the mouse or send the API calls, the SME Agents dictates *what* should be done based on deep SAP knowledge. The Orchestrator consults these SMEs during the planning phase.

### A. The ABAP Core Developer Agent
- **Domain:** OO-ABAP, Classes, Interfaces, Reports, Data Dictionary (SE11).
- **Responsibility:** Designs the optimal class architecture, ensures strict adherence to naming conventions (Z-namespaces), and writes the actual ABAP code that the Frontend Agent will paste into the SAP GUI.

### B. The Gateway & OData Services Expert Agent
- **Domain:** SEGW, RFC mapping, DPC_EXT/MPC_EXT redefinitions, REST constraints.
- **Responsibility:** Designs the Entity Data Model based on business needs, maps properties to standard RFCs/BAPIs, and handles the logic for handling GET_ENTITYSET or complex $filter operations.

### C. The Functional Configurator Agents
- **FI Expert:** Domain covers general ledger, accounts payable/receivable, and strict posting rules.
- **Banking Configuration Expert:** Domain covers house banks, bank chains, electronic bank statements (EBS), and payment media workbench (PMW).
- **Funds Management (PSM-FM) Expert:** Domain covers Public Sector Management, fund accounting, budget control systems (BCS), and commitment strings.
- **Responsibility:** Validates that any requested data models or workflows do not violate strict FI posting rules, banking standards, or Public Sector fund accounting constraints. Provides the exact SPRO paths for the executing agents.

### D. The Workflow Expert Architect Agent
- **Domain:** SWDD, Business Workflows, Tasks, Events.
- **Responsibility:** Designs approval matrixes, determines the necessary Boris events to trigger workflows, and defines custom agent determination rules.

## 3. Specialized Execution Workers (The Hands)

### A. The UI Automation Agent (Frontend)
- **Tooling:** Playwright, `playwright-sap`, Fiori/UI5 Inspector, Locators.
- **Responsibility:** Strictly handles Web SAP GUI interactions builder tasks like SEGW creation, ABAP class generation via Web, or Fiori application testing.
- **Rules:** Operates entirely within the browser context. Reports UI failures up to the Orchestrator.

### B. The Core System Agent (Backend)
- **Tooling:** `node-rfc`, BAPIs, standard REST OData.
- **Responsibility:** Handles high-volume data creation, user role modifications, table maintenance, and direct system configurations bypassing the UI.

### C. The Native Fallback Agent (Thick Client)
- **Tooling:** `winax`, `win32com`, SAP GUI Scripting Engine.
- **Responsibility:** Only activated by the Orchestrator when the Frontend Web GUI Agent fails. Hooks directly into the Windows native SAP Logon Pad for legacy ECC 6.0 transactions.

### E. The CI/CD Agent (Operations)
- **Tooling:** `abapGit` GUI, GitHub/GitLab integration.
- **Responsibility:** Triggered at the very end of a successful generation cycle to pull/push the newly generated ABAP objects to version control.

## 4. Deep-Dive Orchestration Workflow Example (SEGW Creation)
To understand how all these tools and agents work together, consider a user request to "Create a new OData Service for Material and Customer data based on my Notion spec":

1. **Requirements Ingestion (Orchestrator):** 
   - The Orchestrator receives the Notion URL from the user.
   - It boots the **Notion MCP Server** (`npx mcp-server-notion`) in the background, authenticates with the token in `Zagentexecution/config/notion_auth.json`, and extracts the structured tables/text containing the Project Name (ZTEST), W-Request, and Data Model.
2. **Business Validation (SME Architects):**
   - The Orchestrator passes the raw Notion data to the **Gateway & OData SME Agent**, which validates the entity relationships and maps them to standard SAP tables (MARA, KNA1).
   - The Orchestrator consults the **ABAP Developer SME Agent**, which drafts the exact OO-ABAP syntax needed for the `DPC_EXT` class redefine methods.
3. **Execution Routing (Orchestrator):**
   - The Orchestrator evaluates `.agents/workflows/hybrid_orchestration.md`. Since SEGW is a visual builder, it decides UI automation is needed.
   - It creates the isolated execution folder: `Zagentexecution/tasks/2026-03-04_ZTEST_SEGW/`.
4. **Primary Execution (Frontend Worker):**
   - The Orchestrator dispatches the **UI Automation Agent**, handing it the approved Data Model and ABAP code.
   - This worker writes a `create_segw.js` script using **Playwright** and `playwright-sap`, logs into the Web SAP GUI, navigates to SEGW, physically clicks through the builder to create the entities, and pastes the ABAP SME's code into the class editor.
5. **Fallback Execution (Native Worker - if needed):**
   - If Playwright crashes because the SAP Web GUI fails to render a specific popup in SEGW, the Frontend Worker reports the failure.
   - The Orchestrator instantly dispatches the **Native Fallback Agent**, which writes a `winax` script to hook into the running native Windows `saplogon.exe` and completes the step via VBScript.
6. **Backend Configuration (Core System Worker - Optional):**
   - If the task also required generating test data or assigning roles for the new service, the Orchestrator dispatches the **Core System Agent** to quietly execute high-speed BAPIs via `node-rfc` in the background, bypassing the UI entirely.
7. **Version Control (CI/CD Worker):**
   - Once the Web GUI or Native GUI finishes generating the ABAP objects and locks them in the W-Request, the Orchestrator calls the final agent.
   - The **CI/CD Agent** takes over, drives the Web GUI to transaction `ZABAPGIT`, selects the `ZTEST` package, and commits the newly generated code to the company's GitHub repository.
8. **Final Reporting:**
   - The Orchestrator collects the Playwright screenshots, standard outputs, and Git commit hashes from the `Zagentexecution` folder, and reports total success and proof-of-work back to the user.
