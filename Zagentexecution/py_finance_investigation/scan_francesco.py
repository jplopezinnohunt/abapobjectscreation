"""Full footprint of FP_SPEZZANO and M_SPRONK 2022-2026"""
import os, sqlite3, json, sys
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')
sys.path.insert(0,'Zagentexecution/mcp-backend-server-python')

con = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

fp = cur.execute("SELECT * FROM cts_transports WHERE as4user IN ('FP_SPEZZANO','M_SPRONK','S_IGUENINNI') AND as4date BETWEEN '20220421' AND '20260421' ORDER BY as4date DESC").fetchall()
print(f"Total Francesco/Marlies/Said transports 2022-2026: {len(fp)}")

trs = [dict(t) for t in fp]
# Get descriptions
from sap_utils import get_sap_connection
desc = {}
try:
    conn = get_sap_connection('P01')
    trkorrs = [t['trkorr'] for t in trs]
    for i in range(0, len(trkorrs), 8):
        chunk = trkorrs[i:i+8]
        where = " OR ".join(f"TRKORR = '{tt}'" for tt in chunk)
        try:
            r = conn.call('RFC_READ_TABLE', QUERY_TABLE='E07T',
                          FIELDS=[{'FIELDNAME':'TRKORR'},{'FIELDNAME':'LANGU'},{'FIELDNAME':'AS4TEXT'}],
                          OPTIONS=[{'TEXT': where}], DELIMITER='|', ROWCOUNT=0)
            for row in r['DATA']:
                parts = row['WA'].split('|')
                if len(parts) >= 3:
                    tr = parts[0].strip(); lang = parts[1].strip(); txt = parts[2].strip()
                    if tr not in desc or lang == 'E':
                        desc[tr] = {'lang':lang,'text':txt}
        except Exception as e:
            try: conn = get_sap_connection('P01')
            except: pass
except Exception as e:
    print(f"RFC err: {e}")

# Get objects for each
for t in trs:
    objs = cur.execute("SELECT object, obj_name FROM cts_objects WHERE trkorr = ?", (t['trkorr'],)).fetchall()
    t['objects'] = [f"{o['object']}/{o['obj_name']}" for o in objs]
    t['description'] = desc.get(t['trkorr'],{}).get('text','')

with open('Zagentexecution/py_finance_investigation/fp_ms_si_footprint.json','w') as f:
    json.dump(trs, f, indent=2, ensure_ascii=False)

# Classify by description prefix / ticket / content
import re
from collections import Counter, defaultdict
pattern_counts = defaultdict(Counter)  # editor -> pattern
for t in trs:
    txt = t['description']
    u = t['as4user']
    if not txt:
        pattern_counts[u]['UNDOCUMENTED'] += 1
    elif re.match(r'^\s*\d{5,7}\s*[/\-]', txt):
        # Ticket-driven
        m = re.search(r'(Payment Method|Currency|House Bank|Payroll|Bank|FO|Field Office|Vendor|Customer|Asset|Tax|VAT|New|Creat)', txt, re.IGNORECASE)
        if m: pattern_counts[u][f'TICKET_{m.group(1).upper().replace(" ","_")}'] += 1
        else: pattern_counts[u]['TICKET_OTHER'] += 1
    elif re.search(r'LCR_|payroll activit', txt, re.IGNORECASE):
        pattern_counts[u]['LCR'] += 1
    elif re.search(r'C - HR - PY|HR - PY', txt):
        pattern_counts[u]['HR_PY_GENERIC'] += 1
    elif re.search(r'Payment Method|Currency|House Bank|DMEE|Bank', txt, re.IGNORECASE):
        pattern_counts[u]['TREASURY_CONFIG'] += 1
    elif re.search(r'Tax|VAT|GL|Account|FI', txt, re.IGNORECASE):
        pattern_counts[u]['FI_CONFIG'] += 1
    else:
        pattern_counts[u]['OTHER'] += 1

print("\n=== Pattern breakdown by editor (full 2022-2026 footprint) ===")
for u, counts in pattern_counts.items():
    total = sum(counts.values())
    print(f"\n{u} ({total} transports):")
    for p,n in counts.most_common():
        print(f"  {p}: {n}")

# Print description samples (all)
print("\n=== All descriptions ===")
for t in trs:
    txt = t['description'] or '(NO TEXT)'
    print(f"  {t['as4date']} {t['as4user']:13s} {t['trkorr']} | {txt[:100]}")

# Count touches of the 5 WT tables specifically
five_wt = {'T512T','T512W','T52DZ','T52EL','T52EZ'}
wt_touches = [t for t in trs if any(o.split('/')[-1] in five_wt for o in t['objects'])]
print(f"\n=== Francesco/Marlies/Said transports that touch at least one of the 5 WT tables: {len(wt_touches)} ===")
for t in wt_touches:
    wt_in = [o for o in t['objects'] if o.split('/')[-1] in five_wt]
    txt = t['description'] or '(NO TEXT)'
    print(f"  {t['as4date']} {t['as4user']:13s} {t['trkorr']} WT={len(wt_in)}/{len(t['objects'])} | {txt[:80]}")
    for o in wt_in: print(f"      {o}")
