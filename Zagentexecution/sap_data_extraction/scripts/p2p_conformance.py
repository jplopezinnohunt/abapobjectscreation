"""
p2p_conformance.py — AN-STDREF + AN-G-P2P: custom-over-standard P2P x-ray.
=========================================================================
The STANDARD (AS-DESIGNED) P2P normative model (SAP best practice / PaPM, verified
research wh5gw9exu/wgrqpmt9f): PO -> Goods Receipt -> Invoice Receipt, 3-way match,
GR strictly BEFORE IR (goods confirmed before paying). We measure how UNESCO's AS-RUN
deviates from it, on the FULL log, using real DATES (not the arbitrary same-day order).

Deterministic, full-population (no sampling). Each metric is a business-meaningful
conformance rule with its count + %. Output: p2p_conformance.json.
"""
import os, sqlite3, json
from pathlib import Path

ROOT = Path(r"c:\Users\jp_lopez\projects\abapobjectscreation")
GOLD = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT = ROOT / "Zagentexecution" / "sap_data_extraction" / "process_discovery" / "p2p_conformance.json"

SQL = """
SELECT k.EBELN,
       k.AEDAT AS po_created,
       MIN(CASE WHEN b.VGABE='1' THEN b.BUDAT END) AS first_gr,
       MIN(CASE WHEN b.VGABE='2' THEN b.BUDAT END) AS first_ir,
       SUM(CASE WHEN b.VGABE='1' THEN 1 ELSE 0 END) AS n_gr,
       SUM(CASE WHEN b.VGABE='2' THEN 1 ELSE 0 END) AS n_ir
FROM ekko k LEFT JOIN ekbe b ON k.EBELN=b.EBELN
GROUP BY k.EBELN, k.AEDAT
"""


def run():
    con = sqlite3.connect(GOLD)
    rows = con.execute(SQL).fetchall()
    con.close()
    total = len(rows)
    c = dict(po_only=0, gr_no_ir=0, ir_no_gr=0, both=0,
             both_gr_before_ir=0, both_ir_before_gr=0, both_same_day=0, no_po_date=0)
    for ebeln, po_created, first_gr, first_ir, n_gr, n_ir in rows:
        if not po_created:
            c["no_po_date"] += 1
        has_gr, has_ir = bool(first_gr), bool(first_ir)
        if not has_gr and not has_ir:
            c["po_only"] += 1
        elif has_gr and not has_ir:
            c["gr_no_ir"] += 1
        elif has_ir and not has_gr:
            c["ir_no_gr"] += 1               # invoiced, never received — control risk
        else:  # both
            c["both"] += 1
            if first_gr < first_ir:
                c["both_gr_before_ir"] += 1   # CONFORMING 3-way order
            elif first_ir < first_gr:
                c["both_ir_before_gr"] += 1   # invoice dated before goods — real deviation
            else:
                c["both_same_day"] += 1       # same date — order indeterminate

    def pct(n):
        return round(100 * n / total, 2) if total else 0.0

    # STANDARD conformance = both present AND GR before IR (or same-day, given as benign)
    conforming = c["both_gr_before_ir"]
    result = {
        "_design": "P2P custom-over-standard conformance. STANDARD = PO->GR->IR, GR before IR (3-way match). Full population, date-based.",
        "total_pos": total,
        "standard_conformance_pct": pct(conforming),
        "conforming_pos_gr_before_ir": conforming,
        "deviations": {
            "po_only_open_or_abandoned": {"n": c["po_only"], "pct": pct(c["po_only"]), "meaning": "PO created, never received nor invoiced"},
            "gr_no_ir_received_not_invoiced": {"n": c["gr_no_ir"], "pct": pct(c["gr_no_ir"]), "meaning": "goods received, no invoice yet (GR/IR open)"},
            "ir_no_gr_invoiced_not_received": {"n": c["ir_no_gr"], "pct": pct(c["ir_no_gr"]), "meaning": "INVOICED WITHOUT GOODS RECEIPT — control risk (no 3-way match)"},
            "ir_before_gr_date": {"n": c["both_ir_before_gr"], "pct": pct(c["both_ir_before_gr"]), "meaning": "invoice DATED before goods receipt — real ordering deviation (date-based, not same-day artifact)"},
            "both_same_day": {"n": c["both_same_day"], "pct": pct(c["both_same_day"]), "meaning": "GR and IR same date — order indeterminate (would need intra-day time / CDPOS)"},
        },
        "data_quality_flags": {
            "no_po_created_date": c["no_po_date"],
            "note": "ir_no_gr + ir_before_gr are the headline custom-over-standard control findings; same_day is a measurement limit, not a finding.",
        },
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== P2P CUSTOM-OVER-STANDARD CONFORMANCE (full population: {total:,} POs) ===")
    print(f"STANDARD-conforming (PO->GR->IR, GR before IR): {conforming:,} ({pct(conforming)}%)")
    print("\nDEVIATIONS:")
    for k, v in result["deviations"].items():
        print(f"  {v['n']:>8,} ({v['pct']:>5}%)  {k}: {v['meaning']}")
    print(f"\nsaved: {OUT}")
    return result


if __name__ == "__main__":
    run()
