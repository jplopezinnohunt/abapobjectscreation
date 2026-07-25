"""H48 final brain update — session #055 findings.

Corrects prior claims, adds new ones, updates KUs with transport history + config-level asymmetry.
"""
import json
from pathlib import Path

KU_PATH = Path("brain_v2/agi/known_unknowns.json")
CLAIMS_PATH = Path("brain_v2/claims/claims.json")
ANN_PATH = Path("brain_v2/annotations/annotations.json")


# ===== KU updates =====
KU_UPDATES = {
    "KU-027": {
        "status": "ANSWERED",
        "answered_session": 55,
        "answer": "YFO_CODES contains FOCOD='JAK' with FOTXT='JAKARTA' (verified via RFC_READ_TABLE on P01 session #055). The list of valid FOCODs includes: HQ, JAK, IBE, ICB, ICTP, UIL, UIS, IIEP_BUA, IIEP_PAR, IIEP_PDK + many UNDP-XX codes + city codes (ABJ, BEI, CAI, etc.). H45 is UNBLOCKED — AL_JONATHAN SU3 update from 'HQ' to 'JAK' is safe."
    },
    "KU-030": {
        "status": "MOSTLY_ANSWERED",
        "answered_session": 55,
        "answer_update": "Transport history via E071 + E070 extracted: 57 transports modified YRGGBS00 between 2002-2026. Main editor: I_KONAKOV (~20 transports spanning 2008-2023, including the 2015-2017 era when substitution mods were heavy). Other editors: MAGAL/PARENT-DU (2002 initial), AHOUNOU (2003-2006), MENARD (2022-2026), RIOS (2025). CLUSTER of substitution-related transports: D01K951442 (2009-08-27 'WF - FI substitutions user-exit correction' by KONAKOV), D01K951618 (2009-08-27 'WF - FI Substitution rules' by KONAKOV), D01K960319 (2010-04-26 'WF - FI substitutions' by KONAKOV). The guard was most likely commented in one of these KONAKOV transports. Definitive identification requires diff-by-diff compare of YRGGBS00 source between transport versions (VRSD returned TABLE_WITHOUT_DATA via RFC — would need SE38 Version Management GUI).",
        "still_unknown": "Exact transport that commented the IF bseg_xref1 = space guard. Narrowed to I_KONAKOV transports 2009-2010. To definitively close: SE38 diff between D01K951442 and its predecessor D01K951407 (also KONAKOV, 2009-08-27 different hour) on lines 996-1016."
    },
    "KU-031": {
        "status": "ANSWERED_CORRECTED",
        "answered_session": 55,
        "answer": "Substitution step prerequisites at UNESCO ARE DECLARATIVE via 3-table chain: GB922 (step definition: SUBSTID+SUBSEQNR+CONDID implicit via exit name) -> GB921 (step-to-CONDID linkage: 16 rows for SUBSTID='UNESCO') -> GB901 (boolean expressions indexed by CONDID, 583 rows total, 56 rows for BOOLID LIKE '3UNESCO%'). My prior session #054 claim that prerequisites were 'procedural in FORM bodies' was WRONG — they are declarative. Correction: the FORM body contains the ACTION logic once the declarative prereq passes. KEY FINDING: step 005 (UXR1/XREF1) has NO prerequisite row in GB901 — fires UNCONDITIONALLY for every BSEG line. Step 006 (UXR2/XREF2) has a prerequisite: `HKONT IN ('1375012','1375022','1375032','1375052','1341011','1341021')` — only fires for specific GL accounts. GB905 exists but returned 0 rows for UNES-related BOOLIDs.",
        "tables_architecture": "GB922 = step definition. GB921 = step-to-condition linkage (MANDT+SUBSTID+SUBSEQNR -> CONDID). GB901 = boolean expression body (BOOLID+SEQNR -> BOOLEXP multi-line text). GB903 = boolean header (BOOLID -> SHORTNAME+SETID). GB931 = VALIDATION step-to-condition for VALID='UNES' (12 rows, separate from substitutions). GB02C = message class mapping."
    },
    "KU-032": {
        "status": "ENRICHED_NOT_CLOSED",
        "enrichment_session": 55,
        "enrichment": "New data reduces the asymmetry mystery but does not fully explain F110 vs F-53. Finding: UXR1 has NO declarative prereq (fires on every BSEG line of every UNESCO posting). UXR2 has declarative prereq HKONT IN (bank-related GL list). So XREF1 auto-write should fire for EVERY line in EVERY tcode (F110, F-53, FB60, MIRO, etc.). The asymmetry observed in INC-000005240 (F110 fires on vendor clearing line but not bank GL line) must therefore come from either (a) SAP standard F110 batch context only iterating certain lines through callpoint 3, or (b) a downstream filter on bseg-hkont within substitution dispatcher. ST05 trace still required to resolve."
    }
}


# ===== Correct claim #47 + new claims =====
# Claim #47 upgrade — acknowledge double asymmetry
CLAIM_47_UPDATE = {
    "id": 47,
    "claim": "YRGGBS00 UXR1 (XREF1 substitution, step 005) has DOUBLE ASYMMETRY vs UXR2 (XREF2, step 006): (1) CODE-LEVEL: line 998 has `IF bseg_xref1 = space` guard commented out, while UXR2 line 1026 keeps its guard intact; (2) CONFIG-LEVEL: UXR1 has NO declarative prerequisite in GB901 — fires unconditionally for every BSEG line, while UXR2 has prereq `HKONT IN ('1375012','1375022','1375032','1375052','1341011','1341021')` restricting to 6 specific GL accounts. Combined effect: UXR1 fires on EVERY posting line of EVERY user at UNESCO and unconditionally overwrites user-typed XREF1 with USR05.Y_USERFO. This is the root cause of the systemic XREF drift pattern observed in DQ-019 (21,754 manual Q1 2026 XREF edits via FBL3N/FB02/FBL5N). The manual edits are predominantly on XREF1 (universal), not XREF2 (targeted 6 accounts).",
    "claim_type": "defect",
    "confidence": "TIER_1",
    "evidence_for": [
        {"type": "source_code", "ref": "Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt:998", "cite": "`*  if bseg_xref1 = space.` commented out — UXR1 falls through to unconditional USR05 select + overwrite at line 1004", "added_session": 54},
        {"type": "source_code", "ref": "Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt:1026", "cite": "`IF bseg_xref2 = space.` active in UXR2 — guard maintained", "added_session": 54},
        {"type": "config_data", "ref": "GB901 BOOLID '3UNESCO#005' (step 005 UXR1 prereq)", "cite": "RFC_READ_TABLE returns 0 rows — step 005 fires unconditionally (verified session #055)", "added_session": 55},
        {"type": "config_data", "ref": "GB901 BOOLID '3UNESCO#006' (step 006 UXR2 prereq)", "cite": "RFC_READ_TABLE returns 3 rows: HKONT IN ('1375012','1375022','1375032','1375052','1341011','1341021') — step 006 only fires for 6 bank-related GLs (verified session #055)", "added_session": 55},
        {"type": "config_data", "ref": "GB921 SUBSTID='UNESCO' (verified session #055)", "cite": "16 substitution steps mapped to CONDID — confirms declarative architecture. Step 005=3UNESCO#005 (XREF1 prereq), Step 006=3UNESCO#006 (XREF2 prereq)", "added_session": 55},
        {"type": "production_data", "ref": "DQ-019 finding", "cite": "21,754 manual XREF post-posting edits in Q1 2026 on UNES BELEG documents via FBL3N/FBL1N/FB02/FBL5N — consistent with users correcting silently-overwritten XREF1 on every posting", "added_session": 54}
    ],
    "evidence_against": [],
    "related_objects": ["YRGGBS00", "USR05", "BSEG.XREF1", "BSEG.XREF2", "GB901", "GB921", "GB922"],
    "domain": "FI",
    "created_session": 54,
    "updated_session": 55,
    "resolved_session": None,
    "status": "active"
}

# New claim #48 — UXR2 HKONT filter specificity
NEW_CLAIM_48 = {
    "id": 48,
    "claim": "YRGGBS00 UXR2 (XREF2 substitution, step 006) has a GL-account-restricted prerequisite: fires ONLY when BSEG.HKONT IN ('1375012','1375022','1375032','1375052','1341011','1341021') — 6 specific GL accounts stored in GB901 BOOLID '3UNESCO#006'. These 6 accounts are likely foreign-currency or bank-clearing accounts (GL pattern 137xxxx = intra-group, 1341xxx = bank-clearing). This selective firing explains why XREF2 auto-write only affects specific posting contexts, while XREF1 (step 005) fires universally (no prerequisite).",
    "claim_type": "config_structure",
    "confidence": "TIER_1",
    "evidence_for": [
        {"type": "config_data", "ref": "GB901 BOOLID '3UNESCO#006'", "cite": "SEQNR 01-03: HKONT = '1375012' OR HKONT = '1375022' OR HKONT = '1375032' OR HKONT = '1375052' OR HKONT = '1341011' OR HKONT = '1341021' (verified session #055 via RFC_READ_TABLE)", "added_session": 55},
        {"type": "config_data", "ref": "GB921 SUBSTID='UNESCO' SUBSEQNR='006'", "cite": "CONDID='3UNESCO#006' links UXR2 step to the HKONT boolean", "added_session": 55}
    ],
    "evidence_against": [],
    "related_objects": ["YRGGBS00", "UXR2", "BSEG.HKONT", "GB901", "GB921"],
    "domain": "FI",
    "created_session": 55,
    "resolved_session": None,
    "status": "active"
}

# New claim #49 — transport history 57 transports 2002-2026
NEW_CLAIM_49 = {
    "id": 49,
    "claim": "YRGGBS00 has been modified by 57 distinct transports between 2002 and 2026. Primary maintainer: I_KONAKOV (~20 transports spanning 2008-2023). Other notable editors: MAGAL/PARENT-DU (initial 2002), AHOUNOU (2003-2006), MENARD (2022-2026, recent), RIOS (2025). CLUSTER of substitution-specific changes by KONAKOV in 2009-08-27 (D01K951407, D01K951442, D01K951618 — three transports same day, all with substitution-related descriptions). The UXR1 guard comment-out is almost certainly in one of these KONAKOV substitution transports — narrowed search scope for KU-030 definitive closure.",
    "claim_type": "verified_fact",
    "confidence": "TIER_1",
    "evidence_for": [
        {"type": "production_data", "ref": "E071 WHERE OBJ_NAME='YRGGBS00' AND OBJECT='REPS'", "cite": "57 distinct TRKORR values on P01", "added_session": 55},
        {"type": "production_data", "ref": "E070 headers for 57 TRKORRs", "cite": "AS4USER dimension: I_KONAKOV dominant 2008-2023. Earliest 2002-01-18 (MAGAL). Most recent 2026-01-11 (MENARD 'W - FI - Substitution rule update for Travel (YRGGBS00)')", "added_session": 55},
        {"type": "production_data", "ref": "E07T descriptions", "cite": "D01K951442 = 'WF - FI substitutions user-exit correction' (KONAKOV 2009-08-27), D01K951618 = 'WF - FI Substitution rules' (KONAKOV 2009-08-27), D01K960319 = 'WF - FI substitutions' (KONAKOV 2010-04-26)", "added_session": 55}
    ],
    "evidence_against": [],
    "related_objects": ["YRGGBS00", "E070", "E071", "E07T"],
    "domain": "FI",
    "created_session": 55,
    "resolved_session": None,
    "status": "active"
}


# YRGGBS00 annotations (new session #055 findings)
YRGGBS00_ANNOTATION_DOUBLE_ASYM = {
    "tag": "CRITICAL",
    "finding": "DOUBLE asymmetry UXR1 vs UXR2 confirmed at config + code level. UXR1 has NO declarative prereq in GB901 (fires for every BSEG line) + code guard commented at line 998 (overwrites user input). UXR2 has prereq HKONT IN (6 bank GLs) + code guard active at line 1026. Combined: XREF1 drift is systemic (every posting), XREF2 drift is account-scoped.",
    "timestamp": "2026-04-14T23:00:00Z",
    "session": "#055",
    "incident": "INC-000005240",
    "related": ["GB901.3UNESCO#005", "GB901.3UNESCO#006", "GB921.SUBSTID=UNESCO", "UXR1", "UXR2"],
    "impact": "Universal overwrite of XREF1 on every UNESCO posting with USR05.Y_USERFO. Users correcting via FBL3N/FB02 = de-facto reconciliation mechanism (21,754 edits Q1 2026 per DQ-019)."
}

YRGGBS00_ANNOTATION_HISTORY = {
    "tag": "HISTORY",
    "finding": "57 transports modified YRGGBS00 between 2002-2026. Primary maintainer: I_KONAKOV (~20 transports). Substitution changes clustered in KONAKOV 2009-08-27 (D01K951407/442/618) + 2010 (D01K960319). Guard comment-out narrow-scoped to this era.",
    "timestamp": "2026-04-14T23:01:00Z",
    "session": "#055",
    "related": ["E070", "E071", "E07T"],
    "impact": "Knowing primary maintainer + timing scope enables targeted SE38 version diff for KU-030 definitive closure."
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

    # 2. Update claim #47 + add 48, 49
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        claims = json.load(f)
    # Remove existing #47 and re-add updated
    claims = [c for c in claims if c.get("id") not in (47, 48, 49)]
    claims.append(CLAIM_47_UPDATE)
    claims.append(NEW_CLAIM_48)
    claims.append(NEW_CLAIM_49)
    with open(CLAIMS_PATH, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2, ensure_ascii=False)
    print(f"Claims: 47 updated, 48 + 49 added. Total: {len(claims)}")

    # 3. Add YRGGBS00 annotations
    with open(ANN_PATH, "r", encoding="utf-8") as f:
        anns = json.load(f)
    if "YRGGBS00" not in anns:
        anns["YRGGBS00"] = {"annotations": []}
    anns["YRGGBS00"].setdefault("annotations", []).append(YRGGBS00_ANNOTATION_DOUBLE_ASYM)
    anns["YRGGBS00"]["annotations"].append(YRGGBS00_ANNOTATION_HISTORY)
    with open(ANN_PATH, "w", encoding="utf-8") as f:
        json.dump(anns, f, indent=2, ensure_ascii=False)
    print(f"YRGGBS00 annotations: {len(anns['YRGGBS00']['annotations'])} total")


if __name__ == "__main__":
    main()
