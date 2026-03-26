# SAP Intelligence Documents
> Living documentation for the UNESCO SAP development and monitoring toolkit.
> **Read `PROJECT_MEMORY.md` first at every session start.**

---

## Core Memory

| File | Purpose | Read When |
|------|---------|-----------|
| **[PROJECT_MEMORY.md](./PROJECT_MEMORY.md)** | Session memory — architecture rules, extractions, BDC findings | **FIRST — every session** |
| [sap_companion_intelligence.md](./sap_companion_intelligence.md) | Full reference — ADT map, monitor commands, auth, Allos strategy | Deep technical work |
| [vscode_sap_plugin_intelligence.md](./vscode_sap_plugin_intelligence.md) | VS Code plugin analysis, ADT endpoint discovery | Plugin/extension work |

## Knowledge Graph

| File | Purpose |
|------|---------|
| [sap_brain.json](./sap_brain.json) | Machine-readable graph (55 nodes, 66 edges) |
| [sap_knowledge_graph.html](./sap_knowledge_graph.html) | Interactive visual graph (open in browser) |

Rebuild after new extractions:
```bash
python sap_brain.py --build --html
```

## Related Skills (`../skills/`)

| Skill | Use For |
|-------|---------|
| `sap_adt_api` | ABAP read/write via ADT REST |
| `sap_fiori_tools` | Fiori app scaffold/modify |
| `sap_segw` | OData service builder |
| `sap_webgui` | Browser SAP automation |
| `sap_debugging_and_healing` | Self-repair after errors |
| `sap_reverse_engineering` | Extract code from SAP |
| **`skill_creator`** | **Create/improve new skills (Anthropic framework)** |

## Key Scripts (`../../Zagentexecution/mcp-backend-server-python/`)

| Script | System | Purpose |
|--------|--------|---------|
| `sap_adt_client.py` | D01 | Full ADT client |
| `extract_bsp_via_adt.py` | D01 | BSP/UI5 downloader |
| `sap_system_monitor.py` | **P01** | Runtime dashboard |
| `sap_brain.py` | both | Knowledge graph builder |

---
*Update PROJECT_MEMORY.md at end of every session.*
