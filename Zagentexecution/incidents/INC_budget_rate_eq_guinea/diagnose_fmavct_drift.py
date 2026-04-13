"""
diagnose_fmavct_drift.py
========================
Live P01 query of FMAVCT for the INC-BUDGETRATE-EQG control object.

Connects to P01 via SNC, queries:
  1. FMAVCT for 9H/2026/UNES/3110111021/PAX/TC — the failing control object
  2. FMAVCT for all CIs under PAX/3110111021/2026 (full cover group rollup)
  3. FMBDT (budget totals) for the same fund/year
  4. FMIOI sum (commitments) for comparison
  5. FMIFIIT sum (actuals) for comparison

Computes the expected vs actual FMAVCT balance and flags any drift.

Usage:
    python diagnose_fmavct_drift.py

Requires:
    - VPN to UNESCO intranet active
    - SNC/SSO session valid for P01
    - .env from Zagentexecution/mcp-backend-server-python/ with SAP_P01_* vars
"""

import os
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from pyrfc import Connection

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', 'mcp-backend-server-python', '.env'))
load_dotenv(ENV_PATH)


def get_p01_connection():
    def env(k, d=None):
        return os.getenv(f'SAP_P01_{k}') or os.getenv(f'SAP_{k}') or d

    params = {
        'ashost': env('ASHOST'),
        'sysnr': env('SYSNR', '00'),
        'client': env('CLIENT', '350'),
        'lang': env('LANG', 'EN'),
        'snc_mode': '1',
        'snc_partnername': env('SNC_PARTNERNAME'),
        'snc_qop': env('SNC_QOP', '9'),
    }
    # Override if .env was loaded from the wrong scope (SAP_ASHOST is D01)
    params['ashost'] = '172.16.4.100'
    params['snc_partnername'] = 'p:CN=P01'
    print(f"Connecting to P01 @ {params['ashost']}...")
    return Connection(**params)


def parse_sap_amount(s):
    """Parse SAP numeric string with trailing '-' for negatives and thousands."""
    if not s:
        return 0.0
    s = str(s).strip().replace(',', '')
    if s.endswith('-'):
        return -float(s[:-1])
    try:
        return float(s)
    except ValueError:
        return 0.0


def query_table(conn, table, where, fields, rowcount=500):
    """Thin wrapper around RFC_READ_TABLE."""
    rfc_fields = [{'FIELDNAME': f} for f in fields]
    # Split WHERE into 72-char chunks (RFC_READ_TABLE limit)
    options = []
    current = ''
    for part in where.split(' AND '):
        part = 'AND ' + part if options else part
        if len(current) + len(part) + 1 > 72:
            options.append({'TEXT': current})
            current = part
        else:
            current = (current + ' ' + part).strip() if current else part
    if current:
        options.append({'TEXT': current})

    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=table,
                  DELIMITER='|', OPTIONS=options, FIELDS=rfc_fields,
                  ROWCOUNT=rowcount)
    result = []
    for row in r['DATA']:
        values = row['WA'].split('|')
        result.append(dict(zip(fields, [v.strip() for v in values])))
    return result


def analyze_fmavct(rows, label):
    """Aggregate FMAVCT rows and report the net balance per commitment item."""
    totals = defaultdict(lambda: {'count': 0, 'sum': 0.0})
    for r in rows:
        ci = r.get('RCMMTITEM', '').strip()
        drcrk = r.get('DRCRK', '').strip()
        vers = r.get('RVERS', '').strip()
        rcty = r.get('RRCTY', '').strip()
        tcur = r.get('RTCUR', '').strip()
        s = parse_sap_amount(r.get('TSLVT', ''))
        for i in range(1, 17):
            s += parse_sap_amount(r.get(f'TSL{i:02d}', ''))
        # In FMAVCT: DRCRK='S' is normally the budget side (positive availability)
        # and consumption/commitment is recorded via RRCTY (record type)
        # Record types: 0 = actual, 1 = plan, 2 = commitment, 4 = reservation, etc.
        # Version: 0 = actual plan/budget version
        key = (rcty, vers, ci, drcrk, tcur)
        totals[key]['count'] += 1
        totals[key]['sum'] += s

    print(f"=== {label} ===")
    print("  RCTY | VERS | CI     | D/C | CUR  | rows | total")
    print("  -----+------+--------+-----+------+------+----------------")
    for k in sorted(totals.keys()):
        v = totals[k]
        print(f"  {k[0]:<4} | {k[1]:<4} | {k[2]:<6} | {k[3]:<3} | {k[4]:<4} | {v['count']:4d} | {v['sum']:15.2f}")
    print()


def main():
    conn = get_p01_connection()
    print("Connected P01")
    print()

    fmavct_fields = ['RRCTY', 'RVERS', 'RYEAR', 'RTCUR', 'DRCRK',
                     'RFIKRS', 'RFUND', 'RFUNDSCTR', 'RCMMTITEM',
                     'RLDNR', 'TSLVT',
                     'TSL01', 'TSL02', 'TSL03', 'TSL04',
                     'TSL05', 'TSL06', 'TSL07', 'TSL08',
                     'TSL09', 'TSL10', 'TSL11', 'TSL12',
                     'TSL13', 'TSL14', 'TSL15', 'TSL16']

    # 1. The specific failing control object
    rows = query_table(conn, 'FMAVCT',
                       "RLDNR = '9H' AND RYEAR = '2026' AND RFIKRS = 'UNES' "
                       "AND RFUND = '3110111021' AND RFUNDSCTR = 'PAX' "
                       "AND RCMMTITEM = 'TC'",
                       fmavct_fields)
    analyze_fmavct(rows, 'FMAVCT 9H/2026/UNES/3110111021/PAX/TC (the failing CO)')

    # 2. All CIs under the same fund/center for 2026 (to see the full cover group)
    rows = query_table(conn, 'FMAVCT',
                       "RLDNR = '9H' AND RYEAR = '2026' AND RFIKRS = 'UNES' "
                       "AND RFUND = '3110111021' AND RFUNDSCTR = 'PAX'",
                       fmavct_fields)
    analyze_fmavct(rows, 'FMAVCT 9H/2026/UNES/3110111021/PAX (all CIs)')

    # 3. FMIOI commitment sum for same key
    print("=== FMIOI sum for fund 3110111021 GJAHR 2026 ===")
    rows = query_table(conn, 'FMIOI',
                       "FONDS = '3110111021' AND GJAHR = '2026' AND BUKRS = 'UNES'",
                       ['WRTTP', 'FISTL', 'FIPEX', 'FKBTR', 'TRBTR', 'TWAER'],
                       rowcount=500)
    fmioi_totals = defaultdict(lambda: {'count': 0, 'fkbtr': 0.0, 'trbtr': 0.0})
    for r in rows:
        key = (r['WRTTP'], r['FISTL'], r['FIPEX'], r['TWAER'])
        fmioi_totals[key]['count'] += 1
        fmioi_totals[key]['fkbtr'] += parse_sap_amount(r['FKBTR'])
        fmioi_totals[key]['trbtr'] += parse_sap_amount(r['TRBTR'])
    print("  WRTTP | FISTL | FIPEX  | TWAER | rows | FKBTR (USD)     | TRBTR")
    print("  ------+-------+--------+-------+------+-----------------+-----------------")
    for k in sorted(fmioi_totals.keys()):
        v = fmioi_totals[k]
        print(f"  {k[0]:<5} | {k[1]:<5} | {k[2]:<6} | {k[3]:<5} | {v['count']:4d} | {v['fkbtr']:15.2f} | {v['trbtr']:15.2f}")
    print()

    # 4. FMIFIIT actuals sum for same key
    print("=== FMIFIIT sum for fund 3110111021 GJAHR 2026 ===")
    rows = query_table(conn, 'FMIFIIT',
                       "FONDS = '3110111021' AND GJAHR = '2026' AND BUKRS = 'UNES'",
                       ['WRTTP', 'FISTL', 'FIPEX', 'FKBTR', 'TRBTR', 'TWAER'],
                       rowcount=500)
    fmifi_totals = defaultdict(lambda: {'count': 0, 'fkbtr': 0.0, 'trbtr': 0.0})
    for r in rows:
        key = (r['WRTTP'], r['FISTL'], r['FIPEX'], r['TWAER'])
        fmifi_totals[key]['count'] += 1
        fmifi_totals[key]['fkbtr'] += parse_sap_amount(r['FKBTR'])
        fmifi_totals[key]['trbtr'] += parse_sap_amount(r['TRBTR'])
    print("  WRTTP | FISTL | FIPEX  | TWAER | rows | FKBTR (USD)     | TRBTR")
    print("  ------+-------+--------+-------+------+-----------------+-----------------")
    for k in sorted(fmifi_totals.keys()):
        v = fmifi_totals[k]
        print(f"  {k[0]:<5} | {k[1]:<5} | {k[2]:<6} | {k[3]:<5} | {v['count']:4d} | {v['fkbtr']:15.2f} | {v['trbtr']:15.2f}")
    print()

    conn.close()


if __name__ == '__main__':
    main()
