"""
Tier 0 + Tier 1 process-mining pipeline (process_mining_maturity.md roadmap).
Tier 0 (foundation): OCEL 2.0 substrate (pm4py-full) + event-log-QUALITY (incomplete-case filter).
Tier 1 (the product):  INDUCTIVE discovery (real model, not just DFG) + CONFORMANCE (fitness).
Runs on the existing P2P OCEL 2.0 store. First concrete step of the gradual build.

Run:  python process_mining/tier0_1_pipeline.py [object_type]
"""
import sys, pm4py

OCEL = r"Zagentexecution/sap_data_extraction/process_discovery/p2p.ocel2.sqlite"


def main():
    ocel = pm4py.read_ocel2_sqlite(OCEL)
    ots = pm4py.ocel_get_object_types(ocel)
    print(f"OCEL 2.0 loaded — object types: {ots}")
    ot = sys.argv[1] if len(sys.argv) > 1 else "Purchaseorder"
    print(f"\n=== Flattening on object type: {ot} ===")
    log = pm4py.ocel_flattening(ocel, ot)
    A, T, C = "concept:name", "time:timestamp", "case:concept:name"
    n0, c0 = len(log), log[C].nunique()
    print(f"  raw: {n0:,} events / {c0:,} cases")

    # --- Tier 0: event-log QUALITY — drop incomplete cases (no real end activity) ---
    ends = log.sort_values(T).groupby(C)[A].last()
    acts = log[A].value_counts()
    end_acts = set(ends.value_counts().head(5).index)   # the genuine terminal activities
    starts = log.sort_values(T).groupby(C)[A].first()
    start_acts = set(starts.value_counts().head(3).index)
    complete = set(ends[ends.isin(end_acts)].index) & set(starts[starts.isin(start_acts)].index)
    logq = log[log[C].isin(complete)]
    print(f"  Tier0 quality filter: start-acts={start_acts} end-acts={end_acts}")
    print(f"  complete cases kept: {len(complete):,}/{c0:,} ({100*len(complete)//max(c0,1)}%)  "
          f"events {len(logq):,}")

    # --- Tier 1: variants + INDUCTIVE discovery + CONFORMANCE fitness ---
    variants = pm4py.get_variants(logq)
    print(f"\n=== Tier1 ===\n  variants: {len(variants):,}")
    top = sorted(variants.items(), key=lambda kv: -(kv[1] if isinstance(kv[1], int) else len(kv[1])))[:5]
    for v, cnt in top:
        c = cnt if isinstance(cnt, int) else len(cnt)
        seq = " -> ".join(v[:6]) + (" ..." if len(v) > 6 else "")
        print(f"    {c:>6}x  {seq}")
    net, im, fm = pm4py.discover_petri_net_inductive(logq)
    print(f"  inductive model: {len(net.places)} places, {len(net.transitions)} transitions")
    fit = pm4py.fitness_token_based_replay(logq, net, im, fm)
    print(f"  CONFORMANCE fitness (token replay): {fit.get('average_trace_fitness', fit.get('log_fitness')):.3f} "
          f"| perc fitting traces: {fit.get('percentage_of_fitting_traces', '?')}")
    print("\nTier0+1 OK — foundation + inductive discovery + conformance running on real P2P OCEL.")


if __name__ == "__main__":
    main()
