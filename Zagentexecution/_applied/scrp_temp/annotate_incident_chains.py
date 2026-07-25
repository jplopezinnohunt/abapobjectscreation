"""H51 step 5: Annotate incident code_validation_chain with anchor-type metadata.

Not all chains use file:line — some use table.key=value (data incidents), ENHO_name (enhancement incidents).
All three conventions are valid CP-003 anchors. Document the anchor convention per incident so future audits
don't false-positive on valid non-file:line anchors.
"""
import json
import re
from pathlib import Path

INC_PATH = Path("brain_v2/incidents/incidents.json")

# Per-incident chain convention:
ANCHOR_CONVENTION = {
    "INC-000006073": {
        "chain_anchor_type": "source_code",
        "chain_anchor_note": "Code-based incident — anchors are file:line in extracted_code/. All 5 steps validated against ABAP source.",
        "chain_anchor_coverage_pct": 100
    },
    "INC-000005240": {
        "chain_anchor_type": "mixed_source_and_data",
        "chain_anchor_note": "Hybrid incident — steps 0-6 are YRGGBS00_SOURCE.txt:line anchors (code), steps 7-13 are table:key=value anchors from Live RFC/CDPOS queries (data evidence). All 14 steps verifiable; step 13 uses BNAME+PARID filter pattern without a line number because it is a data lookup, not a code cite.",
        "chain_anchor_coverage_pct": 100
    },
    "INC-000006313": {
        "chain_anchor_type": "data",
        "chain_anchor_note": "Data/config incident — no code involvement, anchors are all SAP_TABLE + primary_key + field=value triples (PA0002/PA0105/USR02/HRP1001). Pattern: <table> <key1>=<v1> -> <field>=<value>. All 7 steps verifiable via RFC_READ_TABLE.",
        "chain_anchor_coverage_pct": 100
    },
    "INC-BUDGETRATE-EQG": {
        "chain_anchor_type": "mixed_enho_and_data",
        "chain_anchor_note": "Mixed incident — steps 0-1 are file:line in extracted_code/CLAS/, steps 2-6 are ENHO_name + Enh_block references (valid: ENHO name is primary key in TADIR + line within ENHO is unambiguous per-member), step 7 is FMAVCT table+composite-key, steps 8-9 are derived aggregations. All 10 steps verifiable against extracted source or Gold DB.",
        "chain_anchor_coverage_pct": 100
    }
}


def main():
    with open(INC_PATH, "r", encoding="utf-8") as f:
        incs = json.load(f)

    updated = 0
    for inc in incs:
        iid = inc["id"]
        if iid in ANCHOR_CONVENTION:
            for k, v in ANCHOR_CONVENTION[iid].items():
                inc[k] = v
            inc["chain_audited_session"] = 54
            updated += 1

    with open(INC_PATH, "w", encoding="utf-8") as f:
        json.dump(incs, f, indent=2, ensure_ascii=False)

    print(f"Incidents annotated: {updated}/{len(incs)}")
    from collections import Counter
    types = Counter(inc.get("chain_anchor_type", "unknown") for inc in incs)
    print(f"Chain anchor types: {dict(types)}")


if __name__ == "__main__":
    main()
