# INC-000011781 — Add Renata Ritter to UBO BCM signatory panel (+ Martin removal, drift findings)

**Status**: EXECUTED (partial) 2026-06-19 — Renata added to all 4 nodes + Martin/Ba delimited (live-verified); **OPEN**: Renata's `BNK_APP` role (Security) + 2 carton discrepancies (Yli-Hietanen missing, De Sousa over-auth)
**Type**: Operational change (add/remove signatory) + pre-existing drift findings
**Date opened**: 2026-06-17
**Requester**: Ingrid Wettie (BFM-TRS, Middle Office)
**Executed by**: DBS in P01 via `OOCU_RESP` (P01 is read-only for the AI agent)
**Verified by**: AI agent — live read-only via `RFC_READ_TABLE` on P01
**System**: P01 · **Entity**: UBO (UNESCO Brasília) · **Banks**: Citibank Brazil (CIT01) + Banco do Brasil (BRA01)
**Related domain**: Treasury / BCM Signatory Management — [domain README](../domains/Treasury/README.md)
**Related rule/model**: [bcm_signatory_rules.md](../domains/Treasury/bcm_signatory_rules.md) · [bcm_signatory_change_solution_design.md](../domains/Treasury/bcm_signatory_change_solution_design.md) · companion `companions/bcm_signatory_companion.html`
**Precedent**: [INC-000006313](INC-000006313_uis_bcm_add_voffal.md) (UIS — same Ingrid→Pablo "add X in BCM" pattern)

---

## 0. Execution status — validated live P01 (2026-06-19)
Official UBO carton received (**8 signatories**: 7 at both tiers + Amaral ≤10K only). OOCU_RESP changes were made; read back live from the 4 UBO nodes (`HRP1001` A007→P):
- ✅ **Done & correct:** Renata `10021811` added to all 4 nodes (BEGDA 2026-06-19 / ENDDA 9999-12-31); Martin `10108464` delimited (ends today); Ba `10005016` delimited (ends today); the 5 unlimited keepers (Cuba, Godinho, Jovchelovitch, Otero, Soares) + Amaral (≤10K) match the carton.
- ❌ **Open (3):**
  1. **Renata has no `BNK_APP` role** — verified still missing (`bcm_signatory_role_gap`) → she **cannot sign**; Security ticket `YS:FI:M:BCM_MON_APP______:UBO` **pending**. *The incident is not closeable until this is granted.*
  2. **Yli-Hietanen `10097358` MISSING** — on the carton (both tiers) but not active in any UBO node (expired 2024; holds role via UIS/UNES) → **ADD ×4 nodes**.
  3. **De Sousa Carvalho `10016038` over-authorized — and can sign TODAY.** Full access: in all 4 UBO nodes since 2024-01-25 (unlimited, both steps) + holds **both** `YS:FI:M:BCM_MON_APP______:UBO` (sign/approve) **and** `YS:FI:M:BCM_REV_REJ_PAY__:UBO` (reverse/reject) since Jan-2024; SAP user active (last logon 2026-06-19), employee active in UBO/Brasília (BR04). Not on the carton of 8 → **control gap** (can validate/sign/reverse UBO payments at any amount while not bank-authorized). TRS to confirm: add to carton, **or DELIMIT all 4 nodes + remove both roles**.

Refreshed live: `extract_bcm_signatories.py` + `bcm_role_gap_check.py` + `bcm_release_vs_approve.py` (Golden DB). Companion + solution-design §3e/§4b/§4d + incident page updated.

---

## 1. Request
Email chain (`IMPORTANT_ Change in Bank Signatory panel of UBO + Smart ticket INC-000011781.eml`):
- **Evaney Amaral (UBO, Treasury) → Ingrid Wettie** — "Signature Panel - CITIBANK": Renata registered in the **Role Management System** as Bank Signatory; asks if SAP/IRIS needs adjustment so she can authorize Citibank payments. Name: **Renata Da Silva Freire Ritter — PERNR `10021811`, SAP user `R_RITTER`**.
- **Ingrid Wettie → Pablo** (2026-06-17) — *"Can you please add Renata RITTER for UBO in BCM?"*

### Attached TRS letters + cartons (authoritative)
| Bank | REF | Account | DELETE | ADD |
|------|-----|---------|--------|-----|
| Citibank Brazil | FIN.8/MOD/10.0000003618 | BRL BR2433…086124552 | Von Michael MARTIN | Renata DA SILVA FREIRE RITTER |
| Banco do Brasil | FIN.8/MOD/10.0000003617 | BRL 405 275 7/2004.4 | Von Michael MARTIN | Renata DA SILVA FREIRE RITTER |

Both dated 24/03/2026, "immediate effect". HEPATUS *carton* (Code compte BRZ, 08/04/2026) — **8 signatories, identical on both banks** → the single entity rule is representable (alignment gate ✅). ⚠️ Ingrid's note said only "add Renata"; the authoritative letters also **delete Martin**.

## 2. Node selection (why these 4 nodes) — IT1218
UBO nodes selected by `ZBUKR=UBO` + `MAXPAYAMT_RULECURR` band (IT1218 expressions on `BNK_STR_BATCH_REL_APPR`; see [rules §Node selection](../domains/Treasury/bcm_signatory_rules.md)). Renata is "unlimited" on the carton → all 4 UBO nodes.

## 3. Pre-change verification (live P01, read-only)
- **Renata `10021811`**: `PA0002` = Renata Da … RITTER (DOB 1973-09-24, matches passport); `PA0105/0001` USRID=`R_RITTER`; `0010` email `R.RITTER@UNESCO.ORG`; `USR02` UFLAG=0 (unlocked), USTYP=A. ⚠️ **GLTGB=2026-09-30** (user validity ends) and she **lacks the `BNK_APP` role** (her screenshot "not authorized to use BNK_APP").
- **Employee validity**: all 11 affected PERNRs are `PA0000` STAT2=3 (active). No ghost PERNR.
- **Martin `10108464`**: active row only in **50034893** (`2024-11-19 → 99991231`); expired everywhere else. (Screenshot "Other period" hid the active row — confirmed via all-periods `HRP1001` read.)

## 4. Change spec for DBS — `OOCU_RESP`, BEGDA=exec date, ENDDA=99991231
**Current ask (authorized by REF 3617/3618):**
| Op | PERNR | Rule | Node |
|----|-------|------|------|
| ADD | 10021811 Ritter | 90000005 | 50034892 |
| ADD | 10021811 Ritter | 90000005 | 50034893 |
| ADD | 10021811 Ritter | 90000004 | 50034894 |
| ADD | 10021811 Ritter | 90000004 | 50036737 |
| DELIMIT | 10108464 Martin | 90000005 | 50034893 |

**+ Security ticket:** grant `BNK_APP` role (`YS:FI:M:BCM_MON_APP______:UBO` + signature user `F_STAT_USR`) to `R_RITTER`.

## 5. Old issues — hold for TRS sign-off (NOT in this letter)
- **Ba `10005016`** + **De Sousa Carvalho `10016038`** — active in UBO nodes but on **neither** carton → over-authorization. (UBO's only BCM bank is CIT01; BRA01 is Process 2 manual, no BCM batch — so the "other bank" defence doesn't apply.)
- **Yli-Hietanen `10097358`** — on both cartons but delimited from UBO since 2024-01-26 → gap (re-add or confirm intentional HQ-treasurer exclusion).
- **Gazi `10105030`** — expired, not on carton → no action.

## 6. Output (mandatory structure)
Full reconciliation as the mandatory single table (Rule | Node OBJID | Node name | PERNR | Person | Live status | Action), mirroring `OOCU_RESP` 1:1 (active + expired rows) + the adds — see the companion (§8) / design doc (§6). Net = 4 ADD + 1 DELIMIT (current ask); 3 old issues parked for TRS.

## 7. Learnings
1. **Node selection = IT1218** (`HRP1218`/`HRT1218` on `BNK_STR_BATCH_REL_APPR`), not PFAC `HRP1222` (empty). Captured in `bcm_signatory_rules.md`.
2. **Never conclude from screenshots** — OOCU_RESP "Other period" hid Martin's active period; resolve multi-period people via live `HRP1001` (all periods).
3. **Reconciliation universe = banks that produce BCM batches** (`BNK_BATCH_HEADER`), not all `T042A` banks — UBO/BRA01 is Process 2 (manual), only CIT01 reaches BCM.
4. **Discoverability fix**: linked this knowledge from the Treasury README hub, the skill triggers/routing, the rules doc, and the precedent (it was hard to find before despite prior discussion).

## 8. Closure checklist
- [x] Letters + cartons read; alignment confirmed (8 = 8)
- [x] Live P01 pre-verification (Renata, employee validity, Martin periods, IT1218)
- [x] Change spec + mandatory output produced
- [ ] DBS executes in P01 (`OOCU_RESP`)
- [ ] Post-change `HRP1001` verification + `extract_bcm_signatories.py` refresh + reconciliation check
- [ ] Security grants `BNK_APP` to R_RITTER
- [ ] TRS sign-off on old issues (Ba, Carvalho, Yli-Hietanen)
- [ ] Reply to Ingrid (confirm add + flag Martin delete + drift + bank-confirmation deadline)
