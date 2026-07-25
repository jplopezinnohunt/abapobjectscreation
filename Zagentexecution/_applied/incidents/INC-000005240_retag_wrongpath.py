# -*- coding: utf-8 -*-
"""
Re-tag Session #050 wrong-path brain entries.

Claims 27-30 were created by the Session #050 subagent pursuing the FMDERIVE
hypothesis (ZXFMDTU02_RPY hardcoding FICTR='UNESCO' for 3 GLs). That was the
WRONG mechanism for INC-000005240. The finding itself may be a real standalone
observation (filed as obs_fmderive_hardcoded_fictr_gl_6045xxx.md) but must NOT
be linked to INC-000005240.

Same treatment for annotations on ZXFMDTU02_RPY, fmifiit_full, fund_centers.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation\brain_v2")

TRIAGE_NOTE = (
    "[Session #51 triage] Originally captured by INC-000005240 Session #50 subagent "
    "pursuing FMDERIVE/ZXFMDTU02_RPY FICTR='UNESCO' hypothesis that was LATER REJECTED "
    "as the wrong mechanism for INC-000005240 (the real root cause is XREF1/XREF2 "
    "substitution via YRGGBS00 UXR1/UXR2 — see knowledge/incidents/INC-000005240_xref_office_substitution.md). "
    "The finding itself may be a real standalone observation — filed as "
    "knowledge/observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md. "
    "Do NOT link this entry to INC-000005240."
)

# ---------- Re-tag claims 27, 28, 29, 30 ---------------------------------
claims_path = ROOT / "claims/claims.json"
claims = json.loads(claims_path.read_text(encoding="utf-8"))
wrong_path_claim_ids = {27, 28, 29, 30}
retagged_claims = 0
for c in claims:
    if c.get("id") in wrong_path_claim_ids:
        notes = c.get("resolution_notes", "") or ""
        if "Session #51 triage" not in notes:
            c["resolution_notes"] = (notes + " " + TRIAGE_NOTE).strip()
            # Also downgrade tier if it was TIER_1 — these are now observations, not confirmed facts
            if c.get("tier") == "TIER_1":
                c["tier"] = "TIER_3_OBSERVATION_ONLY"
                c["tier_changed_by"] = "#51 triage"
            retagged_claims += 1
            print(f"Retagged claim {c['id']}: '{c.get('claim', '')[:100]}...'")
claims_path.write_text(json.dumps(claims, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nRetagged {retagged_claims} claims")

# ---------- Re-tag annotations for ZXFMDTU02_RPY, fmifiit_full, fund_centers ---
ann_path = ROOT / "annotations/annotations.json"
ann = json.loads(ann_path.read_text(encoding="utf-8"))

wrong_path_objects = ["ZXFMDTU02_RPY", "fmifiit_full", "fund_centers"]
retagged_objects = 0
for obj in wrong_path_objects:
    if obj in ann:
        entries = ann[obj]
        # entries is a dict with 'annotations' key that's a list
        if isinstance(entries, dict) and "annotations" in entries:
            ann_list = entries["annotations"]
            if isinstance(ann_list, list):
                # Add a triage note as a new annotation entry OR update each
                for a in ann_list:
                    if isinstance(a, dict):
                        current_note = a.get("session_note", "") or ""
                        if "Session #51 triage" not in current_note:
                            a["session_note"] = (current_note + " " + TRIAGE_NOTE).strip()
                            a["observation_only"] = True
                            a["linked_observation"] = "knowledge/observations/obs_fmderive_hardcoded_fictr_gl_6045xxx.md"
                            a["not_linked_to"] = "INC-000005240"
                            retagged_objects += 1
                print(f"Retagged annotation object: {obj} ({len(ann_list)} entries)")
ann_path.write_text(json.dumps(ann, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nRetagged {retagged_objects} annotation entries across {len(wrong_path_objects)} objects")

# ---------- Summary ------------------------------------------------------
print("\n=== Wrong-path triage complete ===")
print(f"  claims.json     : {retagged_claims} claims re-tagged as TIER_3_OBSERVATION_ONLY")
print(f"  annotations.json: {retagged_objects} annotation entries re-tagged with linked_observation pointer")
