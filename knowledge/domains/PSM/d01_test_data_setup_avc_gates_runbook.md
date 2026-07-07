---
name: D01 test-data setup — make a workplan/WBS GO through BOTH AVC gates (4 cases)
description: Reusable runbook to stand up the test data that lets a cost object (cert / earmarked doc / posting) on a workplan→WBS pass BOTH availability-control engines on D01 (FM-AVC ledger 9H + PS-AVC on the WBS). Four ordered cases — Fund master exists, PS master exists, Top-up Fund (FM budget), PS budget (CJ30→CJ32→CJBV). Anchored on the live-verified 650RER0008 / VNI+HEQ / PR00021132 walkthrough (s-2026-07-03..05).
type: runbook
domain: PSM / Fund_Management / BCS / Project_System
evidence_tier: TIER_1
cross_links:
  - knowledge/domains/PSM/budget_control_system_bcs_domain.md
  - knowledge/domains/PS/ps_availability_control.md
  - knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md
---

# D01 test-data setup — make a workplan/WBS GO through BOTH AVC gates

> **Why this exists.** A cost object coded to a cost-recovery WBS (e.g. cert `0000190` on workplan `016266`
> → `650RER0008 / VNI`) is checked by **TWO availability-control engines simultaneously** — both must pass or
> the create is blocked ([ps_availability_control.md:5](../PS/ps_availability_control.md)):
> - **Gate 1 — FM-AVC** (ledger **9H**), enforced at the **control** address, blocks with `FMAVC0xx`.
> - **Gate 2 — PS-AVC** (on the WBS), blocks with `BP603`/`BP604`.
>
> To make the test "GO", you load budget through 4 ordered cases. **Cases 1–2 are preconditions (verify, create
> only if missing); Cases 3–4 are the budget loads.**

## ⚠️ Critical addressing correction (claim #327, TIER_1, live D01)

A diagram/leaf-level view suggests the FM gate is at **`9H / 650RER0008 / VNI / 13`**. That is the **LEAF** where
the fund's own posting lines sit. **The AVC ledger does NOT enforce at the leaf — it enforces at the CONTROL node,
which for 650RER0008 is `9H / 650RER0008 / HEQ / 11`.** This was revealed live by error **FMAVC015**
("Overall budget exceeded by 1,000.00 USD") naming that exact triple; top-up doc **2000000266** (+100,000 USD at
**HEQ/11/2026**) cleared it.
**Operational rule (generalizes):** when an AVC posting fails with `FMAVC015`/`FMAVC0xx`, **read the control
object DIRECTLY FROM THE ERROR MESSAGE and post budget at THAT address** — never infer the control fund center
from FMIFIIT/FMAVCT leaf rows (they show the fund's postings, not necessarily the enforced node).

## The 4 cases (ordered)

### Case 1 — Fund master data EXISTS (FM master, precondition)
The fund is the FM twin of the PS project: **FINCODE = PSPID**.

| What to verify | Table / key | tcode (display / create) | 650RER0008 value |
|---|---|---|---|
| Fund | `FMFINCODE` (FIKRS+FINCODE) | FM5S / **FM5I** | FIKRS=**UNES**, FINCODE=**650RER0008** |
| Fund center — **leaf** | `FMFCTR` (FIKRS+FICTR) | FMSC / **FMSA** | **VNI** |
| Fund center — **AVC control** | `FMFCTR` | FMSC / FMSA | **HEQ** (VNI rolls up to HEQ) |
| Commitment items | `FMCI` (FIKRS+GJAHR+FIPEX) | FMCIC / **FMCIA** | **11** and **13** |

- If any are missing, create via the proven scripts: `fund_sync.py <TGT>`, `fund_center_sync.py <TGT>`
  (topological — parents first), or the create FMs (`FM_FUND_CREATE_RFC`, `FM_FUNDS_CTR_CREATE_RFC`;
  remember `I_FLG_TESTRUN=' '` and **verify by re-read** — ET_MESSAGES is empty even on real create).
- **`FMFCTR` is SAIS-RFC-blocked (claim #328)** — `RFC_READ_TABLE` on FMFCTR returns a false `TABLE_WITHOUT_DATA`
  for live HEQ/VNI. **Confirm the VNI→HEQ hierarchy via GUI/ADT, not RFC_READ_TABLE.**

### Case 2 — PS master data EXISTS (project structure, precondition)
| What to verify | Table / key | tcode | 650RER0008 value |
|---|---|---|---|
| Project definition | `PROJ` (PSPID) | CJ20N / CJ03 | PSPID = **650RER0008** |
| WBS element | `PRPS` (POSID→OBJNR) | CJ20N / CJ12 | OBJNR = **PR00021132** |
| Budget profile assigned | `PROJ.BPROF` | CJ20N (Control tab) | must be non-blank (enables CJ30/CJ32) |

- If missing, create via `ps_project_sync.py <TGT> <PSPID>` (flat WBS + release via `BAPI_PROJECT_MAINTAIN`;
  nested hierarchy still needs CJ20N — see BCS §5). The WBS **is** the CO object (satisfies KI235; OKB9 is not
  the mechanism). A WBS with no budget profile cannot be budgeted — fix in CJ20N before Case 4.

### Case 3 — Top-up Fund (FM budget, Gate 1)
**Prerequisite (claim #307):** FM budget **version-0 status must be OPEN for FIKRS+year**, or `BAPI_0050_CREATE`
fails "No status assigned to version 0, year <Y>". Open it with tcode **FMBV** for **UNES / 2026** first.

Then post the FM budget **at the CONTROL node** (not the leaf):
- **GUI:** tcode **FMBB** → Process **ENTER**, Budget type **9F/3000**, Document type **2000**, line:
  Fund **650RER0008**, Fund Center **HEQ**, Commitment Item **11**, Year **2026**, amount ≥ cert value → **POST**.
- **RFC (proven):** `BAPI_0050_CREATE` — HEADER `DOCTYPE=2000 / PROCESS=ENTR / DOCSTATE=1 / VERSION=000`,
  **omit PSTNG_DATE** (else "no active budgetary ledger"); ITEM `BUDCAT=9F / BUDTYPE=3000 / VALTYPE=B1 /
  DISTKEY=1 / ITEM_NUM=<string>`; `TESTRUN=' '`; then `BAPI_TRANSACTION_COMMIT`. Wrapper:
  `Y_FMKU_0050_CREATE_WITH_COMMIT`. **Sign convention:** positive input → stored NEGATIVE B1; to REMOVE budget
  post the negative (offset), do NOT use `BAPI_0050_REVERSE` (reversal reasons not active FY2026 — claim #324).
- **Verify:** re-read FMAVCT / FMBL, or just re-attempt the create — FMAVC015 should be gone.

### Case 4 — PS budget (WBS, Gate 2) — CJ30 → CJ32 → CJBV
Classic PS budgeting (KBPP family). **No clean single-call RFC BAPI** (`KBPP_EXTERN_UPDATE` throws DA300 without
the CJ30 buffer) → **GUI**.

1. **CJ30** — enter ORIGINAL/current budget on WBS **650RER0008**, year **2026**, amount ≥ cert value.
   → lands in **`BPJA WRTTP=41`, GJAHR=2026, VERSN=000** (verified: 10,000 USD after CJ30, D01 2026-06-30).
2. **CJ32** — RELEASE the budget **at the ANNUAL level** (select GJAHR=2026 explicitly, not overall).
   → lands in **`BPJA WRTTP=42`**.
3. **CJBV** — **Reconstruct project Availability Control** so the AVC pool reflects the new released budget.
   This is the step the earlier CJ30/CJ32-only attempts were MISSING — without a CJBV reconstruct the
   released budget does not become disponible to the PS-AVC pool, which is the leading hypothesis for
   `KU-2026-CJ32-RELEASE-NOT-LANDING` (CJ32 left WRTTP=42 at 0 / BP604 persisted). **Run CJBV for the project
   after every CJ30/CJ32 change.**
   → verify: BP604/BP603 clears on the create; the WBS pool is positive.

> **Note on cost-recovery WBS:** 650RER0008 carries **0 PS budget in P01 too** — its real coverage is the FUND
> (cost recovery / credit `633CRP9003`), so a `BP604` on D01 is likely a PS-AVC-profile config difference, not a
> genuinely missing budget. CJ30+CJ32+CJBV is the **test-unblock**; the byte-faithful fix is the AVC profile.

## GO check
After all 4 cases: create the cert on workplan 016266 → should clear **both** gates (no FMAVC0xx, no BP603/604)
→ JV post → BOR (the email object). If Gate 1 still fires, re-read the control triple **from the error** and
top up THERE (Case 3 rule). If Gate 2 still fires, confirm CJBV actually ran at the annual level.

## Open known-unknowns (do not re-litigate — park & route around)
- `KU-2026-CJ32-RELEASE-NOT-LANDING` — whether CJBV closes it is to be RUNTIME-VERIFIED on the next execution.
- Programmatic FMBV (open FM version-status per area/year via RFC/config) — unresolved; use the GUI tcode.
- Programmatic BCS reversal-reason customizing (mirrors FMBV) — unresolved; use the negative-offset workaround.
- FMFCTR hierarchy (VNI→HEQ) confirmation via GUI/ADT — RFC_READ_TABLE on FMFCTR is SAIS-blocked (claim #328).
