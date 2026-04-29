"""Extract the 17 CITIPMW V3 FMs we hadn't extracted yet, all active in P01 via MP_EXIT_FUNC."""
import sys, os, hashlib
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # noqa

REMAINING = [
    '/CITIPMW/V3_CGI_BANK_NAME',
    '/CITIPMW/V3_CGI_TAXAMT_TTLAMT',
    '/CITIPMW/V3_CGI_TAX_CATEGORY',
    '/CITIPMW/V3_CGI_TAX_CTGRY_DTLS',
    '/CITIPMW/V3_CGI_TAX_FORMS_CODE',
    '/CITIPMW/V3_CGI_TAX_METHOD',
    '/CITIPMW/V3_DMEE_EXIT_CGI_XML',
    '/CITIPMW/V3_DMEE_EXIT_INV_DESC',
    '/CITIPMW/V3_EXIT_CGI_CRED_NM3',
    '/CITIPMW/V3_EXIT_CGI_CRED_NM4',
    '/CITIPMW/V3_EXIT_CGI_DEBT_NAME',
    '/CITIPMW/V3_EXIT_CGI_TAX_SQNB',
    '/CITIPMW/V3_EXIT_CGI_TP_WHT',
    '/CITIPMW/V3_GET_CDTR_EMAIL',
    '/CITIPMW/V3_GET_CDTR_MOBILE',
    '/CITIPMW/V3_POSTALCODE',
    '/CITIPMW/V3_TAXAMT_TXBASEAMT',
    '/CITIPMW/V3_WL949_BIC_OR_ID',
]

OUT = Path('extracted_code/FI/DMEE_full_inventory')
OUT.mkdir(parents=True, exist_ok=True)


def extract(conn, fm):
    """Use RPY_FUNCTIONMODULE_READ_NEW with NEW_SOURCE field (proven works for /CITIPMW/)."""
    try:
        r = conn.call('RPY_FUNCTIONMODULE_READ_NEW',
                      FUNCTIONNAME=fm,
                      ONLY_SOURCE='X')
        lines = r.get('NEW_SOURCE', [])
        text = '\n'.join(ln.get('LINE', '') for ln in lines)
        return text
    except Exception as e:
        # Try other RFC variant
        try:
            r = conn.call('RPY_FUNCTIONMODULE_READ',
                          FUNCTIONNAME=fm)
            lines = r.get('SOURCE_EXTENDED', []) or r.get('SOURCE', [])
            text = '\n'.join(ln.get('LINE', '') for ln in lines)
            return text
        except Exception as e2:
            return f'EXTRACT_ERROR: {e} | fallback: {e2}'


def main():
    print(f'=== Extract {len(REMAINING)} remaining CITIPMW V3 FMs ===')
    conn = get_connection('P01')
    extracted_count = 0
    for fm in REMAINING:
        clean_name = fm.replace('/', '_').strip('_')
        out_file = OUT / f'{clean_name}.abap'
        print(f'  {fm}')
        text = extract(conn, fm)
        if text and not text.startswith('EXTRACT_ERROR'):
            out_file.write_text(text, encoding='utf-8')
            extracted_count += 1
            print(f'    -> {out_file.name} ({len(text.splitlines())} lines, sha={hashlib.sha256(text.encode()).hexdigest()[:12]})')
        else:
            print(f'    FAIL: {text[:200]}')
    conn.close()
    print(f'\n{extracted_count}/{len(REMAINING)} extracted to {OUT}')


if __name__ == '__main__':
    main()
