"""Add session #76 rules + claims to brain JSON files. Idempotent."""
import json
import sys
import os

# Run from project root
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ============================================================================
# 1. Add 4 feedback rules
# ============================================================================
with open("brain_v2/agent_rules/feedback_rules.json", encoding="utf-8") as f:
    rules = json.load(f)
print(f"Rules before: {len(rules)}")

new_rules = [
    {
        "id": "feedback_no_menus_when_decision_is_clear",
        "rule": "When prior analysis has converged on an obvious recommended path AND the user signals agreement (OK/si/dale/proceed), do NOT present a 3-option AskUserQuestion menu. Execute the recommendation directly. The agent OWNS the technical decision.",
        "why": "During session #076 ADT expansion, after a long analysis that converged on Build now + BASIS ticket in parallel, I still presented a 3-option menu. User rejected the tool use and said OK proceed im not sure what you need from basis. Menus are friction when path is obvious. Reinforces existing rule feedback_own_the_decision_stop_asking.",
        "how_to_apply": "1. If my prior message ended with clear recommendation + user agrees (OK/si/dale/proceed), do not present options. Execute.\n2. Reserve AskUserQuestion for genuinely-equivalent-tradeoff cases or when user has not yet given any signal.\n3. When the user signals lack of context (not sure what X means), do NOT ask them to choose - give them what they need or just decide for them and explain.\n4. If I find myself drafting an AskUserQuestion after a long analysis, delete it and proceed.",
        "severity": "HIGH",
        "created_session": 76,
        "source_file": "feedback_no_menus_when_decision_is_clear.md",
        "derives_from_core_principle": "CP-001",
        "cp_derivation_method": "explicit_session_076",
        "domain_axes": {"functional": ["*"], "module": ["*"], "process": ["*"]},
    },
    {
        "id": "feedback_verify_capabilities_before_recommending",
        "rule": "Before recommending any SAP capability (ADT endpoint, BAPI, RFC FM, transaction availability), VERIFY it exists on the target kernel via empirical probe. SAP NetWeaver capabilities differ across releases - what works in S/4HANA / NW 7.5x may be 404 on UNESCO ECC 6.0 EhP8 (NW 7.40). Never assume kernel-uniform.",
        "why": "Session #076 violation: I confidently recommended ADT REST define_table / create_index as the canonical DDIC path, including copy-paste prompts for the parallel unescrp conversation. Then user tested empirically and confirmed /sap/bc/adt/ddic/tables returns HTTP 404 on D01 (NW 7.40) - endpoint shipped in NW 7.50. ~400 lines of code became S/4HANA scaffolding, cross-project recommendation had to be retracted before being applied.",
        "how_to_apply": "1. Before recommending an ADT method, call adt_discovery() and grep the response for the relevant collection. If endpoint absent, the method will 404 - recommend RFC alternative instead.\n2. Before recommending a BAPI / RFC FM, run RFC_READ_TABLE FROM TFDIR WHERE FUNCNAME EQ name to confirm availability.\n3. Before recommending a transaction, verify via TSTCT or quick GUI probe.\n4. UNESCO landscape baseline: ECC 6.0 EhP8 = NW 7.40. Treat any capability described as NW 7.5+ or S/4HANA-only as unavailable until proven otherwise.\n5. When recommending a path that crosses kernel versions, be explicit about version requirement IN THE RECOMMENDATION.\n6. When a recommendation is later proven wrong by empirical evidence, revise the related memory rules IMMEDIATELY and acknowledge the error directly - no softening.",
        "severity": "HIGH",
        "created_session": 76,
        "source_file": "feedback_verify_capabilities_before_recommending.md",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "explicit_session_076",
        "domain_axes": {"functional": ["*"], "module": ["*", "BASIS"], "process": ["*"]},
    },
    {
        "id": "feedback_new_objects_only_in_d01_never_p01",
        "rule": "For ANY new ABAP/DDIC object work (create table, DE, domain, class, program, FM, index, etc.), the agent works EXCLUSIVELY in D01. NEVER touches P01 - not for write, not for read, not for preflight, not for does this exist. The only legitimate P01 read in a creation context is post-transport verification.",
        "why": "Session #076 violation: I called from_env(P01) and ran RFC_READ_TABLE FROM DD02L WHERE TABNAME='ZCRP_CERTHEAD' to triple-confirm the table doesn't exist there. The check was logically unnecessary - by the transport model, if it doesn't exist in D01 it cannot exist in P01 - and crossed a boundary the user explicitly maintains. User response in CAPS: PARA NUEVOS OBJETOS LO HACEMOS EN D01!!! NUNCA P01. This rule is STRICTER than the broader no-prod-writes rule.",
        "how_to_apply": "1. When the user mentions creating/modifying/deploying a new ABAP/DDIC object: pin the system as D01 only. Do not call from_env(P01).\n2. For preflight of objects related to a new creation, query D01 only.\n3. The only legitimate P01 read in a new-object context is post-transport verification - prefer STMS over RFC.\n4. If user explicitly requests a P01 probe for some OTHER reason (incident, data extraction, customizing read), that is allowed under standard no-prod-writes rule.\n5. If unsure whether request is new-object work or diagnosis work, ASK before touching P01.",
        "severity": "CRITICAL",
        "created_session": 76,
        "source_file": "feedback_new_objects_only_in_d01_never_p01.md",
        "derives_from_core_principle": "CP-001",
        "cp_derivation_method": "explicit_session_076",
        "domain_axes": {"functional": ["*"], "module": ["*", "BASIS", "CTS"], "process": ["*"]},
    },
    {
        "id": "feedback_adt_first_kernel_qualified",
        "rule": "ADT-first is qualified by kernel + object class. SOURCE CODE objects (PROG/CLAS/INTF/FUGR/FUNC/INCLUDE/ENHO/XSLT/BSP) - ADT-first on ALL kernels including EhP8. DDIC objects (TABL/DTEL/DOMA/INDX) - ADT-first ONLY on NW 7.50+ / S/4HANA. On EhP8 (UNESCO D01/P01) DDIC creation MUST use the DDIF wrapper (sap_adt_client.define_table_via_ddif / define_data_element_via_ddif / define_domain_via_ddif) with TR_TADIR_INTERFACE injection and verify_tadir post-check.",
        "why": "Session #076: I originally saved a rule ADT-first for ALL DDIC, generating ABAP programs that call DDIF_*_PUT is forbidden as architecture. Empirical probe revealed ADT REST /sap/bc/adt/ddic/tables returns HTTP 404 on NW 7.40 - endpoint shipped in NW 7.50. So on EhP8 the DDIF_*_PUT via RFC_ABAP_INSTALL_AND_RUN pattern is NOT debt - it is the only path. Pain points (opaque RC=2, IN-list parser bug, TADIR-orphan) are real and mitigated by the wrapper, not avoided. The original rule overgeneralized and had to be corrected.",
        "how_to_apply": "1. Before any DDIC create/modify, call adt_discovery() once and grep for the endpoint. If absent, fall back to the DDIF wrapper (NEVER to ad-hoc programs without preflight + TADIR fix).\n2. For SOURCE CODE work, default to ADT REST.\n3. When reviewing legacy projects for RFC_ABAP_INSTALL_AND_RUN + DDIF_*_PUT patterns on EhP8, do NOT mark them as debt - verify they implement preflight + TR_TADIR_INTERFACE + structured-error mitigation. If they do, the pattern is correct; if not, refactor to the wrapper, do not switch to ADT (which would fail).\n4. Track the S/4HANA migration: when UNESCO upgrades, flip DDIC operations to the ADT methods (already scaffolded) - field-list and return-dict shape are identical.\n5. DDIC creation order (both paths): Domain - Data Element - Table - Index. Validate prerequisites before each create.",
        "severity": "HIGH",
        "created_session": 76,
        "source_file": "feedback_adt_first_no_abap_program_generators.md",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "explicit_session_076",
        "domain_axes": {"functional": ["*"], "module": ["*", "BASIS", "CTS"], "process": ["*"]},
    },
]

# Idempotent: remove any prior version of these rules by id, then re-add
existing_ids = {r["id"] for r in new_rules}
rules = [r for r in rules if r["id"] not in existing_ids]
rules.extend(new_rules)

with open("brain_v2/agent_rules/feedback_rules.json", "w", encoding="utf-8") as f:
    json.dump(rules, f, ensure_ascii=False, indent=2)
print(f"Rules after:  {len(rules)} (+{len(new_rules)} new/replaced)")

# ============================================================================
# 2. Add 5 TIER_1 claims
# ============================================================================
with open("brain_v2/claims/claims.json", encoding="utf-8") as f:
    claims = json.load(f)
print(f"\nClaims before: {len(claims)}, max id={max(c['id'] for c in claims)}")

# Idempotent: drop any prior session-76 claims with the specific claim_types
session76_types = {
    "kernel_capability_gap",
    "infrastructure_state_change",
    "bug_pattern_and_mitigation",
    "code_bug_fix",
    "architecture_decision",
}
claims = [
    c for c in claims
    if not (c.get("created_session") == 76 and c.get("claim_type") in session76_types)
]
next_id = max(c["id"] for c in claims) + 1

new_claims = [
    {
        "id": next_id,
        "claim": "ADT REST DDIC creation endpoints (/sap/bc/adt/ddic/tables, .../indexes) are ABSENT on NW 7.40 (UNESCO ECC 6.0 EhP8). Empirical probe against D01 2026-05-24: POST /sap/bc/adt/ddic/tables returns HTTP 404; adt_discovery() lists 217 collections, DDIC subset includes dataelements/structures/views/typegroups/ddl/sources but NO tables and NO tables/*/indexes. These endpoints shipped in NW 7.50. Implication: on UNESCO current systems, all DDIC TABL/INDX creation MUST use the DDIF wrapper.",
        "claim_type": "kernel_capability_gap",
        "confidence": "TIER_1",
        "evidence_for": [{
            "type": "empirical_http_probe",
            "ref": "Zagentexecution/mcp-backend-server-python/sap_adt_client.py:adt_discovery",
            "cite": "Session #076 live probe 2026-05-24 against D01 HTTPS:443 - adt_discovery() returned 217 collections, grep for tables showed only datapreview/ddic. POST /sap/bc/adt/ddic/tables returned HTTP 404 with empty body.",
            "added_session": 76,
        }],
        "evidence_against": None,
        "related_objects": ["sap_adt_client.py", "define_table", "create_index", "adt_discovery"],
        "domain": "BASIS",
        "created_session": 76,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
        "domain_axes": {"functional": ["*"], "module": ["BASIS", "CTS"], "process": []},
    },
    {
        "id": next_id + 1,
        "claim": "D01 ADT HTTP authentication restored 2026-05-24 after ~6 weeks of HTTP 401 (broken 2026-04-10 to 2026-05-24). Working endpoint switched from http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80 to https://HQ-SAP-D01.HQ.INT.UNESCO.ORG:443 - BASIS likely tightened SICF policy to require HTTPS. Confirmed by live CSRF fetch returning valid token and 217-collection discovery response.",
        "claim_type": "infrastructure_state_change",
        "confidence": "TIER_1",
        "evidence_for": [
            {
                "type": "empirical_http_probe",
                "ref": "Zagentexecution/mcp-backend-server-python/sap_adt_client.py:fetch_csrf",
                "cite": "Session #076 live probe 2026-05-24 - fetch_csrf() returned a real CSRF token via HTTPS:443. Compare to session #75 evidence (2026-05-13) where every HTTP:80 endpoint returned 401.",
                "added_session": 76,
            },
            {
                "type": "prior_session_evidence",
                "ref": "knowledge/session_retros/session_075_retro.md",
                "cite": "Session #75 retro documents the original 401 break; session #76 probe confirms resolution and protocol change.",
                "added_session": 76,
            },
        ],
        "evidence_against": None,
        "related_objects": ["sap_adt_client.py", "fetch_csrf", "_request", "sap_adt_api_skill"],
        "domain": "BASIS",
        "created_session": 76,
        "resolved_session": 76,
        "resolution_notes": "401 was the failure mode that motivated the original silent-401 bug discovery. Both auth and bug fixed same session.",
        "status": "active",
        "domain_axes": {"functional": ["*"], "module": ["BASIS"], "process": []},
    },
    {
        "id": next_id + 2,
        "claim": "TADIR-orphan bug pattern documented: bare DDIF_TABL_PUT calls return SY-SUBRC=0 and build DD02L/DD03L/DD09L rows, but TADIR has no row OR has blank DEVCLASS. Result: object active in DDIC but unable to transport. Empirical evidence on D01: 3 zombie tables in AS4LOCAL=N state inherited from prior runs without TR_TADIR_INTERFACE - ZCRP_ATTACH, ZCRP_AUTH_AUDIT, ZCRP_GL_MAP. Mitigation enforced in sap_adt_client.define_*_via_ddif: emit TR_TADIR_INTERFACE BEFORE DDIF_*_PUT; post-creation verify_tadir() flags orphans for SE03 manual fix.",
        "claim_type": "bug_pattern_and_mitigation",
        "confidence": "TIER_1",
        "evidence_for": [
            {
                "type": "empirical_rfc_read",
                "ref": "DD02L WHERE TABNAME LIKE ZCRP_%",
                "cite": "Session #076 RFC_READ_TABLE against D01 returned 19 ZCRP_* tables, 3 with AS4LOCAL=N (zombies): ZCRP_ATTACH, ZCRP_AUTH_AUDIT, ZCRP_GL_MAP. All originated from prior bare DDIF_TABL_PUT without TR_TADIR_INTERFACE.",
                "added_session": 76,
            },
            {
                "type": "user_testimony",
                "ref": "session_076_conversation",
                "cite": "User: pattern viejo (RFC + DDIF_TABL_PUT, te dara tablas FUNCIONALES pero sin TADIR como paso con DEs) - direct experience of the orphan bug in parallel unescrp project DE creation runs.",
                "added_session": 76,
            },
        ],
        "evidence_against": None,
        "related_objects": ["ZCRP_ATTACH", "ZCRP_AUTH_AUDIT", "ZCRP_GL_MAP", "define_table_via_ddif", "verify_tadir", "TR_TADIR_INTERFACE"],
        "domain": "CUSTOM",
        "created_session": 76,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
        "domain_axes": {"functional": ["*"], "module": ["BASIS", "CTS"], "process": []},
    },
    {
        "id": next_id + 3,
        "claim": "Silent-401 bug in sap_adt_client._request fixed Session #076. Previously the except urllib.error.HTTPError branch unconditionally stored X-CSRF-Token from error responses (SAP echoes a token even on 401), poisoning self._csrf_token and making fetch_csrf() appear to succeed with empty token. Fix: in error branch do NOT cache CSRF from error responses; in fetch_csrf clear prior token + check status==200 + raise RuntimeError if not.",
        "claim_type": "code_bug_fix",
        "confidence": "TIER_1",
        "evidence_for": [
            {
                "type": "source_code_diff",
                "ref": "Zagentexecution/mcp-backend-server-python/sap_adt_client.py:_request,fetch_csrf",
                "cite": "Session #076 edit removed new_csrf capture in error branch + added explicit status==200 check in fetch_csrf. Verified via py_compile + introspection that method signatures are unchanged.",
                "added_session": 76,
            },
            {
                "type": "prior_session_evidence",
                "ref": "knowledge/session_retros/session_075_retro.md",
                "cite": "Session #75 retro explicitly listed this bug as open follow-up. Closed in session #76.",
                "added_session": 76,
            },
        ],
        "evidence_against": None,
        "related_objects": ["sap_adt_client.py", "_request", "fetch_csrf"],
        "domain": "CUSTOM",
        "created_session": 76,
        "resolved_session": 76,
        "resolution_notes": "Closes follow-up from session #75. Verified live: fetch_csrf returned real CSRF token instead of empty string.",
        "status": "active",
        "domain_axes": {"functional": ["*"], "module": ["BASIS"], "process": []},
    },
    {
        "id": next_id + 4,
        "claim": "DDIF wrapper (sap_adt_client.define_table_via_ddif + define_data_element_via_ddif + define_domain_via_ddif) is the canonical EhP8 path for DDIC creation. Atomic create+activate with TR_TADIR_INTERFACE injection (fixes orphan bug), single-equality preflight (avoids 72-char IN-list parser bug), structured SY-SUBRC mapping (eliminates RC=2 ambiguity), forward-compatible API shape (callers flip _via_ddif to ADT REST suffix when UNESCO migrates to S/4HANA). Replaces ad-hoc generate ABAP program that calls DDIF_*_PUT patterns.",
        "claim_type": "architecture_decision",
        "confidence": "TIER_1",
        "evidence_for": [
            {
                "type": "source_code",
                "ref": "Zagentexecution/mcp-backend-server-python/sap_adt_client.py:define_table_via_ddif,define_data_element_via_ddif,define_domain_via_ddif",
                "cite": "Session #076 added 3 atomic creation methods + 4 helpers (preflight_data_element, preflight_domain, preflight_table_chain, verify_tadir) + 5 internals (_get_rfc_connection, _run_abap_program, _execute_ddif, _abap_quote, _parse_rc_marker). Verified compile + introspection.",
                "added_session": 76,
            },
            {
                "type": "skill_documentation",
                "ref": ".claude/skills/sap_adt_api/SKILL.md#15",
                "cite": "Session #076 added SKILL section 15 (DDIF Wrapper canonical for EhP8) - 8 subsections covering rationale, TADIR-orphan mitigation, RC=2 disambiguation, methods exposed, copy-paste workflow, recovery-by-phase, zombie cleanup, S/4HANA migration path.",
                "added_session": 76,
            },
        ],
        "evidence_against": None,
        "related_objects": ["sap_adt_client.py", "define_table_via_ddif", "define_data_element_via_ddif", "define_domain_via_ddif", "preflight_data_element", "verify_tadir", "sap_adt_api_skill"],
        "domain": "CUSTOM",
        "created_session": 76,
        "resolved_session": None,
        "resolution_notes": None,
        "status": "active",
        "domain_axes": {"functional": ["*"], "module": ["BASIS", "CTS"], "process": []},
    },
]

claims.extend(new_claims)
with open("brain_v2/claims/claims.json", "w", encoding="utf-8") as f:
    json.dump(claims, f, ensure_ascii=False, indent=2)
print(f"Claims after:  {len(claims)} (+{len(new_claims)} new), new ids {next_id} to {next_id + len(new_claims) - 1}")

print("\nDone. Next: run python brain_v2/rebuild_all.py to absorb into brain_state.json.")
