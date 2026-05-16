"""Append session #073 feedback rules to brain_v2/agent_rules/feedback_rules.json.
4 new rules captured from the V001 SEPA Dbtr structured-address fix exercise."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))

PATH = os.path.join(os.path.dirname(__file__), "..", "..",
                   "brain_v2/agent_rules/feedback_rules.json")
with open(PATH, encoding="utf-8") as f:
    rules = json.load(f)
print(f"Before: {len(rules)} rules")

new_rules = [
    {
        "id": "feedback_no_sap_standard_only_z",
        "rule": "Only modify Z (custom) objects. NEVER modify SAP-standard programs, includes, function modules, classes, structures, tables. The boundary is the prefix: anything starting with Y_, Z_, /UNESCO/, or in custom function groups SAPLY*/SAPLZ* is fair game; everything else is read-only.",
        "why": "Direct user directive Session #073 (2026-05-09): 'No cambias ningun programa estandard solo lo nuestro Z por favor / eso es una regla'. Touching SAP standard creates: (1) unrecoverable upgrade pain (any S/4 patch overwrites the change with manual conflict resolution), (2) audit findings (Modification Assistant flags + transport classification 'M' marks the object), (3) loss of SAP support (notes refuse to apply on modified objects). The Z prefix convention is the customer-namespace contract; respecting it is what keeps the upgrade path safe.",
        "how_to_apply": "Before INSERT REPORT / RPY_PROGRAM_INSERT / UPDATE TRDIR / UPDATE FUPARAREF on any object, check the name prefix:\n- Allow: Y_*, Z_*, YCL_*, ZCL_*, /UNESCO/*, /CUSTOM/*, SAPLY*, SAPLZ*, LY*U*, LZ*U*\n- Deny: SAP*, RFEB*, RFFO*, RPRA*, RP*, F1*, S* (system), tables T0*-T9** (config), DD0*-DD9* (DDIC system)\n- Greys: prefix not Y/Z but in customer namespace (UNESCO has Y_FI_*, Y_HR_*, etc.). Confirm via TADIR.AUTHOR — if author is SAP, treat as standard.\nWhen unsure, ask. Standard objects can be EXTENDED via BAdI / Enhancement Spot / Append Structure / Customer Exit — never modified in place.",
        "severity": "CRITICAL",
        "created_session": 73,
        "source_file": "session_073_v001_sepa_dbtr_fix",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "user_directive_session_073",
        "domain_axes": {
            "functional": ["*"],
            "module": ["*"],
            "process": ["*"]
        }
    },
    {
        "id": "feedback_insert_report_destroys_fuparref",
        "rule": "INSERT REPORT on a function-group include (e.g. LYFPAYMU19) DESTROYS the FUPARAREF interface metadata for the function modules in that include. After every INSERT REPORT on such an include, ALWAYS execute `GENERATE REPORT '<FUNCTION_GROUP>'` (e.g. SAPLYFPAYM) in the same one-shot to repopulate FUPARAREF.",
        "why": "Session #073 (2026-05-09): deployed Y_FI_DMEE_ADR v2 via INSERT REPORT on LYFPAYMU19. The FM source updated correctly (REPOSRC R3STATE='A'), but FUPARAREF returned TABLE_WITHOUT_DATA — interface metadata was wiped. Symptoms: RPY_FUNCTIONMODULE_READ_NEW returns 0 lines; DMEE editor reports DMEE_ABA358 'incorrect interface'; FM may execute partially (cached compiled code) or fail silently per call. The fix was an explicit `GENERATE REPORT 'SAPLYFPAYM'` which restored 11 FUPARAREF rows from the `*\"` interface comments in the source.",
        "how_to_apply": "Whenever updating a function-module body via INSERT REPORT on its include:\n1. INSERT REPORT 'L<FG>U<NN>' FROM lt_src DIRECTORY ENTRY ls_trdir.\n2. COMMIT WORK.\n3. GENERATE REPORT 'SAPL<FG>' MESSAGE lv_msg.\n4. Verify: SELECT COUNT(*) FROM fupararef WHERE funcname='Y_xxx' — should be > 0.\n5. If still empty, the GENERATE failed silently — investigate before assuming the FM is OK.\nThe RFC_ABAP_INSTALL_AND_RUN one-shot must include both INSERT and GENERATE in one program so they execute under the same transaction.",
        "severity": "CRITICAL",
        "created_session": 73,
        "source_file": "session_073_v001_sepa_dbtr_fix",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "incident_diagnosis_session_073",
        "domain_axes": {
            "functional": ["FI", "Payment"],
            "module": ["FI", "BASIS"],
            "process": []
        }
    },
    {
        "id": "feedback_generate_report_does_not_reparse_interface_comments",
        "rule": "`GENERATE REPORT '<FG>'` regenerates the function-group code BUT does NOT re-parse the `*\"` interface comments to update existing FUPARAREF rows. To change a parameter's pass-by-reference flag (VALUE→REFERENCE or vice versa), you must `UPDATE fupararef SET reference='X' WHERE funcname=... AND parameter=...` directly via ABAP one-shot, then GENERATE again.",
        "why": "Session #073 (2026-05-09): edited Y_FI_DMEE_ADR `*\"` comments to change `VALUE(I_EXTENSION)` → `REFERENCE(I_EXTENSION)` (matching DMEE_EXIT_TEMPLATE_EXTEND_ABA). Deployed via INSERT REPORT + GENERATE REPORT. FUPARAREF still showed `reference=' '` (blank=VALUE) for I_EXTENSION. DMEE_ABA358 errors persisted. Fix: explicit UPDATE fupararef SET reference='X' WHERE funcname='Y_FI_DMEE_ADR' AND parameter='I_EXTENSION'. Then re-GENERATE. The errors disappeared.",
        "how_to_apply": "When changing FM interface in `*\"` comments (pass-by-value vs reference, optional flag, type, structure):\n1. Edit the source `*\"` comments and INSERT REPORT.\n2. GENERATE REPORT '<FG>' (regenerates code but NOT FUPARAREF flags).\n3. SELECT * FROM fupararef WHERE funcname='Y_xxx' — verify each parameter's `reference`, `optional`, `structure` matches the new comments.\n4. For any mismatch, UPDATE fupararef SET <flag>='<new>' WHERE funcname=... AND parameter=...\n5. COMMIT WORK + GENERATE REPORT '<FG>' again.\n6. Re-verify FUPARAREF and run the FM via SE37 or actual caller to confirm.\nKey FUPARAREF columns: PARAMETER, PARAMTYPE (I/E/C/T), STRUCTURE, OPTIONAL, REFERENCE, PPOSITION, R3STATE.",
        "severity": "HIGH",
        "created_session": 73,
        "source_file": "session_073_v001_sepa_dbtr_fix",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "incident_diagnosis_session_073",
        "domain_axes": {
            "functional": ["FI", "Payment"],
            "module": ["FI", "BASIS"],
            "process": []
        }
    },
    {
        "id": "feedback_dmee_exit_must_match_template_exactly",
        "rule": "DMEE exit function modules (those configured as MP_EXIT_FUNC in DMEE_TREE_NODE) MUST have an interface that EXACTLY matches one of the two SAP templates: DMEE_EXIT_TEMPLATE_ABA (legacy) or DMEE_EXIT_TEMPLATE_EXTEND_ABA (modern, with REFERENCE(I_EXTENSION)). Any deviation triggers DMEE_ABA358 'function module XXX has incorrect interface' and the tree validation refuses to compile.",
        "why": "Session #073 (2026-05-09): Y_FI_DMEE_ADR had `VALUE(I_EXTENSION)` while DMEE_EXIT_TEMPLATE_EXTEND_ABA has `REFERENCE(I_EXTENSION)`. The mismatch produced 8 DMEE_ABA358 errors (one per Dbtr/PstlAdr/* leaf assigned to Y_FI_DMEE_ADR). Runtime sometimes tolerates the mismatch (executes with a cached compile), but tree-editor validation, transport activation, and Test mode all reject. Strict-match is enforced field-by-field in FUPARAREF: parameter name, paramtype (I/E/C/T), structure, reference flag, optional flag, position.",
        "how_to_apply": "Before assigning a custom FM as a DMEE node exit:\n1. SELECT * FROM fupararef WHERE funcname='DMEE_EXIT_TEMPLATE_EXTEND_ABA' (the reference).\n2. SELECT * FROM fupararef WHERE funcname='<your custom FM>'.\n3. Diff the two: every field — PARAMETER, PARAMTYPE, STRUCTURE, OPTIONAL, REFERENCE, PPOSITION — must match.\n4. If mismatch, fix via INSERT REPORT (source comments) + UPDATE fupararef (reference flag) + GENERATE REPORT.\n5. Test by running tx DMEE → tree → Validate / Test active version. Should be zero DMEE_ABA358.\nReference template (extended): `IMPORTING VALUE(I_TREE_TYPE) TYPE DMEE_TREETYPE_ABA, VALUE(I_TREE_ID) TYPE DMEE_TREEID_ABA, VALUE(I_ITEM), VALUE(I_PARAM), VALUE(I_UPARAM), REFERENCE(I_EXTENSION) TYPE DMEE_EXIT_INTERFACE_ABA. EXPORTING REFERENCE(O_VALUE), REFERENCE(C_VALUE), REFERENCE(N_VALUE), REFERENCE(P_VALUE). TABLES I_TAB.`",
        "severity": "HIGH",
        "created_session": 73,
        "source_file": "session_073_v001_sepa_dbtr_fix",
        "derives_from_core_principle": "CP-003",
        "cp_derivation_method": "incident_diagnosis_session_073",
        "domain_axes": {
            "functional": ["FI", "Payment"],
            "module": ["FI"],
            "process": ["P2P", "T2R"]
        }
    },
]

# Append + dedupe by id
existing_ids = {r["id"] for r in rules}
appended = 0
for nr in new_rules:
    if nr["id"] in existing_ids:
        print(f"  SKIP (exists): {nr['id']}")
    else:
        rules.append(nr)
        appended += 1
        print(f"  ADD:  {nr['id']}  ({nr['severity']})")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)
print(f"\nAfter: {len(rules)} rules (+{appended})")
