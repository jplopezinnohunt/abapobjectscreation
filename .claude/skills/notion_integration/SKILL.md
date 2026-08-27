---
name: Notion Integration
description: Guidelines on how the agent should read and interact with Notion to gather project requirements and documentation.
domains:
  functional: [*]
  module: [*]
  process: []
---

# Notion Integration Guidelines

To extract project requirements (such as SEGW Data Models, Project Names, or Transport Requests) directly from the user's Notion workspace, the agent must follow these guidelines.

## 1. Tooling Requirements (MCP Server Priority)
The absolute preferred method for reading Notion is to utilize the Model Context Protocol (MCP) Server.
- **Package**: `npx -y notion-mcp-server`
- If the MCP server cannot be used for any reason, the fallback is writing a custom script using `npm install @notionhq/client`.

## 2. Authentication & Configuration
- **Notion Integration Token:** The agent requires a Notion Internal Integration Secret Token (usually starts with `secret_`).
- **Storage:** Secure the token in the `Zagentexecution/config/notion_auth.json` file.
- **Access:** The Notion Integration MUST be manually invited/connected to the specific Notion page by the user before the API/MCP can read it.

## 3. Reading Notion Data (Workflow)
When the user asks the agent to read project data from a Notion URL:
1. **Retrieve Token**: Read the Notion token from `Zagentexecution/config/notion_auth.json`.
2. **Execute MCP Server**:
   Instead of writing a custom Node.js crawler, the agent should dynamically boot the Notion MCP server in the background:
   ```bash
   NOTION_API_KEY="your_secret_here" NOTION_PAGE_ID="your_page_id" npx -y notion-mcp-server
   ```
   *(Note: The agent will use its internal tools to interface with this MCP process to query the specific Page).*
3. **Parsing**: Map the extracted Notion content (text/tables) directly to the `segw_interview.md` requirements (Project Name, Data Model, W-*).

*By utilizing the Notion MCP Server, the agent seamlessly bridges external Notion business requirements into actionable SAP ABAP development tasks.*
