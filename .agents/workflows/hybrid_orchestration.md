---
description: Workflow for orchestrating hybrid SAP automation (Web GUI via Playwright vs Backend via BAPI/RFC)
---

# SAP Automation Orchestration Workflow

> ⛔ **CRITICAL CONSTRAINT — APPLIES TO ALL ROUTES:**
> **NEVER use `browser_subagent` for any SAP interaction.**
> `browser_subagent` opens a new unauthenticated browser at `localhost` and cannot reach the SAP server.
> **ALL Web SAP GUI automation MUST** run as Node.js scripts via `run_command`:
> ```
> node <script>.js
> ```
> Scripts connect to the existing Chrome test browser (launched with `--remote-debugging-port=9222`) via:
> ```javascript
> const browser = await chromium.connectOverCDP('http://localhost:9222');
> ```
> SAP URL: `https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350`

When attempting to automate a process in the SAP environment, the AI assistant must evaluate the task to determine the optimal execution path. This ensures maximum control, speed, and reliability.

## 1. Task Evaluation Phase
Analyze the user's request against the following criteria:

### Route A: Web SAP GUI (Playwright-SAP)
Use this route for **Builder/Visual Configuration Tasks**:
- Creating SEGW Services (Data Data Model Builder)
- Generating ABAP Classes or Function Modules in the editor
- Configuring Workflow Steps (SWDD)
- Screen interactions where SAP heavily relies on complex dynamic UI rules that are hard to replicate via API.
- Tasks that require manual visual validation of a screen state.

### Route B: Backend BAPI/RFC (Node-RFC / APIs)
Use this route for **Mass Data/Standardized Action Tasks**:
- Mass User Role Modifications (SU01)
- Mass Data Creation (e.g., creating 100 sales orders or materials)
- Executing standard background jobs
- Reading large tables of data.

### Route C: Hybrid Orchestration
Many complex processes require both. Example: Creating a new service.
1. **Frontend**: Use Web SAP GUI (Route A) to visually design the SEGW service and generate the ABAP artifacts.
2. **Backend**: Once the service is generated, use a BAPI script (Route B) to assign the newly generated authorization roles to a massive list of users.

## 2. Orchestration Steps
When the Assistant receives a complex objective:
1. **Decompose**: Break the objective down into individual steps.
2. **Classify**: Assign each step to Route A or Route B.
3. **Execute Route B First (If possible)**: If preliminary data needs to exist (e.g., creating test users via BAPI), run the Node.js API scripts first as they are faster and less prone to failure.
4. **Execute Route A**: Run the Playwright scripts to navigate the Web GUI for the builder tasks. Pass necessary data (like the generated BAPI return IDs) into the Playwright script as parameters.
5. **Verify**: Use Playwright to visually capture the final success screen (e.g., transaction `/IWFND/MAINT_SERVICE` showing the service is active) and present the screenshot to the user.

## 3. Tooling Requirements
- **Route A**: Requires the Node.js project to have `@playwright/test` and `playwright-sap` installed.
- **Route B**: Requires the Node.js project to have `node-rfc` installed and access to the SAP Router string/credentials.
