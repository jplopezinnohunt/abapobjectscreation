"""
cts_analyze.py -- Transport Order Analysis + Object Evolution Tracker
=====================================================================
Reads raw JSON from cts_extract.py and produces a rich analysis JSON
for consumption by cts_dashboard.html.

Key dimensions:
  - Transport classification (8-rule engine: SAP_UPGRADE, SAP_CONFIG, CUSTOM_DEV, BASIS_SYSTEM)
  - Deployment status distribution (from TRSTATUS heuristic)
  - Timeline by quarter (stacked by classification)
  - Top owners with user-class detection (REAL_USER, SERVICE_ACCOUNT, SAP_SYSTEM)
  - Package (DEVCLASS) breakdown with top change categories
  - Domain (DLVUNIT) breakdown
  - Object evolution timeline: each SAP object tracked across transports over time
    -> hot objects (most transported)
    -> objects with highest developer diversity (most people touching same thing)
    -> evolution charts per quarter: which objects are trending

Usage:
    python cts_analyze.py --input cts_5yr_raw.json
    python cts_analyze.py --input cts_5yr_raw.json --out cts_5yr_analyzed.json
"""

import os
import json
import argparse
import re
from datetime import datetime
from collections import defaultdict, Counter


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION ENGINE (8-rule cascading)
# ─────────────────────────────────────────────────────────────────────────────

# SAP transport number patterns that signal upgrades / support packages
SAP_TRKORR_PREFIXES = re.compile(
    r'^(SAPK|SAPQ|SAP_|SAP\d|SM\d\d|SI\d|SW\d|CS\d|CE\d|HR\d|FI\d|CO\d|SD\d|MM\d|PP\d|QM\d|PM\d)',
    re.IGNORECASE
)

SAP_SYSTEM_USERS  = {"SAP", "DDIC", "BASIS", "SAP_SUPPORT", "SAP-SUPPORT"}
SERVICE_ACCOUNTS  = re.compile(r'^(I\d{6,}|S\d{7,}|SVC|SVC_|SERVICE|BATCH|AUTO)', re.IGNORECASE)

UPGRADE_KEYWORDS  = re.compile(
    r'\b(support.?package|hot.?fix|sp.?stack|patch|upgrade|kernel|basis.?update|'
    r'correction.?note|oss.?note|note.?\d{4,}|transport.?fix)\b', re.IGNORECASE
)
DEV_KEYWORDS      = re.compile(
    r'\b(dev|development|ticket|incident|cr\s*\d+|change.?request|fiori|bsp|odata|'
    r'new.?feature|enhancement|customiz|config)\b', re.IGNORECASE
)


def classify_transport(t: dict) -> str:
    """
    Cascading 8-rule classification. Returns one of:
      SAP_UPGRADE    - SAP-delivered upgrade, support package, kernel
      SAP_CONFIG     - SAP-side configuration (IMG / customizing, SAP user)
      CUSTOM_DEV     - Customer development (Z/Y namespace, real user)
      BASIS_SYSTEM   - Basis/system transport (service accts, non-Z objects)
      UNKNOWN        - Cannot categorize
    """
    trkorr  = t.get("trkorr", "")
    owner   = t.get("owner", "").upper()
    desc    = t.get("description", "").lower()
    type_   = t.get("type", "")              # Workbench / Customizing
    objs    = t.get("objects", [])
    status  = t.get("status", "")

    # Rule 1: TRKORR pattern -> SAP upgrade/SP
    if SAP_TRKORR_PREFIXES.match(trkorr):
        return "SAP_UPGRADE"

    # Rule 2: Description keywords -> SAP upgrade
    if UPGRADE_KEYWORDS.search(desc):
        return "SAP_UPGRADE"

    # Rule 3: SAP system user + customizing -> SAP config
    if owner in SAP_SYSTEM_USERS:
        return "SAP_CONFIG" if type_ == "Customizing" else "SAP_UPGRADE"

    # Rule 4: Object namespace analysis
    z_objects  = sum(1 for o in objs if o.get("obj_name","").upper().startswith(("Z","Y","/UN","/IDF")))
    sap_objs   = sum(1 for o in objs if o.get("srcsystem","").startswith("SAP"))
    total_objs = len(objs)

    if total_objs > 0:
        z_ratio   = z_objects  / total_objs
        sap_ratio = sap_objs   / total_objs
        if z_ratio > 0.5:
            return "CUSTOM_DEV"
        if sap_ratio > 0.7:
            return "SAP_CONFIG"

    # Rule 5: Service account -> Basis/system
    if SERVICE_ACCOUNTS.match(owner):
        return "BASIS_SYSTEM"

    # Rule 6: Type = Customizing + no Z objects -> SAP_CONFIG
    if type_ == "Customizing" and z_objects == 0:
        return "SAP_CONFIG"

    # Rule 7: Description keyword -> Custom dev
    if DEV_KEYWORDS.search(desc):
        return "CUSTOM_DEV"

    # Rule 8: Type = Workbench with real user -> CUSTOM_DEV
    if type_ == "Workbench" and owner and owner not in SAP_SYSTEM_USERS:
        return "CUSTOM_DEV"

    return "UNKNOWN"


def classify_user(owner: str) -> str:
    """Classify the transport owner."""
    owner_uc = owner.upper()
    if owner_uc in SAP_SYSTEM_USERS:
        return "SAP_SYSTEM"
    if SERVICE_ACCOUNTS.match(owner):
        return "SERVICE_ACCOUNT"
    return "REAL_USER"


# ─────────────────────────────────────────────────────────────────────────────
# QUARTER HELPER
# ─────────────────────────────────────────────────────────────────────────────

def date_to_quarter(yyyymmdd: str) -> str:
    """Convert YYYYMMDD -> 'YYYY-QN'."""
    try:
        d = datetime.strptime(yyyymmdd[:8], "%Y%m%d")
        return f"{d.year}-Q{(d.month - 1) // 3 + 1}"
    except Exception:
        return "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# OBJECT EVOLUTION TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def build_object_evolution(transports: list) -> dict:
    """
    Track every SAP object across its full transport history.

    Returns:
      top_hot_objects      - objects most frequently transported (top 50)
      top_diverse_objects  - objects touched by most different developers
      object_quarter_trend - per-quarter count of object modifications
      object_profiles      - detailed profile per hot object
    """
    # obj_key = (obj_type, obj_name)
    obj_transport_map = defaultdict(list)   # obj_key -> list of transport records
    obj_developer_map = defaultdict(set)    # obj_key -> set of owners
    obj_quarter_map   = defaultdict(Counter) # obj_key -> Counter(quarter -> count)
    quarter_obj_set   = defaultdict(set)    # quarter -> set of unique objects touched

    for t in transports:
        owner   = t.get("owner","")
        quarter = date_to_quarter(t.get("date",""))
        trkorr  = t.get("trkorr","")
        classif = t.get("_classification", "UNKNOWN")
        deploy  = t.get("deploy_level","")

        for o in t.get("objects",[]):
            obj_type = o.get("obj_type","")
            obj_name = o.get("obj_name","")
            if not obj_name or not obj_type:
                continue

            key = (obj_type, obj_name)

            obj_transport_map[key].append({
                "trkorr":       trkorr,
                "date":         t.get("date",""),
                "quarter":      quarter,
                "owner":        owner,
                "classification": classif,
                "deploy_level": deploy,
                "devclass":     o.get("devclass",""),
                "change_cat":   o.get("change_cat",""),
            })
            obj_developer_map[key].add(owner)
            obj_quarter_map[key][quarter] += 1
            if quarter != "UNKNOWN":
                quarter_obj_set[quarter].add(key)

    # Top hot objects (by transport count)
    hot_objects = sorted(obj_transport_map.items(), key=lambda x: len(x[1]), reverse=True)[:50]
    top_hot_objects = []
    for (obj_type, obj_name), records in hot_objects:
        quarters_sorted = sorted(obj_quarter_map[(obj_type, obj_name)].items())
        devclass = records[0].get("devclass","") if records else ""
        top_hot_objects.append({
            "obj_type":        obj_type,
            "obj_name":        obj_name,
            "devclass":        devclass,
            "transport_count": len(records),
            "developer_count": len(obj_developer_map[(obj_type, obj_name)]),
            "developers":      sorted(obj_developer_map[(obj_type, obj_name)]),
            "first_touch":     min((r["date"] for r in records if r["date"]), default=""),
            "last_touch":      max((r["date"] for r in records if r["date"]), default=""),
            "quarter_activity": dict(quarters_sorted),
            "change_cats":     dict(Counter(r["change_cat"] for r in records)),
        })

    # Top diverse objects (most developers touching same object)
    diverse_objects = sorted(obj_transport_map.items(),
                             key=lambda x: len(obj_developer_map[x[0]]), reverse=True)[:30]
    top_diverse_objects = [{
        "obj_type":        obj_type,
        "obj_name":        obj_name,
        "developer_count": len(obj_developer_map[(obj_type, obj_name)]),
        "developers":      sorted(obj_developer_map[(obj_type, obj_name)]),
        "transport_count": len(records),
    } for (obj_type, obj_name), records in diverse_objects if len(obj_developer_map[(obj_type, obj_name)]) > 1]

    # Quarter-level activity: unique objects modified per quarter
    quarter_activity = {q: len(objs) for q, objs in sorted(quarter_obj_set.items())}

    return {
        "top_hot_objects":      top_hot_objects,
        "top_diverse_objects":  top_diverse_objects,
        "unique_objects_total": len(obj_transport_map),
        "quarter_activity":     quarter_activity,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze(raw: dict) -> dict:
    transports = raw.get("transports", [])
    print(f"  Analyzing {len(transports)} transports...")

    # ── Classify all transports
    classif_counter = Counter()
    for t in transports:
        cls = classify_transport(t)
        t["_classification"] = cls
        classif_counter[cls] += 1

    # ── Timeline by quarter
    timeline = defaultdict(Counter)      # quarter -> classification -> count
    for t in transports:
        q = date_to_quarter(t.get("date",""))
        timeline[q][t["_classification"]] += 1

    # ── Deployment distribution
    deploy_dist = Counter(t.get("deploy_level","UNKNOWN") for t in transports)

    # ── Change category distribution (from objects)
    change_cat_dist = Counter()
    for t in transports:
        for o in t.get("objects",[]):
            change_cat_dist[o.get("change_cat","")] += 1

    # ── Top owners with user classification
    owner_data = defaultdict(lambda: {"count": 0, "breakdown": Counter(), "user_class": ""})
    for t in transports:
        owner = t.get("owner","")
        owner_data[owner]["count"] += 1
        owner_data[owner]["breakdown"][t["_classification"]] += 1
        owner_data[owner]["user_class"] = classify_user(owner)

    top_owners = sorted(owner_data.items(), key=lambda x: x[1]["count"], reverse=True)[:30]
    top_owners_list = [{
        "user":       o,
        "count":      d["count"],
        "user_class": d["user_class"],
        "breakdown":  dict(d["breakdown"]),
    } for o, d in top_owners]

    # ── Package breakdown (DEVCLASS)
    pkg_data = defaultdict(lambda: {"obj_count": 0, "transport_count": 0,
                                     "dlvunit": "", "top_categories": Counter()})
    for t in transports:
        pkg_seen = set()
        for o in t.get("objects",[]):
            dc = o.get("devclass","") or "(none)"
            pkg_data[dc]["obj_count"] += 1
            pkg_data[dc]["dlvunit"]    = pkg_data[dc]["dlvunit"] or o.get("dlvunit","")
            pkg_data[dc]["top_categories"][o.get("change_cat","")] += 1
            pkg_seen.add(dc)
        for dc in pkg_seen:
            pkg_data[dc]["transport_count"] += 1

    top_packages = sorted(
        [{"devclass": k, **{kk: v for kk, v in vv.items() if kk != "top_categories"},
          "top_categories": dict(vv["top_categories"].most_common(5))}
         for k, vv in pkg_data.items()],
        key=lambda x: x["obj_count"], reverse=True
    )[:60]

    # ── Domain breakdown (DLVUNIT)
    domain_data = defaultdict(lambda: {"obj_count": 0, "transport_count": 0})
    for t in transports:
        dom_seen = set()
        for o in t.get("objects",[]):
            dl = o.get("dlvunit","") or "UNCLASSIFIED"
            domain_data[dl]["obj_count"] += 1
            dom_seen.add(dl)
        for dl in dom_seen:
            domain_data[dl]["transport_count"] += 1

    top_domains = sorted(
        [{"dlvunit": k, **v} for k, v in domain_data.items()],
        key=lambda x: x["obj_count"], reverse=True
    )[:30]

    # ── KPI totals
    real_users    = len({t["owner"] for t in transports if classify_user(t["owner"])=="REAL_USER"})
    total_objects = sum(t.get("obj_count",0) for t in transports)

    totals = {
        "transports":  len(transports),
        "objects":     total_objects,
        "real_users":  real_users,
        "packages":    len([p for p in top_packages if p["devclass"] and p["devclass"] != "(none)"]),
    }

    # ── Object evolution tracking (user insight: track object/topic evolution)
    print("  Building object evolution tracker...")
    obj_evolution = build_object_evolution(transports)

    return {
        "meta":                  raw.get("meta", {}),
        "totals":                totals,
        "classification_dist":   dict(classif_counter),
        "deployment_dist":       dict(deploy_dist),
        "change_category_dist":  dict(change_cat_dist.most_common(20)),
        "timeline_by_quarter":   {q: dict(v) for q, v in sorted(timeline.items())},
        "top_owners":            top_owners_list,
        "top_packages":          top_packages,
        "top_domains":           top_domains,
        "top_hot_objects":       obj_evolution["top_hot_objects"],
        "top_diverse_objects":   obj_evolution["top_diverse_objects"],
        "object_quarter_activity": obj_evolution["quarter_activity"],
        "unique_objects_total":  obj_evolution["unique_objects_total"],
        # Raw transports (strip internal _classification to keep JSON clean)
        "transports": [{k: v for k, v in t.items() if k != "_classification"}
                       for t in transports],
    }


def main():
    parser = argparse.ArgumentParser(description="CTS Transport Order Analyzer")
    parser.add_argument("--input", type=str, default="cts_5yr_raw.json")
    parser.add_argument("--out",   type=str, default=None)
    args = parser.parse_args()

    outfile = args.out or args.input.replace("_raw.json", "_analyzed.json").replace(".json", "_analyzed.json")

    print("=" * 60)
    print(f"  CTS ANALYZER -- UNESCO Transport Intelligence")
    print(f"  Input  : {args.input}")
    print(f"  Output : {outfile}")
    print("=" * 60)

    with open(args.input, encoding="utf-8") as f:
        raw = json.load(f)

    result = analyze(raw)

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  [OK] Analysis complete")
    print(f"  Transports   : {result['totals']['transports']}")
    print(f"  Objects      : {result['totals']['objects']}")
    print(f"  Unique SAP objects tracked : {result['unique_objects_total']}")
    print(f"  Hot objects (top 50)       : {len(result['top_hot_objects'])}")
    print(f"  Diverse objects (2+ devs)  : {len(result['top_diverse_objects'])}")
    print(f"\n  Classification:")
    for cls, cnt in sorted(result['classification_dist'].items(), key=lambda x: -x[1]):
        pct = cnt / max(result['totals']['transports'], 1) * 100
        print(f"    {cls:<20} {cnt:>6}  ({pct:.1f}%)")
    print(f"\n  Load {outfile} in cts_dashboard.html")
    print("=" * 60)


if __name__ == "__main__":
    main()
