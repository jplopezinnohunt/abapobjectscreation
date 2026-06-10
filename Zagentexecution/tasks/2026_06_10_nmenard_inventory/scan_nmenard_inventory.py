"""
scan_nmenard_inventory.py — Complete N_MENARD object inventory from D01 (READ-ONLY).

Step 1 of the N_MENARD style-guide completion task:
  1. TADIR: full content of package YHR_PA_WF
  2. TADIR: all objects authored by N_MENARD (any package) -> sibling packages
  3. TFDIR: function modules of every FUGR found
  4. Description texts: SEOCLASSTX / DD02T / TRDIRT / TFTIT / TLIBT (EN)
  5. Dump everything to nmenard_inventory.json (incremental-safe: written at the end
     of each phase so a stall never loses completed phases)

READ-ONLY: RFC_READ_TABLE only. No writes, no deploys.
"""
import sys, json, time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
MCP_DIR = HERE.parent.parent / 'mcp-backend-server-python'
sys.path.insert(0, str(MCP_DIR))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa

OUT = HERE / 'nmenard_inventory.json'
state = {'phases_done': [], 'package_objects': [], 'author_objects': [],
         'fugr_fms': {}, 'descriptions': {}}


def save():
    OUT.write_text(json.dumps(state, indent=1), encoding='utf-8')


def rfc_read_all(conn, table, fields, where):
    """Single RFC_READ_TABLE call, ROWCOUNT=0 (no paging — this kernel rejects
    ROWSKIPS without GET_SORTED). Pipe delimiter, parse via FIELDS offsets."""
    options = [{'TEXT': chunk} for chunk in _split_where(where)]
    result = conn.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|',
                       FIELDS=[{'FIELDNAME': f} for f in fields],
                       OPTIONS=options, ROWCOUNT=0, ROWSKIPS=0)
    rows = []
    for line in result['DATA']:
        parts = line['WA'].split('|')
        rows.append({f: parts[i].strip() if i < len(parts) else ''
                     for i, f in enumerate(fields)})
    return rows


def _split_where(where):
    """OPTIONS lines max 72 chars."""
    out, cur = [], ''
    for tok in where.split(' '):
        if len(cur) + len(tok) + 1 > 72:
            out.append(cur)
            cur = tok
        else:
            cur = (cur + ' ' + tok).strip()
    if cur:
        out.append(cur)
    return out


def main():
    print('=== N_MENARD inventory scan (D01, read-only) ===')
    conn = get_connection('D01')

    # Phase 1: package YHR_PA_WF content
    print('\n[1] TADIR: package YHR_PA_WF...')
    rows = rfc_read_all(conn, 'TADIR',
                        ['PGMID', 'OBJECT', 'OBJ_NAME', 'AUTHOR', 'DEVCLASS'],
                        "DEVCLASS = 'YHR_PA_WF'")
    state['package_objects'] = rows
    state['phases_done'].append('package')
    save()
    print(f'    {len(rows)} objects in YHR_PA_WF')

    # Phase 2: everything N_MENARD authored (sibling packages)
    print('\n[2] TADIR: AUTHOR = N_MENARD (all packages)...')
    rows = rfc_read_all(conn, 'TADIR', ['PGMID', 'OBJECT', 'OBJ_NAME', 'AUTHOR', 'DEVCLASS'], "AUTHOR = 'N_MENARD'")
    state['author_objects'] = rows
    state['phases_done'].append('author')
    save()
    pkgs = sorted({r.get('DEVCLASS', '') for r in rows})
    print(f'    {len(rows)} objects across packages: {pkgs}')

    # Phase 3: FMs of every function group in scope
    fugrs = sorted({r['OBJ_NAME'].strip() for r in
                    state['package_objects'] + state['author_objects']
                    if r.get('OBJECT', '').strip() == 'FUGR'})
    print(f'\n[3] TFDIR: FMs of function groups {fugrs}...')
    for fg in fugrs:
        rows = rfc_read_all(conn, 'TFDIR', ['FUNCNAME', 'PNAME', 'FMODE'],
                            f"PNAME = 'SAPL{fg}'")
        state['fugr_fms'][fg] = rows
        print(f'    {fg}: {len(rows)} FMs')
    state['phases_done'].append('fms')
    save()

    # Phase 4: descriptions (EN) — pull Y* texts wholesale, filter at report time
    print('\n[4] Description texts (EN)...')
    text_pulls = [
        ('SEOCLASSTX', ['CLSNAME', 'DESCRIPT'], "CLSNAME LIKE 'Y%' AND LANGU = 'E'"),
        ('DD02T',      ['TABNAME', 'DDTEXT'],   "TABNAME LIKE 'Y%' AND DDLANGUAGE = 'E' AND AS4LOCAL = 'A'"),
        ('TRDIRT',     ['NAME', 'TEXT'],        "NAME LIKE 'Y%' AND SPRSL = 'E'"),
        ('TFTIT',      ['FUNCNAME', 'STEXT'],   "FUNCNAME LIKE 'Y%' AND SPRAS = 'E'"),
        ('TLIBT',      ['AREA', 'AREAT'],       "AREA LIKE 'Y%' AND SPRAS = 'E'"),
        ('DD04T',      ['ROLLNAME', 'DDTEXT'],  "ROLLNAME LIKE 'Y%' AND DDLANGUAGE = 'E' AND AS4LOCAL = 'A'"),
    ]
    for table, fields, where in text_pulls:
        try:
            rows = rfc_read_all(conn, table, fields, where)
            state['descriptions'][table] = {r[fields[0]].strip(): r[fields[1]].strip()
                                            for r in rows}
            print(f'    {table}: {len(rows)} texts')
        except Exception as e:
            print(f'    {table}: FAILED ({e}) — continuing')
            state['descriptions'][table] = {}
        save()
    state['phases_done'].append('texts')
    save()

    conn.close()
    print(f'\nDONE. Inventory at {OUT}')


if __name__ == '__main__':
    main()

