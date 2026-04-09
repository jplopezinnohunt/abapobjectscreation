# Session #049 Plan

## Hypothesis (what this session will prove)
H1: SAP's own cross-reference tables (D010TAB, WBCROSS, D010INC) provide a complete, 100%-accurate dependency graph that replaces regex parsing
H2: Materializing metadata edges + cross-reference data transforms the Brain from 4,030 orphan ABAP nodes into a connected dependency graph where `impact` and `depends` queries return real chains

## Deliverables (shippable artifacts, named)
1. Gold DB tables: D010TAB, WBCROSS, D010INC extracted from P01
2. Brain v2 cross-reference ingestor — reads D010TAB/WBCROSS/D010INC from Gold DB → graph edges (READS_TABLE, CALLS_FM, INCLUDES)
3. Brain v2 rebuild with all new data (34 SAP standard files, 21 BP tables, cross-references, annotations)
4. Validation: `brain_v2 impact LFA1` shows chain to GGB1 rules
5. Validation: `brain_v2 depends ZCL_IM_TRIP_POST_FI` shows PA0027 + HR_READ_INFOTYPE

## Out of scope (declared)
- G56 Travel/BP discovery (next session)
- G55 BP Conversion Readiness research
- Historical annotation deep review (200+ annotations) — only if time permits after core deliverables
- Any new data extraction beyond D010TAB/WBCROSS/D010INC

## Success criteria (testable at close)
- [ ] H1: D010TAB/WBCROSS/D010INC in Gold DB with row counts documented
- [ ] H2: `brain_v2 impact LFA1` returns multi-hop chain (not empty)
- [ ] H2: `brain_v2 depends ZCL_IM_TRIP_POST_FI` returns dependencies (not empty)
- [ ] 4,030 orphan ABAP nodes reduced to <500
- [ ] items_shipped >= items_added

## What a reasonable reviewer would ask to kill
- "Is anyone actually querying the Brain?" — Yes: INC-000006073 was the first real incident resolved using platform intelligence. Cross-references make every future incident faster.
- "Why not just grep the extracted code?" — Grep finds text matches. Cross-references find runtime dependencies (dynamic calls, config reads) that grep misses. SAP maintains these at compile time.
- "Is this just more write-only brain growth?" — No: the validation queries (impact/depends) are the test. If they don't return useful chains, the session fails.
