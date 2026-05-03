"""
nightly_diff.py — Compare today's detector output vs yesterday's.
Emit an alert CSV listing pairs that flipped INTO HARD-BLOCK state today.
"""
import csv
import os
import glob
from datetime import datetime, timedelta

NIGHTLY = r'c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\quality_checks\nightly'
TODAY = datetime.now().strftime('%Y%m%d')
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

today_csv = os.path.join(NIGHTLY, f'committed_vs_available_{TODAY}.csv')
yest_csv = os.path.join(NIGHTLY, f'committed_vs_available_{YESTERDAY}.csv')

if not os.path.exists(yest_csv):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] no prior nightly snapshot — skipping diff')
    raise SystemExit(0)

def load(p):
    rows = {}
    with open(p, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            key = (row.get('fund',''), row.get('wbs_objnr',''))
            rows[key] = row.get('pre_flight_verdict','PASS')
    return rows

today = load(today_csv)
yest = load(yest_csv)

new_blocks = []
for key, verdict_today in today.items():
    verdict_yest = yest.get(key, 'PASS')
    if verdict_yest == 'PASS' and verdict_today.startswith('PRE_FLIGHT_BLOCK'):
        new_blocks.append((*key, verdict_today))

resolved = []
for key, verdict_yest in yest.items():
    verdict_today = today.get(key, 'PASS')
    if verdict_yest.startswith('PRE_FLIGHT_BLOCK') and verdict_today == 'PASS':
        resolved.append((*key, verdict_yest))

alert_path = os.path.join(NIGHTLY, f'diff_alert_{TODAY}.csv')
with open(alert_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['change_type','fund','wbs_objnr','verdict'])
    for r in new_blocks: w.writerow(['NEW_BLOCK', *r])
    for r in resolved: w.writerow(['RESOLVED', *r])

print(f'[{datetime.now().strftime("%H:%M:%S")}] diff alert written: {alert_path}')
print(f'  NEW_BLOCK pairs: {len(new_blocks)}')
print(f'  RESOLVED pairs: {len(resolved)}')

if new_blocks:
    print(f'  ALERT: {len(new_blocks)} new pre-flight HARD-BLOCK candidates today')
    # If you want email integration: hook into your SMTP config here
