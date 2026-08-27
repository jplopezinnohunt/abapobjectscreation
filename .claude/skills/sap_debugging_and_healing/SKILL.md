---
name: SAP Debugging and Autonomous Self-Healing
description: Protocols for the AI to autonomously analyze SAP system dumps, authorization failures, and UI crashes to self-correct execution scripts.
domains:
  functional: [Support]
  module: [BASIS, CUSTOM]
  process: []
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

---

## 4. Real-Session Patterns (from 103 Experiments + Sessions #001-#022)

### RFC/pyrfc Failures (Data Extraction)
| Error | Cause | Fix |
|-------|-------|-----|
| `RFC_ERROR_DATA_LOSS` | Pagination bug in RFC_READ_TABLE for large tables | Extract day-by-day (not month). See `feedback_rfc_data_loss_workaround.md` |
| `DATA_BUFFER_EXCEEDED` | Row too wide for RFC buffer (>512 bytes) | Use adaptive field splitting — remove large text fields, re-add in separate pass |
| `KEY_NOT_FOUND` / `NOT_FOUND` | Cluster table (e.g., BSEG before declustering) | BSEG is declustered in P01 — use RFC_READ_TABLE directly. No MANDT in WHERE. |
| `INVALID_TABLE_NAME` | Table not accessible via RFC_READ_TABLE | Try SE16N equivalent or use BAPI approach |
| SNC auth failure on P01 | SNC partner name wrong | Check SM59 for exact partner name. Format: `p:CN=P01,O=...` |

### Playwright/WebGUI Failures (UI Automation)
| Symptom | Cause | Fix |
|---------|-------|-----|
| Element not found | SAP dynamically changed element ID | Switch from ID locator to text locator: `filter({ hasText: /text/ })` |
| Right-click menu never appears | Timing issue with SAP context menus | Use Select-Then-Toolbar pattern instead. Never right-click. |
| Tree node not expanding | Focus lost after click | Click node → then `page.keyboard.press('ArrowRight')` |
| Transport popup missed | Appears after async SAP round-trip | Always `await session.handleTransportRequest()` after save |
| Status bar empty / wrong | SAP not finished processing | `await page.waitForSelector('#stbar-msg-txt:not(:empty)')` |

### SAP Authorization Failures (SU53)
- Run `/nSU53` IMMEDIATELY after the auth error (SU53 shows last failure only)
- Common missing auth objects at UNESCO:
  - `S_TABU_DIS` — table display (SE16/SE16N)
  - `S_RFC` — RFC function group access
  - `S_ADMI_FCD` — system administration (SM21, ST22)
  - `F_STAT_MON` / `F_STAT_USR` — BCM payment monitoring/approval

### ADT REST API Failures
| HTTP Code | Meaning | Fix |
|-----------|---------|-----|
| 403 | Missing CSRF token | Call `GET /sap/bc/adt/` with `X-CSRF-Token: Fetch` first, then POST with token |
| 404 | Object doesn't exist in D01 | Check if only in P01 — may not have been transported down |
| 400 | Activation error | Read ST22 dump for ABAP compile error detail |
| 503 | ADT not enabled | Check SICf for `/sap/bc/adt` — activate via SM59/SICf |

## 4. Validation Status (Session #017)

> [!WARNING]
> **This skill is a FRAMEWORK DEFINITION — it has NOT been fully tested in production.**
> The self-healing loop has been designed but never executed end-to-end against a real SAP failure.
> The Triple Threat protocol (ST22 + SU53 + SM21) is proven individually via `sap_system_monitor.py`,
> but the autonomous loop (detect → diagnose → fix → retry) has not been validated.
>
> **Before trusting this skill for autonomous operation:**
> 1. Test ST22 dump detection → ADT extraction → code fix cycle manually
> 2. Test SU53 auth failure → role identification → user notification
> 3. Test Playwright DOM self-healing → screenshot → locator correction cycle
> 4. Validate 3-attempt limit actually stops (no infinite loops)

## Known Failures

| Error | Cause | Fix |
|-------|-------|-----|
| ST22 query returns empty | No dumps in timeframe | Normal — system healthy |
| SU53 returns previous auth check | SU53 shows LAST failure, not current | Run `/nSU53` immediately after error |
| SM21 access denied | Missing S_ADMI_FCD auth | Fall back to SNAP table via RFC |
| Screenshot fails in headless | Playwright window not visible | Use `page.screenshot()` not `page.pdf()` |
