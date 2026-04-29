"""Full object breakdown for FP_SPEZZANO, M_SPRONK, S_IGUENINNI 2022-2026
and identification of WT-adjacent / payroll-bridge objects."""
import os, sqlite3, json
from collections import Counter, defaultdict
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

con = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

# For each of the 3 people, get all their transports + all their objects
users = ['FP_SPEZZANO','M_SPRONK','S_IGUENINNI']
out = {}
for u in users:
    trs = cur.execute("SELECT trkorr, as4date, year FROM cts_transports WHERE as4user=? AND as4date BETWEEN '20220421' AND '20260421' ORDER BY as4date DESC",(u,)).fetchall()
    # Get objects
    trkorr_list = [t['trkorr'] for t in trs]
    q = "SELECT trkorr, object, obj_name FROM cts_objects WHERE trkorr IN (" + ",".join("?"*len(trkorr_list)) + ")"
    objs = cur.execute(q, trkorr_list).fetchall()
    out[u] = {
        'n_transports': len(trs),
        'objects': Counter((o['object'], o['obj_name']) for o in objs),
        'object_types': Counter(o['object'] for o in objs),
        'trs': trs,
        'obj_map': defaultdict(list),
    }
    for o in objs:
        out[u]['obj_map'][o['trkorr']].append((o['object'], o['obj_name']))

# Define expanded WT-adjacent object set:
# Core (5): T512T, T512W, T52DZ, T52EL, T52EZ
# Other WT tables: T511/K/P, T512C/E/N/Z, T52* (many), T527O, T513, T520S, T51P1
# WT→FI bridge: T52EK, T52EM, T52EN (symbolic accounts), T030* (account determination for payroll)
# Payroll payment: T52BT (paymt), T52BK (payment runs)
# Pay scale: T510 family
# Currency × payment: T012/T012K (house bank), V_T042E/ZL/ZM/ZS (payment methods), T042Y/Z
# Schemas/PCRs: PSCC, PCYC, PDWS
# WT classes: T52C0/1/5/CC/CD/CE/CT (schemas/rules)
CORE_5 = {'T512T','T512W','T52DZ','T52EL','T52EZ'}
WT_TABLES = CORE_5 | {'T500L','T500P','T510','T510A','T510D','T510F','T510G','T510I','T510J','T510M','T510N','T510S','T510U','T510W','T511','T511K','T511P','T512','T512C','T512E','T512N','T512Z','T514N','T514V','T539A','T539J','T52BK','T52BT','T52C0','T52C1','T52C5','T52CC','T52CD','T52CE','T52CT','T52D1','T52D2','T52D3','T52D4','T52D5','T52D6','T52D7','T52D8','T52D9','T52EG','T52EH','T52EK','T52EM','T52EN','T52EP','T52FA','T52FB','T527O','T513','T520S','T51P1'}
WT_FI_BRIDGE = {'T52EK','T52EM','T52EN','T52EL','T539J','T030','T030U','T030W','T030B'}  # WT→GL mapping
PAYROLL_PAYMT = {'T52BT','T52BK','T42P'}  # payroll payments
PAY_SCALE_VIEWS = set()  # handled via startswith V_T510
WT_ADJACENT_VIEW_PREFIX = ('V_T51','V_T52','V_T030','V_T012','V_T042','V_T039')
PAYMT_METHOD_TABLES = {'T042E','T042Y','T042Z','T042ZL','T042ZM','T042ZS','T042S'}

def classify_object(obj_type, name):
    if name in CORE_5: return 'WT_CORE_5'
    if name in WT_TABLES: return 'WT_OTHER'
    if name.startswith(('V_T51','V_T52')): return 'WT_VIEW'
    if obj_type in ('PSCC','PCYC','PDWS'): return 'WT_SCHEMA_PCR'
    if name in PAYMT_METHOD_TABLES or name.startswith('V_T042') or name.startswith('VC_T042'): return 'PAYMT_METHOD'
    if name.startswith(('T030','V_T030')): return 'ACCT_DETERM'
    if name.startswith(('T012','V_T012')): return 'HOUSE_BANK'
    if name.startswith(('T039','V_T039')): return 'CASH_MGMT'
    if name.startswith(('T052','V_T052')): return 'PAYMT_TERMS'
    if name.startswith(('T001','V_T001')): return 'COMPANY_CODE'
    if name == 'TPS31' or name.startswith('TPS'): return 'TREASURY'
    if obj_type == 'DMEE': return 'DMEE_FORMAT'
    return 'OTHER'

# Per user, show category breakdown
print("="*70)
for u in users:
    data = out[u]
    print(f"\n{u} — {data['n_transports']} transports")
    cat_counter = Counter()
    tr_categories = defaultdict(set)  # trkorr -> set of categories
    for tr in data['trs']:
        for obj_type, name in data['obj_map'].get(tr['trkorr'],[]):
            cat = classify_object(obj_type, name)
            cat_counter[cat] += 1
            if cat != 'OTHER':
                tr_categories[tr['trkorr']].add(cat)
    # How many TRANSPORTS touch each category?
    tr_cat_counts = Counter()
    for tr, cats in tr_categories.items():
        for c in cats: tr_cat_counts[c] += 1
    print("  OBJECT hits by category:")
    for c,n in cat_counter.most_common():
        print(f"    {c}: {n}")
    print(f"  TRANSPORTS by category (count = TRs that touch at least one):")
    for c,n in tr_cat_counts.most_common():
        print(f"    {c}: {n}")

# Identify transports that touch CORE_5 OR WT_CORE/VIEW/SCHEMA (broad WT)
print("\n\n" + "="*70)
print("WT-RELATED TRANSPORTS (broad: core + views + schemas + bridge)")
print("="*70)
WT_RELATED = {'WT_CORE_5','WT_OTHER','WT_VIEW','WT_SCHEMA_PCR'}
for u in users:
    data = out[u]
    wt_trs = []
    for tr in data['trs']:
        cats = set(classify_object(t, n) for t, n in data['obj_map'].get(tr['trkorr'],[]))
        if cats & WT_RELATED:
            wt_trs.append({'trkorr': tr['trkorr'], 'date': tr['as4date'], 'year': tr['year'], 'cats': list(cats)})
    print(f"\n{u}: {len(wt_trs)} WT-related transports")
    for t in wt_trs[:50]:
        print(f"  {t['date']} {t['trkorr']}  cats={sorted(t['cats'])}")
    if len(wt_trs) > 50: print(f"  ... ({len(wt_trs)-50} more)")

# Save the enriched data
save = {}
for u in users:
    save[u] = {
        'n_transports': out[u]['n_transports'],
        'object_types': dict(out[u]['object_types']),
        'top_objects': out[u]['objects'].most_common(30),
    }
with open('Zagentexecution/py_finance_investigation/fp_ms_si_categorized.json','w') as f:
    json.dump(save, f, indent=2, default=str)
print("\nSaved: fp_ms_si_categorized.json")
