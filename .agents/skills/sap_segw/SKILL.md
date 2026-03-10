---
name: ABAP SEGW Services Construction
description: Guidelines for creating OData services via SAP Gateway Service Builder (SEGW) in Web SAP GUI.
---

# ABAP SEGW Services Construction

## Overview
Creating SEGW services in SAP involves defining data models, generating runtime artifacts, and registering the service. Automating this through Web SAP GUI requires navigating specific transaction codes and UI patterns.

## Core Process Rules
### 1. Pre-Development Interview
Before starting any SEGW creation task, you MUST execute the interview checklist defined in `.agents/workflows/segw_interview.md`. Do not proceed without gathering the SAP System URL, exact Authentication method, Project Name, Development Package, and relevant Transport Requests.

### 2. Hybrid Orchestration Evaluation
Evaluate if the task should be done via Web GUI (Playwright) or Backend API (BAPI) by consulting `.agents/workflows/hybrid_orchestration.md`. SEGW creation is almost always a "Route A" Web GUI task.

## Core Steps
1. **Transaction SEGW**: Launch the SAP Gateway Service Builder.
2. **Project Creation**: Create a new project and assign it a package (e.g., `$TMP` for local objects or a custom package).
3. **Data Model Definition**: Import DDIC structures or define entities and properties manually.
4. **Service Generation**: Click the "Generate Runtime Objects" button to create DPC and MPC classes.
5. **Service Registration**: Use transaction `/IWFND/MAINT_SERVICE` to register the newly generated service so it can be consumed externally.

## Automation via Generic Framework

Automating SEGW must follow the **Generic Primitives First** philosophy. Do NOT use `browser_subagent` for direct interaction; instead, use the `lib/sap-webgui-core/` framework via `SegwAutomation.js`.

### Key Primitives for SEGW
- **Tree Navigation**: Use `tree.selectNode(['Project Name', 'Data Model', 'Entity Types'])`.
- **Toolbar Actions**: Use `toolbar.clickCreate()` or `toolbar.clickButton('Generate')`.
- **Keyboard Over Mouse**: Use `page.keyboard.press('ArrowRight')` to expand tree nodes.
- **Select-Then-Toolbar**: Always select the parent node in the tree before clicking a toolbar action.

### Critical Rules
1. **No Context Menus**: Avoid right-clicks. Use the toolbar buttons that become active after selecting a node.
2. **Handle Transports**: Always call `session.handleTransportRequest()` after creating or saving objects.
3. **Verify State**: Use `session.getStatusBarMessage()` to verify success or capture errors.

Refer to `CLAUDE.md` and `lib/README.md` for full implementation patterns.
