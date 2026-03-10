---
name: Web SAP GUI Automation
description: Best practices and guidelines for automating SAP GUI for HTML
---

# Web SAP GUI Automation

## Overview
SAP GUI for HTML (Web SAP GUI) maps SAP screen elements to HTML dynamically. This means standard web automation techniques might be fragile and require special care.

## ⛔ CRITICAL: NEVER USE `browser_subagent` FOR SAP TASKS ⛔
**This is a hard, non-negotiable rule. Violating it is the #1 failure mode.**

- **NEVER** call the `browser_subagent` tool for any SAP interaction.
- `browser_subagent` opens a **fresh, unauthenticated browser** at `localhost` — it has **no SAP session**, **no client certificate**, and cannot reach `hq-sap-d01.hq.int.unesco.org`.
- **ALWAYS** interact with SAP by writing a Node.js script and running it via `run_command`:
  ```
  node <script>.js
  ```
- **ALL** Playwright scripts MUST connect to the existing, pre-authenticated Chrome test browser via CDP:
  ```javascript
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  ```
- The correct SAP URL is: `https://hq-sap-d01.hq.int.unesco.org/sap/bc/gui/sap/its/webgui?sap-client=350`
- **NEVER** navigate to `localhost` or open any URL other than the correct SAP server above.
- The Chrome test browser is launched separately via `00_launch_browser.js` with `--remote-debugging-port=9222` and a persistent profile in `playwright_data/`. This is the ONLY browser that should be used.

## Core Process Rules
### 1. Pre-Development Interview
Before starting any significant Web SAP GUI task, you MUST execute the interview checklist defined in `.agents/workflows/segw_interview.md`.

### 2. Hybrid Orchestration Evaluation
Evaluate the task using `.agents/workflows/hybrid_orchestration.md`. If the task involves massive pure data manipulation, consider if a BAPI approach is better than Web GUI automation.

## Best Practices
1. **Playwright-SAP Locators**: Standard Playwright selectors fail easily in SAP. ALWAYS use the `playwright-sap` module and its native locators (like `getByRoleUI5`, `locateSID`) whenever possible.
2. **Iframes**: Web SAP GUI relies heavily on iframes. Always ensure your Playwright script has switched contexts to the correct iframe before interacting.
3. **Execution Wait States**: Leverage `playwright-sap`'s built-in wait logic to handle SAP's complex UI rendering cycles rather than hardcoded sleeps.
4. **Tool-Assisted Debugging**: When writing scripts, use these browser extensions:
   *   **SAP UI5 Inspector**: To inspect the true UI5 control hierarchy and data bindings.
   *   **SelectorsHub**: For older, non-UI5 classic web GUI screens to generate precise XPath/CSS.

## Playwright Script Generation & Execution
Do not guess complex DOM paths. Use specialized tools to generate the UI code:
1. **Playwright-SAP Smarter Codegen**: ALWAYS use the augmented `playwright-sap` recorder instead of writing raw clicks by hand when capturing long workflows. It will generate stable `getByRoleUI5` calls.
2. **Context Selection**: Start scripts by identifying and focusing on the main content iframe.
3. **Locator Hierarchy**: 
   *   Primary: `playwright-sap` extensions (`locateSID`, `getByRoleUI5`).
   *   Secondary: Stable Text definitions.
   *   Last Resort: CSS/XPath (verified via SelectorsHub).
