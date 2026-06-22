"""
build_gold_table_registry.py
-----------------------------
Categorize EVERY golden-DB table by (domain x table_type) so any agent can know
*immediately* which tables belong to a domain and how to refresh them.

Two layers:
  CURATED  — hand-authored specs for domains we actively refresh (PSM_FM, PS).
             Each spec carries the refresh contract: key, delta strategy, partition,
             value_fields (for totals). This DRIVES scripts/extraction/gold_refresh.py.
  AUTO     — heuristic name-based classification of the remaining tables so the
             domain map is COMPLETE (lower fidelity, source='auto').

table_type taxonomy (the user's axis): master_data | text | totals | transaction
             | config | hierarchy | log | provenance | unknown

Emits:
  brain_v2/gold_table_registry.json          (machine-readable, drives the refresher)
  knowledge/gold_table_domain_map.md          (human view, grouped domain -> type)
Run:  python brain_v2/build_gold_table_registry.py
"""
import json
import re
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
OUT_JSON = REPO / "brain_v2" / "gold_table_registry.json"
OUT_MD = REPO / "knowledge" / "gold_table_domain_map.md"

# ----------------------------------------------------------------- CURATED
# domain -> table_type -> [ spec ]
# spec keys:
#   gold   : golden-DB table name
#   sap    : real SAP table
#   key    : primary-key columns (delta PK)
#   delta  : 'pk-upsert' (master) | 'value-compare' (totals) | 'hwm-append' (txn)
#   partition: FIKRS/etc to read per-partition (P01 wrapper rejects ROWSKIPS)
#   created/changed: SAP audit cols for the delta report (master only)
#   value_fields: amount cols to diff (totals only)
#   hwm    : high-water-mark col for incremental txn pulls
CURATED = {
    "PSM_FM": {
        "master_data": [
            {"gold": "funds", "sap": "FMFINCODE", "key": ["FIKRS", "FINCODE"],
             "fields": ["FIKRS", "FINCODE", "TYPE", "ERFDAT", "ERFNAME"],
             "partition": "FIKRS", "created": "ERFDAT", "changed": None, "delta": "pk-upsert"},
            {"gold": "fund_centers", "sap": "FMFCTR", "key": ["FIKRS", "FICTR"],
             "fields": ["FIKRS", "FICTR", "ERFDAT", "ERFNAME"],
             "partition": "FIKRS", "created": "ERFDAT", "delta": "pk-upsert"},
            {"gold": "commitment_items", "sap": "FMCI", "key": ["FIKRS", "GJAHR", "FIPEX"],
             "fields": ["FIKRS", "GJAHR", "FIPEX", "KATEG", "FIVOR", "FICTR"],
             "partition": "FIKRS", "delta": "pk-upsert"},
            {"gold": "functional_areas", "sap": "TFKB", "key": ["FKBER"],
             "fields": ["FKBER", "AUTHGRP", "DATAB", "DATBIS"], "partition": None, "delta": "pk-upsert"},
        ],
        "text": [
            {"gold": "FMFINT", "sap": "FMFINT", "key": ["FIKRS", "FINCODE", "SPRAS"],
             "fields": ["FIKRS", "FINCODE", "SPRAS", "BEZEICH", "BESCHR"],
             "partition": "FIKRS", "where": "SPRAS = 'E'", "delta": "pk-upsert"},
            {"gold": "fund_centers_text", "sap": "FMFCTRT", "key": ["FIKRS", "FICTR", "SPRAS"],
             "fields": ["FIKRS", "FICTR", "SPRAS", "BEZEICH", "BESCHR"],
             "partition": "FIKRS", "where": "SPRAS = 'E'", "delta": "pk-upsert"},
            {"gold": "commitment_items_text", "sap": "FMCIT", "key": ["FIKRS", "FIPEX", "SPRAS"],
             "fields": ["FIKRS", "FIPEX", "SPRAS", "BEZEI", "TEXT1"],
             "partition": "FIKRS", "where": "SPRAS = 'E'", "delta": "pk-upsert"},
            {"gold": "functional_areas_text", "sap": "TFKBT", "key": ["FKBER", "SPRAS"],
             "fields": ["FKBER", "SPRAS", "FKBTX"], "partition": None, "where": "SPRAS = 'E'",
             "delta": "pk-upsert"},
        ],
        "totals": [
            {"gold": "bpge", "sap": "BPGE", "key": ["__all_dims__"],
             "value_fields": ["WTGES", "WTGEV", "WLGES", "WLGEV"], "partition": None,
             "delta": "value-compare", "note": "BCS overall budget total. key=all dims (engine-derived)"},
            {"gold": "bpja", "sap": "BPJA", "key": ["__all_dims__"],
             "value_fields": ["WTJHR", "WTJHV", "WLJHR", "WLJHV"], "partition": "GJAHR",
             "delta": "value-compare", "note": "BCS annual budget total; partition by GJAHR. key=all dims"},
            # fmavct_summary is an ANALYSIS table (RFIKRS/RYEAR/RFUND/COUNT), NOT a raw FMAVCT
            # mirror -> not value-comparable; left to auto-classify (totals, source=auto).
        ],
        "transaction": [
            {"gold": "fmbh", "sap": "FMBH", "key": ["__all_dims__"], "value_fields": [],
             "partition": ["FM_AREA"], "delta": "txn-partitioned",
             "note": "BCS budget doc header (immutable; key=all cols, all years)"},
            {"gold": "fmbl", "sap": "FMBL", "key": ["__all_dims__"], "value_fields": [],
             "partition": ["FM_AREA", "DOCYEAR"], "delta": "txn-partitioned",
             "note": "BCS budget doc line (scope DOCYEAR 2024-2026)"},
            {"gold": "fmioi", "sap": "FMIOI", "key": ["__all_dims__"], "value_fields": ["FKBTR", "TRBTR"],
             "partition": ["BUKRS", "GJAHR", "PERIO"], "delta": "txn-partitioned",
             "note": "FM commitment line items (scope GJAHR 2024-2026, sub by PERIO)"},
            {"gold": "fmifiit_full", "sap": "FMIFIIT", "key": ["__all_dims__"], "value_fields": ["FKBTR", "TRBTR"],
             "partition": ["FIKRS", "GJAHR", "PERIO"], "delta": "txn-partitioned",
             "note": "FM actual (FI-FM) line items (scope GJAHR 2024-2026, sub by PERIO)"},
        ],
    },
    "PS": {
        "master_data": [
            {"gold": "proj", "sap": "PROJ", "key": ["PSPID"],
             "fields": ["VBUKR", "PSPID", "POST1", "VERNR", "ERDAT", "PSPNR"],
             "partition": None, "created": "ERDAT", "delta": "pk-upsert"},
            {"gold": "prps", "sap": "PRPS", "key": ["POSID"],
             "fields": ["PBUKR", "POSID", "POST1", "VERNR", "ERDAT", "PSPHI", "PSPNR", "OBJNR", "ERNAM"],
             "partition": None, "created": "ERDAT", "delta": "pk-upsert"},
        ],
        "hierarchy": [
            {"gold": "proj_hierarchy", "sap": "PRHI", "key": ["POSNR"],
             "fields": ["POSNR", "PSPHI", "UP", "DOWN", "LEFT", "RIGHT"],
             "gold_cols": ["POSNR", "PSPHI", "UP", "DOWN", "LEFTND", "RIGHTND"],
             "partition": None, "delta": "pk-upsert"},
        ],
    },
}

# ----------------------------------------------------------------- AUTO heuristics
DOMAIN_RULES = [
    ("provenance",  r"^(d01_|v01_)"),
    ("PS",          r"^(proj|prps|prhi|rpsco|rpsco)"),
    ("PSM_FM",      r"^(fm|bp[0-9gj]|ytfm|funds|fund_|commitment_|functional_|buavc|tabadr|movements_summary)"),
    ("Procurement", r"^(ekko|ekpo|ekbe|ekkn|eban|esll|essr|rseg|rbkp|me[0-9])"),
    ("Controlling", r"^(coep|cooi|cosp|covp|cobk|tka0|csl)"),
    ("Travel",      r"^(ptrv|trip|tcos|ttrv)"),
    ("Integration", r"^(edidc|edid|rfcdes|icfservice|tfdir|tbdls|srt_)"),
    ("Payment",     r"^(reguh|regup|payr|bcm_|bnk_batch|dfpay|febep|febko|febre|feban|t012|t042|t028|t033|tiban|sim_|sepa|payment_|zfi_payrel|tfpm042)"),
    ("Master_BP",   r"^(adr[0-9]|adrc|bnka|but0|but100|knvv|kna1|knb1|lfa1|lfb1|lfbk|cvi_|bp001)"),
    ("FI",          r"^(bsis|bsas|bseg|bkpf|bsid|bsik|bsad|bsak|glt0|faglflext|fagl|p01_sk|p01_csk|ska1|skat|skb1|csk|knc|lfc|tcurr|tcurf|gb0|gb9|set(header|leaf|node)|ybasubst|ytfi|sapf100|tj[0-9]|tj02t|tj30t)"),
    ("Security",    r"^(agr_|ust|usr|tobj|usobx|usobt|jest)"),
    ("Transport",   r"^(e07|tms|tcevers|tadir_enrich|spau|cts)"),
    ("Logs",        r"^(tbtco|tbtcp|cdhdr|cdpos|rsau|syslog|sm21|st22|smodilog|pat03|tpalog|cvers|uvers|snap)"),
    ("HCM",         r"^(pa0|pernr|hrp|t5|allos)"),
    ("Config",      r"^t[0-9]"),
]
TYPE_RULES = [
    ("provenance",  r"^(d01_|v01_)"),
    ("log",         r"^(tbtco|tbtcp|cdhdr|cdpos|rsau|syslog|sm21|st22|smodilog|pat03|tpalog|cvers|uvers|snap)"),
    ("hierarchy",   r"(hierarchy|^prhi|^setnode|^setleaf|^setheader$|^setheadert$)"),
    ("text",        r"(_t$|_text$|text$|^skat$|^csku$|^p01_skat$|^p01_csku$|^tj02t$|^tj30t$|^tabadrt$|^tabadrst$|t$)"),
    ("totals",      r"(_summary$|^bpge|^bpja|^glt0|faglflext|^fmavct|^fmbdt|^cosp|^rpsco|^knc|^lfc|total|anchor)"),
    ("transaction", r"^(bkpf|bseg|bsis|bsas|bsid|bsik|bsad|bsak|fmbh|fmbl|fmioi|fmifiit|fmreserv|reguh|regup|payr|febep|febko|febre|dfpayg|dfpayv|cobk|coep|cooi|covp|edidc|edid|ekko|ekpo|ekbe|eban|esll|essr|rseg|rbkp|ptrv|jest|bnk_batch|movements|cts_transport)"),
    ("config",      r"^(t[0-9]|tcurr|tcurf|tiban|gb0|gb9|tka0|agr_|fagl_split|fmderive|fmavcatgr|fmavcbudfil|fmavcldgr|fmup|fm01tol|fmfmoa|fmafm|rfcdes|icfservice|tfdir|tabadr|ekkn|sapf100|ybasubst|ytfi|ytfm|bcm_|zfi|buavc|sim_|scenario_|payment_objects|tfpm042)"),
    ("master_data", r"^(funds|fund_centers|commitment_items|functional_areas|proj|prps|ska1|skb1|csks|cska|cskb|lfa1|lfb1|lfbk|kna1|knb1|knvv|but000|but100|but0bk|bp001|adr[0-9]|adrc|bnka|cvi_|p01_sk|p01_csk|ekko_master|fmfincode|fmfctr|fmci|fmfpo|fmmeasure|tfkb|tadir_enrich|tfdir_custom|cts_object)"),
]

# Explicit overrides for tables that pattern-matching gets wrong or that carry intent
# (analysis/custom tables). (domain, table_type). Highest precedence after curated.
OVERRIDES = {
    "movements_summary": ("PSM_FM", "totals"),
    "volume_anchors": ("PSM_FM", "totals"),
    "buavctolass": ("PSM_FM", "config"),
    "rpsco": ("PS", "totals"),
    "jest": ("Cross_Domain", "transaction"),
    "tadir_enrichment": ("Transport", "master_data"),
    "tfdir_custom": ("Integration", "master_data"),
    "sapf100_vari": ("FI", "config"), "sapf100_varid": ("FI", "config"),
    "scenario_samples": ("Payment", "config"),
    "sim_all_formats": ("Payment", "transaction"), "sim_sepa_all": ("Payment", "transaction"),
    "sim_v6_results": ("Payment", "transaction"),
    "payment_objects": ("Payment", "master_data"),
    "currency_usd_rates": ("FI", "config"),
    "spau_2024_objects": ("Transport", "log"),
    "tka01": ("Controlling", "config"), "tka02": ("Controlling", "config"),
}


def classify(name, rules, default="unknown"):
    low = name.lower()
    for label, pat in rules:
        if re.search(pat, low):
            return label
    return default


def main():
    con = sqlite3.connect(GOLD)
    cur = con.cursor()
    all_tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

    # index curated by gold name
    curated_index = {}
    for dom, types in CURATED.items():
        for ttype, specs in types.items():
            for s in specs:
                curated_index[s["gold"]] = (dom, ttype, s)

    registry = {"domains": {}, "_meta": {"total_tables": len(all_tables)}}

    def add(dom, ttype, entry):
        registry["domains"].setdefault(dom, {}).setdefault(ttype, []).append(entry)

    auto_count = 0
    for t in all_tables:
        if t.startswith("_") or t == "sqlite_sequence":
            continue
        try:
            rows = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except sqlite3.Error:
            rows = None
        if t in curated_index:
            dom, ttype, spec = curated_index[t]
            e = dict(spec); e["rows"] = rows; e["source"] = "curated"
            add(dom, ttype, e)
        elif t.lower() in OVERRIDES:
            dom, ttype = OVERRIDES[t.lower()]
            add(dom, ttype, {"gold": t, "rows": rows, "source": "override"})
            auto_count += 1
        else:
            dom = classify(t, DOMAIN_RULES, "Uncatalogued")
            ttype = classify(t, TYPE_RULES, "unknown")
            add(dom, ttype, {"gold": t, "rows": rows, "source": "auto"})
            auto_count += 1

    registry["_meta"]["curated"] = len(curated_index)
    registry["_meta"]["auto"] = auto_count

    OUT_JSON.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- markdown view
    lines = ["# Golden DB — domain × table-type map",
             "",
             f"> Generated by `brain_v2/build_gold_table_registry.py`. {len(all_tables)} tables: "
             f"{len(curated_index)} curated (drive the refresher), {auto_count} auto-classified.",
             "> table_type axis (user directive): **master_data · text · totals · transaction · "
             "config · hierarchy · log · provenance**.",
             "> Refresher: `scripts/extraction/gold_refresh.py <domain> [type]` (registry-driven, delta-aware).",
             ""]
    TYPE_ORDER = ["master_data", "text", "totals", "transaction", "hierarchy",
                  "config", "log", "provenance", "unknown"]
    for dom in sorted(registry["domains"]):
        types = registry["domains"][dom]
        n = sum(len(v) for v in types.values())
        lines.append(f"## {dom}  ({n} tables)")
        for ttype in TYPE_ORDER:
            if ttype not in types:
                continue
            entries = sorted(types[ttype], key=lambda e: e["gold"])
            tags = []
            for e in entries:
                tag = e["gold"]
                if e.get("source") == "curated":
                    tag = f"**{tag}**"
                if e.get("rows") is not None:
                    tag += f" ({e['rows']:,})"
                tags.append(tag)
            lines.append(f"- _{ttype}_: " + ", ".join(tags))
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    con.close()
    print(f"Registry: {OUT_JSON}  ({len(curated_index)} curated + {auto_count} auto = {len(all_tables)} tables)")
    print(f"Domain map: {OUT_MD}")
    print("\nDomains:")
    for dom in sorted(registry["domains"]):
        types = registry["domains"][dom]
        tt = {k: len(v) for k, v in types.items()}
        print(f"  {dom:14s} {sum(tt.values()):>4} tables  {tt}")


if __name__ == "__main__":
    main()
