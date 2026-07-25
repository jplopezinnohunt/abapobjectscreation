# F0 — the INGEST GATE (`probe_suite_f0.json` + `f0_probe.py` → `system_profile.json`)

**What it is.** F0 is the *negative contract* of a SAP landscape, made executable. Before any extractor is
written for a tenant, F0 asks — against that tenant's own system — what the RFC boundary will **not** let us
read, records the **real** symptom SAP returns, and derives the extraction strategy that works anyway.

It exists because the frontier was learned the expensive way on P01 (secured RFC wrapper rejecting ROWSKIPS,
anti-injection WHERE guard, 512-byte work area, cluster/pool opacity, EhP8 ADT gaps, FMAVC* not RFC-enabled)
and that knowledge lived as prose in docstrings and `constraint` fields. F0 turns it into a suite you run in
minutes on client #2 instead of re-discovering it at client price.

Contract: `sapilot/analysis/arch/C1-extraccion-hub.md` §3 "Contrato C". Running it moves sub-capability
**C1.1c from M0 (tribal prose) to M2 (executable, versioned artifact)**.

Three files, one job:

| File | Role |
|---|---|
| `probe_suite_f0.json` | the **specification** — 8 probes, each with its question, the expected failure, the failure signatures, the derived strategy, the fallback, severity and which part of the `method_registry` it feeds. Declarative; the runner never rewrites it. |
| `f0_probe.py` | the **runner** — executes the probes read-only, with hard timeouts. |
| `system_profile.json` | the **output** — this system's answers, with the real SAP evidence attached. |

---

## The one rule that makes the profile trustworthy

Three outcomes, never conflated:

| Runner status | Suite status | Meaning | What you may derive |
|---|---|---|---|
| `CONSTRAINT_CONFIRMED` | `CONFIRMED` | the expected failure reproduced → **the restriction exists here** | apply `derived_strategy` |
| `NO_CONSTRAINT` | `NOT_PRESENT` | the call worked → **the restriction does not exist here** | the naive/fast path (`fallback_strategy`) is allowed |
| `COULD_NOT_PROBE` | `INCONCLUSIVE` | no connection, the control call failed, a hung call, or an error that does **not** match the declared signatures | **nothing.** `strategy` is `null` by construction |

"I could not probe it" is never reported as "the restriction exists". A profile with any `COULD_NOT_PROBE`
is written but flagged `summary.complete = false`, `verdict = INCOMPLETE`, and the runner exits **1** — do
not use it as a tenant baseline until the missing probes are re-run.

Every probe that can be confounded runs a **control call first** (e.g. `ROWSKIPS=0` before `ROWSKIPS=1`, a
single-equality WHERE before `IN (...)`, a key-only read before the pooled-payload read). If the control
fails, the probe is `COULD_NOT_PROBE` — a failure you cannot attribute proves nothing.

---

## Read-only, and bounded in time

* Only the function modules in `read_only_allowlist` may be called (`RFC_READ_TABLE`,
  `SADT_REST_RFC_ENDPOINT`), enforced in `_guard_fm`; anything else raises before it reaches SAP.
* `SADT_REST_RFC_ENDPOINT` is pinned to HTTP **GET** (the ADT constraint is re-derived from the read-only
  discovery document, never from a POST).
* No probe writes to SAP. Nothing is created, changed, deleted or transported.
* Every RFC call runs in a daemon thread with `--call-timeout` (default 30 s); the whole run is capped by
  `--budget` (default 240 s). A hung call marks the connection dead and the remaining probes become
  `COULD_NOT_PROBE` rather than hanging the gate.

---

## How to run it on a new client

```bash
cd Zagentexecution/sap_data_extraction/scripts

# 1. Read the gate before running it. Never connects — works with no pyrfc, no VPN.
python f0_probe.py --system P01 --dry-run

# 2. Put SAP_<SID>_* credentials in Zagentexecution/mcp-backend-server-python/.env
#    (ASHOST / SYSNR / CLIENT / USER / PASSWD or SNC_MODE+SNC_PARTNERNAME), then run the gate.
python f0_probe.py --system Q01 --allow-unknown-system --out q01_system_profile.json

# 3. Re-run a single probe after fixing an auth or connectivity issue
python f0_probe.py --system P01 --probe max_where_conditions --out p01_system_profile.json

# CI gating: non-zero when a KILL-severity constraint is confirmed
python f0_probe.py --system Q01 --allow-unknown-system --fail-on-kill
```

`--allow-unknown-system` is the normal flag when onboarding: `P01/D01/V01` are *our* SIDs, a new tenant has
its own. `--env` points at a different `.env`.

**Exit codes**

| code | meaning |
|---|---|
| 0 | profile written, every probe evaluated |
| 1 | profile written but **incomplete** (≥1 `COULD_NOT_PROBE`) |
| 2 | usage / suite error — nothing written |
| 3 | could not connect (VPN, SNC/SSO, missing `pyrfc`) — **nothing written**, deliberately |
| 4 | `--fail-on-kill` and a KILL-severity constraint was confirmed |

Cost: 8 probes, roughly 25–40 RFC calls, all `ROWCOUNT=1` or narrow metadata reads. Minutes, not hours.

---

## How the result feeds that tenant's `method_registry`

`brain_v2/method_registry.json` resolves *"given this table class / object, which `(extract, constraint,
analyze, retention)` method applies"*. F0 reads it never and **feeds** it always: each probe declares
`feeds.type_rules` / `feeds.overrides`, and the runner aggregates the confirmed ones into
`summary.method_registry_feeds`:

```json
"method_registry_feeds": {
  "type_rules": {
    "TRANSP": [ { "probe": "rowskips_rejected",
                  "constraint": "ROWSKIPS rejected by the RFC wrapper: OPTION_NOT_VALID ...",
                  "strategy":   "Read ROWSKIPS-FREE: ROWCOUNT=0 and PARTITION ..." } ]
  },
  "overrides": { "CDPOS": [ ... ], "FMAVC": [ ... ] }
}
```

Mapping, probe by probe:

| Probe | Feeds | If confirmed, the tenant's registry must say |
|---|---|---|
| `rowskips_rejected` | `type_rules.TRANSP/VIEW` | `constraint`: no ROWSKIPS → `ROWCOUNT=0` partitioned on a low-cardinality key |
| `in_clause_rejected` | `type_rules.TRANSP/VIEW` | `constraint`: no `IN`/`OR`/parentheses → one equality per call |
| `max_where_conditions` | `type_rules.TRANSP/VIEW` | `constraint`: `max_where_conditions=<measured N>` — the **measured** number, never P01's |
| `wide_field_split` | `type_rules.TRANSP/VIEW` | `extract`: field-split at the measured `chunk_size`, merge by row position with an equal-rowcount guard |
| `cluster_unreadable` | `type_rules.CLUSTER`, `overrides.CDPOS` | `extract`: FOR-ALL-ENTRIES over the physical cluster — **or**, if `NO_CONSTRAINT`, treat as TRANSP (declustered kernel: the cheap path) |
| `strg_pool_unreadable` | `type_rules.POOL` | `extract`: key-only via RFC + a content FM for the payload |
| `adt_404_ehp8` | `overrides.ADT_DDIC` | `extract`: DDIC via `DDIF_*_PUT` / source via `CLIF_GET_SOURCE` (lossy — never read-modify-write), not ADT |
| `fmavc_not_rfc` | `overrides.FMAVC` | scoped **KILL**: no standard AVC read over RFC → decide the fallback (FMAVCT table / standard report / `RFC_ABAP_INSTALL_AND_RUN` on non-PROD) **at onboarding, not at delivery** |

Also carried into the profile: `measured` (the numbers that must not be copied between systems —
`max_where_conditions`, `chunk_size`, `estimated_wa_bytes`, FMAVC counts) and, per probe, `evidence.calls`
— the actual RFC calls issued with the real SAP error text, key, class and number. That is the audit trail
that lets someone six months later verify the constraint instead of believing it.

**Never copy a `system_profile.json` between systems.** The whole point of the gate is that the P01 numbers
are P01's. A different kernel, a different wrapper, a different authorization set gives different answers —
`cluster_unreadable` in particular flips to `NO_CONSTRAINT` on declustered EhP8 kernels, and taking the
expensive ABAP path when the cheap RFC path works is a self-inflicted cost.

---

## Suggested onboarding sequence

1. `--dry-run` — review the 8 questions with the client's Basis team; this is also the compliance
   conversation (everything is read-only; the ABAP paths in the *derived* strategies are not).
2. Full run → `system_profile.json`. Exit 0 or the profile is not a baseline yet.
3. Read `summary.verdict`: `GO` / `GO_WITH_CONSTRAINTS` / `SCOPE_LIMITED` (a KILL confirmed — renegotiate
   scope now) / `INCOMPLETE` (re-run, do not proceed).
4. Materialize `summary.method_registry_feeds` into that tenant's `method_registry` (`type_rules` +
   `overrides`) and the measured numbers into its profile.
5. Only then write extractors. They inherit the frontier instead of rediscovering it.

## Known limitations

* `adt_404_ehp8` tries a small set of GET parameter signatures for `SADT_REST_RFC_ENDPOINT`; if the kernel
  uses a different interface the probe returns `COULD_NOT_PROBE` with the real parameter errors attached
  rather than guessing. Add the signature to `_ADT_SIGNATURES` when you meet a new one.
* `cluster_unreadable` reports `COULD_NOT_PROBE` when the cluster table returns zero rows without an error:
  "declustered but empty" and "not readable" are not distinguishable from that observation alone.
* The suite's probe objects (`DD02L`, `T001`, `CDPOS`, `VARI`, `TFDIR`) are standard everywhere, but a
  hardened system may deny `S_TABU_*` on some of them — that surfaces as `COULD_NOT_PROBE` with the
  authorization error as evidence, which is itself a finding worth recording at onboarding.
