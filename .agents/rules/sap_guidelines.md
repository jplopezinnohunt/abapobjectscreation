---
description: General guidelines for working with SAP Web GUI and ABAP development
---

# SAP Development Guidelines

## 1. Safety and Error Handling
- **Always verify the SAP system environment** before making modifications (Development vs. Quality vs. Production).
- **Check for SAP locks (SM12)** if you cannot edit an object.
- **Handling pop-ups:** SAP Web GUI often uses modal dialogs for confirmations or errors. Always check for active iframes or overlapping div elements that signify a modal before assuming a process is complete or hung.

## 2. Navigation
- Avoid relying solely on visual coordinates. Use stable DOM element attributes such as `title`, `aria-label`, or custom SAP data attributes (`data-sap-ls-id`).
- When executing a transaction, verify the screen title has changed appropriately before proceeding with data entry.

## 3. SEGW Specific Rules
- Ensure all OData property names adhere to the project's naming conventions (typically CamelCase for the external model, mapping to upper case ABAP fields).
- Always generate runtime objects after modifying the data model and ensure the generation log contains no errors before attempting to test the service.

## 4. Execution Paradigm & Authorizations
- **Local Execution:** All SAP automation (UI or API) is executed by generating and running Node.js scripts locally on the user's PC.
- **Authorizations:** Automation scripts authenticate using the user's SSO certificate or provided credentials. Therefore, the agent can only perform actions that the user's SAP profile is authorized to execute.
- **Tooling Duality:** 
  - For **Frontend Visual tasks** (e.g., SEGW Builder, ABAP generation), use Native Node.js `playwright` + `playwright-sap` to control the Web GUI.
  - For **Backend Mass Data tasks** (e.g., Role assignment, material creation), bypass the UI entirely and utilize `node-rfc` to call SAP BAPIs directly.
- **Code Archiving:** ALL generated execution scripts (like a one-off Playwright test) must be saved into a dedicated folder inside `/Zagentexecution/tasks/`. NEVER write temporary execution code directly to the project root or the `.agents/` folder. Read `.agents/rules/archiving_guidelines.md` for strict details.
