# Code Brain Strategy — From Code Analysis to Reusable Knowledge

**Created:** Session #048 (2026-04-08/09)
**Priority:** H34 (HIGH — next session)
**Problem:** Every incident re-discovers relationships from scratch. Code and tables are analyzed but the learnings are not tagged back to the objects.

---

## 1. The Problem

Session #048 analyzed ~100 programs and tables for INC-000006073. We learned:

- LHRTSF01.abap line 852: `IF bukst = bukrs` — only fills GSBER for same-company
- LHRTSF01.abap line 1693: CLEARs GSBER on vendor lines (koart='K', ktosl='HRP')
- ZCL_IM_TRIP_POST_FI CM00A: reads PA0027 subtype 02, exits if no record
- ZXTRVU05: BusA derivation commented out for non-UNES by Konakov 2018
- LHRTSU05: RW609 is a wrapper, not a validation
- GB901: rule 3IIEP###002 only covers GL 2021042/2021061
- LFA1.KTOKK determines LFB1.AKONT determines GGB1 coverage

**None of these learnings are tagged back to the objects.** Next time someone asks about LHRTSF01 or PA0027 or GGB1, the Brain doesn't know what we discovered. We'd re-analyze from scratch.

## 2. What "Tagging" Means

Every code object and table we analyze should carry **annotations** — what we learned, when, and why it matters:

```json
{
  "node_id": "ABAP:LHRTSF01",
  "type": "SAP_STANDARD_INCLUDE",
  "annotations": [
    {
      "line": 852,
      "tag": "CRITICAL_LOGIC",
      "finding": "IF epk-bukst = epk-bukrs — only propagates GSBER for same-company postings. Intercompany counterpart lines get NO GSBER.",
      "impact": "Any intercompany posting where the partner company has no fallback BusA derivation will fail",
      "discovered": "INC-000006073, Session #048",
      "related_edges": ["DERIVES_FIELD:GSBER", "READS:PA0001.GSBER"]
    },
    {
      "line": 1693,
      "tag": "SIDE_EFFECT",
      "finding": "CLEAR epk-gsber on vendor lines with koart=K and ktosl=HRP/HRV",
      "impact": "Vendor clearing lines lose GSBER even if it was set upstream",
      "discovered": "INC-000006073, Session #048"
    }
  ]
}
```

This is NOT documentation — it's **machine-readable knowledge** that the Brain can use for impact analysis, similarity search, and gap detection.

## 3. Why Not the Entire SAP System

We don't need 452,000 tables or 826 programs in the graph. We need the objects that matter for **UNESCO's processes**:

| Process | Key Programs | Key Tables | Key Config |
|---|---|---|---|
| **Travel (T2R)** | RPRAPA00, LHRTSF01, LHRTSU01-08, ZCL_IM_TRIP_POST_FI, ZXTRVU05 | PA0001, PA0027, PTRV_SCOS, PTRV_SHDR, LFA1, LFB1 | GB901, GB922, YTFI_BA_SUBST, YBASUBST |
| **Payment (P2P)** | RFFOUS_T, F110, SAPF110V | REGUH, REGUP, PAYR, T042*, FPAYP | DMEE trees, T012/T012K, FBZP chain |
| **Bank Statement** | RFEBKA00, FEBAN | FEBEP, FEBKO, FEBRE, T028* | T028B/D/E/G, account symbols |
| **Budget (B2R)** | RFFMRP00, SAPLFMBU | FMIFIIT, FMIOI, FMBH, FMBL | YTFM_WRTTP_GR, YTFM_FUND_CPL |
| **HCM (H2R)** | RPTIME00, RP_CALC_* | PA0001-PA0027, IT0014, IT0015 | T510, T511, Allos BDC |
| **Intercompany** | SAPF100, SAPF124 | BSIK, BSAK, BSIS, BSAS | T001, GGB0/GGB1 rules |

~200 programs, ~100 tables, ~50 config objects. That's our universe. Not 452K tables.

## 4. Three Approaches Researched

### Approach 1: SAP Cross-Reference Tables (RECOMMENDED)

SAP already maintains the complete dependency graph in system tables:

| Table | Content | What We Get |
|---|---|---|
| **D010TAB** | Program → Table usage | Which programs read/write which tables |
| **WBCROSS** | Program → FM/Class calls | Call graph across all objects |
| **WBCROSSGT** | Global type references | Type dependencies |
| **D010INC** | Include dependencies | Program → include hierarchy |
| **TRDIR** | Program directory | Metadata (type, author, package, dates) |
| **TADIR** | Object catalog | Package → object mapping (already partially extracted) |

**Why this is the best:** SAP rebuilds these tables every time code is activated. 100% accuracy, zero parsing needed. We extract only for OUR objects (WHERE MASTER IN our_programs), not the entire system.

**Extraction plan:**
```python
# 1. Get our program list from TADIR (packages: YWFI, YFI, ZFI, YHR, etc.)
programs = extract("TADIR", where="DEVCLASS IN ('YWFI','YFI','ZFI','YHR','YPS','YFM')")

# 2. Get table usage for those programs
table_usage = extract("D010TAB", where="MASTER IN (our_programs)")
# Result: MASTER=program, TABNAME=table, SQESSION=SELECT/INSERT/UPDATE/DELETE

# 3. Get call graph
calls = extract("WBCROSS", where="MASTER IN (our_programs)")
# Result: MASTER=caller, NAME=called_object, OTYPE=FM/CLASS/PROG

# 4. Get include hierarchy  
includes = extract("D010INC", where="MASTER IN (our_programs)")
```

### Approach 2: ACE (ABAP Code Explorer) — Open Source

GitHub: https://github.com/ysichov/ACE/

**What it does:** Backward program slicing — builds data dependency graphs at FIELD level. Shows which fields a program needs from which tables, and how variables flow through the code.

**Advantage:** Field-level granularity (e.g., "line 852 reads PA0001-GSBER and writes to EPK-GSBER")
**Disadvantage:** Runs inside SAP as ABAP program — needs installation in D01. More complex than table extraction.

**When to use:** After Approach 1 gives us the program→table graph, use ACE for deep dives on critical programs (like LHRTSF01) to get field-level flows.

### Approach 3: SAP Knowledge Graph / Cerebro (Commercial)

SAP's own: 452K tables, 80K CDS views, 7.3M fields. Pre-built.
Cerebro: Scans system, builds enterprise knowledge graph. Commercial license.

**When to use:** If UNESCO decides on S/4HANA migration, this becomes relevant. Not now.

## 5. The Annotation Model

Every object in the Brain should support annotations — learnings from incident analysis, code review, or discovery sessions.

### Node with Annotations

```
ABAP_CLASS: LHRTSF01
  ├── type: SAP_STANDARD_INCLUDE
  ├── function_group: HRTS
  ├── lines: 3,526
  ├── domain: Travel
  ├── extracted: Session #048, extracted_code/SAP_STANDARD/TV_TRAVEL/
  │
  ├── ANNOTATIONS:
  │   ├── [#048] line 852: CRITICAL — bukst=bukrs same-company check. Intercompany gets no GSBER.
  │   ├── [#048] line 1693: SIDE_EFFECT — CLEARs GSBER on vendor lines (HRP/HRV)
  │   ├── [#048] line 1550: CROSS_COMPANY — restores GSBER for tax lines only, NOT vendor lines
  │   └── [#048] line 848: CONTROL_FLAG — gsber_a parameter controls whether GSBER is derived at all
  │
  ├── EDGES:
  │   ├── CALLS → LHRTSU05 (PTRV_ACC_EMPLOYEE_PAY_POST)
  │   ├── READS_TABLE → PA0001 (GSBER, BUKRS via wa_ep_translate)
  │   ├── READS_TABLE → PTRV_SCOS (COMP_CODE, BUS_AREA via cost assignment)
  │   ├── DERIVES_FIELD → BSEG.GSBER (from gsbst when bukst=bukrs)
  │   ├── CLEARS_FIELD → BSEG.GSBER (vendor lines, line 1693)
  │   └── INCLUDED_IN → SAPLHRTS (function group)
  │
  └── INCIDENTS:
      └── INC-000006073 → ROOT_CAUSE (line 852 + line 1693)
```

### Table with Annotations

```
SAP_TABLE: LFA1
  ├── type: TRANSPARENT_TABLE
  ├── rows: 316,104 (Gold DB)
  ├── cols: 147
  ├── domain: BusinessPartner
  │
  ├── ANNOTATIONS:
  │   ├── [#048] KTOKK field: determines LFB1.AKONT (reconciliation GL). Wrong KTOKK = wrong GL = missing GGB1 coverage.
  │   ├── [#048] 316K vendors but only 559 BUT000 records = <1% BP conversion done.
  │   ├── [#048] KTOKK=SCSA+PERSG=1 is anomalous — should be KTOKK=UNES for International Staff.
  │   └── [#048] ADRNR field → links to ADRC for full address. LFA1 name fields are vendor name, not address.
  │
  ├── EDGES:
  │   ├── READ_BY → LHRTSF01, ZCL_IM_TRIP_POST_FI, YFI_LFBK_TRAVEL_UPDATE
  │   ├── JOINS → LFB1 (via LIFNR)
  │   ├── JOINS → LFBK (via LIFNR)
  │   ├── DETERMINES → LFB1.AKONT (via KTOKK → account group → recon GL)
  │   └── MAPPED_BY → CVI_VEND_LINK (BP↔Vendor, currently 0 rows)
  │
  └── INCIDENTS:
      └── INC-000006073 → CONTRIBUTING_FACTOR (KTOKK=SCSA since 2016)
```

## 6. Implementation Plan for H34

### Phase 1: Extract SAP Cross-Reference (D010TAB + WBCROSS)
- Filter to UNESCO custom packages + known standard programs
- Load to Gold DB
- ~30 min extraction

### Phase 2: Build Code Brain Ingestor v2
- Reads D010TAB → creates READS_TABLE edges (replaces regex parser)
- Reads WBCROSS → creates CALLS_FM/CALLS_PROGRAM edges
- Reads D010INC → creates INCLUDES edges
- 100% accuracy, no false positives

### Phase 3: Annotation Framework
- Add `annotations` list to Brain node schema
- Each annotation: session, line, tag (CRITICAL/SIDE_EFFECT/CONTROL_FLAG), finding, impact
- Annotations survive brain rebuilds (stored separately, merged on build)
- Annotations are queryable: "show all CRITICAL annotations" or "what did we learn about LHRTSF01?"

### Phase 4: Incident Linking
- New edge type: ROOT_CAUSED_BY (incident → code:line + config)
- New edge type: CONTRIBUTING_FACTOR (incident → data anomaly)
- INC-000006073 becomes the first incident node with full traceability

### Phase 5: Session Learning Propagation
- At session close, every analyzed object gets annotations from that session
- Brain grows not just in nodes/edges but in **understanding per node**
- Next time someone asks about LHRTSF01, the Brain shows: "line 852 — critical for intercompany GSBER, discovered in INC-000006073"

## 7. The Value Proposition

**Without annotations:** "LHRTSF01 is an include in function group HRTS with 3,526 lines. It reads PA0001 and calls LHRTSU05."

**With annotations:** "LHRTSF01 line 852 is CRITICAL — it only fills GSBER for same-company postings. Line 1693 clears GSBER on vendor lines. This caused INC-000006073 when an IIEP traveler had a UNES-funded trip. The BAdI fallback (PA0027-02) is expired since 2021. The exit (ZXTRVU05) is commented out since 2018. Three safety nets are broken."

That's the difference between a graph database and a **knowledge brain**.

## 8. References

- [ACE: ABAP Code Explorer](https://github.com/ysichov/ACE/) — open source field-level dependency analysis
- [SAP Cerebro AI](https://www.aifalabs.com/cerebro/sap-ai-code-assistant) — commercial enterprise knowledge graph builder
- [SAP Knowledge Graph](https://www.sap.com/products/artificial-intelligence/ai-foundation-os/knowledge-graph.html) — 452K tables, 80K CDS views, 7.3M fields
- [SAP Knowledge Graph for LLM Grounding](https://community.sap.com/t5/technology-blog-posts-by-sap/knowledge-graphs-for-llm-grounding-and-avoiding-hallucination/ba-p/13779734)
- [WBCROSSGT Documentation](https://www.tcodesearch.com/sap-tables/WBCROSSGT)
- [SAP-ABAP-1 Foundation Model](https://www.sap.com/products/artificial-intelligence/sap-abap.html)
