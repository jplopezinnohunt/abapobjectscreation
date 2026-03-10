# Evaluation: Web SAP GUI vs. Native Performance

## 1. Why the Playwright Script is Slow
The slowness and the resulting timeout errors are due to the architecture of **Web SAP GUI (SAP GUI for HTML)**. 
- **Translation Overhead:** The SAP backend must translate complex ABAP Dynpro screens into large HTML/JS payloads (using the legacy ITS / Lightspeed framework) on the fly.
- **Heavy Polling:** The web client constantly polls the server for state changes.
- **Playwright Wait States:** Playwright attempts to wait for `networkidle` or `domcontentloaded`. However, because Web SAP GUI is extremely heavy and constantly firing background XHR requests, these wait states often hit the 60-second limit and fail, causing the script to crash or behave unreliably.

## 2. The Current Error
The scripts are failing with:
`page.goto: Timeout 60000ms exceeded.`
Even when we wrap this in a `try/catch`, the subsequent interactions fail because the DOM elements (particularly inside the multiple nested `iframes`) haven't finished rendering. The high latency makes traditional Web UI scraping highly unstable.

## 3. How It Can Be Faster: The Alternative Tool
Yes, the tool is a major bottleneck here. To achieve significantly faster and more stable UI automation, we should pivot away from Playwright/Web GUI entirely and use **Native SAP GUI Desktop Scripting (Thick Client Fallback)**.

### Native Desktop Automation (`win32com` / VBScript)
- **Direct Interaction:** Instead of waiting for HTML rendering, this approach interacts directly with the SAP Logon Windows desktop application via its native OLE/COM interface.
- **Speed:** It does not suffer from network translation latency. Commands like pressing `F8` or retrieving text from a grid execute almost instantaneously.
- **Stability:** There are no iframe or DOM element locator issues. We interact with absolute SAP ID paths (e.g., `wnd[0]/tbar[1]/btn[8]`).

## Conclusion & Next Step
We will abandon the Web Playwright approach for this task. Instead, we will construct a Python script utilizing `win32com.client` to connect to the active SAP Logon session and extract the ST22 dumps directly from the thick client.
