---
description: Guidelines on how the agent should manage generated files, test scripts, and scratchpads to keep the main project directory clean.
---

# Code & Artifact Archiving Guidelines

To preserve the integrity of the agent's core skills (`.agents/skills`), rules (`.agents/rules`), and workflows (`.agents/workflows`), and to keep the root `c:\Users\jp_lopez\projects\abapobjectscreation` directory perfectly clean:

## 1. Output Isolation
- **Never** write task-specific generated code (e.g., a one-off Playwright script like `create_segw_ZTEST.js` or a BAPI test script) into the `.agents` folder or directly into the root directory permanently.
- All automation outputs, scripts, and logs related to a specific user request must be created inside a dedicated subfolder within a `Zagentexecution/tasks/` directory at the project root.

## 2. Directory Structure execution
When executing a new user request that requires generating code or scripts, structure the output into a task-based folder:
1. Create a master `Zagentexecution/tasks/` directory at the project root if it doesn't exist.
2. Inside `Zagentexecution/tasks/`, create a clearly named and timestamped subfolder representing the specific request.
   *Format:* `Zagentexecution/tasks/[YYYY-MM-DD]_[Short_Task_Description]/`
   *Example:* `Zagentexecution/tasks/2026-03-04_ZCRP_SEGW_Creation/`
3. Write ALL Playwright `.js` files, `node-rfc` scripts, test data JSON, and configuration files required for that task directly inside that specific folder.
4. Execute the script from within that context.
5. Save any screenshots, execution logs, or debug output inside that same folder.

## 3. Discarding Scratch Files
If the user asks a question that requires writing a temporary script just to test a theory (with no intent to save the automation for the future), use the temporary artifact storage or the system `/tmp/` directory, rather than writing to the project codebase.

*By adhering to this strict archiving rule, the agent ensures that the project framework remains an elegant, reusable engine, while the specific executions are neatly organized in the `Zagentexecution/` archive.*
