---
name: PBC encumbrance — the rules that decide, read from production source
description: What a post commits, how a vacancy is treated, and against which period. Read from ZCL_IM__UNESCO_ENCUMB in P01 (1,296 lines) — these decisions are OURS, not SAP's, and several live as hard-coded constants no configuration analysis can see.
type: project
module: PA-PM-PB
capability_domain: PBC
status: PRODUCTIVE
claims: [358, 388, 397, 398]
---

# PBC encumbrance — the rules that actually decide

**Source of truth:** `extracted_sap_p01/ZPBC/ZCL_IM__UNESCO_ENCUMB.abap` — 1,296 lines read
from **P01**, not D01. That distinction is not pedantry here: 37 of the 114 ZPBC objects in
D01 never reached production ([[claim 397]]).

**Why this document exists.** PBC drives the largest write path in the installation —
`FMRESERV`, 6.95M change documents. The AS-DESIGNED half of it **cannot be taken from SAP
standard documentation**, because the standard is not what decides: the engine is
*overridden* by BAdI implementations, not extended.

---

## Rule 1 — a post commits only while it is VACANT

Stated in the code itself:

> `"UNESCO requires Precommitment ONLY for vacant and integrated positions"`

`DO_HANDLE_VACANCY` walks the requirement set and:

| object | condition | effect |
|---|---|---|
| position (`OTYPE_S`) | `HROBJECT_DP` is **not** empty → the post is **occupied** | requirement **dropped** |
| person (`OTYPE_P`) | its `HROBJECT_DP` points at a position | that pointer is **cleared** |

So an **occupied** post generates no commitment of its own: the commitment comes from the
**person**. That is what prevents the post and its holder being counted twice.

**A discrepancy worth knowing.** The comment block says the pointer deletion is
`"deactivated:"` because *"deleting P→S pointers would lead to incorrect PCS-documents"* —
but the code below it **does** clear the pointer for `OTYPE_P`. Comment and code disagree.
Treat the code as authoritative and the comment as stale, and confirm before relying on
either.

---

## Rule 2 — commitments are pro-rated by date intersection

`ADJUST_REQ_WITH_VALIDITY` resolves a requirement against a funding validity window in
three cases:

| case | outcome |
|---|---|
| no overlap (`new.BEGDA > req.ENDDA` or `new.ENDDA < req.BEGDA`) | **skipped** entirely |
| validity fully contains the requirement | **adjusted**, kept whole |
| partial overlap | **split** — the portion outside is skipped, the portion inside is kept |

On a split, the amount is re-derived by
`ZCL_HRFPM_REQUIREMENT_SERVICES=>ADJUST_COST_DIST_AMOUNT`, so the money follows the day
range rather than the record. A commitment is therefore never all-or-nothing at a period
boundary.

---

## Rule 3 — the biennium, and the transport that changed its meaning

`DET_BIENNIUM_FROM_ENC_IV` derives the *relevant biennium* from the encumbrance interval,
under two assertions that are worth reading as **system invariants**:

```abap
ASSERT IS_ENC_IV-ENDDA+4(4) = '1231'.   "the interval must end on 31 December
ASSERT LV_YEAR_SPAN GE 1.               "was: BETWEEN 1 AND 2
```

The biennium **begins** with the encumbrance period. Its **end** was changed by transport
`D01K9B04Z3`:

| | formula |
|---|---|
| before | `endda(4) = enc_iv.endda(4) − 1` — one year *before* the interval end |
| now | `endda(4) = begda(4) + 1` — two years *from the start* |

**These agree only while the interval is exactly two years.** The same transport relaxed the
span assertion from `BETWEEN 1 AND 2` to `GE 1`, which permits longer intervals — so the two
edits are one change, and the formula had to move with the assertion. This is the
period/biennium rule that the capability model previously recorded as unknown.

---

## Rule 4 — a business rule living as a hard-coded constant

```abap
"until a configuration for the enddate determination rules
"is available, use hard-coded values
********Quasi-config *****************************
*{   REPLACE        D01K9B04Y9
*\      mv_extension_years = 1.
      "as per a change request from Spring 2019
      " Temporary positions need to be financed until end of contract date:
      " and that may exceed three years ==> according to communication with
      " business no contract end date will exceed 3 years from today
      " so a limit of 10 should be sufficient
      MV_EXTENSION_YEARS = 10.
*}   REPLACE
```

**How far into the future a temporary position is financed is a business decision, and it is
a constant in a class.** No configuration analysis can find it, and no table records it. The
author labelled it *quasi-config* and said why: the configuration for end-date determination
does not exist.

Note the reasoning has an expiry built in — *"no contract end date will exceed 3 years from
today"* — and the limit was set to 10 for headroom. If that assumption ever stops holding,
nothing in the system will say so.

A second transport, `D01K9B050N`, extends the same theme: *"temporary positions need to be
financed until 'highdate' regardless of their business area"*.

---

## Rule 5 — the scenario is fixed

```abap
METHOD GET_SCENARIO.
  RV_SCENARIO = C_SCENARIO_STAT.
ENDMETHOD.
```

The scenario is not derived from anything. It always returns the same constant.

---

## What is still in production that should not be

- **`BREAK-POINT ID Z_ENCUMB_PROTO`** appears in the decision methods, and the checkpoint
  group `Z_ENCUMB_PROTO` is a real object in the package. A checkpoint group inside the code
  that computes commitments is a live switch, not a comment.
- `ZIF_ENCUMB_HANDLING~GET_INSTANCE` is commented `"prototype`.
- Across the 25 production objects, algorithm A9 counts **120 leftover artifacts**.

Naming these is not a style complaint. The word *prototype* sits on the largest write path in
the installation.

---

## How this was obtained, and how to repeat it

1. `Zagentexecution/sap_data_extraction/scripts/extract_p01_source.py ZPBC` — production
   source, read-only. Classes need the generated pool plus one include per method; the pool
   alone is 25 lines of skeleton and would report this class as empty.
2. `process_mining/extract_business_rules.py` — **algorithm A9**, which finds the
   quasi-config, the hard constants with their reasoning, the intent comments, the
   modification blocks with their transports, the standard interfaces overridden, and the
   leftovers.

Neither step is specific to PBC or to this tenant.

**Limit, stated plainly:** A9 reads text. A construct it does not recognise is not reported,
so absence in its output is never evidence. Every finding carries a line number so it can be
confirmed against the source — and every rule above was confirmed that way before being
written here.
