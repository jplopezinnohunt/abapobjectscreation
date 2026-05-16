"""Session #075 brain update — REF01/REF02 ownership correction.

Triggered by user question: "how does FI_FILL_FPAYHX feed REF01 for /CGI_XML_CT_UNESCO?"

Findings recorded:
- Correct CGI call chain (SAPFPAYM Event 05 → FI_PAYMEDIUM_DMEE_CGI_05 → factory → GENERIC_CALL).
- Correct attribution of REF01 (paying-co ADRC) vs REF02 (vendor ADRC). Previous brain
  annotations said "ADRC of the LIFNR" for REF01 — incorrect.
- New DQ flag on v001_change_matrix.csv row 1 (SEPA Cdtr/StrtNm → FPAYP/REF01) which under
  the corrected understanding would render paying-co address in <Cdtr><StrtNm>, not vendor.

CP-003 anchor: code citations are explicit. All evidence is path:line.
"""
import json
import datetime
import pathlib

BASE = pathlib.Path(__file__).resolve().parents[2]
ANN_PATH = BASE / "brain_v2" / "annotations" / "annotations.json"
CLA_PATH = BASE / "brain_v2" / "claims" / "claims.json"
DQ_PATH  = BASE / "brain_v2" / "agi" / "data_quality_issues.json"

NOW = datetime.datetime.now().isoformat(timespec="seconds")
SESSION = "#075"

# --- Load ---
with open(ANN_PATH, encoding="utf-8") as f:
    annotations = json.load(f)
with open(CLA_PATH, encoding="utf-8") as f:
    claims = json.load(f)
with open(DQ_PATH, encoding="utf-8") as f:
    dq = json.load(f)

# ============================================================
# 1) CORRECT existing annotation on FI_PAYMEDIUM_DMEE_CGI_05
# ============================================================
correction_cgi05 = {
    "tag": "REF01_REF02_OWNERSHIP_CORRECTION",
    "finding": (
        "CORRECTION to prior #074 annotation 'ADRC of the LIFNR': the actual code in "
        "CL_IDFI_CGI_CALL05_GENERIC->GENERIC_CALL (CM005.abap:89-127) reads "
        "cl_idfi_cgi_dmee_utils=>get_company_address(iv_bukrs=is_fpayh-zbukr, iv_nation=...) "
        "which loads ADRC of T001(zbukr).ADRNR — i.e. PAYING-COMPANY address, NOT vendor. "
        "REF01 is therefore Dbtr-context (the run's ZBUKR cocode address). "
        "Vendor address lives in REF02 (CM005.abap:138-209): "
        "  - if FPAYH-ZADNR populated AND GPA1T != '14': ADDR_SELECT_ADRC_SINGLE(zadnr) → ADRC of vendor; "
        "  - if FPAYH-ZADNR initial OR GPA1T = '14' (CPD/one-time): READ_BSEC by xbelnr/xbukrs from "
        "    fpayp-doc2r → BSEC-PSTL2/PSTLZ/STRAS, then split_street_house_no → REF02+10/+20. "
        "REF01 byte layout (CM005:89-127): [0..60]=ADRC.STREET, [60..80]=BUILDING (20 bytes), "
        "[80..90]=POST_CODE1, [90..100]=REGION, [100..110]=HOUSE_NUM1, [110..116]=batch_booking. "
        "REF06[0..40]=CITY1 (falls back to is_fpayhx-ort1z if empty). "
        "FPAYP rows: same paying-co address written via LOOP at CM005:108-115, with refresh of "
        "ls_adrc to ls_fpayp-bukrs's company-address if multi-cocode run (CM005:102-107)."
    ),
    "impact": (
        "Two prior brain artifacts must be re-read with this lens: "
        "(a) Brain annotation on FPAYHX-REF01 #074 'from ADRC of the LIFNR' — wrong, see correction below. "
        "(b) v001_change_matrix.csv row 1 SEPA Cdtr/StrtNm → FPAYP/REF01: under the corrected "
        "understanding this binding would render paying-co street in <Cdtr><StrtNm>. The 2026-05-07 "
        "BERTOLDINI empirical test rendered vendor street there ('BFM/FAS/PAY'), so the actual "
        "deployed V001 binding likely differs from the matrix as written OR the test used a "
        "different binding path. Flagged as DQ open question (see data_quality_issues.json)."
    ),
    "field": "FPAYHX-REF01/REF02 ownership",
    "related": [
        "CL_IDFI_CGI_CALL05_GENERIC",
        "CL_IDFI_CGI_CALL05_FACTORY",
        "FPAYHX-REF01",
        "FPAYHX-REF02",
        "T001",
        "ADRC",
        "BSEC",
        "FI_PAYM_MEDIUM_OPEN",
        "FI_PAYM_MEDIUM_WRITE",
        "TFPM042FB",
    ],
    "evidence": [
        {"type": "source_code",
         "ref": "extracted_code/FI/DMEE_full_inventory/CL_IDFI_CGI_CALL05_GENERIC_CM005.abap:89-127",
         "cite": "ls_adrc = get_company_address(zbukr,...) → cs_fpayhx_fref-ref01+0(60) = ls_adrc-street …"},
        {"type": "source_code",
         "ref": "extracted_code/FI/DMEE_full_inventory/CL_IDFI_CGI_CALL05_GENERIC_CM005.abap:138-209",
         "cite": "CPD branch reads BSEC by doc2r; non-CPD branch ADDR_SELECT_ADRC_SINGLE(zadnr)"},
        {"type": "source_code",
         "ref": "extracted_code/FI/DMEE_full_inventory/CL_IDFI_CGI_CALL05_FACTORY_CM001.abap:11-67",
         "cite": "Factory dispatches by LAND1 from TFPM042F, fallback UBISO/UBNKS"},
        {"type": "source_code",
         "ref": "extracted_code/FI/SAPFPAYM/funcs/FI_PAYMEDIUM_DMEE_CGI_05.abap:30-54",
         "cite": "FM is the Event 05 entry point; instantiates factory and calls fill_fpay_fref"},
        {"type": "source_code",
         "ref": "extracted_code/FI/SAPFPAYM/FPAYM_GET.abap:54-85",
         "cite": "SAPFPAYM driver calls FI_PAYM_MEDIUM_OPEN/WRITE which fires Event 05 per format"},
    ],
    "timestamp": NOW,
    "session": SESSION,
}

annotations["FI_PAYMEDIUM_DMEE_CGI_05"]["annotations"].append(correction_cgi05)
annotations["FI_PAYMEDIUM_DMEE_CGI_05"]["last_updated"] = NOW

# Same correction for FPAYHX-REF01 annotation (different impact text)
correction_ref01 = {
    "tag": "DBTR_NOT_VENDOR_CORRECTION",
    "finding": (
        "CORRECTION to prior #074 annotation 'from ADRC of the LIFNR': REF01 is populated from "
        "ADRC of the paying-company (T001(zbukr).ADRNR), via "
        "cl_idfi_cgi_dmee_utils=>get_company_address(zbukr, nation) in "
        "CL_IDFI_CGI_CALL05_GENERIC->GENERIC_CALL (CM005.abap:89-127). REF01 is therefore "
        "Dbtr-context. The vendor address (Cdtr-context) lives in REF02 (CM005:138-209)."
    ),
    "impact": (
        "Trees binding to FPAYHX-REF01 for <Dbtr> tags render paying-co address (correct). "
        "Trees binding to FPAYHX-REF01 for <Cdtr> tags would render paying-co address as the "
        "creditor's — inverse of what's intended. The historic SCSA-staff-dept-code bug therefore "
        "lives in REF02 (vendor ADRC blind read), not REF01."
    ),
    "field": "REF01",
    "related": ["FPAYHX-REF02", "CL_IDFI_CGI_CALL05_GENERIC", "T001", "ADRC"],
    "evidence": correction_cgi05["evidence"],
    "timestamp": NOW,
    "session": SESSION,
}
annotations["FPAYHX-REF01"]["annotations"].append(correction_ref01)
annotations["FPAYHX-REF01"]["last_updated"] = NOW

# New annotation on CL_IDFI_CGI_CALL05_GENERIC — the full call chain
chain_annotation = {
    "tag": "CALL_CHAIN_EVENT05_CGI",
    "finding": (
        "End-to-end call chain that fills FPAYHX_FREF for /CGI_XML_CT_UNESCO (the user's "
        "mental model 'FI_FILL_FPAYHX' resolves to fill_fpay_fref on this class hierarchy):\n"
        "  1. SAPFPAYM LDB FPMF driver — GET fpayh / GET fpayp / GET fpayh LATE.\n"
        "     [extracted_code/FI/SAPFPAYM/FPAYM_GET.abap:54-85]\n"
        "  2. FI_PAYM_MEDIUM_OPEN (first item) + FI_PAYM_MEDIUM_WRITE (each item) — "
        "     internally fire Event 05 per format via TFPM042FB lookup.\n"
        "  3. Event 05 FM for /CGI_XML_CT_UNESCO (and all CGI variants): "
        "     FI_PAYMEDIUM_DMEE_CGI_05. [extracted_code/FI/SAPFPAYM/funcs/FI_PAYMEDIUM_DMEE_CGI_05.abap:16-54]\n"
        "  4. FM instantiates cl_idfi_cgi_call05_factory=>get_instance(...). Factory "
        "     dispatches by LAND1 from TFPM042F-LAND1 (UNESCO format → FR), with fallback "
        "     FPAYHX-UBISO then FPAYHX-UBNKS. Tries CL_IDFI_CGI_CALL05_<ISO>; if cx_sy_create_object_error, "
        "     falls back to CL_IDFI_CGI_CALL05_GENERIC. Special-case: LI dispatches to CH.\n"
        "     [extracted_code/FI/DMEE_full_inventory/CL_IDFI_CGI_CALL05_FACTORY_CM001.abap:1-69]\n"
        "  5. FM calls ro_instance->fill_fpay_fref(...). This orchestrator method (not extracted "
        "     by name) internally invokes — in this order: GENERIC_CALL → COUNTRY_SPECIFIC_CALL → "
        "     CHECK_CHANGES. GENERIC_CALL writes REF01..REF12; COUNTRY_SPECIFIC_CALL adds country "
        "     overrides (FR=REF14 SIRET only; DE/IT/GB also REF14-only); CHECK_CHANGES does byte-by-byte "
        "     compare and raises change_found if a country method overwrote a non-empty generic char "
        "     (W011 IDFIPAYM_MSG logged to FBPM).\n"
        "     [CL_IDFI_CGI_CALL05_GENERIC_CM005.abap (GENERIC_CALL), CL_IDFI_CGI_CALL05_FR_CM001.abap "
        "     (COUNTRY_SPECIFIC_CALL), CL_IDFI_CGI_CALL05_GENERIC_CM001.abap (CHECK_CHANGES), "
        "     CL_IDFI_CGI_CALL05_GENERIC_CM003.abap (compare_structures), "
        "     CL_IDFI_CGI_CALL05_GENERIC_CM002.abap (compare_by_chars)]\n"
        "Key consequence: country classes CANNOT override REF01/REF02/REF06 (the address fields) "
        "because CHECK_CHANGES blocks any non-empty-position overwrite. Address-mapping "
        "customization is impossible at the country-class layer; it must happen either "
        "(a) inside GENERIC_CALL via SAP std support package, (b) by replacing the registered "
        "TFPM042FB Event 05 FM, or (c) at the DMEE tree leaf via an EXIT_FUNC."
    ),
    "impact": (
        "Closes the user's mental-model question 'how does FI_FILL_FPAYHX feed REF01'. Anchors "
        "vocabulary: there is no SAP-std FM named FI_FILL_FPAYHX; the conceptual filler is method "
        "fill_fpay_fref on the if_idfi_cgi_call05 instance returned by cl_idfi_cgi_call05_factory."
    ),
    "field": "fill_fpay_fref method orchestration",
    "related": [
        "FI_PAYMEDIUM_DMEE_CGI_05",
        "CL_IDFI_CGI_CALL05_FACTORY",
        "CL_IDFI_CGI_CALL05_FR",
        "CL_IDFI_CGI_CALL05_DE",
        "CL_IDFI_CGI_CALL05_IT",
        "CL_IDFI_CGI_CALL05_GB",
        "FPAYHX_FREF",
        "TFPM042F",
        "TFPM042FB",
        "SAPFPAYM",
    ],
    "evidence": correction_cgi05["evidence"],
    "timestamp": NOW,
    "session": SESSION,
}
if "CL_IDFI_CGI_CALL05_GENERIC" not in annotations:
    annotations["CL_IDFI_CGI_CALL05_GENERIC"] = {
        "annotations": [],
        "first_seen": NOW,
        "last_updated": NOW,
    }
annotations["CL_IDFI_CGI_CALL05_GENERIC"]["annotations"].append(chain_annotation)
annotations["CL_IDFI_CGI_CALL05_GENERIC"]["last_updated"] = NOW

# ============================================================
# 2) Data Quality flag — the matrix row 1 vs the code reality
# ============================================================
new_dq = {
    "id": f"DQ-{NOW[:10]}-001",
    "title": "v001_change_matrix.csv row 1 (SEPA Cdtr/StrtNm → FPAYP/REF01) contradicts code reading",
    "severity": "HIGH",
    "domain": "Payment",
    "discovered_session": SESSION,
    "discovered_at": NOW,
    "summary": (
        "Matrix row 1 binds /SEPA_CT_UNES Cdtr/StrtNm to FPAYP/REF01 with rationale "
        "'CM005 line 109 writes Cdtr to FPAYP-REF01'. Direct code reading of "
        "CL_IDFI_CGI_CALL05_GENERIC->GENERIC_CALL line 108-115 shows the LOOP writes "
        "<fs_fpayp>-ref01+0(60) = ls_adrc-street where ls_adrc was loaded via "
        "get_company_address(zbukr) — i.e. PAYING-CO address, not vendor. "
        "Under this code path, the matrix-row-1 binding would render UNESCO HQ street as "
        "<Cdtr><StrtNm>. Empirical 2026-05-07 BERTOLDINI test rendered VENDOR street "
        "('BFM/FAS/PAY') under V001, which is inconsistent with the matrix-row-1 design."
    ),
    "candidate_explanations": [
        "(A) The actual V001 binding deployed to D01 SEPA tree differs from matrix-row-1 — "
        "the deployed binding uses FPAYH-ZSTRA (vendor street Z-field) directly, and the "
        "matrix row 1 is forward-design only.",
        "(B) FPAYP-REF01 layout for SEPA differs from FPAYHX-REF01 for CGI — but matrix row 1 "
        "says they're identical (CM005 line 109 cite).",
        "(C) There's another code path that overwrites FPAYP-REF01 with vendor data after "
        "GENERIC_CALL (e.g. a BAdI or another Event)."
    ],
    "verification_plan": [
        "(1) RFC-extract DMEE_TREE_NODE WHERE TREE_ID='/SEPA_CT_UNES' AND VERSION='001' for "
        "node N_3513093480 (per matrix row 1) — read MP_SC_TAB and MP_SC_FLD.",
        "(2) If (1) returns MP_SC_TAB=FPAYP, MP_SC_FLD=REF01, then trace the V001 BERTOLDINI "
        "F110 run on 2026-05-07 — check whether SAPFPAYM_MERGE bypassed CGI_05 entirely (using "
        "ZSAPFPAYM_REPLAY path) which would explain a different REF01 population.",
        "(3) Examine ZSAPFPAYM_REPLAY's FPAYHX/FPAYP construction — does it call FI_PAYMEDIUM_DMEE_CGI_05 "
        "or pre-populate REF01 from REGUH/FPAYH-ZSTRA?"
    ],
    "blocks": "Phase 5 V001 SEPA cutover — must not release until matrix row 1 vs code reality is reconciled",
    "status": "OPEN",
    "owner": "next session",
}
if "issues" not in dq:
    dq = {"issues": dq if isinstance(dq, list) else [], "_meta": {"created": NOW}}
if isinstance(dq, list):
    dq = {"issues": dq, "_meta": {"created": NOW}}
if "issues" not in dq:
    dq["issues"] = []
dq["issues"].append(new_dq)

# ============================================================
# 3) Save all three artifacts
# ============================================================
with open(ANN_PATH, "w", encoding="utf-8") as f:
    json.dump(annotations, f, indent=2, ensure_ascii=False)
with open(CLA_PATH, "w", encoding="utf-8") as f:
    json.dump(claims, f, indent=2, ensure_ascii=False)
with open(DQ_PATH, "w", encoding="utf-8") as f:
    json.dump(dq, f, indent=2, ensure_ascii=False)

print(f"OK — annotations updated on: FI_PAYMEDIUM_DMEE_CGI_05, FPAYHX-REF01, CL_IDFI_CGI_CALL05_GENERIC")
print(f"OK — new DQ open issue: {new_dq['id']}")
print(f"Session: {SESSION}  timestamp: {NOW}")
