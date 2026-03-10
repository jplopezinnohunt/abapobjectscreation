---
description: Interview checklist and predefined questions to ask the user before starting any SEGW or Web SAP GUI development task.
---

# Pre-Development Interview Questionnaire

Before executing any SAP development or configuration task via Web SAP GUI, you MUST gather the following information from the user if it has not already been provided explicitly.

## Core Connection Details
1. **SAP System URL**: What is the direct URL to access the Web SAP GUI environment?
2. **Authentication**: Are you already logged in, or how should authentication be handled?

## Project Object Details
3. **Project Name**: What is the name of the SEGW project or configuration object being created?
4. **Development Package**: Which package should this object be saved to? (e.g., `$TMP` for local, or a specific `Z*` package).

## Transport Requests
5. If the package is NOT `$TMP`, you must ask for the appropriate transport request numbers:
   - **Workbench Request (W-*)**: For cross-client repository objects (like SEGW projects, ABAP classes, dictionary objects).
   - **Customizing Request (C-*)**: For client-specific configuration settings.
   Ask: "Please provide the target Workbench request (starting with 'W-') and/or Customizing request (starting with 'C-') for these objects."

## Technical Details
6. **Data Model**: What entities, properties, or DDIC structures need to be imported or modeled?

> **Rule:** Do not proceed with the `browser_subagent` or Playwright script execution until you have the URL, Package, and Transport Requests (if applicable).
