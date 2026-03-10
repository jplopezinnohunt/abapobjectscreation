---
name: SAP Debugging and Autonomous Self-Healing
description: Protocols for the AI to autonomously analyze SAP system dumps, authorization failures, and UI crashes to self-correct execution scripts.
---

# SAP Debugging and Autonomous Self-Healing

When an Execution Agent (Frontend, Backend, or Native) encounters a hard failure during a task, it is strictly forbidden from immediately aborting and reporting failure to the human user. 

Instead, the Orchestrator must trigger the **Autonomous Self-Healing Loop**. The AI must act as its own Basis and ABAP support team to root-cause the issue.

## 1. The Core 3 Diagnostic Transactions (The "Triple Threat" Check)
If a script fails (e.g., an OData service refuses to activate, or the Playwright browser receives a red SAP status-bar error), the UI or Native Agent must immediately pivot its execution to gather diagnostic data:

### A. ST22 (ABAP Runtime Errors / Short Dumps)
- **Trigger:** If the system throws an HTTP 500, a literal "Short Dump" screen in the UI, or a `node-rfc` exception indicating a backend crash.
- **Action:** The agent must navigate to `ST22`, filter by the current `sap_auth.json` user and today's date, and extract the exact "What happened?", "Error analysis", and "Source Code Extract" sections.
- **Resolution:** The Orchestrator passes the ST22 dump text to the **ABAP Core Developer SME Agent** to rewrite the generated class logic and retry.

### B. SU53 (Authorization Failures)
- **Trigger:** If the SAP status bar reads *"You are not authorized to use transaction X"*, *"No authorization for object Y"*, or an RFC call returns an auth error.
- **Action:** The agent must immediately execute `/nSU53` (or call `BAPI_USER_GET_DETAIL`). It must extract the exact missing Authorization Object, Field, and Value.
- **Resolution:** The AI logs the specific missing Auth Object to `Zagentexecution/tasks/` and halts, notifying the user exactly what Basis roles are missing to proceed.

### C. SM21 (System Log)
- **Trigger:** Undefined system lockups, database connection drops, or enqueue (SM12) lock issues.
- **Action:** Execute `SM21`, filter by the last 15 minutes, and extract the core system error (e.g., "Transaction Canceled", "Database deadlock").

## 2. Playwright/DOM Self-Healing (UI Failures)
If the failure is not an SAP backend issue, but rather a Playwright UI script failing to find a button:
1. **HTML/Visual Dump:** The script must be programmed to automatically execute `page.screenshot({ path: 'crash.png' })` and `fs.writeFileSync('crash.html', await page.content())` in the `Zagentexecution/tasks/` folder on an unhandled exception.
2. **Vision Analysis:** The Orchestrator agent will ingest `crash.png` and `crash.html`.
3. **Locator Correction:** The Orchestrator updates the specific CSS/XPath locator in the script (e.g., if SAP dynamically changed the `id` from `btn_save_1` to `btn_save_2`) and re-executes the script silently.

## 3. The Re-Execution Limit
To prevent infinite diagnostic loops, the **Self-Healing Loop** is limited to **three (3)** attempts. 
If the AI encounters an ST22 dump, rewrites the code, tries again, and dumps exactly three times, it must trigger the Master Abort protocol, format all three crash logs into a final `analysis_report.md`, and ping the user for manual intervention.
