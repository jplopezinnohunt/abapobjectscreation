"""
One-shot brain update for Session #051 / INC-000006313.
Appends:
  - 3 feedback rules (p01_readonly_absolute, bcm_signatory_ry_otype, bcm_ghost_pernr_check)
  - 2 claims (bcm_ry_otype, ghost_pernr_oesttveit)
  - 1 data quality issue (dq_ghost_pernr_bcm_oesttveit)
  - 2 known unknowns (uq_uis_non_citibank_signatories, uq_uis_bcm_role_split_consistency)
  - 1 incident (INC-000006313)
Idempotent — skips any id that already exists.
"""
import json
import io
from pathlib import Path

ROOT = Path(__file__).parent.parent
SESSION = 51

def load(path):
    return json.load(io.open(ROOT / path, encoding="utf-8"))

def save(path, data):
    json.dump(data, io.open(ROOT / path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# ------------------------------------------------------------------
# 1. feedback rules
# ------------------------------------------------------------------
rules_path = "brain_v2/agent_rules/feedback_rules.json"
rules = load(rules_path)

new_rules = [
    {
        "id": "feedback_p01_readonly_absolute",
        "rule": "P01 is strictly read-only for the AI agent. Never attempt INSERT/UPDATE/DELETE on P01 via RFC, BAPI, RFC_ABAP_INSTALL_AND_RUN, OOCU_RESP WebGUI automation, or any other path.",
        "why": "P01 is production. Signatory changes, master data updates, and config changes are executed by DBS via direct OOCU_RESP/SPRO/PA30 access in P01 after TRS/business authorization. An AI write to P01 bypasses the CFO delegation chain and the audit trail. Confirmed by user during INC-000006313 (2026-04-09) with an emphatic 'you can not do any insert'.",
        "how_to_apply": "Agent scope on any P01 change request is: (1) read-only analysis via RFC_READ_TABLE, (2) produce a written change spec for DBS, (3) post-change verification via RFC_READ_TABLE and Gold DB refresh. Never write a script with a --execute flag targeting P01. Never call write BAPIs. Never run RFC_ABAP_INSTALL_AND_RUN with INSERT/UPDATE/MODIFY/DELETE. If the user asks 'update it', the answer is 'spec for DBS + verify after'. D01 writes are still allowed.",
        "severity": "CRITICAL",
        "created_session": SESSION,
        "source_file": "knowledge/incidents/INC-000006313_uis_bcm_add_voffal.md"
    },
    {
        "id": "feedback_bcm_signatory_ry_otype",
        "rule": "BCM signatory responsibility groups are PD objects of OTYPE='RY' (not 'AC'). HRP1000.SHORT holds the rule class ('BNK_01_01_03' = rule 90000004, 'BNK_01_01_04' = rule 90000005). User assignments live in HRP1001 with RELAT='007' SCLAS='P' SOBID=<PERNR>. Resolve names via PA0002, SAP user via PA0105 SUBTY='0001', email via PA0105 SUBTY='0010'. PA0001 is blocked.",
        "why": "Session #051 (INC-000006313) discovered that querying HRP1000 OTYPE='AC' for PFAC workflow rules returns zero rows for our SNC user, while OTYPE='RY' works. Without this documented path, a future agent wastes significant time re-discovering the schema from scratch. The RY -> HRP1001/007/P -> PA0002/PA0105 chain was verified against the OOCU_RESP screens provided by the user.",
        "how_to_apply": "For any BCM signatory question: (1) list groups via HRP1000 OTYPE='RY' SHORT IN ('BNK_01_01_03','BNK_01_01_04'), (2) list assignments via HRP1001 OTYPE='RY' OBJID=<ry_objid> then filter RELAT='007' SCLAS='P' in Python, (3) resolve PERNRs via PA0002 for name and PA0105 SUBTY='0001' for SAP user + SUBTY='0010' for email. RFC_READ_TABLE rejects IN() and more than ~3 AND clauses on HR tables, so keep WHERE simple.",
        "severity": "HIGH",
        "created_session": SESSION,
        "source_file": "knowledge/domains/Treasury/bcm_signatory_rules.md"
    },
    {
        "id": "feedback_bcm_ghost_pernr_check",
        "rule": "When investigating a BCM signatory, always cross-check that HRP1001.SOBID has a non-empty PA0105 SUBTY='0001' USRID. An empty USRID means the PERNR is a ghost shell and the signatory cannot be routed work items by workflow 90000003 even though they appear in OOCU_RESP and on the bank carton.",
        "why": "Session #051 (INC-000006313) discovered a ghost PERNR 10567156 for Svein OESTTVEIT active on UIS rules 90000004 + 90000005 since 2025-10-04. Real PERNR is 10067156 (user S_OESTTVEIT). Ghost has no PA0105/0001, so Svein silently cannot sign UIS payments in BNK_APP. This is a production defect that was invisible until the bank's carton des signatures was compared PERNR-by-PERNR against HRP1001.",
        "how_to_apply": "Run `python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py` at session start when the user asks about BCM signatories, AND after any DBS signatory update. Check 1 of the script detects ghost PERNRs. Treat any ghost as CRITICAL data quality defect and log to data_quality_issues.json. Always compare against the PERNR on the HEPATUS carton des signatures page (last page of a TRS letter), not the cover letter which uses names only.",
        "severity": "HIGH",
        "created_session": SESSION,
        "source_file": "Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py"
    }
]

existing_ids = {r["id"] for r in rules}
added = 0
for r in new_rules:
    if r["id"] not in existing_ids:
        rules.append(r)
        added += 1
        print(f"  +rule {r['id']}")
    else:
        print(f"  =rule {r['id']} already present")
save(rules_path, rules)
print(f"feedback_rules.json: {len(rules)} total (+{added})")
print()

# ------------------------------------------------------------------
# 2. claims
# ------------------------------------------------------------------
claims_path = "brain_v2/claims/claims.json"
claims = load(claims_path)

new_claims = [
    {
        "id": "claim_bcm_ry_otype",
        "claim": "At UNESCO P01, BCM workflow responsibility groups (rules 90000004 BNK_COM and 90000005 BNK_INI) are stored as PD objects OTYPE='RY' under PLVAR='01'. HRP1000.SHORT = rule class, HRP1000.STEXT = group name. HRP1001 RELAT='007' SCLAS='P' SOBID=<PERNR> assigns users. Workflow 90000003 resolves rule 90000005 first (validators) then 90000004 (committers).",
        "claim_type": "config_structure",
        "confidence": "VERIFIED",
        "evidence_for": [
            "HRP1000 SHORT LIKE 'BNK%' returned 20 RY objects including the 7 live UIS/UNES/IIEP/UBO/UIL groups (Session #051 probe)",
            "HRP1001 RELAT='007' SCLAS='P' returned 253 rows (now 255 post-INC6313) across the 24 RY groups",
            "Counts per group match the OOCU_RESP screens provided by user for rule 90000004: 13/13 UNES, 20/20 UIS, 16/16 IIEP, 11/11 UBO<=10K, 15/15 UIS<=10K, 10/10 UBO>10K, 8/8 UIL",
            "PA0002 VORNA/NACHN for resolved PERNRs match the names on the OOCU_RESP screenshots and the UIS carton des signatures (INC-000006313 PDF page 4)"
        ],
        "evidence_against": [],
        "related_objects": ["HRP1000", "HRP1001", "PA0002", "PA0105", "OOCU_RESP", "BNK_COM_01_01_03", "BNK_INI_01_01_04"],
        "domain": "Treasury",
        "created_session": SESSION,
        "resolved_session": SESSION
    },
    {
        "id": "claim_ghost_pernr_oesttveit",
        "claim": "PERNR 10567156 is a ghost shell referenced by HRP1001 rows under RY 50010054 and RY 50036801 (UIS signatures for all transfers / UIS Validation) with BEGDA=2025-10-04 ENDDA=99991231. It has a PA0002 record with name 'Svein OESTTVEIT' but NO PA0105 SUBTY='0001' SAP user and NO PA0105 SUBTY='0010' work email. The real Svein OESTTVEIT is PERNR 10067156 (user S_OESTTVEIT). Impact: workflow 90000003 cannot route a BNK_APP work item to PERNR 10567156, so Svein is silently unable to sign UIS payments in SAP despite appearing on OOCU_RESP and on the Citibank Canada carton.",
        "claim_type": "defect",
        "confidence": "VERIFIED",
        "evidence_for": [
            "PA0002 read for 10067156 returned 5 continuous employment records 1955 -> 9999",
            "PA0002 read for 10567156 returned 1 flat record 1955-12-16 -> 9999-12-31 with same name",
            "PA0105 for 10067156 returned SUBTY='0001' USRID='S_OESTTVEIT' and SUBTY='0010' USRID_LONG='S.OESTTVEIT@UNESCO.ORG'",
            "PA0105 for 10567156 returned only SUBTY='0030' private email 'svein.osttveit@orange.fr'",
            "HEPATUS carton des signatures (UIS Citibank Canada 02/04/2026, INC-000006313 PDF page 4) lists PERNR 10067156 for Svein OESTTVEIT, not 10567156"
        ],
        "evidence_against": [],
        "related_objects": ["HRP1001", "PA0002", "PA0105", "50010054", "50036801", "BNK_COM_01_01_03", "BNK_INI_01_01_04"],
        "domain": "Treasury",
        "created_session": SESSION,
        "resolved_session": None
    }
]

existing_ids = {c["id"] for c in claims}
added = 0
for c in new_claims:
    if c["id"] not in existing_ids:
        claims.append(c)
        added += 1
        print(f"  +claim {c['id']}")
save(claims_path, claims)
print(f"claims.json: {len(claims)} total (+{added})")
print()

# ------------------------------------------------------------------
# 3. data quality issues
# ------------------------------------------------------------------
dq_path = "brain_v2/agi/data_quality_issues.json"
dqs = load(dq_path)

new_dqs = [
    {
        "id": "dq_ghost_pernr_bcm_oesttveit",
        "source": "HRP1001 (P01) via bcm_signatory_assignment (Gold DB)",
        "issue": "Ghost PERNR 10567156 active in UIS BCM rules 90000004 + 90000005 since 2025-10-04. PA0105/0001 empty -> workflow 90000003 cannot route BNK_APP work items -> Svein OESTTVEIT silently cannot sign UIS payments even though he appears on the Citibank Canada carton des signatures as PERNR 10067156.",
        "severity": "HIGH",
        "impact": "Production payment routing for UIS is understaffed by one committer. If Svein would have been the deciding signatory, the batch waits or a different user approves. The real PERNR 10067156 (user S_OESTTVEIT, email S.OESTTVEIT@UNESCO.ORG) should have been used in OOCU_RESP.",
        "workaround": "None automated. DBS must delimit HRP1001 SOBID=10567156 and insert fresh rows with SOBID=10067156 after TRS authorization. Until then, the other 7 UIS signatories on the carton must cover Svein's work.",
        "discovered_session": SESSION,
        "promoted_to_recurring_check": True,
        "related_check_script": "Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py",
        "related_known_unknown": None,
        "first_seen_date": "2025-10-04",
        "status": "OPEN"
    }
]

existing_ids = {i["id"] for i in dqs}
added = 0
for i in new_dqs:
    if i["id"] not in existing_ids:
        dqs.append(i)
        added += 1
        print(f"  +dq {i['id']}")
save(dq_path, dqs)
print(f"data_quality_issues.json: {len(dqs)} total (+{added})")
print()

# ------------------------------------------------------------------
# 4. known unknowns
# ------------------------------------------------------------------
ku_path = "brain_v2/agi/known_unknowns.json"
kus = load(ku_path)

new_kus = [
    {
        "id": "uq_uis_non_citibank_signatories",
        "question": "Does UIS have bank accounts besides Citibank Canada (USD 2017588014, CAD 2017588006)? If yes, are Ophelia STEPHENSON-ODLE (PERNR 10136066) and Yanhong ZHANG (PERNR 10098989) authorized signatories on any of those other cartons? They are currently active in SAP RY 50010054 (UIS signatures for all transfers) but not on the 2026-04-02 Citibank Canada carton.",
        "why_unknown": "SAP BCM responsibility groups are entity-level, not bank-account-level. One group 'UIS signatures for all transfers' covers every UIS bank account at every bank. We only have the Citibank Canada carton on file. Without all UIS cartons we cannot distinguish legitimate multi-bank coverage from stale SAP config.",
        "raised_session": SESSION,
        "domain": "Treasury",
        "source_incident": "INC-000006313",
        "addressed_to": "TRS (Ingrid Wettie / BFM-TRS-MO)",
        "blocks_action": "SAP cleanup delimit for STEPHENSON/ZHANG on UIS groups"
    },
    {
        "id": "uq_uis_bcm_role_split_consistency",
        "question": "Is the role split on UIS BCM rules intentional? Anssi YLI-HIETANEN (10097358, Treasurer) is on rule 90000004 (Commit) but not on rule 90000005 (Validation). Lamin SANNEH (10150918) is on rule 90000005 but not on rule 90000004. The Citibank Canada carton lists both flatly as 'authorized to sign jointly two by two' without distinguishing validator vs committer. Is the SAP split deliberate (e.g., Treasurer commits only) or a maintenance accident?",
        "why_unknown": "The carton does not carry SAP rule semantics. The business rule for the validator/committer split is oral/undocumented and must be confirmed by TRS.",
        "raised_session": SESSION,
        "domain": "Treasury",
        "source_incident": "INC-000006313",
        "addressed_to": "TRS (Ingrid Wettie)",
        "blocks_action": "Any role-mirroring cleanup on UIS BCM panel"
    }
]

existing_ids = {q["id"] for q in kus}
added = 0
for q in new_kus:
    if q["id"] not in existing_ids:
        kus.append(q)
        added += 1
        print(f"  +known_unknown {q['id']}")
save(ku_path, kus)
print(f"known_unknowns.json: {len(kus)} total (+{added})")
print()

# ------------------------------------------------------------------
# 5. incidents
# ------------------------------------------------------------------
inc_path = "brain_v2/incidents/incidents.json"
incs = load(inc_path)

new_incident = {
    "id": "INC-000006313",
    "status": "CLOSED",
    "title": "Add Said OULD AHMEDOU VOFFAL to UIS BCM signatory panel",
    "reporter": "Ingrid Wettie (BFM-TRS-MO / Middle Office)",
    "received_date": "2026-04-09",
    "analyzed_session": SESSION,
    "domain": "Treasury",
    "secondary_domains": ["BCM", "HR"],
    "transactions": ["OOCU_RESP", "BNK_APP", "PA30"],
    "primary_object_id": "10092400",
    "primary_subject": "PERNR 10092400 Said OULD AHMEDOU VOFFAL (SAP user S_VOFFAL)",
    "company_codes_involved": ["UIS"],
    "scenario": "signatory_panel_change",
    "incident_type": "operational_change",
    "error_messages": [],
    "root_cause_summary": "Not a defect. Operational change request forwarded from TRS. Said returned as UNESCO staff on 2026-03-22 (PA0002 new record) and was reinstated on the UIS Citibank Canada authorized signatory panel by TRS letter FIN.8/MOD/10.0000003625 dated 02/04/2026. His prior UIS BCM assignments had expired between 2023-10-04 and 2024-01-17 during his absence.",
    "code_validation_chain": [
        "PA0002 PERNR=10092400 -> new record BEGDA=20260322 ENDDA=99991231 (returning employee)",
        "PA0105 SUBTY=0001 PERNR=10092400 -> USRID=S_VOFFAL",
        "USR02 BNAME=S_VOFFAL -> UFLAG=0 GLTGV=20260402 GLTGB=20280319 USTYP=A",
        "HRP1001 RY=50010054 SOBID=10092400 historical row BEGDA=20160303 ENDDA=20231004 (expired)",
        "HRP1001 RY=50036801 SOBID=10092400 historical row BEGDA=20211018 ENDDA=20231004 (expired)",
        "Post-change HRP1001 RY=50010054 SOBID=10092400 BEGDA=20260409 ENDDA=99991231 (verified)",
        "Post-change HRP1001 RY=50036801 SOBID=10092400 BEGDA=20260409 ENDDA=99991231 (verified)"
    ],
    "scope": {
        "person_added": "10092400 Said OULD AHMEDOU VOFFAL",
        "rules_affected": ["90000004", "90000005"],
        "ry_objids_affected": ["50010054", "50036801"],
        "bank_accounts_affected": ["Citibank Canada USD 2017588014", "Citibank Canada CAD 2017588006"],
        "bank_confirmation_deadline": "2026-04-22"
    },
    "fix_path": {
        "immediate": "DBS added 2 HRP1001 rows via OOCU_RESP in P01 (SOBID=10092400, BEGDA=20260409, ENDDA=99991231) on 2026-04-09. BEGDA used execution date instead of letter date 2026-04-02 (7-day audit gap, low material risk).",
        "structural": "None - operational change.",
        "preventive": [
            "Run bcm_signatory_reconciliation_check.py after every BCM signatory change to catch drift automatically",
            "Store each bank carton under Zagentexecution/quality_checks/cartons/<entity>_<bank>_<yyyymmdd>.txt for future diffs",
            "When executing future changes, use TRS letter effective date as BEGDA, not execution date"
        ]
    },
    "side_findings": [
        "Ghost PERNR 10567156 for Svein OESTTVEIT on RY 50010054 + 50036801 (logged as dq_ghost_pernr_bcm_oesttveit)",
        "Possible UIS panel drift STEPHENSON/ZHANG vs Citibank Canada carton (logged as uq_uis_non_citibank_signatories)",
        "Role-split inconsistency YLI-HIETANEN/SANNEH on UIS rules (logged as uq_uis_bcm_role_split_consistency)"
    ],
    "analysis_doc": "knowledge/incidents/INC-000006313_uis_bcm_add_voffal.md"
}

existing_ids = {i["id"] for i in incs}
if new_incident["id"] not in existing_ids:
    incs.append(new_incident)
    print(f"  +incident {new_incident['id']}")
else:
    print(f"  =incident {new_incident['id']} already present")
save(inc_path, incs)
print(f"incidents.json: {len(incs)} total")
