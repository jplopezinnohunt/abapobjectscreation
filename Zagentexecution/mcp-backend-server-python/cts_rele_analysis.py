"""
cts_rele_analysis.py
====================
Parses RELE objects to extract the precise transport release audit trail.

RELE obj_name format: 'D01K9B0218 20170119 161514 AN_LEVEQUE'
  [0] TRKORR (transport number)
  [1] YYYYMMDD (release date)
  [2] HHMMSS   (release time)
  [3] USER     (who released it — may differ from transport creator)

This gives us:
  - Exact release timestamp per transport
  - Cycle time: (release_date - creation_date) = how long in dev
  - Release vs create ownership (who built it vs who pushed it)
"""
import json, re
from collections import defaultdict, Counter
from datetime import datetime, date

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# Index transports by TRKORR for cross-referencing
trkorr_index = {t['trkorr']: t for t in raw['transports']}

release_records = []
parse_errors    = 0

for t in raw['transports']:
    for o in t.get('objects', []):
        if o.get('obj_type','').upper() != 'RELE':
            continue
        name = o.get('obj_name','').strip()
        # Parse: "D01K9B0218 20170119 161514 AN_LEVEQUE"
        parts = name.split()
        if len(parts) < 3:
            parse_errors += 1
            continue
        ref_trkorr = parts[0]
        release_dt_str = parts[1] if len(parts) > 1 else ''
        release_tm_str = parts[2] if len(parts) > 2 else ''
        release_user   = parts[3] if len(parts) > 3 else parts[-1] if len(parts) > 2 else ''

        try:
            release_dt = datetime.strptime(release_dt_str + release_tm_str, '%Y%m%d%H%M%S')
        except:
            parse_errors += 1
            continue

        # Cross-reference the header transport (the one CONTAINING this RELE)
        header_trkorr = t['trkorr']
        creator       = t.get('owner','')
        created_date  = t.get('date','')[:8]

        # Also look up the REFERENCED transport if it's different
        ref_transport = trkorr_index.get(ref_trkorr, {})
        ref_owner     = ref_transport.get('owner','') if ref_transport else ''
        ref_desc      = ref_transport.get('description','') if ref_transport else ''

        try:
            created_dt = datetime.strptime(created_date, '%Y%m%d')
            cycle_days = (release_dt.date() - created_dt.date()).days
        except:
            cycle_days = None

        release_records.append({
            'header_trkorr': header_trkorr,
            'ref_trkorr':    ref_trkorr,
            'release_dt':    release_dt,
            'release_user':  release_user.strip().upper(),
            'creator':       creator.strip().upper(),
            'cycle_days':    cycle_days,
            'ref_desc':      ref_desc,
        })

print(f"Parsed {len(release_records):,} RELE release records ({parse_errors} errors)\n")

# ─── Release user vs creator analysis ────────────────────────────────────────
print("=" * 75)
print("  RELEASE USER vs CREATOR — who builds vs who releases")
print("=" * 75)
same = sum(1 for r in release_records if r['release_user'] == r['creator'] and r['creator'])
diff = sum(1 for r in release_records if r['release_user'] != r['creator'] and r['creator'] and r['release_user'])
print(f"  Same person builds+releases: {same:,} ({same/len(release_records)*100:.0f}%)")
print(f"  Different release user:      {diff:,} ({diff/len(release_records)*100:.0f}%)")

# Top releaser users
releaser_ctr = Counter(r['release_user'] for r in release_records if r['release_user'])
print(f"\n  Top release users (who pushed transports to next system):")
for user, cnt in releaser_ctr.most_common(15):
    pct = cnt / len(release_records) * 100
    bar = '#' * int(pct / 2)
    print(f"  {user.title():<22} {cnt:>5,}  {pct:>4.1f}%  {bar}")

# ─── Cycle time analysis ──────────────────────────────────────────────────────
print(f"\n{'='*75}")
print(f"  TRANSPORT CYCLE TIME (creation -> release)  [days in development]")
print(f"{'='*75}")
valid_cycles = [r['cycle_days'] for r in release_records if r['cycle_days'] is not None and r['cycle_days'] >= 0]
if valid_cycles:
    same_day  = sum(1 for d in valid_cycles if d == 0)
    within_7  = sum(1 for d in valid_cycles if 0 < d <= 7)
    within_30 = sum(1 for d in valid_cycles if 7 < d <= 30)
    long_dev  = sum(1 for d in valid_cycles if 30 < d <= 180)
    very_long = sum(1 for d in valid_cycles if d > 180)
    avg       = sum(valid_cycles) / len(valid_cycles)
    total     = len(valid_cycles)

    print(f"  Average cycle time:        {avg:.1f} days")
    print(f"  Same-day release (0 days): {same_day:>5,} ({same_day/total*100:.0f}%) — hotfixes / urgent changes")
    print(f"  Within 1 week (1–7 days):  {within_7:>5,} ({within_7/total*100:.0f}%) — fast track")
    print(f"  1 week – 1 month:          {within_30:>5,} ({within_30/total*100:.0f}%) — normal sprint")
    print(f"  1–6 months:                {long_dev:>5,} ({long_dev/total*100:.0f}%) — long-running projects")
    print(f"  > 6 months:                {very_long:>5,} ({very_long/total*100:.0f}%) — very old transports released late")

# ─── Year-by-year release activity ───────────────────────────────────────────
print(f"\n{'='*75}")
print(f"  RELEASE ACTIVITY BY YEAR (when transports were actually pushed)")
print(f"{'='*75}")
by_year = defaultdict(int)
for r in release_records:
    by_year[str(r['release_dt'].year)] += 1
for yr in sorted(by_year):
    cnt = by_year[yr]
    bar = '#' * int(cnt / 50)
    print(f"  {yr}  {cnt:>5,}  {bar}")

# ─── Release vs Create year mismatch ─────────────────────────────────────────
print(f"\n  TRANSPORTS RELEASED IN DIFFERENT YEAR THAN CREATED:")
different_year = [r for r in release_records
                  if r['cycle_days'] and r['cycle_days'] > 180]
print(f"  {len(different_year):,} transports took > 6 months from creation to release")
print(f"  Sample (oldest first):")
for r in sorted(different_year, key=lambda x: -x['cycle_days'])[:8]:
    print(f"    {r['ref_trkorr']}  cycle={r['cycle_days']} days  by {r['creator'].title():<18}  released by {r['release_user'].title()}")
