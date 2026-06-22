# Way-of-Working Plan — driven by the META-CAPABILITY model (from 2026-06-22)

> **From now on, the plan is evaluated and organized by the meta-capability categories + sub-levers.**
> Run `python brain_v2/meta_capability.py` EVERY session (auto-surfaced by `session_start_hook.py`).
> Each WEAK sub-lever is a tracked target; each `[E]` (estimate) is itself a lever ("instrument it -> [M]").
> Rule: **move ONE weak sub-lever per session.** Current **META-MATURITY = 64.4%**.

The 7 capabilities, ordered by weakness (lowest first = highest claim on attention).
`now` = measured this session. `→` = target. Action = the concrete move (mapped to a PMO H-item).

---
## 🔴 DURABILITY — 0.23  (most URGENT: catastrophic-loss risk)
| sub-lever | now | → | action | owner | H |
|---|---|---|---|---|---|
| `assets_backed_up` | 0.00 [E] | 1.0 | offsite/disk backup of Golden DB (~6.4GB) + `~/.claude` memory — git does NOT protect them | JP | **H83 (new)** |
| `unattended_ready` | 0.00 [M] | 1.0 | BASIS keytab / headless SNC (interactive ticket dies ~10h) | BASIS | H66 |
| `tooling_tracked` | 0.70 [M] | 1.0 | move `accumulate_logs.py`/`accumulate_problems.py` to git-tracked `scripts/` | me | H70 |

## 🟡 VERIFY — 0.41  (the KEYSTONE: makes the brain trustworthy; the #232 failure mode)
| sub-lever | now | → | action | owner | H |
|---|---|---|---|---|---|
| `claims_2plus_sources` | 0.24 [M] | 0.60 | give each weak claim a 2nd INDEPENDENT source (`claims_health.py` worklist) | me | **H84 (new)** |
| `weak_tier1_cleared` | 0.00 [M] | 1.0 | verify the 21 weak TIER_1 claims (start with this session's own: #213/#214/#217) | me | **H84 (new)** |
| `adversarial_verify_rate` | 0.40 [E] | 0.80 | spawn a verifier chip for EVERY quantitative conclusion BEFORE it is a firm claim | me | **H85 (new)** |
| `refutation_capture` | 1.00 [M] | — | done — supersede mechanism works (#232→#236) | — | — |

## 🟡 ANALYZE — 0.48  (the PRODUCT: G = AS-DESIGNED vs AS-RUN delta = conformance)
| sub-lever | now | → | action | owner | H |
|---|---|---|---|---|---|
| `domain_conformance` | 0.20 [E] | 0.50 | a conformance pass per domain | me | H71·H72·H73·H79 |
| `process_mining_maturity` | 0.30 [E] | 0.50 | OCEL origin=resource + more domains | me | H77·H80·H81 |
| `decode_before_conclude` | 0.50 [E] | 1.0 | tier-at-statement + decode detail before concluding (a count = hypothesis) | me | **H86 (new)** |
| `rfc_call_classification` | 0.93 [M] | — | strong (self-adapting 92.5%) | — | — |

## 🟢 SELF_CORRECT — 0.60
| sub-lever | now | → | action | owner | H |
|---|---|---|---|---|---|
| `self_caught_ratio` | 0.30 [E] | 0.60 | catch errors BEFORE stating (couples to VERIFY `decode_before_conclude`) | me | H86 |
| `correction_latency` | 0.50 [E] | — | instrument (turns from wrong-claim to supersede) | me | — |
| `supersede_mechanism` | 1.00 [M] | — | strong | — | — |

## 🟢 EXTRACT — 0.90
| sub-lever | now | → | action | owner | H |
|---|---|---|---|---|---|
| `kernel_verified` | 0.60 [E] | 0.90 | empirically verify each registry method on the target kernel; populate all elements | me | H82 |
| `registry_resolver` / `table_class_coverage` / `special_element_coverage` | 1.00 | — | strong | — | — |

## 🟢 CONSOLIDATE — 0.95 · ESCALATE — 0.93  (strong — MAINTAIN, don't let decay)
Coverage 100% / 0 blind-spots / steward-at-close / rule #162 + PMO. Maintenance only.

---
## The standing ritual (the user directive, 2026-06-22)
1. **Session start:** the hook surfaces the meta-maturity headline + weakest lever (already wired).
2. **During:** pick ONE weak sub-lever; the action above is the move.
3. **Session close:** re-run `meta_capability.py` + `claims_health.py`; the number should rise or a lever flip `[E]→[M]`.
4. **Evolution = the trend of META-MATURITY over sessions**, not a one-time score. Instrumenting an `[E]` lever
   (making it measured) is as valuable as raising a `[M]` score — it makes the self-model honest.

## Unmapped backlog still tracked (fold into the above next session)
H75 (9,242 status-29 IDocs → ANALYZE), H78 (problems-accumulator schedule → DURABILITY/ANALYZE).
