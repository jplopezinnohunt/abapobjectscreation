"""
Follow-up probes after first drift detector run revealed:
1. FM_MISSING (10 items) — false positives, need TFDIR-based probe
2. DMEE tree 2x nodes in D01 — need to list versions per tree
3. TFPM042FB / T042Z extra rows in D01 — identify which 5 / 3 rows differ
4. DMEE_TREE_NODE / COND DATA_BUFFER_EXCEEDED — re-probe with field-split

Output: knowledge/domains/Payment/phase0/d01_vs_p01_drift_followup.md
"""
import os, sys, json
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

TARGET_FMS = [
    'FI_PAYMEDIUM_DMEE_CGI_05',
    '/CITIPMW/V3_PAYMEDIUM_DMEE_05',
    '/CITIPMW/V3_CGI_CRED_STREET',
    '/CITIPMW/V3_CGI_CRED_PO_CITY',
    '/CITIPMW/V3_CGI_CRED_REGION',
    '/CITIPMW/V3_EXIT_CGI_CRED_NAME',
    '/CITIPMW/V3_EXIT_CGI_CRED_NM2',
    '/CITIPMW/V3_EXIT_CGI_CRED_CITY',
    '/CITIPMW/V3_GET_BANKCODE',
    '/CITIPMW/V3_GET_CDTR_BLDG',
]

TARGET_TREES = [
    '/SEPA_CT_UNES',
    '/CITI/XML/UNESCO/DC_V3_01',
    '/CGI_XML_CT_UNESCO',
    '/CGI_XML_CT_UNESCO_1',
]


def probe_fm_via_tfdir(conn, fm_name):
    """Verify FM existence + last-changed via TFDIR -> include -> REPOSRC."""
    # 1. TFDIR holds funcname -> include LX...U... mapping
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='TFDIR',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'FUNCNAME'},
                              {'FIELDNAME':'PNAME'},
                              {'FIELDNAME':'INCLUDE'},
                              {'FIELDNAME':'FMODE'}],
                      OPTIONS=[{'TEXT': f"FUNCNAME EQ '{fm_name}'"}])
        if not r['DATA']:
            return {'exists': False, 'reason': 'not in TFDIR'}
        f = r['DATA'][0]['WA'].split('|')
        funcgroup = f[1].strip()  # PNAME like 'SAPLZxxxx' or '/CITIPMW/SAPLPMWV3U31'
        include_no = f[2].strip()  # numeric include number
        # 2. The actual include holding source = funcgroup + 'U' + include_no
        # For SAPL<group> the source include is L<group>U<no>
        # For /NS/SAPL<group> the source include is /NS/L<group>U<no>
        if funcgroup.startswith('/'):
            ns_end = funcgroup.find('/', 1) + 1
            ns = funcgroup[:ns_end]
            grp_clean = funcgroup[ns_end:].replace('SAPL', '', 1)
            inc_name = f"{ns}L{grp_clean}U{include_no.zfill(2)}"
        else:
            grp_clean = funcgroup.replace('SAPL', '', 1)
            inc_name = f"L{grp_clean}U{include_no.zfill(2)}"
        # 3. REPOSRC for that include
        r2 = conn.call('RFC_READ_TABLE', QUERY_TABLE='REPOSRC',
                       DELIMITER='|',
                       FIELDS=[{'FIELDNAME':'PROGNAME'},
                               {'FIELDNAME':'UNAM'},
                               {'FIELDNAME':'UDAT'},
                               {'FIELDNAME':'UTIME'}],
                       OPTIONS=[{'TEXT': f"PROGNAME EQ '{inc_name}'"}])
        if r2['DATA']:
            ff = r2['DATA'][0]['WA'].split('|')
            return {'exists': True, 'fm_name': fm_name, 'include': inc_name,
                    'funcgroup': funcgroup,
                    'last_user': ff[1].strip(),
                    'last_date': ff[2].strip(),
                    'last_time': ff[3].strip()}
        return {'exists': True, 'fm_name': fm_name, 'include': inc_name,
                'funcgroup': funcgroup,
                'note': 'TFDIR found but REPOSRC empty (try other include nos)'}
    except Exception as e:
        return {'exists': None, 'error': str(e)}


def probe_dmee_tree_versions(conn, tree_id):
    """List ALL versions of a DMEE tree with status, date, user, node count."""
    out = {'tree_id': tree_id, 'versions': []}
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='DMEE_TREE_HEAD',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'TREE_ID'},
                              {'FIELDNAME':'VERSION'},
                              {'FIELDNAME':'EX_STATUS'},
                              {'FIELDNAME':'LAST_USER'},
                              {'FIELDNAME':'LAST_DATE'},
                              {'FIELDNAME':'LAST_TIME'}],
                      OPTIONS=[{'TEXT': f"TREE_ID EQ '{tree_id}'"}])
        for row in r['DATA']:
            f = row['WA'].split('|')
            ver = {'version': f[1].strip(), 'ex_status': f[2].strip(),
                   'last_user': f[3].strip(), 'last_date': f[4].strip(),
                   'last_time': f[5].strip()}
            # Count nodes per version
            try:
                rn = conn.call('RFC_READ_TABLE', QUERY_TABLE='DMEE_TREE_NODE',
                               DELIMITER='|',
                               FIELDS=[{'FIELDNAME':'NODE_ID'}],
                               OPTIONS=[{'TEXT':
                                   f"TREE_ID EQ '{tree_id}' AND VERSION EQ '{ver['version']}'"}],
                               ROWCOUNT=99999)
                ver['node_count'] = len(rn['DATA'])
            except Exception as e:
                ver['node_count_error'] = str(e)
            out['versions'].append(ver)
    except Exception as e:
        out['error'] = str(e)
    return out


def probe_tfpm042fb_full(conn):
    """Read every row of TFPM042FB to identify D01-only rows."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='TFPM042FB',
                      DELIMITER='|',
                      OPTIONS=[], ROWCOUNT=99999)
        fields = [f['FIELDNAME'] for f in r['FIELDS']]
        rows = []
        for row in r['DATA']:
            vals = row['WA'].split('|')
            rows.append(dict(zip(fields, [v.strip() for v in vals])))
        return {'fields': fields, 'rows': rows}
    except Exception as e:
        return {'error': str(e)}


def probe_t042z_full(conn):
    """Read every row of T042Z to identify D01-only rows."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='T042Z',
                      DELIMITER='|',
                      OPTIONS=[], ROWCOUNT=99999)
        fields = [f['FIELDNAME'] for f in r['FIELDS']]
        rows = []
        for row in r['DATA']:
            vals = row['WA'].split('|')
            rows.append(dict(zip(fields, [v.strip() for v in vals])))
        return {'fields': fields, 'rows': rows}
    except Exception as e:
        return {'error': str(e)}


def main():
    print("=== Drift Follow-up Probe ===")
    out_dir = Path('knowledge/domains/Payment/phase0')
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for sysid in ('P01', 'D01'):
        print(f"\n--- {sysid} ---")
        try:
            conn = get_connection(sysid)
        except Exception as e:
            print(f"  Connection failed: {e}")
            continue

        sys_out = {'fms': {}, 'trees': {}}

        print("  FMs via TFDIR:")
        for fm in TARGET_FMS:
            print(f"    {fm}")
            sys_out['fms'][fm] = probe_fm_via_tfdir(conn, fm)

        print("  DMEE tree versions:")
        for tree in TARGET_TREES:
            print(f"    {tree}")
            sys_out['trees'][tree] = probe_dmee_tree_versions(conn, tree)

        print("  TFPM042FB full:")
        sys_out['tfpm042fb'] = probe_tfpm042fb_full(conn)

        print("  T042Z full:")
        sys_out['t042z'] = probe_t042z_full(conn)

        results[sysid] = sys_out
        conn.close()

    # Save raw
    with open(out_dir / 'drift_followup_raw.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw saved.")

    # Diff analysis
    md = ['# Drift Follow-up Report\n',
          f'**Generated**: {datetime.now().isoformat()}\n']

    p = results.get('P01', {})
    d = results.get('D01', {})

    # Section 1: FMs
    md.append('## 1. Function modules — TFDIR-based verification\n')
    md.append('Replaces the false-positive "FM_MISSING" findings from initial drift run.\n')
    md.append('\n| FM | P01 exists? | P01 last change | D01 exists? | D01 last change | Verdict |\n')
    md.append('|---|---|---|---|---|---|\n')
    for fm in TARGET_FMS:
        pf = p.get('fms', {}).get(fm, {})
        df = d.get('fms', {}).get(fm, {})
        p_ex = '✅' if pf.get('exists') else ('❌' if pf.get('exists') is False else '?')
        d_ex = '✅' if df.get('exists') else ('❌' if df.get('exists') is False else '?')
        p_chg = f"{pf.get('last_date','')} {pf.get('last_time','')} {pf.get('last_user','')}".strip()
        d_chg = f"{df.get('last_date','')} {df.get('last_time','')} {df.get('last_user','')}".strip()
        if pf.get('exists') and not df.get('exists'):
            verdict = '🔴 D01-MISSING'
        elif pf.get('exists') and df.get('exists'):
            if p_chg != d_chg:
                verdict = '🟡 DRIFT'
            else:
                verdict = '🟢 IN SYNC'
        else:
            verdict = '⚪ INCONCLUSIVE'
        md.append(f'| `{fm}` | {p_ex} | {p_chg or "-"} | {d_ex} | {d_chg or "-"} | {verdict} |\n')

    # Section 2: DMEE tree versions
    md.append('\n## 2. DMEE tree versions (the 2x node count mystery)\n')
    for tree in TARGET_TREES:
        md.append(f'\n### {tree}\n')
        pt = p.get('trees', {}).get(tree, {}).get('versions', [])
        dt = d.get('trees', {}).get(tree, {}).get('versions', [])
        md.append('| System | Version | Status | Last user | Last date | Node count |\n')
        md.append('|---|---|---|---|---|---|\n')
        for v in pt:
            md.append(f"| P01 | {v.get('version','')} | {v.get('ex_status','')} | "
                      f"{v.get('last_user','')} | {v.get('last_date','')} | "
                      f"{v.get('node_count','?')} |\n")
        for v in dt:
            md.append(f"| D01 | {v.get('version','')} | {v.get('ex_status','')} | "
                      f"{v.get('last_user','')} | {v.get('last_date','')} | "
                      f"{v.get('node_count','?')} |\n")

    # Section 3: TFPM042FB diff
    md.append('\n## 3. TFPM042FB rows — identify D01-only rows\n')
    p_rows = p.get('tfpm042fb', {}).get('rows', [])
    d_rows = d.get('tfpm042fb', {}).get('rows', [])
    p_set = {json.dumps(r, sort_keys=True) for r in p_rows}
    d_set = {json.dumps(r, sort_keys=True) for r in d_rows}
    only_d = [json.loads(s) for s in (d_set - p_set)]
    only_p = [json.loads(s) for s in (p_set - d_set)]
    md.append(f'**P01**: {len(p_rows)} rows · **D01**: {len(d_rows)} rows\n')
    md.append(f'**Only in D01**: {len(only_d)} rows · **Only in P01**: {len(only_p)} rows\n')
    if only_d:
        md.append('\n### Rows only in D01 (possible WIP)\n```json\n')
        md.append(json.dumps(only_d, indent=2, ensure_ascii=False))
        md.append('\n```\n')
    if only_p:
        md.append('\n### Rows only in P01\n```json\n')
        md.append(json.dumps(only_p, indent=2, ensure_ascii=False))
        md.append('\n```\n')

    # Section 4: T042Z diff
    md.append('\n## 4. T042Z rows — identify D01-only rows\n')
    p_rows = p.get('t042z', {}).get('rows', [])
    d_rows = d.get('t042z', {}).get('rows', [])
    p_set = {json.dumps(r, sort_keys=True) for r in p_rows}
    d_set = {json.dumps(r, sort_keys=True) for r in d_rows}
    only_d = [json.loads(s) for s in (d_set - p_set)]
    only_p = [json.loads(s) for s in (p_set - d_set)]
    md.append(f'**P01**: {len(p_rows)} rows · **D01**: {len(d_rows)} rows\n')
    md.append(f'**Only in D01**: {len(only_d)} rows · **Only in P01**: {len(only_p)} rows\n')
    if only_d:
        md.append('\n### Rows only in D01 (possible WIP)\n```json\n')
        md.append(json.dumps(only_d, indent=2, ensure_ascii=False))
        md.append('\n```\n')
    if only_p:
        md.append('\n### Rows only in P01\n```json\n')
        md.append(json.dumps(only_p, indent=2, ensure_ascii=False))
        md.append('\n```\n')

    md_path = out_dir / 'd01_vs_p01_drift_followup.md'
    md_path.write_text(''.join(md), encoding='utf-8')
    print(f"Report: {md_path}")


if __name__ == '__main__':
    main()
