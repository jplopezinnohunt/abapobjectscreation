"""Patch dashboard to add True Inventory page and corrected breakdowns."""
import json, os

# Fix cts_true_inventory.json (separator issue won't affect JSON)
with open('cts_true_inventory.json', encoding='utf-8') as f:
    inv = json.load(f)

# Re-run print-only summary without unicode separators
buckets = inv['buckets']
total   = inv['total']
sg      = inv['summary_groups']

print("\n=== SUMMARY GROUPS ===")
for grp, cnt in sorted(sg.items(), key=lambda x: -x[1]):
    mods = sum(buckets.get(b,{}).get('mods',0) for b in [
        'Custom Dev -- Classes','Custom Dev -- Reports','Custom Dev -- Func/RFC',
        'Custom Dev -- Fiori/BSP','Custom Dev -- OData/ICF','Custom Dev -- Workflow',
        'Custom Dev -- Enhancements','Custom Dev -- Forms','Custom Data Model',
    ] if grp == 'Custom Dev (all)') or sum(buckets.get(b,{}).get('mods',0) for b,v in buckets.items())
    print(f"  {grp:<35} {cnt:>6,}  {cnt/total*100:.1f}%")

print("\nKey unique counts:")
for b in sorted(buckets, key=lambda x: -buckets[x]['unique']):
    v = buckets[b]
    if v['unique'] >= 50:
        avg = round(v['mods']/v['unique'],1)
        print(f"  {b:<40} {v['unique']:>5,}  {v['mods']:>7,} mods  {avg}x avg")
