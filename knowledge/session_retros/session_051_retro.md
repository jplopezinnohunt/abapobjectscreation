# Session #051 Retrospective
**Date:** 2026-04-09 | **Duration:** ~6 hours (full investigation + finalization) | **Type:** Single-incident deep investigation + post-mortem of Session #50
**Focus:** INC-000005240 — XREF office-tag substitution gap; retrospective learnings from Session #50 wrong-path; full brain finalization

## Primary artifact

**This session's closing document IS the incident report:** [knowledge/incidents/INC-000005240_xref_office_substitution.md](../incidents/INC-000005240_xref_office_substitution.md)

Everything material (root cause, evidence, fix path, process lessons, scale metrics, end-to-end model) lives there. This retrospective exists only to capture **session-level metadata**, not to duplicate content.

## What happened — one-paragraph summary

INC-000005240 (AL_JONATHAN, Jakarta Field Unit, F-53 outgoing payment reporting `XREF='HQ'` instead of `'JAK'`). Session #50 delegated the workflow to a subagent which burned 154K tokens chasing the wrong mechanism (FMDERIVE fund center hardcoding in `ZXFMDTU02_RPY` — a real but unrelated observation). Session #51 restarted in the main agent, translated the user's own-language terms to SAP fields first, and found the actual root cause in ~3 hours of investigation: `USR05.Y_USERFO='HQ'` driving `YRGGBS00` `UXR1`/`UXR2` substitution on every BSEG line. Spent an additional ~3 hours on retrospective / domain knowledge harvest / brain finalization. Session closed with a single commit (`877b635`).

## The two pivots that shaped the investigation

**Pivot 1 — "do not delegate to subagent, main agent holds context".** Early in Session #51 I started down the same path as Session #50 (handing the `.eml` to a subagent). User pushed back: main agent must read the email and hold the terminology translation directly. Pivot produced `feedback_main_agent_holds_incident_context` + `feedback_read_emails_in_main_agent`.

**Pivot 2 — "read PSM/EXTENSIONS first; you are not using it".** Mid-investigation I was re-deriving the YRGGBS00 form-pool structure from scratch. User pointed out that `knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md` + `validation_substitution_matrix.md` + `basu_mod_technical_autopsy.md` already existed and documented UAEP/UATF/U904/U917 in full — I just hadn't looked. The gap was specifically the XREF trio (UXR1/UXR2/UZLS), which INC-000005240 then filled. Pivot produced `feedback_psm_extensions_is_fi_substitution_home`.

**Pivot 3 — "bseg_union has no XREF columns; you are reading empty fields from a non-existent schema".** I claimed `XREF` was blank on GL lines based on a `bseg_union` query. CDPOS then contradicted the claim: a live `VALUE_OLD='HQ'` on the bank GL line of doc `3100003438` proved substitution had fired there at posting time. The "blank" was an artifact of `bseg_union` not carrying XREF columns at all. Pivot produced `feedback_bseg_union_has_no_xref` + `feedback_empirical_over_theoretical_substitution`.

**Pivot 4 — "FB1K clearing pair is metadata, not a real business line".** I initially flagged the `L_HANGI` FB1K clearing docs as a "1,300× blast radius structural risk" based on the `BSCHL=27/37` zero-balancing pair carrying the clearing user's XREF. User pointed out: these lines net to zero, have no financial impact, and the ORIGINAL invoice line's XREF is preserved. Severity downgraded from HIGH to LOW for that class. Pivot produced `feedback_metadata_vs_real_bseg_lines`.

## Deliverables (13)

| # | Deliverable | Type |
|---|---|---|
| 1 | [knowledge/incidents/INC-000005240_xref_office_substitution.md](../incidents/INC-000005240_xref_office_substitution.md) — canonical 16-section report (§1 intake, §2 exec summary, §3.2/3.3/3.4 unified validation+substitution model, §4 investigation, §5 system execution chain, §6.1 AUGBL trace, §7 seven broken safety nets, §7.5 cross-user observation with REAL/METADATA distinction, §8 evidence, §10 fix recommendation with KU-027 YFO_CODES prerequisite, §13 wrong-path triage) | Incident |
| 2 | [knowledge/domains/Treasury/xref_office_tagging_model.md](../domains/Treasury/xref_office_tagging_model.md) — new end-to-end Treasury domain doc: TCODE×event coverage matrix, REAL/METADATA line distinction, scale metrics, 5 fix design patterns | Domain knowledge |
| 3 | [knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md](../domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md) §2.5–§2.8 added: UXR1/UXR2/UZLS/U915/U916/U917 verbatim source and behavior, fills the historical gap in the PSM autopsy | Domain knowledge |
| 4 | [knowledge/domains/FI/ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md) appendices A/B/C: GB93/GB931 findings, BOOLID naming convention (`1<name>###X`=CONDID, `2<name>###X`=CHECKID, `3<name>#X`=substitution prerequisite), T80D form pool registration | Domain knowledge |
| 5 | [knowledge/observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md](../observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md) — new observations/ folder created; Session #50 FMDERIVE wrong-path analysis triaged here as a standalone observation, NOT linked to INC-000005240 | Observation |
| 6 | [.agents/skills/sap_incident_analyst/SKILL.md](../../.agents/skills/sap_incident_analyst/SKILL.md) — Core Principles expanded from 5 → 12 rules; Step 3 Gold DB pull now has mandatory GGB-table extraction list and Gold DB schema gotchas | Skill |
| 7 | [.claude/agents/incident-analyst.md](../../.claude/agents/incident-analyst.md) — CRITICAL section expanded with the 12-rule framework | Agent def |
| 8 | 7 new feedback rules (62 → 69): `psm_extensions_is_fi_substitution_home`, `bseg_union_has_no_xref`, `empirical_over_theoretical_substitution`, `metadata_vs_real_bseg_lines`, `no_learning_capture_mid_investigation`, `extract_ggb_tables_for_substitution_incidents`, `read_emails_in_main_agent` | Rules |
| 9 | `brain_v2/incidents/incidents.json` — INC-000005240 first-class record (1 → 2 incidents) | Brain layer 11 |
| 10 | `brain_v2/annotations/annotations.json` — 22 new object annotations (34 → 53 objects): YRGGBS00/UXR1/UXR2/UZLS/U915/U916/U917, USR05, USR05.Y_USERFO, YFO_CODES, PA0001, PA0001.BTRTL, PA0105, VALID=UNES, SUBSTID=UNESCO, GB93, GB931, GB905, GB921, BSEG.XREF1/XREF2/ZLSCH. Plus 3 wrong-path objects retagged as observation-only | Brain annotations |
| 11 | `brain_v2/claims/claims.json` — 11 new Tier-1 claims (30 → 41); 4 wrong-path Session #50 claims (27–30) downgraded to `TIER_3_OBSERVATION_ONLY` | Brain claims |
| 12 | `brain_v2/agi/known_unknowns.json` — 6 new KUs (26 → 32): KU-027 (YFO_CODES JAK), KU-028 (class generalization), KU-029 (downstream impact), KU-030 (UXR1 guard history), KU-031 (GB905 empty), KU-032 (F110 bank GL anomaly); 3 old KUs retagged | AGI layer |
| 13 | `brain_v2/agi/data_quality_issues.json` — 3 new DQs (17 → 20): DQ-018 (AL_JONATHAN Y_USERFO drift), DQ-019 (21,754 Q1 manual corrections systemic), DQ-020 (BTRTL↔Y_USERFO mapping gap) | AGI layer |

## Evidence extracted this session

| Source | What | How |
|---|---|---|
| `YRGGBS00_SOURCE.txt` lines 996–1119 | UXR1/UXR2/UZLS body | File read |
| `YRGGBS00_SOURCE.txt` lines 1499–1590 | U915/U916/U917 body | File read |
| `USR05` | `Y_USERFO` for 13 users (AL_JONATHAN, A_HIZKIA, T_ENG, S_EARLE, C_LOPEZ, I_MARQUAND, B_GAZI, I_WETTIE, S_AGOSTO, JJ_YAKI-PAHI, L_HANGI, O_RASHIDI, DA_ENGONGA) | Live RFC per-user (IN (...) blocked by SAIS) |
| `PA0001` + `PA0105 SUBTY='0001'` | HR cross-reference for 7 users — authoritative office = WERKS+BTRTL | Live RFC |
| `BSAK`, `BSAS`, `BSIS` | 10 AL_JONATHAN F-53 vendor lines + 36-line full sweep | Live RFC |
| `CDHDR` (Gold DB, 7.8M rows) + live RFC for A_HIZKIA changes | Full change history for AL_JONATHAN's 10 F-53 docs; 22K UNES BELEG manual edits count for Q1 2026 | Gold DB query + RFC |
| `CDPOS` | A_HIZKIA's 2 FBL3N changes on docs 3100003438/3100003439 — proved `XREF1` `HQ`→`JAK` and `VALUE_OLD='HQ'` at time of change | Live RFC |
| `GB93` | 17 rows, validation header; key row `VALID='UNES' BOOLCLASS='009'` | Live RFC (full extraction, client-side filter) |
| `GB931` | 53 rows, 12 steps for `VALID='UNES'` with full CONDID/CHECKID/VALSEVERE/VALMSG map | Live RFC |
| `GB905`, `GB921`, `GB92`, `GB90` | All empty at UNESCO via broad probe — step-to-prerequisite linkage is NOT in standard tables | Live RFC |
| `bkpf` (Gold DB) | AL_JONATHAN's FBZ2 docs + F110 posters + L_HANGI XBLNR patterns + scale metrics | Gold DB queries |
| `bseg_union` (Gold DB) | AUGBL trace proving self-clearing (AL_JONATHAN) vs external clearing (DA_ENGONGA) | Gold DB queries |
| `T80D` | Form pool registration: `GBLR`/`GBLS` → `YRGGBS00` (both validation and substitution) | Gold DB |
| SE93 for F-53 | Parameter transaction defn: Target = `FBZ2`, Screen 103, Module pool SAPMF05A | User-provided screenshot |

## Hypotheses tested

| # | Hypothesis | Result |
|---|---|---|
| H51.1 | The substitution fires on every BSEG line on F-53, not just vendor lines | **CONFIRMED** via CDPOS `VALUE_OLD='HQ'` on bank GL line 001 of doc 3100003438. My earlier "vendor-lines-only" claim was a `bseg_union` schema artifact (false negative from a column that doesn't exist) |
| H51.2 | F-53 manual payment is completely outside the UNES line-item validation layer | **CONFIRMED** via GB931 extraction: F-53/FBZ2 is in zero CONDIDs across all 12 UNES validation steps |
| H51.3 | F110 automatic payment run fires substitution on vendor line but NOT on bank GL line | **CONFIRMED** via live RFC on C_LOPEZ's F110 clearing docs — vendor line has `XREF='HQ'`, bank GL line is blank. Mechanism still unexplained (KU-032) |
| H51.4 | A_HIZKIA is a Jakarta user independently confirming the correct value | **CONFIRMED** via USR05 RFC: her `Y_USERFO='JAK'` |
| H51.5 | PA0001.BTRTL and USR05.Y_USERFO use different code systems at UNESCO | **CONFIRMED** via 7-user PA0001+USR05 sample: KBL vs KAB (Kabul), DKR vs DAK (Dakar), JKT vs JAK (Jakarta), PAR vs HQ (Paris) |
| H51.6 | The UNES validation rule family `1UNES###X` / `2UNES###X` is the CONDID/CHECKID pair for 12 validation steps; `3UNESCO#X` is substitution | **CONFIRMED** via GB931 extraction showing CONDID/CHECKID naming pattern |
| H51.7 | FB1K zero-balance clearing pair (BSCHL=27/37) is metadata, not a real business line | **CONFIRMED** via analysis — pair nets to zero, original invoice line XREF preserved. Initial severity of 1,300× downgraded to LOW for this class |
| H51.8 | Session #50's subagent chased the wrong mechanism (FMDERIVE instead of XREF substitution) | **CONFIRMED** via reading the v1 file + comparing to actual .eml: "reference key" literally meant BSEG-XREF1/XREF2, not FISTL/FICTR |

## Scale metrics captured

- **AL_JONATHAN posting history:** 14 BKPF docs (10 FBZ2 outgoing payments + 4 FBZ1 incoming — excluded from scope); 36 BSEG line items; 100% self-clearing; all vendor lines tagged `HQ/HQ`; blast radius bounded to his 10 weeks of activity
- **UNESCO manual workaround scale Q1 2026:** 21,754 post-posting edits via FBL3N/FBL1N/FB02/FBL5N on UNES BELEG; 242 distinct users; 24,597 distinct documents touched
- **Top manual editors:** C_VINCENZI 2,075, R_MUSAKWA 1,422, I_BIDAULT 631, M_AHMADI 550, L_HANGI 499, A_HIZKIA 932 (full year)
- **Jakarta cluster (A_* prefix):** ~5,400 FBL3N edits over 2 years
- **Brain v2 stats after rebuild:** 53,909 nodes / 114,009 edges / 69 rules / 41 claims / 4 incidents / 12 domains / 59% coverage / 50 blind spots

## What went better than Session #50

- Main agent read the `.eml` directly; terminology translation was correct on first pass
- Empirical path (CDPOS + AUGBL + RFC) pushed back hard on wrong theoretical hypotheses
- User challenges at each step forced recalibration (delegation, PSM/EXTENSIONS, bseg_union, FB1K metadata)
- 6 hours vs the 154K-token dead end of Session #50

## What still needs to be better

- **I still speculated about GB901 step prerequisites** before extracting GB905/GB921 at the start — the GGB table extraction should have been in Step 3 from the beginning, not discovered mid-investigation
- **I flattened the report to match the user's draft verbatim** on one iteration — losing rigor until the user said "do your own analysis, my draft is a best guess". Should have trusted evidence over the user's suggested framing
- **Session #50 subagent artifacts** (FMDERIVE analysis, claims 27–30, KU-024/025/026) were left in the brain and needed retagging at finalization. A clean rollback of wrong-path brain entries should have been part of early investigation cleanup, not end-of-session
- **F110 bank GL XREF anomaly (KU-032)** remains unexplained. The "F-53 fires on all lines, F110 fires only on vendor line" asymmetry was observed but not fully traced to a mechanism — would need GGB1 GUI inspection or BAPI_ACC_DOCUMENT_POST trace which is outside Claude's empirical reach

## Scope clarification recorded this session

**We recommend, we do not execute master-data or config changes at UNESCO.** The investigation produces the analysis, recommendation, fix path, and evidence trail. Execution (SU3 update, YFO_CODES row addition, GGB1 config change, transport creation) is the UNESCO BASIS / master-data / functional team's responsibility. This was explicitly clarified by the user mid-session.

## Follow-ups (handed off, not blockers for session closure)

| ID | Item | Owner |
|---|---|---|
| KU-027 | Verify `'JAK'` exists in `YFO_CODES.FOCOD` before SU3 deployment | UNESCO BASIS / Finance |
| KU-028 | Run the PA0001×PA0105×USR05 class-generalization audit (diagnostic — we can run this on request) | UNESCO / us if requested |
| KU-029 | Downstream impact trace on the 21,754 Q1 corrections (BCM routing, field-office reports) | UNESCO Finance / BI |
| KU-030 | Git blame on `YRGGBS00_SOURCE.txt:998` for the commented-out UXR1 guard | UNESCO ABAP team |
| KU-031 | Where is the substitution step linkage at UNESCO if GB905/GB921 are empty? | UNESCO BASIS (GGB1 GUI) |
| KU-032 | F110 bank GL XREF asymmetry vs F-53 | UNESCO ABAP team (SAPF110S trace) |
| Strategic | Add XREF consistency validation as a 13th step to `VALID='UNES'` — see INC-000005240 §10.3 Option A | UNESCO Finance decision |
| Strategic | Audit the class of drifted users across UNES (KU-028 implementation) | UNESCO BASIS |

## Commit

[`877b635`](../../) — INC-000005240 closure: XREF office-tag substitution gap + retrospective (37 files staged, 4 unrelated files left for their respective owners)

## Cross-references

- **Previous session retro:** [session_050_retro.md](session_050_retro.md) — Brain v3 + incident methodology bootstrap
- **Incident canonical doc:** [INC-000005240_xref_office_substitution.md](../incidents/INC-000005240_xref_office_substitution.md)
- **Cross-domain impact:** [Treasury/xref_office_tagging_model.md](../domains/Treasury/xref_office_tagging_model.md), [PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md](../domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md), [FI/ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md)
- **Wrong-path observation:** [observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md](../observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md)
