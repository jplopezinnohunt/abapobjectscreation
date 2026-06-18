"""
session078_odp_compliance_brain.py
==================================
Persist Session #78 finding: UNESCO Gold DB extraction is OUT OF SCOPE of
SAP Note 3255746 (Unpermitted usage of ODP Data Replication APIs).

Appends (idempotent by id):
  - claims.json       : 2 claims (203 verified_fact, 204 operational_risk)
  - feedback_rules.json: 1 rule (classify exact API before a compliance call)

Run:  python Zagentexecution/session078_odp_compliance_brain.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIMS = os.path.join(ROOT, "brain_v2", "claims", "claims.json")
RULES  = os.path.join(ROOT, "brain_v2", "agent_rules", "feedback_rules.json")
SESS = 78

NEW_CLAIMS = [
  {
    "id": 203,
    "claim": "UNESCO Gold DB extraction uses ONLY RFC_READ_TABLE (generic single-table reader, function group SDTX) over pyrfc + SNC/SSO against P01. It uses NO ODP Data Replication API (RODPS_REPL_*, ODQ_* Operational Delta Queue, /SAPDS/ operators, CDS/extractor/DataSource subscriptions). Therefore it is OUT OF SCOPE of SAP Note 3255746 ('Unpermitted usage of ODP Data Replication APIs', updated 2026-04-13) and is unaffected by the 2026-06-09 Patch-Day patch that blocks unauthorized ODP-RFC calls. A Gold DB refresh runs unchanged after the patch.",
    "claim_type": "verified_fact",
    "confidence": "TIER_1",
    "evidence_for": [
      {"type": "source_code", "ref": "Zagentexecution/mcp-backend-server-python/rfc_helpers.py:147",
       "cite": "rfc_read_paginated() -> _rfc_read_single_page() issues conn.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|', ROWCOUNT=batch_size, ROWSKIPS=offset, OPTIONS=rfc_options, FIELDS=rfc_fields). This is the sole shared extraction primitive imported by every extract_*.py.",
       "added_session": SESS},
      {"type": "source_code", "ref": "Zagentexecution/sap_data_extraction/scripts/extract_bkpf_bseg_parallel.py:94",
       "cite": "Extraction thread calls RFC_READ_TABLE with ROWCOUNT/ROWSKIPS pagination and a WHERE clause pushed via OPTIONS. Standard generic table read, no ODP context.",
       "added_session": SESS},
      {"type": "empirical", "ref": None,
       "cite": "Repo-wide grep for ODP replication APIs (RODPS_REPL, ODQ_, /SAPDS/, RODPS, ODP_) across all .py files = 0 calls. Only token match is a name-classifier regex in sap_brain.py:863 (r'ODQ_|RSN3|RSCOLL' labels BW/Analytics objects in the knowledge graph) -- a classifier, not an ODP call.",
       "added_session": SESS},
      {"type": "sap_doc", "ref": "SAP Note 3255746 / Note 3439624",
       "cite": "Note 3255746 scopes ODP Data Replication APIs only (delta-queue replication to 3rd-party tools). Note 3439624 provides the self-assessment tool to confirm ODP-RFC usage. Both target ODP, not the generic RFC_READ_TABLE reader.",
       "added_session": SESS},
    ],
    "evidence_against": None,
    "related_objects": ["RFC_READ_TABLE", "rfc_helpers.py", "extract_bkpf_bseg_parallel.py",
                        "p01_gold_master_data.db", "SAP_Note_3255746", "SAP_Note_3439624"],
    "domain": "Infrastructure",
    "created_session": SESS,
    "resolved_session": None,
    "resolution_notes": None,
    "status": "active",
    "domain_axes": {"functional": ["Infrastructure"], "module": ["BASIS"], "process": ["*"]},
  },
  {
    "id": 204,
    "claim": "UNESCO's entire Gold DB extraction floor (2,059 tables, 24M+ rows) depends on a SINGLE function module -- RFC_READ_TABLE -- which SAP does not classify as released for productive third-party use. This is the residual data-access compliance flank to monitor: out of scope of Note 3255746 today, but exposed under SAP's broader direction to restrict third-party direct data access. SAP-endorsed durable alternatives for bulk data are ODP-OData and SAP Business Data Cloud; CDS/OData building blocks already exist via the sap_segw skill.",
    "claim_type": "operational_risk",
    "confidence": "TIER_2",
    "evidence_for": [
      {"type": "empirical", "ref": "Zagentexecution/mcp-backend-server-python/rfc_helpers.py",
       "cite": "Single point of dependency: every extract_*.py routes through the shared rfc_read_paginated() -> RFC_READ_TABLE. There is no second extraction mechanism feeding the Gold DB.",
       "added_session": SESS},
      {"type": "sap_policy", "ref": "SAP Note 3255746 (direction-of-travel)",
       "cite": "Note 3255746 formalizes SAP policy of blocking third-party direct data access (ODP first). RFC_READ_TABLE is the more exposed flank under the same governance philosophy and is documented by SAP as not released for productive use. Forward-looking inference, not a current restriction.",
       "added_session": SESS},
    ],
    "evidence_against": None,
    "related_objects": ["RFC_READ_TABLE", "p01_gold_master_data.db", "sap_segw"],
    "domain": "Infrastructure",
    "created_session": SESS,
    "resolved_session": None,
    "resolution_notes": "Mitigation path if SAP ever restricts generic table-read RFCs: migrate the extraction floor to ODP-OData / Business Data Cloud. Not urgent; monitor SAP notes on RFC_READ_TABLE governance.",
    "status": "active",
    "domain_axes": {"functional": ["Infrastructure"], "module": ["BASIS"], "process": ["*"]},
  },
]

NEW_RULE = {
  "id": "feedback_classify_exact_api_before_compliance_call",
  "rule": "When assessing whether a SAP data-access restriction (note, patch, audit, security advisory) affects us, FIRST read our code to classify the EXACT function-module / API family our pipeline calls, then compare it against the SPECIFIC API the restriction names. Never reason from the category ('it is an RFC that reads data'). ODP Data Replication APIs (RODPS_REPL_*, ODQ_*, /SAPDS/) are a different framework from the generic RFC_READ_TABLE reader. UNESCO's Gold DB uses RFC_READ_TABLE only and is OUT OF SCOPE of SAP Note 3255746; the 2026-06-09 ODP-blocking patch does not affect it.",
  "why": "SAP Note 3255746 ('Unpermitted usage of ODP Data Replication APIs') triggered an 'are we affected?' question. The failure mode is reasoning from the category: assuming any data-extraction RFC is in scope. ODP is a replication framework (delta queues, subscriptions, change-data-capture); RFC_READ_TABLE is a generic single-table SELECT-equivalent with no delta queue and no subscription. Conflating them produces either a false 'we are non-compliant' panic or -- worse -- a false 'we are safe' on a note that DID hit us. Precision on the exact API IS the whole answer (CP-003: precision + evidence + facts).",
  "how_to_apply": "1) Grep the repo for the SPECIFIC restricted FMs/namespaces named in the note (e.g. RODPS_REPL, ODQ_, /SAPDS/) -- report the call count with file:line.\n2) Identify the FM our pipeline actually calls (read rfc_helpers.py / extract_*.py) and cite it.\n3) Produce a restricted-vs-used comparison so the verdict is auditable.\n4) Recommend running SAP's own self-assessment tool (when the note ships one, e.g. Note 3439624) to convert code evidence into SAP-sourced confirmation.\n5) If the pipeline depends on a single non-released FM (RFC_READ_TABLE), flag it as a forward-looking risk and name the SAP-endorsed durable path (ODP-OData / Business Data Cloud).",
  "severity": "HIGH",
  "created_session": SESS,
  "source_file": "session078_odp_compliance_brain.py",
  "derives_from_core_principle": "CP-003",
  "cp_derivation_method": "explicit_session_078",
  "domain_axes": {"functional": ["Infrastructure"], "module": ["BASIS", "*"], "process": ["*"]},
}


def upsert_list(path, items, key):
    data = json.load(open(path, encoding="utf-8"))
    existing = {str(x.get(key)) for x in data if isinstance(x, dict)}
    added = 0
    for it in items:
        if str(it[key]) in existing:
            print(f"  SKIP {key}={it[key]} (already present)")
            continue
        data.append(it); added += 1
        print(f"  ADD  {key}={it[key]}")
    if added:
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return added


print("== claims.json ==")
c = upsert_list(CLAIMS, NEW_CLAIMS, "id")
print("== feedback_rules.json ==")
r = upsert_list(RULES, [NEW_RULE], "id")
print(f"\nDone. claims added={c}, rules added={r}")
