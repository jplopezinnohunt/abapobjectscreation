# Session #056 Retro — Integration-element forensic audit + live P01 probe

**Date**: 2026-04-16
**Driver**: User flagged shallow integration inventory ("EACH integration must have the details behind"). Forced a forensic pass with live `RFC_READ_TABLE` probes on D01 and P01. Surfaced major corrections to prior memory, a new integration (UNESCORE Identity Manager), and an ops finding (9,242 failing PROJECT02 IDocs on P01).

---

## 1. What the session delivered

### New memory
| Artifact | Purpose |
|---|---|
| `memory/project_integration_elements_gap.md` | 19-integration inventory with real SAP elements (RFCDEST, IDoc type, program+variant, FMs, DBCON). Tier per integration. Explicit KNOWN vs UNKNOWN list. |
| `Zagentexecution/mcp-backend-server-python/probe_p01_integration.py` | Reproducible P01 probe — MULE_PROD partner profile (EDP13/EDP21), EDIDC traffic, DBCON, SM58 state |
| `Zagentexecution/mcp-backend-server-python/probe_bor_caller.py` | BOR-caller hunt — TADIR/TFDIR/WBCROSSGT scan for custom BOR/SALESFORCE/SFDC/MULE objects |

### Skill updated
`.agents/skills/sap_interface_intelligence/SKILL.md` — new "Session #055 Integration Element Audit" section with:
- No-GUI equivalents table (SM58/SMQ1/WE02/WE20/WE21/SICF/DBCON)
- IDoc status code reference
- EDIDS status-trail detective pattern
- `RFC_READ_TABLE` quirks on P01 (DATA_BUFFER_EXCEEDED, OPTION_NOT_VALID on TADIR OR/parens)
- D01 ≠ P01 partner-profile divergence warning

### ABAP source extracted (5 programs via pyrfc `SIW_RFC_READ_REPORT`)
| Program | What it does |
|---|---|
| `YFI_COUPA_POSTING_FILE` | `YCL_FI_COUPA_ACCOUNTING_LOAD` generates SAP standard RFBIBL00 batch input from COUPA files |
| `YHR_SF_EXPORT_GEODIS` | SuccessFactors Geographical Distribution CSV export (`YCL_SF_EXPORT_GEODIS`) |
| `YHR_SF_EXPORT_ORGANIZATION` | SuccessFactors org structure CSV export (`YCL_SF_EXPORT_ORGANIZATION`) |
| `YHR_MANAGER_FROM_TULIP_UPDATE` | Pulls manager data from Tulip HR DB via DBCON, updates SAP HR |
| `YHR_CREATE_MAIL_FROM_UNESDIR` | Reads UNESCO AD, updates PA0105 subtype 0010 (work email) |

### Live-probe discoveries (P01)

| Discovery | Evidence |
|---|---|
| **9,242 PROJECT02 IDocs stuck at status 29 (ALE error)** on P01 → MULE_PROD | `EDIDC` WHERE `RCVPRN = 'MULE_PROD' AND MESTYP = 'PROJECT'` = 9,242. Latest DOCNUM 4143503 by user M_SARMENTO-G 2025-11-12. Status trail `01 → 29`. |
| **P01 partner profile ≠ D01 profile** for MULE_PROD | P01 EDP13 outbound: PROJECT/PROJECT02, FUNDSCENTER, SYNCH. D01 EDP13: ALEAUD, DEBMAS, FUNDSCENTER, SYNCH. EDP21 inbound same: ADRMAS/ADR2MAS/ADR3MAS/DEBMAS. |
| **SISTER DBCON is D01-only, not P01** | P01 DBCON = 2 entries (TULIP, UNESDIR). D01 had 5 (incl. SISTER, SISTER41, ZTESTNME). SISTER production = RFC-only. |
| **`MULESOFT_PROD` RFCDEST is a stub** | RFCOPTIONS lacks `H=` host — cannot route outbound HTTP. |
| **UNESCORE = Identity Manager** (new integration #19) | User correction, then verified: `svc-prod-role.hq.int.unesco.org:80`, GUID SOAMANAGER logical port `005056BE59091ED9BEFB8CB619545146`, consumed by `Y_UNESCORE_BAPI` FG (4 BAPIs `FUND_GET_LIST`, `FUND_CENTER_GET_LIST`, `PROJECT_GET_LIST`, `WBS_ELEMENT_GET_LIST`) for fund/project authorization mapping |
| **Salesforce BOR has zero SAP custom footprint** | 0 hits in TADIR/TFDIR for BOR/SALESFORCE/SFDC/MULE names. 0 WBCROSSGT refs to MULESOFT_PROD. Conclusion: MuleSoft pulls from SAP, pushes to SF from its own runtime. |

### Corrections to prior memory
- SuccessFactors **is LIVE** (was "planned, not live") — jobs `INTERFACE_SF_EMPLOYEE/ORGANIZATION/GEODIS` run 16+ times
- GEODIS = **SuccessFactors Geographical Distribution**, not logistics
- SISTER is **RFC-only in production** (not dual-channel)
- UNESDIR is **SQL-direct via DBCON** (not HTTP)
- UNESCORE = **Identity Manager** (not Core Manager)
- My earlier Gold DB read of "4,420 PROJECT02 → MULE_PROD" was a mis-parsed GROUP BY; real live count is 9,242

### PMO updates
- **H52** opened mid-session ("Integration-element audit"). Updated with live-probe closure notes. Remaining unknowns: .NET `Web.config` → FM caller map (7 apps), COUPA file schema (inside `YCL_FI_COUPA_ACCOUNTING_LOAD`), UNJSPF SOAP payload, SF BOR MuleSoft iflow listing, resolution of the 9,242 stuck IDocs.
- **H53** (HR COBL fund types) added by user separately.

---

## 2. Phase 4b — SAP learnings captured

- **IDoc status 29 is a silent trap.** A broken ALE channel piles failed IDocs in EDIDC with no SM58 trace (status 29 is a synchronous ALE failure, not a queued tRFC entry).
- **EDP13 ≠ EDP21 ≠ EDIDC.** All three must be checked — a partner profile entry does not guarantee real traffic, and real traffic can exist without a matching profile (custom programs bypass).
- **RFC_READ_TABLE has three Ws** on P01: **W**ider-than-512-char concat fails (DATA_BUFFER_EXCEEDED), **W**HERE with OR/parens fails (OPTION_NOT_VALID), **W**rong field name (`IDOCTYP` vs `IDOCTP`). For any wide or permission-sensitive table (TADIR, TFDIR, EDIDC, ARFCSSTATE), single-condition + narrow FIELDS is the only reliable form.
- **`svc-prod-role` hostname → UNESCORE**. When a GUID-named G-type RFCDEST points to `svc-prod-role...`, it's a SOAMANAGER logical port to an identity/role system.
- **An RFCDES entry without `H=` host is dead on arrival** (stub).
- **Default `.env` points to D01**, not P01. P01 requires prefixed `SAP_P01_*` vars + SNC partner `p:CN=P01`. Confirm `STFC_CONNECTION → Sysid: P01` before claiming prod truth.

---

## 3. Candidate behavioural rule (for next session)

`feedback_confirm_system_before_claiming` (HIGH, derives from CP-003):
> Before claiming any fact about production, call `STFC_CONNECTION` and verify `Sysid` matches the expected system. Never generalize a D01 finding to P01.
>
> **Why**: Two factual claims this session (D01 partner profile, D01 DBCON list) were wrongly stated as P01 truth. Only a second round of probing caught it.
>
> **How to apply**: Every probe script starts with `print('OK:', conn.call('STFC_CONNECTION', REQUTEXT='ping')['RESPTEXT'][:80])`. Include target Sysid in the first line of any integration-related output.

---

## 4. Items at close

| Metric | Value |
|---|---|
| PMO H open before session | 14 |
| PMO H open after session | 15 (+H52, +H53, -0 closed) |
| PMO total | 48 |
| Reward function (items_shipped − items_added) | -2 |

Net-negative on reward. Justification: the two added items (H52, H53) are **forensic gaps previously hidden**. Surfacing them is a CP-001 win ("never sacrifice traceability for velocity"). Not a process failure — the items already existed as unknowns, now they're explicit.

---

## 5. Commit scope

- `memory/project_integration_elements_gap.md` (new)
- `.agents/skills/sap_interface_intelligence/SKILL.md` (appended "Session #055 Integration Element Audit" section)
- `.agents/intelligence/PMO_BRAIN.md` (H52 detail + counts)
- `Zagentexecution/mcp-backend-server-python/probe_p01_integration.py` (new)
- `Zagentexecution/mcp-backend-server-python/probe_bor_caller.py` (new)
- `knowledge/session_retros/session_056_retro.md` (this)

Brain rebuild: deferred — user closed with "update skills", not "rebuild brain". Will rebuild on next session start if stale.
