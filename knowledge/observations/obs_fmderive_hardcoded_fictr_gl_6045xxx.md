# Observation: FMDERIVE hardcoded FICTR='UNESCO' for GL 0006045011 / 0007045011 / 0006045014

**Type:** Observation (not an incident)
**Discovered during:** INC-000005240 Session #050 subagent investigation (wrong-path analysis)
**Filed:** 2026-04-09 as part of INC-000005240 finalization triage
**Status:** Observation — not yet a confirmed defect; needs independent verification from UNESCO Finance/PSM if anyone cares to act on it

## Triage context

This observation was surfaced during an aborted analysis of INC-000005240. The subagent originally believed AL_JONATHAN's ticket was about **FM fund center (FISTL/FICTR)** being wrong, and traced the issue to `ZXFMDTU02_RPY`. The subagent was **wrong about the mechanism** — AL_JONATHAN's ticket is about `BSEG-XREF1` / `BSEG-XREF2` office tagging via `YRGGBS00` forms `UXR1` / `UXR2`, NOT about FM fund center derivation. The definitive INC-000005240 analysis is in [`knowledge/incidents/INC-000005240_xref_office_substitution.md`](../incidents/INC-000005240_xref_office_substitution.md).

**However, the FMDERIVE finding itself may be a real standalone observation worth documenting** — it describes a genuine hardcoded value in a production ABAP exit. Preserving it here as an observation (not linked to any ticket) lets UNESCO act on it independently if desired.

## The finding

Include `ZXFMDTU02_RPY.abap` (the `EXIT_SAPLFMDT_004` FI→FM derivation exit) contains a hardcoded assignment around line 94-101:

```abap
*SROCHA16112010
IF ( I_COBL-HKONT = '0006045011' OR
     I_COBL-HKONT = '0007045011' OR
     I_COBL-HKONT = '0006045014' )
    AND I_COBL-FISTL = SPACE AND I_COBL-FIKRS = 'UNES'.
  C_FMDERIVE-FUND_CENTER = 'UNESCO'.    " ← hardcoded line
  W_FLAG2 = 1.
ENDIF.
```

**What it does:** for any UNES posting where the FI line's HKONT is one of the three GL accounts above and the incoming FISTL is blank, the FMDERIVE exit force-assigns `FUND_CENTER = 'UNESCO'` (the generic HQ default), regardless of the posting user's office or any other context.

**Scope (from Gold DB fmifiit_full):** 187,514 rows historically tagged `FISTL='UNESCO'` on these 3 GLs in UNES. Going back to the SROCHA comment marker (2010-11-16), the hardcode has been in place for ~15 years.

**No user-office branch exists in the exit.** There is no `SELECT ... FROM usr05 WHERE PARID='Y_USERFO'`, no PA0001 lookup, no YXUSER bypass, no HR-org check. The exit unconditionally forces `UNESCO` for these three specific GLs.

## Is this actually a defect?

**Unknown — depends on UNESCO Finance/PSM intent.** The hardcode has been live for 15+ years without anyone flagging it as broken (until the subagent misdiagnosed INC-000005240). Possible interpretations:

1. **Intentional design** — UNESCO decided that these 3 specific GLs should ALWAYS attribute their fund-center expense to the generic `UNESCO` pool, regardless of the posting user's office. If true, this is working as intended and shouldn't be "fixed".

2. **Stale technical debt** — the hardcode was appropriate in 2010 but the business has since moved to per-office attribution. If true, the exit should be modernized.

3. **A real defect that has been silently absorbed** — field-office postings on these GLs have been mis-attributed to HQ for 15 years, and nobody has complained because the three GLs aren't material to anyone's reporting.

**Which of these is true requires a conversation with UNESCO Finance/PSM** — not something the incident-analyst can determine from code alone.

## Classification of GL 0006045011 / 0007045011 / 0006045014

These are likely personnel-cost GL accounts (the `60450*` / `70450*` ranges in UNESCO's chart of accounts are typically operational personnel costs). The `SROCHA16112010` comment suggests they were added during a 2010 configuration refresh for GEF (Global Environment Facility) / operational personnel cost processing.

## What to do with this observation

- **Nothing in the immediate term.** It's not AL_JONATHAN's issue; his ticket has its own root cause (§INC-000005240 v2).
- **If someone investigates FM fund-center attribution** on these GLs, this file is the starting point.
- **If UNESCO Finance/PSM runs a code review on ZXFMDTU02** (the FMDERIVE exit), flag this as "review for intent" — decide whether the hardcode is still desired or should be replaced with a per-user/per-office derivation.
- **Do NOT link this observation to INC-000005240** — they are different mechanisms.

## Related artifacts from Session #050 (wrong-path investigation)

The Session #050 subagent created these files while chasing this (wrong) mechanism. They remain on disk:

| File | Status |
|---|---|
| `Zagentexecution/incidents/INC-000005240_intake.json` | **Was rewritten** in the v2 investigation with the correct XREF1/XREF2 mapping. The old FISTL-based intake is gone. |
| `Zagentexecution/quality_checks/fmderive_hardcoded_fictr_check.py` | Useful quality check that counts violations of this hardcode. Not linked to any ticket. Can be kept as an observation-linked tool. |
| `brain_v2/annotations/annotations.json` — ZXFMDTU02_RPY, fmifiit_full, fund_centers annotations | Should be re-tagged to reference this observation file (`obs_fmderive_hardcoded_fictr_gl_6045xxx.md`), NOT INC-000005240. |
| `brain_v2/claims/claims.json` claims 27-30 | Tied to the FMDERIVE hypothesis. Should be re-tagged or marked `status: observation_only, unlinked_to_incident`. |
| `brain_v2/agi/known_unknowns.json` KU-024/025/026 | Mostly FMDERIVE-related. Should be reviewed individually — some may still apply to the FMDERIVE observation, some are obsolete. |
| `brain_v2/agi/data_quality_issues.json` DQ-017 | Reviewed — this may still apply as a real DQ finding on the FMDERIVE hardcode. Keep but link to this observation. |

## Anti-confusion note

**`HQ` and `UNESCO` are different strings with different semantics:**
- `'UNESCO'` = the FM **fund center** default used by FMDERIVE exit ZXFMDTU02_RPY on specific personnel GLs (this observation)
- `'HQ'` = the 2-char **office code** written to `BSEG-XREF1`/`BSEG-XREF2` by YRGGBS00 forms UXR1/UXR2 based on the posting user's `USR05.Y_USERFO` (INC-000005240)

Do NOT conflate them. They are different fields, different tables, different exits, different mechanisms.
