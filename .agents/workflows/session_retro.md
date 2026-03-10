---
description: Post-session retrospective to improve MCP tools and agent skills
---

To ensure continuous improvement, run this workflow at the end of every significant SAP task or conversation.

1. **Discovery Analysis**: 
   - Identify any new SAP tables, BAPIs, or RFC behaviors discovered during the session.
   - Document any performance bottlenecks (latency, memory, timeouts).

2. **MCP Evolution**:
   - Evaluate if any manual script success should be integrated into `sap_mcp_server.py`.
   - Update `read_table_generic.py` if new extraction patterns were required.

3. **Skill & Protocol Update**:
   - Review the `.agents/skills` folder. 
   - Update `SKILL.md` files with new interaction patterns or discovered element IDs (for UI automation).

4. **Knowledge Persistence**:
   - Create or update a Knowledge Item (KI) in the `knowledge/` directory with the "Analysis-First" results.

5. **User Confirmation**:
   - Present the "Learning Summary" to the user for feedback.
