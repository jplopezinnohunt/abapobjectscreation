---
title: UNESCO SAP transport landscape — ABAP-discipline step #0 (read-only probe)
status: VERIFIED (live RFC read of D01 TMS config) + role of V01 confirmed by JP
verified_date: 2026-06-15
verified_by: agent (read-only RFC_READ_TABLE on D01) + JP (V01 = QAS)
reverify_command: python Zagentexecution/mcp-backend-server-python/probe_landscape_readonly.py
canonical_source: true
relates_to: ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md (step #0/#2)
---

# UNESCO SAP transport landscape — what step #0 of the ABAP change-discipline rule found

Read-only landscape probe (rule step #0: *"probe the landscape read-only FIRST — never assume it"*). Source:
live `RFC_READ_TABLE` of `TMSCSYS` / `TMSCROUTE` / `TMSCDOM` / `E070` on D01 (2026-06-15). Nothing was written.
The role of V01 was **confirmed by JP**: **V01 = QAS** (it was a parked detail in the raw probe).

## ✅ The landscape IS a 3-system DEV → QAS → PROD (corrected — there IS a QAS)

| System | SYSTYP | Role | Evidence |
|---|---|---|---|
| **D01** | R (real) | **DEV** | dev system the agent writes to; CICFG=O, DLCFG=O, HOLDCON=X |
| **V01** | R (real) | **QAS (Quality Assurance)** | **confirmed by JP 2026-06-15**; also the recovery source for INC-CLASS-LOSS (transport of copies V01→D01) — so D01↔V01 transport path is proven |
| **P01** | R (real) | **PROD** | CICFG=O, DLCFG=blank (endpoint) |
| TS1, TS3 | R (real) | test / sandbox | generic "System TSx"; not in the DEV→QAS→PROD release path |
| VDE, VRT | V (virtual) | transport validation | "virtual for transport validation to P01" / "virtual target system" |

**7 systems = 5 real + 2 virtual**, all **basis 7.50** (SAPREL=750), one domain **DOMAIN_P01**. A second domain
**DOMAIN_TS2** is isolated (TS2 lives there) — which is why TS2 could only be a baseline, never deliver to D01.

## The decisive findings

1. **A QAS EXISTS: V01.** The 3-system safety net is present → **D01 (DEV) → V01 (QAS) → P01 (PROD)**. The rule's
   step #2 escalation ("if no QAS…") is therefore **RESOLVED**: there is a real system to import-and-test into
   before PROD. *(Earlier "no QAS" reading was the un-assigned role of V01; JP confirmed it. Corrected.)*
2. **Transports ARE released at scale — releasing is already the landscape norm.** `E070`: **29,408 released**
   (TRSTATUS=R) vs **511 open** (TRSTATUS=D). The durable-version + 4-eyes + rollback mechanism exists and is used.
   INC-CLASS-LOSS was **the agent bypassing it** via ADT in-place activation — **not** a landscape limitation.
3. **Basis 7.50 on every system** → native REST gates (ATC `/sap/bc/adt/atc`, transport release `/sap/bc/adt/cts`,
   ABAP Unit) are all in scope. The kernel blocks nothing.

## Implication for the ABAP change-discipline rule

| Step | Verdict from this probe |
|---|---|
| **#1 — transport-mandatory write** | ✅ Viable AND already the landscape norm (29k released). The agent must wrap its writes the way the rest of the landscape already does. |
| **#2 — QAS** | ✅ **RESOLVED — QAS = V01.** The disciplined flow is real: D01 (dev) → release transport → import to **V01 (QAS)** → test → P01 (prod). No need to provision one. |
| **#3 — ATC REST gate** | ✅ Available (7.50). |

## Minor open detail (parked)

`TMSCROUTE` returned 0 rows in the raw read → the D01→V01→P01 moves may be **manual STMS import-queue** rather than
a table-configured route chain (consistent with the recovery, which imported V01K910259 by manual queue selection).
The QAS *system* (V01) is confirmed; the exact route-config vs manual-import mechanism is the only residual detail.

## AI Diligence Statement

| Element | Detail |
|---|---|
| **AI Role** | Claude ran the read-only landscape probe and interpreted TMSCSYS/TMSCROUTE/TMSCDOM/E070. |
| **Model** | Claude Opus 4.8 (1M context) — via Claude Code CLI. |
| **Human Role** | JP directed "start with #0 and finish," then **confirmed V01 = QAS** (correcting the parked role). |
| **Verification** | `[VERIFIED]` live RFC on D01 2026-06-15: 7 systems / DOMAIN_P01 / basis 7.50 / 29,408 released vs 511 open. `[VERIFIED by JP]` V01 = QAS → D01→V01→P01. `[INFERRED]` route-config vs manual-import mechanism (parked). |
| **Accountability** | JP Lopez maintains full responsibility for decisions based on this output. |
