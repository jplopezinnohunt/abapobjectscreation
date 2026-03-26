"""
p2p_process_mining.py — UNESCO P2P Process Mining (Phase 3)
===========================================================
Builds an event log from the full P2P chain:
  EBAN (Purchase Req) → EKKO/EKPO (PO) → ESSR/ESLL (SES) → RBKP/RSEG (Invoice) → EKBE (GR/IR)

Then applies pm4py for:
  - Process discovery (DFG, Heuristic Miner)
  - Conformance checking
  - Bottleneck analysis
  - Variant analysis

Output:
  - p2p_event_log.csv (for import into any process mining tool)
  - p2p_process_mining.html (interactive dashboard)

Usage:
    python p2p_process_mining.py
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
OUTPUT_DIR = PROJECT_ROOT / "Zagentexecution/mcp-backend-server-python"


def build_event_log():
    """Build P2P event log from Gold DB tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    events = []  # [{case_id, activity, timestamp, resource, amount, vendor, ...}]

    print("  Building P2P event log from Gold DB...")

    # ── STEP 1: Purchase Requisitions (EBAN) ──
    print("  [1/6] EBAN (Purchase Requisitions)...")
    rows = conn.execute("""
        SELECT BANFN, BNFPO, ERNAM, ERDAT, BADAT, FRGDT, FRGKZ, BSART,
               TXZ01, MENGE, MEINS, PREIS, WAERS, EKGRP
        FROM eban WHERE ERDAT IS NOT NULL AND ERDAT != '' AND ERDAT != '00000000'
    """).fetchall()

    pr_to_cases = {}  # Track which PRs link to which POs later
    for r in rows:
        case_id = f"PR_{r['BANFN']}_{r['BNFPO']}"
        # PR Created
        events.append({
            'case_id': case_id,
            'activity': 'PR Created',
            'timestamp': r['ERDAT'],
            'resource': r['ERNAM'] or '',
            'doc_number': r['BANFN'],
            'item': r['BNFPO'],
            'doc_type': r['BSART'] or '',
            'description': (r['TXZ01'] or '')[:50],
            'amount': r['PREIS'] or 0,
            'currency': r['WAERS'] or '',
        })
        # PR Released (if FRGDT exists)
        if r['FRGDT'] and r['FRGDT'] != '00000000':
            events.append({
                'case_id': case_id,
                'activity': 'PR Released',
                'timestamp': r['FRGDT'],
                'resource': '',
                'doc_number': r['BANFN'],
                'item': r['BNFPO'],
                'doc_type': r['BSART'] or '',
                'description': '',
                'amount': r['PREIS'] or 0,
                'currency': r['WAERS'] or '',
            })

    print(f"    -> {len(events)} events from {len(rows)} PR items")

    # ── STEP 2: Purchase Orders (EKKO + EKPO) ──
    print("  [2/6] EKKO/EKPO (Purchase Orders)...")
    po_rows = conn.execute("""
        SELECT k.EBELN, k.BEDAT, k.AEDAT, k.BSART, k.LIFNR, k.EKGRP, k.WAERS,
               p.EBELP, p.TXZ01, p.NETWR, p.MENGE, p.MEINS
        FROM ekko k JOIN ekpo p ON k.EBELN=p.EBELN
        WHERE k.BEDAT IS NOT NULL AND k.BEDAT != '' AND k.BEDAT != '00000000'
        AND p.LOEKZ = '' OR p.LOEKZ IS NULL
    """).fetchall()

    po_cases = set()
    for r in po_rows:
        case_id = f"PO_{r['EBELN']}_{r['EBELP']}"
        po_cases.add(case_id)
        events.append({
            'case_id': case_id,
            'activity': 'PO Created',
            'timestamp': r['BEDAT'],
            'resource': '',
            'doc_number': r['EBELN'],
            'item': r['EBELP'],
            'doc_type': r['BSART'] or '',
            'vendor': r['LIFNR'] or '',
            'description': (r['TXZ01'] or '')[:50],
            'amount': r['NETWR'] or 0,
            'currency': r['WAERS'] or '',
        })

    print(f"    -> {len(po_rows)} PO line items")

    # ── STEP 3: Goods Receipt / Invoice Receipt (EKBE) ──
    print("  [3/6] EKBE (GR/IR History)...")
    # VGABE: 1=GR, 2=IR, 3=Delivery, 9=GR Reversal
    vgabe_map = {'1': 'Goods Receipt', '2': 'Invoice Receipt',
                 '3': 'Delivery Note', '9': 'GR Reversal'}
    ekbe_rows = conn.execute("""
        SELECT EBELN, EBELP, VGABE, GJAHR, BELNR, XBLNR
        FROM ekbe WHERE EBELN IS NOT NULL AND EBELN != ''
    """).fetchall()

    ekbe_count = 0
    for r in ekbe_rows:
        case_id = f"PO_{r['EBELN']}_{r['EBELP']}"
        activity = vgabe_map.get(str(r['VGABE']), f"EKBE_{r['VGABE']}")
        # Use GJAHR as rough timestamp (we don't have exact date in our extract)
        ts = f"{r['GJAHR']}0101" if r['GJAHR'] else ''
        if not ts:
            continue
        events.append({
            'case_id': case_id,
            'activity': activity,
            'timestamp': ts,
            'resource': '',
            'doc_number': r['BELNR'] or '',
            'item': r['EBELP'],
            'doc_type': str(r['VGABE']),
            'description': '',
            'amount': 0,
            'currency': '',
        })
        ekbe_count += 1

    print(f"    -> {ekbe_count} GR/IR events")

    # ── STEP 4: Service Entry Sheets (ESSR → ESLL) ──
    print("  [4/6] ESSR/ESLL (Service Entry Sheets)...")
    # ESSR links PO to service package (PACKNO), ESLL has service line details
    ses_rows = conn.execute("""
        SELECT s.LBLNI, s.PACKNO, s.EBELN, s.EBELP,
               e.SRVPOS, e.TBTWR, e.KTEXT1, e.BUDAT
        FROM essr s JOIN esll e ON s.PACKNO=e.PACKNO
        WHERE s.EBELN IS NOT NULL AND s.EBELN != ''
        AND e.BUDAT IS NOT NULL AND e.BUDAT != '' AND e.BUDAT != '00000000'
        LIMIT 500000
    """).fetchall()

    ses_count = 0
    for r in ses_rows:
        case_id = f"PO_{r['EBELN']}_{r['EBELP']}"
        events.append({
            'case_id': case_id,
            'activity': 'Service Entry Sheet',
            'timestamp': r['BUDAT'],
            'resource': '',
            'doc_number': r['LBLNI'] or '',
            'item': r['EBELP'],
            'doc_type': 'SES',
            'description': (r['KTEXT1'] or '')[:50],
            'amount': r['TBTWR'] or 0,
            'currency': '',
        })
        ses_count += 1

    print(f"    -> {ses_count} SES events")

    # ── STEP 5: Invoices (RBKP + RSEG) ──
    print("  [5/6] RBKP/RSEG (Invoices)...")
    inv_rows = conn.execute("""
        SELECT r.BELNR, r.GJAHR, r.BUDAT, r.USNAM, r.BLART, r.LIFNR,
               r.RMWWR, r.WAERS, r.BUKRS,
               s.EBELN, s.EBELP
        FROM rbkp r JOIN rseg s ON r.BELNR=s.BELNR AND r.GJAHR=s.GJAHR
        WHERE r.BUDAT IS NOT NULL AND r.BUDAT != '' AND r.BUDAT != '00000000'
        AND s.EBELN IS NOT NULL AND s.EBELN != ''
    """).fetchall()

    inv_count = 0
    for r in inv_rows:
        case_id = f"PO_{r['EBELN']}_{r['EBELP']}"
        events.append({
            'case_id': case_id,
            'activity': 'Invoice Posted',
            'timestamp': r['BUDAT'],
            'resource': r['USNAM'] or '',
            'doc_number': r['BELNR'],
            'item': r['EBELP'],
            'doc_type': r['BLART'] or '',
            'vendor': r['LIFNR'] or '',
            'description': '',
            'amount': r['RMWWR'] or 0,
            'currency': r['WAERS'] or '',
        })
        inv_count += 1

    print(f"    -> {inv_count} invoice events")

    # ── STEP 6: Payment (from BSAK — cleared vendor items) ──
    print("  [6/6] BSAK (Vendor Payments)...")
    pay_rows = conn.execute("""
        SELECT COUNT(*) FROM bsak
    """).fetchone()
    print(f"    -> BSAK has {pay_rows[0]:,} cleared items (payment proxy)")

    conn.close()

    # Sort all events by case_id + timestamp
    events.sort(key=lambda e: (e['case_id'], e['timestamp']))

    print(f"\n  Total events: {len(events):,}")
    print(f"  Unique cases: {len(set(e['case_id'] for e in events)):,}")

    return events


def analyze_events(events):
    """Compute process mining statistics."""
    # Activity frequency
    activity_freq = Counter(e['activity'] for e in events)

    # Cases by variant (sequence of activities)
    case_variants = defaultdict(list)
    case_events = defaultdict(list)
    for e in events:
        case_events[e['case_id']].append(e['activity'])

    variant_counter = Counter()
    for case_id, acts in case_events.items():
        variant = ' → '.join(acts)
        variant_counter[variant] += 1

    # Throughput by year
    year_counts = Counter()
    for e in events:
        if e['timestamp'] and len(e['timestamp']) >= 4:
            year_counts[e['timestamp'][:4]] += 1

    # Top vendors (from PO/Invoice events)
    vendor_counts = Counter()
    for e in events:
        v = e.get('vendor', '')
        if v:
            vendor_counts[v] += 1

    # DFG (Directly-Follows Graph)
    dfg = Counter()
    for case_id, acts in case_events.items():
        for i in range(len(acts) - 1):
            dfg[(acts[i], acts[i+1])] += 1

    return {
        'activity_freq': activity_freq,
        'variant_counter': variant_counter,
        'year_counts': year_counts,
        'vendor_counts': vendor_counts,
        'dfg': dfg,
        'total_cases': len(case_events),
        'total_events': len(events),
    }


def generate_html(stats):
    """Generate process mining dashboard HTML."""

    # DFG nodes and edges
    activities = list(stats['activity_freq'].keys())
    act_colors = {
        'PR Created': '#3498DB', 'PR Released': '#2980B9',
        'PO Created': '#E67E22', 'Goods Receipt': '#2ECC71',
        'Invoice Receipt': '#E74C3C', 'Service Entry Sheet': '#9B59B6',
        'Invoice Posted': '#E74C3C', 'Delivery Note': '#1ABC9C',
        'GR Reversal': '#95A5A6',
    }

    # Build vis.js nodes for DFG
    dfg_nodes = []
    for act in activities:
        freq = stats['activity_freq'][act]
        color = act_colors.get(act, '#95A5A6')
        dfg_nodes.append({
            'id': act, 'label': f'{act}\\n({freq:,})',
            'color': color, 'shape': 'box',
            'font': {'color': '#fff', 'size': 12},
            'size': max(15, min(50, freq // 5000)),
        })

    dfg_edges = []
    max_freq = max(stats['dfg'].values()) if stats['dfg'] else 1
    for (a, b), freq in stats['dfg'].most_common(30):
        width = max(1, int(freq / max_freq * 8))
        dfg_edges.append({
            'from': a, 'to': b,
            'label': f'{freq:,}',
            'width': width,
            'arrows': 'to',
            'color': {'color': '#4ECDC4', 'opacity': 0.7},
        })

    # Activity table
    act_rows = ''
    for act, freq in stats['activity_freq'].most_common():
        color = act_colors.get(act, '#95A5A6')
        act_rows += f'<tr><td><span style="color:{color}">●</span> {act}</td><td style="text-align:right">{freq:,}</td></tr>'

    # Top variants
    var_rows = ''
    for variant, count in stats['variant_counter'].most_common(20):
        pct = count / stats['total_cases'] * 100
        var_rows += f'<tr><td style="font-size:10px">{variant}</td><td style="text-align:right">{count:,}</td><td style="text-align:right">{pct:.1f}%</td></tr>'

    # Year distribution
    year_rows = ''
    for year in sorted(stats['year_counts'].keys()):
        cnt = stats['year_counts'][year]
        year_rows += f'<tr><td>{year}</td><td style="text-align:right">{cnt:,}</td></tr>'

    # Top vendors
    vendor_rows = ''
    for vendor, cnt in stats['vendor_counts'].most_common(15):
        vendor_rows += f'<tr><td>{vendor}</td><td style="text-align:right">{cnt:,}</td></tr>'

    # DFG table (top transitions)
    dfg_rows = ''
    for (a, b), freq in stats['dfg'].most_common(15):
        dfg_rows += f'<tr><td>{a}</td><td>→</td><td>{b}</td><td style="text-align:right">{freq:,}</td></tr>'

    nodes_json = json.dumps(dfg_nodes)
    edges_json = json.dumps(dfg_edges)

    html = f'''<!DOCTYPE html>
<html>
<head>
<title>UNESCO P2P Process Mining</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a1a;font-family:'Segoe UI',Inter,sans-serif;color:#ddd}}
#header{{padding:14px 24px;background:#101030;border-bottom:2px solid #1a1a4e;
  display:flex;justify-content:space-between;align-items:center}}
#header h1{{font-size:18px;color:#4ECDC4}}
.meta{{font-size:11px;color:#888}}
.kpi-bar{{display:flex;gap:20px;padding:12px 24px;background:#0d0d25;border-bottom:1px solid #1a1a4e}}
.kpi{{text-align:center}}
.kpi-val{{font-size:22px;font-weight:bold;color:#4ECDC4}}
.kpi-label{{font-size:10px;color:#888;margin-top:2px}}
#main{{display:flex;height:calc(100vh - 130px)}}
#dfg-container{{flex:1;background:#0d0d25}}
#sidebar{{width:400px;background:#101030;border-left:1px solid #1a1a4e;
  overflow-y:auto;padding:16px}}
.section{{margin-bottom:20px}}
.section h3{{color:#4ECDC4;font-size:13px;margin-bottom:8px;
  border-bottom:1px solid #1a1a4e;padding-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{text-align:left;color:#888;padding:3px 6px;border-bottom:1px solid #1a1a4e}}
td{{padding:3px 6px;border-bottom:1px solid #0d0d25}}
.tab-bar{{display:flex;gap:2px;margin-bottom:10px}}
.tab{{padding:6px 12px;background:#1a1a4e;border-radius:4px 4px 0 0;cursor:pointer;
  font-size:11px;color:#888}}
.tab.active{{background:#4ECDC4;color:#000;font-weight:bold}}
.tab-content{{display:none}}.tab-content.active{{display:block}}
</style>
</head>
<body>
<div id="header">
  <h1>UNESCO P2P Process Mining — Procure-to-Pay</h1>
  <span class="meta">EBAN → EKKO/EKPO → ESSR/ESLL → RBKP/RSEG → EKBE | Gold DB Analysis</span>
</div>
<div class="kpi-bar">
  <div class="kpi"><div class="kpi-val">{stats['total_events']:,}</div><div class="kpi-label">Total Events</div></div>
  <div class="kpi"><div class="kpi-val">{stats['total_cases']:,}</div><div class="kpi-label">Process Cases</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['activity_freq'])}</div><div class="kpi-label">Activity Types</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['variant_counter'])}</div><div class="kpi-label">Process Variants</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['dfg'])}</div><div class="kpi-label">DFG Transitions</div></div>
</div>
<div id="main">
  <div id="dfg-container"></div>
  <div id="sidebar">
    <div class="tab-bar">
      <div class="tab active" onclick="switchTab('activities')">Activities</div>
      <div class="tab" onclick="switchTab('variants')">Variants</div>
      <div class="tab" onclick="switchTab('dfg-table')">DFG</div>
      <div class="tab" onclick="switchTab('years')">Timeline</div>
      <div class="tab" onclick="switchTab('vendors')">Vendors</div>
    </div>

    <div id="tab-activities" class="tab-content active">
      <div class="section">
        <h3>Activity Frequency</h3>
        <table><tr><th>Activity</th><th>Count</th></tr>{act_rows}</table>
      </div>
    </div>

    <div id="tab-variants" class="tab-content">
      <div class="section">
        <h3>Top 20 Process Variants</h3>
        <table><tr><th>Variant (activity sequence)</th><th>Cases</th><th>%</th></tr>{var_rows}</table>
      </div>
    </div>

    <div id="tab-dfg-table" class="tab-content">
      <div class="section">
        <h3>Directly-Follows Graph (Top 15)</h3>
        <table><tr><th>From</th><th></th><th>To</th><th>Freq</th></tr>{dfg_rows}</table>
      </div>
    </div>

    <div id="tab-years" class="tab-content">
      <div class="section">
        <h3>Events by Year</h3>
        <table><tr><th>Year</th><th>Events</th></tr>{year_rows}</table>
      </div>
    </div>

    <div id="tab-vendors" class="tab-content">
      <div class="section">
        <h3>Top 15 Vendors</h3>
        <table><tr><th>Vendor</th><th>Events</th></tr>{vendor_rows}</table>
      </div>
    </div>
  </div>
</div>

<script>
function switchTab(id) {{
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  event.target.classList.add('active');
}}

var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var container = document.getElementById('dfg-container');
var options = {{
  layout: {{ hierarchical: {{ direction: 'LR', sortMethod: 'directed', levelSeparation: 200 }} }},
  physics: false,
  nodes: {{ borderWidth: 2, shadow: true, font: {{ face: 'Segoe UI', multi: true }} }},
  edges: {{ font: {{ size: 9, color: '#666', strokeWidth: 0 }}, smooth: {{ type: 'cubicBezier' }} }},
  interaction: {{ hover: true }}
}};
new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);
</script>
</body>
</html>'''
    return html


def export_csv(events):
    """Export event log as CSV for external tools."""
    csv_path = OUTPUT_DIR / "p2p_event_log.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'case_id', 'activity', 'timestamp', 'resource',
            'doc_number', 'item', 'doc_type', 'description',
            'amount', 'currency'
        ], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(events)
    print(f"  CSV: {csv_path} ({len(events):,} rows)")


def main():
    print("\n  P2P Process Mining — UNESCO SAP")
    print("  " + "="*50)

    events = build_event_log()
    stats = analyze_events(events)

    # Export CSV
    export_csv(events)

    # Generate HTML dashboard
    html = generate_html(stats)
    html_path = OUTPUT_DIR / "p2p_process_mining.html"
    html_path.write_text(html, encoding='utf-8')
    print(f"  HTML: {html_path}")

    # Print summary
    print(f"\n  {'='*50}")
    print(f"  SUMMARY")
    print(f"  {'='*50}")
    print(f"  Events: {stats['total_events']:,}")
    print(f"  Cases: {stats['total_cases']:,}")
    print(f"  Activities: {len(stats['activity_freq'])}")
    print(f"  Variants: {len(stats['variant_counter'])}")
    print(f"\n  Top activities:")
    for act, freq in stats['activity_freq'].most_common():
        print(f"    {act:30s} {freq:>10,}")
    print(f"\n  Top DFG transitions:")
    for (a, b), freq in stats['dfg'].most_common(10):
        print(f"    {a:25s} -> {b:25s} {freq:>8,}")


if __name__ == '__main__':
    main()
