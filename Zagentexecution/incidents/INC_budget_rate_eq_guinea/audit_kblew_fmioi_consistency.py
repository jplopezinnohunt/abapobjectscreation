"""
audit_kblew_fmioi_consistency.py
================================
Audits consistency between the Fund Reservation consumption log (KBLEW) and
the FM Commitments table (FMIOI) for FR 3250117351 on UNESCO P01.

Expected invariants (per knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md):
  - Every EUR consumption row in KBLEW should have curtp=00 (transaction) and
    curtp=10 (FM area) with ratio wrbtr(10)/wrbtr(00) = 1.09529 (EURX rate type).
  - Each matching FMIOI row for WRTTP in (54/51/81/66) with TWAER=EUR should
    show FKBTR/TRBTR = 1.09529.
  - KBLE line ties to an FI doc via (RBELNR, RGJAHR); that FI doc appears in
    FMIFIIT via KNBELNR+KNGJAHR, which is the bridge to the FMIOI consumption
    reduction row.

Approach:
  1. Pull KBLEW rows for BELNR=3250117351 via RFC `/SAPPSPRO/PD_GM_FMR2_READ_KBLE`
     (handles cluster table). Use T_RANGE_BLPOS with OPTION='BT', LOW='001',
     HIGH='999' (non-blank HIGH required to avoid pyrfc numeric-string error).
  2. Pull KBLE (header/consumption) rows the same way to obtain RBELNR/RGJAHR.
  3. Pull FMIOI rows via RFC_READ_TABLE with REFBN='3250117351' — FMIOI is a
     transparent table so direct read is safe.
  4. Compute ratios, flag drift, cross-correlate via (RBELNR, RGJAHR) ->
     FMIFIIT.KNBELNR -> FMIOI.FMBELNR.
  5. Print structured findings.

Usage:
    cd c:/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/mcp-backend-server-python/
    python ../incidents/INC_budget_rate_eq_guinea/audit_kblew_fmioi_consistency.py

Requires VPN + SNC/SSO to P01.
"""

import os
import sys
import json
import traceback
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

FR_NUMBER = '3250117351'
EXPECTED_BR_RATIO = 1.09529
RATIO_TOLERANCE = 0.001
EUR_CURRENCIES = {'EUR'}  # only EUR should use EURX
# Carryforward items flagged in task prompt
CARRYFORWARD_BLPOS = {'00038', '00039', '00040', '00041', '00042', '00043', '00045'}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(SCRIPT_DIR, 'audit_kblew_fmioi_consistency_output.json')


# ─────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────
def get_p01_connection():
    from dotenv import load_dotenv
    from pyrfc import Connection
    env_path = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..',
                                            'mcp-backend-server-python', '.env'))
    load_dotenv(env_path)

    def env(k, d=None):
        return os.getenv(f'SAP_P01_{k}') or os.getenv(f'SAP_{k}') or d

    params = {
        'ashost': '172.16.4.100',
        'sysnr': env('SYSNR', '00'),
        'client': env('CLIENT', '350'),
        'lang': env('LANG', 'EN'),
        'snc_mode': '1',
        'snc_partnername': 'p:CN=P01',
        'snc_qop': env('SNC_QOP', '9'),
        'config': {'rstrip': True},
    }
    if env('SNC_MYNAME'):
        params['snc_myname'] = env('SNC_MYNAME')
    print(f"[conn] Connecting to P01 @ {params['ashost']}...")
    return Connection(**params)


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────
def parse_sap_amount(s):
    if s is None:
        return 0.0
    s = str(s).strip().replace(',', '')
    if not s:
        return 0.0
    if s.endswith('-'):
        return -float(s[:-1])
    try:
        return float(s)
    except ValueError:
        return 0.0


def safe_ratio(num, den):
    if den == 0:
        return None
    return num / den


def read_table(conn, table, where_parts, fields, rowcount=5000):
    """Thin RFC_READ_TABLE wrapper with 72-char option chunking."""
    rfc_fields = [{'FIELDNAME': f} for f in fields]
    options = []
    current = ''
    for i, part in enumerate(where_parts):
        tok = part if i == 0 else 'AND ' + part
        if len(current) + len(tok) + 1 > 72:
            options.append({'TEXT': current})
            current = tok
        else:
            current = (current + ' ' + tok).strip() if current else tok
    if current:
        options.append({'TEXT': current})
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=table,
                  DELIMITER='|', OPTIONS=options, FIELDS=rfc_fields,
                  ROWCOUNT=rowcount)
    out = []
    for row in r['DATA']:
        vals = row['WA'].split('|')
        out.append(dict(zip(fields, [v.strip() for v in vals])))
    return out


# ─────────────────────────────────────────────────────────────────────────
# KBLE/KBLEW extraction via /SAPPSPRO/PD_GM_FMR2_READ_KBLE
# ─────────────────────────────────────────────────────────────────────────
def read_kble_kblew(conn, belnr):
    """
    Call /SAPPSPRO/PD_GM_FMR2_READ_KBLE which handles the KBLE/KBLEW cluster.
    Range LOW='001', HIGH='999' avoids the pyrfc empty-string numeric bug.
    """
    print(f"[kble] Calling /SAPPSPRO/PD_GM_FMR2_READ_KBLE for BELNR={belnr}...")
    t_range_blpos = [{'SIGN': 'I', 'OPTION': 'BT',
                      'LOW': '001', 'HIGH': '999'}]

    result = conn.call(
        '/SAPPSPRO/PD_GM_FMR2_READ_KBLE',
        I_BELNR=belnr,
        T_RANGE_BLPOS=t_range_blpos,
    )
    # The FM returns tables — we don't know the exact parameter names until
    # we see the FM signature; probe common names.
    probe_keys = list(result.keys())
    print(f"[kble] FM returned keys: {probe_keys}")
    return result


# ─────────────────────────────────────────────────────────────────────────
# Main audit
# ─────────────────────────────────────────────────────────────────────────
def run_audit():
    findings = {
        'fr_number': FR_NUMBER,
        'expected_br_ratio': EXPECTED_BR_RATIO,
        'timestamp': datetime.now().isoformat(),
        'kble': None,
        'kblew': None,
        'fmioi': None,
        'cross_correlation': [],
        'errors': [],
    }

    try:
        conn = get_p01_connection()
    except Exception as e:
        msg = f"[FATAL] P01 connection failed: {e}"
        print(msg)
        findings['errors'].append({'phase': 'connect', 'error': str(e),
                                   'traceback': traceback.format_exc()})
        _dump(findings)
        return findings

    # ---------------- KBLE/KBLEW --------------------------------------
    try:
        fm_result = read_kble_kblew(conn, FR_NUMBER)
        # Heuristic: find KBLE and KBLEW tables in result by field inspection
        kble_rows = []
        kblew_rows = []
        for key, val in fm_result.items():
            if not isinstance(val, list) or not val:
                continue
            sample = val[0]
            keys_upper = {k.upper() for k in sample.keys()}
            # KBLEW has CURTP + WRBTR + BLPOS + BPENT
            if {'CURTP', 'WRBTR', 'BLPOS', 'BPENT'}.issubset(keys_upper):
                kblew_rows = val
                print(f"[kble] Identified KBLEW-like table in '{key}' "
                      f"({len(val)} rows)")
            # KBLE has BLPOS + BPENT + RBELNR + RGJAHR (no CURTP)
            elif {'BLPOS', 'BPENT', 'RBELNR'}.issubset(keys_upper) \
                    and 'CURTP' not in keys_upper:
                kble_rows = val
                print(f"[kble] Identified KBLE-like table in '{key}' "
                      f"({len(val)} rows)")

        findings['kble'] = {'row_count': len(kble_rows),
                            'sample': kble_rows[:2]}
        findings['kblew'] = analyze_kblew(kblew_rows)
    except Exception as e:
        msg = f"[ERROR] KBLE/KBLEW read failed: {e}"
        print(msg)
        findings['errors'].append({'phase': 'kble_kblew', 'error': str(e),
                                   'traceback': traceback.format_exc()})
        kble_rows, kblew_rows = [], []

    # ---------------- FMIOI -------------------------------------------
    try:
        fmioi_rows = read_table(
            conn, 'FMIOI',
            [f"REFBN = '{FR_NUMBER}'"],
            ['FIKRS', 'GJAHR', 'FMBELNR', 'FMBUZEI', 'BTART', 'RLDNR',
             'WRTTP', 'TWAER', 'FKBTR', 'TRBTR', 'REFBN', 'REFBZ',
             'PERIO', 'STATS', 'VRGNG', 'FONDS', 'FISTL', 'FIPEX'],
            rowcount=5000,
        )
        print(f"[fmioi] {len(fmioi_rows)} rows for REFBN={FR_NUMBER}")
        findings['fmioi'] = analyze_fmioi(fmioi_rows)
    except Exception as e:
        msg = f"[ERROR] FMIOI read failed: {e}"
        print(msg)
        findings['errors'].append({'phase': 'fmioi', 'error': str(e),
                                   'traceback': traceback.format_exc()})
        fmioi_rows = []

    # ---------------- Cross-correlation -------------------------------
    if kble_rows and fmioi_rows:
        try:
            findings['cross_correlation'] = cross_correlate(
                conn, kble_rows, kblew_rows, fmioi_rows)
        except Exception as e:
            msg = f"[ERROR] cross-correlation failed: {e}"
            print(msg)
            findings['errors'].append({'phase': 'cross_corr',
                                       'error': str(e),
                                       'traceback': traceback.format_exc()})

    try:
        conn.close()
    except Exception:
        pass

    _dump(findings)
    print_summary(findings)
    return findings


# ─────────────────────────────────────────────────────────────────────────
# Analyzers
# ─────────────────────────────────────────────────────────────────────────
def analyze_kblew(rows):
    """Group by (BLPOS, BPENT); compute ratio curtp=10 / curtp=00."""
    by_key = defaultdict(dict)
    by_cur_pair = defaultdict(int)
    for r in rows:
        key = (r.get('BLPOS', ''), r.get('BPENT', ''))
        curtp = r.get('CURTP', '')
        by_key[key][curtp] = r

    pairs = []
    drift_rows = []
    no_curtp10 = []

    for key, curtps in by_key.items():
        r00 = curtps.get('00')
        r10 = curtps.get('10')
        if r00 and r10:
            w00 = parse_sap_amount(r00.get('WRBTR'))
            w10 = parse_sap_amount(r10.get('WRBTR'))
            ratio = safe_ratio(w10, w00)
            waers00 = r00.get('WAERS', '')
            waers10 = r10.get('WAERS', '')
            cur_pair = f"{waers00}->{waers10}"
            by_cur_pair[cur_pair] += 1
            pair_info = {
                'blpos': key[0],
                'bpent': key[1],
                'waers00': waers00,
                'wrbtr00': w00,
                'waers10': waers10,
                'wrbtr10': w10,
                'ratio': ratio,
                'rbelnr': r00.get('RBELNR') or r10.get('RBELNR'),
                'rgjahr': r00.get('RGJAHR') or r10.get('RGJAHR'),
            }
            pairs.append(pair_info)
            # Flag drift only when EUR -> (USD|FM area) conversion expected
            if waers00 in EUR_CURRENCIES and ratio is not None:
                if abs(ratio - EXPECTED_BR_RATIO) > RATIO_TOLERANCE:
                    drift_rows.append(pair_info)
        elif r00 and not r10:
            no_curtp10.append({
                'blpos': key[0], 'bpent': key[1],
                'waers': r00.get('WAERS', ''),
                'wrbtr': parse_sap_amount(r00.get('WRBTR')),
            })

    return {
        'row_count': len(rows),
        'pair_count': len(pairs),
        'pairs_by_currency': dict(by_cur_pair),
        'drift_rows': drift_rows,
        'no_curtp10_rows': no_curtp10,
        'first_3_pairs': pairs[:3],
    }


def analyze_fmioi(rows):
    by_wrttp = defaultdict(list)
    for r in rows:
        by_wrttp[r.get('WRTTP', '')].append(r)

    summary = {}
    drift_rows = []
    carry_forward_rows = []

    for wrttp, wrows in by_wrttp.items():
        total_fkbtr = sum(parse_sap_amount(r.get('FKBTR')) for r in wrows)
        total_trbtr = sum(parse_sap_amount(r.get('TRBTR')) for r in wrows)
        ratio = safe_ratio(total_fkbtr, total_trbtr)
        summary[wrttp] = {
            'count': len(wrows),
            'sum_fkbtr': round(total_fkbtr, 2),
            'sum_trbtr': round(total_trbtr, 2),
            'ratio': ratio,
        }
        # Per-row ratio for EUR rows where WRTTP in (54,51,81,66)
        if wrttp in ('54', '51', '81', '66'):
            for r in wrows:
                twaer = r.get('TWAER', '')
                fk = parse_sap_amount(r.get('FKBTR'))
                tr = parse_sap_amount(r.get('TRBTR'))
                rratio = safe_ratio(fk, tr)
                row_data = {
                    'fmbelnr': r.get('FMBELNR'),
                    'fmbuzei': r.get('FMBUZEI'),
                    'gjahr': r.get('GJAHR'),
                    'wrttp': wrttp,
                    'twaer': twaer,
                    'fkbtr': fk,
                    'trbtr': tr,
                    'ratio': rratio,
                    'refbz': r.get('REFBZ'),
                    'btart': r.get('BTART'),
                    'vrgng': r.get('VRGNG'),
                }
                if r.get('REFBZ', '') in CARRYFORWARD_BLPOS:
                    carry_forward_rows.append(row_data)
                if twaer in EUR_CURRENCIES and rratio is not None:
                    if abs(rratio - EXPECTED_BR_RATIO) > RATIO_TOLERANCE:
                        drift_rows.append(row_data)

    return {
        'row_count': len(rows),
        'by_wrttp': summary,
        'drift_rows': drift_rows,
        'carryforward_rows': carry_forward_rows,
    }


def cross_correlate(conn, kble_rows, kblew_rows, fmioi_rows):
    """
    For each KBLE header, use RBELNR+RGJAHR to find FMIFIIT rows (KNBELNR+
    KNGJAHR) and then match the FMIOI row (FMBELNR = FMIFIIT.FMBELNR) for
    the consumption event. Compare KBLEW curtp=10 wrbtr vs FMIOI.FKBTR.
    """
    # Index KBLEW by (BLPOS, BPENT) curtp=10
    kblew_10 = {}
    for r in kblew_rows:
        if r.get('CURTP') == '10':
            kblew_10[(r.get('BLPOS'), r.get('BPENT'))] = r

    # Index FMIOI by FMBELNR+FMBUZEI
    fmioi_by_fmbelnr = defaultdict(list)
    for r in fmioi_rows:
        fmioi_by_fmbelnr[r.get('FMBELNR')].append(r)

    correlations = []

    # Batch KBLE RBELNR/RGJAHR lookups to FMIFIIT
    needed = set()
    for kr in kble_rows:
        rbelnr = kr.get('RBELNR', '')
        rgjahr = kr.get('RGJAHR', '')
        if rbelnr and rgjahr:
            needed.add((rbelnr, rgjahr))

    fmifiit_index = {}  # (KNBELNR,KNGJAHR) -> list of rows
    for rbelnr, rgjahr in list(needed)[:50]:  # cap to avoid floods
        try:
            rows = read_table(
                conn, 'FMIFIIT',
                [f"KNBELNR = '{rbelnr}'", f"KNGJAHR = '{rgjahr}'"],
                ['FMBELNR', 'FMBUZEI', 'KNBELNR', 'KNGJAHR', 'KNBUZEI',
                 'WRTTP', 'TWAER', 'FKBTR', 'TRBTR', 'GJAHR', 'FONDS'],
                rowcount=500,
            )
            fmifiit_index[(rbelnr, rgjahr)] = rows
        except Exception as e:
            fmifiit_index[(rbelnr, rgjahr)] = []
            print(f"[xcorr] FMIFIIT read failed for {rbelnr}/{rgjahr}: {e}")

    for kr in kble_rows:
        key = (kr.get('BLPOS'), kr.get('BPENT'))
        kblew10 = kblew_10.get(key)
        rbelnr = kr.get('RBELNR', '')
        rgjahr = kr.get('RGJAHR', '')
        kblew10_wrbtr = (parse_sap_amount(kblew10.get('WRBTR'))
                         if kblew10 else None)
        fmifiit_rows = fmifiit_index.get((rbelnr, rgjahr), [])
        # Find the FMIFIIT reduction lines (WRTTP in 51/54/actual)
        fmioi_fkbtr_for_consumption = None
        fmbelnr_matched = None
        for fi in fmifiit_rows:
            fmbelnr = fi.get('FMBELNR')
            if not fmbelnr:
                continue
            matching_fmioi = fmioi_by_fmbelnr.get(fmbelnr, [])
            if matching_fmioi:
                # sum FKBTR of matching FMIOI rows (consumption side)
                fmioi_fkbtr_for_consumption = sum(
                    parse_sap_amount(m.get('FKBTR'))
                    for m in matching_fmioi
                    if m.get('WRTTP') in ('54', '51', '66'))
                fmbelnr_matched = fmbelnr
                break

        delta = None
        if kblew10_wrbtr is not None and \
                fmioi_fkbtr_for_consumption is not None:
            delta = round(kblew10_wrbtr - fmioi_fkbtr_for_consumption, 4)

        correlations.append({
            'blpos': key[0], 'bpent': key[1],
            'rbelnr': rbelnr, 'rgjahr': rgjahr,
            'kblew10_wrbtr': kblew10_wrbtr,
            'fmifiit_hits': len(fmifiit_rows),
            'fmbelnr_matched': fmbelnr_matched,
            'fmioi_consumption_fkbtr': fmioi_fkbtr_for_consumption,
            'delta': delta,
            'mismatch': (delta is not None and abs(delta) > 0.01),
        })

    return correlations


# ─────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────
def _dump(findings):
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(findings, f, indent=2, default=str)
    print(f"[out] Wrote {OUTPUT_JSON}")


def print_summary(f):
    print('\n' + '=' * 72)
    print(f"AUDIT SUMMARY — FR {f['fr_number']}  (BR ratio expected: "
          f"{f['expected_br_ratio']})")
    print('=' * 72)
    if f['errors']:
        print(f"\nERRORS ({len(f['errors'])}):")
        for e in f['errors']:
            print(f"  - [{e['phase']}] {e['error']}")
    kblew = f.get('kblew') or {}
    print(f"\nKBLEW rows: {kblew.get('row_count', 0)}  "
          f"(pairs: {kblew.get('pair_count', 0)})")
    print(f"  By currency pair: {kblew.get('pairs_by_currency', {})}")
    drift = kblew.get('drift_rows', [])
    print(f"  Drift rows (ratio != {EXPECTED_BR_RATIO}, tol "
          f"{RATIO_TOLERANCE}): {len(drift)}")
    for d in drift[:5]:
        print(f"    BLPOS={d['blpos']} BPENT={d['bpent']}  "
              f"{d['waers00']} {d['wrbtr00']} -> {d['waers10']} "
              f"{d['wrbtr10']}  ratio={d['ratio']}")
    no10 = kblew.get('no_curtp10_rows', [])
    if no10:
        print(f"  Rows missing curtp=10: {len(no10)}")
        for n in no10[:5]:
            print(f"    BLPOS={n['blpos']} BPENT={n['bpent']} "
                  f"WAERS={n['waers']} WRBTR={n['wrbtr']}")

    fmioi = f.get('fmioi') or {}
    print(f"\nFMIOI rows: {fmioi.get('row_count', 0)}")
    for wrttp, s in (fmioi.get('by_wrttp') or {}).items():
        print(f"  WRTTP={wrttp}  n={s['count']}  sum_fkbtr={s['sum_fkbtr']}  "
              f"sum_trbtr={s['sum_trbtr']}  ratio={s['ratio']}")
    fdrift = fmioi.get('drift_rows', [])
    print(f"  FMIOI drift rows (EUR rows, ratio != {EXPECTED_BR_RATIO}): "
          f"{len(fdrift)}")
    for d in fdrift[:5]:
        print(f"    FMBELNR={d['fmbelnr']}/{d['fmbuzei']} GJAHR={d['gjahr']} "
              f"WRTTP={d['wrttp']} FKBTR={d['fkbtr']} TRBTR={d['trbtr']} "
              f"ratio={d['ratio']}")
    cf = fmioi.get('carryforward_rows', [])
    print(f"\nCarry-forward rows (BLPOS in {sorted(CARRYFORWARD_BLPOS)}): "
          f"{len(cf)}")
    for d in cf:
        print(f"    FMBELNR={d['fmbelnr']}/{d['fmbuzei']} WRTTP={d['wrttp']} "
              f"REFBZ={d['refbz']} TWAER={d['twaer']} FKBTR={d['fkbtr']} "
              f"TRBTR={d['trbtr']} ratio={d['ratio']}")

    corrs = f.get('cross_correlation') or []
    mismatches = [c for c in corrs if c.get('mismatch')]
    print(f"\nCross-correlation: {len(corrs)} KBLE lines examined, "
          f"{len(mismatches)} mismatches (|delta| > 0.01 USD)")
    for m in mismatches[:5]:
        print(f"    BLPOS={m['blpos']} BPENT={m['bpent']}  "
              f"KBLEW10={m['kblew10_wrbtr']}  FMIOI={m['fmioi_consumption_fkbtr']}  "
              f"delta={m['delta']}")
    print('=' * 72)


if __name__ == '__main__':
    try:
        run_audit()
    except Exception as e:
        print(f"[FATAL] {e}")
        traceback.print_exc()
        sys.exit(1)
