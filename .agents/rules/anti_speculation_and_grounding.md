# Grounding & Anti-Speculation Rules (WoW)

This document establishes the strict behavioral guidelines for the AI assistant operating on the UNESCO SAP Intelligence Platform. These rules are derived from historical session forensics and are non-negotiable.

---

## 1. The "No Inventes" Principle (Anti-Speculation)

Never hallucinate or write SAP configuration or ABAP code from scratch ("De 0"). If an implementation is required, you must base your work on existing, verified SAP standard or custom objects.

*   **Extraction over Assumption:** You must read the source code of related programs (e.g., standard program `SAPFPAYM` or custom equivalents) and adapt it, rather than writing a speculative wrapper.
*   **Remove Unverified Checks:** Do not add speculative conditional checks or assertions unless they are directly visible in the source system code or specifically requested by the user.
*   **Consequence of halluncination:** Speculation puts the system and transports at risk (*"me pones en riesgo"*).

---

## 2. Bilingual Command Parsing (Spanish / English)

The interface language is hybrid. You must maintain complete context awareness of language switching:
*   **Technical Prose:** Always keep SAP technical objects, tables, DMEE elements, and BCM details in English.
*   **Direct Commands:** Interpret Spanish prompts as high-priority, context-dependent directives. For example:
    *   *"Nueva session. Protocolo de apertura"* $\rightarrow$ Execute the session start protocol.
    *   *"cerremos la session"* $\rightarrow$ Execute the session retro/close protocol.
    *   *"que falta"* or *"nada"* $\rightarrow$ Output the exact remaining backlog status or proceed with the current step.

---

## 3. Evidence Tier-1 Validation

Every claim made regarding SAP configuration, master data, or program logic must carry a validated citation from the system.
*   **Golden DB & D01 First:** Base conclusions on actual database states (e.g., tables `BKPF`, `T036FT`, `FMFINCODE`, `PROJ`, `PRPS`) queried from the active SQLite database or the live D01 system via ADT/RFC.
*   **User Spreadsheets are Interpretations:** Verbatim rule: *"Remember that the excel passed is just an user interpretation we must base our conclusion in data SAP system and SAP and bank informations"*. Do not treat user excel files as the absolute source of truth.

---

## 4. Visual Diagram Formatting Rules

When creating or modifying flowcharts or diagrams (HTML/CSS/SVG), follow these exact dimensional specifications to ensure readability and fit the screen canvas without horizontal scrolling:
*   **Layout:** Use a multi-row (zigzag/snake) flow layout rather than a single horizontal line.
*   **Node dimensions:** Every node must be exactly `width: 180` and `height: 80`.
*   **Font inside nodes:** `15px`, white, bold, centered, with text wrapping enabled.
*   **Theme:** Modern dark mode with neon accents.

---

## 5. Post-Session Verification Pass (The 7-Check Drill)

Before declaring any session closed or writing persistent memories:
1.  **Check 1 (Agent Spot Checks):** Verify 2 claims from any parallel agent against the source.
2.  **Check 2 (Source Authority Sanity):** Verify source age and ranking; demote Tier 4+ sources.
3.  **Check 3 (Contradiction Scan):** Search for contradictions; if zero are found, broaden keywords (zero contradictions indicates insufficient effort).
4.  **Check 4 (Single-Source Audit):** Demote single-source claims to TIER_3.
5.  **Check 5 (Prediction Closure):** Update and mark outcomes in `falsification_log.md`.
6.  **Check 6 (Parent-Tree Walk):** Ensure scope claims ("all", "every") are backed by reading $\ge 50\%$ of target children.
7.  **Check 7 (Forbidden Pattern Audit):** Remove self-congratulatory words (*"best session"*, *"highest yield"*).
