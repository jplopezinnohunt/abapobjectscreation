"""
Tier 2 — systematic Segregation-of-Duties (SoD) from ACTUAL behavior (process_mining_maturity.md).
Grounded in research wwyujjqyk (SoD = function->action->permission ruleset, SAP GRC model). Here we run
the ACTION level against what users ACTUALLY did (rsau_audit_history tcode starts) — not what they're
authorized for. This is the "declared-vs-actual" angle and generalizes the BCM dual-control finding to the
whole landscape as a query. (Permission-level + AGR_* role reconciliation = next increment.)

Run:  python process_mining/tier2_sod.py
"""
import sqlite3
from collections import defaultdict

GOLD = r"Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"

# SoD ruleset (ACTION level) — standard Finance/P2P conflicting function pairs.
# Each rule: name, function A tcodes, function B tcodes. A user doing BOTH = a conflict.
RULES = [
    ("Vendor master + Invoice posting",
     {"XK01", "XK02", "FK01", "FK02", "MK01", "MK02"},
     {"MIRO", "MIR7", "FB60", "FB01", "F-43", "FV60"}),
    ("Invoice posting + Payment/clearing",
     {"MIRO", "MIR7", "FB60", "FB01", "F-43", "FV60"},
     {"F110", "F-53", "F-58", "FBRA", "F.13", "F-44", "FF67"}),
    ("Bank master + Payment",
     {"FI12", "FI01", "FI02", "FI12_HBANK"},
     {"F110", "F-53", "F-58"}),
    ("GL master + JE posting",
     {"FS00", "FSP0", "FSS0"},
     {"FB01", "FB50", "F-02"}),
    ("PO create + Goods receipt",
     {"ME21N", "ME21", "ME22N"},
     {"MIGO", "MB01", "MB31"}),
]

TECH = ("SAPSYS", "JOBBATCH", "WF-BATCH", "MULESOFT", "BRIDGE-RFC", "SMTMSBP", "DDIC", "TMSADM")


def main():
    c = sqlite3.connect(GOLD, timeout=10)
    c.execute("PRAGMA busy_timeout=10000")
    # user -> {tcode: count}  from real Transaction Start events
    user_tc = defaultdict(lambda: defaultdict(int))
    q = (f"SELECT SLGUSER, SLGTC, COUNT(*) FROM rsau_audit_history "
         f"WHERE TXSUBCLSID='Transaction Start' AND SLGTC<>'' "
         f"AND SLGUSER NOT IN {TECH} AND SLGUSER NOT LIKE '%RFC%' "
         f"GROUP BY SLGUSER, SLGTC")
    for u, tc, n in c.execute(q):
        user_tc[u][tc] += n
    span = c.execute('SELECT MIN(SAL_DATE),MAX(SAL_DATE) FROM rsau_audit_history').fetchone()
    print(f"SoD over rsau_audit_history (actual behavior) | span {span[0]}->{span[1]} | "
          f"{len(user_tc):,} human users\n")

    total_conflicts = 0
    for name, A, B in RULES:
        hits = []
        for u, tcs in user_tc.items():
            a = {t: tcs[t] for t in A if t in tcs}
            b = {t: tcs[t] for t in B if t in tcs}
            if a and b:
                hits.append((u, sum(a.values()), sum(b.values()), sorted(a) + ["|"] + sorted(b)))
        hits.sort(key=lambda x: -(x[1] + x[2]))
        print(f"=== {name}: {len(hits)} users in conflict ===")
        for u, na, nb, tcs in hits[:8]:
            print(f"  {u:14} A={na:>5} B={nb:>5}  {' '.join(tcs)}")
        total_conflicts += len(hits)
        print()
    print(f"TOTAL action-level SoD conflicts (user x rule): {total_conflicts}")
    print("Next increments: (1) permission level via AGR_*/USOBX_C; (2) reconcile declared auth vs this "
          "actual behavior (right-unused / done-without-role); (3) time-proximity (same user A then B on same doc).")


if __name__ == "__main__":
    main()
