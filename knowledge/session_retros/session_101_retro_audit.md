# Session #101 — AGI Retro Audit

**Verdict:** FAIL
**Auditor:** agi_retro_agent (fresh subagent, no session narrative)
**Audit timestamp:** 2026-08-19T19:30+04:00
**Scope audited:** commits `81b0baa` (17:55) and `06e5244` (19:04), the brain source stores, the
generated entry points, the task artifact folder, PMO_BRAIN, and the project's own quality gates.

> Reading note: this audit does not dispute the SAP work. The SAP work is the best part of the
> session and is corroborated below. It disputes what happened to that work afterwards.

---

## Headline

The session did the hard thing (proved a control end-to-end in D01 with a real file) and then
skipped every step that makes the proof survive the session boundary. **The whole session touched
4 files** [VERIFIED — `git log --since="2026-08-19 17:30" --name-only`: two XMLs, `claims.json`,
`incidents.json`]. No rebuild, no index, no memory, no companion, no domain doc, no rule, no
check, no PMO, no push.

The measurable consequence: **`brain_v2/BRAIN_INDEX.md` — the file every session is ordered to read
first — still tells the next agent `INC-EGYPT-PPC - SPEC_READY` and instructs it to build "T1 …
T015L 10 rows EG0..EG9"** [VERIFIED — `BRAIN_INDEX.md:93-94`, file mtime 16:36 vs `incidents.json`
19:03]. That plan is wrong on three counts as of 19:04: the config is already built, it has 5 codes
not 10, and the single transport that exists carries an Indonesian key. A session obeying the entry
point would re-derive a superseded plan and could instruct the user to rebuild what is built.

This is the exact failure the project diagnosed in s099 and wrote a rule and a gate for. Both the
rule and the gate are in the repo. Neither stopped it.

---

## Principle Scores

| # | Principle | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Consistency | **0** | `brain_state.json` holds 520 claims / max id 521; `claims.json` holds 526 / max id 527 [VERIFIED, python read]. `brain_state` incident `INC-EGYPT-PPC.status = SPEC_READY`, no `build_record`, no `e2e_test_d01`, `ticket_number = None`. PMO_BRAIN header "Last reconciled: Session #082", count "29 High \| 36 Backlog = 65 total" while the file lists items through H100 [VERIFIED, `PMO_BRAIN.md:1,10`]. |
| 2 | Reusability | **0.5** | `Zagentexecution/tasks/2026_08_19_egypt_ppc_d01_test/` contains 2 XML files and nothing else [VERIFIED, `ls -a`]. CLAUDE.md §File Organization mandates `task_details.md` + `learning_summary.md`. No skill owner declared; **zero files under `.agents/skills/` changed on 2026-08-19** [VERIFIED, `git log --name-only -- .agents/skills/`]. |
| 3 | Closure over discovery | **0.5** | Two open questions closed with execution evidence (Ustrd exit wiring; the render half). At least four new open items created (split the transport; confirm 5 reasons with Mathewos/CitiService; add pay-type R rows; remove the Indonesian key from `D01K9B0FXF`). **None entered PMO_BRAIN** — last commit touching it is `5445a17` at 16:33, before both Egypt commits [VERIFIED]. Closure is real; the ledger was not updated, so it is unauditable next session. |
| 4 | Hypothesis-grounding | **1** | Strongest principle of the session. The `<Ustrd>` string was **predicted** by simulating CM003/CM004 over the read config, then the F110 file was generated and matched character-for-character [VERIFIED — `incidents.json` `config_verified_d01.rendered` written before `e2e_test_d01.result`; both commits ordered 17:55 then 19:04]. That is a falsifiable pre-declaration, executed. |
| 5 | Anti-hoarding | **1** | No Gold DB tables added. The REGUH 3.7M-line pull was aimed at a specific question (does pay type R ever fire?) and answered it. |
| 6 | Stale detection | **0** | No zombie review performed. PMO is 19 sessions past its last reconciliation by its own header. |
| 7 | Knowledge routing | **0** | No skill updated. **No feedback rule added** — `feedback_rules.json` holds 214 rules, last commit `5445a17` at 16:33 (pre-Egypt) [VERIFIED]. Three distinct mechanizable defect classes were discovered and none were routed. |
| 8 | Best-practices drift | **0.5** | The project's own gate `knowledge_reachability_check.py` **exits 0** against an index that is materially misleading [VERIFIED, run at audit time]. The check asserts `incident_id in index` and that `next_action` is non-empty *in the store* (lines 63-70) — it never compares the index's rendered text against the store. Ceremony, not substance. |
| 9 | Brutal honesty | **0.5** | Genuine credit: the block-test tier limit is stated in three places — claim 527 body, `incidents.json` `e2e_test_d01.block_test.tier`, and the `06e5244` commit body ("no vi la pantalla, y asi queda etiquetado"). Deduction: claim 527's own `resolution_notes` contradicts its body (below), and claim 526 still asserts a D01 state that had already been repaired. |
| 10 | Self-verification | **0.5** | Every cited path resolves and the quoted ABAP is verbatim [VERIFIED — `extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_UTIL_CM004.abap` contains exactly the `IF iv_value_c IS INITIAL … ENDIF` body claim 524 quotes; `YRGGBS00_SOURCE.txt:1547+` is `FORM u917`]. Deduction: claim 527 carries a single `confidence: TIER_1` over two halves of unequal evidential strength, and its `evidence_for` list has **no entry at all** for the block half. |

**One failing principle is enough to FAIL. Four fail outright (1, 6, 7, and — by its own gate — 8).**

---

## Per-Core-Principle score

### CP-001 Knowledge over velocity — **FAIL**
The artifact that convicts: `brain_v2/BRAIN_INDEX.md:93` (mtime 16:36) versus
`brain_v2/incidents/incidents.json` (mtime 19:03). Three hours of the session's best work exist
only in two source JSON files and are invisible to both mandatory entry points. CP-001's own
`how_to_apply` says traceability loss is irreversible while slowness is reversible; the session
chose to end at 19:04 rather than run `python brain_v2/rebuild_all.py`.

Second artifact: `companions/inc_egypt_ppc_configuration.html` (mtime **Aug 17** 20:45) still lists
ten codes `EG0..EG9`, still contains the word `unproven`, and contains **0** occurrences of
`INC-000016101` or `D01K9B0FX` [VERIFIED, grep]. Yet `incidents.json` `next_action` sends the next
reader to "companions/inc_egypt_ppc_configuration.html seccion 11" for the step-by-step, and claims
525 and 527 both say they *close* "the one thing still unproven de … seccion 5". The companion still
says it is unproven. CLAUDE.md §"Companion & Report Quality Rules" #1 (cross-reference rule) is
violated head-on. `knowledge/domains/Procurement/p2p_purpose_of_payment_e2e.md` (mtime Aug 17
19:57) is equally stale: 0 mentions of the ticket, the transports, or `224938`.

Third: `git branch -vv` → `master … [origin/master: ahead 2]`. Per MEMORY.md's own durability rule,
"Durabilidad = on origin". The E2E proof exists on one disk.

### CP-002 Preserve first, context is cheap — **PASS WITH CONDITIONS**
Nothing was destroyed or lossily compressed; the incident record is exceptionally rich
(`build_record`, `deviations_from_spec` with 6 typed entries, `config_verified_d01`,
`e2e_test_d01`). That is correct CP-002 behaviour and the best-structured artifact of the session.

The condition: CP-002 says explicitly *"Never concatenate evidencia distinta en un string — siempre
lista tipada con type/ref/cite."* Claim 527 is a ~4,000-character single string that concatenates
(a) file-artifact evidence, (b) source-simulation evidence, (c) a user's screen observation, and
(d) two collateral validation rules — with one flat `confidence: TIER_1` over all of it. The
structure cannot express what the prose correctly admits.

### CP-003 Precision, evidence, facts — **PASS WITH CONDITIONS (with one hard violation)**
Strong evidence: every `evidence_for.ref` resolves on disk; the ABAP quotes are verbatim; the
numbers are exact, not approximate (3,707,737 REGUH lines; HR-PY 180,372; TR-CM-BT 713; 17 transport
keys = 5+11+1; 2,153 bytes). The prediction-then-execution sequence is textbook CP-003.

Hard violation: **claim 526 is now factually wrong as a standalone record.** It states, present
tense, that `YTFI_PPC_STRUC ID/USTRD/O/01` "tiene el separador BORRADO en D01 (vacio frente a '/' en
P01)" and that the built T015L list is "EG0..EG4 (SUPP/SCVE/**SALA**/BEXP/CHAR)". Both were repaired
the same day: `incidents.json` deviation 1 is `RESOLVED_VALUE_RESTORED_KEY_REMAINS` and
`config_verified_d01` shows `EG2 BEXP / EG3 CHAR / EG4 OTHR` with SALA withdrawn. Claim 526 was
written in `81b0baa` and **was not amended in `06e5244`** — that commit touched only claims 524 and
527 [VERIFIED, `git show 06e5244 -- brain_v2/claims/claims.json | grep '"id"'`]. The claims store and
the incidents store now disagree about the current contents of D01.

---

## The specific judgements requested

### 1. Claim 527's TIER_1 over two unequal halves — **not defensible as structured, honest as prose**

What is right: the caveat is explicit and appears in three independent places, including the commit
message. The agent did not launder a second-hand observation into first-hand evidence in the prose.

What is wrong, and it is not cosmetic:
- `confidence` is a single scalar `TIER_1` covering a half whose only witness is the user's screen.
  Any consumer filtering `confidence == "TIER_1"` — `graph_queries.py`, the trust layer, a future
  agent — gets a TIER_1 verdict on a report the agent did not observe.
- `evidence_for` has 5 entries. **None of them is the block test.** The closest, the GB931/T100
  read, is evidence for *which message step 012 owns*, not evidence that a posting was rejected.
  The load-bearing observation for half the claim has no typed evidence row at all — it exists only
  inside the prose blob. That is precisely what CP-002's typed-evidence rule exists to prevent.
- `resolution_notes` on claim 527 reads: *"Deja abierta SOLO la prueba del bloqueo (u917 sin
  LZBKZ)."* The claim body says the block half **is** proven. A record that contradicts itself in
  two fields is worse than either version alone — leftover from the pre-amendment draft, not caught.
- **No negative control was run.** The causal attribution — "the rejection was caused by the EG rows
  via u917" — rests on the message text being unique to step 012. Nobody posted the same FB60
  against a non-PPC-country vendor, and nobody posted it before the EG rows existed. One extra FB60
  would have isolated the cause. The claim states the mechanism as established; it is inferred.

Correct shape: split the block half into its own claim at TIER_2 with an `evidence_for` entry of
type `user_report` (witness, date, transaction, what was on screen), leaving 527 TIER_1 for the file.

### 2. The pay-type-R downgrade — **the original was not evidence-based; the correction is only half-reachable**

The original rating was CRITICAL and was derived from design symmetry (the companion's "lo unico que
no hay que copiar" framing of BH/MY/PH), not from measured traffic. Asserting a severity from a
pattern rather than a measurement is a live CP-003 violation, self-corrected within the session —
which is the right outcome, and the record says so in the agent's own words: *"MEDIDO 2026-08-19, y
corrige mi propia valoracion inicial de CRITICO"* [`incidents.json`, `deviations_from_spec[n=3]`].
Credit where due: the correction is explicit, self-attributed, and carries exact numbers and the
limit of the measurement ("la nomina de El Cairo no aparece como HR-PY … no investigado").

Where it is not reachable:
- Claim 526's deviation (3) still reads in the original framing — "un payment request de Tesoreria a
  Egipto emite VACIO en silencio … justo el defecto de BH/MY/PH" — with no measurement and no
  downgrade. The claims store carries the un-corrected version.
- `brain_state.json` carries neither version (stale).
- The genuinely reusable, class-level fact — **six countries' R rows have never fired in ten years;
  the PPC pay-type coverage was built by defensive symmetry, not measured traffic** — exists only as
  prose inside one deviation entry of one incident. It is not a claim. It will not surface for the
  next country added.

### 3. The Indonesia near-miss — **named as a class, mechanized as nothing**

The generalization is genuinely articulated (claim 526's closing sentence; deviation 1's `fix`
ordering "restore first, then edit the object list, and not the inverse"). That is real thinking.

But: `Zagentexecution/quality_checks/ppc_country_consistency_check.py` has mtime **Aug 18 09:46** and
was not touched [VERIFIED]. `feedback_rules.json` was not touched by either Egypt commit [VERIFIED].
No procedure doc was written. **Zero mechanization for three separately-specified defect classes:**

| Class found today | Mechanizable as | Cost |
|---|---|---|
| SEPARATOR row with empty `PPC_VALUE` → string comes out glued | check E, static, Gold DB — the nine configured countries are the reference set | small |
| `T015L-ZWCK1` with two spaces → `SPLIT AT SPACE` leaks a blank into the narrative | check F, static, Gold DB, byte-exact read | small |
| SM30 maintenance of one country captures a neighbour's key; only a whole-table D01-vs-P01 diff sees it | check G, needs an RFC read of both systems + `E071K` | medium |

The project's own standard is that by the **2nd occurrence** you owe a procedure and a recurring
check. The 2nd occurrence happened *inside this session*: invisible-whitespace-in-a-maintained-field
bit twice in one day, in two different tables (`PPC_VALUE` separators, `T015L-ZWCK1`). The gate had
already tripped before the session ended. Also note the irony of scope: this very check file's
docstring says it was "Promoted from INC-EGYPT-PPC (session #099). The Egypt request exposed a class
of defect, not one country's gap." The session found three more classes in the same incident and
extended nothing.

**Judgement: yes, this is a gap, and it is the session's largest process failure** — larger than the
stale index, because the index is one command away from fixed and these checks are the only thing
that will catch defect #4 when the tenth country is added.

### 4. Reachability from the entry points — **fails both entry points**

- `BRAIN_INDEX.md` is GENERATED. No rebuild was run: mtime 16:36, and the last commit touching
  `brain_state.json` is `e4af44a` at 16:58, before both Egypt commits [VERIFIED]. The OPEN WORK block
  renders `SPEC_READY` and a superseded ten-code plan.
- `MEMORY.md` line 24 still reads "Diez codigos EG0..EG9 (SUPP/SCVE/SALA/BEXP/GDDS/CHAR/RENT/STDY/
  GOVT/OTHR)" and "T1 inerte ya, T2 el momento vivo" — the spec, not the build. It does not mention
  that the config exists, the real ticket `INC-000016101`, the transports, the E2E proof, or the
  Indonesia near-miss. **Line 22 of the same file states the rule that line 24 violates**
  ("Guardar no es recuperar: si no se llega desde los DOS puntos de entrada, no existe").
- After a rebuild, the OPEN WORK block *would* render correctly — `next_action` in the store is
  excellent and already states the corrected plan including "OPCIONAL: tipo de pago R (medido cero
  trafico en 10 anos)". The fix is one command plus a MEMORY.md edit. That it was not run is the
  point.

### 5. Is `brain_state.json` stale? — **Yes, measurably, and it was already stale before this session**

`brain_state.json`: 520 claims, max id 521, incident status `SPEC_READY`, no `ticket_number`, no
`build_record`, no `e2e_test_d01`, `related_claims` stops at 496. Source stores: 526 claims, max id
527, status `TESTED_IN_D01_BOTH_HALVES_PROVEN`. Six claims (522-527) are missing from the aggregate.

Note for fairness: commit `7a652af` at 17:00 added claims after the last rebuild at 16:58, so claims
522-523 were already orphaned when this session's Egypt work began. The session inherited a stale
aggregate and then widened the gap by four claims and one incident rewrite.

---

## Closure Math

- PMO items before: **65 declared** in the header (`0 Blocking | 29 High | 36 Backlog`), last
  reconciled Session #082, while the body enumerates items through **H100** [VERIFIED]. The header
  arithmetic does not reconcile with the body; the Phase 0.75 gate **fails on arithmetic alone**.
- Added this session to PMO: **0**
- Closed this session in PMO: **0**
- Items actually created by the work, unrecorded: **4** (split the transport before release; remove
  key `350ID USTRD O01` from `D01K9B0FXF`; add pay-type R rows; confirm the 5 reasons with Mathewos
  Mehari + CitiService Egypt).
- Items actually closed by the work, unrecorded in PMO: **2** (the Ustrd-exit unknown, closed by
  claim 525; the rendering proof, closed by claim 527).

**Net: RED.** Not because the session shipped nothing — it shipped the most consequential proof in
the incident's life — but because the ledger recorded neither side, so from PMO's point of view the
session did not happen.

---

## Zombie items (>10 sessions old)

No zombie review was performed this session. PMO's own header dates its last reconciliation to
Session #082 — **19 sessions** ago. H66-H70 (2026-06-21), H71-H80 (2026-06-22), H84-H90 (2026-06-23)
have all crossed the 10-session threshold without a ship/kill/rejustify decision. This audit does not
adjudicate them; it records that Principle 6 was not exercised and the backlog is unbounded.

---

## Ungrounded artifacts

| Artifact | Type | Missing |
|---|---|---|
| `Zagentexecution/tasks/2026_08_19_egypt_ppc_d01_test/UNES_SOGE_03INTUSD_20260819_EG1.xml` | evidence file | `task_details.md`, `learning_summary.md` (CLAUDE.md §File Organization); no provenance note — the incident says the run wrote no file to `\\hq-sapitf\SWIFT$\D01\INPUT`, so *how* these 2,153 bytes reached the repo (REGUT read? medium display download?) is nowhere recorded. A future auditor cannot reproduce the capture. |
| `…_pretty.xml` | derived | Same folder, same gap. No statement that it is a reformat of the sibling and not a second observation. |

The analysis itself is **not** ungrounded — the CM003/CM004 prediction is a textbook pre-declared
hypothesis and is the session's best work. The artifact folder is what lacks grounding paperwork.

---

## Rule violations (project rules, cited)

| Rule | Violation | Evidence |
|---|---|---|
| `feedback_knowledge_must_be_reachable_from_the_entry_points` (s099) | Neither entry point reflects the work | `BRAIN_INDEX.md:93` = `SPEC_READY`; `MEMORY.md:24` = ten-code spec |
| CLAUDE.md §Companion & Report Quality Rules #1 (cross-reference) | Companion + domain doc not swept for the changed entity | `inc_egypt_ppc_configuration.html` mtime Aug 17, 0 hits for `INC-000016101`/`D01K9B0FX`, still says `unproven` |
| `feedback_artifact_hierarchy_brain_companion_word` | Layer 1 updated, layers 2-3 untouched | Only `claims.json` + `incidents.json` changed |
| `feedback_retro_to_pmo_bridge` (CP-001-derived) | 4 new commitments never formalized | PMO_BRAIN last commit `5445a17` 16:33, pre-Egypt |
| "by the 2nd occurrence you owe a procedure + a recurring check" | 3 defect classes, 0 checks, 0 rules, 0 procedure | `ppc_country_consistency_check.py` mtime Aug 18 09:46; `feedback_rules.json` untouched |
| `feedback_never_leave_ideas_as_comments` | The Indonesia class-of-defect and the R-traffic measurement live as prose inside records | claim 526 tail; `deviations_from_spec[n=3]` |
| Durability ("on origin") | 2 commits unpushed | `git branch -vv` → `ahead 2` |
| Preflight close gate | 2 FAILs at close time | 1 uncommitted file `Zagentexecution/sap_data_extraction/backup_location.json` [VERIFIED via `git status --porcelain`]; SYM 1 unaudited plan 062 / 25 un-planned retros |

**Not violated, and worth stating explicitly:** BROADCAST-007 / ABAP change discipline. Every SAP
write in this session (SM30 config, FB60, F110) was performed by `JP_LOPEZ` as an authorized human
in D01; the agent read via RFC and wrote nothing. `git status` shows no deploy script ran. This is
the discipline working as designed.

---

## Claims that failed verification

1. **Claim 526 vs `incidents.json`** — claim asserts a D01 state (`separator BORRADO`, code `SALA`
   present) that the incident records as repaired hours earlier. One of the two stores is wrong;
   given `config_verified_d01` was re-read from D01, the claim is the wrong one.
2. **Claim 527 `resolution_notes` vs claim 527 body** — "Deja abierta SOLO la prueba del bloqueo"
   against "LA MITAD DE CAPTURA TAMBIEN QUEDA PROBADA".
3. **Claims 525 & 527 `resolution_notes`** — both assert they close "el 'one thing still unproven'
   de companions/inc_egypt_ppc_configuration.html seccion 5". The companion was never edited and
   still contains `unproven`. The claim describes a state of the world it did not create.
4. **`incidents.json` `closed_followups[0]`** — still ends "sigue pendiente el F110 real como prueba
   del fichero". The F110 ran at 16:45. Stale within the same record that documents the run.
5. **`incidents.json` internal disagreement on the P-type fixed value** — `build_record` says
   `FIXED_VAL 'Salary (Compensation of employees)'` while `config_verified_d01` says
   `'Salary payment'` and lists `/Salary payment/<SGTXT> (23)`. Claim 524 uses the first. Nothing
   says which is the current D01 value; the next session must re-read D01 to find out.

---

## What a new CTO would kill

- **`knowledge_reachability_check.py` in its current form.** It exits 0 while the index it is
  guarding is three hours stale and materially misleading. It checks that a string is present, not
  that it is current — which is exactly the pattern this same session documented in SAP as claim 496
  ("el control prueba presencia, no correccion"). The session found the anti-pattern in someone
  else's system and shipped it in its own. Either add "index mtime ≥ store mtime **and** the index
  contains each live incident's current `status` string", or stop running it and stop taking comfort
  from its exit 0.
- **The PMO_BRAIN header.** A counter that says 65 while the body enumerates to H100, last
  reconciled 19 sessions ago, is not a ledger — it is decoration that makes closure math impossible.
  Either derive the counts from the body programmatically or delete the counter.
- **The two-commit close without a rebuild.** `rebuild_all.py` is the step that converts private
  work into project state. Closing before it is the difference between having done the work and
  having shipped it.

---

## Decisions deferred without reason

- Whether claim 526 gets corrected or superseded. It is wrong now; nothing in the record says who
  fixes it or when.
- Whether the three new defect classes become checks. Not deferred with a reason — simply not
  addressed.
- Whether `350ID USTRD O01` is removed from `D01K9B0FXF` by SE10 or left with a re-read before
  release. The incident presents both and recommends the first; no owner, no date.
- Whether the last hop (file landing in `\\hq-sapitf\SWIFT$\D01\INPUT`) is in scope before
  2026-09-05. Honestly flagged as untested, then dropped.

---

## Blockers — MUST be fixed before session close

1. **Run `python brain_v2/rebuild_all.py`.** `brain_state.json` is missing claims 522-527 and carries
   `INC-EGYPT-PPC = SPEC_READY`. Nothing downstream is trustworthy until this runs.
2. **Verify `BRAIN_INDEX.md` OPEN WORK after the rebuild** renders the new status and the corrected
   `next_action` (build exists / 5 codes / split the transport / R optional). If it does not, the
   generator — not the record — is the bug.
3. **Fix claim 526.** It states a D01 state that was repaired the same day (`separator BORRADO`,
   `SALA`). Either amend in place with a dated correction or supersede it with a link, per CP-001.
4. **Fix claim 527's `resolution_notes`** — it contradicts its own body.
5. **Update `MEMORY.md` line 24** to the build reality (config built in D01 under `INC-000016101`,
   transports `D01K9B0FXE/FXF` unreleased, E2E proven both halves 2026-08-19, remaining work is the
   transport split + business confirmation). MEMORY.md is the second mandatory entry point and line
   22 of that same file is the rule requiring it.
6. **Update `companions/inc_egypt_ppc_configuration.html`** — it is the artifact the incident's
   `next_action` points at, and it still describes ten codes, two hypothetical transports, and an
   unproven mechanism. Also sweep `knowledge/domains/Procurement/p2p_purpose_of_payment_e2e.md`.
7. **Push.** `master` is ahead of `origin/master` by 2. The E2E proof is on one disk.
8. **Commit or revert** `Zagentexecution/sap_data_extraction/backup_location.json` (preflight FAIL).

## Conditions — should fix, and the reason each matters

1. **Extend `ppc_country_consistency_check.py`** with check E (SEPARATOR row with empty
   `PPC_VALUE`) and check F (`T015L-ZWCK1` must have exactly one space between code and narrative).
   Both are static, both run against the Gold DB, both would have caught a defect found by hand
   today. Check G (whole-table D01-vs-P01 drift + transport key ownership) is the expensive one —
   scope it, or record explicitly why not.
2. **Add one feedback rule.** Candidate, stated in the session's own words: *maintaining one country
   in SM30 can capture a neighbouring country's key in the transport; the diff that sees it is the
   whole-table D01-vs-P01 diff, not the diff of the keys you meant to touch.* Zero rules were added
   this session; this one is already written, it just is not in `feedback_rules.json`.
3. **Promote the R-traffic measurement to a claim.** "Six countries' R rows have never fired in ten
   years; PPC pay-type coverage is defensive symmetry, not measured traffic" is a class-level fact
   sitting inside one deviation entry.
4. **Split claim 527's block half into a TIER_2 claim** with a typed `user_report` evidence row, or
   add such a row to 527 and downgrade. The prose caveat is good; the schema does not carry it.
5. **Run the negative control** — one FB60 to a non-PPC-country vendor, or to an EG vendor with the
   `PPC_DESCR` row temporarily absent — to isolate u917 as the cause rather than infer it from
   message uniqueness. One posting; it converts an inference into a measurement before 2026-09-05.
6. **Add `task_details.md` + `learning_summary.md` to the task folder**, including how the XML was
   captured given no file was written to the SWIFT directory.
7. **Reconcile PMO_BRAIN** — the 4 new items, the 2 closures, and the header arithmetic.

---

## Recommended retro content — the 5 findings worth preserving

1. **A prediction that matched character-for-character is the strongest evidence this project has
   produced.** Simulating CM003/CM004 over the read config, writing the expected `<Ustrd>` down
   *first*, then generating the file and finding it identical — that is falsifiable engineering, and
   it is the reason the "zero ABAP to add a country" conclusion is safe to act on. Preserve the
   method, not just the result: read config → simulate the algorithm → record the prediction →
   execute → diff.
2. **One file proved two countries.** `DbtrAgt BIC SOGEFRPP` selected the `_FR` class and
   `CdtrAgt BIC AGRIEGCX` selected the `LAND1='EG'` rows in the same document — the two-layer
   dispatch is proven by one artifact, with no country literal anywhere. This is the transferable
   fact for country #11.
3. **Invisible whitespace is a defect class, and it bit twice in one day.** Empty `PPC_VALUE`
   separators and a double space in `T015L-ZWCK1` — neither visible in SM30, both only findable by
   reading the field raw. Plus the storage fact behind it: `PPC_VALUE` is `CHAR(60)`, so a *trailing*
   space cannot be stored at all while a *leading* one survives. This is the finding that most
   deserves to become executable code rather than prose.
4. **Maintaining one country in SM30 can enrol a neighbour's key in your transport, and only a
   whole-table diff sees it.** Indonesia's separator was blanked in D01 and its key travelled inside
   the Egypt transport. Caught by diffing all three tables D01-vs-P01 in full, not by diffing the
   keys the change intended to touch. Generalize beyond PPC: this applies to any SM30-maintained
   cross-country table.
5. **A presence check is not a currency check — we built the same weakness we diagnosed.** Claim 496
   says u917 proves the field is non-empty, not that the code is right. `knowledge_reachability_
   check.py` proves the incident id appears in the index, not that the index says anything true. The
   gate passed at 19:04 while the index told the next session to build something already built.

### Where the main agent is likely to have overstated its performance

- **"Promoted to brain."** Four claims and one incident were written to two source JSON files. The
  brain — `brain_state.json`, the thing sessions load — does not contain them. Written ≠ promoted.
- **"Closes the last unproven piece."** Claims 525 and 527 both say they close section 5 of the
  companion. The companion still says `unproven`. Closed in the claim's own opinion, not in the
  artifact a reader would open.
- **"Both halves proven."** The render half is proven by a file in the repo. The block half is a
  second-hand screen report plus a config read, with no typed evidence and no negative control. The
  status string `TESTED_IN_D01_BOTH_HALVES_PROVEN` grants both halves the same word.

### Where it is likely to have understated its performance

- **The self-correction on pay type R.** Going from CRITICAL to MEDIUM by measuring 3.7M REGUH lines,
  writing "corrige mi propia valoracion inicial de CRITICO" into the permanent record, and stating
  the limit of the measurement ("la nomina de El Cairo … no investigado") is exactly CP-003 working.
  Most sessions quietly drop a wrong severity; this one recorded it. It belongs in the retro as a
  positive, not buried in a deviation entry.
- **The near-miss catch itself.** Nobody asked about Indonesia. Diffing the whole table rather than
  the intended keys is what found a change that would have silently degraded 921 live payment lines.
  That is the highest-value ten minutes of the session and it reads, in the record, like a footnote.
- **The discipline.** Every SAP write was done by the authorized human; the agent read and reasoned.
  After INC-CLASS-LOSS that is not a given, and it should be stated.

---

## Recommended next-session focus (ranked by business value / effort)

1. **Close the loop the deadline depends on** — split `D01K9B0FXF` into T1 (T015L + `YTFI_PPC_TAG`,
   inert, releasable now) and T2 (`YTFI_PPC_STRUC`, 1-2 days before 2026-09-05), and remove
   `350ID USTRD O01`. 17 days remain. This is the only item with a hard external date.
2. **Mechanize the three defect classes** into `ppc_country_consistency_check.py` (E and F at
   minimum) and add the one feedback rule. Cheap, and it is what makes country #11 safe.
3. **Fix the currency gap in the reachability gate** — assert the index reflects each live
   incident's current status, not merely its id. Without it, this audit's headline finding recurs
   at the next close.

---

**Auditor's closing note.** The SAP engineering in this session is the strongest evidence chain in
the incident's file: a prediction, an execution, a byte-identical match, and a near-miss caught by
diffing more than was asked. None of it is visible from the two files the next session is ordered to
read. That gap, not the analysis, is what this audit fails.
