# H18 DMEE Tree Findings — Session #039

**Date:** 2026-04-06
**Source:** P01 (production, SNC/SSO)
**Status:** CONFIRMED — H18 can be struck

---

## Question (H18, raised #026)

Where does the SEPA `<Purp><Cd>` PurposeCode value come from in UNESCO's payment XML?

## Answer

**`FPAYP-XREF3`** — the reference field 3 on the payment detail line (table FPAYP), read by the DMEE format tree and post-processed by BAdI `FI_CGI_DMEE_EXIT_W_BADI`.

## Evidence (from P01 DMEE_TREE_NODE)

### Tree: `/CGI_XML_CT_UNESCO` (631 nodes in P01)

Node `N_5443906990` (`Purp`, type=ELEM) has 4 children:

| Node ID | TECH_NAME | Source Table | Source Field | Exit Function | Role |
|---|---|---|---|---|---|
| N_9662041050 | `Cd` | FPAYP | XREF3 | FI_CGI_DMEE_EXIT_W_BADI | **ISO 20022 PurposeCode** (e.g., SUPP, SALA) |
| N_2524282270 | `Prtry` | FPAYP | STRFR | FI_CGI_DMEE_EXIT_W_BADI | Proprietary code fallback |
| N_0383793140 | `-Cd` | — | — | FI_CGI_DMEE_EXIT_W_BADI | Condition: suppress Cd node |
| N_5023885600 | `-Prtry` | — | — | FI_CGI_DMEE_EXIT_W_BADI | Condition: suppress Prtry node |

Same structure confirmed in `/CGI_XML_CT_UNESCO_1` (639 nodes, identical Purp hierarchy).

### How the value flows

```
F110 payment run
  → FPAYP line created (XREF3 populated from vendor master / payment config)
  → DMEE tree `/CGI_XML_CT_UNESCO` renders XML
    → Node `Purp > Cd`: reads FPAYP.XREF3
    → BAdI `FI_CGI_DMEE_EXIT_W_BADI` post-processes (can override/suppress)
    → If XREF3 empty → `-Cd` condition fires → Purp node suppressed entirely
  → Output: `<Purp><Cd>SUPP</Cd></Purp>` (or omitted if no PurposeCode)
```

### Why prior investigations failed

1. **Session #038 (ABAP classes):** `YCL_IDFI_CGI_DMEE_FR`, `_FALLBACK`, `_UTIL` are BAdI implementations. They don't contain the literal because they RECEIVE the node value from the tree at runtime. The tree says "read FPAYP.XREF3" — the BAdI only processes it.
2. **PMO named wrong classes:** `_AE` and `_BH` don't exist. The real classes are `_FR` (France/SEPA format), `_FALLBACK` (fallback logic), `_UTIL` (utilities).
3. **Initial probe filtered for literal values in `MP_CONST`:** The Cd node has `MP_CONST=empty` because the source is a table field, not a constant. The original filter for SEPA code literals correctly returned 0 — but the answer was in `MP_SC_TAB`/`MP_SC_FLD`, not `MP_CONST`.

### Additional finding: D01 ≠ P01

| Tree | D01 nodes | P01 nodes | Delta |
|---|---|---|---|
| /CGI_XML_CT_UNESCO | 1,262 | 631 | **D01 has 2× (untransported versions)** |
| /CGI_XML_CT_UNESCO_1 | 1,264 | 639 | Same |
| /SEPA_CT_UNES | 190 | 95 | Same |
| CGI_FICA_XML_CT | 1,210 | 1,210 | Equal |
| CGI_XML_CT | 1,274 | 1,274 | Equal |

Custom UNESCO trees (`/` prefix) have diverged — D01 has draft versions not transported to P01. Standard CGI trees match. **This validates the user's rule: only P01 data is trustworthy for config analysis.**

## Artifacts

- `h18_dmee_trees.csv` — 13 UNESCO DMEE tree headers (P01)
- `h18_dmee_tree_nodes.csv` — 8,308 nodes across 13 trees (P01)
- `h18_dmee_tree_probe.py` — reusable probe script

## Next steps (if needed, not H18 scope)

- Read `FPAYP` for a sample payment to confirm XREF3 population
- Extract BAdI implementation `FI_CGI_DMEE_EXIT_W_BADI` to understand what transformations it applies
- Check if XREF3 is populated from vendor master (LFB1/LFA1) or payment config (T042*)
