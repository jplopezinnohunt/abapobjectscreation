"""H51 step 2: Link 15 superseded claims to their replacement + add superseded_reason.

Methodology: manual mapping based on cross-reference of claim text + resolved_session + PMO closure notes.
Each entry: (claim_id, superseded_by_claim_id | None, superseded_reason_text).
None = corrected without a specific replacement claim (the correction was PMO/retro evidence).
"""
import json
from pathlib import Path

CLAIMS_PATH = Path("brain_v2/claims/claims.json")

# (id, replacement_claim_id, reason)
MAPPING = {
    3: (None, "FEBEP_2024_2026 extraction in s29-30 revealed 223,710 actual rows. Original count was from truncated FEBEP table (50K rows, 104 cols). See PMO H22 closure note. No specific replacement claim — correction was captured in Gold DB schema."),
    13: (None, "H17 (s28) 4-stream payment event model showed OP goes through F110+BCM+DMEE+SWIFT like other streams. Original claim was from incomplete stream identification in s26. Correction in payment_process_mining.html."),
    14: (6, "Claim #6 (s37) restates the BCM dual-control gap with correct count 3,359 (+1,366 drift from the original 1,557). Top 2 offenders also identified (C_LOPEZ + I_MARQUAND)."),
    15: (None, "H17 4-stream payment model clarified the REGUH→BSAK linkage is mediated by PAYR + AUGBL depending on stream. Correction captured in Golden Query documentation, not as a separate claim."),
    16: (None, "Payment on-time rate recomputed in H17 (s28) process mining with correct case definitions (550K cases). 1.1% was derived from incomplete case set. Corrected value lives in payment_process_mining.html, not as a separate claim."),
    17: (None, "FEBRE 102I analysis (s30, H24) identified 102I root cause = ACH returns with BELNR='*' — these are not regular clearing posts but return/reject items. The 29.2% rate was meaningless without that classification."),
    18: (None, "H19/H28 investigation (s29) showed 199K items on 10xxxxx GLs are permanent ledger entries by design (never cleared). Real unreconciled = 2,737 on 11xxxxx (0.6% gap). See bank_statement_ebs_architecture.md."),
    19: (None, "Session #31 correction: D/E/F/P in T010P/TABKEY are LANGUAGE codes (Deutsch/English/Français/Portuguese), not functional period types. Tracked as DQ-009."),
    20: (None, "Session #31: ICBA FMIFIIT=0 was an extraction-filter bug (ICBA and UIL missing from filter list), not an architectural sharing. Tracked as DQ-010 (RESOLVED)."),
    21: (None, "Session #34: CSKA extraction was incomplete in s33 — re-extraction yielded non-zero cost element config. Cost elements ARE configured."),
    22: (5, "Claim #5 (s39, H18 closure) identifies PurposeCode source as FPAYP-XREF3 via DMEE tree /CGI_XML_CT_UNESCO node N_9662041050 + BAdI FI_CGI_DMEE_EXIT_W_BADI. The 'AE and BH DMEE currency BAdI' classes (YCL_IDFI_CGI_DMEE_AE/BH) do NOT exist in P01 TADIR — only in D01 CTS. Tracked as DQ-013."),
    23: (None, "DQ-002 (OPEN): T015L PPC codes are UNESCO-proprietary format (001/002/003...), not ISO 20022 standard. Documentation PDFs show wrong ISO codes. Correction in DQ-002, no replacement claim."),
    24: (6, "Claim #6 (s37) identified C_LOPEZ (94.7% self-approval) and I_MARQUAND (92.9%) as the top 2 BCM dual-control offenders. F_DERAKHSHAN was reclassified — 74% dual-controlled (below the risk threshold). See H13 closure."),
    25: (None, "H17 4-stream model (s28) and CO table extraction (s35, B3 closure) established real sizes: COOI=773K, COEP=2.55M, RPSCO=127K. The s005 anchors were ~2x too small."),
    26: (None, "B9 closure (s28): STEM not in T001 — not a real company code at UNESCO. 9 real co codes: IBE, ICBA, ICTP, IIEP, MGIE, UBO, UIL, UIS, UNES. CBE01 bank mapping is moot."),
}


def main():
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        claims = json.load(f)

    updated = 0
    missing = []
    for c in claims:
        if c.get("claim_type") != "superseded":
            continue
        cid = c["id"]
        if cid in MAPPING:
            replacement, reason = MAPPING[cid]
            c["superseded_by_claim_id"] = replacement
            c["superseded_reason"] = reason
            c["superseded_linked_session"] = 54
            updated += 1
        else:
            missing.append(cid)

    with open(CLAIMS_PATH, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)

    print(f"Superseded claims linked: {updated}")
    print(f"Without mapping: {missing}")
    print(f"Total superseded: {sum(1 for c in claims if c.get('claim_type')=='superseded')}")


if __name__ == "__main__":
    main()
