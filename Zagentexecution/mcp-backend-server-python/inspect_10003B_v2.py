"""Robust inspection of 10003B — use rfc_read_paginated to handle field-buffer split."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

c = get_connection("D01")

print("=== DFPAYG D01 LAUFD=20260507 LAUFI=10003B ===")
rows = rfc_read_paginated(c, "DFPAYG",
    fields=["LAUFD","LAUFI","XVORL","GRPNO","FORMI","HBKID","HKTID","RZAWE","WAERS","ANZ_ERZ","ANZ_ERL"],
    where="LAUFD = '20260507' AND LAUFI = '10003B'",
    batch_size=50, throttle=0.0)
for r in rows: print(f"  {r}")

print("\n=== REGUH D01 LAUFD=20260507 LAUFI=10003B ===")
rows = rfc_read_paginated(c, "REGUH",
    fields=["LIFNR","VBLNR","WAERS","RBETR","HBKID","HKTID","RZAWE",
            "UBNKS","UBNKL","UBNKN","ZBNKL","XVORL"],
    where="LAUFD = '20260507' AND LAUFI = '10003B'",
    batch_size=50, throttle=0.0)
print(f"  total REGUH rows: {len(rows)}")
for r in rows: print(f"  {r}")

print("\n=== REGUP D01 LAUFD=20260507 LAUFI=10003B (sample) ===")
rows = rfc_read_paginated(c, "REGUP",
    fields=["LIFNR","VBLNR","BELNR","BUZEI","WAERS","DMBTR","WRBTR","XBLNR"],
    where="LAUFD = '20260507' AND LAUFI = '10003B'",
    batch_size=50, throttle=0.0)
print(f"  total REGUP rows: {len(rows)}")
for r in rows[:5]: print(f"  {r}")
