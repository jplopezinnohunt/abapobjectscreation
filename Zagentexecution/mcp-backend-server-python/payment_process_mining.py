"""
payment_process_mining.py — UNESCO Payment Process Mining (Invoice-to-Reconciliation)
======================================================================================
Mines the full payment lifecycle from Gold DB:
  Invoice Posted → Due Date → Advance Payment → Payment Executed (F110) →
  Vendor Cleared → BCM Payment Request

Tables used:
  BKPF  (1.67M) — Document headers (BLART=KR/RE/ZP/KZ/KA)
  BSAK  (739K)  — Vendor cleared items (AUGDT/AUGBL = clearing link)
  BSIK  (8K)    — Vendor open items (not yet paid)
  T042*/T012*   — Payment configuration (FBZP chain)
  T001          — Company code master

Output:
  - payment_event_log.csv (for pm4py / Celonis import)
  - payment_process_mining.html (interactive dashboard with vis.js DFG)

Usage:
    python payment_process_mining.py
"""

import sqlite3
import json
import csv
import sys
import io
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
OUTPUT_DIR = Path(__file__).parent
VIS_JS_PATH = OUTPUT_DIR / "vis-network.min.js"


def date_diff_days(d1, d2):
    """Days between two YYYYMMDD strings. Returns None if invalid."""
    try:
        if not d1 or not d2 or d1 == '00000000' or d2 == '00000000':
            return None
        dt1 = datetime.strptime(d1[:8], '%Y%m%d')
        dt2 = datetime.strptime(d2[:8], '%Y%m%d')
        return (dt2 - dt1).days
    except (ValueError, TypeError):
        return None


def build_event_log():
    """Build payment event log from Gold DB tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    events = []
    print("  Building Payment event log from Gold DB...")

    # ── STEP 1: Invoice Posted (BKPF + BSAK/BSIK for vendor info) ──
    # KR = vendor invoice, RE = invoice (Rechnung), KG = vendor credit memo
    print("  [1/5] Vendor Invoices (BKPF BLART=KR/RE/KG joined with BSAK/BSIK)...")

    # Build invoice→vendor mapping from BSAK + BSIK
    inv_vendor = {}  # (BUKRS, BELNR, GJAHR) -> {LIFNR, WRBTR, WAERS, ZFBDT, ZTERM, AUGDT, AUGBL}
    for tbl in ['bsak', 'bsik']:
        rows = conn.execute(f"""
            SELECT BUKRS, BELNR, GJAHR, BUZEI, LIFNR, WRBTR, WAERS, ZFBDT, ZTERM,
                   AUGDT, AUGBL, BSCHL, BUDAT
            FROM {tbl}
            WHERE LIFNR IS NOT NULL AND LIFNR != ''
              AND BUDAT >= '20240101'
        """).fetchall()
        for r in rows:
            key = (r['BUKRS'], r['BELNR'], r['GJAHR'])
            if key not in inv_vendor:
                inv_vendor[key] = {
                    'LIFNR': r['LIFNR'], 'WRBTR': r['WRBTR'], 'WAERS': r['WAERS'],
                    'ZFBDT': r['ZFBDT'], 'ZTERM': r['ZTERM'],
                    'AUGDT': r['AUGDT'], 'AUGBL': r['AUGBL'],
                    'BSCHL': r['BSCHL'], 'source': tbl,
                }
    print(f"    Vendor mapping: {len(inv_vendor):,} invoice→vendor links")

    # Invoice posted events
    inv_rows = conn.execute("""
        SELECT BUKRS, BELNR, GJAHR, BLART, BUDAT, CPUDT, USNAM, TCODE, WAERS, BKTXT
        FROM bkpf
        WHERE BLART IN ('KR', 'RE', 'KG')
          AND BUDAT >= '20240101'
    """).fetchall()

    invoice_cases = set()
    for r in inv_rows:
        case_id = f"INV_{r['BUKRS']}_{r['BELNR']}_{r['GJAHR']}"
        invoice_cases.add(case_id)
        vendor_info = inv_vendor.get((r['BUKRS'], r['BELNR'], r['GJAHR']), {})
        events.append({
            'case_id': case_id,
            'activity': 'Invoice Posted',
            'timestamp': r['BUDAT'],
            'resource': r['USNAM'] or '',
            'doc_number': r['BELNR'],
            'company_code': r['BUKRS'],
            'doc_type': r['BLART'],
            'tcode': r['TCODE'] or '',
            'amount': vendor_info.get('WRBTR', 0),
            'currency': r['WAERS'] or vendor_info.get('WAERS', ''),
            'vendor': vendor_info.get('LIFNR', ''),
            'description': (r['BKTXT'] or '')[:50],
        })

        # Due date event (ZFBDT)
        zfbdt = vendor_info.get('ZFBDT', '')
        if zfbdt and zfbdt != '00000000' and zfbdt != r['BUDAT']:
            events.append({
                'case_id': case_id,
                'activity': 'Invoice Due',
                'timestamp': zfbdt,
                'resource': '',
                'doc_number': r['BELNR'],
                'company_code': r['BUKRS'],
                'doc_type': r['BLART'],
                'tcode': '',
                'amount': vendor_info.get('WRBTR', 0),
                'currency': r['WAERS'] or '',
                'vendor': vendor_info.get('LIFNR', ''),
                'description': vendor_info.get('ZTERM', ''),
            })

    print(f"    -> {len(inv_rows):,} invoices, {len(invoice_cases):,} unique cases")

    # ── STEP 2: Down Payment Requests (BKPF BLART=KA) ──
    print("  [2/5] Down Payment Requests (BKPF BLART=KA)...")
    dp_rows = conn.execute("""
        SELECT BUKRS, BELNR, GJAHR, BLART, BUDAT, USNAM, TCODE, WAERS, BKTXT
        FROM bkpf
        WHERE BLART = 'KA'
          AND BUDAT >= '20240101'
    """).fetchall()

    for r in dp_rows:
        case_id = f"DP_{r['BUKRS']}_{r['BELNR']}_{r['GJAHR']}"
        vendor_info = inv_vendor.get((r['BUKRS'], r['BELNR'], r['GJAHR']), {})
        events.append({
            'case_id': case_id,
            'activity': 'Down Payment Request',
            'timestamp': r['BUDAT'],
            'resource': r['USNAM'] or '',
            'doc_number': r['BELNR'],
            'company_code': r['BUKRS'],
            'doc_type': r['BLART'],
            'tcode': r['TCODE'] or '',
            'amount': vendor_info.get('WRBTR', 0),
            'currency': r['WAERS'] or '',
            'vendor': vendor_info.get('LIFNR', ''),
            'description': (r['BKTXT'] or '')[:50],
        })
    print(f"    -> {len(dp_rows):,} down payment requests")

    # ── STEP 3: F110 Payment Proposals (REGUH XVORL='X') ──
    print("  [3/8] F110 Payment Proposals (REGUH)...")
    reguh_proposal_count = 0
    reguh_final_count = 0
    try:
        reguh_rows = conn.execute("""
            SELECT LAUFD, LAUFI, ZBUKR, LIFNR, VBLNR, XVORL, HBKID, HKTID
            FROM REGUH
            WHERE LAUFD >= '20240101'
        """).fetchall()

        # Build VBLNR → invoice case linkage (REGUH.VBLNR = payment doc = BSAK.AUGBL)
        for r in reguh_rows:
            vblnr = r['VBLNR'] or ''
            zbukr = r['ZBUKR'] or ''
            is_proposal = r['XVORL'] == 'X'

            # Link via VBLNR → BSAK.AUGBL (same as payment_to_invoices but via REGUH)
            # We'll build this linkage after payment_to_invoices is built
            # For now, create REGUH-level events
            if is_proposal:
                reguh_proposal_count += 1
            else:
                reguh_final_count += 1

        print(f"    -> {len(reguh_rows):,} REGUH items ({reguh_proposal_count:,} proposals, {reguh_final_count:,} final)")
    except Exception as e:
        reguh_rows = []
        print(f"    -> REGUH not available: {e}")

    # ── STEP 3b: Payment Executed (BKPF BLART=ZP/KZ) ──
    print("  [3b/8] Payment Execution (BKPF BLART=ZP/KZ)...")
    pay_rows = conn.execute("""
        SELECT BUKRS, BELNR, GJAHR, BLART, BUDAT, USNAM, TCODE, WAERS, BKTXT
        FROM bkpf
        WHERE BLART IN ('ZP', 'KZ')
          AND BUDAT >= '20240101'
    """).fetchall()

    # Build payment doc → case mapping via BSAK.AUGBL
    # BSAK.AUGBL = payment document number that cleared the invoice
    payment_to_invoices = defaultdict(list)  # payment_doc → [invoice case_ids]
    for (bukrs, belnr, gjahr), info in inv_vendor.items():
        augbl = info.get('AUGBL', '')
        if augbl and augbl != '00000000':
            payment_to_invoices[(bukrs, augbl, gjahr)].append(
                f"INV_{bukrs}_{belnr}_{gjahr}")

    pay_event_count = 0
    unlinked_payments = 0
    for r in pay_rows:
        pay_key = (r['BUKRS'], r['BELNR'], r['GJAHR'])
        linked_cases = payment_to_invoices.get(pay_key, [])

        if linked_cases:
            # Link payment to each invoice it clears
            for case_id in linked_cases:
                events.append({
                    'case_id': case_id,
                    'activity': 'Payment Executed',
                    'timestamp': r['BUDAT'],
                    'resource': r['USNAM'] or '',
                    'doc_number': r['BELNR'],
                    'company_code': r['BUKRS'],
                    'doc_type': r['BLART'],
                    'tcode': r['TCODE'] or '',
                    'amount': 0,
                    'currency': r['WAERS'] or '',
                    'vendor': '',
                    'description': (r['BKTXT'] or '')[:50],
                })
                pay_event_count += 1
        else:
            # Unlinked payment (advance, manual, or cross-year)
            case_id = f"PAY_{r['BUKRS']}_{r['BELNR']}_{r['GJAHR']}"
            events.append({
                'case_id': case_id,
                'activity': 'Payment Executed (Unlinked)',
                'timestamp': r['BUDAT'],
                'resource': r['USNAM'] or '',
                'doc_number': r['BELNR'],
                'company_code': r['BUKRS'],
                'doc_type': r['BLART'],
                'tcode': r['TCODE'] or '',
                'amount': 0,
                'currency': r['WAERS'] or '',
                'vendor': '',
                'description': (r['BKTXT'] or '')[:50],
            })
            unlinked_payments += 1

    print(f"    -> {len(pay_rows):,} payment docs, {pay_event_count:,} linked to invoices, {unlinked_payments:,} unlinked")

    # ── STEP 3c: Link REGUH proposals to invoice cases via VBLNR ──
    # REGUH.VBLNR = payment doc number, same as BSAK.AUGBL
    print("  [3c/8] Linking REGUH proposals to invoices...")
    reguh_linked = 0
    if reguh_rows:
        for r in reguh_rows:
            if r['XVORL'] != 'X':
                continue  # Only proposals, finals are already captured as Payment Executed
            vblnr = r['VBLNR'] or ''
            zbukr = r['ZBUKR'] or ''
            if not vblnr:
                continue
            # Find invoices cleared by this payment doc
            # Try multiple GJAHR since REGUH doesn't have GJAHR
            linked = []
            for gjahr in ['2024', '2025', '2026']:
                linked.extend(payment_to_invoices.get((zbukr, vblnr, gjahr), []))
            if linked:
                for case_id in linked[:3]:  # Limit to avoid explosion
                    events.append({
                        'case_id': case_id,
                        'activity': 'F110 Proposal Created',
                        'timestamp': r['LAUFD'],
                        'resource': '',
                        'doc_number': vblnr,
                        'company_code': zbukr,
                        'doc_type': 'F110',
                        'tcode': 'F110',
                        'amount': 0,
                        'currency': '',
                        'vendor': r['LIFNR'] or '',
                        'description': f"Run:{r['LAUFI']} Bank:{r['HBKID']}",
                    })
                    reguh_linked += 1
    print(f"    -> {reguh_linked:,} proposal events linked to invoices")

    # ── STEP 4: BCM Batch Events (BNK_BATCH_HEADER) ──
    # BCM sits between F110 payment run and bank file transmission
    # Link: BNK_BATCH_HEADER.LAUFD+LAUFI = REGUH.LAUFD+LAUFI = F110 run
    # BCM events: Batch Created (CRDATE) → Batch Approved (CHDATE if CHUSR != CRUSR)
    print("  [4/7] BCM Batches (BNK_BATCH_HEADER)...")
    bcm_count = 0
    bcm_approval_count = 0
    try:
        # Check if BNK_BATCH_HEADER exists in Gold DB
        bcm_rows = conn.execute("""
            SELECT BATCH_NO, RULE_ID, ITEM_CNT, LAUFD, LAUFI,
                   BATCH_SUM, BATCH_CURR, CRUSR, CRDATE, CRTIME,
                   CHUSR, CHDATE, CHTIME, CUR_PROCESSOR, ZBUKR, HBKID, CUR_STS
            FROM BNK_BATCH_HEADER
            WHERE CRDATE >= '20240101'
        """).fetchall()

        for r in bcm_rows:
            # BCM batch = a process case on its own (batch-level tracking)
            case_id = f"BCM_{r['ZBUKR']}_{r['BATCH_NO']}"
            rule = r['RULE_ID'] or ''

            # Batch Created
            events.append({
                'case_id': case_id,
                'activity': 'BCM Batch Created',
                'timestamp': r['CRDATE'],
                'resource': r['CRUSR'] or '',
                'doc_number': r['BATCH_NO'],
                'company_code': r['ZBUKR'] or '',
                'doc_type': 'BCM',
                'tcode': 'BNK_MONI',
                'amount': r['BATCH_SUM'] or 0,
                'currency': r['BATCH_CURR'] or '',
                'vendor': '',
                'description': f"Rule:{rule} Items:{r['ITEM_CNT']} Bank:{r['HBKID']}",
            })
            bcm_count += 1

            # Batch Approved/Changed (if CHDATE != CRDATE or CHUSR != CRUSR)
            chdate = r['CHDATE'] or ''
            crusr = r['CRUSR'] or ''
            chusr = r['CHUSR'] or ''
            if chdate and chdate >= '20240101':
                if chusr != crusr:
                    activity = 'BCM Batch Approved'
                    bcm_approval_count += 1
                else:
                    activity = 'BCM Batch Updated'
                events.append({
                    'case_id': case_id,
                    'activity': activity,
                    'timestamp': chdate,
                    'resource': chusr,
                    'doc_number': r['BATCH_NO'],
                    'company_code': r['ZBUKR'] or '',
                    'doc_type': 'BCM',
                    'tcode': 'BNK_MONI',
                    'amount': r['BATCH_SUM'] or 0,
                    'currency': r['BATCH_CURR'] or '',
                    'vendor': '',
                    'description': f"Status:{r['CUR_STS']}",
                })
                bcm_count += 1

            # Final status events
            cur_sts = r['CUR_STS'] or ''
            bcm_status_map = {
                'IBC05': 'BCM Sent to Bank',
                'IBC11': 'BCM Batch Completed',
                'IBC15': 'BCM Batch Completed',
                'IBC17': 'BCM Batch Failed',
                'IBC06': 'BCM Batch Rejected',
                'IBC20': 'BCM Batch Reversed',
            }
            if cur_sts in bcm_status_map:
                events.append({
                    'case_id': case_id,
                    'activity': bcm_status_map[cur_sts],
                    'timestamp': chdate or r['CRDATE'],
                    'resource': chusr or crusr,
                    'doc_number': r['BATCH_NO'],
                    'company_code': r['ZBUKR'] or '',
                    'doc_type': 'BCM',
                    'tcode': 'BNK_MONI',
                    'amount': r['BATCH_SUM'] or 0,
                    'currency': r['BATCH_CURR'] or '',
                    'vendor': '',
                    'description': f"Status:{cur_sts} Bank:{r['HBKID']}",
                })
                bcm_count += 1

        print(f"    -> {len(bcm_rows):,} BCM batches, {bcm_count:,} events, {bcm_approval_count:,} approvals")
    except Exception as e:
        print(f"    -> BCM data not available: {e}")

    # ── STEP 4b: BCM Batch Items → Invoice linkage ──
    print("  [4b/8] BCM Batch Items → Invoice linkage (BNK_BATCH_ITEM)...")
    bcm_item_linked = 0
    try:
        bcm_items = conn.execute("""
            SELECT BATCH_NO, LIFNR, VBLNR, ZBUKR, LAUFD, HBKID, CUR_STS
            FROM BNK_BATCH_ITEM
            WHERE LAUFD >= '20240101'
        """).fetchall()
        print(f"    {len(bcm_items):,} BCM items loaded")

        for r in bcm_items:
            vblnr = r['VBLNR'] or ''
            zbukr = r['ZBUKR'] or ''
            if not vblnr:
                continue
            # Link BCM item to invoice via VBLNR = BSAK.AUGBL
            for gjahr in ['2024', '2025', '2026']:
                linked = payment_to_invoices.get((zbukr, vblnr, gjahr), [])
                for case_id in linked[:2]:
                    events.append({
                        'case_id': case_id,
                        'activity': 'BCM Batch Routed',
                        'timestamp': r['LAUFD'],
                        'resource': '',
                        'doc_number': r['BATCH_NO'],
                        'company_code': zbukr,
                        'doc_type': 'BCM',
                        'tcode': 'BNK_MONI',
                        'amount': 0,
                        'currency': '',
                        'vendor': r['LIFNR'] or '',
                        'description': f"Bank:{r['HBKID']} Status:{r['CUR_STS']}",
                    })
                    bcm_item_linked += 1
        print(f"    -> {bcm_item_linked:,} BCM items linked to invoices")
    except Exception as e:
        print(f"    -> BCM items not available: {e}")

    # ── STEP 5: Vendor Cleared (BSAK.AUGDT) ──
    print("  [5/8] Vendor Clearing (BSAK.AUGDT)...")
    cleared_count = 0
    for (bukrs, belnr, gjahr), info in inv_vendor.items():
        augdt = info.get('AUGDT', '')
        if augdt and augdt != '00000000' and info.get('source') == 'bsak':
            case_id = f"INV_{bukrs}_{belnr}_{gjahr}"
            events.append({
                'case_id': case_id,
                'activity': 'Vendor Cleared',
                'timestamp': augdt,
                'resource': '',
                'doc_number': info.get('AUGBL', ''),
                'company_code': bukrs,
                'doc_type': 'CLR',
                'tcode': '',
                'amount': info.get('WRBTR', 0),
                'currency': info.get('WAERS', ''),
                'vendor': info.get('LIFNR', ''),
                'description': '',
            })
            cleared_count += 1
    print(f"    -> {cleared_count:,} clearing events")

    # ── STEP 6: Open Items (BSIK — still unpaid) ──
    print("  [6/8] Open Items (BSIK — not yet paid)...")
    open_count = 0
    for (bukrs, belnr, gjahr), info in inv_vendor.items():
        if info.get('source') == 'bsik':
            open_count += 1
    print(f"    -> {open_count:,} invoices still open (no clearing event)")

    # ── STEP 7: Summary ──
    print("  [7/8] Finalizing...")

    conn.close()

    # Sort events by case_id + timestamp
    events.sort(key=lambda e: (e['case_id'], e['timestamp']))

    total_cases = len(set(e['case_id'] for e in events))
    print(f"\n  Total events: {len(events):,}")
    print(f"  Unique cases: {total_cases:,}")

    return events


def analyze_events(events):
    """Compute process mining statistics + cycle times."""
    activity_freq = Counter(e['activity'] for e in events)

    # Cases by variant
    case_events = defaultdict(list)
    case_timestamps = defaultdict(dict)  # case -> {activity: timestamp}
    case_meta = {}  # case -> {company_code, vendor, amount, currency}

    for e in events:
        case_events[e['case_id']].append(e['activity'])
        case_timestamps[e['case_id']][e['activity']] = e['timestamp']
        if e['case_id'] not in case_meta:
            case_meta[e['case_id']] = {
                'company_code': e['company_code'],
                'vendor': e.get('vendor', ''),
                'amount': e.get('amount', 0),
                'currency': e.get('currency', ''),
            }

    variant_counter = Counter()
    for case_id, acts in case_events.items():
        variant = ' → '.join(acts)
        variant_counter[variant] += 1

    # Throughput by month
    month_counts = Counter()
    for e in events:
        ts = e['timestamp']
        if ts and len(ts) >= 6:
            month_counts[ts[:6]] += 1

    # Company code distribution
    bukrs_counts = Counter()
    bukrs_inv_counts = Counter()
    for e in events:
        bukrs_counts[e['company_code']] += 1
        if e['activity'] == 'Invoice Posted':
            bukrs_inv_counts[e['company_code']] += 1

    # DFG
    dfg = Counter()
    for case_id, acts in case_events.items():
        for i in range(len(acts) - 1):
            dfg[(acts[i], acts[i + 1])] += 1

    # ── Cycle Time Analysis ──
    cycle_times = {
        'invoice_to_payment': [],
        'invoice_to_clearing': [],
        'payment_to_clearing': [],
        'due_to_payment': [],  # negative = early, positive = late
    }
    cycle_by_bukrs = defaultdict(lambda: defaultdict(list))

    for case_id, ts_map in case_timestamps.items():
        inv_ts = ts_map.get('Invoice Posted')
        due_ts = ts_map.get('Invoice Due')
        pay_ts = ts_map.get('Payment Executed')
        clr_ts = ts_map.get('Vendor Cleared')
        bukrs = case_meta.get(case_id, {}).get('company_code', '')

        if inv_ts and pay_ts:
            d = date_diff_days(inv_ts, pay_ts)
            if d is not None and 0 <= d <= 365:
                cycle_times['invoice_to_payment'].append(d)
                cycle_by_bukrs[bukrs]['invoice_to_payment'].append(d)

        if inv_ts and clr_ts:
            d = date_diff_days(inv_ts, clr_ts)
            if d is not None and 0 <= d <= 365:
                cycle_times['invoice_to_clearing'].append(d)
                cycle_by_bukrs[bukrs]['invoice_to_clearing'].append(d)

        if pay_ts and clr_ts:
            d = date_diff_days(pay_ts, clr_ts)
            if d is not None and -30 <= d <= 30:
                cycle_times['payment_to_clearing'].append(d)

        if due_ts and pay_ts:
            d = date_diff_days(due_ts, pay_ts)
            if d is not None and -180 <= d <= 365:
                cycle_times['due_to_payment'].append(d)
                cycle_by_bukrs[bukrs]['due_to_payment'].append(d)

    # Compute stats per metric
    cycle_stats = {}
    for metric, values in cycle_times.items():
        if values:
            cycle_stats[metric] = {
                'count': len(values),
                'mean': round(statistics.mean(values), 1),
                'median': round(statistics.median(values), 1),
                'p90': round(sorted(values)[int(len(values) * 0.9)], 1),
                'min': min(values),
                'max': max(values),
            }

    # On-time % (due_to_payment <= 0 means paid on or before due date)
    on_time = sum(1 for d in cycle_times['due_to_payment'] if d <= 0)
    on_time_pct = round(on_time / len(cycle_times['due_to_payment']) * 100, 1) if cycle_times['due_to_payment'] else 0

    # TCODE distribution
    tcode_counts = Counter()
    for e in events:
        if e.get('tcode'):
            tcode_counts[e['tcode']] += 1

    return {
        'activity_freq': activity_freq,
        'variant_counter': variant_counter,
        'month_counts': month_counts,
        'bukrs_counts': bukrs_counts,
        'bukrs_inv_counts': bukrs_inv_counts,
        'dfg': dfg,
        'cycle_stats': cycle_stats,
        'cycle_by_bukrs': dict(cycle_by_bukrs),
        'on_time_pct': on_time_pct,
        'tcode_counts': tcode_counts,
        'total_cases': len(case_events),
        'total_events': len(events),
    }


def load_fbzp_chain(db_path):
    """Load FBZP chain completeness per company code from config tables."""
    conn = sqlite3.connect(str(db_path))

    # Company codes from T001
    codes = {}
    try:
        for r in conn.execute("SELECT BUKRS, BUTXT, LAND1, WAERS FROM T001").fetchall():
            codes[r[0]] = {'name': r[1], 'country': r[2], 'currency': r[3]}
    except Exception:
        pass

    chain = {}
    tables_to_check = {
        'T042': ('BUKRS', 'Paying CoCode'),
        'T042A': ('ZBUKR', 'Pmt Methods/CoCode'),
        'T042E': ('ZLSCH', 'Pmt Methods/Country'),
        'T042I': ('ZBUKR', 'Bank Ranking'),
        'T012': ('BUKRS', 'House Banks'),
        'T012K': ('BUKRS', 'Bank Accounts'),
    }

    for tbl, (key_field, label) in tables_to_check.items():
        try:
            rows = conn.execute(f'SELECT "{key_field}", COUNT(*) FROM "{tbl}" GROUP BY "{key_field}"').fetchall()
            chain[tbl] = {r[0]: r[1] for r in rows}
        except Exception:
            chain[tbl] = {}

    conn.close()
    return codes, chain


def generate_html(stats, db_path):
    """Generate interactive payment process mining dashboard."""

    # Load vis.js
    vis_js = ""
    if VIS_JS_PATH.exists():
        vis_js = VIS_JS_PATH.read_text(encoding='utf-8')
        print(f"  vis.js inlined ({len(vis_js):,} chars)")
    else:
        print(f"  WARNING: {VIS_JS_PATH} not found — DFG will not render!")

    # Load FBZP chain
    codes, fbzp_chain = load_fbzp_chain(db_path)

    # ── DFG Nodes & Edges ──
    act_colors = {
        'Invoice Posted': '#E74C3C',
        'Invoice Due': '#E67E22',
        'Down Payment Request': '#F39C12',
        'F110 Proposal Created': '#27AE60',
        'Payment Executed': '#2ECC71',
        'Payment Executed (Unlinked)': '#229954',
        'BCM Batch Routed': '#A569BD',
        'BCM Batch Created': '#9B59B6',
        'BCM Batch Approved': '#8E44AD',
        'BCM Batch Updated': '#7D3C98',
        'BCM Sent to Bank': '#1ABC9C',
        'BCM Batch Completed': '#16A085',
        'BCM Batch Failed': '#C0392B',
        'BCM Batch Rejected': '#922B21',
        'BCM Batch Reversed': '#7B241C',
        'Vendor Cleared': '#3498DB',
    }

    dfg_nodes = []
    for act in stats['activity_freq']:
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
            'width': width, 'arrows': 'to',
            'color': {'color': '#4ECDC4', 'opacity': 0.7},
        })

    # ── Tab content builders ──

    # Activities tab
    act_rows = ''
    for act, freq in stats['activity_freq'].most_common():
        color = act_colors.get(act, '#95A5A6')
        pct = freq / stats['total_events'] * 100
        act_rows += f'<tr><td><span style="color:{color}">●</span> {act}</td><td class="r">{freq:,}</td><td class="r">{pct:.1f}%</td></tr>'

    # Variants tab
    var_rows = ''
    for variant, count in stats['variant_counter'].most_common(25):
        pct = count / stats['total_cases'] * 100
        # Color-code the variant path
        var_html = variant.replace(' → ', ' <span style="color:#4ECDC4">→</span> ')
        var_rows += f'<tr><td style="font-size:10px">{var_html}</td><td class="r">{count:,}</td><td class="r">{pct:.1f}%</td></tr>'

    # Cycle times tab
    cycle_rows = ''
    metric_labels = {
        'invoice_to_payment': 'Invoice → Payment',
        'invoice_to_clearing': 'Invoice → Clearing (E2E)',
        'payment_to_clearing': 'Payment → Clearing',
        'due_to_payment': 'Due Date → Payment',
    }
    for metric, label in metric_labels.items():
        s = stats['cycle_stats'].get(metric, {})
        if s:
            cycle_rows += f'''<tr><td>{label}</td><td class="r">{s['count']:,}</td>
                <td class="r">{s['mean']}</td><td class="r">{s['median']}</td>
                <td class="r">{s['p90']}</td></tr>'''

    # Company codes tab
    bukrs_rows = ''
    for bukrs, cnt in stats['bukrs_inv_counts'].most_common():
        info = codes.get(bukrs, {})
        name = info.get('name', '')[:20]
        country = info.get('country', '')
        currency = info.get('currency', '')
        # Cycle time for this BUKRS
        cycle_data = stats['cycle_by_bukrs'].get(bukrs, {})
        avg_i2p = ''
        avg_d2p = ''
        if cycle_data.get('invoice_to_payment'):
            avg_i2p = f"{statistics.mean(cycle_data['invoice_to_payment']):.0f}d"
        if cycle_data.get('due_to_payment'):
            vals = cycle_data['due_to_payment']
            avg_d2p = f"{statistics.mean(vals):.0f}d"
            on_time = sum(1 for v in vals if v <= 0)
            on_time_pct = f"{on_time / len(vals) * 100:.0f}%"
        else:
            on_time_pct = '-'
        total_events = stats['bukrs_counts'].get(bukrs, 0)
        bukrs_rows += f'''<tr><td><b>{bukrs}</b></td><td>{name}</td><td>{country}</td>
            <td>{currency}</td><td class="r">{cnt:,}</td><td class="r">{total_events:,}</td>
            <td class="r">{avg_i2p}</td><td class="r">{on_time_pct}</td></tr>'''

    # FBZP chain tab
    chain_tables = ['T042', 'T042A', 'T042E', 'T042I', 'T012', 'T012K']
    chain_labels = ['Paying CoCode', 'Pmt Methods', 'Pmt/Country', 'Bank Ranking', 'House Banks', 'Bank Accounts']
    fbzp_header = ''.join(f'<th>{l}</th>' for l in chain_labels)
    fbzp_rows = ''
    for bukrs in sorted(codes.keys()):
        info = codes[bukrs]
        cells = ''
        for tbl in chain_tables:
            count = fbzp_chain.get(tbl, {}).get(bukrs, 0)
            if count > 0:
                cells += f'<td style="color:#2ECC71;text-align:center">✓ ({count})</td>'
            else:
                cells += '<td style="color:#E74C3C;text-align:center">✗</td>'
        fbzp_rows += f'<tr><td><b>{bukrs}</b></td><td>{info.get("name","")[:18]}</td>{cells}</tr>'

    # Timeline tab
    timeline_rows = ''
    for month in sorted(stats['month_counts'].keys()):
        cnt = stats['month_counts'][month]
        year = month[:4]
        mo = month[4:]
        bar_width = min(300, cnt // 100)
        timeline_rows += f'''<tr><td>{year}-{mo}</td><td class="r">{cnt:,}</td>
            <td><div style="background:#4ECDC4;height:12px;width:{bar_width}px;border-radius:2px"></div></td></tr>'''

    # TCodes tab
    tcode_rows = ''
    for tc, cnt in stats['tcode_counts'].most_common(15):
        tcode_rows += f'<tr><td>{tc}</td><td class="r">{cnt:,}</td></tr>'

    nodes_json = json.dumps(dfg_nodes)
    edges_json = json.dumps(dfg_edges)

    # Avg cycle time for KPI
    avg_e2e = stats['cycle_stats'].get('invoice_to_clearing', {}).get('mean', '-')
    avg_i2p = stats['cycle_stats'].get('invoice_to_payment', {}).get('mean', '-')

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>UNESCO Payment Process Mining — Invoice to Reconciliation</title>
<script>{vis_js}</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a1a;font-family:'Segoe UI',Inter,sans-serif;color:#ddd}}
#header{{padding:14px 24px;background:#101030;border-bottom:2px solid #1a1a4e;
  display:flex;justify-content:space-between;align-items:center}}
#header h1{{font-size:18px;color:#4ECDC4}}
.meta{{font-size:11px;color:#888}}
.kpi-bar{{display:flex;gap:20px;padding:12px 24px;background:#0d0d25;border-bottom:1px solid #1a1a4e;flex-wrap:wrap}}
.kpi{{text-align:center;min-width:100px}}
.kpi-val{{font-size:22px;font-weight:bold;color:#4ECDC4}}
.kpi-val.warn{{color:#E67E22}}
.kpi-val.good{{color:#2ECC71}}
.kpi-label{{font-size:10px;color:#888;margin-top:2px}}
#main{{display:flex;height:calc(100vh - 140px)}}
#dfg-container{{flex:1;background:#0d0d25}}
#sidebar{{width:480px;background:#101030;border-left:1px solid #1a1a4e;overflow-y:auto;padding:16px}}
.section{{margin-bottom:20px}}
.section h3{{color:#4ECDC4;font-size:13px;margin-bottom:8px;border-bottom:1px solid #1a1a4e;padding-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{text-align:left;color:#888;padding:3px 6px;border-bottom:1px solid #1a1a4e}}
td{{padding:3px 6px;border-bottom:1px solid #0d0d25}}
.r{{text-align:right}}
.tab-bar{{display:flex;gap:2px;margin-bottom:10px;flex-wrap:wrap}}
.tab{{padding:6px 12px;background:#1a1a4e;border-radius:4px 4px 0 0;cursor:pointer;font-size:11px;color:#888}}
.tab.active{{background:#4ECDC4;color:#000;font-weight:bold}}
.tab-content{{display:none}}.tab-content.active{{display:block}}
.flow-diagram{{background:#0d0d25;border:1px solid #1a1a4e;border-radius:8px;padding:16px;margin:12px 0;font-size:11px}}
.flow-step{{display:inline-block;padding:6px 12px;border-radius:4px;margin:2px 4px;font-weight:bold}}
.flow-arrow{{color:#4ECDC4;font-size:16px;margin:0 2px}}
</style>
</head>
<body>
<div id="header">
  <h1>UNESCO Payment Process Mining — Invoice to Reconciliation</h1>
  <span class="meta">BKPF + BSAK/BSIK + T042*/T012* | Gold DB | 2024-2026</span>
</div>
<div class="kpi-bar">
  <div class="kpi"><div class="kpi-val">{stats['total_events']:,}</div><div class="kpi-label">Total Events</div></div>
  <div class="kpi"><div class="kpi-val">{stats['total_cases']:,}</div><div class="kpi-label">Process Cases</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['activity_freq'])}</div><div class="kpi-label">Activity Types</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['variant_counter']):,}</div><div class="kpi-label">Variants</div></div>
  <div class="kpi"><div class="kpi-val">{avg_i2p}d</div><div class="kpi-label">Avg Invoice→Payment</div></div>
  <div class="kpi"><div class="kpi-val">{avg_e2e}d</div><div class="kpi-label">Avg E2E Cycle</div></div>
  <div class="kpi"><div class="kpi-val {'good' if stats['on_time_pct'] >= 80 else 'warn'}">{stats['on_time_pct']}%</div><div class="kpi-label">On-Time Payment</div></div>
  <div class="kpi"><div class="kpi-val">{len(stats['bukrs_inv_counts'])}</div><div class="kpi-label">Company Codes</div></div>
</div>
<div id="main">
  <div id="dfg-container"></div>
  <div id="sidebar">
    <div class="tab-bar">
      <div class="tab active" onclick="switchTab('activities')">Activities</div>
      <div class="tab" onclick="switchTab('variants')">Variants</div>
      <div class="tab" onclick="switchTab('cycle')">Cycle Times</div>
      <div class="tab" onclick="switchTab('bukrs')">Company Codes</div>
      <div class="tab" onclick="switchTab('fbzp')">FBZP Chain</div>
      <div class="tab" onclick="switchTab('timeline')">Timeline</div>
      <div class="tab" onclick="switchTab('tcodes')">TCodes</div>
      <div class="tab" onclick="switchTab('bcm')">BCM Flow</div>
    </div>

    <div id="tab-activities" class="tab-content active">
      <div class="section">
        <h3>Activity Frequency</h3>
        <table><tr><th>Activity</th><th>Count</th><th>%</th></tr>{act_rows}</table>
      </div>
    </div>

    <div id="tab-variants" class="tab-content">
      <div class="section">
        <h3>Top 25 Process Variants</h3>
        <table><tr><th>Variant (activity sequence)</th><th>Cases</th><th>%</th></tr>{var_rows}</table>
      </div>
    </div>

    <div id="tab-cycle" class="tab-content">
      <div class="section">
        <h3>Cycle Time Analysis (days)</h3>
        <table><tr><th>Metric</th><th>N</th><th>Mean</th><th>Median</th><th>P90</th></tr>{cycle_rows}</table>
        <p style="color:#888;font-size:10px;margin-top:8px">
          Due→Payment: negative = early, positive = late<br>
          Filtered: Invoice→Payment 0-365d, Due→Payment -180 to 365d
        </p>
      </div>
    </div>

    <div id="tab-bukrs" class="tab-content">
      <div class="section">
        <h3>Company Code Comparison</h3>
        <table><tr><th>Code</th><th>Name</th><th>Country</th><th>Ccy</th><th>Invoices</th><th>Events</th><th>Avg I→P</th><th>On-Time</th></tr>{bukrs_rows}</table>
      </div>
    </div>

    <div id="tab-fbzp" class="tab-content">
      <div class="section">
        <h3>FBZP Payment Chain Completeness</h3>
        <p style="color:#888;font-size:10px;margin-bottom:8px">
          ✓ = configured, ✗ = missing. F110 requires all 6 levels.
        </p>
        <table><tr><th>Code</th><th>Name</th>{fbzp_header}</tr>{fbzp_rows}</table>
      </div>
    </div>

    <div id="tab-timeline" class="tab-content">
      <div class="section">
        <h3>Monthly Event Volume (2024-2026)</h3>
        <table><tr><th>Month</th><th>Events</th><th>Distribution</th></tr>{timeline_rows}</table>
      </div>
    </div>

    <div id="tab-tcodes" class="tab-content">
      <div class="section">
        <h3>Transaction Codes (Top 15)</h3>
        <table><tr><th>TCode</th><th>Count</th></tr>{tcode_rows}</table>
      </div>
    </div>

    <div id="tab-bcm" class="tab-content">
      <div class="section">
        <h3>BCM Payment Flow (Configuration)</h3>
        <div class="flow-diagram">
          <p style="color:#4ECDC4;font-weight:bold;margin-bottom:8px">Standard Payment Flow (F110)</p>
          <span class="flow-step" style="background:#E74C3C">Invoice Posted</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#E67E22">Invoice Due</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#2ECC71">F110 Payment Run</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#3498DB">Payment Medium (DMEE)</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#9B59B6">BCM Batch Created</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#1ABC9C">Bank File Sent</span>
        </div>
        <div class="flow-diagram">
          <p style="color:#F39C12;font-weight:bold;margin-bottom:8px">BCM Manual Payment Request Flow</p>
          <span class="flow-step" style="background:#F39C12">User Creates BCM Request</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#9B59B6">BCM Batch (BNK_MONI)</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#E67E22">Approval (BNK_INI/BNK_COM)</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#1ABC9C">Bank File Sent</span>
        </div>
        <div class="flow-diagram">
          <p style="color:#F39C12;font-weight:bold;margin-bottom:8px">Advance Payment Flow (FBA6/KA)</p>
          <span class="flow-step" style="background:#F39C12">Down Payment Request (KA)</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#2ECC71">F110 or Manual Pay</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#3498DB">Down Payment Posted</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#E74C3C">Invoice Received</span>
          <span class="flow-arrow">→</span>
          <span class="flow-step" style="background:#1ABC9C">DP Clearing</span>
        </div>
        <div style="margin-top:16px">
          <h3>BCM Configuration Requirements</h3>
          <table>
            <tr><th>Step</th><th>Transaction</th><th>What to Check</th></tr>
            <tr><td>1</td><td>SWU3</td><td>Verify SAP_WFRT workflow user active</td></tr>
            <tr><td>2</td><td>SWE2</td><td>BUSISB001 event linkage active</td></tr>
            <tr><td>3</td><td>BNK_MONI</td><td>Batch approval status + routing</td></tr>
            <tr><td>4</td><td>BNK_INI/BNK_COM</td><td>Approval roles assigned</td></tr>
            <tr><td>5</td><td>OBPM1/DMEE</td><td>Payment format tree exists</td></tr>
            <tr><td>6</td><td>OBPM4</td><td>Selection variants (NEVER transported)</td></tr>
            <tr><td>7</td><td>FBZP</td><td>Full 6-level chain configured</td></tr>
          </table>
        </div>
        <div style="margin-top:16px">
          <h3>Custom Programs Found</h3>
          <table>
            <tr><th>Program</th><th>Purpose</th></tr>
            <tr><td>ZFI_SWIFT_UPLOAD_BCM</td><td>BCM SWIFT payment file upload (2.8K lines)</td></tr>
            <tr><td>YENH_FI_DMEE</td><td>DMEE format enhancement (credit/debit calc)</td></tr>
            <tr><td>YCEI_FI_SUPPLIERS_PAYMENT</td><td>Supplier payment enhancement</td></tr>
            <tr><td>Y_F110_AVIS_IBE</td><td>Payment advice form (IBE company code)</td></tr>
            <tr><td>ZF140_CHEQUE_DOC</td><td>Cheque document form (ICTP company code)</td></tr>
          </table>
        </div>
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
  layout: {{ hierarchical: {{ direction: 'LR', sortMethod: 'directed', levelSeparation: 220 }} }},
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
    """Export event log as CSV."""
    csv_path = OUTPUT_DIR / "payment_event_log.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'case_id', 'activity', 'timestamp', 'resource', 'company_code',
            'doc_number', 'doc_type', 'tcode', 'amount', 'currency', 'vendor', 'description'
        ], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(events)
    print(f"  CSV: {csv_path} ({len(events):,} rows)")


def main():
    print("\n  Payment Process Mining — UNESCO SAP")
    print("  " + "=" * 50)

    events = build_event_log()
    stats = analyze_events(events)

    # Export CSV
    export_csv(events)

    # Generate HTML dashboard
    html = generate_html(stats, DB_PATH)
    html_path = OUTPUT_DIR / "payment_process_mining.html"
    html_path.write_text(html, encoding='utf-8')
    print(f"  HTML: {html_path}")

    # Summary
    print(f"\n  {'=' * 50}")
    print(f"  SUMMARY")
    print(f"  {'=' * 50}")
    print(f"  Events: {stats['total_events']:,}")
    print(f"  Cases:  {stats['total_cases']:,}")
    print(f"  Activities: {len(stats['activity_freq'])}")
    print(f"  Variants: {len(stats['variant_counter']):,}")
    print(f"  On-Time: {stats['on_time_pct']}%")

    print(f"\n  Activity frequency:")
    for act, freq in stats['activity_freq'].most_common():
        print(f"    {act:35s} {freq:>10,}")

    print(f"\n  Cycle times (days):")
    for metric, s in stats['cycle_stats'].items():
        print(f"    {metric:25s} mean={s['mean']:6.1f}  median={s['median']:6.1f}  P90={s['p90']:6.1f}  (N={s['count']:,})")

    print(f"\n  Top DFG transitions:")
    for (a, b), freq in stats['dfg'].most_common(10):
        print(f"    {a:30s} → {b:30s} {freq:>8,}")

    print(f"\n  Company code breakdown:")
    for bukrs, cnt in stats['bukrs_inv_counts'].most_common():
        print(f"    {bukrs:6s} {cnt:>8,} invoices")


if __name__ == '__main__':
    main()
