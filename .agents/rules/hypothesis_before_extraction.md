# Rule: Hypothesis Before Extraction

**Author:** Session #036 (2026-04-05)
**Enforcement:** `agi_retro_agent` Principle 4 + `session_preflight.py` Check 10
**Severity:** Mandatory. Violations block session close.

---

## The Rule

> **No data extraction, companion build, or analysis may begin without a pre-declared hypothesis document.**

## Why

Session #035 extracted 3.45M rows of CO tables because they were on an old blocking list (B3, raised #005). No hypothesis was stated before extraction. Result: 3.45M rows sit in Gold DB with no analytical question pointed at them. Classic hoarding.

This rule converts "extraction as self-justifying activity" into "extraction as evidence-gathering for a stated question."

---

## What a hypothesis document contains

Minimum required fields:

```markdown
# Hypothesis: <short title>

**Task folder:** Zagentexecution/tasks/YYYY_MM_DD_<slug>/
**Raised by:** Session #NNN

## Question
What specific business or technical question does this extraction answer?

## Hypothesis (H1...Hn)
What do I expect to find? State expectations as falsifiable claims.

## Decision it enables
What will change based on the answer? If "nothing," STOP.

## Data scope
Which tables, which date range, which filters. No "let's see what's there."

## Expected shape
Approximate row count, approximate columns, expected distributions.

## Success criteria
How do I know the hypothesis was confirmed, refuted, or refined?

## Failure mode
What does a "bad" result look like? What do I do if extraction returns
nothing, returns 10x expected, or returns corrupted data?

## Out of scope
What I am NOT answering with this extraction.
```

---

## Examples

### Valid hypothesis (H13 BCM)
- Question: "Can we reproduce the 3,394 same-user batches finding from #027?"
- Hypothesis: "SELECT on BNK_BATCH_HEADER WHERE CRUSR=CHUSR will return 3,394 ± 5%"
- Decision: "Report to Finance Director; trigger workflow review"
- This is grounded. ✅

### Invalid hypothesis (a zombie extraction)
- Question: "Let's extract CO tables because they're on the blocking list."
- Hypothesis: none
- Decision: unclear
- This is hoarding. ❌

---

## Enforcement

### Pre-extraction (human responsibility)
- Task folder MUST contain `hypothesis.md` before any extraction script runs
- `session_preflight.py --mode start` Check 10 warns if task folders lack hypothesis

### Post-session (automated)
- `agi_retro_agent` scans the session's git diff for new extractions
- Each extracted table/file is cross-referenced with an existing `hypothesis.md`
- Ungrounded extractions are tagged `[UNGROUNDED]` in the retro audit
- **3 ungrounded artifacts in a single session = audit FAIL = session close blocked**

### Escalation
If the agent discovers that a required extraction has no possible hypothesis (e.g., pure exploratory discovery of an unknown system), it must produce a `discovery_charter.md` instead — which is a hypothesis document for hypothesis generation. Even "let's explore" needs a declared scope.

---

## Counter-examples (what this rule does NOT forbid)

- Enrichment of already-extracted tables (no new extraction)
- Re-running a proven extraction after a fix (the original hypothesis applies)
- Small exploratory queries against Gold DB (read-only, no new tables created)
- Brain rebuilds (no SAP data movement)

---

## Relationship to other rules

- Supersedes `feedback_extraction_scope.md` (more specific and enforceable)
- Supersedes `feedback_estimate_before_extract.md` (expands the scope check into a full hypothesis)
- Works with `feedback_data_scope_2024_2026.md` (scope is still 2024-2026, and now must be justified)

---

## Retirement condition

This rule retires when:
- Every extraction in the last 10 sessions has a hypothesis.md
- `agi_retro_agent` reports zero ungrounded artifacts for 5 consecutive sessions
- OR when a better enforcement mechanism replaces it

Until then: **mandatory.**
