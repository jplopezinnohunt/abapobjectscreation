"""
sap_process_discovery.py
========================
Core process mining engine using pm4py.
Discovers patterns from existing SAP data (CTS transports, FMIFIIT fund documents).

Output is JSON-first (feeds brain graph), HTML-second (visual exploration).

Usage:
    python sap_process_discovery.py --cts-dfg
    python sap_process_discovery.py --cts-variants
    python sap_process_discovery.py --cts-conformance
    python sap_process_discovery.py --cts-bottleneck
    python sap_process_discovery.py --cts-temporal
    python sap_process_discovery.py --fm-lifecycle
    python sap_process_discovery.py --all
    python sap_process_discovery.py --cts-dfg --output html
    python sap_process_discovery.py --cts-dfg --output json  (default)
"""

import os
import sys
import json
import argparse
import sqlite3
from datetime import datetime

import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "process_discovery_output")
EVENTLOG_PATH = os.path.join(BASE_DIR, "cts_eventlog.json")
GOLD_DB_PATH = os.path.join(BASE_DIR, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")

# WRTTP to human-readable activity mapping
WRTTP_ACTIVITY = {
    "50": "Funds Reservation",
    "51": "Funds Reservation Reduction",
    "52": "Funds Reservation Transfer",
    "54": "Actual Expenditure",
    "57": "Actual Revenue",
    "58": "Funds Commitment",
    "60": "Funds Precommitment",
    "61": "Actual Expenditure (Down Payment)",
    "65": "Commitment",
    "66": "Actual (Clearing)",
    "80": "Blocked Funds",
    "81": "Release Blocked Funds",
    "82": "Precommitment",
}


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(data, filename):
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  -> {path}")
    return path


def save_html(html_content, filename):
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    if hasattr(html_content, "save"):
        html_content.save(path)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(html_content))
    print(f"  -> {path}")
    return path


# ─────────────────────────────────────────────────────────────────────
# CTS EVENT LOG LOADING
# ─────────────────────────────────────────────────────────────────────

def load_cts_dataframe():
    with open(EVENTLOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    events = data["events"]
    df = pd.DataFrame(events)
    df = df.rename(columns={
        "caseId": "case:concept:name",
        "activity": "concept:name",
        "timestamp": "time:timestamp",
        "owner": "org:resource",
    })
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    df = df.sort_values("time:timestamp")
    print(f"  CTS event log: {len(df)} events, {df['case:concept:name'].nunique()} cases")
    return df


# ─────────────────────────────────────────────────────────────────────
# FMIFIIT EVENT LOG LOADING
# ─────────────────────────────────────────────────────────────────────

def load_fmifiit_dataframe():
    conn = sqlite3.connect(GOLD_DB_PATH)

    df = pd.read_sql_query("""
        SELECT FONDS, FMBELNR, FMBUZEI, GJAHR, PERIO, WRTTP, FKBTR, FAREA,
               VRGNG, BUKRS, HKONT, KNBELNR, SGTXT
        FROM fmifiit_full
        WHERE WRTTP IN ('50','51','52','54','57','58','60','61','65','66','80','81','82')
    """, conn)
    conn.close()

    # Map WRTTP to activity name
    df["concept:name"] = df["WRTTP"].map(WRTTP_ACTIVITY).fillna("Unknown WRTTP " + df["WRTTP"])

    # Build case ID from fund document
    df["case:concept:name"] = df["FMBELNR"]

    # Build timestamp from GJAHR + PERIO (no BUDAT in our extraction)
    # PERIO is 1-12 (or 13-16 for special periods). Map to month.
    df["month"] = df["PERIO"].astype(str).str.zfill(3).astype(int).clip(1, 12)
    df["time:timestamp"] = pd.to_datetime(
        df["GJAHR"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-15",
        format="%Y-%m-%d",
        errors="coerce"
    )
    df = df.dropna(subset=["time:timestamp"])
    df = df.sort_values("time:timestamp")

    print(f"  FMIFIIT event log: {len(df)} events, {df['case:concept:name'].nunique()} cases")
    return df


# ─────────────────────────────────────────────────────────────────────
# CTS MINING COMMANDS
# ─────────────────────────────────────────────────────────────────────

def cmd_cts_dfg(output_format="json"):
    print("\n[CTS-DFG] Discovering Directly-Follows Graph from CTS transports...")
    df = load_cts_dataframe()

    # Discover DFG directly from DataFrame (pm4py 2.7+)
    dfg, start_activities, end_activities = pm4py.discover_dfg(df)

    # Convert to serializable
    dfg_serial = {f"{a} -> {b}": count for (a, b), count in dfg.items()}

    result = {
        "type": "cts_dfg",
        "generated_at": datetime.now().isoformat(),
        "total_events": len(df),
        "total_cases": df["case:concept:name"].nunique(),
        "dfg_edges": len(dfg),
        "start_activities": dict(start_activities),
        "end_activities": dict(end_activities),
        "dfg": dfg_serial,
        "top_edges": sorted(dfg_serial.items(), key=lambda x: -x[1])[:20],
    }

    save_json(result, "cts_dfg.json")

    if output_format == "html":
        pm4py.save_vis_dfg(dfg, start_activities, end_activities,
                           os.path.join(OUTPUT_DIR, "cts_dfg.png"))
        print(f"  -> {OUTPUT_DIR}/cts_dfg.png")

    return result


def cmd_cts_variants(output_format="json"):
    print("\n[CTS-VARIANTS] Analyzing transport flow variants...")
    df = load_cts_dataframe()

    variants = pm4py.get_variants(df)
    variant_list = []
    for variant_key, count in variants.items():
        activities = list(variant_key) if isinstance(variant_key, tuple) else [variant_key]
        variant_list.append({
            "activities": activities,
            "count": count,
            "flow": " → ".join(activities),
        })
    variant_list.sort(key=lambda x: -x["count"])

    result = {
        "type": "cts_variants",
        "generated_at": datetime.now().isoformat(),
        "total_variants": len(variant_list),
        "total_cases": sum(v["count"] for v in variant_list),
        "top_20_variants": variant_list[:20],
        "all_variants": variant_list,
    }

    save_json(result, "cts_variants.json")
    return result


def cmd_cts_conformance(output_format="json"):
    print("\n[CTS-CONFORMANCE] Checking CTS against expected promotion path...")
    df = load_cts_dataframe()

    # Discover Petri net via pm4py high-level API (pm4py 2.7+)
    net, im, fm = pm4py.discover_petri_net_inductive(df)

    # Token-based replay for conformance
    replayed = pm4py.conformance_diagnostics_token_based_replay(df, net, im, fm)

    fitness_values = [t["trace_fitness"] for t in replayed]
    avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0

    conformant = sum(1 for f in fitness_values if f >= 1.0)
    non_conformant = len(fitness_values) - conformant

    result = {
        "type": "cts_conformance",
        "generated_at": datetime.now().isoformat(),
        "total_traces": len(fitness_values),
        "average_fitness": round(avg_fitness, 4),
        "conformant_traces": conformant,
        "non_conformant_traces": non_conformant,
        "conformance_rate": round(conformant / len(fitness_values) * 100, 1) if fitness_values else 0,
        "fitness_distribution": {
            "perfect (1.0)": conformant,
            "high (0.8-1.0)": sum(1 for f in fitness_values if 0.8 <= f < 1.0),
            "medium (0.5-0.8)": sum(1 for f in fitness_values if 0.5 <= f < 0.8),
            "low (<0.5)": sum(1 for f in fitness_values if f < 0.5),
        },
    }

    save_json(result, "cts_conformance.json")
    return result


def cmd_cts_bottleneck(output_format="json"):
    print("\n[CTS-BOTTLENECK] Performance DFG with time annotations...")
    df = load_cts_dataframe()

    # Performance DFG (average time between activities)
    perf_dfg, start_act, end_act = pm4py.discover_performance_dfg(df)

    # Convert timedelta values to hours
    perf_serial = {}
    for (a, b), duration in perf_dfg.items():
        hours = duration / 3600 if isinstance(duration, (int, float)) else 0
        perf_serial[f"{a} -> {b}"] = round(hours, 2)

    # Find bottlenecks (longest waits)
    sorted_edges = sorted(perf_serial.items(), key=lambda x: -x[1])

    result = {
        "type": "cts_bottleneck",
        "generated_at": datetime.now().isoformat(),
        "unit": "hours",
        "total_edges": len(perf_serial),
        "top_10_bottlenecks": sorted_edges[:10],
        "all_edges": perf_serial,
    }

    save_json(result, "cts_bottleneck.json")

    if output_format == "html":
        pm4py.save_vis_performance_dfg(perf_dfg, start_act, end_act,
                                        os.path.join(OUTPUT_DIR, "cts_bottleneck.png"))
        print(f"  -> {OUTPUT_DIR}/cts_bottleneck.png")

    return result


def cmd_cts_temporal(output_format="json"):
    print("\n[CTS-TEMPORAL] Temporal profile analysis...")
    df = load_cts_dataframe()

    # Discover temporal profile (mean + stdev for each activity pair)
    temporal = pm4py.discover_temporal_profile(df)

    # Convert to serializable format
    temporal_serial = {}
    for key, values in temporal.items():
        a, b = key if isinstance(key, tuple) else (str(key), "")
        mean_sec = values[0] if isinstance(values, (list, tuple)) else values
        stdev_sec = values[1] if isinstance(values, (list, tuple)) and len(values) > 1 else 0
        temporal_serial[f"{a} -> {b}"] = {
            "mean_hours": round(mean_sec / 3600, 2),
            "stdev_hours": round(stdev_sec / 3600, 2),
            "mean_days": round(mean_sec / 86400, 2),
        }

    # Find activities with highest variability (deviation risk)
    by_stdev = sorted(temporal_serial.items(), key=lambda x: -x[1]["stdev_hours"])

    result = {
        "type": "cts_temporal_profile",
        "generated_at": datetime.now().isoformat(),
        "total_pairs": len(temporal_serial),
        "highest_variability": by_stdev[:10],
        "profile": temporal_serial,
    }

    save_json(result, "cts_temporal.json")
    return result


# ─────────────────────────────────────────────────────────────────────
# FM LIFECYCLE MINING
# ─────────────────────────────────────────────────────────────────────

def cmd_fm_lifecycle(output_format="json"):
    print("\n[FM-LIFECYCLE] Fund document lifecycle from FMIFIIT...")
    df = load_fmifiit_dataframe()

    # DFG
    dfg, start_activities, end_activities = pm4py.discover_dfg(df)
    dfg_serial = {f"{a} -> {b}": count for (a, b), count in dfg.items()}

    # Variants
    variants = pm4py.get_variants(df)
    variant_list = []
    for variant_key, count in variants.items():
        activities = list(variant_key) if isinstance(variant_key, tuple) else [variant_key]
        variant_list.append({
            "activities": activities,
            "count": count,
            "flow": " → ".join(activities),
        })
    variant_list.sort(key=lambda x: -x["count"])

    # Conformance against Inductive Miner model
    net, im, fm = pm4py.discover_petri_net_inductive(df)
    replayed = pm4py.conformance_diagnostics_token_based_replay(df, net, im, fm)
    fitness_values = [t["trace_fitness"] for t in replayed]
    avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0

    # WRTTP distribution
    wrttp_dist = df.groupby("concept:name").size().to_dict()

    # Fund area distribution
    farea_dist = df.groupby("FAREA").size().to_dict()

    result = {
        "type": "fm_lifecycle",
        "generated_at": datetime.now().isoformat(),
        "total_events": len(df),
        "total_cases": df["case:concept:name"].nunique(),
        "unique_funds": df["FONDS"].nunique(),
        "dfg_edges": len(dfg_serial),
        "start_activities": dict(start_activities),
        "end_activities": dict(end_activities),
        "dfg": dfg_serial,
        "top_dfg_edges": sorted(dfg_serial.items(), key=lambda x: -x[1])[:20],
        "total_variants": len(variant_list),
        "top_10_variants": variant_list[:10],
        "conformance": {
            "average_fitness": round(avg_fitness, 4),
            "conformant_traces": sum(1 for f in fitness_values if f >= 1.0),
            "total_traces": len(fitness_values),
        },
        "wrttp_distribution": wrttp_dist,
        "fund_area_distribution": farea_dist,
    }

    save_json(result, "fm_process_patterns.json")

    if output_format == "html":
        pm4py.save_vis_dfg(dfg, start_activities, end_activities,
                           os.path.join(OUTPUT_DIR, "fm_lifecycle_dfg.png"))
        print(f"  -> {OUTPUT_DIR}/fm_lifecycle_dfg.png")

    return result


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SAP Process Discovery Engine (pm4py)")
    parser.add_argument("--cts-dfg", action="store_true", help="DFG from CTS event log")
    parser.add_argument("--cts-variants", action="store_true", help="Variant analysis on transport patterns")
    parser.add_argument("--cts-conformance", action="store_true", help="Conformance vs expected CTS path")
    parser.add_argument("--cts-bottleneck", action="store_true", help="Performance DFG with time annotations")
    parser.add_argument("--cts-temporal", action="store_true", help="Temporal profile analysis")
    parser.add_argument("--fm-lifecycle", action="store_true", help="Fund lifecycle from FMIFIIT")
    parser.add_argument("--all", action="store_true", help="Run all analyses")
    parser.add_argument("--output", choices=["json", "html"], default="json",
                        help="Output format (default: json)")
    args = parser.parse_args()

    run_all = args.all or not any([
        args.cts_dfg, args.cts_variants, args.cts_conformance,
        args.cts_bottleneck, args.cts_temporal, args.fm_lifecycle
    ])

    results = {}
    t0 = datetime.now()

    if args.cts_dfg or run_all:
        results["cts_dfg"] = cmd_cts_dfg(args.output)

    if args.cts_variants or run_all:
        results["cts_variants"] = cmd_cts_variants(args.output)

    if args.cts_conformance or run_all:
        results["cts_conformance"] = cmd_cts_conformance(args.output)

    if args.cts_bottleneck or run_all:
        results["cts_bottleneck"] = cmd_cts_bottleneck(args.output)

    if args.cts_temporal or run_all:
        results["cts_temporal"] = cmd_cts_temporal(args.output)

    if args.fm_lifecycle or run_all:
        results["fm_lifecycle"] = cmd_fm_lifecycle(args.output)

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"\n{'='*60}")
    print(f"  Process Discovery complete. {len(results)} analyses in {elapsed:.1f}s")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"{'='*60}")

    # Summary for brain integration
    summary = {
        "engine": "sap_process_discovery.py",
        "generated_at": datetime.now().isoformat(),
        "analyses_run": list(results.keys()),
        "output_dir": OUTPUT_DIR,
    }
    save_json(summary, "discovery_summary.json")


if __name__ == "__main__":
    main()
