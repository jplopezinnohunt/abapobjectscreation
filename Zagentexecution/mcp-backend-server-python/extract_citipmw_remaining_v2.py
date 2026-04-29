"""Retry the 6 CITIPMW FMs with simpler RFC method (no ONLY_SOURCE param)."""
import sys, hashlib
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

REMAINING = [
    '/CITIPMW/V3_EXIT_CGI_CRED_NM3',
    '/CITIPMW/V3_EXIT_CGI_CRED_NM4',
    '/CITIPMW/V3_EXIT_CGI_DEBT_NAME',
    '/CITIPMW/V3_GET_CDTR_MOBILE',
    '/CITIPMW/V3_WL949_BIC_OR_ID',
]
OUT = Path('extracted_code/FI/DMEE_full_inventory')


def extract_via_tfdir_repo(conn, fm):
    """Get include name via TFDIR, then read REPOSRC source."""
    try:
        r = conn.call('RFC_READ_TABLE', QUERY_TABLE='TFDIR', DELIMITER='|',
                      FIELDS=[{'FIELDNAME':'PNAME'},{'FIELDNAME':'INCLUDE'}],
                      OPTIONS=[{'TEXT': f"FUNCNAME EQ '{fm}'"}])
        if not r['DATA']:
            return None, 'NOT_IN_TFDIR'
        f = r['DATA'][0]['WA'].split('|')
        funcgroup = f[0].strip()
        inc_no = f[1].strip().zfill(2)
        # /NS/SAPL<GRP>  ->  /NS/L<GRP>U<NN>
        if funcgroup.startswith('/'):
            ns_end = funcgroup.find('/', 1) + 1
            ns = funcgroup[:ns_end]
            grp = funcgroup[ns_end:].replace('SAPL', '', 1)
            inc = f'{ns}L{grp}U{inc_no}'
        else:
            grp = funcgroup.replace('SAPL', '', 1)
            inc = f'L{grp}U{inc_no}'
        # Read source from include via RPY_PROGRAM_READ
        r2 = conn.call('RPY_PROGRAM_READ', PROGRAM_NAME=inc,
                       WITH_INCLUDELIST=' ', ONLY_SOURCE='X',
                       WITH_LOWERCASE='X')
        lines = r2.get('SOURCE_EXTENDED', [])
        return '\n'.join(ln.get('LINE', '') for ln in lines), inc
    except Exception as e:
        return None, str(e)


def main():
    conn = get_connection('P01')
    ok = 0
    for fm in REMAINING:
        clean = fm.replace('/', '_').strip('_')
        out_file = OUT / f'{clean}.abap'
        print(f'  {fm}')
        text, info = extract_via_tfdir_repo(conn, fm)
        if text:
            out_file.write_text(text, encoding='utf-8')
            print(f'    -> {out_file.name} ({len(text.splitlines())} lines, via {info})')
            ok += 1
        else:
            print(f'    FAIL: {info}')
    conn.close()
    print(f'\n{ok}/{len(REMAINING)} extracted')


if __name__ == '__main__':
    main()
