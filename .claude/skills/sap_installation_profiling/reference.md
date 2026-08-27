# sap_installation_profiling — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

## The catalogue must not lie about itself

The registry says which algorithms exist. That claim has to be **derived from disk**, never
written by hand, and this is not a hypothetical:

> `C3_static_edge_extraction` was reported **PROPOSED** — an idea with no implementation —
> while `parse_abap_edges.py` sat in the repository, running. One entry in its list of
> tools was a sentence, `"brain_v2 graph build"`, instead of a path. The binding check
> requires every declared tool to exist on disk; a sentence exists nowhere, so the check
> went false and a BUILT algorithm was published as unbuilt.

Correcting that entry was not the fix. Searching for others found the **same prose copied
into the asset registry** — a second store, same defect, nobody checking. A defect that
appears twice is structural, so it became a gate: `validate_paths.py` now checks all 147
path-typed fields across five stores on every rebuild.

**The rule:** a field that is declared to hold a path holds a path. Prose belongs in a
field named for prose. A path field carrying a sentence does not fail loudly — it makes
every check over it *silently wrong*, which is worse than a gap, because a gap is visible.

---

## Write-path discovery — the generic enrichment (algorithm A8)

**Use it whenever a domain holds tables with no maintenance transaction.** Listing a
domain's tables is not understanding it; the WRITE PATH is the behaviour. And the field
that should answer — the transaction code on the change document — is frequently **empty**:
in this tenant, 93% of the largest object class's changes carry none.

**An empty transaction code is a POINTER, not a gap.** It usually means the write arrived
through a **BAPI or RFC whose interface design never set one**. Reading it as "batch" throws
away the interface; reading it correctly hands you straight to F1 and F2.

**The join** is two streams every SAP tenant already produces, on `(user, day, hour)`:

| | |
|---|---|
| change stream | who changed WHICH object, when |
| execution stream | who ran WHICH program, when |

Nothing about it is SAP-specific. The same shape answers *which program sends this IDoc
type*, *which job produces this file*, *which process touches this interface*.

### Three scorings, two of them wrong — do not repeat them

| attempt | what happened |
|---|---|
| raw coincidence | the RFC dispatcher runs constantly, so it coincides with everything. It named a **spool artifact** as the writer of the largest object class |
| **lift** `P(ran∣changed)/P(ran)` | fixes that and **inverts** the error. It rewards RARITY — so it ranked the real engine below noise and filtered it out. An engine runs on 91 of 108 days, giving a base rate of 0.84 and a lift that cannot exceed 1.19 *however perfect the coincidence*. **An engine is not rare; running whenever the thing changes is what makes it the engine** |
| **φ coefficient** over the slot contingency table | symmetric — how much of the change activity a program covers AND how specific it is — correcting for both base rates. A program present in every slot has `d=0`, its margin collapses, and it scores nothing |

Two further guards, both from defects that happened: **small denominators** (a program that
ran one day scored lift 27 on a single coincidence — the same defect as D6's z-score over a
two-month baseline), and **volume weighting** (a user with 4 changes and one with 5,640,493
are not equal witnesses).

### Exclusivity — the answer is an assignment, not N rankings

A program associated with forty classes has explained none of them. After scoring, each
program is counted across classes; one claimed broadly is reported **AMBIGUOUS**, and a
dispatcher is labelled as **evidence of an interface**, never as the writer. Attributing the
same writer to every table is the failure this constraint exists to prevent.

**Output is a ranked HYPOTHESIS with its evidence and a verdict, for a human to confirm.**
Co-occurrence is not causation, and two programs in the same chain cannot be separated below
the shared time granularity.

---

## Orchestration — a trigger reports evidence, the cycle holds the order

**A trigger must never name a script to run.** Naming one is a decision taken on demand, and
on-demand decisions are precisely the ones that stop being taken — which is the hole the
trigger mechanism exists to close, so committing it there defeats the mechanism. It also
scatters the ordering knowledge across every call site, where it rots quietly: nine of ten
triggers here named individual scripts, and not one of them knew that write-path attribution
must precede boundary discovery.

A trigger reports **evidence** and a **response class**:

| class | meaning |
|---|---|
| `CYCLE` | the analysis cycle runs it, in dependency order |
| `EXTRACTION` | needs a connection — deliberately outside the cycle, because it depends on a VPN and on someone deciding it is time |
| `AUTHORING` | a human writes it; no algorithm produces a domain doc or a capability row |

**Adding an algorithm means placing it in the chain**, with a stated reason for its level —
not remembering to call it. A8 sits at L2, ahead of boundary discovery, because classifying a
class as INTERFACE names the calling function modules, and those functions are what the
satellite derivation groups on.

**If the answer to a trigger is "run X", the real answer is "X belongs in the cycle".**

---

## Prose identifies, the log confirms — prose alone is worth nothing

**An analysis written up as prose is not knowledge the system can use.** It reads well, it is
usually correct, and no algorithm can reach it — so the next question re-derives it, and the
two answers drift with nothing able to notice.

The measured instance: the integration map classifies **48 flows into 8 channels** — RFC,
IDoc, middleware, file jobs, batch input, LSMW, DBCON, HTTP/SOAP — records that Coupa arrives
as a **file processed by a job**, and that TULIP and UNESDIR come over a **direct database
connection and fail 93% of the time**. All in markdown tables. The consequence:
`interface_boundary.json` contained the string "channel" **zero times**, and A8 was about to
re-derive the whole taxonomy from the audit log while the answer sat in a document nobody
could query.

**The contract:**

| side | role |
|---|---|
| **DECLARED** — `brain_v2/integration_channels.json` | what we documented. It **identifies** what to look for |
| **DERIVED** — A8, from the logs | what the system actually does. It **confirms** |

They are kept in **separate fields** with an explicit verdict, and this matters more than it
looks: the first version appended the declared channel beside the derived ones, which
quietly promotes a sentence in a table to the standing of a measurement and destroys the
comparison that makes either side worth having.

| verdict | meaning |
|---|---|
| `CONFIRMED` | documented and visible in the logs — two independent sources agreeing |
| `UNCONFIRMED PROSE` | documented, not visible. Either the documentation is stale, the flow stopped, or the derivation is missing it — one of the three, and finding out which is the work |
| `UNDECLARED` | visible in the logs, absent from the map. Something writes off-map |

**Before deriving anything, check whether it was already analysed and left as prose.**
`audit_prose_classifications.py` answers that from disk. A document whose table is genuinely
illustrative declares itself with `<!-- narrative-only -->`; the point is that the choice
becomes deliberate rather than accidental.

---

## Prose identifies; the derivation confirms

**A documented finding is a hypothesis to verify, never evidence to add.** Use the prose to
know what to look for, then confirm it against derived data and report the verdict —
**CONFIRMED · CONTRADICTED · UNVERIFIED**. Merging a documented claim into a derived result
set launders a document into a measurement, and afterwards the two cannot be told apart.

**Before deriving anything, check whether it was already analysed.** This cost real work:
the write-channel taxonomy — RFC, IDoc, middleware, FILE, batch input, LSMW, DBCON,
HTTP/SOAP — was fully analysed and written into `integration_map_complete.md` **as markdown
tables**. The measurable consequence: `interface_boundary.json` contains the word "channel"
**zero times**, and A8 was about to re-derive the same taxonomy from the audit log while the
answer sat in a document nobody could query. Two answers to one question, drifting apart,
with nothing able to notice.

`brain_v2/build_channel_registry.py` parses it — it does not re-analyse it — keyed on the
artifact that carries the channel, because that is the key the attribution algorithm holds.

**CONTRADICTED is the valuable verdict.** It means the documentation and the running system
disagree, which before could not even be expressed.

### The write channels, and why a label is not enough

Beyond a person in a transaction, a change can arrive through: an **interface** (BAPI/RFC —
and `PARAMX` names the calling host and destination, which *is* the satellite); a **job**
firing a program; a program reading a **file** in a directory; a **batch-input session**
replayed; a **DBCON** link to a declared external database; or an inbound **web service**.

Two of those hide in plain sight:

- **BATCH INPUT writes as if a person typed it.** A replayed session drives real screens, so
  it can carry a transaction code and pass for a dialog change. It must be detected
  explicitly, from the session processors (`RSBDC*`, `SAPMSBDC*`). Its detail is in
  `APQI`/`APQD`.
- **WEB SERVICE cannot be seen in this log at all.** An inbound call is processed by the
  ICF/SRT runtime, not by an ABAP program, so it never reaches `SLGREPNA`. Matching `SRT_`
  looks like it works and detects only **housekeeping** — CCMS collection and queue cleanup,
  which run constantly. That scored a web-service channel at 0.99 that does not exist: the
  dispatcher trap in SOAP clothing. **A near-certain confidence built on plumbing is worse
  than no detection, because it reads as proof.** The honest output is
  `WEBSERVICE_UNDETECTABLE` with the reason — never silence, because silence reads as
  absence, and absence in the wrong log is not absence in the system.

These compose. Bank statements and postings originate in COUPA, which writes a **file** into
a folder; a scheduled **job** picks it up; the **program** posts. A single-label
classification calls that "PROGRAM" and throws away three links and the entire external
origin. So channels are reported as a **chain**, each link with its own evidence.

---

## The rules that decide are often not in configuration

**A domain can look fully configured and still behave in a way nobody documented.** The
decisions frequently live in a custom BAdI implementation — as a hard-coded constant, a
branch condition, or a comment stating an intent no table records. A config-frontier
analysis cannot see any of them.

The case that produced algorithm **A9**, read from production source:

```abap
"until a configuration for the enddate determination rules
"is available, use hard-coded values
********Quasi-config *****************************
*{   REPLACE        D01K9B04Y9
*\      mv_extension_years = 1.
      MV_EXTENSION_YEARS = 10.
*}   REPLACE
```

How far ahead a temporary position is financed — a business decision — living as a constant,
raised from 1 by a named transport, with the reasoning in a comment **and an expiry built
into that reasoning**. The same read recovered the biennium rule the capability model had
recorded as unknown.

A9 extracts six things from any ABAP corpus: **QUASI_CONFIG** (a literal the author flagged
as standing in for missing configuration) · **HARD_CONSTANT** with the comment that explains
it · **INTENT** (a comment stating a requirement) · **MODIFICATION** (`*{ REPLACE
<transport>` — what changed and under which transport) · **OVERRIDE** (which standard
interface this code takes over) · **LEFTOVER** (debug and prototype artifacts still in
production).

**Its limit is the important part:** A9 reads text. A construct it does not recognise is
simply not reported, so **absence in its output is never evidence** — which is the most
dangerous way to misuse it, because the output looks like an inventory. Every finding carries
a line number so it can be confirmed against the source, and it must be.

### Knowledge is a record, not a paragraph

A finding written into a document — or into the body of a claim — cannot be queried, cannot
be diffed next month, and cannot go stale visibly. Everything discovered goes into a
**structured store keyed on something an algorithm holds**, with the document as its human
companion, never as its home:

| finding | its record |
|---|---|
| what writes each object class, through which channel | `brain_v2/change_attribution.json` |
| every inbound and outbound path | `brain_v2/interface_inventory.json` |
| rules living in code | `brain_v2/business_rules.json` |
| what CORRECT means per flow, as checkable rules | `brain_v2/normative_models/` |

**A rule with no way to be violated is prose.** Every normative rule carries
`violation_looks_like` and `checkable_against` — that is what makes it a conformance
reference rather than a description.

---

## Anti-methods — each of these cost real errors in instance #1

| | why it looks like evidence, and is not |
|---|---|
| **Absence in a derived index** | Absence in an execution map or an extract is a FLOOR, never an inventory. It yields *not evidenced*, never *not used*. Cost: five productive modules reported as not implemented. |
| **Substring name matching** | Matching a module name inside free text. Two-letter modules are catastrophic — `CO` matched 337 claims. Noise presented as coverage reads as linkage. |
| **Suppressing a generic error** | `TABLE_WITHOUT_DATA` swallowed as "empty is normal" was masking an invalid FIELD. Three extraction runs returned zero rows with no error. |
| **Answering from memory** | Component codes, table and field names are resolved from the system, never recalled. |
| **Comparing domain names raw** | Aliases are declared; use the resolver. This single defect appeared three times in one session. |
| **Trusting a regenerated artifact** | Always diff it against its predecessor. An inline `#` comment silently swallowed two dictionary entries and moved 70,766 executions between domains with no error. |

---

## Order of work, and what actually blocks

Phases 0–2 are the foundation and are cheap. Phase 3 is the long pole and its log
accumulator is time-critical — **start it on day one or lose that history forever**.
Phases 4–5 produce the finding that reframes everything for the client. Phase 6 is where
the commercial product lives, and it is blocked on the AS-DESIGNED baseline more than on
any amount of extraction.

**References:** `brain_v2/installation/` · `brain_v2/system_profile/` ·
`brain_v2/capability_model/` · `brain_v2/methods/` · `process_mining/` ·
`scripts/extraction/`. Replicability analysis (reference, not authority):
`projects/sapilot/analysis/07-inventario-replicabilidad.md`.
