"""
analyze_user_lock_ush02.py
=========================
The user mass lock/unlock for an upgrade IS logged in USH02 (logon-data change
history; field UFLAG = lock state). This recovers the MEASURED lock (UFLAG->64)
and release (UFLAG->0) mass events per upgrade -- the real maintenance window
boundary (corrects the earlier "not in readable logs" claim). Read-only P01.
UFLAG: 0 = not locked, 64 = locked by administrator.
"""
import sys, os
from collections import Counter
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection, rfc_read_paginated

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WINDOWS = {
    "2026 (import Sun 06-07)": ("20260605", "20260610"),
    "2024 (import Fri 07-05)": ("20240703", "20240709"),
    "2023 (import Sat 06-10)": ("20230608", "20230613"),
}


def hm(t): return f"{t[:2]}:{t[2:4]}"
def dow(d): return DOW[datetime.strptime(d, "%Y%m%d").weekday()]


def peak(sub):
    """Return the dense burst: (date, t_first, t_last, n_users, by) of the peak hour."""
    if not sub:
        return None
    buck = Counter((r["MODDA"], r["MODTI"][:2]) for r in sub)
    (pd, ph), pn = buck.most_common(1)[0]
    grp = [r for r in sub if r["MODDA"] == pd and r["MODTI"][:2] == ph]
    ts = sorted(r["MODTI"] for r in grp)
    by = Counter(r["MODBE"] for r in grp).most_common(1)[0][0]
    return pd, ts[0], ts[-1], len(grp), by


def main():
    conn = get_connection("P01")
    for lab, (a, b) in WINDOWS.items():
        rows = rfc_read_paginated(conn, "USH02", ["UFLAG", "MODDA", "MODTI", "MODBE"],
            [{"TEXT": f"MODDA >= '{a}'"}, {"TEXT": f"AND MODDA <= '{b}'"}],
            batch_size=1_000_000, throttle=0)
        lock = peak([r for r in rows if r["UFLAG"] == "64"])
        unlk = peak([r for r in rows if r["UFLAG"] == "0"])
        print(f"=== {lab} ===")
        if lock and lock[3] > 100:
            print(f"   LOCK   {dow(lock[0])} {lock[0]} {hm(lock[1])}-{hm(lock[2])}  "
                  f"{lock[3]} users -> UFLAG=64  by {lock[4]}")
        else:
            print(f"   LOCK   no mass user-lock in USH02 (peak {lock[3] if lock else 0} users) "
                  f"-> different method (login restriction); use activity-gap inference")
        if unlk and unlk[3] > 100:
            print(f"   UNLOCK {dow(unlk[0])} {unlk[0]} {hm(unlk[1])}-{hm(unlk[2])}  "
                  f"{unlk[3]} users -> UFLAG=0   by {unlk[4]}")
    conn.close()


if __name__ == "__main__":
    main()
