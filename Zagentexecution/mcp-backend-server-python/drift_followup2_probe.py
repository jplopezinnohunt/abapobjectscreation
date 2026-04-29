"""
Follow-up #2:
1. DMEE tree versions — read DMEE_TREE_HEAD unfiltered, Python-side filter for slashes
2. Extract D01 source of FALLBACK CM001 + others — compare line-by-line vs P01
"""
import os, sys, json, hashlib
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

TARGET_TREES = {'/SEPA_CT_UNES', '/CITI/XML/UNESCO/DC_V3_01',
                '/CGI_XML_CT_UNESCO', '/CGI_XML_CT_UNESCO_1'}

CRITICAL_INCLUDES = [
    # Class includes — these are the actual REPOSRC keys
    # Format: classname padded with = to total 20 chars + suffix
    'YCL_IDFI_CGI_DMEE_FALLBACK====CM001',
    'YCL_IDFI_CGI_DMEE_FALLBACK====CCDEF',
    'YCL_IDFI_CGI_DMEE_FALLBACK====CCIMP',
    'YCL_IDFI_CGI_DMEE_FALLBACK====CCMAC',
    'YCL_IDFI_CGI_DMEE_FR==========CM001',
    'YCL_IDFI_CGI_DMEE_UTIL========CM001',
    'YCL_IDFI_CGI_DMEE_UTIL========CM003',
]


def list_dmee_versions(conn):
    """Read DMEE_TREE_HEAD unfiltered, return per-tree versions."""
    rows = rfc_read_paginated(
        conn, 'DMEE_TREE_HEAD',
        ['TREE_ID', 'VERSION', 'EX_STATUS', 'LAST_USER', 'LAST_DATE', 'LAST_TIME'],
        '', batch_size=5000, throttle=0)
    versions = {}
    for r in rows:
        tid = r.get('TREE_ID', '')
        if tid in TARGET_TREES:
            versions.setdefault(tid, []).append({
                'version': r.get('VERSION'),
                'ex_status': r.get('EX_STATUS'),
                'last_user': r.get('LAST_USER'),
                'last_date': r.get('LAST_DATE'),
                'last_time': r.get('LAST_TIME'),
            })
    return versions


def count_nodes_per_version(conn, tree_id, version):
    """Count nodes filtered Python-side after reading all rows for one version."""
    try:
        # Use RFC_READ_TABLE WHERE on VERSION only (no slash issue)
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='DMEE_TREE_NODE',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'TREE_ID'},
                              {'FIELDNAME':'VERSION'},
                              {'FIELDNAME':'NODE_ID'}],
                      OPTIONS=[{'TEXT': f"VERSION EQ '{version}'"}],
                      ROWCOUNT=999999)
        count = sum(1 for row in r['DATA']
                    if row['WA'].split('|')[0].strip() == tree_id)
        return count
    except Exception as e:
        return f'ERROR: {e}'


def extract_source(conn, prog_name):
    """Read source code via RPY_PROGRAM_READ."""
    try:
        r = conn.call('RPY_PROGRAM_READ', PROGRAM_NAME=prog_name,
                      WITH_INCLUDELIST=' ', ONLY_SOURCE='X', WITH_LOWERCASE='X')
        lines = [ln.get('LINE','') for ln in r.get('SOURCE_EXTENDED', [])]
        return '\n'.join(lines), len(lines)
    except Exception as e:
        return None, str(e)


def main():
    print("=== Drift Follow-up #2 ===")
    out_dir = Path('knowledge/domains/Payment/phase0')
    out_dir.mkdir(parents=True, exist_ok=True)
    src_dir = Path('extracted_code/FI/DMEE_d01_for_drift')
    src_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for sysid in ('P01', 'D01'):
        print(f"\n--- {sysid} ---")
        try:
            conn = get_connection(sysid)
        except Exception as e:
            print(f"  Connection failed: {e}")
            continue

        sys_out = {}

        # 1. DMEE versions
        print("  DMEE_TREE_HEAD versions per tree:")
        versions = list_dmee_versions(conn)
        for tree, vlist in versions.items():
            print(f"    {tree}: {len(vlist)} version(s)")
            for v in vlist:
                v['node_count'] = count_nodes_per_version(conn, tree, v['version'])
                print(f"      V{v['version']} status={v['ex_status']} "
                      f"user={v['last_user']} date={v['last_date']} "
                      f"nodes={v['node_count']}")
        sys_out['dmee_versions'] = versions

        # 2. Source of critical includes (D01 only — P01 already extracted)
        if sysid == 'D01':
            print("  Extracting D01 source of critical includes:")
            sys_out['d01_sources'] = {}
            for inc in CRITICAL_INCLUDES:
                print(f"    {inc}")
                src, line_count = extract_source(conn, inc)
                if src is not None:
                    sys_out['d01_sources'][inc] = {
                        'lines': line_count,
                        'sha256': hashlib.sha256(src.encode()).hexdigest(),
                    }
                    out_path = src_dir / f'{inc}.abap'
                    out_path.write_text(src, encoding='utf-8')
                else:
                    sys_out['d01_sources'][inc] = {'error': str(line_count)}

        results[sysid] = sys_out
        conn.close()

    # Save raw + write markdown report
    with open(out_dir / 'drift_followup2_raw.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    md = ['# Drift Follow-up #2 — DMEE versions + D01 source diff\n',
          f'**Generated**: {datetime.now().isoformat()}\n']

    md.append('\n## DMEE tree versions per system\n')
    for sysid in ('P01', 'D01'):
        md.append(f'\n### {sysid}\n')
        versions = results.get(sysid, {}).get('dmee_versions', {})
        for tree in sorted(TARGET_TREES):
            vlist = versions.get(tree, [])
            md.append(f'\n**{tree}** — {len(vlist)} version(s)\n')
            md.append('\n| Version | Status | Last user | Last date | Last time | Nodes |\n')
            md.append('|---|---|---|---|---|---|\n')
            for v in vlist:
                md.append(f"| {v.get('version')} | {v.get('ex_status')} | "
                          f"{v.get('last_user')} | {v.get('last_date')} | "
                          f"{v.get('last_time')} | {v.get('node_count')} |\n")

    md.append('\n## D01 source for critical includes (extracted)\n')
    md.append('\nFiles written to `extracted_code/FI/DMEE_d01_for_drift/`. '
              'Compare to `extracted_code/FI/DMEE/` (P01) line by line.\n\n')
    md.append('| Include | D01 lines | D01 sha256 (first 16) | P01 file | Diff cmd |\n')
    md.append('|---|---|---|---|---|\n')
    d01_srcs = results.get('D01', {}).get('d01_sources', {})
    for inc in CRITICAL_INCLUDES:
        info = d01_srcs.get(inc, {})
        if 'error' in info:
            md.append(f'| `{inc}` | ❌ {info["error"]} | - | - | - |\n')
        else:
            sha_short = info.get('sha256','')[:16]
            p01_file = f'extracted_code/FI/DMEE/{inc}.abap'
            md.append(f'| `{inc}` | {info.get("lines")} | `{sha_short}` | '
                      f'`{p01_file}` | `diff extracted_code/FI/DMEE/{inc}.abap '
                      f'extracted_code/FI/DMEE_d01_for_drift/{inc}.abap` |\n')

    md_path = out_dir / 'd01_vs_p01_drift_followup2.md'
    md_path.write_text(''.join(md), encoding='utf-8')
    print(f"\nReport: {md_path}")


if __name__ == '__main__':
    main()
