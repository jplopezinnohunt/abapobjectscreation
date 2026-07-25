# -*- coding: utf-8 -*-
"""
Add INC-000005240 annotations to brain_v2/annotations/annotations.json.

Objects to annotate (from INC-000005240 verified findings):
  - YRGGBS00 (the custom form pool)
  - YRGGBS00/UXR1, UXR2, UZLS, U915, U916, U917 (the specific forms)
  - USR05 + USR05.Y_USERFO
  - YFO_CODES (whitelist dictionary)
  - PA0001 / PA0105 (HR cross-reference tables)
  - VALID='UNES' (GGB0 validation header)
  - SUBSTID='UNESCO' (GGB1 substitution rule)
  - GB93, GB931 (validation header/steps)
  - GB901, GB922 (Boolean expressions / substitution values)
  - T80D (form pool registration)
  - BSEG.XREF1, BSEG.XREF2, BSEG.ZLSCH (the affected fields)
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation\brain_v2")
ann_path = ROOT / "annotations/annotations.json"
ann = json.loads(ann_path.read_text(encoding="utf-8"))

SESSION = "#51"
TS = datetime.utcnow().isoformat() + "Z"
INCIDENT = "INC-000005240"
ANALYSIS_DOC = "knowledge/incidents/INC-000005240_xref_office_substitution.md"


def ensure_object(obj_name, domain, obj_type):
    """Ensure the annotations dict has an entry for this object."""
    if obj_name not in ann:
        ann[obj_name] = {"annotations": [], "domain": domain, "type": obj_type}
    elif not isinstance(ann[obj_name], dict):
        # legacy format — wrap
        ann[obj_name] = {"annotations": list(ann[obj_name]) if isinstance(ann[obj_name], list) else [], "domain": domain, "type": obj_type}
    if "annotations" not in ann[obj_name]:
        ann[obj_name]["annotations"] = []
    ann[obj_name].setdefault("domain", domain)
    ann[obj_name].setdefault("type", obj_type)


def add_annotation(obj_name, finding, tag="INCIDENT_FINDING", impact=None, related=None):
    """Add a new annotation entry to an object (idempotent-ish via finding text hash)."""
    entries = ann[obj_name]["annotations"]
    # Skip if an entry with the same finding already exists
    for e in entries:
        if isinstance(e, dict) and e.get("finding") == finding:
            return False
    entry = {
        "tag": tag,
        "finding": finding,
        "timestamp": TS,
        "session": SESSION,
        "incident": INCIDENT,
        "analysis_doc": ANALYSIS_DOC,
    }
    if impact:
        entry["impact"] = impact
    if related:
        entry["related"] = related
    entries.append(entry)
    return True


# ==================== YRGGBS00 form pool ====================
ensure_object("YRGGBS00", "FI", "ABAP_INCLUDE")
add_annotation(
    "YRGGBS00",
    "Custom form pool registered via T80D ARBGB='GBLS' (substitution) AND ARBGB='GBLR' (validation) for the FI module. Both the GGB1 substitution framework (SUBSTID='UNESCO') and the GGB0 validation framework (VALID='UNES') dispatch exit-call steps to forms in this pool. Forms include UXR1/UXR2/UZLS (XREF office tagging), U915/U916/U917 (validation checks), UAEP/UATF (asset), U910 (business area), U901/U902/U904/U908 (treasury/payment), UIT1-4 (ICTP MM postings).",
    tag="ARCHITECTURE",
    related=["T80D", "SUBSTID=UNESCO", "VALID=UNES"],
)

# ==================== UXR1 ====================
ensure_object("YRGGBS00/UXR1", "FI", "ABAP_FORM")
add_annotation(
    "YRGGBS00/UXR1",
    "Registered at YRGGBS00_SOURCE.txt:230 as substitution exit 'UXR1' (XREF1 field substitution). Body at lines 996-1016. Unconditionally reads USR05 WHERE BNAME=SY-UNAME AND PARID='Y_USERFO' and writes the value to bseg_xref1. Original guard 'IF bseg_xref1 = space' at line 998 is commented out — UXR1 ALWAYS overwrites, even if the user typed a value on the screen. After writing, validates against YFO_CODES.FOCOD and raises w018 ZFI warning (non-blocking) if missing.",
    tag="CODE_BEHAVIOR",
    impact="Writes posting user's office code to every BSEG line at callpoint 3 regardless of TCODE/KOART. Has an in-code dictionary check but it only catches dictionary misses, not wrong-but-valid codes.",
    related=["USR05.Y_USERFO", "YFO_CODES", "BSEG.XREF1"],
)

# ==================== UXR2 ====================
ensure_object("YRGGBS00/UXR2", "FI", "ABAP_FORM")
add_annotation(
    "YRGGBS00/UXR2",
    "Registered at YRGGBS00_SOURCE.txt:235 as substitution exit 'UXR2' (XREF2 field substitution). Body at lines 1024-1041. ASYMMETRIC VALIDATION: (a) IF bseg_xref2 = space (auto-write branch from USR05) — NO validation against YFO_CODES, trusts USR05 blindly. (b) ELSE branch (user typed a value on screen) — SELECT YFO_CODES and raise e018 ZFI HARD error if missing. This asymmetry means wrong master data (USR05) propagates silently while manual typing errors are blocked. On F-53, the screen hides XREF2 so UXR2 always takes the SPACE branch → no validation.",
    tag="CODE_BEHAVIOR",
    impact="Is the main vector for AL_JONATHAN-class master-data errors propagating to XREF2 silently. The asymmetric validation design was likely intended to protect against typos, but it fails to protect against stale user parameters.",
    related=["USR05.Y_USERFO", "YFO_CODES", "BSEG.XREF2"],
)

# ==================== UZLS ====================
ensure_object("YRGGBS00/UZLS", "Treasury", "ABAP_FORM")
add_annotation(
    "YRGGBS00/UZLS",
    "Registered at YRGGBS00_SOURCE.txt:240 as substitution exit 'UZLS' (ZLSCH field substitution). Body at lines 1050-1119. Derives BSEG-ZLSCH (payment method) from BSEG-XREF2 per company code. Special case: IF bseg-xref2(4) <> 'UNDP' → CASE bukrs... ENDCASE. For UNES, XREF2='HQ' keeps ZLSCH at default; non-HQ forces ZLSCH='O' (field-office outbound). Similar rules for UBO/BRZ, UIS/UIS, IBE/IBE, IIEP/IIEP_PAR. UNDP-prefixed XREF2 gets ZLSCH='U'. This is the downstream consumer of UXR2's output — wrong XREF2 causes wrong payment method routing at F110/BCM time.",
    tag="CODE_BEHAVIOR",
    impact="Wrong XREF2 → wrong ZLSCH → wrong payment method → wrong DMEE format → wrong house bank → misrouted payment. Single-point chain.",
    related=["BSEG.XREF2", "BSEG.ZLSCH", "F110", "DMEE"],
)

# ==================== U915 ====================
ensure_object("YRGGBS00/U915", "FI", "ABAP_FORM")
add_annotation(
    "YRGGBS00/U915",
    "Validation exit (VALID='UNES' VALSEQNR=011, CHECKID='2UNES###011'). Body at YRGGBS00_SOURCE.txt:1499-1519. Returns b_false if the vendor has >1 bank account in LFBK and no BVTYP is specified on the line. Skips BSCHL 26/39 (down-payment clearing). Fires only on invoice-entry TCODEs via CONDID '1UNES###011' (invoice TCODE list + KOART='K'). Does NOT reference or check BSEG-XREF fields.",
    tag="CODE_BEHAVIOR",
    impact="Protects against ambiguous vendor bank selection but does NOT protect against wrong XREF values. Not a useful safety net for XREF-related incidents.",
    related=["VALID=UNES", "LFBK"],
)

# ==================== U916 ====================
ensure_object("YRGGBS00/U916", "FI", "ABAP_FORM")
add_annotation(
    "YRGGBS00/U916",
    "Validation exit (VALID='UNES' VALSEQNR=009, CHECKID='2UNES###012'). Body at YRGGBS00_SOURCE.txt:1525-1541. Fund GL restriction: for FISTL='UNESCO' allows HKONT in a fixed list of 6 GLs, otherwise requires HKONT='0006043011'. Severity I (informational only — does not block). Does NOT reference or check BSEG-XREF fields.",
    tag="CODE_BEHAVIOR",
    related=["VALID=UNES"],
)

# ==================== U917 ====================
ensure_object("YRGGBS00/U917", "FI", "ABAP_FORM")
add_annotation(
    "YRGGBS00/U917",
    "Validation exit (VALID='UNES' VALSEQNR=012, CHECKID='2UNES###009'). Body at YRGGBS00_SOURCE.txt:1543-1590. Checks SCB (State Central Bank) indicator LZBKZ consistency with vendor's bank country. Reads LFBK.BANKS; if LZBKZ is filled, its first 2 chars must match. If LZBKZ empty, checks YTFI_PPC_STRUC for PPC_VAR/PPC_DESCR requirement. Skips BSCHL 26/39. Fires only on invoice-entry TCODEs via CONDID '1UNES###009'. Does NOT reference or check BSEG-XREF fields.",
    tag="CODE_BEHAVIOR",
    impact="Protects against SCB indicator mismatches for cross-border vendor payments but does NOT protect against wrong XREF values.",
    related=["VALID=UNES", "LFBK", "YTFI_PPC_STRUC"],
)

# ==================== USR05 ====================
ensure_object("USR05", "BASIS", "SAP_TABLE")
add_annotation(
    "USR05",
    "User parameters table (SU3). At UNESCO, the Y_USERFO parameter on USR05 drives office-code substitution on BSEG.XREF1/XREF2 via YRGGBS00 forms UXR1/UXR2. There is NO mechanism that keeps USR05.Y_USERFO in sync with HR master (PA0001.WERKS/BTRTL). A user's finance office code can drift from their HR personnel area with no detection.",
    tag="DATA_MODEL",
    related=["USR05.Y_USERFO", "YRGGBS00/UXR1", "YRGGBS00/UXR2"],
)

# ==================== USR05.Y_USERFO ====================
ensure_object("USR05.Y_USERFO", "Treasury", "USER_PARAMETER")
add_annotation(
    "USR05.Y_USERFO",
    "SU3 parameter on USR05 containing the UNESCO office code for the user (HQ, JAK, YAO, KAB, DAK, BRZ, IIEP_PAR, UIS, IBE, etc.). Read by YRGGBS00 forms UXR1, UXR2 (and the commented-out legacy UZLS branch) at FI posting time to populate BSEG-XREF1/BSEG-XREF2 with the originating office tag. Maintained via SU01/SU3 as free-text — no validation at maintenance time, no HR alignment, no automated drift detection. This is the single driver of AL_JONATHAN's INC-000005240 ticket.",
    tag="POSTING_DRIVER",
    impact="HIGH — any drift between this parameter and the user's actual office silently mis-tags every FI document they post. No runtime validation anywhere in the UNES framework catches wrong values.",
    related=["YRGGBS00/UXR1", "YRGGBS00/UXR2", "YFO_CODES", "PA0001.BTRTL"],
)

# ==================== YFO_CODES ====================
ensure_object("YFO_CODES", "Treasury", "CUSTOM_TABLE")
add_annotation(
    "YFO_CODES",
    "UNESCO custom whitelist table for valid Field Office codes. Minimum columns FOCOD (office code) + PAYMT (payment method). Used by YRGGBS00 UXR1 (after writing XREF1, validates against FOCOD; warns w018 ZFI if missing) and YRGGBS00 UXR2 (only in the user-typed ELSE branch; hard error e018 ZFI if missing). Not in Gold DB (KU-027). Contents not yet verified — the JAK code's presence is critical to the AL_JONATHAN fix. Maintained by UNESCO BASIS via SM30.",
    tag="DICTIONARY",
    impact="If FOCOD='JAK' is missing when AL_JONATHAN's Y_USERFO is updated to 'JAK', UXR1 will raise w018 warnings on every posting and UXR2 ELSE branch will throw e018 hard errors if he ever manually types 'JAK' on an invoice screen.",
    related=["YRGGBS00/UXR1", "YRGGBS00/UXR2", "USR05.Y_USERFO"],
)

# ==================== PA0001 (extend existing or create) ====================
ensure_object("PA0001", "HCM", "HR_INFOTYPE")
add_annotation(
    "PA0001",
    "HR master Organizational Assignment infotype. At UNESCO, PA0001.WERKS (personnel area, e.g., FR00=France, ID00=Indonesia, CM00=Cameroon) + PA0001.BTRTL (personnel subarea, e.g., PAR=Paris, JKT=Jakarta, YAO=Yaoundé, KBL=Kabul, DKR=Dakar) is the HR-authoritative office identifier. NOT synchronized with USR05.Y_USERFO — users can drift from HR without detection. Cross-reference via PA0105 SUBTY='0001' USRID=SY-UNAME → PERNR → PA0001.",
    tag="AUTHORITATIVE_SOURCE",
    impact="The audit query PA0001 × PA0105 × USR05 is the definitive class-generalization tool for detecting drifted office codes (KU-028).",
    related=["PA0105", "USR05.Y_USERFO"],
)

# ==================== PA0001.BTRTL ====================
ensure_object("PA0001.BTRTL", "HCM", "HR_FIELD")
add_annotation(
    "PA0001.BTRTL",
    "Personnel subarea code. At UNESCO, this is the HR-authoritative office code. Observed values and mapping to USR05.Y_USERFO: PAR→HQ (Paris), JKT→JAK (Jakarta), YAO→YAO (Yaoundé, match), KBL→KAB (Kabul, mismatch), DKR→DAK (Dakar, mismatch). The BTRTL→Y_USERFO mapping is tribal knowledge — NOT enforced by any table. This is DQ-020.",
    tag="MAPPING_GAP",
    related=["PA0001", "USR05.Y_USERFO"],
)

# ==================== PA0105 ====================
ensure_object("PA0105", "HCM", "HR_INFOTYPE")
add_annotation(
    "PA0105",
    "HR Communications infotype. SUBTY='0001' rows contain USRID = the user's SAP BNAME. This is the canonical bridge from SY-UNAME → PERNR for any HR cross-reference. Used in the INC-000005240 PA0001 lookups to get AL_JONATHAN's personnel area/subarea from his BNAME.",
    tag="BRIDGE",
    related=["PA0001", "USR05"],
)

# ==================== VALID='UNES' ====================
ensure_object("VALID=UNES", "FI", "GGB0_VALIDATION")
add_annotation(
    "VALID=UNES",
    "GGB0 validation rule at BOOLCLASS=009 (FI line item). Created 2007-09-05 by M_SPRONK, last changed 2026-10-11 by FP_SPEZZANO. Has 12 steps in GB931 (extracted via RFC Session #51). Full CONDID/CHECKID/severity/message map in knowledge/incidents/INC-000005240_xref_office_substitution.md §3.4.3. **NONE of the 12 steps reference BSEG-XREF1 or BSEG-XREF2.** The validation checks GSBER, BLART, TCODE, HKONT, GEBER, BSCHL, bank account count (U915), SCB indicator (U917), and fund GL (U916) — but zero XREF content. F-53/FBZ2 is NOT in any prerequisite — manual outgoing payments are completely outside the UNES validation layer.",
    tag="VALIDATION_GAP",
    impact="The validation rule exists but has a critical scope gap: no XREF check and no F-53 coverage. This is why wrong XREF values commit silently on manual payments.",
    related=["GB93", "GB931", "YRGGBS00/U915", "YRGGBS00/U916", "YRGGBS00/U917"],
)

# ==================== SUBSTID='UNESCO' ====================
ensure_object("SUBSTID=UNESCO", "FI", "GGB1_SUBSTITUTION")
add_annotation(
    "SUBSTID=UNESCO",
    "GGB1 substitution rule at callpoint 3 (complete document). 17 steps in GB922 (Gold DB confirmed). Steps include: 001 (HKONT via UGLS), 002 (GSBER via U910), 003 (BVTYP/PYCUR via U901/U902), 004 (GSBER='GEF'), 005 (XREF1 via UXR1), 006 (XREF2 via UXR2), 007 (ZLSCH via UZLS), 008 (UAEP asset), 009 (HKONT='2021023'), 010 (GSBER via U904), 011-012 (FDLEV/ZLSPR), 013 (FDLEV via U908), 014-015 (ZUONR/ZLSPR), 016 (UATF). GB905/GB921 are empty at UNESCO — step-to-prerequisite linkage is NOT in standard tables. Step prerequisites are likely implicit via naming convention 3UNESCO#X → GB901, with empty entries meaning 'no gate / fires unconditionally'.",
    tag="SUBSTITUTION_RULE",
    related=["GB922", "GB901", "GB905", "GB921"],
)

# ==================== GB93 ====================
ensure_object("GB93", "FI", "GGB0_TABLE")
add_annotation(
    "GB93",
    "GGB0 validation rule header. 17 rows at UNESCO P01 (RFC confirmed Session #51). Key row: VALID='UNES' BOOLCLASS='009' MSGID='ZFI'. NOT in Gold DB — should be extracted for future FI validation incidents.",
    tag="EXTRACTION_GAP",
    related=["VALID=UNES", "GB931"],
)

# ==================== GB931 ====================
ensure_object("GB931", "FI", "GGB0_TABLE")
add_annotation(
    "GB931",
    "GGB0 validation steps. 53 rows total; 12 rows for VALID='UNES' (RFC confirmed Session #51). Fields: VALID, VALSEQNR, CONDID, CHECKID, VALSEVERE, VALMSG, MSGTAB1-4, MSGFIELD1-4. The full 12-step UNES validation map is in INC-000005240 §3.4.3. NOT in Gold DB — should be extracted.",
    tag="EXTRACTION_GAP",
    related=["VALID=UNES", "GB93"],
)

# ==================== GB905 / GB921 ====================
ensure_object("GB905", "FI", "GGB1_TABLE")
add_annotation(
    "GB905",
    "Substitution step header — expected to link GB922 SUBSTID+SUBSEQNR to a BOOLID prerequisite. Returns ZERO rows via RFC_READ_TABLE at UNESCO P01 broad probe (Session #51). Either empty (UNESCO doesn't use standard GGB1 step-header mechanism) or inaccessible via RFC. This is KU-031. Practical consequence: substitution step prerequisites must be discovered via empirical CDPOS testing or GGB1 GUI inspection.",
    tag="EXTRACTION_GAP",
    related=["SUBSTID=UNESCO", "GB922"],
)

ensure_object("GB921", "FI", "GGB1_TABLE")
add_annotation(
    "GB921",
    "Substitution rule header — expected to store SUBSTID + callpoint + BOOLCLASS. Returns ZERO rows via RFC_READ_TABLE at UNESCO P01 (Session #51). Same status as GB905 — either empty or inaccessible.",
    tag="EXTRACTION_GAP",
    related=["SUBSTID=UNESCO"],
)

# ==================== BSEG.XREF1 / XREF2 / ZLSCH ====================
ensure_object("BSEG.XREF1", "FI", "SAP_FIELD")
add_annotation(
    "BSEG.XREF1",
    "12-char Reference Key 1 field on BSEG. SAP leaves it for customer use. At UNESCO, repurposed as the originating office tag on vendor lines via YRGGBS00 form UXR1 (reads USR05.Y_USERFO and writes unconditionally — original guard commented out). Observed values: HQ (Paris), JAK (Jakarta), YAO (Yaoundé), KAB (Kabul), DAK (Dakar), BRZ (Brasilia), IIEP_PAR, UIS, IBE. NOT carried in Gold DB bseg_union view — must read via RFC on BSAK/BSAS/BSIS/BSIK/BSAD/BSID.",
    tag="FIELD_REPURPOSE",
    related=["YRGGBS00/UXR1", "USR05.Y_USERFO"],
)

ensure_object("BSEG.XREF2", "FI", "SAP_FIELD")
add_annotation(
    "BSEG.XREF2",
    "12-char Reference Key 2 field on BSEG. At UNESCO, overloaded: (a) on most UNES vendor lines it carries the same office code as XREF1 via UXR2 auto-write; (b) on UNDP transfer transactions it carries 'UNDP-*' memo references (UXR2 recognizes this via UZLS special case IF bseg-xref2(4)<>'UNDP'); (c) on MIRO/FB60 invoices where the screen exposes XREF2 the user can enter custom values that survive UXR2's ELSE branch (subject to e018 YFO_CODES hard error check). NOT in Gold DB bseg_union.",
    tag="FIELD_REPURPOSE",
    related=["YRGGBS00/UXR2", "USR05.Y_USERFO", "YFO_CODES"],
)

ensure_object("BSEG.ZLSCH", "Treasury", "SAP_FIELD")
add_annotation(
    "BSEG.ZLSCH",
    "Payment method field on BSEG. At UNESCO, derived from BSEG-XREF2 per company code via YRGGBS00 form UZLS: for UNES XREF2='HQ' keeps default, non-HQ forces 'O' (field-office outbound); for UBO 'BRZ', UIS 'UIS', IBE 'IBE', IIEP 'IIEP_PAR'. UNDP special case sets 'U'. Wrong XREF2 → wrong ZLSCH → wrong downstream payment routing (F110, BCM, DMEE, house bank).",
    tag="FIELD_DERIVATION",
    related=["BSEG.XREF2", "YRGGBS00/UZLS", "F110"],
)

# ==================== Write back ====================
ann_path.write_text(json.dumps(ann, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"annotations.json: now has {len(ann)} objects")
print("\nNew objects annotated:")
for k in [
    "YRGGBS00", "YRGGBS00/UXR1", "YRGGBS00/UXR2", "YRGGBS00/UZLS",
    "YRGGBS00/U915", "YRGGBS00/U916", "YRGGBS00/U917",
    "USR05", "USR05.Y_USERFO", "YFO_CODES", "PA0001", "PA0001.BTRTL", "PA0105",
    "VALID=UNES", "SUBSTID=UNESCO", "GB93", "GB931", "GB905", "GB921",
    "BSEG.XREF1", "BSEG.XREF2", "BSEG.ZLSCH",
]:
    if k in ann:
        n = len(ann[k].get("annotations", []))
        print(f"  {k:25s} {n} annotation entries")
