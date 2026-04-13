"""
Budget Rate Consumption Audit — analyzes BR-applicability per FR position
and per fund-level USD consumption.

For a target Fund Reservation:
  1. Lists all positions (RFPOS) of the FR with FKBTR/TRBTR ratio per year.
     A row at ratio 1.09529 = BR was applied (EUR posting) → APPLICABLE
     A row at ratio 1.00000 = BR was bypassed (USD posting, identity) → BYPASSED
     Other ratio = M rate or anomaly → INSPECT
  2. Lists all fmifiit_full consumption rows on the same FUND (broader than the FR)
     showing which were BR-applied vs BR-bypassed.
  3. Quantifies the drift contribution of the BR-bypassed USD rows.

Reads from local Gold DB (no SAP connection required).
Output: JSON + human-readable table.

Usage:
  python budget_rate_consumption_audit.py --fr 3250117351 [--fund 3110111021]
"""
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BR_RATE = 1.09529
# Tolerance must accommodate SAP rounding on small amounts.
# Example: 33.00 EUR * 1.09529 = 36.14457 → rounded to 36.14 → effective ratio 1.09515.
# So at small amounts the visible ratio can deviate by ~0.00015 from BR_RATE.
TOLERANCE = 0.002


def f(s):
    """Parse SAP-style numeric (handles trailing minus sign)."""
    if s is None or s == '':
        return 0.0
    s = str(s).strip()
    if s.endswith('-'):
        return -float(s[:-1])
    return float(s)


def classify(fkbtr, trbtr):
    """Return ('APPLICABLE'|'BYPASSED'|'NOT_APPLICABLE'|'M_RATE'|'ZERO', ratio)."""
    if trbtr == 0 and fkbtr == 0:
        return ('ZERO', 0.0)
    if trbtr == 0:
        return ('NO_TRBTR', 0.0)
    ratio = fkbtr / trbtr
    if abs(ratio - BR_RATE) < TOLERANCE:
        return ('APPLICABLE', ratio)
    if abs(ratio - 1.0) < TOLERANCE:
        return ('BYPASSED', ratio)
    return ('M_RATE_OR_OTHER', ratio)


def audit(db_path: str, fr: str, fund: str | None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Section 1 — FR positions
    cur.execute("""
        SELECT RFPOS, GJAHR, FKBTR, TRBTR, BUDAT
        FROM fmioi WHERE REFBN=? ORDER BY GJAHR, RFPOS, BUDAT
    """, (fr,))
    raw = cur.fetchall()

    fr_by_pos = {}
    for rfpos, gjahr, fkbtr_s, trbtr_s, budat in raw:
        key = (rfpos, gjahr)
        fr_by_pos.setdefault(key, {
            'rfpos': rfpos, 'gjahr': gjahr, 'rows': 0,
            'sum_fkbtr_signed': 0.0, 'sum_trbtr_signed': 0.0,
            'sum_fkbtr_abs': 0.0, 'sum_trbtr_abs': 0.0, 'budat': budat
        })
        d = fr_by_pos[key]
        d['rows'] += 1
        fkbtr, trbtr = f(fkbtr_s), f(trbtr_s)
        d['sum_fkbtr_signed'] += fkbtr
        d['sum_trbtr_signed'] += trbtr
        d['sum_fkbtr_abs'] += abs(fkbtr)
        d['sum_trbtr_abs'] += abs(trbtr)

    fr_positions = []
    for key in sorted(fr_by_pos):
        d = fr_by_pos[key]
        cls, ratio = classify(d['sum_fkbtr_abs'], d['sum_trbtr_abs'])
        # Determine status: pair sums to zero = consumed; non-zero = open
        consumed = abs(d['sum_fkbtr_signed']) < 0.01 and d['sum_trbtr_signed'] == 0
        d['status'] = 'CONSUMED' if consumed else 'OPEN'
        d['classification'] = cls
        d['ratio_abs'] = round(ratio, 5)
        fr_positions.append(d)

    # Section 2 — fund-level USD bypass
    fund_rows = []
    if fund:
        cur.execute("""
            SELECT FMBELNR, FMBUZEI, GJAHR, PERIO, WRTTP, TWAER,
                   FKBTR, TRBTR, KNBELNR, VRGNG, HKONT, SGTXT
            FROM fmifiit_full
            WHERE FONDS=? ORDER BY GJAHR, FMBELNR
        """, (fund,))
        for row in cur.fetchall():
            fkbtr, trbtr = f(row[6]), f(row[7])
            cls, ratio = classify(abs(fkbtr), abs(trbtr))
            fund_rows.append({
                'fmbelnr': row[0], 'buzei': row[1], 'gjahr': row[2],
                'perio': row[3], 'wrttp': row[4], 'twaer': row[5],
                'fkbtr': fkbtr, 'trbtr': trbtr,
                'knbelnr': row[8], 'vrgng': row[9], 'hkont': row[10],
                'sgtxt': (row[11] or '')[:60],
                'classification': cls, 'ratio': round(ratio, 5),
            })

    # Section 3 — drift quantification (USD bypass on same fund)
    bypass_rows = [r for r in fund_rows if r['classification'] == 'BYPASSED' and r['twaer'] == 'USD']
    bypass_total_usd = sum(r['fkbtr'] for r in bypass_rows)

    # Drift: at BR these would have been recorded as fkbtr_at_br = trbtr * BR_RATE
    # Instead they were recorded at fkbtr = trbtr (identity, M-implicit)
    # Drift per row = (BR_RATE - 1.0) * trbtr  ≈ +9.529% of each USD posting
    # IF the FR was loaded at BR but consumption is at identity, the AVC pool
    # is short by (BR_RATE - 1.0)*sum(trbtr) over time.
    drift_estimate = sum((BR_RATE - 1.0) * abs(r['trbtr']) for r in bypass_rows)

    return {
        'fr': fr,
        'fund': fund,
        'br_rate': BR_RATE,
        'timestamp': datetime.now().isoformat(),
        'fr_positions': fr_positions,
        'fr_summary': {
            'total_positions': len(fr_positions),
            'applicable_count': sum(1 for p in fr_positions if p['classification'] == 'APPLICABLE'),
            'bypassed_count': sum(1 for p in fr_positions if p['classification'] == 'BYPASSED'),
            'consumed_count': sum(1 for p in fr_positions if p['status'] == 'CONSUMED'),
            'open_count': sum(1 for p in fr_positions if p['status'] == 'OPEN'),
        },
        'fund_consumption_rows': fund_rows,
        'fund_summary': {
            'total_rows': len(fund_rows),
            'br_applicable_eur': sum(1 for r in fund_rows if r['classification'] == 'APPLICABLE'),
            'br_bypassed_usd': len(bypass_rows),
            'br_bypassed_total_amount_usd': round(bypass_total_usd, 2),
            'estimated_avc_drift_usd': round(drift_estimate, 2),
        },
    }


def print_report(result: dict):
    print(f"\n{'='*78}")
    print(f"BUDGET RATE CONSUMPTION AUDIT — FR {result['fr']}, Fund {result['fund']}")
    print(f"{'='*78}\n")

    print(f"## 1. FR positions ({result['fr_summary']['total_positions']} total)")
    print(f"   Applicable (BR ratio 1.09529): {result['fr_summary']['applicable_count']}")
    print(f"   Bypassed   (identity ratio 1): {result['fr_summary']['bypassed_count']}")
    print(f"   Consumed positions:            {result['fr_summary']['consumed_count']}")
    print(f"   Open positions:                {result['fr_summary']['open_count']}")
    print()
    print(f"   {'RFPOS':6} {'GJAHR':5} {'sum_FKBTR':>14} {'sum_TRBTR':>14} {'ratio':>9} {'status':>9} {'class':>16}")
    for p in result['fr_positions']:
        print(f"   {p['rfpos']:6} {p['gjahr']:5} {p['sum_fkbtr_abs']:14.2f} {p['sum_trbtr_abs']:14.2f} "
              f"{p['ratio_abs']:9.5f} {p['status']:>9} {p['classification']:>16}")

    print(f"\n## 2. Fund-level consumption ({result['fund_summary']['total_rows']} rows)")
    print(f"   EUR rows BR-applied:            {result['fund_summary']['br_applicable_eur']}")
    print(f"   USD rows BR-bypassed:           {result['fund_summary']['br_bypassed_usd']}")
    print(f"   USD bypassed total (signed):    {result['fund_summary']['br_bypassed_total_amount_usd']:>12.2f} USD")
    print(f"   Estimated AVC drift accumulated:{result['fund_summary']['estimated_avc_drift_usd']:>12.2f} USD")
    print()
    print(f"   {'FMBELNR':12} {'GJ':4} {'PER':3} {'W':3} {'TWAER':5} {'FKBTR':>10} {'TRBTR':>10} {'class':>16}")
    for r in result['fund_consumption_rows']:
        if r['classification'] != 'APPLICABLE':  # show only non-EUR-BR rows
            print(f"   {r['fmbelnr']:12} {r['gjahr']:4} {r['perio']:3} {r['wrttp']:3} "
                  f"{r['twaer']:5} {r['fkbtr']:10.2f} {r['trbtr']:10.2f} {r['classification']:>16}  {r['sgtxt']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fr', required=True, help='Fund Reservation number (REFBN in fmioi)')
    ap.add_argument('--fund', help='Fund code (FONDS) for fund-level analysis')
    ap.add_argument('--db', default='p01_gold_master_data.db')
    ap.add_argument('--out', help='Optional JSON output path')
    args = ap.parse_args()

    if not Path(args.db).exists():
        # Try standard project location
        alt = Path('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
        if alt.exists():
            args.db = str(alt)
        else:
            raise SystemExit(f"Gold DB not found: {args.db}")

    result = audit(args.db, args.fr, args.fund)
    print_report(result)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, default=str))
        print(f"\n  -> JSON saved to {args.out}")


if __name__ == '__main__':
    main()
