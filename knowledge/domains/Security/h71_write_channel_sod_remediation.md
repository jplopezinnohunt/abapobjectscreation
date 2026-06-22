---
name: PMO H71 — Write-channel Segregation-of-Duties (SoD) finding + remediation
description: The portal-as-user RFC/BAPI write channel carries SoD conflicts confirmed at BOTH the behavioral (audit log + change docs + posted documents) and the declared (AGR role) level. Conflict 1 = Brasília AP self-approves the 3-way match (R$ 264.7M); Conflict 2 = HQ ICTP controls vendor master + PR + PO (EUR ~11.8M). Root structural weakness: S_RFC=* + custom BAPIs that skip standard authorization. Control must live at the call/data layer, not the dialog/role layer. 2026-06-22.
type: project
domain: Security
related: [system_operating_model_rfc.md, claim_213, claim_6]
---

# PMO H71 — Write-Channel SoD: confirmation, $ exposure, control design

**Date:** 2026-06-22 · **Status:** ANALYSIS COMPLETE (a+b done; c designed) · **Severity:** 🔴 CONTROL
**Extends:** claim #213 (dialog SoD, audit log) + claim #6 (BCM dual-control) to the **integration write channel**.
**Evidence base:** `rsau_audit_history` (P01 audit log, 15.6M rows Feb–Jun 2026), `cdhdr_history` (change docs),
`rbkp`/`rseg`/`ekbe`/`bsak` (posted documents), and a **live P01 pull of `AGR_USERS` + `AGR_1251`** (role data,
previously not in the Gold DB → now `agr_users` + `agr_1251_sod`). Extraction: `Zagentexecution/tasks/2026_06_22_h71_sod_write_channel/`.

## Why this is the control that matters
UNESCO's P01 is **operated by integration, not dialog** — 80.6% of business RFC is driven by external satellites
(`system_operating_model_rfc.md`). Transaction + master-data WRITES enter through a **"portal-as-user" channel**:
ORION EAI (`HQ-ORION-EAI01/03/04`) calls standard + custom BAPIs **under the named user's SAP ID**. So the place a
fraud control must sit is this channel — dialog SoD is the minority. This finding is the conformance focus for the
write side.

---

## (a) CONFIRMATION — behavioral AND declared (role) evidence

Two independent layers agree. The **behavioral** layer (what they DID) and the **declared** layer (what their roles
AUTHORIZE) both confirm the conflict — and the role pull added precision (change vs display) and exposed a deeper hole.

### Conflict 1 — 3-way-match self-approval (Brasília AP / office BRB)
Four users post **both** the goods receipt **and** the vendor invoice — they alone complete the 3-way match
(PO = GR = Invoice) that is supposed to require ≥2 people.

| User | BAPI_GOODSMVT_CREATE (GR) | BAPI_INCOMINGINVOICE_CREATE1 (IV) | window |
|---|---|---|---|
| **E_SILVA**  | 1,774 | 1,738 | 2026-03-09 → 06-19 |
| **L_NEVES**  | 1,487 | 1,479 | 2026-02-23 → 06-19 |
| **C_SOUZA**  |   56  |   56  | 2026-03-30 → 04-02 |
| **B_LOPES**  |    1  |    1  | 2026-03-19 |

> The task named E_SILVA + L_NEVES; the audit log shows **C_SOUZA and B_LOPES also call both** — the conflict
> population is 4, not 2. All four operate via ORION (function groups `MB_BUS2017` = GR, `MRM_BAPI` = invoice).

**Declared (AGR roles):** all four hold the **same `Y_UBO_*` Brasília bundle (54 roles; L_NEVES 49 = subset)**.
Activity-level (`AGR_1251.ACTVT`) confirms the grants are **change/create, not display**:
- **GR = create** — `Y_UBO_MM_GOODS_ENTRY` (ACTVT 01/*), `Y_UBO_MM_Y_MIGO` (01/02/03/*).
- **Invoice = create/post** — `Y_UBO_FI_AP_INVOICE_STAFF`, `Y_UBO_FI_GL_POSTINGS` (01/02), `YS:FI:M:AP_ACCOUNT_POST__:UBO` (01), `Y_UBO_MM_INVOICE_RELEASE` (02).
- **PO = create** too — `Y_UBO_MM_CREATE_PO` (01/02/*). So one identity can do **PO → GR → Invoice** end-to-end.
- **Vendor bank data = DISPLAY ONLY** — `YS:CA:D:MD_VNDR_BNK_DATA_:UBO` is ACTVT **03/08** (display + display-change-docs). *The Brasília users canNOT change vendor bank master* — important precision; their conflict is the 3-way match, not vendor redirection.

### Conflict 2 — vendor-master control + spend direction (HQ / ICTP)
Two users change purchase requisitions **and** vendor master **and** purchase orders — they can stand up / redirect a
vendor and then create the requisition+PO that spends to it.

| User | PR changes (BANF) | Vendor changes (KRED) | PO changes (EINKBELEG) | distinct vendors |
|---|---|---|---|---|
| **S_STANTIC** | 60,389 | 6,972 | 2,710 | 4,079 |
| **MP_ANCUTA** | 16,769 | 1,999 |   544 | 1,316 |

(`cdhdr_history`, Feb–Jun 2026. Audit log corroborates: `BAPI_PR_CHANGE` 30,101/7,146; `ZBAPI_VENDOR_CHANGE` 19,481/4,683.)

**Declared (AGR roles):** `Y_ICTP_*` bundle.
- **MP_ANCUTA** — `Y_ICTP_SIS` grants **VENDOR create/change (ACTVT 01/02/03)** + **PR create/change** + **PO create/change**. Fully declared.
- **S_STANTIC** — PR/PO/invoice change declared (`Y_ICTP_ALH`/`I50`/…), but **NO standard `F_LFA1_*` (vendor) grant at all** — yet she changed vendor master 6,972×. ⇒ see the structural hole below.

### Cross-cutting ROOT WEAKNESS — the call layer is wide open
- **`S_RFC = '*'`** on `Y_ICTP_COMMON` (held by **both** MP_ANCUTA and S_STANTIC) and on `Y_UBO_ADMINISTRATION`
  (all four Brasília users **and `UBO-RFC`**). Every portal user can call **any** RFC-enabled function module.
- Therefore SoD cannot be enforced at the function-call layer — it depends entirely on whatever each BAPI checks
  **internally**, and those checks are inconsistent.
- **Proof the custom path skips authorization:** S_STANTIC changed 6,972 vendors with **`S_RFC=*` but no `F_LFA1`**.
  ⇒ the custom **`ZBAPI_VENDOR_CHANGE`** (func group `ZFI_VENDOR_MGMT`) performs **no vendor-master AUTHORITY-CHECK**;
  it relies on call-authority alone. A role-only split of `F_LFA1` would be **cosmetic** — the custom BAPI ignores it.
- **`UBO-RFC`** (technical service account) posts FI via `Y_RFC_FMRP_RFFMEP1FX_FI_POST` (30,738×) and carries
  `Y_UBO_ADMINISTRATION` (S_RFC=*) — a service identity with broad post capability and universal call rights.

---

## (b) $ EXPOSURE — BAPI activity joined to posted documents

### Conflict 1 — self-approved 3-way-match throughput (Brasília, BRL)
Attribution link verified: `RBKP.USNAM` / `BKPF.USNAM` = these portal users (E_SILVA posted 16,285 invoices /
41,817 FI docs). Currency is **99.9% BRL** (TCODE MIRO) — this is UNESCO **Brasília**.

| Measure | Value |
|---|---|
| Logistics invoices posted by the 4 users (full history 2024-01 → 2026-04) | **20,573** |
| **Invoice value (RBKP.RMWWR, BRL)** | **R$ 264,658,831** (≈ **US$ 49.0M** @ 5.4) |
| Distinct POs they invoiced | 9,411 |
| Of those POs, share with a goods receipt (EKBE VGABE=1) | **100%** — every one is a real 3-way match |
| Windowed lower bound (BUDAT ≥ 2026-02-23; RBKP extract ends 2026-04-30, so May–Jun missing) | ≥ R$ 24,973,846 |

**Interpretation:** R$ 264.7M of logistics spend flowed through a channel where the 3-way-match control could be, and
behaviorally was, satisfied by a single identity. (Residual: proving GR and IR on the *same PO* were posted by the
*same* user needs `MSEG.USNAM`, which is not extracted — MSEG/MKPF absent from the Gold DB. The capability + dual
activity are confirmed; same-document self-match is the one un-extracted link. Tracked as a follow-up pull.)

### Conflict 2 — spend directable to controlled vendors (HQ, EUR)
The vendors these two users maintain are the **`VS9…` account-group** (a portal-managed range, distinct from the
classic numeric LIFNR). Joining the controlled-vendor set (CDHDR KRED OBJECTID) to AP postings:

| Source | Lines | Amount | Distinct controlled vendors |
|---|---|---|---|
| **BSAK (cleared AP, DMBTR local cur)** | 15,318 | **≈ EUR 11,775,875** | 2,137 |
| BSIK (open AP) | 173 | EUR 95,511 | 83 |
| RBKP (MM invoices, EUR) | 4,718 | EUR 1,538,990 | 1,984 |
| EKPO (PO commitments, EUR) | 5,543 POs | EUR 2,985,416 | — |
| *context: all VS9 vendors (cleared)* | — | EUR 23,689,149 | — |

**Interpretation:** **~EUR 11.8M of cleared AP (≈ half of all VS9-vendor spend) went to the 2,137 vendors whose master
data was changed by the same two users who also create/change the requisitions and POs.** They additionally control
the forward pipeline (77,158 PR changes between them). (DMBTR is company-code-local currency, predominantly EUR for HQ
vendors; mixed-CC residual noted.)

---

## (c) CONTROL DESIGN — enforce SoD at the CALL/DATA layer, not the role layer

The defining constraint: writes arrive through ORION as BAPIs under the user's ID with `S_RFC=*`, and at least one
custom BAPI ignores standard auth. **So a role split alone is bypassable.** The control must be layered, and the
preventive layers must be SAP-side (so they hold no matter which channel writes).

**1. Detective (now — zero build).** Run this SoD report monthly from `rsau_audit_history` + `cdhdr_history` (the
pipeline already exists). Flag any identity exercising both sides of a conflict; review the $ via RBKP/BSAK. This is
the immediate compensating control while the preventive ones are built.

**2. Foundational — close the call layer (highest leverage).**
   - **Eliminate `S_RFC='*'`** on `Y_ICTP_COMMON`, `Y_UBO_ADMINISTRATION` (and any role). Replace with explicit
     function-group allow-lists per role. Until this is done, no role-level SoD is enforceable on the write channel.
   - **Add `AUTHORITY-CHECK` to the custom write BAPIs** — first `ZBAPI_VENDOR_CHANGE` must check `F_LFA1_AEN`
     (vendor bank/sensitive) + `F_LFA1_GEN`, so the role design actually bites. Audit every `Z*`/`Y*` write BAPI in
     the portal path for missing checks (own-Z-objects only — D01 dev, released transport; BROADCAST-007).

**3. Structural — SAP-native approval steps (the real safeguard; cannot be bypassed by channel).**
   - **Vendor bank data → sensitive-fields dual control (`T055F` + FK08).** Any change to bank account (LFBK) requires
     confirmation by a **second** user before the vendor is usable for payment. Closes Conflict 2's redirection path
     **regardless of who or which BAPI changes it** — this is the single most important fix.
   - **Logistics invoices → payment block + `MRBR` release by a different user than the GR poster.** Closes Conflict 1's
     self-approved 3-way match. (Combine with invoice tolerance/auto-block when GR-user = IV-user.)
   - **PR/PO → release strategy that forbids creator = releaser.** EBAN already carries FRGKZ/FRGDT; verify the strategy
     requires a *different* releaser.

**4. Role redesign (make segregation the default; the approval steps are the backstop).**
   - Conflict 1: split GR roles (`Y_UBO_MM_GOODS_ENTRY`/`Y_UBO_MM_Y_MIGO`) from invoice roles
     (`Y_UBO_FI_AP_INVOICE_STAFF`/`Y_UBO_FI_GL_POSTINGS`/`Y_UBO_MM_INVOICE_RELEASE`). In Brasília all 4 hold both →
     create ≥2 segregated groups (receiving vs AP).
   - Conflict 2: remove vendor-master change (`Y_ICTP_SIS` F_LFA1 02) from identities that also hold PR/PO change;
     move vendor maintenance to a dedicated master-data team.

**Recommended sequence:** 1 (now) → 3a vendor dual-control (fastest high-impact, SAP standard) → 2 (call layer) →
3b/3c invoice & PR/PO release → 4 (role split). Owner: Controls/Treasury + BASIS/Security; D01 dev → released
transport → ATC → JP 4-eyes (BROADCAST-007). UNESCO has no QAS — flag that as the structural risk for these changes.

---

## Provenance / reproducibility
- Behavioral: `rsau_audit_history` (verify: `SELECT SLGUSER,PARAM3,COUNT(*) … TXSUBCLSID='RFC Function Call' …`).
- Change docs: `cdhdr_history` (OBJECTCLAS KRED/BANF/EINKBELEG).
- Posted docs: `rbkp`/`rseg`/`ekbe` (Conflict 1), `bsak`/`bsik`/`ekpo` (Conflict 2). MSEG/MKPF absent (GR-poster link).
- Role data: live P01 `AGR_USERS`/`AGR_1251`/`AGR_AGRS` via `pull_agr_sod.py` → `agr_users`, `agr_1251_sod`, `agr_sod_map.json`.
- **SAP learning:** P01's secured `RFC_READ_TABLE` (SAIS wrapper) **rejects `IN (...)` WHERE lists** ("suspicious WHERE
  condition") — read with **per-value equality loops** (no ROWSKIPS), as the log accumulators do.
