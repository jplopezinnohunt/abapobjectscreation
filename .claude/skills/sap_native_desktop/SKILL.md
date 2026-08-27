---
name: SAP Native Desktop Scripting (Thick Client Fallback)
description: Guidelines on using win32com to automate the native Windows SAP Logon Desktop Client when Web GUI fails.
domains:
  functional: [*]
  module: [*]
  process: []
---

# SAP Native Desktop Scripting

While the primary UI execution engine for this framework is Playwright against the Web SAP GUI, some legacy transactions in ECC 6.0 may crash, fail to render properly in a browser, or have severe HTML limitations. 

When absolute maximum UI control is required and the Web GUI fails, the agent must fallback to the Native SAP GUI Desktop Client using SAP's built-in VBScript API.

## 1. Tooling Requirements
To hook into the running SAP Logon process on Windows, the agent must use the `win32com` library via Python, or `winax` via Node.js.
Since the agent primarily writes Node.js scripts for Playwright, the fallback is **`winax`**.
- `npm install winax`

## 2. Pre-Requisites
Before attempting a native desktop automation, the agent MUST:
1. Ensure the SAP Logon (saplogon.exe) is currently running on the user's machine.
2. Ensure the user's SAP GUI has GUI Scripting enabled (both in the SAP system `RZ11` parameter `sapgui/user_scripting` = TRUE, and locally in the SAP Logon options).

## 3. Execution Paradigm
When generating a fallback native script in `Zagentexecution/tasks/`, use the following general connection boilerplate for `winax`:

```javascript
const winax = require('winax');

// Connect to the running SAP GUI
const SapGuiAuto = new winax.Object("SAPROTWr.SAPApplication");
const application = SapGuiAuto.GetScriptingEngine();
const connection = application.Children(0);
const session = connection.Children(0);

// Example: Go to transaction SE11
session.findById("wnd[0]/tbar[0]/okcd").text = "SE11";
session.findById("wnd[0]").sendVKey(0); // Press Enter
```

## 4. Orchestration Rule Update
The `hybrid_orchestration` workflow dictates:
1. **Try BAPI/RFC first** (for data).
2. **Try Playwright Web GUI next** (for Builders/Config).
3. **If Web GUI cannot render the transaction correctly**, instantly pivot to writing a `winax` script for the **Native Desktop Client**.
