---
name: DOMAIN × CAPABILITY strategy — where the product actually is, and where nobody else is
description: Capabilities classified by domain, redundancy exposed, the Public Sector thesis stated with evidence, and the trigger model that makes the loop fire on accumulation instead of on someone remembering. Created s097.
type: project
---

# Domain × capability — the strategy, measured

Three questions this answers, none of which a tool list can:

1. Where is our capability **concentrated**, and does that match where the system's
   activity actually is?
2. What is **redundant** — the same capability built twice, or effort spent where it
   does not pay?
3. What is the **differentiator** — the thing no other vendor covers?

---

## 1. The coverage inversion — effort does not follow importance

Measured: assets per domain against actual execution volume.

| domain | execs | docs | companions | capability cells | verdict |
|---|---:|---:|---:|---:|---|
| **PS** | **1,611,381** | **0** | **0** | 4/11 | the busiest business domain in the tenant, and it is **undocumented** |
| Integration | 1,330,675 | 0 | 3 | 5/11 | cross-cutting; documented as a map, not a domain |
| FI | 418,050 | 6 | 1 | 8/11 | proportionate |
| HCM | 270,267 | 3 | 0 | 6/11 | thin for the volume |
| BusinessPartner | 241,583 | 1 | 0 | 5/11 | thin |
| HR_Workflows | 223,420 | 2 | 0 | 5/11 | thin |
| **PSM_FM** | 178,042 | 5 | 1 | **10/11** | the best-modelled domain we have |
| **Treasury_EBS** | 98,785 | **7** | **8** | 9/11 | **15 assets for 6% of PS's volume** |
| Procurement_P2P | 66,209 | 1 | 0 | 9/11 | modelled, not documented |
| CO | 26,836 | 1 | 0 | 2/11 | barely opened |
| Payment_BCM | 13,302 | 4 | 2 | 9/11 | well covered; low volume, high criticality — defensible |
| **PBC** | 9,115 | 1 | 0 | 4/11 | **68 users, the widest dialog audience in the tenant** |
| SD · PM · RE_FX · FI_AA | <3,500 | 1 each | 0 | 2–4/11 | newly opened |

**The finding:** Treasury_EBS carries fifteen assets for 98K executions while PS carries
zero documents for 1.6M. That is not a judgement about Treasury — it is evidence that
coverage grew by **where incidents happened**, not by where the work is.

**Volume is not the only priority signal** — Payment_BCM is low-volume and high-consequence,
and deserves its coverage. But PS at 1.6M executions with no documentation is indefensible
under any weighting.

---

## 2. Redundancy — three distinct kinds, all present

### Literal duplication
`p2p_conformance.py` exists in **two directories** (`process_mining/` and
`Zagentexecution/sap_data_extraction/scripts/`). One is authoritative; nobody knows which.

### Vocabulary duplication
The domain registry holds **`Payment` and `BCM` as separate entries** that both canonicalise
to `Payment_BCM`. Every crossing counts them twice.

### Generational duplication
`p01_master_data_sync` v1 through **v6**, plus `p01_massive_extractor` and `p01_raw_puller`
— eight superseded extractors, all still on disk, all shadowing `gold_refresh.py`. Classified
LEGACY by the coverage audit, which is honest, but they still confuse anyone reading the tree.

### The redundancy that is NOT redundancy
Multiple probes reading the same table for different purposes is **not** duplication — a
footprint probe and a domain extractor legitimately both touch `EKKO`. Redundancy is *the
same capability implemented twice*, not *the same data read twice*.

---

## 3. The Public Sector thesis — where nobody else is

**This is the product.**

Process-engineering and process-mining vendors ship content for the standard commercial
modules: order-to-cash, procure-to-pay, record-to-report, hire-to-retire. FI, CO, MM, SD.
Those are solved, competitive, and commoditised.

**There is no packaged process engineering for public-sector finance:**

| capability | what it is | vendor coverage |
|---|---|---|
| **BCS** — Budget Control System | budget structures, availability control, tolerance profiles | none |
| **FM** — Funds Management | funds, fund centres, commitment items, funded programs, the commitment chain | none |
| **PBC** — Position Budgeting and Control | staff posts committed against budget, the payroll-to-budget bridge | none |
| **GM** — Grants Management | sponsored programs and their eligibility rules | none |
| **PS ↔ FM** | projects consuming budget; WBS-to-fund derivation | none |
| **Earmarked funds** | reservations, commitments, the pre-posting chain | none |

**And this tenant runs exactly that stack, at scale:**

```
PSM_FM + PBC + PS + CO  =  1,825,374 executions
   PS      1,611,381    2.19M commitments, 13,976 projects, 59,749 WBS
   PSM_FM    178,042    67,500 funds · 787 fund centres · availability control ACTIVE
   CO         26,836
   PBC         9,115    68 users — the widest dialog audience measured anywhere here
   FMRESERV  6,415,467 change documents (the earmarked-funds chain)
```

**Why no commercial tool can do this**, stated precisely: process mining labels activities
from standard transaction and BAPI names. The public-sector chain here runs through
`Y_FMKU_0050_CREATE_WITH_COMMIT`, `RHRFPM_ENGINE_PNP`, `Y_BAPI_WBS_FINANCIAL_DATA_1`,
`Y_RFC_FMRP_RFFMEP1FX_FI_POST`, `Y_KBLP_PBC_OPEN_N`. A tool that does not know the
customer's Z/Y namespace sees unlabelled noise. **Our component chain resolves them
deterministically** — `PA-PM-PB`, `PSM-FM-BCS-BU` — because it asks SAP rather than
pattern-matching a name.

**The strategic consequence:** capability investment should be **deliberately asymmetric**.
FI/CO/MM need to be *competent* — they are table stakes and the competition is fierce.
BCS/FM/PBC/GM/PS-FM need to be *excellent*, because that is the only ground where being
best is achievable and defensible.

**Measured against that thesis, the current portfolio is misallocated:** PSM_FM is our
strongest domain (10/11 cells) — correct. But PBC has 4/11 and no companion, PS has 4/11
and no document, and Grants Management has never been examined (0 documents in the tenant,
but the *capability* to analyse grants does not exist either — and the next UN organisation
almost certainly uses GM).

---

## 4. The invariant: nothing in the log stays unrelated

> *The execution log is the reality that validates.* If an executed object is not related to
> a domain, a subdomain or a process, we do not understand the day-to-day.

The principle is right. Applying it naively is wrong: filing `RFCPING` under a business
domain would satisfy the letter and destroy the meaning. So explanation has **three tiers**,
and every executed object must land in exactly one:

| tier | what it is | s097 measurement |
|---|---|---|
| **BUSINESS** | a domain/subdomain that a person would recognise as work | ~4.6M execs |
| **TECHNICAL SUBSTRATE** | connectivity, session, monitoring, transaction control — real execution, legitimately non-business | 37 objects / **3,221,557** execs |
| **UNEXPLAINED** | the honest frontier | 3,819 objects / **1,329,986** execs |

Declaring the substrate tier moved the unexplained figure from **4,551,543 (40% of all
execution) to 1,329,986 (11.7%)**. Nothing was hidden — `RFCPING` alone is 1.4M executions
of connectivity checks. What changed is that the remaining number now *means* something and
can be worked down.

**The frontier is a health signal, and its TREND matters more than its size.** It shrinks
when the classifier learns; it grows when the system changes. A frontier that stops moving
means the discovery loop has stopped running.

---

## 5. The trigger model — the loop must fire on evidence, not on memory

The user's insight, and it is the correct one: **a capability should re-run when enough new
evidence has accumulated to change its answer** — not on a calendar, and not when someone
remembers.

### Accumulation triggers

| capability | fires when | why that threshold |
|---|---|---|
| classifier / `adaptive_discovery` | the frontier grows by >5%, **or** ≥50 objects appear that have never been classified | new objects mean new behaviour; below that it is noise |
| `probe_footprint` | a new company code / plant / sales org appears, **or** an activated business function changes, **or** quarterly | the footprint drifts silently and nothing else detects it |
| `extract_component_hierarchy` | any object resolves to a package absent from `tdevc` | the taxonomy has gained a branch |
| operating-model rebuild | ≥30 days of new audit history, **or** a new satellite host appears in the RFC stream | a month is the shortest window where the channel mix is stable |
| capability model | a domain crosses from NONE to evidence in any dimension | the matrix is stale the moment evidence exists that it does not reflect |
| interface map | a new destination, IDoc type, or scheduled job appears | **a new interface can re-open a settled domain question** |

### Maturity triggers — a score movement re-opens work

- **Ascent falls** below its previous value → new objects arrived that the chain cannot
  resolve → run the component extraction.
- **Coherence flags UNSUPPORTED** → the macro drifted from the detail → re-probe that module.
- **A blind spot appears** → a module is running that the model has never examined → open it.
- **Claim verification rate falls** → new claims are outpacing verification → stop
  extracting, start verifying.

### Interpretation triggers — the ones that matter most

These are the user's sharpest point, and they are qualitatively different from the others:

> **Logs we did not have before can change the interpretation of a domain.**
> **Interfaces we did not know can change a domain or subdomain.**

A domain assignment is a **hypothesis**, not a fact. When the log accumulator delivers a
month we never had, or the interface map finds a destination nobody knew, the correct
response is not to append the new data to the old conclusion — it is to **re-derive the
affected domain**.

Concretely, from this session: RE-FX was "not evidenced" until its transactions appeared in
a log window. PBC was an "engine" until execution showed 68 users. PM's whole meaning
changes if the `Mouv` satellite turns out to be its front-end — that single interface fact
would move it from an internal maintenance domain to an externally-orchestrated one.

**Therefore:** every domain assignment carries the evidence window it was derived from. When
the window extends materially, the assignment is due for re-derivation — and the model
should say so rather than wait to be asked.

---

## 6. What to do, in order

1. **Document PS.** 1.6M executions, zero documents. The largest unexplained-to-a-human
   business domain in the tenant.
2. **Deepen PBC and the FM chain.** This is the differentiator, and PBC sits at 4/11 with
   68 users depending on it.
3. **Build the Grants capability before the next client needs it.** UNESCO does not use GM,
   which makes it cheap to be wrong about — and almost every peer organisation does use it.
4. **Retire the redundancy:** one `p2p_conformance`, merge `Payment`/`BCM` in the registry,
   archive the eight superseded extractors.
5. **Wire the accumulation triggers** so the loop fires on evidence. Today every cadence in
   the model is a calendar entry that depends on a human.
6. **Stamp every domain assignment with its evidence window**, so extending the window
   automatically flags what must be re-derived.

**The honest constraint on all of it:** this depends on the log accumulator, which is the
most valuable capability in the inventory and the least protected — gitignored, unversioned,
writing to a local database with no confirmed backup.
