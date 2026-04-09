# Recovering Historical Annotations — 47 Sessions of Lost Learnings

**Problem:** Sessions #001-#047 produced learnings about specific programs, tables, and config objects. Those learnings exist in retros, knowledge docs, skills, and memory files — but were never tagged back to the objects. Every time we re-encounter an object, we re-discover what we already knew.

**Examples of lost annotations:**

| Source | Learning | Should Be Tagged To |
|---|---|---|
| feedback_bseg_is_readable.md | "BSEG declustered in P01, no MANDT in WHERE" | SAP_TABLE:BSEG |
| feedback_bseg_is_join_not_table.md | "BSEG is a JOIN via Golden Query, never extract" | SAP_TABLE:BSEG |
| project_golden_query.md | "FMIFIIT.KNBELNR = BKPF.BELNR — perfect 1:1 FM↔FI join" | SAP_TABLE:FMIFIIT, SAP_TABLE:BKPF |
| session_029_retro.md | "FEBEP 10xxxxx = permanent ledger, 11xxxxx = clearing" | SAP_TABLE:FEBEP |
| session_021_retro.md | "BCM workflow 90000003, 3,394 same-user batches" | CONFIG:BCM_WORKFLOW |
| payment_full_landscape.md | "FPAYP.XREF3 carries PurposeCode for DMEE" | SAP_TABLE:FPAYP, field XREF3 |
| session_038_retro.md | "DMEE AE/BH classes don't exist, real classes contain no Purp/Cd" | ABAP_CLASS:YCL_IDFI_CGI_DMEE_* |
| feedback_tabkey_language_codes.md | "D/E/F/P in TABKEYs = SPRAS language keys" | Multiple config tables |
| session_030_retro.md | "EBS algo 015 = 85.7% of bank statement postings" | CONFIG:T028B |
| sap_house_bank_configuration SKILL.md | "T012/T012K/T030H/T035D = house bank config chain" | SAP_TABLE:T012, T012K, T030H, T035D |

## Recovery Strategy

### Option A: AI-Assisted Mining (recommended for H34)

Use Claude to read each knowledge doc and extract object-level annotations:

```
For each file in knowledge/domains/**/*.md + session_retros/*.md + memory/feedback_*.md:
  1. Read the file
  2. Identify every SAP object mentioned (program, table, FM, config, field)
  3. For each object, extract:
     - What was learned about it
     - Why it matters (impact)
     - Which session discovered it
     - Any incidents or issues related
  4. Call annotate() for each finding
```

This is a Claude task, not a script — it requires understanding context, not regex.

### Option B: Pattern-Based Extraction (partial, automated)

```python
# Mine feedback files for table/program references
for file in glob("memory/feedback_*.md"):
    content = read(file)
    # Extract SAP object names (Z*, Y*, T0*, PA00*, BSEG, BKPF, etc.)
    objects = re.findall(r'\b([TZY][A-Z0-9_]{3,30}|[A-Z]{2,4}[0-9]{2,4}|BSEG|BKPF|BSIK|BSAK|FEBEP|FMIFIIT)\b', content)
    # The feedback file's finding = the annotation
    for obj in objects:
        annotate(obj, tag="HISTORICAL", finding=summarize(content), session=extract_session(file))
```

Catches ~40% of learnings. Misses context and impact.

### Option C: Session Retro Mining (structured)

Session retros have a consistent structure:
- "Key Discoveries" section → annotations
- "What Went Well" → validated patterns
- "What Went Wrong" → anti-patterns to tag

```python
for retro in glob("session_retros/session_*_retro.md"):
    discoveries = extract_section(retro, "Key Discoveries")
    for discovery in discoveries:
        objects = find_sap_objects(discovery)
        for obj in objects:
            annotate(obj, tag="DISCOVERY", finding=discovery, session=extract_session_number(retro))
```

## Session Close Protocol Addition

At session close, BEFORE writing the retro:

```
1. List every SAP object analyzed this session (programs, tables, config)
2. For each object, summarize what was learned
3. Call annotate() for each learning
4. THEN write the retro (retro references annotations, not the other way around)
```

This ensures zero learnings are lost going forward. Historical recovery (Options A-C) catches the past.

## Priority

1. **NOW:** Session #048 annotations seeded (DONE — 15 objects, 21 annotations)
2. **H34:** Run Option A on the top 20 knowledge docs (highest-value learnings)
3. **Ongoing:** Add annotation step to session close protocol
4. **Backlog:** Run Option B+C on all 130+ docs for completeness
