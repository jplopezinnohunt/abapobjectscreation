"""
D01 vs P01 drift detector for BCM Structured Address project.

Compares CHANGED_ON / CHANGED_BY / source-hash for every object we extracted
or plan to touch in Phase 2. Detects content drift even when both systems
have the object (TADIR-level inventory says BOTH but version may differ).

Why this matters: my Phase 2 design (Pattern A fix at FALLBACK_CM001:13-31)
is anchored on P01 source. If D01 has a different version (e.g., older
without the overflow logic, or newer with someone's WIP), the line numbers
won't match and the fix may collide with unseen code.

Output:
- knowledge/domains/Payment/phase0/d01_vs_p01_drift_report.md
- knowledge/domains/Payment/phase0/d01_vs_p01_drift_data.json
"""
import os, sys, json, hashlib
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

# Comparison scope = "everything that could have been maintained directly
# in P01 without flowing back through D01". Categories cover both
# specifically-targeted objects and dynamic enumeration to catch unknowns.
#
# 1. UNESCO custom Y* classes (drift very possible — 9 N_MENARD transports 2024)
# 2. UNESCO custom ENHO impls (drift possible)
# 3. UNESCO custom Z* utilities (payment-related)
# 4. SAP-std country dispatcher (drift unlikely but verify — patches?)
# 5. SAP-std FI_PAYMEDIUM_DMEE_CGI_05 (drift unlikely but verify)
# 6. CITIPMW industry solution (verify — proveedor patches possible)
# 7. DMEE trees (drift CONFIRMED via H18 — CGI has 2x nodes in D01)
# 8. Customizing tables — full content compare, not row count
# 9. DYNAMIC enumeration — TADIR scan per package/namespace catches unknowns
OBJECTS_TO_CHECK = {
    'unesco_classes': [
        'YCL_IDFI_CGI_DMEE_FALLBACK',
        'YCL_IDFI_CGI_DMEE_FR',
        'YCL_IDFI_CGI_DMEE_UTIL',
        'YCL_IDFI_CGI_DMEE_DE',  # P01-only per Finding I
        'YCL_IDFI_CGI_DMEE_IT',  # P01-only per Finding I
    ],
    'unesco_enho': [
        'YENH_FI_DMEE_CGI_FALLBACK',
        'Y_IDFI_CGI_DMEE_COUNTRY_FR',
        'Y_IDFI_CGI_DMEE_COUNTRIES_DE',  # P01-only
        'Y_IDFI_CGI_DMEE_COUNTRIES_FR',  # P01-only
        'Y_IDFI_CGI_DMEE_COUNTRIES_IT',  # P01-only
    ],
    'unesco_z_utils': [
        'ZDMEE_EXIT_SEPA_21',
        'Z_DMEE_EXIT_TAX_NUMBER',
    ],
    'sap_std_classes': [
        'CL_IDFI_CGI_CALL05_FACTORY',
        'CL_IDFI_CGI_CALL05_GENERIC',
        'CL_IDFI_CGI_CALL05_FR',
        'CL_IDFI_CGI_CALL05_DE',
        'CL_IDFI_CGI_CALL05_IT',
        'CL_IDFI_CGI_CALL05_GB',
    ],
    'sap_std_fms': [
        'FI_PAYMEDIUM_DMEE_CGI_05',
    ],
    'citipmw_fms': [
        '/CITIPMW/V3_PAYMEDIUM_DMEE_05',
        '/CITIPMW/V3_CGI_CRED_STREET',
        '/CITIPMW/V3_CGI_CRED_PO_CITY',
        '/CITIPMW/V3_CGI_CRED_REGION',
        '/CITIPMW/V3_EXIT_CGI_CRED_NAME',
        '/CITIPMW/V3_EXIT_CGI_CRED_NM2',
        '/CITIPMW/V3_EXIT_CGI_CRED_CITY',
        '/CITIPMW/V3_GET_BANKCODE',
        '/CITIPMW/V3_GET_CDTR_BLDG',
    ],
    'dmee_trees': [
        '/SEPA_CT_UNES',
        '/CITI/XML/UNESCO/DC_V3_01',
        '/CGI_XML_CT_UNESCO',
        '/CGI_XML_CT_UNESCO_1',
    ],
    # Full-content compare (every row diffed, not just count)
    'customizing_full_diff': [
        ('TFPM042FB', ''),                 # OBPM4 Event 05 registrations
        ('T042Z',     ''),                 # PMW format → DMEE tree
        ('T042E',     ''),                 # country-currency → format
        ('T042I',     ''),                 # IBAN config
        ('T042D',     ''),                 # paying co code config
        ('T042B',     ''),                 # PMW format header
        ('TFIBLMPAYBLOCK', ''),            # BCM routing rule (Claim #65)
        ('T012',      ''),                 # House banks
        ('T012K',     ''),                 # House bank accounts
        ('T012T',     ''),                 # House bank texts
        ('TBKK1',     ''),                 # Bank chains
        ('DMEE_TREE_HEAD', ''),            # All DMEE trees header
        ('DMEE_TREE_NODE', ''),            # All DMEE nodes
        ('DMEE_TREE_COND', ''),            # All DMEE conditions
        ('DMEE_TREE_SORT', ''),            # All DMEE sort rules
    ],
    # Dynamic enumeration — catches unknown objects we haven't named yet.
    # For each (object_type, name_pattern, devclass_pattern), TADIR scan
    # both systems and compare the full set.
    'dynamic_tadir_scans': [
        ('CLAS', 'YCL_IDFI%',  ''),        # all Y FI custom classes
        ('CLAS', 'YCL_%DMEE%', ''),        # all Y DMEE classes broad
        ('CLAS', 'ZCL_FI%',    ''),        # any Z FI classes
        ('CLAS', '/CITIPMW/%', ''),        # all CITIPMW classes
        ('FUGR', '/CITIPMW/%', ''),        # all CITIPMW funcgroups
        ('FUNC', '/CITIPMW/%', ''),        # all CITIPMW FMs
        ('FUNC', 'Y_FPAY%',    ''),        # any Y payment FMs
        ('FUNC', 'Z_FPAY%',    ''),        # any Z payment FMs
        ('FUNC', 'Y_DMEE%',    ''),        # any Y DMEE FMs
        ('FUNC', 'Z_DMEE%',    ''),        # any Z DMEE FMs
        ('PROG', 'Y%',          'YA'),     # all Y programs in YA package
        ('PROG', 'Z%',          'YA'),     # all Z programs in YA package
        ('PROG', 'YRGGB%',     ''),        # substitution exit programs
        ('PROG', 'ZRGGB%',     ''),        # substitution exit programs
        ('ENHO', 'Y%',          ''),       # all Y enhancement impls
        ('ENHO', 'Z%',          ''),       # all Z enhancement impls
        ('XSLT', 'CGI%',       ''),        # CGI XSLT (verify SAP std drift)
        ('XSLT', 'Y%',          ''),       # any custom XSLT
        ('XSLT', 'Z%',          ''),       # any custom XSLT
        ('TABL', 'YT%',         'YA'),     # custom tables in YA
    ],
}


def hash_source(lines):
    """Stable hash of source lines, ignoring comments + whitespace."""
    norm = []
    for ln in lines:
        s = ln.split('"', 1)[0].rstrip()  # strip ABAP comments
        s = ' '.join(s.split())            # normalize whitespace
        if s:
            norm.append(s.upper())
        return hashlib.sha256('\n'.join(norm).encode()).hexdigest()


def get_repo_meta(conn, prog_name):
    """REPOSRC metadata: UNAM (last user), UDAT, UTIME, UTASK."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='REPOSRC',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'PROGNAME'},
                              {'FIELDNAME':'UNAM'},
                              {'FIELDNAME':'UDAT'},
                              {'FIELDNAME':'UTIME'},
                              {'FIELDNAME':'CNAM'},
                              {'FIELDNAME':'CDAT'}],
                      OPTIONS=[{'TEXT': f"PROGNAME EQ '{prog_name}'"}])
        if r['DATA']:
            f = r['DATA'][0]['WA'].split('|')
            return {'progname': f[0].strip(), 'unam': f[1].strip(),
                    'udat': f[2].strip(), 'utime': f[3].strip(),
                    'cnam': f[4].strip(), 'cdat': f[5].strip()}
    except Exception as e:
        return {'error': str(e)}
    return None


def get_class_includes(conn, class_name):
    """For a class, list all sub-includes (CCDEF/CCIMP/CCMAC/CM001/etc.)."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='REPOSRC',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'PROGNAME'}],
                      OPTIONS=[{'TEXT': f"PROGNAME LIKE '{class_name}%'"}])
        return [row['WA'].split('|')[0].strip() for row in r['DATA']]
    except Exception:
        return []


def get_dmee_tree_meta(conn, tree_id):
    """DMEE_TREE_HEAD: CHANGED_ON, CHANGED_BY + node count from DMEE_TREE_NODE."""
    out = {'tree_id': tree_id}
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
        out['head_rows'] = []
        for row in r['DATA']:
            f = row['WA'].split('|')
            out['head_rows'].append({
                'tree_id': f[0].strip(), 'version': f[1].strip(),
                'ex_status': f[2].strip(), 'last_user': f[3].strip(),
                'last_date': f[4].strip(), 'last_time': f[5].strip()
            })
    except Exception as e:
        out['head_error'] = str(e)
    try:
        r2 = conn.call('RFC_READ_TABLE', QUERY_TABLE='DMEE_TREE_NODE',
                       DELIMITER='|',
                       FIELDS=[{'FIELDNAME':'NODE_ID'}],
                       OPTIONS=[{'TEXT': f"TREE_ID EQ '{tree_id}'"}],
                       ROWCOUNT=99999)
        out['node_count'] = len(r2['DATA'])
    except Exception as e:
        out['node_error'] = str(e)
    return out


def get_table_row_count(conn, table_name, where=''):
    """Generic row count for customizing tables."""
    try:
        opts = [{'TEXT': where}] if where else []
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE=table_name,
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'MANDT'}],
                      OPTIONS=opts, ROWCOUNT=99999)
        return len(r['DATA'])
    except Exception as e:
        return f'ERROR: {e}'


def get_table_full_content(conn, table_name, where=''):
    """Read every row of a customizing table. Hashes per-row for diff."""
    try:
        opts = [{'TEXT': where}] if where else []
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE=table_name,
                      DELIMITER='|',
                      OPTIONS=opts, ROWCOUNT=999999)
        rows = [row['WA'] for row in r['DATA']]
        fields = [f['FIELDNAME'] for f in r['FIELDS']]
        # Hash whole table content for quick equality, plus per-row dict
        # for granular diff
        content_hash = hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()
        parsed = []
        for raw in rows:
            vals = raw.split('|')
            parsed.append(dict(zip(fields, [v.strip() for v in vals])))
        return {'fields': fields, 'rows': parsed, 'content_hash': content_hash,
                'row_count': len(rows)}
    except Exception as e:
        return {'error': str(e)}


def tadir_scan(conn, object_type, name_pattern, devclass_pattern=''):
    """Dynamic TADIR enumeration to catch unknown objects per pattern."""
    where = f"PGMID EQ 'R3TR' AND OBJECT EQ '{object_type}' AND OBJ_NAME LIKE '{name_pattern}'"
    if devclass_pattern:
        where += f" AND DEVCLASS LIKE '{devclass_pattern}'"
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='TADIR',
                      DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'OBJECT'},
                              {'FIELDNAME':'OBJ_NAME'},
                              {'FIELDNAME':'DEVCLASS'},
                              {'FIELDNAME':'AUTHOR'},
                              {'FIELDNAME':'CREATED_ON'},
                              {'FIELDNAME':'CHANGED_BY'},
                              {'FIELDNAME':'CHANGED_TS'}],
                      OPTIONS=[{'TEXT': where}], ROWCOUNT=9999)
        out = []
        for row in r['DATA']:
            f = row['WA'].split('|')
            out.append({'object': f[0].strip(), 'name': f[1].strip(),
                        'devclass': f[2].strip(), 'author': f[3].strip(),
                        'created_on': f[4].strip(), 'changed_by': f[5].strip(),
                        'changed_ts': f[6].strip()})
        return out
    except Exception as e:
        return [{'_error': str(e), '_pattern': name_pattern}]


def probe_system(conn, system_label):
    """Probe one system, return all metadata."""
    print(f"\n=== Probing {system_label} ===")
    out = {'system': system_label, 'probed_at': datetime.now().isoformat()}

    # Custom + SAP-std classes
    out['classes'] = {}
    for cat in ('unesco_classes', 'sap_std_classes'):
        for cls in OBJECTS_TO_CHECK[cat]:
            print(f"  class {cls}")
            includes = get_class_includes(conn, cls)
            metas = {inc: get_repo_meta(conn, inc) for inc in includes}
            out['classes'][cls] = {'category': cat, 'includes': metas}

    # Function modules (SAP std + CITIPMW)
    out['fms'] = {}
    for cat in ('sap_std_fms', 'citipmw_fms'):
        for fm in OBJECTS_TO_CHECK[cat]:
            print(f"  fm    {fm}")
            # FM source is in include LX<funcgroup>U<nn> — get_repo_meta
            # works on the function module name through TFDIR lookup
            meta = get_repo_meta(conn, fm)
            out['fms'][fm] = {'category': cat, 'meta': meta}

    # ENHO
    out['enho'] = {}
    for enh in OBJECTS_TO_CHECK['unesco_enho']:
        print(f"  enho  {enh}")
        # ENHO header in ENHHEADER table
        try:
            r = conn.call('RFC_READ_TABLE', QUERY_TABLE='ENHHEADER',
                          DELIMITER='|',
                          FIELDS=[{'FIELDNAME':'ENHNAME'},
                                  {'FIELDNAME':'PROCNAME'},
                                  {'FIELDNAME':'CHANGED_BY'},
                                  {'FIELDNAME':'CHANGED_ON'}],
                          OPTIONS=[{'TEXT': f"ENHNAME EQ '{enh}'"}])
            if r['DATA']:
                f = r['DATA'][0]['WA'].split('|')
                out['enho'][enh] = {'enhname': f[0].strip(),
                                    'procname': f[1].strip(),
                                    'changed_by': f[2].strip(),
                                    'changed_on': f[3].strip()}
            else:
                out['enho'][enh] = {'status': 'NOT_FOUND'}
        except Exception as e:
            out['enho'][enh] = {'error': str(e)}

    # Z utilities
    out['z_utils'] = {}
    for z in OBJECTS_TO_CHECK['unesco_z_utils']:
        print(f"  zutil {z}")
        out['z_utils'][z] = get_repo_meta(conn, z)

    # DMEE trees
    out['dmee_trees'] = {}
    for tree in OBJECTS_TO_CHECK['dmee_trees']:
        print(f"  tree  {tree}")
        out['dmee_trees'][tree] = get_dmee_tree_meta(conn, tree)

    # Customizing tables — FULL CONTENT diff (per-row hash)
    out['cust_tables'] = {}
    for tbl, where in OBJECTS_TO_CHECK['customizing_full_diff']:
        print(f"  cust  {tbl} {where or ''}")
        out['cust_tables'][tbl] = get_table_full_content(conn, tbl, where)

    # Dynamic TADIR enumeration
    out['tadir_scans'] = {}
    for obj_type, pattern, devclass in OBJECTS_TO_CHECK['dynamic_tadir_scans']:
        key = f"{obj_type}|{pattern}|{devclass}"
        print(f"  tadir {key}")
        out['tadir_scans'][key] = tadir_scan(conn, obj_type, pattern, devclass)

    return out


def diff_systems(p01, d01):
    """Compare two probe outputs and identify drifts."""
    drifts = []

    # Classes
    for cls, p_data in p01.get('classes', {}).items():
        d_data = d01.get('classes', {}).get(cls)
        if not d_data:
            drifts.append({'severity': 'CRITICAL', 'category': 'CLAS_MISSING',
                           'object': cls, 'detail': 'Exists in P01 only'})
            continue
        for inc, p_meta in p_data.get('includes', {}).items():
            d_meta = d_data.get('includes', {}).get(inc)
            if not d_meta:
                drifts.append({'severity': 'HIGH', 'category': 'INC_MISSING',
                               'object': f'{cls}/{inc}',
                               'detail': 'Include exists in P01 only'})
                continue
            if not p_meta or not d_meta:
                continue
            p_stamp = (p_meta.get('udat',''), p_meta.get('utime',''),
                       p_meta.get('unam',''))
            d_stamp = (d_meta.get('udat',''), d_meta.get('utime',''),
                       d_meta.get('unam',''))
            if p_stamp != d_stamp:
                drifts.append({'severity': 'HIGH', 'category': 'INC_DRIFT',
                               'object': f'{cls}/{inc}',
                               'p01_changed': f"{p_stamp[0]} {p_stamp[1]} by {p_stamp[2]}",
                               'd01_changed': f"{d_stamp[0]} {d_stamp[1]} by {d_stamp[2]}"})

    # FMs
    for fm, p_data in p01.get('fms', {}).items():
        d_data = d01.get('fms', {}).get(fm)
        if not d_data or not d_data.get('meta'):
            drifts.append({'severity': 'CRITICAL', 'category': 'FM_MISSING',
                           'object': fm, 'detail': 'Exists in P01 only'})
            continue
        p_meta = p_data.get('meta', {}) or {}
        d_meta = d_data.get('meta', {}) or {}
        p_stamp = (p_meta.get('udat',''), p_meta.get('utime',''))
        d_stamp = (d_meta.get('udat',''), d_meta.get('utime',''))
        if p_stamp != d_stamp:
            drifts.append({'severity': 'HIGH', 'category': 'FM_DRIFT',
                           'object': fm,
                           'p01_changed': f"{p_meta.get('udat')} {p_meta.get('utime')} by {p_meta.get('unam')}",
                           'd01_changed': f"{d_meta.get('udat')} {d_meta.get('utime')} by {d_meta.get('unam')}"})

    # DMEE trees
    for tree, p_data in p01.get('dmee_trees', {}).items():
        d_data = d01.get('dmee_trees', {}).get(tree, {})
        p_nodes = p_data.get('node_count', 0)
        d_nodes = d_data.get('node_count', 0)
        if p_nodes != d_nodes:
            drifts.append({'severity': 'CRITICAL', 'category': 'TREE_NODE_DRIFT',
                           'object': tree,
                           'p01_nodes': p_nodes, 'd01_nodes': d_nodes,
                           'detail': f'D01 has {d_nodes - p_nodes:+d} nodes vs P01'})
        # Compare head LAST_USER/LAST_DATE for active version
        for p_head in p_data.get('head_rows', []):
            if p_head.get('ex_status') == 'A':
                d_head = next((h for h in d_data.get('head_rows', [])
                               if h.get('version') == p_head.get('version')), None)
                if not d_head:
                    drifts.append({'severity': 'CRITICAL',
                                   'category': 'TREE_VERSION_MISSING',
                                   'object': tree,
                                   'detail': f"V{p_head.get('version')} not in D01"})
                    continue
                if (p_head.get('last_user'), p_head.get('last_date')) != \
                   (d_head.get('last_user'), d_head.get('last_date')):
                    drifts.append({'severity': 'HIGH', 'category': 'TREE_HEAD_DRIFT',
                                   'object': f"{tree}#V{p_head.get('version')}",
                                   'p01': f"{p_head.get('last_date')} by {p_head.get('last_user')}",
                                   'd01': f"{d_head.get('last_date')} by {d_head.get('last_user')}"})

    # Customizing tables — full content compare
    for tbl, p_data in p01.get('cust_tables', {}).items():
        d_data = d01.get('cust_tables', {}).get(tbl, {})
        if 'error' in p_data or 'error' in d_data:
            drifts.append({'severity': 'LOW', 'category': 'CUST_PROBE_ERROR',
                           'object': tbl,
                           'detail': f"P01: {p_data.get('error','OK')} | D01: {d_data.get('error','OK')}"})
            continue
        if p_data.get('content_hash') != d_data.get('content_hash'):
            # Per-row diff — find rows in P01 not in D01 and vice versa
            p_rows_set = {json.dumps(r, sort_keys=True) for r in p_data.get('rows', [])}
            d_rows_set = {json.dumps(r, sort_keys=True) for r in d_data.get('rows', [])}
            only_p = p_rows_set - d_rows_set
            only_d = d_rows_set - p_rows_set
            drifts.append({'severity': 'HIGH', 'category': 'CUST_CONTENT_DRIFT',
                           'object': tbl,
                           'p01_rows': p_data.get('row_count'),
                           'd01_rows': d_data.get('row_count'),
                           'only_in_p01': len(only_p),
                           'only_in_d01': len(only_d),
                           'sample_p01_only': list(only_p)[:3],
                           'sample_d01_only': list(only_d)[:3]})

    # TADIR dynamic scan diff
    for key, p_list in p01.get('tadir_scans', {}).items():
        d_list = d01.get('tadir_scans', {}).get(key, [])
        if p_list and isinstance(p_list[0], dict) and '_error' in p_list[0]:
            continue
        p_names = {row.get('name'): row for row in p_list if 'name' in row}
        d_names = {row.get('name'): row for row in d_list if 'name' in row}
        only_p = set(p_names) - set(d_names)
        only_d = set(d_names) - set(p_names)
        for name in only_p:
            drifts.append({'severity': 'HIGH', 'category': 'TADIR_P01_ONLY',
                           'object': name,
                           'detail': f"Pattern {key}: in P01 only ({p_names[name].get('author')} {p_names[name].get('changed_ts')})"})
        for name in only_d:
            drifts.append({'severity': 'CRITICAL', 'category': 'TADIR_D01_ONLY',
                           'object': name,
                           'detail': f"Pattern {key}: in D01 only ({d_names[name].get('author')} {d_names[name].get('changed_ts')}) — possible WIP"})
        # For BOTH: compare changed_ts
        both = set(p_names) & set(d_names)
        for name in both:
            p_ts = p_names[name].get('changed_ts', '')
            d_ts = d_names[name].get('changed_ts', '')
            if p_ts and d_ts and p_ts != d_ts:
                # Only flag if difference is meaningful (not just both empty)
                drifts.append({'severity': 'MEDIUM', 'category': 'TADIR_TS_DRIFT',
                               'object': name,
                               'detail': f"P01 ts={p_ts} by {p_names[name].get('changed_by')} | D01 ts={d_ts} by {d_names[name].get('changed_by')}"})

    return drifts


def write_report(p01, d01, drifts, out_dir):
    """Write JSON + markdown report."""
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, 'd01_vs_p01_drift_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({'p01': p01, 'd01': d01, 'drifts': drifts}, f,
                  indent=2, ensure_ascii=False)
    print(f"\nJSON: {json_path}")

    md_path = os.path.join(out_dir, 'd01_vs_p01_drift_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# D01 vs P01 Drift Report\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write(f"**Total drifts detected**: {len(drifts)}\n\n")
        bysev = {}
        for d in drifts:
            bysev.setdefault(d['severity'], []).append(d)
        for sev in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'):
            items = bysev.get(sev, [])
            f.write(f"## {sev} ({len(items)})\n\n")
            if not items:
                f.write("_None._\n\n")
                continue
            f.write("| Object | Category | Detail |\n|---|---|---|\n")
            for d in items:
                detail = d.get('detail', '')
                if 'p01_changed' in d:
                    detail = f"P01: {d['p01_changed']} \\| D01: {d['d01_changed']}"
                elif 'p01_nodes' in d:
                    detail = f"P01: {d['p01_nodes']} nodes \\| D01: {d['d01_nodes']} nodes"
                elif 'p01_rows' in d:
                    detail = f"P01: {d['p01_rows']} rows \\| D01: {d['d01_rows']} rows"
                elif 'p01' in d:
                    detail = f"P01: {d['p01']} \\| D01: {d['d01']}"
                f.write(f"| `{d['object']}` | {d['category']} | {detail} |\n")
            f.write("\n")
        f.write("## Conclusion guidance\n\n")
        f.write("- **CRITICAL**: blocks Phase 2 — must resolve before any D01 transport\n")
        f.write("- **HIGH**: requires N_MENARD review or retrofit before Phase 2\n")
        f.write("- **MEDIUM**: customizing drift — verify intent before changing\n\n")
    print(f"MD:   {md_path}")


def main():
    print("=== D01 vs P01 Drift Detector ===")
    print(f"Started: {datetime.now().isoformat()}")

    out_dir = 'knowledge/domains/Payment/phase0'
    os.makedirs(out_dir, exist_ok=True)

    p01 = None
    d01 = None

    print("\nConnecting P01...")
    try:
        p01_conn = get_connection('P01')
        p01 = probe_system(p01_conn, 'P01')
        p01_conn.close()
        # Save P01 snapshot immediately so it's not lost if D01 fails
        with open(os.path.join(out_dir, 'd01_vs_p01_drift_p01_snapshot.json'),
                  'w', encoding='utf-8') as f:
            json.dump(p01, f, indent=2, ensure_ascii=False)
        print("  P01 snapshot saved to d01_vs_p01_drift_p01_snapshot.json")
    except Exception as e:
        print(f"  P01 FAILED: {e}")
        return

    print("\nConnecting D01...")
    try:
        d01_conn = get_connection('D01')
        d01 = probe_system(d01_conn, 'D01')
        d01_conn.close()
        with open(os.path.join(out_dir, 'd01_vs_p01_drift_d01_snapshot.json'),
                  'w', encoding='utf-8') as f:
            json.dump(d01, f, indent=2, ensure_ascii=False)
        print("  D01 snapshot saved to d01_vs_p01_drift_d01_snapshot.json")
    except Exception as e:
        print(f"  D01 FAILED: {e}")
        print("\nProceeding with P01-only snapshot. To complete drift analysis,")
        print("add D01 credentials to .env (SAP_D01_*) and re-run.")
        return

    print("\nDiffing...")
    drifts = diff_systems(p01, d01)
    write_report(p01, d01, drifts, out_dir)
    print(f"\nDONE. {len(drifts)} drifts detected.")


if __name__ == '__main__':
    main()
