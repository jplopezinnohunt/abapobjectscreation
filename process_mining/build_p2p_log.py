"""
Tier 0 (do-it-right): build a PROPERLY-LABELED P2P event log from the source Gold DB tables
(EKKO = Create PO, EKBE by VGABE = Goods/Invoice Receipt), instead of the coarse existing OCEL where
every event collapsed to "PO Created". Then Tier 1: inductive discovery + variants on the REAL process.
This is the semantic-activity-labeling step (deterministic map now; LLM-semantic = the AI-native evolution).

Run:  python process_mining/build_p2p_log.py
"""
import sqlite3, datetime, pandas as pd, pm4py

GOLD = r"Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
# VGABE (PO-history transaction/event type) -> business activity + intra-day order rank
VGABE_ACT = {"1": ("Goods Receipt", 2), "2": ("Invoice Receipt", 3),
             "3": ("Subsequent Adjustment", 4), "9": ("Delivery Cost/Other", 5),
             "C": ("Down Payment", 1), "4": ("Service Entry", 2)}


def to_dt(yyyymmdd, rank):
    try:
        d = datetime.datetime.strptime(yyyymmdd, "%Y%m%d")
        return d + datetime.timedelta(seconds=rank)   # same-day ordering by activity rank
    except Exception:
        return None


def main():
    c = sqlite3.connect(GOLD, timeout=10)
    cols_ekko = {x[1] for x in c.execute("PRAGMA table_info(ekko)")}
    user_col = "ERNAM" if "ERNAM" in cols_ekko else None
    date_col = "AEDAT" if "AEDAT" in cols_ekko else ("BEDAT" if "BEDAT" in cols_ekko else None)
    rows = []
    # Create PO
    sel = f"EBELN,{date_col}" + (f",{user_col}" if user_col else "")
    for r in c.execute(f"SELECT {sel} FROM ekko WHERE {date_col}>'0'"):
        dt = to_dt(r[1], 0)
        if dt: rows.append((r[0], "Create PO", dt, r[2] if user_col else ""))
    # GR / IR / ... from EKBE
    for ebeln, budat, vgabe in c.execute("SELECT EBELN,BUDAT,VGABE FROM ekbe WHERE EBELN<>'' AND BUDAT>'0'"):
        act, rank = VGABE_ACT.get(str(vgabe), (f"PO-hist {vgabe}", 6))
        dt = to_dt(budat, rank)
        if dt: rows.append((ebeln, act, dt, ""))
    log = pd.DataFrame(rows, columns=["case:concept:name", "concept:name", "time:timestamp", "org:resource"])
    print(f"event log: {len(log):,} events / {log['case:concept:name'].nunique():,} cases")
    print("activity counts:")
    for a, n in log["concept:name"].value_counts().items():
        print(f"  {n:>8,}  {a}")

    # Tier 0 quality: keep cases that start with 'Create PO' (complete-from-origin)
    starts = log.sort_values("time:timestamp").groupby("case:concept:name")["concept:name"].first()
    keep = set(starts[starts == "Create PO"].index)
    logq = log[log["case:concept:name"].isin(keep)].copy()
    print(f"\nTier0 quality (cases starting at Create PO): {len(keep):,} cases / {len(logq):,} events")

    # Tier 1: variants + inductive discovery
    logq = pm4py.format_dataframe(logq, case_id="case:concept:name", activity_key="concept:name",
                                  timestamp_key="time:timestamp")
    variants = pm4py.get_variants(logq)
    print(f"\n=== Tier1 — {len(variants):,} variants (the REAL P2P process) ===")
    top = sorted(variants.items(), key=lambda kv: -(kv[1] if isinstance(kv[1], int) else len(kv[1])))[:8]
    for v, cnt in top:
        n = cnt if isinstance(cnt, int) else len(cnt)
        print(f"  {n:>6}x  {' -> '.join(v)}")
    net, im, fm = pm4py.discover_petri_net_inductive(logq, noise_threshold=0.2)
    print(f"  inductive model: {len(net.places)} places, {len(net.transitions)} transitions")
    print("\nDone — Tier1 now on a richly-labeled log (Create PO / GR / IR), real variants visible.")


if __name__ == "__main__":
    main()
