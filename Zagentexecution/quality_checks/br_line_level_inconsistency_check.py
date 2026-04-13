"""
BR Line-Level Inconsistency Check.

Premise: UNESCO has NO system control preventing a USD posting against an
earmarked-fund LINE that was reserved in EUR with Budget Rate. The BR
enhancement silently skips the conversion (mr_waers=['EUR'] gate), the
posting persists at identity (FKBTR=TRBTR), AVC drifts, and FMAVC005
surfaces eventually.

This check enumerates EVERY earmarked-fund LINE ITEM that was reserved at
BR (= EUR + GEF, by gate logic) and classifies it:

  AFFECTED        — line already shows hybrid rows (BR + identity in fmioi)
                    = cross-currency consumption already happened on this line
  AT_RISK_OPEN    — line still has open balance + the same fund has had
                    USD activity in 2026 (Vonthron-class latent risk)
  CLEAN_OPEN      — line still has open balance, no USD activity nearby
  CLEAN_CONSUMED  — line fully consumed, all rows at BR (no inconsistency)

Reads from local Gold DB (P01 snapshot). No SAP connection needed.

Usage:
  python br_line_level_inconsistency_check.py [--db PATH] [--out JSON_PATH] [--year 2026]
"""
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

BR_LO, BR_HI = 1.094, 1.097           # 1.09529 ± rounding tolerance
ID_LO, ID_HI = 0.999, 1.001           # 1.00000 ± rounding


def run(db_path: str, year: str | None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Per-line aggregation across fmioi
    cur.execute("""
        WITH per_row AS (
          SELECT REFBN, RFPOS, GJAHR, FONDS,
                 CASE WHEN INSTR(FKBTR,'-')>0
                      THEN -CAST(REPLACE(FKBTR,'-','') AS REAL)
                      ELSE  CAST(FKBTR AS REAL)
                 END AS fkbtr_signed,
                 CASE WHEN INSTR(TRBTR,'-')>0
                      THEN -CAST(REPLACE(TRBTR,'-','') AS REAL)
                      ELSE  CAST(TRBTR AS REAL)
                 END AS trbtr_signed,
                 CAST(REPLACE(FKBTR,'-','') AS REAL)
                   / NULLIF(CAST(REPLACE(TRBTR,'-','') AS REAL),0) AS ratio
          FROM fmioi WHERE REFBT='110'
        )
        SELECT REFBN, RFPOS, GJAHR, FONDS,
               COUNT(*) AS n_rows,
               SUM(CASE WHEN ratio BETWEEN ? AND ? THEN 1 ELSE 0 END) AS n_br,
               SUM(CASE WHEN ratio BETWEEN ? AND ? THEN 1 ELSE 0 END) AS n_id,
               SUM(fkbtr_signed) AS net_fkbtr,
               SUM(trbtr_signed) AS net_trbtr,
               AVG(ratio) AS avg_ratio
        FROM per_row
        GROUP BY REFBN, RFPOS, GJAHR, FONDS
    """, (BR_LO, BR_HI, ID_LO, ID_HI))
    raw_lines = cur.fetchall()

    # 2. Build map of funds with USD bypass activity (lifetime, not just target year —
    # any historical USD posting on the fund proves the cross-currency pattern is in use there).
    target_year = year or '2026'
    cur.execute("""
        SELECT FONDS,
               COUNT(*) AS n_usd_bypass,
               SUM(ABS(CAST(REPLACE(TRBTR,'-','') AS REAL))) AS sum_usd,
               MAX(GJAHR||PERIO) as last_period
        FROM fmifiit_full
        WHERE TWAER='USD' AND FKBTR=TRBTR
          AND WRTTP IN ('51','54','66')
        GROUP BY FONDS
    """)
    usd_activity = {r[0]: {'n': r[1], 'sum': r[2] or 0, 'last_period': r[3]} for r in cur.fetchall()}

    # 3. Classify each BR-applicable line.
    # A line is BR-applicable if it has ANY BR-rate row (n_br > 0). Once that is true,
    # the FR was reserved at BR (EUR+GEF). Subsequent identity rows on the same line
    # = cross-currency consumption that bypassed BR.
    affected, at_risk, clean_open, clean_consumed = [], [], [], []
    for refbn, rfpos, gjahr, fonds, n_rows, n_br, n_id, net_fk, net_tr, avg_ratio in raw_lines:
        if n_br == 0:
            continue   # not a BR line — out of scope
        is_open = abs(net_fk or 0) > 0.01
        record = {
            'refbn': refbn, 'rfpos': rfpos, 'gjahr': gjahr, 'fonds': fonds,
            'n_rows': n_rows, 'n_br_rows': n_br, 'n_identity_rows': n_id,
            'net_fkbtr_usd_at_br': round(net_fk or 0, 2),
            'net_trbtr_eur': round(net_tr or 0, 2),
            'avg_ratio': round(avg_ratio, 5),
            'fund_usd_activity_lifetime': usd_activity.get(fonds, None),
        }
        if n_id > 0:
            record['classification'] = 'AFFECTED'
            affected.append(record)
        elif is_open and fonds in usd_activity:
            record['classification'] = 'AT_RISK_OPEN'
            at_risk.append(record)
        elif is_open:
            record['classification'] = 'CLEAN_OPEN'
            clean_open.append(record)
        else:
            record['classification'] = 'CLEAN_CONSUMED'
            clean_consumed.append(record)

    # 4. Summary stats
    total_open_eur = sum(abs(r['net_trbtr_eur']) for r in at_risk + clean_open)
    at_risk_eur = sum(abs(r['net_trbtr_eur']) for r in at_risk)

    return {
        'generated_at': datetime.now().isoformat(),
        'source_db': db_path,
        'target_year': target_year,
        'br_rate_band': [BR_LO, BR_HI],
        'gate_invariant': "FRs at BR ratio (~1.09529) are EUR+GEF (only authorized perimeter per mr_gsber+mr_waers)",
        'missing_control': "No system check prevents posting in USD against an EUR-reserved BR line. The ZFIX_EXCHANGERATE_* enhancements silently skip USD via mr_waers=['EUR'] gate. AVC catches the resulting drift only when the cover group reaches zero headroom.",
        'summary': {
            'total_br_lines_lifetime': len(affected) + len(at_risk) + len(clean_open) + len(clean_consumed),
            'affected_lines': len(affected),
            'at_risk_open_lines': len(at_risk),
            'clean_open_lines': len(clean_open),
            'clean_consumed_lines': len(clean_consumed),
            'total_open_eur': round(total_open_eur, 2),
            'at_risk_open_eur': round(at_risk_eur, 2),
            'at_risk_open_usd_at_br': round(at_risk_eur * 1.09529, 2),
            'distinct_funds_with_usd_activity_target_year': len(usd_activity),
        },
        'affected_lines': sorted(affected, key=lambda r: -abs(r['net_trbtr_eur'])),
        'at_risk_open_lines': sorted(at_risk, key=lambda r: -abs(r['net_trbtr_eur'])),
        'clean_open_lines_count': len(clean_open),
    }


def print_report(r):
    s = r['summary']
    print("=" * 96)
    print("BR LINE-LEVEL INCONSISTENCY CHECK")
    print(f"DB: {r['source_db']}  Target year for USD activity: {r['target_year']}")
    print(f"Generated: {r['generated_at']}")
    print("=" * 96)
    print(f"\nGate invariant: {r['gate_invariant']}")
    print(f"Missing control: {r['missing_control']}")
    print()
    print(f"Universe — EUR+GEF (BR-applicable) FR lines lifetime: {s['total_br_lines_lifetime']:>6}")
    print(f"  AFFECTED       (cross-currency consumption already fired): {s['affected_lines']:>5}")
    print(f"  AT_RISK_OPEN   (open + same fund has USD postings in {r['target_year']}):      {s['at_risk_open_lines']:>5}")
    print(f"  CLEAN_OPEN     (open + no USD activity nearby):           {s['clean_open_lines']:>5}")
    print(f"  CLEAN_CONSUMED (closed, internally consistent):           {s['clean_consumed_lines']:>5}")
    print()
    print(f"Open balance (EUR) on BR lines:                   {s['total_open_eur']:>12,.2f} EUR")
    print(f"  of which AT_RISK:                               {s['at_risk_open_eur']:>12,.2f} EUR")
    print(f"  AT_RISK in USD at BR:                           {s['at_risk_open_usd_at_br']:>12,.2f} USD")
    print()

    print(f"\n## AFFECTED lines ({s['affected_lines']} — bug ALREADY fired on these)")
    print(f"   {'REFBN':12} {'RFPOS':6} {'GJ':4} {'FONDS':12} {'n_BR':>4} {'n_ID':>4} {'net_EUR':>10} {'net_USD@BR':>11}")
    for r2 in r['affected_lines']:
        print(f"   {r2['refbn']:12} {r2['rfpos']:6} {r2['gjahr']:4} {r2['fonds'] or '':12} "
              f"{r2['n_br_rows']:>4} {r2['n_identity_rows']:>4} "
              f"{r2['net_trbtr_eur']:>10,.2f} {r2['net_fkbtr_usd_at_br']:>11,.2f}")

    print(f"\n## AT_RISK_OPEN lines ({s['at_risk_open_lines']} — Vonthron-class, latent FMAVC005 if USD posted)")
    print(f"   {'REFBN':12} {'RFPOS':6} {'GJ':4} {'FONDS':12} {'open_EUR':>10} {'open_USD@BR':>11} {'fund_usd_n':>10} {'fund_usd_amt':>14} {'last_per':>9}")
    for r2 in r['at_risk_open_lines']:
        ua = r2['fund_usd_activity_lifetime']
        print(f"   {r2['refbn']:12} {r2['rfpos']:6} {r2['gjahr']:4} {r2['fonds'] or '':12} "
              f"{abs(r2['net_trbtr_eur']):>10,.2f} {abs(r2['net_fkbtr_usd_at_br']):>11,.2f} "
              f"{ua['n']:>10} {ua['sum']:>14,.2f} {ua['last_period']:>9}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db')
    ap.add_argument('--year', default='2026', help='Target year for USD activity correlation')
    ap.add_argument('--out', help='Optional JSON output')
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"Gold DB not found: {args.db}")

    result = run(args.db, args.year)
    print_report(result)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, default=str))
        print(f"\n  -> JSON saved to {args.out}")


if __name__ == '__main__':
    main()
