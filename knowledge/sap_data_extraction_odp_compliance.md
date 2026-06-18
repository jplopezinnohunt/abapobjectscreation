# SAP Data Extraction Compliance — ODP-RFC (SAP Note 3255746)

**Status:** ✅ Compliant — Not Affected
**Assessed:** 2026-06-02 (Session #78)
**Scope:** UNESCO Gold DB extraction pipeline (P01 → `p01_gold_master_data.db`, ~68 extracted tables, 24M+ rows)
**Brain:** claims #203 (verified_fact), #204 (operational_risk); rule `feedback_classify_exact_api_before_compliance_call`

---

## Source basis (read first)

The SAP Note text was **NOT directly read** — `me.sap.com` is S-user gated. The verdict rests on three independent legs:

1. **Code, verified (TIER_1):** our pipeline calls `RFC_READ_TABLE`, not any ODP API (I read the source).
2. **Note scope, independently corroborated (web check 2026-06-02):** 6+ authoritative public sources agree the note restricts the **ODP Data Replication API over RFC (`RODPS_REPL_*`)** only.
3. **Table-read RFC explicitly unaffected:** Theobald (the leading SAP-extraction vendor) states it plainly (quoted below).

Net: the "not affected" verdict is **solid** for acting on. The only thing that outranks it is SAP reading SAP — **the per-system formal sign-off remains the Note 3439624 self-assessment on P01 + D01.**

### Corroboration — verbatim (web check 2026-06-02)

> "Only the use of the **ODP Data Replication API via RFC** in SAP-to-non-SAP scenarios is restricted. **RFC remains fully usable, for example for table/CDS view extractions, DeltaQ, BAPIs, or function modules.**"
> — [Theobald Software, "SAP Note 3255746: How to Achieve Data Integration Without ODP-RFC"](https://theobald-software.com/en/blog/sap-note-3255746)

Restricted function modules named across sources: **`RODPS_REPL_ODP_CLOSE` / `RODPS_REPL_ODP_PREFETCH` / `RODPS_REPL_ODP_FETCH_XML`** (the ODP delta-replication family used by Azure Data Factory, Qlik Replicate, SNP Glue, Google Cloud Data Fusion, etc.). `RFC_READ_TABLE` is none of these.

**Sources:** [Theobald](https://theobald-software.com/en/blog/sap-note-3255746) · [Databricks community](https://community.databricks.com/t5/technical-blog/navigating-the-sap-data-ocean-demystifying-sap-data-extraction/ba-p/94617) · [Microsoft Q&A (SAP CDC)](https://learn.microsoft.com/en-us/answers/questions/1659375/sap-cdc-and-sap-tables-connectors-regarding-sap-no) · [Qlik community](https://community.qlik.com/t5/Connectivity-Data-Prep/SAP-are-sending-out-note-3255746-Unpermitted-usage-of-ODP-Data/td-p/2480141) · [CData](https://www.cdata.com/blog/sap-odp-ban) · [Forrester (strategic context)](https://www.forrester.com/blogs/sap-is-attempting-to-become-the-gatekeeper-of-enterprise-ai-cios-should-push-back/)

## The trigger

SAP (or partner) notified UNESCO that **SAP Note 3255746 — "Unpermitted usage of ODP Data Replication APIs"** was updated 2026-04-13. Key points of the notice:

- **ODP-RFC extractions are not permitted** for third-party (non-SAP) tools.
- Permitted alternatives: **SAP Business Data Cloud** or **ODP-OData**.
- A **self-assessment tool** is available via **SAP Note 3439624** to verify ODP-RFC usage.
- A **security patch ships on Patch Day, 2026-06-09**, to verify usage patterns and **block unauthorized ODP-RFC calls**. Installation can be deferred for a compliance grace period.

The question put to the brain: **does this affect the way we extract data for the Gold DB?**

---

## Verdict: out of scope. We are not affected.

The note restricts the **ODP Data Replication API framework**. Our Gold DB extraction does not use it. It uses a different, generic mechanism.

### What the note restricts (ODP-RFC) — we use NONE of these
| API / mechanism | Purpose |
|---|---|
| `RODPS_REPL_*` | ODP replication RFC interface |
| `ODQ_*` | Operational Delta Queue |
| `/SAPDS/` operators | SLT / SAP Data Services extraction |
| CDS-view / extractor / DataSource subscriptions | Source objects for ODP |
| Change-data-capture / delta replication to 3rd-party tools | The thing the note governs |

### What the Gold DB actually uses (out of scope)
| Mechanism | Detail |
|---|---|
| **`RFC_READ_TABLE`** | Generic single-table reader, function group SDTX |
| Pagination | `ROWCOUNT` / `ROWSKIPS`, `WHERE` pushed via `OPTIONS` |
| Source objects | Transparent application tables (BKPF, BSEG, FMIFIIT, SKB1, …) |
| Transport | pyrfc over **SNC/SSO**, P01 read-only |
| Delta / subscription | **None** — every refresh is a full bounded read |

## Why the distinction holds

ODP and `RFC_READ_TABLE` are **different frameworks**:

- **ODP** is a *replication* mechanism — delta queues, subscriptions, change-data-capture. Built for continuously streaming changes into an external warehouse/tool.
- **`RFC_READ_TABLE`** is the equivalent of *"SELECT these fields FROM this table WHERE …, return the rows."* No delta queue, no subscription, no ODP context.

SAP Note 3255746, its self-assessment (Note 3439624), and the 2026-06-09 patch **all target ODP only**. The patch blocks unauthorized **ODP-RFC** calls; our pipeline makes none, so a Gold DB refresh runs unchanged after the patch. **No action and no patch deferral are required on our account.**

## Evidence (code, source of truth)

| Evidence | Reference |
|---|---|
| Sole extraction primitive | [`rfc_helpers.py:147`](../Zagentexecution/mcp-backend-server-python/rfc_helpers.py) — `conn.call("RFC_READ_TABLE", …)` |
| Representative extractor | [`extract_bkpf_bseg_parallel.py:94`](../Zagentexecution/sap_data_extraction/scripts/extract_bkpf_bseg_parallel.py) |
| Repo-wide scan for ODP APIs | **0 calls** (`RODPS_REPL`, `ODQ_`, `/SAPDS/`, `RODPS`, `ODP_`) across all `.py` |
| Only token match | `sap_brain.py:863` — a **name-classifier regex** (`ODQ_\|RSN3\|RSCOLL` → labels BW objects), not an ODP call |

## For an SAP-defensible sign-off

Code evidence is strong a priori. To convert it into SAP's own confirmation, **run the Note 3439624 self-assessment tool on P01 and D01.** That is what closes the loop UNESCO is being asked to close.

## Residual risk to monitor (forward-looking — claim #204)

This specific note is a non-event for us, and `RFC_READ_TABLE` is currently the *vendor-recommended compliant alternative* to ODP-RFC — not a flagged risk. (Earlier drafts of this doc overstated it as "not released for productive use"; corrected after web corroboration.)

The genuine residual risk is **strategic and directional, not imminent:** SAP is broadly moving to gatekeep third-party data access and steer customers toward SAP Business Data Cloud / ODP-OData ([Forrester, 2026](https://www.forrester.com/blogs/sap-is-attempting-to-become-the-gatekeeper-of-enterprise-ai-cios-should-push-back/)). The Gold DB's entire extraction floor rests on **one function module, `RFC_READ_TABLE`** — so *if* SAP ever extended restrictions to generic table-read RFC, that would be a single point of failure for every refresh.

**Mitigation path (only if that ever materializes):** migrate the extraction floor to **ODP-OData** or **SAP Business Data Cloud.** CDS/OData building blocks already exist via the `sap_segw` skill. Monitor SAP notes on table-read-RFC governance; no action needed now.

---

## Reusable lesson (rule `feedback_classify_exact_api_before_compliance_call`)

When a SAP data-access restriction arrives, **classify the exact FM/API family our code calls before judging impact.** Never reason from the category ("it's an RFC that reads data"). The precise API *is* the whole answer (CP-003).

## Surfaced on

The companion landing page carries a permanent compliance banner stating this verdict: [`companions/unesco_sap_landing.html`](../companions/unesco_sap_landing.html) (section "SAP Data Extraction Compliance — ODP-RFC").
