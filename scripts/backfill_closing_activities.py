# Backfill Closing_Activities gap objects with EVIDENCE-TRUE structured records.
# Genuine FX-related objects found by the coverage audit: SKAT, T044A, TBTCO,
# TBTCP, P01_SKA1. (INPUT = false positive "BATCH INPUT SESSION"; RFFOUS_C =
# a Payment-domain example, not closing — both correctly excluded.)
import json, io, os
ROOT = r"C:\Users\jp_lopez\projects\abapobjectscreation"
CLA = os.path.join(ROOT, "brain_v2", "claims", "claims.json")
INC = os.path.join(ROOT, "brain_v2", "incidents", "incidents.json")
DOC = "knowledge/domains/Closing_Activities/fx_revaluation_process.md"

claims = json.load(io.open(CLA, encoding="utf-8"))
incidents = json.load(io.open(INC, encoding="utf-8"))

# idempotent
claims = [c for c in claims if c.get("id") not in (209, 210)]

new = [
    {"id": 209,
     "claim": "F.05/SAPF100 valuation behaviour is governed by a valuation method (config table T044A): it sets reversing vs non-reversing posting and the determination of exchange-rate diffs. Mode A (reversing, open items) vs Mode B (balance-sheet preparation, permanent, no reversal). For bank-balance revaluation the correct mode is non-reversing; confirming which method UNES_UNBA uses is the open known-unknown for the balance-non-reversal question.",
     "claim_type": "verified_fact", "confidence": "TIER_2",
     "evidence_for": [{"type": "sap_config", "ref": "T044A (Valuation Methods)", "cite": "T044A holds KOAR/valuation-method flags incl. reversal indicator; SAPF100 reads the method named in the F.05 variant. Mode determines whether FBB1 docs reverse next period."}],
     "evidence_against": [], "related_objects": ["T044A", "SAPF100", "F.05", "OB09", "UNES_UNBA"],
     "domain": "Closing Activities", "created_session": 79, "status": "active",
     "domain_axes": ["FI", "Treasury"]},
    {"id": 210,
     "claim": "The currency of a revaluation/bank GL account is read from the account master TEXT (SKAT) + the document currency, NOT from SKB1.WAERS. SKB1.WAERS is the account-currency control, often blank/local; the operative currency (e.g. Citibank Dakar 1143254 = XOF) is identifiable from the SKAT account name and the FX document currency. Gold DB P01_SKA1/SKAT extracts carry these texts.",
     "claim_type": "verified_fact", "confidence": "TIER_1",
     "evidence_for": [{"type": "table_query", "ref": "SKAT / P01_SKA1 vs SKB1 (P01)", "cite": "1143254 SKB1.WAERS blank but SKAT name = Citibank Dakar (XOF); FS10N shows XOF balance. Confirms currency source = SKAT name + doc currency."}],
     "evidence_against": [], "related_objects": ["SKAT", "P01_SKA1", "SKB1", "SKA1"],
     "domain": "Closing Activities", "created_session": 79, "status": "active",
     "domain_axes": ["FI", "Treasury"]},
]
claims.extend(new)

# extend the FX incident's related_objects with the genuine tables (promotes them)
for rec in incidents:
    if rec.get("id") == "INC-FXREVAL-OB09":
        ro = set(rec.get("related_objects", []))
        ro |= {"SKAT", "T044A", "TBTCO", "TBTCP", "P01_SKA1", "SKA1"}
        rec["related_objects"] = sorted(ro)
        rec.setdefault("related_claims", []).extend([
            {"id": 209, "claim": "Valuation method (T044A) governs reversing vs non-reversing F.05 postings."},
            {"id": 210, "claim": "Account currency from SKAT text + doc currency, not SKB1.WAERS."},
        ])
        # dedup related_claims by id
        seen = {}; rec["related_claims"] = [seen.setdefault(c["id"], c) for c in rec["related_claims"] if c["id"] not in seen]

# also extend claim 208 (jobs) to explicitly list TBTCP
for c in claims:
    if c.get("id") == 208:
        ro = set(c.get("related_objects", [])) | {"TBTCO", "TBTCP"}
        c["related_objects"] = sorted(ro)

json.dump(claims, io.open(CLA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(incidents, io.open(INC, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("Backfill done: claims 209-210 added; 6 tables promoted via incident related_objects.")
print(f"  claims now: {len(claims)}")
