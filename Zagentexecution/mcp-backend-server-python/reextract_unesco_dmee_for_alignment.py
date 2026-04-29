"""
Re-extract ALL UNESCO custom DMEE source from P01 + D01 cleanly.

Goal: produce a complete retrofit base anchored on P01. Every UNESCO
custom DMEE include extracted full-fidelity (no 80-char truncation),
so D01 retrofit transport is aligned 1:1 with P01.

Output:
- extracted_code/FI/DMEE_p01_canonical/<INCLUDE>.abap — P01 canonical
- extracted_code/FI/DMEE_d01_state/<INCLUDE>.abap — D01 current state
- knowledge/domains/Payment/phase0/retrofit_diff_matrix.md — per-include diff verdict
"""
import os, sys, json, hashlib, difflib
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

CLASSES = [
    'YCL_IDFI_CGI_DMEE_FALLBACK',
    'YCL_IDFI_CGI_DMEE_FR',
    'YCL_IDFI_CGI_DMEE_UTIL',
    'YCL_IDFI_CGI_DMEE_DE',
    'YCL_IDFI_CGI_DMEE_IT',
]
ENHO_NAMES = [
    'YENH_FI_DMEE_CGI_FALLBACK',
    'Y_IDFI_CGI_DMEE_COUNTRY_FR',
    'Y_IDFI_CGI_DMEE_COUNTRIES_DE',
    'Y_IDFI_CGI_DMEE_COUNTRIES_FR',
    'Y_IDFI_CGI_DMEE_COUNTRIES_IT',
]
Z_UTILS = [
    'ZDMEE_EXIT_SEPA_21',
    'Z_DMEE_EXIT_TAX_NUMBER',
]


def list_class_includes(conn, class_name):
    """REPOSRC LIKE class_name% returns all sub-includes."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='REPOSRC',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'PROGNAME'},
                              {'FIELDNAME':'UNAM'},
                              {'FIELDNAME':'UDAT'},
                              {'FIELDNAME':'UTIME'}],
                      OPTIONS=[{'TEXT': f"PROGNAME LIKE '{class_name}%'"}])
        rows = []
        for row in r['DATA']:
            f = row['WA'].split('|')
            rows.append({
                'progname': f[0].strip(), 'unam': f[1].strip(),
                'udat': f[2].strip(), 'utime': f[3].strip(),
            })
        return rows
    except Exception as e:
        print(f"    list_class_includes ERROR for {class_name}: {e}")
        return []


def extract_source(conn, prog_name):
    """Read source via RPY_PROGRAM_READ with SOURCE_EXTENDED (255-char lines)."""
    try:
        r = conn.call('RPY_PROGRAM_READ',
                      PROGRAM_NAME=prog_name,
                      WITH_INCLUDELIST=' ',
                      ONLY_SOURCE='X',
                      WITH_LOWERCASE='X')
        lines = [ln.get('LINE', '') for ln in r.get('SOURCE_EXTENDED', [])]
        return '\n'.join(lines)
    except Exception as e:
        return f'EXTRACT_ERROR: {e}'


def normalize_for_diff(text):
    """Strip leading/trailing whitespace per line, collapse blank-line runs."""
    lines = []
    prev_blank = False
    for ln in text.splitlines():
        s = ln.rstrip()
        is_blank = not s.strip()
        if is_blank and prev_blank:
            continue
        lines.append(s)
        prev_blank = is_blank
    return '\n'.join(lines)


def main():
    print("=== Re-extract UNESCO DMEE for D01-P01 alignment ===")
    print(f"Started: {datetime.now().isoformat()}")

    p01_dir = Path('extracted_code/FI/DMEE_p01_canonical')
    d01_dir = Path('extracted_code/FI/DMEE_d01_state')
    out_dir = Path('knowledge/domains/Payment/phase0')
    p01_dir.mkdir(parents=True, exist_ok=True)
    d01_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: enumerate all class includes that exist in EITHER system
    print("\n--- Enumerating class includes ---")
    p01_conn = get_connection('P01')
    d01_conn = get_connection('D01')

    include_metadata = {}  # include_name -> {p01_meta, d01_meta}
    for cls in CLASSES:
        print(f"  {cls}")
        for sysid, conn in (('p01', p01_conn), ('d01', d01_conn)):
            for row in list_class_includes(conn, cls):
                inc = row['progname']
                if inc not in include_metadata:
                    include_metadata[inc] = {}
                include_metadata[inc][sysid] = row
        # Also enumerate Z* utilities
    for z in Z_UTILS:
        print(f"  {z}")
        for sysid, conn in (('p01', p01_conn), ('d01', d01_conn)):
            for row in list_class_includes(conn, z):
                inc = row['progname']
                if inc not in include_metadata:
                    include_metadata[inc] = {}
                include_metadata[inc][sysid] = row

    print(f"\n  Total unique includes across systems: {len(include_metadata)}")

    # Step 2: extract source for each include from each system where it exists
    print("\n--- Extracting source ---")
    diff_results = []
    for inc, meta in sorted(include_metadata.items()):
        p_meta = meta.get('p01')
        d_meta = meta.get('d01')

        p_src = None
        d_src = None
        if p_meta:
            p_src = extract_source(p01_conn, inc)
            (p01_dir / f'{inc}.abap').write_text(p_src, encoding='utf-8')
        if d_meta:
            d_src = extract_source(d01_conn, inc)
            (d01_dir / f'{inc}.abap').write_text(d_src, encoding='utf-8')

        # Classify
        if p_meta and not d_meta:
            verdict = 'P01_ONLY'
            severity = 'CRITICAL'
            detail = 'Must retrofit to D01 from P01'
        elif d_meta and not p_meta:
            verdict = 'D01_ONLY'
            severity = 'CRITICAL'
            detail = 'Possible WIP — review with N_MENARD before deciding'
        else:
            # Both exist — compute diff
            if p_src is None or d_src is None:
                verdict = 'EXTRACT_FAILED'
                severity = 'HIGH'
                detail = f"P01 src: {'OK' if p_src else 'fail'} | D01 src: {'OK' if d_src else 'fail'}"
            elif p_src == d_src:
                verdict = 'IDENTICAL'
                severity = 'NONE'
                detail = 'Byte-by-byte equal'
            elif normalize_for_diff(p_src) == normalize_for_diff(d_src):
                verdict = 'COSMETIC_ONLY'
                severity = 'LOW'
                detail = 'Only blank lines / trailing whitespace differ'
            else:
                # Real semantic diff
                p_norm = normalize_for_diff(p_src).splitlines()
                d_norm = normalize_for_diff(d_src).splitlines()
                differ_lines = sum(1 for tag, _, _ in
                                   difflib.SequenceMatcher(None, p_norm, d_norm).get_opcodes()
                                   if tag != 'equal')
                verdict = 'FUNCTIONAL_DIFF'
                severity = 'HIGH'
                detail = f'{differ_lines} block(s) differ semantically — retrofit P01→D01'

        result = {
            'include': inc,
            'p01_unam': p_meta.get('unam') if p_meta else None,
            'p01_udat': p_meta.get('udat') if p_meta else None,
            'd01_unam': d_meta.get('unam') if d_meta else None,
            'd01_udat': d_meta.get('udat') if d_meta else None,
            'verdict': verdict,
            'severity': severity,
            'detail': detail,
            'p01_lines': len(p_src.splitlines()) if p_src else 0,
            'd01_lines': len(d_src.splitlines()) if d_src else 0,
        }
        diff_results.append(result)
        print(f"  {inc:50s} {verdict:18s} {severity:8s}")

    # Save raw + write report
    with open(out_dir / 'retrofit_diff_raw.json', 'w', encoding='utf-8') as f:
        json.dump(diff_results, f, indent=2, ensure_ascii=False)

    # Markdown report
    md = ['# Retrofit Diff Matrix — D01 alignment to P01 base\n',
          f'**Generated**: {datetime.now().isoformat()}\n',
          f'**Total includes analyzed**: {len(diff_results)}\n\n',
          '## Goal\n\n',
          'Establish P01 as the **canonical base** for UNESCO custom DMEE code, '
          'and produce the exact retrofit list to align D01.\n\n',
          'Once D01 = P01 across all UNESCO custom code, we can safely apply '
          'the Pattern A fix and create V001 trees without risk of clobbering.\n\n']

    by_severity = {}
    for r in diff_results:
        by_severity.setdefault(r['severity'], []).append(r)

    for sev in ('CRITICAL', 'HIGH', 'LOW', 'NONE'):
        items = by_severity.get(sev, [])
        md.append(f'## {sev} ({len(items)})\n\n')
        if not items:
            md.append('_None._\n\n')
            continue
        md.append('| Include | Verdict | P01 (date) | D01 (date) | Detail |\n')
        md.append('|---|---|---|---|---|\n')
        for r in sorted(items, key=lambda x: x['include']):
            md.append(f"| `{r['include']}` | {r['verdict']} | "
                      f"{r['p01_udat'] or '-'} | {r['d01_udat'] or '-'} | "
                      f"{r['detail']} |\n")
        md.append('\n')

    md.append('## Retrofit transport scope (D01-RETROFIT-01)\n\n')
    must_retrofit = [r for r in diff_results
                     if r['severity'] in ('CRITICAL', 'HIGH')
                     and r['verdict'] in ('P01_ONLY', 'FUNCTIONAL_DIFF')]
    md.append(f'**{len(must_retrofit)} includes need retrofit**:\n\n')
    for r in must_retrofit:
        md.append(f"- `{r['include']}` — {r['verdict']}\n")

    must_review = [r for r in diff_results
                   if r['verdict'] == 'D01_ONLY']
    md.append(f'\n**{len(must_review)} D01-only includes — need N_MENARD review**:\n\n')
    for r in must_review:
        md.append(f"- `{r['include']}` — D01 has it, P01 doesn't. WIP?\n")

    safe_to_skip = [r for r in diff_results
                    if r['verdict'] in ('IDENTICAL', 'COSMETIC_ONLY')]
    md.append(f'\n**{len(safe_to_skip)} includes safe to skip retrofit** '
              f'(byte-equal or cosmetic blanks-only)\n')

    md_path = out_dir / 'retrofit_diff_matrix.md'
    md_path.write_text(''.join(md), encoding='utf-8')
    print(f"\nReport: {md_path}")
    print(f"P01 canonical: {p01_dir}")
    print(f"D01 state:     {d01_dir}")

    p01_conn.close()
    d01_conn.close()


if __name__ == '__main__':
    main()
