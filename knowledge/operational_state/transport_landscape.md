---
title: UNESCO SAP transport landscape — ABAP-discipline step #0 (read-only probe)
status: VERIFIED (live RFC read of D01 TMS config)
verified_date: 2026-06-15
verified_by: agent (read-only RFC_READ_TABLE on D01)
reverify_command: python Zagentexecution/mcp-backend-server-python/probe_landscape_readonly.py
canonical_source: true
relates_to: ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md (step #0/#2)
---

# UNESCO SAP transport landscape — what step #0 of the ABAP change-discipline rule found

This is the **read-only landscape probe** the rule (`sap-abap-change-discipline.md`) mandates as step #0:
*"probe the landscape read-only FIRST — never assume it."* It converts the earlier `[REPORTED]` assumption
("no QAS, D01+P01 only") into a `[VERIFIED]` fact. Source: live `RFC_READ_TABLE` of `TMSCSYS` / `TMSCROUTE` /
`TMSCDOM` / `E070` on D01 (2026-06-15). Nothing was written.

## The systems (TMSCSYS — domain DOMAIN_P01, all basis 7.50 / SAPREL=750)

| System | SYSTYP | Config | Role (evidence-based) |
|---|---|---|---|
| **D01** | R (real) | CICFG=O, DLCFG=O, HOLDCON=X | **DEV** — the development system (the one the agent writes to) |
| **P01** | R (real) | CICFG=O, **DLCFG=blank** | **PROD** — production; no delivery onward (endpoint) |
| **V01** | R (real) | CICFG=O, DLCFG=O | sibling real system — was the **recovery source** for INC-CLASS-LOSS (transport of copies V01→D01) |
| **TS1** | R (real) | CICFG=O, DLCFG=O | test/sandbox real system (modified 2025-09) |
| **TS3** | R (real) | CICFG=O, DLCFG=O | test/sandbox real system |
| **VDE** | V (virtual) | COMSYS=V01 | "virtual for transport validation to P01" |
| **VRT** | V (virtual) | COMSYS=P01 | "virtual target system" |

**7 systems total = 5 real + 2 virtual.** A second domain, **DOMAIN_TS2**, is isolated (TS2 lives there; not in
D01's TMS list) — that is why TS2 could only serve as a baseline, never deliver a transport to D01 (INC-CLASS-LOSS).

## The three decisive findings

1. **NO QAS quality-gate system between DEV (D01) and PROD (P01).** None of the real systems is described or
   positioned as a Quality Assurance test system in the dev→prod path. `TMSCROUTE` returned **0 rows** → there is
   **no configured consolidation/delivery route chain**; transports are moved by **manual STMS import-queue
   selection** (exactly what the 2026-06-12 recovery did: "import only V01K910259, queue row 9"). The only thing
   resembling a quality hop is two **virtual** validation placeholders (VDE/VRT), not a real system where you test
   with productive-like data. → This is the **3-system-landscape gap** the rule flags at step #2.

2. **Transports ARE released at scale — releasing is already the landscape norm.** `E070`: **29,408 released**
   (TRSTATUS=R) vs **511 open** (TRSTATUS=D). So the durable-version + 4-eyes + rollback mechanism **exists and is
   used landscape-wide.** INC-CLASS-LOSS was **the agent bypassing it** via ADT in-place activation — **not** a
   landscape limitation. The fix (#1, transport-mandatory write) asks the agent to do what the landscape already does.

3. **Basis 7.50 confirmed on every system** (SAPREL=750) → the native REST gates (ATC `/sap/bc/adt/atc`, transport
   release `/sap/bc/adt/cts`, ABAP Unit) are all in scope. Nothing about the rule is blocked by the kernel.

## Implication for the ABAP change-discipline rule

| Step | Verdict from this probe |
|---|---|
| **#1 — transport-mandatory write** | ✅ Viable AND already the norm (29k released). The agent must wrap its writes the way the rest of the landscape already does. No blocker. |
| **#2 — QAS / escalate** | 🔴 **ESCALATION TO JP (open decision).** There is **no QAS** to import-and-test into before "real". For AI-generated ABAP the only pre-prod environment is **D01 itself + virtual validation**. Decision for JP: (a) accept **D01 + ATC + human-4-eyes-on-release** as the gate for now, or (b) provision/identify a real QAS (V01/TS1/TS3 could be a candidate — role not yet confirmed). |
| **#3 — ATC REST gate** | ✅ Available (7.50). |

## Open detail (parked — minor)

The exact **role of V01 / TS1 / TS3** and the precise consolidation-route topology were **not fully enumerated**
(`TMSCROUTE` came back empty in this read; routes appear to be manual-queue, not table-configured). The "no QAS"
conclusion rests on: no system described as QAS + no route chain + the documented Two-System operating model + the
recovery treating it as dev↔prod. If JP wants to use one of V01/TS1/TS3 as a QAS, confirm its intended role first.

## AI Diligence Statement

| Element | Detail |
|---|---|
| **AI Role** | Claude ran the read-only landscape probe (`probe_landscape_readonly.py`) and interpreted TMSCSYS/TMSCROUTE/TMSCDOM/E070. |
| **Model** | Claude Opus 4.8 (1M context) — via Claude Code CLI. |
| **Human Role** | JP directed "start with #0 and finish." |
| **Verification** | `[VERIFIED]` live RFC_READ_TABLE on D01 2026-06-15: 7 systems / DOMAIN_P01 / basis 7.50 / 29,408 released vs 511 open / TMSCROUTE empty. `[INFERRED]` the specific role of V01/TS1/TS3 (parked). |
| **Accountability** | JP Lopez maintains full responsibility for decisions based on this output. |
