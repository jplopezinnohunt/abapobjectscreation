"""H48 findings — update KU-030/031/032 + add claim (UXR1/UXR2 asymmetry) + YRGGBS00 annotation."""
import json
from pathlib import Path

KU_PATH = Path("brain_v2/agi/known_unknowns.json")
CLAIMS_PATH = Path("brain_v2/claims/claims.json")
ANN_PATH = Path("brain_v2/annotations/annotations.json")


# ====== Update KU-030, KU-031, KU-032 ======
KU_UPDATES = {
    "KU-030": {
        "status": "PARTIALLY_ANSWERED",
        "answered_session": 54,
        "answer_partial": "Confirmed via code read (YRGGBS00_SOURCE.txt:998): line `* if bseg_xref1 = space.` IS commented out. UXR1 therefore unconditionally overwrites bseg_xref1 with USR05.Y_USERFO whenever the user has that param, silently losing any user-typed value. ASYMMETRY DISCOVERED: UXR2 (line 1026) STILL has the guard `IF bseg_xref2 = space` — only UXR1 is unguarded. This is the root cause of manual XREF drift observed in DQ-019 (21,754 Q1 2026 edits).",
        "still_unknown": "WHEN the guard was commented out and BY WHOM. Requires SE38 version history (SAP session, not available via RFC).",
        "findings_location": "YRGGBS00_SOURCE.txt:998 (line commented), YRGGBS00_SOURCE.txt:1026 (UXR2 guard intact)"
    },
    "KU-031": {
        "status": "ANSWERED",
        "answered_session": 54,
        "answer": "Substitution step prerequisites at UNESCO are PROCEDURAL (inside YRGGBS00 FORM bodies UXR1/UXR2/U910/UGLS/etc. via IF/SELECT logic), NOT declarative. GB922 stores the step sequence (SUBSTID+SUBSEQNR+CONSEQNR) and points to EXITSUBST=form_name. GB901 stores BOOLEAN expressions used by VALIDATIONS (VALID='UNES' has 12 steps in GB931), not by substitutions. GB905 and GB921 are SAP dictionary tables, not populated in P01 (the storage model for this SAP version uses GB922+GB901+GB903).",
        "findings_location": "Gold DB: GB922 (17 UNES rows), GB901 (583 rows with BOOLEXP), GB903 (3 rows); YRGGBS00_SOURCE.txt FORM bodies"
    },
    "KU-032": {
        "status": "INVESTIGATION_BLOCKED_LIVE_TRACE_REQUIRED",
        "scoped_session": 54,
        "scope": "UXR1 has NO filter by TCODE/BUKRS/callpoint context within the FORM body. Both UXR1 and UXR2 are registered as callpoint-3 (complete document) substitutions for UNES. Therefore the F110 vs F-53 asymmetry cannot come from the FORM itself. Two remaining hypotheses: (a) F110 batch context iterates BSEG lines differently, applying substitution only to vendor lines (SAP standard behavior with bseg-lifnr filter inside the callpoint dispatcher), (b) GGB1 or GB921 callpoint-level prerequisites filter tcode but are not extracted to Gold DB. Definitive answer needs ST05 SQL trace in TS3 with one F110 run + one F-53 posting to capture the actual substitution call sequence per BSEG line.",
        "blocks_on": "Live SAP session in TS3 — user-assisted work required. Cannot proceed autonomously via RFC."
    }
}

# ====== New claim: UXR1/UXR2 asymmetry ======
NEW_CLAIM = {
    "id": 47,
    "claim": "YRGGBS00 UXR1 (XREF1 substitution) has the guard `IF bseg_xref1 = space` COMMENTED OUT at line 998, while UXR2 (XREF2 substitution) at line 1026 KEEPS the equivalent guard `IF bseg_xref2 = space`. Consequence: UXR1 unconditionally overwrites user-typed XREF1 with USR05.Y_USERFO whenever the posting user has that SU3 param; UXR2 only auto-writes when blank. This asymmetry is the root cause of the systemic XREF drift pattern observed in DQ-019 (21,754 manual Q1 2026 XREF edits via FBL3N/FB02/FBL5N).",
    "claim_type": "defect",
    "confidence": "TIER_1",
    "evidence_for": [
        {
            "type": "source_code",
            "ref": "Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt:998",
            "cite": "`*  if bseg_xref1 = space.` — line commented out, breaking the guard. UXR1 then falls through to unconditional USR05 select + overwrite at line 1004.",
            "added_session": 54
        },
        {
            "type": "source_code",
            "ref": "Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt:1026",
            "cite": "`IF bseg_xref2 = space.` — line active in UXR2, maintaining the guard. UXR2 only enters USR05 select when XREF2 is blank.",
            "added_session": 54
        },
        {
            "type": "production_data",
            "ref": "DQ-019 finding",
            "cite": "21,754 manual XREF post-posting edits in Q1 2026 on UNES BELEG documents via FBL3N/FBL1N/FB02/FBL5N — consistent with users correcting silently-overwritten XREF1.",
            "added_session": 54
        }
    ],
    "evidence_against": None,
    "related_objects": ["YRGGBS00", "USR05", "BSEG.XREF1", "BSEG.XREF2"],
    "domain": "FI",
    "created_session": 54,
    "resolved_session": None,
    "status": "active"
}

# ====== New annotation for YRGGBS00 ======
YRGGBS00_ANNOTATION = {
    "tag": "CRITICAL",
    "finding": "UXR1 guard commented out (line 998) while UXR2 guard active (line 1026) — silent overwrite of user-typed XREF1. Asymmetric defect, root cause of DQ-019 systemic drift.",
    "timestamp": "2026-04-14T22:00:00Z",
    "session": "#054",
    "incident": "INC-000005240",
    "line": 998,
    "related": ["USR05.Y_USERFO", "YFO_CODES", "BSEG.XREF1", "UXR2"],
    "impact": "Every FI posting by a user with USR05.Y_USERFO populated has XREF1 silently overwritten, regardless of whether the user typed a value. Post-posting manual edits (FB02) become the de-facto correction mechanism."
}


def main():
    # 1. Update KUs
    with open(KU_PATH, "r", encoding="utf-8") as f:
        kus = json.load(f)
    for k in kus:
        if k["id"] in KU_UPDATES:
            k.update(KU_UPDATES[k["id"]])
    with open(KU_PATH, "w", encoding="utf-8") as f:
        json.dump(kus, f, indent=2, ensure_ascii=False)
    print(f"KUs updated: {len(KU_UPDATES)}")

    # 2. Add claim 47
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        claims = json.load(f)
    if not any(c["id"] == 47 for c in claims):
        claims.append(NEW_CLAIM)
        with open(CLAIMS_PATH, "w", encoding="utf-8") as f:
            json.dump(claims, f, indent=2, ensure_ascii=False)
        print(f"Claim #47 added. Total claims: {len(claims)}")
    else:
        print("Claim #47 already exists")

    # 3. Add annotation to YRGGBS00
    with open(ANN_PATH, "r", encoding="utf-8") as f:
        anns = json.load(f)
    if "YRGGBS00" not in anns:
        anns["YRGGBS00"] = {"annotations": []}
    anns["YRGGBS00"].setdefault("annotations", []).append(YRGGBS00_ANNOTATION)
    with open(ANN_PATH, "w", encoding="utf-8") as f:
        json.dump(anns, f, indent=2, ensure_ascii=False)
    print(f"YRGGBS00 annotation added. Total annotations for YRGGBS00: {len(anns['YRGGBS00']['annotations'])}")


if __name__ == "__main__":
    main()
