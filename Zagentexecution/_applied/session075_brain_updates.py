"""Session #075 brain updates — D01 HTTP auth break + cross-project diagnostic."""
import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# === CLAIMS ===
P = 'brain_v2/claims/claims.json'
d = json.load(open(P, encoding='utf-8'))
next_id = max(c['id'] for c in d) + 1
S = 75

d.extend([
    {
        "id": next_id,
        "claim": "D01 HTTP Basic Auth for user jp_lopez broke between 2026-04-10 and 2026-05-13. Same credentials (40-char password from .env) continue to authenticate cleanly via RFC port 3300 (pyrfc) — RFC_READ_TABLE T000 returns 200, all our v6/replay deployments via RFC_ABAP_INSTALL_AND_RUN succeed. Same credentials against HTTP port 80 ICF services (/sap/bc/adt/*, /sap/bc/ui5_ui5/*) return HTTP 401 'Anmeldung fehlgeschlagen' uniformly. Tested across 5 URL variants (DNS uppercase/lowercase/IP/port-explicit/no-sap-client) and 4 ADT endpoints — all 401. Root cause is SAP-side, NOT credentials: candidate causes (in order of likelihood) — SU01 user type changed to Communication/Service (allows RFC, blocks Dialog HTTP), USR02 password buffer desync after rotation (BCODE vs PASSCODE mismatch), or SICF policy hardening (require SAML/SNC instead of Basic).",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "D01 RFC + HTTP empirical test 2026-05-13",
            "cite": "pyrfc T000 read succeeds. urllib + Basic Auth to /sap/bc/adt/discovery returns HTTP 401 in 5 URL variants. Same against ZAW_CRP BSP. Body = SAP Logon Error in German. Last successful HTTP deploy: 2026-04-10 (unescrp S-51).",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["SU01", "USR02", "SICF", "rfc_helpers.py", "sap_adt_client.py", "@sap-ux/deploy-tooling"],
        "domain": "BASIS",
        "created_session": S, "resolved_session": None,
        "resolution_notes": "Open. Diagnosis complete; fix requires BASIS action (SU01 user type / USR02 rotation sync / SICF policy review). Workaround: RFC paths work for all ABAP source ops; BSP deploy needs abapGit pull-from-GitHub.",
        "status": "active",
        "domain_axes": {"functional": ["Infrastructure"], "module": ["BASIS"], "process": []}
    },
    {
        "id": next_id + 1,
        "claim": "Cross-project failure pattern: abapobjectscreation deploys ABAP successfully via RFC (RFC_ABAP_INSTALL_AND_RUN, INSERT REPORT, RPY_PROGRAM_*) while unescrp's frontend BSP deploy fails via @sap-ux/deploy-tooling HTTP. Both projects share same .env credentials, same target (D01/350/jp_lopez). Difference is purely protocol (RFC port 3300 vs HTTP port 80). The unescrp BSP ZAW_CRP exists in TADIR (R3TR WAPA in $TMP package, AUTHOR=JP_LOPEZ) but cannot be updated since the HTTP path is blocked. Last successful BSP deploy: unescrp session S-51 on 2026-04-09/10 via @sap-ux/deploy-tooling. 5 weeks of frontend work (S-58→S-78) may not have reached D01 — needs verification once HTTP is restored. Backend ABAP for unescrp continues to deploy via Python RFC scripts (deploy_*.py) throughout S-60→S-78.",
        "claim_type": "verified_fact", "confidence": "TIER_1",
        "evidence_for": [{
            "type": "production_data",
            "ref": "Cross-project SAP D01 audit 2026-05-13",
            "cite": "TADIR queries: ZAW_CRP in $TMP, backend ZCL_*/Z_CRP_SRV in ZCRP. E070/E071 ZERO transports for WAPA ZAW_CRP. unescrp/brain/sessions/s51-spec-visual-docs-deploy-closing.md last BSP deploy log.",
            "added_session": S
        }],
        "evidence_against": None,
        "related_objects": ["TADIR", "ZAW_CRP", "Z_CRP_SRV", "ZCL_Z_CRP_SRV_DPC_EXT", "WAPA_INDX"],
        "domain": "Payment",
        "created_session": S, "resolved_session": None,
        "resolution_notes": "Diagnosis enables targeted fix path. abapGit pull-from-GitHub recommended for unescrp frontend recovery without waiting for BASIS.",
        "status": "active",
        "domain_axes": {"functional": ["Deployment"], "module": ["BASIS", "CTS"], "process": []}
    }
])
json.dump(d, open(P, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Claims: +2 (id {next_id}, {next_id+1}). Total: {len(d)}")

# === FEEDBACK RULES ===
R = 'brain_v2/agent_rules/feedback_rules.json'
rules = json.load(open(R, encoding='utf-8'))
existing = {r['id'] for r in rules}

new_rules = [
    {
        "id": "feedback_isolate_protocol_before_blaming_credentials",
        "rule": "When SAP auth fails, ALWAYS test the same credentials via both RFC (port 3300) AND HTTP (port 80) before declaring 'password is wrong'. SAP commonly accepts the same user/password on one protocol while rejecting it on another — caused by SU01 user type, USR02 password-buffer desync, or SICF policy. Run the 60-second diagnostic in unescrp/.claude/skills/sap-fiori-react-builder/sap-fiori-react-builder/references/deployment/sap-d01-connection-patterns.md before opening a credentials INC.",
        "why": "Session #075: unescrp project burned 2+ hours assuming the 40-char password was stale, including retrying passwords found in earlier .env snapshots and probing /sap/bc/adt/discovery 6 times. The same password authenticates cleanly via RFC. Root cause is SAP-side ICF/SU01 — none of the client-side fixes would have helped. Isolating protocol vs credentials would have saved the time and triggered the correct BASIS ticket immediately.",
        "how_to_apply": "(1) First failure to authenticate → run RFC probe (pyrfc T000 read). (2) If RFC works → it's not the password; switch to HTTP probe (urllib Basic + ADT discovery). (3) If RFC fails → check .env / VPN / SNC config. (4) If RFC works AND HTTP fails → SAP-side, open BASIS ticket with the diagnostic evidence. Don't keep trying passwords. (5) Document the result in the project's connection-patterns reference file.",
        "severity": "HIGH",
        "created_session": "#075",
        "source_file": "unescrp/.claude/skills/sap-fiori-react-builder/sap-fiori-react-builder/references/deployment/sap-d01-connection-patterns.md",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "session_075_diagnostic_loss",
        "domain_axes": {"functional": ["Infrastructure", "Tooling"], "module": ["BASIS"], "process": ["*"]}
    },
    {
        "id": "feedback_sap_adt_client_silent_401",
        "rule": "Do NOT trust `sap_adt_client.fetch_csrf()` or any `_request()` call as proof of HTTP auth success. The current `_request` implementation catches `urllib.error.HTTPError` and returns `(status, body, headers)` without raising — and SAP echoes a CSRF token even on 401 when `X-CSRF-Token: Fetch` is sent. Always assert `status == 200` after the call. Patch `_request()` to raise on 4xx, or replace the client with one that propagates errors.",
        "why": "Session #075: I told the user 'ADT HTTP works' based on `fetch_csrf()` returning normally, then realized the client silently swallowed the 401 and returned an empty token. The mistake cost trust and required a public correction. The bug has likely caused false positives in other sessions where ADT 'success' messages preceded mysterious downstream failures.",
        "how_to_apply": "(1) When calling sap_adt_client methods, check the returned status code explicitly, not just whether a value came back. (2) Add a fix to `_request`: `if status >= 400: raise HTTPError(...)`. (3) Same patch needed for fetch_csrf, search_object, get_source, etc. (4) Until patched, run a separate `urllib.request.urlopen` probe to confirm 200 before trusting the client.",
        "severity": "MEDIUM",
        "created_session": "#075",
        "source_file": "Zagentexecution/mcp-backend-server-python/sap_adt_client.py",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "session_075_silent_bug",
        "domain_axes": {"functional": ["Tooling"], "module": ["BASIS"], "process": ["*"]}
    },
]
added = 0
for nr in new_rules:
    if nr['id'] not in existing:
        rules.append(nr)
        added += 1
        print(f"  + rule {nr['id']}")
    else:
        print(f"  = rule {nr['id']} (skip)")
json.dump(rules, open(R, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Rules: +{added}. Total: {len(rules)}")
