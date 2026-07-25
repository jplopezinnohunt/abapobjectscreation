"""H51 step 4: Enrich 34 known_unknowns with blocks_incident, investigation_cost_estimate, owner_session."""
import json
from pathlib import Path

KU_PATH = Path("brain_v2/agi/known_unknowns.json")

# Cost estimate categories:
#   LOW    — single RFC call / single SQL query / quick grep (<30 min)
#   MEDIUM — multi-step investigation, requires cross-reference (1-3 hours)
#   HIGH   — full session of work, may require SAP Basis escalation / new extraction
#   UNKNOWN — cannot estimate without further discovery

ENRICH = {
    "KU-001": {"blocks_incident": "INC-000006073", "investigation_cost_estimate": "HIGH", "owner_session": None, "notes": "RW609 originates in BAdI or customer exit — requires ST05 trace in TS3 with a failing Travel posting."},
    "KU-002": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Requires BizTalk/SuccessFactors integration diagram + HR-team conversation."},
    "KU-003": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "Check SM37 jobs filtering by program containing TCURR/OB08 + TFDIR_CUSTOM FM list for rate feeds."},
    "KU-004": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Data Hub export identifies target via WE21 partner profile + BD64 distribution model. One RFC call set."},
    "KU-005": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "RFCDES scan for GUID-named HTTP destinations + ICF service probe. Cross-ref with integration_map_complete.md."},
    "KU-006": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "Resolved by H20 (s#030) — BSAS AUGBL was extraction gap, now 100% filled. KU can be ANSWERED (forgotten to close)."},
    "KU-007": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Partially answered by H18 (s#039): PurposeCode source = FPAYP-XREF3 via DMEE tree /CGI_XML_CT_UNESCO. XML output path needs one F110 run trace to confirm serialization."},
    "KU-008": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Query bseg_union + REGUH for BSCHL distribution of AB-stream cases. 1-hour SQL work."},
    "KU-009": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "BAdI YCL_IDFI_CGI_DMEE_FR is extracted. Read method stubs + identify PurposeCode handler. 30 min of code reading."},
    "KU-010": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Trace FAGL_FC_VAL for one non-USD account with missing T030H + inspect fallback path in code. Relates to DQ-012."},
    "KU-011": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "PRAGMA table_info(T042Z) in Gold DB. 5-minute answer."},
    "KU-012": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "260 scripts in mcp-backend-server-python/. Audit via grep + cross-reference with skill SKILL.md files."},
    "KU-013": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Analyze payment_process_mining case cycle times for SCB09 bank + compare to other banks in same country."},
    "KU-014": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "MGIE company code drill-down in payment_bcm_companion.html + cycle time decomposition."},
    "KU-015": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "7 open customizing requests — compare TADIR contents D01 vs P01 for objects in those transports. Pre-upgrade blocker."},
    "KU-016": {"blocks_incident": "INC-000006073", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "RFC_READ_TABLE(PA0027, WHERE=\"SUBTY='02'\", LIMIT=10). 5-minute answer."},
    "KU-017": {"blocks_incident": "INC-000006073", "investigation_cost_estimate": "HIGH", "owner_session": None, "notes": "Requires full-table join PRPS×FMIFIIT×BSEG filtered by 2010-2018 SROCHR substitution pattern across 9 company codes. Multi-hour."},
    "KU-018": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": 54, "notes": "Partially falsified FALS-001/002 session #054: brain_state grew to 10.9% context but one-Read pattern validated."},
    "KU-019": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": 54, "notes": "Session #054 showed brain_state.objects[X].knowledge_docs used for incident #053 analysis. Validated."},
    "KU-020": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Full scan LFA1 × T077K × LFB1. ~30 min work. Feeds DQ-001 recurring check + FALS-006."},
    "KU-021": {"blocks_incident": None, "investigation_cost_estimate": "LOW", "owner_session": 52, "notes": "Tested via INC-000006313 + INC-BUDGETRATE-EQG — workflow produces required output. FALS-005 PASSED (probable)."},
    "KU-022": {"blocks_incident": None, "investigation_cost_estimate": "MEDIUM", "owner_session": 54, "notes": "Session #054 audit: coverage now 64.3% (dropped from 75.6% due to added blind_spots). H50 triages."},
    "KU-023": {"blocks_incident": None, "investigation_cost_estimate": "HIGH", "owner_session": None, "notes": "Full TADIR scan by package + object type vs brain_state.objects. Multi-hour data extraction + coverage report."},
    "KU-024": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "Answerable via email request to user + screenshot. Non-technical."},
    "KU-025": {"blocks_incident": "INC-000006073", "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "FMDT* table scan in Gold DB + cross-reference with ZXFMDTU02_RPY.abap derivation. 1 hour."},
    "KU-026": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "USR05 extraction with PARID like 'Y_%' filter. Relates to DQ-018 fix path."},
    "KU-027": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "Single RFC_READ_TABLE on YFO_CODES with WHERE FOCOD='JAK'. BLOCKS H45 AL_JONATHAN fix. <5 min."},
    "KU-028": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "USR05 × PA0001 diff scan. Feeds DQ-020 population sizing."},
    "KU-029": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "HIGH", "owner_session": None, "notes": "Downstream impact on reporting (YRGG*, FI-SL ledger consolidation). Requires ABAP trace + reporting chain map."},
    "KU-030": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "YRGGBS00 version history via SE38 version comparison. H48 scope."},
    "KU-031": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "MEDIUM", "owner_session": None, "notes": "Check GB01 / GGB1 tables via RFC + GCTAB/GCSTR secondary tables. H48 scope."},
    "KU-032": {"blocks_incident": "INC-000005240", "investigation_cost_estimate": "HIGH", "owner_session": None, "notes": "Empirical ST05 trace of F110 vs F-53 substitution callpoint firing in TS3. Requires live test posting. H48 scope."},
    "uq_uis_non_citibank_signatories": {"blocks_incident": "INC-000006313", "investigation_cost_estimate": "LOW", "owner_session": None, "notes": "Query bank masterdata T012K for UIS company code + compare to signatory panel. User question, awaits response."},
    "uq_uis_bcm_role_split_consistency": {"blocks_incident": "INC-000006313", "investigation_cost_estimate": "LOW", "owner_session": 52, "notes": "ANSWERED session #052 (see `answered_session` field). Role split is intentional per OOCU_RESP structure."}
}


def main():
    with open(KU_PATH, "r", encoding="utf-8") as f:
        kus = json.load(f)

    updated = 0
    missing = []
    for k in kus:
        kid = k["id"]
        if kid in ENRICH:
            for key, val in ENRICH[kid].items():
                # Only add if not present
                if k.get(key) is None:
                    k[key] = val
            k["enriched_session"] = 54
            updated += 1
        else:
            missing.append(kid)

    with open(KU_PATH, "w", encoding="utf-8") as f:
        json.dump(kus, f, indent=2, ensure_ascii=False)

    print(f"KUs enriched: {updated}")
    print(f"Without mapping: {missing}")
    print(f"Total KUs: {len(kus)}")

    # Distribution report
    from collections import Counter
    cost_dist = Counter(k.get("investigation_cost_estimate", "UNKNOWN") for k in kus)
    blocks_dist = Counter(k.get("blocks_incident") for k in kus)
    print(f"\nCost distribution: {dict(cost_dist)}")
    print(f"Blocks-incident distribution: {dict(blocks_dist)}")


if __name__ == "__main__":
    main()
