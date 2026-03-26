"""
cdhdr_activity_mapping.py
=========================
Maps CDHDR records (OBJECTCLAS + TCODE) to human-readable process activities.
Based on Javert899/sap-extractor mapping.py (100+ rules) + Celonis P2P reference.

Usage:
    from cdhdr_activity_mapping import map_to_activity, build_event_log

    activity = map_to_activity(objectclas="EINKBELEG", tcode="ME21N")
    # -> "Create Purchase Order"

    df = build_event_log(cdhdr_rows)
    # -> DataFrame ready for pm4py
"""

import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────
# TCODE → Activity mapping (by OBJECTCLAS)
# Source: Javert899/sap-extractor + Celonis + SAP documentation
# ─────────────────────────────────────────────────────────────────────

TCODE_ACTIVITY = {
    # Purchase Documents (EINKBELEG)
    "ME21N": "Create Purchase Order",
    "ME22N": "Change Purchase Order",
    "ME23N": "Display Purchase Order",
    "ME29N": "Release Purchase Order",
    "ME2M":  "List Purchase Orders",

    # Purchase Requisitions (BANF)
    "ME51N": "Create Purchase Requisition",
    "ME52N": "Change Purchase Requisition",
    "ME54N": "Release Purchase Requisition",
    "ME55":  "Collective Release PR",

    # Goods Receipt / Movement
    "MIGO":  "Goods Movement",
    "MB01":  "Goods Receipt",
    "MB1A":  "Goods Issue",
    "MB1C":  "Other Goods Receipt",
    "MB11":  "Goods Movement",

    # Invoice Verification
    "MIRO":  "Invoice Receipt",
    "MIR7":  "Park Invoice",
    "MIR4":  "Display Invoice",
    "MRBR":  "Release Blocked Invoice",

    # Sales Documents (VERKBELEG)
    "VA01":  "Create Sales Order",
    "VA02":  "Change Sales Order",
    "VA03":  "Display Sales Order",

    # Deliveries (LIEFERUNG)
    "VL01N": "Create Delivery",
    "VL02N": "Change Delivery",
    "VL09":  "Reverse Goods Issue",

    # Material Master (MATERIAL)
    "MM01":  "Create Material",
    "MM02":  "Change Material",
    "MM03":  "Display Material",

    # Vendor Master (KRED)
    "XK01":  "Create Vendor",
    "XK02":  "Change Vendor",
    "MK01":  "Create Vendor (Purchasing)",
    "MK02":  "Change Vendor (Purchasing)",

    # Customer Master (DEBT)
    "XD01":  "Create Customer",
    "XD02":  "Change Customer",

    # FI Documents
    "FB01":  "Post FI Document",
    "FB02":  "Change FI Document",
    "FB08":  "Reverse FI Document",
    "F-28":  "Incoming Payment",
    "F-53":  "Outgoing Payment",
    "FBZ1":  "Post Incoming Payment",
    "FBZ2":  "Post Outgoing Payment",
    "FBRA":  "Reset Clearing",

    # FM / Budget (UNESCO specific)
    "FMBB":  "Budget Entry",
    "FR50":  "Funds Reservation",
    "FR58":  "Funds Commitment",
    "FR60":  "Funds Precommitment",
    "FMZA":  "FM Transfer Posting",
    "FMZ1":  "FM Budget Transfer",
    "FMZ3":  "FM Budget Return",

    # Payment
    "F110":  "Automatic Payment Run",
    "FBZ5":  "Print Payment",

    # Config / Customizing
    "SM30":  "Maintain Table View",
    "SM31":  "Maintain Table View",
    "SPRO":  "Customizing",
    "OB52":  "Open/Close Posting Periods",
    "OBBH":  "Account Substitution Config",

    # Service Entry Sheets
    "ML81N": "Create Service Entry Sheet",

    # Travel
    "PR01":  "Create Travel Request",
    "PR02":  "Change Travel Request",
    "PR03":  "Trip Record",
    "PR05":  "Trip Approval",
}

# OBJECTCLAS → default activity prefix (when TCODE not in mapping)
OBJECTCLAS_PREFIX = {
    "EINKBELEG": "Procurement",
    "VERKBELEG": "Sales",
    "LIEFERUNG": "Delivery",
    "MATERIAL":  "Material",
    "KRED":      "Vendor",
    "DEBT":      "Customer",
    "BANF":      "Purchase Requisition",
    "FMIFIIT":   "FM Document",
    "FM_BUDGET":  "FM Budget",
    "BKPF":      "FI Document",
    "ENTRYSHEET": "Service Entry",
    "REISE":     "Travel",
}


def map_to_activity(objectclas, tcode):
    """Map OBJECTCLAS + TCODE to a human-readable activity name."""
    # First try exact TCODE match
    if tcode in TCODE_ACTIVITY:
        return TCODE_ACTIVITY[tcode]

    # Fallback to OBJECTCLAS prefix + TCODE
    prefix = OBJECTCLAS_PREFIX.get(objectclas, objectclas)
    if tcode:
        return f"{prefix} ({tcode})"
    return f"{prefix} Change"


def build_event_log(cdhdr_rows):
    """
    Convert CDHDR rows to a pm4py-ready DataFrame.

    Args:
        cdhdr_rows: list of dicts with keys OBJECTCLAS, OBJECTID, CHANGENR,
                     USERNAME, UDATE, UTIME, TCODE

    Returns:
        DataFrame with columns: case:concept:name, concept:name,
                                time:timestamp, org:resource, OBJECTCLAS, TCODE
    """
    events = []
    for row in cdhdr_rows:
        objectclas = row.get("OBJECTCLAS", "").strip()
        tcode      = row.get("TCODE", "").strip()
        udate      = row.get("UDATE", "").strip()
        utime      = row.get("UTIME", "").strip()

        activity = map_to_activity(objectclas, tcode)

        # Build timestamp from UDATE + UTIME
        try:
            if utime and len(utime) >= 6:
                ts = datetime.strptime(f"{udate}{utime[:6]}", "%Y%m%d%H%M%S")
            else:
                ts = datetime.strptime(udate, "%Y%m%d")
        except (ValueError, TypeError):
            continue

        events.append({
            "case:concept:name": row.get("OBJECTID", "").strip(),
            "concept:name": activity,
            "time:timestamp": ts,
            "org:resource": row.get("USERNAME", "").strip(),
            "OBJECTCLAS": objectclas,
            "TCODE": tcode,
            "CHANGENR": row.get("CHANGENR", "").strip(),
        })

    df = pd.DataFrame(events)
    if not df.empty:
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
        df = df.sort_values("time:timestamp")

    return df


# ─────────────────────────────────────────────────────────────────────
# STANDALONE: load from extracted JSON and produce event log
# ─────────────────────────────────────────────────────────────────────

def main():
    import json
    import os

    cdhdr_dir = os.path.join(os.path.dirname(__file__), "extracted_data", "CDHDR")
    if not os.path.exists(cdhdr_dir):
        print("No CDHDR data found. Run extract_cdhdr.py first.")
        return

    all_rows = []
    for fname in sorted(os.listdir(cdhdr_dir)):
        if fname.endswith(".json"):
            with open(os.path.join(cdhdr_dir, fname), encoding="utf-8") as f:
                data = json.load(f)
            all_rows.extend(data.get("rows", []))

    print(f"Loaded {len(all_rows):,} CDHDR rows")

    df = build_event_log(all_rows)
    print(f"Event log: {len(df)} events, {df['case:concept:name'].nunique()} cases")
    print(f"\nActivity distribution:")
    print(df["concept:name"].value_counts().head(20).to_string())

    print(f"\nOBJECTCLAS distribution:")
    print(df["OBJECTCLAS"].value_counts().head(20).to_string())

    # Save event log
    output = os.path.join(os.path.dirname(__file__), "process_discovery_output", "cdhdr_event_log.json")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    df.to_json(output, orient="records", date_format="iso")
    print(f"\n-> {output}")


if __name__ == "__main__":
    main()
