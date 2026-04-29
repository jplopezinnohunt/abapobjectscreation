"""
Brain updates for the UNESCO bank-reconciliation program family.
Session #057 · 2026-04-20 · follow-up to INC-000006906.

Adds annotations for 14 newly-extracted programs (YTBAE001/_HR, YTBAI001,
YTBAM001-004 + HR + _HR_UBO, YFI_BANK_RECONCILIATION + DATA + SEL).

Updates Claim 54 to note that YTBAE001 + YTBAE001_HR carry the inherited
MODE 'E' pattern but are DORMANT (severity lower).

Updates the INC-000006906 record to note the class-generalization result
(MODE 'E' present in 3 executables but hot only in YTBAE002).
"""
from __future__ import annotations
import json
from pathlib import Path
import datetime as _dt

REPO = Path(__file__).resolve().parent.parent.parent
ANN_FILE = REPO / "brain_v2" / "annotations" / "annotations.json"
CLAIMS_FILE = REPO / "brain_v2" / "claims" / "claims.json"
INC_FILE = REPO / "brain_v2" / "incidents" / "incidents.json"

ts = _dt.datetime.now().isoformat()

# ------------------ 1. Annotations ------------------
ann = json.loads(ANN_FILE.read_text(encoding="utf-8"))

def add_ann(obj_name: str, body: dict):
    if obj_name not in ann:
        ann[obj_name] = {"annotations": []}
    if "annotations" not in ann[obj_name]:
        ann[obj_name]["annotations"] = []
    body.setdefault("timestamp", ts)
    body.setdefault("session", 57)
    body.setdefault("evidence_tier", "TIER_1")
    body.setdefault("incident", "INC-000006906")
    ann[obj_name]["annotations"].append(body)

# YTBAE001 — the oldest HQ bank-clearing executable
add_ann("YTBAE001", {
    "finding": "Interactive bank-clearing executable bound to TCODE YTR1 (variant BK REC STATMT2) and YTR2 (variant BANK_RECONCIL). Uses AT LINE-SELECTION event to trigger PERFORM 19_CALL_TRANSACTION (defined in include YTBAM002) which fires BDC against FB08 + F-04. Declares C_MOD TYPE C VALUE 'E' at YTBAE001.abap:118 which is picked up by YTBAM002's CALL TRANSACTION sites. Authored A.ELMOUCH 2002-01-18, last modified A_AHOUNOU 2007-01-30, devclass YT, 312 LOC. DORMANT: only 1 TBTCO entry and it has STATUS=NULL/STRTDATE=NULL (never actually ran). Inherited MODE 'E' anti-pattern (Claim 54 pattern, milder form — dialog-only, not batch).",
    "tag": "CUSTOM_Y_PROGRAM",
    "flavor": "CUSTOM_Y_PROGRAM",
    "line": "118, 530-532",
    "related_objects": ["YTBAM002", "YTBAM003", "YTBAM004", "YTBAE002"],
})

add_ann("YTBAE001_HR", {
    "finding": "HR/payroll variant of YTBAE001, bound to TCODE YTR2_HR (variant BANK_RECONCIL). Includes YTBAM002_HR + YTBAM003_HR + YTBAM004_HR (YTBAE001_HR.abap:567-571). C_MOD TYPE C VALUE 'E' at :122. Tracks ZUONR_HR (HR assignment-number suffix) alongside standard ZUONR in T_BSIS workstruct. Authored A_AHOUNOU 2007-04-23. 331 LOC. DORMANT: zero TBTCO entries. Inherited MODE 'E' anti-pattern (Claim 54 pattern, milder form).",
    "tag": "CUSTOM_Y_PROGRAM",
    "flavor": "CUSTOM_Y_PROGRAM",
    "line": "122, 567-571",
    "related_objects": ["YTBAM002_HR", "YTBAM003_HR", "YTBAM004_HR", "YTBAE001", "YTBAE002"],
})

add_ann("YTBAI001", {
    "finding": "SMARTLINK CMI940 → MT940 file-format conversion report. Bound to TCODE YTR0 (variant YTBAI001). Reads OPEN DATASET from /usr/sap/D01/conversion/input/TITRBK03/sg2707.txt, writes to /usr/sap/D01/conversion/output/TITRBK03/sg2707out.txt. Filters header with constant C_SOG = ':25:SOGEFRPP/'. Authored A.ELMOUCH 2001-11-05 (the oldest source in the family). No BDC, no CALL TRANSACTION, no DB writes. 197 LOC. DORMANT: zero TBTCO runs AND the hardcoded filesystem path points to /usr/sap/D01/ which suggests this was deployed on D01 only, never promoted to P01 with a path rewrite. Open KU-2026-057-01: is SMARTLINK still in production use?",
    "tag": "CUSTOM_Y_PROGRAM",
    "flavor": "CUSTOM_Y_PROGRAM",
    "line": "29, 50-53",
    "related_objects": [],
})

add_ann("YTBAM001", {
    "finding": "INCLUDE — flow-control helpers for YTBAE001 family. 243 LOC. DORMANT / LEGACY: referenced only in historical SE38 F4 listing but NOT included by the current YTBAE001 source (YTBAE001 includes only YTBAM002/003/004 per :530-532). Authored A.ELMOUCH 2002-01-18, last modified N_MENARD 2023-10-11 (some 2023 maintenance touch though the include is no longer wired in).",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "related_objects": ["YTBAE001"],
})

add_ann("YTBAM002", {
    "finding": "INCLUDE — contains FORM 19_CALL_TRANSACTION (the FB08/F-04 BDC switchboard) used by YTBAE001. 4 CALL TRANSACTION sites at lines 214, 262, 310, 344 firing against FB08 (x2) and F-04 (x2). Inherits MODE from caller's C_MOD constant (no local MODE declaration in this specific extracted copy — verify vs live P01 if source diverges). 734 LOC. S.MAGAL 2002-01-18, A_AHOUNOU 2007-01-30. Devclass YT. Reachable only via YTBAE001 AT LINE-SELECTION event.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "line": "214, 262, 310, 344",
    "related_objects": ["YTBAE001", "YTBAM002_HR"],
})

add_ann("YTBAM002_HR", {
    "finding": "INCLUDE — HR variant of YTBAM002. 4 CALL TRANSACTION sites at 228, 276, 324, 358, each with MODE C_MOD explicit (C_MOD comes from YTBAE001_HR.abap:122 = 'E'). Hardcodes BDCDTAB-FVAL = 'UNES' at :807 (company code of HQ). Tracks ZUONR_HR for HR assignment-number. 740 LOC. A_AHOUNOU 2007-04-23, last A_AHOUNOU 2009-02-02. Carries Claim 54 MODE 'E' pattern but DORMANT because YTBAE001_HR is dormant.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "line": "228, 276, 324, 358, 807",
    "related_objects": ["YTBAE001_HR", "YTBAM002", "YTBAM002_HR_UBO"],
})

add_ann("YTBAM002_HR_UBO", {
    "finding": "INCLUDE — UBO field-office fork of YTBAM002_HR. Only functional diff vs YTBAM002_HR: BDCDTAB-FVAL = 'UBO' at :811 instead of 'UNES' (hardcoded company code). D_SIQUEIRA 2009-02-02 fork. Devclass YUBO. 740 LOC. LEGACY: NOT included by any executable today (YTBAE001_HR still includes YTBAM002_HR, not _HR_UBO). Candidate for TADIR-delete housekeeping. Same Claim 54 MODE 'E' pattern (inherited).",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "line": "231, 279, 327, 361, 811",
    "related_objects": ["YTBAM002_HR"],
})

add_ann("YTBAM003", {
    "finding": "INCLUDE — contains FORM 01_SELECT_BSIS (:51-69) and FORM 03_SELECT_BSEG (:79-121). Drives BSIS/BSEG selection via LOOP AT TSAKO (config-table of accounts configured for reconciliation), which is safe-by-construction against the empty-range bug: if TSAKO has zero matches, the LOOP simply doesn't iterate, no SELECTs fire. Contrast: YTBAE002 uses LDB SDF without this safety. 895 LOC. S.MAGAL 2002-01-18, A_AHOUNOU 2010-05-20. Reachable via YTBAE001.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "line": "51-69, 79-121",
    "related_objects": ["YTBAE001", "YTBAM003_HR"],
})

add_ann("YTBAM003_HR", {
    "finding": "INCLUDE — HR variant of YTBAM003. Same TSAKO-driven BSIS/BSEG selection but with additional ZUONR_HR handling. 949 LOC. A_AHOUNOU 2007-04-23 → last A_AHOUNOU 2014-01-30. Safe-by-construction against empty-range.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "related_objects": ["YTBAE001_HR", "YTBAM003"],
})

add_ann("YTBAM004", {
    "finding": "INCLUDE — table-control data (BDC screen-field constants, number-range helpers). 200 LOC. S.MAGAL (CREAT_USER: A.ARKWRIGHT) 2002-01-18. Byte-identical to YTBAM004_HR per diff.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "related_objects": ["YTBAE001", "YTBAM004_HR"],
})

add_ann("YTBAM004_HR", {
    "finding": "INCLUDE — byte-identical copy of YTBAM004 per diff; only the header comment and author differ. 200 LOC. A_AHOUNOU 2007-04-23. Included by YTBAE001_HR.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "related_objects": ["YTBAE001_HR", "YTBAM004"],
})

add_ann("YFI_BANK_RECONCILIATION", {
    "finding": "Modern (2023) read-only bank-reconciliation report. Bound to TCODE YFI_BANK1 (direct binding, no variant). 34 LOC main + 2 includes (DATA, SEL). Delegates all logic to OOP class YCL_FI_BANK_RECONCILIATION_BL (not yet extracted — KU-2026-057-03). Two output modes: P_DETAIL (ALV list) or P_DASH (ALV dashboard). NO BDC, NO CALL TRANSACTION, NO LDB. Authored N_MENARD 2023-04-07, last 2023-04-14. Devclass YA. ACTIVE (interactive only, no TBTCO jobs). NOT a replacement for YTBAE002 — complementary reporting view, not an action program.",
    "tag": "CUSTOM_Y_PROGRAM",
    "flavor": "CUSTOM_Y_PROGRAM",
    "related_objects": ["YFI_BANK_RECONCILIATION_DATA", "YFI_BANK_RECONCILIATION_SEL", "YCL_FI_BANK_RECONCILIATION_BL"],
})

add_ann("YFI_BANK_RECONCILIATION_DATA", {
    "finding": "INCLUDE — 3-line DATA declarations: GS_BSIS TYPE BSIS, GV_REPORT_TYPE(1) TYPE C, GO_BANK_RECONCILIATION_BL TYPE REF TO YCL_FI_BANK_RECONCILIATION_BL. N_MENARD 2023-04-07.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "related_objects": ["YFI_BANK_RECONCILIATION"],
})

add_ann("YFI_BANK_RECONCILIATION_SEL", {
    "finding": "INCLUDE — selection-screen definition + INITIALIZATION event. Params P_BUKRS, S_HKONT (SELECT-OPTIONS for HKONT), P_DATE_Z, P_DATE_O, radio P_DETAIL/P_DASH. INITIALIZATION calls YCL_FI_BANK_RECONCILIATION_BL=>INITIALIZE_HKONT( ) to auto-populate S_HKONT range (at :20) and auto-computes P_DATE_Z = last day of previous month and P_DATE_O = last day of two months ago (the 'O' = 'older' key date). N_MENARD 2023-04-07, last 2023-06-07.",
    "tag": "INCLUDE",
    "flavor": "CUSTOM_Y_INCLUDE",
    "line": "20, 22-41",
    "related_objects": ["YFI_BANK_RECONCILIATION", "YCL_FI_BANK_RECONCILIATION_BL"],
})

# Also add a Claim-54-sibling annotation on YTBAE002 for the class-generalization linkage
add_ann("YTBAE002", {
    "finding": "Class-generalization scan (Session #057): MODE 'E' + CALL TRANSACTION sibling search for the full bank-recon family found TWO additional inherited cases — YTBAE001 (C_MOD='E' at :118, via YTBAM002) and YTBAE001_HR (C_MOD='E' at :122, via YTBAM002_HR). Both are DORMANT (YTBAE001 has one stale TBTCO entry with STATUS=NULL; YTBAE001_HR has zero runs). YTBAE002 remains the only ACTIVE case of the anti-pattern (5 batch runs in Mar 2026 + J_DAVANE dialog dump 2026-04-20). Recommendation: prioritize YTBAE002 fix transport now; defer YTBAE001/_HR fix behind a decommission review (KU-2026-057-02 checks STAD for recent usage of YTR1/YTR2/YTR2_HR).",
    "tag": "CLASS_GENERALIZATION",
    "line": "27",
    "related_objects": ["YTBAE001", "YTBAE001_HR", "YTBAM002", "YTBAM002_HR"],
})

ANN_FILE.write_text(json.dumps(ann, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
print(f"[OK] Wrote annotations to {ANN_FILE.relative_to(REPO)}")

# ------------------ 2. Claim 54 extension ------------------
claims = json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))

for cl in claims:
    if cl.get("id") == 54:
        # Extend evidence_for with the class-generalization result
        cl.setdefault("evidence_for", []).append({
            "type": "extracted_code",
            "ref": "extracted_code/CUSTOM/BANK_RECONCILIATION/ (Session #057 family extraction)",
            "cite": "YTBAE001.abap:118 declares C_MOD TYPE C VALUE 'E'. YTBAE001 includes YTBAM002 at :530; YTBAM002's 4 CALL TRANSACTION sites (:214, 262, 310, 344) inherit that C_MOD. YTBAE001_HR.abap:122 declares C_MOD='E'; YTBAE001_HR includes YTBAM002_HR at :567; YTBAM002_HR's 4 CALL TRANSACTION sites (:228, 276, 324, 358) explicitly pass MODE C_MOD. Total: 3 executables (YTBAE001, YTBAE001_HR, YTBAE002) in the bank-reconciliation Y-stack carry the MODE 'E' + CALL TRANSACTION pattern. Of those, ONLY YTBAE002 is ACTIVE (5 scheduled runs Mar 2026, dialog dump 2026-04-20). YTBAE001 has 1 TBTCO entry with STATUS=NULL and no runtime; YTBAE001_HR has zero TBTCO entries. Recommendation: fix YTBAE002 now (transport pending), defer YTBAE001/_HR behind a TCODE YTR1/YTR2/YTR2_HR usage review (KU-2026-057-02).",
            "added_session": 57,
        })
        cl["class_generalization_summary"] = "3 executables carry MODE 'E' + CALL TRANSACTION (Claim 54 pattern). YTBAE002 ACTIVE; YTBAE001 + YTBAE001_HR DORMANT. See knowledge/domains/Treasury/bank_reconciliation_program_inventory.md §4.1."
        cl["class_generalization_session"] = 57
        print(f"[OK] Extended Claim {cl['id']}")

for cl in claims:
    if cl.get("id") == 53:
        # Note that Claim 53 does NOT extend to the rest of the family
        cl.setdefault("evidence_for", []).append({
            "type": "extracted_code",
            "ref": "extracted_code/CUSTOM/BANK_RECONCILIATION/ (Session #057 family extraction)",
            "cite": "Class-generalization scan of the full Y-stack found Claim 53 (empty-RANGE → unbounded-LDB-scan) to be UNIQUE to YTBAE002. YTBAE001 + YTBAE001_HR use a completely different selection mechanism: PERFORM 01_SELECT_BSIS in include YTBAM003 iterates TSAKO config-table (YTBAM003.abap:53-59) and is safe-by-construction (empty TSAKO → zero SELECTs, no unbounded scan). YFI_BANK_RECONCILIATION (2023) delegates to YCL_FI_BANK_RECONCILIATION_BL whose selection is user-controlled via S_HKONT SELECT-OPTION (YFI_BANK_RECONCILIATION_SEL.abap:6) — different design entirely. Therefore Claim 53 does NOT auto-extend to the rest of the family.",
            "added_session": 57,
        })
        cl["class_generalization_summary"] = "Claim 53 is UNIQUE to YTBAE002 among bank-reconciliation Y-programs. YTBAE001 family uses TSAKO-iterate which is safe; YFI_BANK_RECONCILIATION delegates to class. See bank_reconciliation_program_inventory.md §4.2."
        cl["class_generalization_session"] = 57
        print(f"[OK] Extended Claim {cl['id']}")

CLAIMS_FILE.write_text(json.dumps(claims, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
print(f"[OK] Wrote claims to {CLAIMS_FILE.relative_to(REPO)}")

# ------------------ 3. Incident record extension ------------------
inc = json.loads(INC_FILE.read_text(encoding="utf-8"))
# Inc structure is either list or dict
target_id = "INC-000006906"
if isinstance(inc, list):
    for row in inc:
        if row.get("id") == target_id or row.get("incident_id") == target_id:
            row.setdefault("related_objects", [])
            for obj in ["YTBAE001","YTBAE001_HR","YTBAI001",
                        "YTBAM001","YTBAM002","YTBAM002_HR","YTBAM002_HR_UBO",
                        "YTBAM003","YTBAM003_HR","YTBAM004","YTBAM004_HR",
                        "YFI_BANK_RECONCILIATION","YFI_BANK_RECONCILIATION_DATA","YFI_BANK_RECONCILIATION_SEL",
                        "YCL_FI_BANK_RECONCILIATION_BL"]:
                if obj not in row["related_objects"]:
                    row["related_objects"].append(obj)
            row["class_generalization"] = {
                "pattern_name": "MODE 'E' + CALL TRANSACTION + BDC chain during AT LINE-SELECTION or LDB fetch (Claim 54)",
                "affected_executables": ["YTBAE002 (ACTIVE, primary case)",
                                         "YTBAE001 (DORMANT, TCODE YTR1/YTR2, inherited via C_MOD → YTBAM002)",
                                         "YTBAE001_HR (DORMANT, TCODE YTR2_HR, inherited via C_MOD → YTBAM002_HR)"],
                "empty_range_pattern_name": "Empty range → unbounded LDB SDF scan (Claim 53)",
                "empty_range_affected": ["YTBAE002 ONLY"],
                "scanned_session": 57,
                "inventory_doc": "knowledge/domains/Treasury/bank_reconciliation_program_inventory.md",
            }
            row["family_inventory_doc"] = "knowledge/domains/Treasury/bank_reconciliation_program_inventory.md"
            row["family_inventory_session"] = 57
            print(f"[OK] Updated incident {target_id} (list shape)")
            break
elif isinstance(inc, dict):
    if target_id in inc:
        row = inc[target_id]
        row.setdefault("related_objects", [])
        for obj in ["YTBAE001","YTBAE001_HR","YTBAI001",
                    "YTBAM001","YTBAM002","YTBAM002_HR","YTBAM002_HR_UBO",
                    "YTBAM003","YTBAM003_HR","YTBAM004","YTBAM004_HR",
                    "YFI_BANK_RECONCILIATION","YFI_BANK_RECONCILIATION_DATA","YFI_BANK_RECONCILIATION_SEL",
                    "YCL_FI_BANK_RECONCILIATION_BL"]:
            if obj not in row["related_objects"]:
                row["related_objects"].append(obj)
        row["class_generalization"] = {
            "pattern_name": "MODE 'E' + CALL TRANSACTION + BDC chain during AT LINE-SELECTION or LDB fetch (Claim 54)",
            "affected_executables": ["YTBAE002 (ACTIVE, primary case)",
                                     "YTBAE001 (DORMANT, TCODE YTR1/YTR2, inherited via C_MOD → YTBAM002)",
                                     "YTBAE001_HR (DORMANT, TCODE YTR2_HR, inherited via C_MOD → YTBAM002_HR)"],
            "empty_range_pattern_name": "Empty range → unbounded LDB SDF scan (Claim 53)",
            "empty_range_affected": ["YTBAE002 ONLY"],
            "scanned_session": 57,
            "inventory_doc": "knowledge/domains/Treasury/bank_reconciliation_program_inventory.md",
        }
        row["family_inventory_doc"] = "knowledge/domains/Treasury/bank_reconciliation_program_inventory.md"
        row["family_inventory_session"] = 57
        print(f"[OK] Updated incident {target_id} (dict shape)")
    else:
        print(f"[WARN] {target_id} not in incidents.json")
else:
    print("[WARN] unexpected incidents.json type:", type(inc))

INC_FILE.write_text(json.dumps(inc, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
print(f"[OK] Wrote incidents to {INC_FILE.relative_to(REPO)}")
print("[DONE]")
