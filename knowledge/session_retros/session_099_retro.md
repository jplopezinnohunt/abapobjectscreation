# Session #99 Retro — a support ticket that turned into a recoverability audit

**2026-08-17 / 18 · 55 commits · Egypt Purpose of Payment (INC-EGYPT-PPC) → the model itself**

## 1. Context

The session opened as a support case: Citibank Egypt requires a Purpose of Payment on every
RTGS and cross-border transfer from 2026-09-05. It ended somewhere else entirely, because of
one question JP asked halfway through:

> *"si cerramos esta sesión, ¿cómo reutilizas todo lo que aprendimos sobre Purpose Payment?"*

Measured rather than answered:

| what a fresh session actually reads | mentions of PPC / Egypt / T015L |
|---|---|
| `brain_v2/BRAIN_INDEX.md` (mandatory first read) | **0** |
| `MEMORY.md` (auto-loaded) | **0** |
| `graph_queries.py incident INC-EGYPT-PPC` | the complete fix |

The analysis was durable, correct, queryable — and unreachable. The only way in was to already
know the incident id, which is exactly what a new session does not know. That reframed the
rest of the session from *solving Egypt* to *fixing why solving Egypt would have been wasted*.

## 2. The Egypt case — resolved, no ABAP

Three maintained tables, no code. Verified from source, not assumed:
`FI_CGI_DMEE_EXIT_W_BADI` selects the implementation by **our** house bank's country
(`FPAYHX-UBISO` → the FR class, SocGen), and inside it CM002 passes **their** bank's country
(`FPAYH-ZBNKS`) to the config lookup. Two countries, two layers — so adding `EG` rows suffices.

**The load order is the whole risk.** The switch is `YTFI_PPC_STRUC`, not `T015L`: the moment
those rows land in P01, every posting in company code `UNES` to a vendor with `LFBK-BANKS = EG`
is blocked. Two transports, or the block starts the second the import finishes with Cairo
untrained.

Ten codes, `EG0..EG9`, agreed with JP and verified against ISO 20022.

## 3. Four gaps closed, each with a ratchet

Numbers can only go down now; the check fails if they grow.

| gap | before | after | enforced by |
|---|---|---|---|
| quality checks nobody ran | 13 idle | 13 running each rebuild | `run_all.py` glob, no registry |
| algorithms discovering with nowhere to land | 27 | **0** | `algorithm_landing_check.py` |
| claims not declaring what they discuss | 233 | **0** | `typed_link_coverage_check.py` |
| open incidents unreachable from the index | 1 | **0** | `knowledge_reachability_check.py` |

Plus the reverse **entity index** (1,242 entities): the brain had four indexes and none by
thing, so *"what do we know about DMEE"* had no answer but a text scan. The structure already
existed and pointed the wrong way — claims carry `related_objects`, nothing indexed it back.

## 4. Mistakes made, and what each one taught

Recorded because the pattern matters more than the individual slips.

- **A zero-match grep is a claim about your grep** (rule #200, made twice). First on
  case: `YRGGBS00_SOURCE.txt` is UTF-16 with lowercase ABAP, so a grep for `'LZBKZ'` found
  nothing and claim 116 asserted no control existed. `FORM u917` was at line 1547. Then again
  on **filenames**: searching companion *names* for `dmee` returned zero while
  `BCM_StructuredAddressChange.html` holds **965 mentions**. JP caught both.
- **Never sum an amount across currencies** (rule #201). Reported "USD 3,285,100" from
  `SUM(RWBTR)` over mixed currencies whose largest entries were EGP.
- **Do not invent codes.** Proposed `TRVL`, `RDEV`, `ITSV`, `TRAI` — none exist in ISO 20022.
  Found only because JP asked for the research.
- **My own checks were hiding their findings.** `baseline.verdict` wrapped `sys.stdout.buffer`
  in a second `TextIOWrapper`; the caller's lines were discarded and only the verdict survived.
  Exit code right, number right, and every line naming *which* findings gone.
- **A silent cap leaves work unreachable.** The first OPEN WORK block showed 8 of 9 live
  incidents. `knowledge_reachability_check.py` caught it on its first run.
- **The ratchet caught me too.** Landing claim 497 introduced `P01_GOLD_MASTER_DATA` as a new
  entity, which exposed two older claims that mentioned it unlinked. A new entity does not just
  get added — it makes visible everything that discussed it without declaring it.

## 5. Phase 4b — what we learned about SAP itself

- **`T015L` has NO country field.** Its key is `LZBKZ` alone (73 rows, one flat global
  namespace). The `EG`/`JO` prefix is a naming convention, not a constraint SAP enforces, and
  `u917` only tests non-empty — so `JO6` on an Egyptian payment passes every layer and reaches
  the bank. One condition (`lzbkz(2) = lv_banks`) would fix it.
- **The switch is `YTFI_PPC_STRUC`, not `T015L`.** All 9 configured countries carry a
  `PPC_VAR`/`PPC_DESCR` row; that row is what blocks the posting. The other two tables are
  inert alone.
- **`u917` keys on `LFBK-BANKS`** — the vendor's *bank* country, not `LFA1-LAND1`. A vendor
  domiciled in India banking in Singapore is unaffected. This explained 259 of 283 apparently
  missing India codes.
- **`REGUH-UBNKS` is OUR house bank's country**, not the payee's (`SOG01` → FR across
  1,943,748 lines, one distinct value). Misreading it understated the Egypt population ~10×.
- **Exact config constants:** `BLART='2'`, `LVAWV='000'` on all 73 `T015L` rows; `ZWCK1` is
  `CHAR(70)` holding `code + space + narrative`; `TAG_ID` is `USTRD` for 7 of 9 countries, only
  AE and CN use `INSTRINF`.
- **`YXUSER` does not cover `u917`.** It gates five routines and this is not one — no
  super-user bypass exists here, by design.
- **Our own config is not uniformly ISO 20022:** `T015L` `PH3` is `TRVL`, which is not an ISO
  purpose code. Do not cite the Philippines as "the ISO precedent" without that caveat.
- **The Central Bank of Egypt adopted ISO 20022 on 2026-06-21**, and publishes no national
  purpose-code list that any search could find — consistent with Citi asking for a description.
- **`BPJA` was consolidated** from per-year tables (`bpja_2024/25/26`) into one table with
  `GJAHR`, and it carries **no indexes** while the per-year `cosp_*` tables do.

## 6. Reward function

The project's rule is `items_shipped - items_added > 0`. Honestly counted: **7 items added**
(H91, H92, H93, H95, H97, H98, H99) against a larger set shipped — the four ratcheted gaps, the
Egypt spec, the backup, three script defects, H96 opened and closed the same day.

But the added items deserve a caveat rather than a win: most are **debt that was already there
and invisible**. The 4 stranded datasets, the missing alias layer, the 191 outlier vendors and
`ZHROFFBOARDING` were not created this session — they became *countable*. A rising backlog made
of newly-visible truth is not the same failure as a rising backlog made of new mess.

## 6b. The second half — architecture, and the two hours it cost

The session's second half was JP saying *"es un tema de arquitectura... nuevamente"* three
times before I heard it. He was right. The recurring failure was never "we forgot to wire X":
seven layers exist — the graph_queries CLI, an MCP server, quality_checks, algorithms, agents,
skills, hooks — and **nothing declared which layer owns a given need**. So the same capability
got built twice, reading two different sources, and both rotted quietly.

Two measured proofs, neither of them an "old tool":

| capability | implementation A | implementation B |
|---|---|---|
| search the brain | `graph_queries.py` reads `brain_state.json` + entity index | `brain_search` reads `output/brain_v2_graph.json` — **different source** |
| write ABAP | `deploy_object.py`, 9 gates, PRE/POST readback | `adt_deploy`: lock→write→activate, **none of it** |

**What landed:** `capability_ownership.json` (one capability, one owner, enforced by a check) ·
deploying ABAP declared **out of scope** · 81 dead write scripts moved to `_obsolete/` with
`git mv` · the risk landed in four places at once (MEMORY.md, a memory file, claim 498, rule
#204) · `golden_hub` extended to stop refusing a fifth of the database.

### And what it cost, honestly

- **The workflow returned nothing.** Five lenses with per-finding refuters, launched to decide
  whether a 200-line module should exist. It took the machine to 100%, died with no completion
  record and no partial results, and burned about two hours. The question was settled
  afterwards by one grep: `import golden_hub as _gh`, line 548. → rule #205.
- **I rebuilt a module that already existed.** I found `golden_query` inside
  `sap_mcp_server.py`, assumed it was MCP-bound, and deprecated the whole directory without
  reading what it imports. `golden_hub.py` and `rfc_helpers.py` were collateral. → rule #206.
- **An invented domain aborted a full rebuild.** Claims 497/498 used `"domain": "Operations"`,
  which is not in the canonical ontology. The Step-0 gate killed the rebuild in 0.8s — working
  exactly as designed, and costing a 15-minute re-run.
- **The writer count went 91 → 3.** Two corrections: `RFC_ABAP_INSTALL_AND_RUN` against P01 is
  a READ technique, and a write FM named inside a *string* is a mention, not a call. The first
  number was alarm, not measurement, and it was reported to JP before being verified.

The pattern under all four: **I acted on a number or a label before reading the thing itself.**
Every correction came from finally reading the source — and in three of the four, from JP
pushing back rather than from any check.

## 7. What remains

**H91** 191 vendors with an outlier `AKONT` · **H92** *(closed — see §3)* · **H93** companions
still absent from `BRAIN_INDEX.md` · **H95** `ZHROFFBOARDING` never downloaded, 26 `HTTP 404`
markers, same HR-Fiori zone as the 37 unlanded `ZTHRFIORI_*` discoveries — suggestive, **not
proven** to be the same cause · **H97** sibling repos with no remote · **H98** 4 stranded
discovery datasets · **H99** the entity index has no alias layer, so `entity DMEE` returns
15 companions and zero claims.

**Durability:** golden verified on `D:\claude_backups` (369 tables, 5 views, `bpja` 135,794,
`quick_check=ok`), `~/.claude` zipped today, 16 GB of same-volume duplicate reclaimed. The
long-running "the golden changed" alarm was a **unit**: 16.33 GB decimal = 15.21 GiB binary.
Same file, every close, for weeks.
