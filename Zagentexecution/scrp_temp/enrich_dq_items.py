"""H51 step 3: Enrich 21 data_quality items with affected_count, resolution_path, related_incidents."""
import json
from pathlib import Path

DQ_PATH = Path("brain_v2/agi/data_quality_issues.json")

# Mapping: dq_id -> {affected_count, resolution_path, related_incidents}
ENRICH = {
    "DQ-001": {
        "affected_count": None,  # unknown until KU-020 answered
        "affected_count_note": "Full LFA1×T077K scan not yet run — tracked as KU-020",
        "resolution_path": "Promoted to recurring check Zagentexecution/quality_checks/vendor_master_integrity_check.py (s#050). Runs weekly against Gold DB. FALS-006 predicts ≥5 new drifters on first full scan.",
        "related_incidents": []
    },
    "DQ-002": {
        "affected_count": 47,
        "affected_count_note": "47 distinct UNESCO PPC codes in T015L (proprietary format, not ISO 20022)",
        "resolution_path": "Documented in payment_bcm_companion.html + epiuse_companion.html. PurposeCode source = FPAYP-XREF3 via BAdI FI_CGI_DMEE_EXIT_W_BADI (see claim #5). No migration planned — UNESCO uses proprietary codes intentionally.",
        "related_incidents": []
    },
    "DQ-003": {
        "affected_count": 119000,
        "affected_count_note": "119K EKBE delivery notes with GJAHR=0000 (VGABE=9)",
        "resolution_path": "H6 closure (s#028): GJAHR=0000 rows are ACH returns marked as delivery notes. Skipped in BUDAT enrichment. Documented in Payment process mining.",
        "related_incidents": []
    },
    "DQ-004": {
        "affected_count": None,
        "affected_count_note": "Auth-restricted tables — count unknown without SAP Basis escalation",
        "resolution_path": "Document per-table in extraction log. Some tables extractable via chunked WHERE clauses + DDIF_FIELDINFO_GET introspection. FMAVCT handled this way (s#053 retro).",
        "related_incidents": []
    },
    "DQ-005": {
        "affected_count": 1690,
        "affected_count_note": "1,690 SKAT rows resolved (518 E + 500 F + 493 P languages + 179 new INSERTs)",
        "resolution_path": "H29 closure (s#038): sync script rfc_helpers.py with SELECT SINGLE + UPDATE FROM ls pattern. All 1,690 rows UPDATE ok=1690/ko=0. Log: knowledge/domains/FI/h29_skat_sync_log.md.",
        "related_incidents": []
    },
    "DQ-006": {
        "affected_count": 553781,
        "affected_count_note": "553,781 BSAS items re-enriched with AUGBL+AUGDT",
        "resolution_path": "H20 closure (s#030): 100% fill rate via targeted enrichment. Documented in bank_statement_ebs_architecture.md.",
        "related_incidents": []
    },
    "DQ-007": {
        "affected_count": 62,
        "affected_count_note": "62 DD03L fields (incl. BUKRS/HBKID/HKTID)",
        "resolution_path": "Re-extracted with explicit FIELDS list (not default 8). Pattern now standard.",
        "related_incidents": []
    },
    "DQ-008": {
        "affected_count": 104,
        "affected_count_note": "104 FEBEP fields including VGEXT/VGINT/GSBER/ZUONR/INTAG/XBLNR/BUTXT",
        "resolution_path": "H22 closure (s#042): FEBEP_2024_2026 table has all 27 critical fields filled. Pattern: always check _2024_2026 suffix, not unsuffixed FEBEP.",
        "related_incidents": []
    },
    "DQ-009": {
        "affected_count": 4,
        "affected_count_note": "4 language keys (D/E/F/P)",
        "resolution_path": "Superseded claim #19 (s#031): these are LANGUAGE keys, not period types. No fix needed — documentation correction only.",
        "related_incidents": []
    },
    "DQ-010": {
        "affected_count": 2,
        "affected_count_note": "2 FM areas missing (ICBA + UIL)",
        "resolution_path": "Filter list extended. Re-extraction completed. All 9 institutes now included.",
        "related_incidents": []
    },
    "DQ-011": {
        "affected_count": 2056,
        "affected_count_note": "2,056 IBC17 items, all 2021-2022 BCM outage",
        "resolution_path": "H16 closure (s#028): out of data scope (2024-2026). Historical record only. Root cause documented: BCM activation Jul2021 misconfigured until Oct2022.",
        "related_incidents": []
    },
    "DQ-012": {
        "affected_count": 261,
        "affected_count_note": "213 non-USD bank accts + 48 non-USD clearing accts missing T030H entries",
        "resolution_path": "Tracked as KU-010 (does FAGL_FC_VAL use fallback?). Needs P01 config check before deciding fix path. May not be a bug — could be intentional (USD-only valuation).",
        "related_incidents": []
    },
    "DQ-013": {
        "affected_count": 2,
        "affected_count_note": "2 classes (YCL_IDFI_CGI_DMEE_AE + YCL_IDFI_CGI_DMEE_BH) exist in D01 TADIR but not P01",
        "resolution_path": "Superseded claim #22 (s#039, H18 closure): PurposeCode comes from FPAYP-XREF3 via DMEE tree + BAdI FI_CGI_DMEE_EXIT_W_BADI, not from AE/BH classes. P01 uses UTIL fallback. No migration needed.",
        "related_incidents": []
    },
    "DQ-014": {
        "affected_count": None,
        "affected_count_note": "Applies to all released transports — structural SAP behavior",
        "resolution_path": "Documented as extraction pattern: always extract transport contents BEFORE release. Previous extraction is source of truth.",
        "related_incidents": []
    },
    "DQ-015": {
        "affected_count": 199000,
        "affected_count_note": "199K permanent ledger items on 10xxxxx GLs (by design)",
        "resolution_path": "Superseded claim #18 (s#029): these are permanent ledger entries, never cleared. Real unreconciled = 2,737 on 11xxxxx (0.6% gap). H28 closure documented in bank_statement_ebs_architecture.md.",
        "related_incidents": []
    },
    "DQ-016": {
        "affected_count": None,
        "affected_count_note": "Multiple memory files on Windows stdout path",
        "resolution_path": "Pattern: always use open(..., encoding='utf-8') + sys.stdout.reconfigure(encoding='utf-8') on Windows. Python scripts retrofitted.",
        "related_incidents": []
    },
    "DQ-017": {
        "affected_count": 187514,
        "affected_count_note": "187,514 fmifiit_full rows UNES + bank clearing GLs + FISTL='UNESCO' hardcode signature",
        "resolution_path": "Claim #28 (s#048) documents the ZXFMDTU02_RPY:99 hardcode. Fix path: remove hardcode via YRGGBS00 restructure (coordinate with H48 investigation).",
        "related_incidents": ["INC-000006073"],
        "discovered_session": 48
    },
    "DQ-018": {
        "affected_count": 1,
        "affected_count_note": "1 user (AL_JONATHAN) with Y_USERFO='HQ' instead of 'JAK'",
        "resolution_path": "H45 (s#054). Blocked by KU-027 (verify YFO_CODES has FOCOD='JAK') before SU3 update. See knowledge/incidents/INC-000005240_xref_office_substitution.md.",
        "related_incidents": ["INC-000005240"]
    },
    "DQ-019": {
        "affected_count": 21754,
        "affected_count_note": "21,754 manual XREF edits Q1 2026 via FBL3N/FBL1N/FB02/FBL5N on UNES BELEG documents",
        "resolution_path": "H46 (s#054). Strategic fix options in knowledge/domains/Treasury/xref_office_tagging_model.md §7.3. Decision pending between preventive substitution fix / opt-in SU3 model / periodic reconciliation / tolerate. Blocked by H48.",
        "related_incidents": ["INC-000005240"]
    },
    "DQ-020": {
        "affected_count": None,
        "affected_count_note": "Unknown drift count without full USR05×PA0001 diff — tracked as KU-028",
        "resolution_path": "H47 (s#054). Organizational process gap. Needs HR→BASIS alert mechanism + periodic diff report + policy for mandatory SU3 update on HR transfer. Cross-domain item.",
        "related_incidents": ["INC-000005240"]
    },
    "dq_ghost_pernr_bcm_oesttveit": {
        "affected_count": 1,
        "affected_count_note": "1 ghost PERNR (10567156 / Svein OESTTVEIT) active in 2 BCM rules",
        "resolution_path": "INC-000006313 closure (s#052). Reconciliation check Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py added as recurring detector. PERNR removed from rules.",
        "related_incidents": ["INC-000006313"]
    }
}


def main():
    with open(DQ_PATH, "r", encoding="utf-8") as f:
        dq = json.load(f)

    updated = 0
    missing = []
    for d in dq:
        did = d["id"]
        if did in ENRICH:
            for k, v in ENRICH[did].items():
                if d.get(k) is None or (isinstance(v, list) and d.get(k) in (None, [])):
                    d[k] = v
            d["enriched_session"] = 54
            updated += 1
        else:
            missing.append(did)

    with open(DQ_PATH, "w", encoding="utf-8") as f:
        json.dump(dq, f, indent=2, ensure_ascii=False)

    print(f"DQ items enriched: {updated}")
    print(f"Without mapping: {missing}")
    print(f"Total DQ: {len(dq)}")


if __name__ == "__main__":
    main()
