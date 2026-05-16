# Session #75 Retro — D01 HTTP Auth broken cross-project (unescrp deploy diagnosis)

**Date:** 2026-05-13 → 2026-05-14
**Duration:** Short focused session, post-#074 close
**Focus:** Confirm D01 connectivity (✓ RFC works). Diagnose why unescrp's `@sap-ux/deploy-tooling` deploy returns HTTP 401. Compare working RFC path vs broken HTTP path. Update both project skills with current state.

---

## 1. Context

User asked me to evaluate why their **unescrp** project (separate UNESCO CRP Fiori app) cannot deploy to D01 while my **abapobjectscreation** project keeps deploying ABAP successfully. Both projects target the same SAP system (D01, client 350, user `jp_lopez`) with the same 40-character password in their respective `.env` files.

Investigation arc:
- "podes confirmar la lectura de SAP D01 esta funcionando" → ✓ RFC reads working
- "ayudame a evaluar porque unescrp no puede conectar" → Diagnosed: HTTP 401, same creds work for RFC
- "tendriamos que actualizar el skill que usa la app de CRP" → Updated unescrp skill
- "ccon todo tu conocimiento de conexion" → Wrote `sap-d01-connection-patterns.md`
- "pero vos sos capaz de hacer delivery the objectos abap usando ADT" → Corrected myself: actually ADT/HTTP is ALSO 401 today in abapobjectscreation; our recent deploys went through RFC (RFC_ABAP_INSTALL_AND_RUN), not ADT. Updated `sap_adt_api` skill with warning.
- "o sea que no se puede entregar el BSP?" → Yes can, via abapGit pull-from-GitHub or Playwright SAP GUI passthrough.
- "Podes analizar como lo entrego la utlima vez ya que yo no lo hice" → Traced last successful BSP deploy: S-51 (2026-04-09/10), 5 weeks ago, via `@sap-ux/deploy-tooling`. BSP `ZAW_CRP` lives in `$TMP` package (never transported). All frontend work S-58→S-78 may not have reached D01.

---

## 2. Delivered this session

### unescrp skill update
- New reference: `unescrp/.claude/skills/sap-fiori-react-builder/sap-fiori-react-builder/references/deployment/sap-d01-connection-patterns.md`
  - 3 working patterns: RFC / abapGit pull / Playwright SAP GUI passthrough
  - 5 failure patterns documented (incl. `@sap-ux/deploy-tooling`, manual urllib, ADT HTTP, hostname variants, password rotation)
  - 60-second diagnostic script
  - SAP-side root-cause candidates (SU01 user type, USR02 buffer mismatch, SICF policy, Web Dispatcher)
  - BASIS ticket template

### abapobjectscreation skill update
- `.agents/skills/sap_adt_api/SKILL.md` — added warning banner: "STATUS 2026-05-13 — D01 HTTP/ADT IS RETURNING 401 FOR jp_lopez". Added RFC alternative table for every previously-recommended ADT operation. Documented the silent-401 bug in `sap_adt_client.py::_request` (catches HTTPError, returns empty CSRF without flagging caller).

### Empirical evidence gathered
- `pyrfc.Connection` to D01 port 3300 with `.env` password → ✓ T000 read works
- `urllib` Basic Auth to D01 port 80 `/sap/bc/adt/discovery` → ✗ HTTP 401 in 5 URL variants tested (DNS uppercase/lowercase, IP, port 80 explicit, no port, no sap-client)
- `sap_adt_client.fetch_csrf()` appears to "work" but actually returns empty token — `_request()` swallows HTTPError silently
- All 4 ADT endpoints tested (`/sap/bc/adt/discovery`, `/sap/bc/adt/programs/includes/LYFPAYMU19/source/main`, `/sap/bc/adt/functions/groups/SAPLYFPAYM`, `/sap/bc/adt/functions/groups/SAPLYFPAYM/fmodules/Y_FI_DMEE_ADR/source/main`) → all 401

### unescrp deployment archaeology
- TADIR query: BSP `ZAW_CRP` is `R3TR WAPA` in `$TMP` package, AUTHOR=`JP_LOPEZ`. 2 SICF nodes also in `$TMP`.
- E070/E071: ZERO transports touching `WAPA ZAW_CRP` in transport history. The `D01K9B0F6A`/`D01K9B0F6E` transports cited in S-51 retro do not exist in E070 today — they were workbench TRs for supporting backend, not the BSP itself (BSP being in $TMP cannot be transported).
- Backend ABAP (`ZCL_Z_CRP_SRV_DPC_EXT`, `ZCL_CRP_PROCESS_REQ`, `Z_CRP_SRV`) lives in `ZCRP` package and continues deploying via Python RFC `deploy_*.py` scripts throughout S-60 → S-78.
- **Last successful BSP HTTP deploy: 2026-04-09/10 (S-51).** 5 weeks of frontend changes (S-58 → S-78) may not have reached D01.

---

## 3. SAP learnings — Phase 4b

1. **D01 HTTP Basic Auth broke between 2026-04-10 and 2026-05-13** for user `jp_lopez`. Same credentials authenticate via RFC (port 3300) but get 401 via HTTP (port 80) ICF services. Cause likely server-side: SU01 user type change, USR02 password-buffer desync after rotation, or SICF policy tightening (now requires SNC/SAML instead of Basic). Not a credentials problem.

2. **`@sap-ux/deploy-tooling` deploys directly to BSP runtime, not via transport.** When BSP is in `$TMP` package (as ZAW_CRP is), the tool uploads files into runtime tables (WAPA_INDX) but does not create or use E070/E071 transports. The "transport" returned in the deploy log may refer to a workbench TR for supporting objects, not the BSP itself.

3. **`WAPA_INDX`, `WAPA_RTC`, `/UI5/UI5_REP_CONTENT`, `/UI5/UI5_REP_HEAD` are NOT remotely-readable tables** via RFC_READ_TABLE — they return `TABLE_NOT_AVAILABLE`. To audit BSP content you need either (a) ADT HTTP (currently 401), (b) SAP GUI in browser, or (c) `RPY_BSP_PAGE_INSERT`/READ RFC family for classic BSPs (does not work for UI5 Repository BSPs).

4. **`sap_adt_client.py::_request` has a silent-401 bug.** The `except urllib.error.HTTPError` branch returns `(status, body, headers)` without raising. Callers that only check `if self._csrf_token` are misled — SAP echoes a CSRF token even with 401 if `X-CSRF-Token: Fetch` header is sent. Patch needed: raise on 4xx in `_request` or have `fetch_csrf` check `status == 200` explicitly.

5. **Cross-project diagnostic pattern.** When two projects share the same SAP target and one works while the other fails, isolate the protocol (RFC vs HTTP vs HTTPS vs Web Dispatcher) before blaming credentials or code. Same user, same password can succeed on one protocol and fail on another due to SAP-side ICF / SU01 configuration differences.

6. **TADIR `$TMP` is not just a housekeeping concern.** A BSP in `$TMP` means deploy tools cannot move it to a real package without manual SE80 intervention, and crucially the BSP cannot be transported to QAS/PRD. The unescrp BSP has lived in $TMP since S-51's investigation discovered it — P-15 still open.

---

## 4. Open follow-ups carry to next session

1. **Decide deploy path for unescrp**: A (abapGit pull-from-GitHub, 2-3h to migrate), B (BASIS ticket to fix HTTP Basic), or C (both in parallel). User has not yet committed to a path.
2. **Patch silent-401 bug in `sap_adt_client.py`** — `_request()` should raise on 4xx, or `fetch_csrf()` should check status before declaring success.
3. **Verify whether unescrp frontend S-58→S-78 changes ever reached D01** — needs either GUI session diff or BASIS-restored HTTP access.
4. **BASIS ticket** with the evidence pack from `sap-d01-connection-patterns.md` (template included).
5. **abapGit verification on D01**: confirm whether `ZAGAPI`/`ZABAPGIT` is installed and RFC-callable for the pull-from-GitHub path.

---

## 5. Status & Resolution

User said "cerremos la session ya fue resuelto" — the diagnosis itself was the deliverable. Path forward is the user's choice (A/B/C). Both project skills updated. No code changes deployed. RFC channel verified healthy.
