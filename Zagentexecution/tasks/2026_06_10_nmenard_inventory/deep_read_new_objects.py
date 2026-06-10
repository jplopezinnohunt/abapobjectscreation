"""Deep-read the 6 representative NEW N_MENARD objects via ADT GET (READ-ONLY).

HARD RULE: on the first HTTP 401, STOP — never retry credentials (SAP locks
accounts after 3-5 failed attempts).
"""
import sys, urllib.error
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = Path(__file__).resolve().parent
MCP_DIR = HERE.parent.parent / 'mcp-backend-server-python'
sys.path.insert(0, str(MCP_DIR))
from sap_adt_client import from_env  # noqa

OUTDIR = HERE / 'readback'
OUTDIR.mkdir(exist_ok=True)

TARGETS = [
    ('YCL_HR_WF_MAIL_GENERATOR_PA_S1', '/sap/bc/adt/oo/classes/ycl_hr_wf_mail_generator_pa_s1', 'clas.abap'),
    ('YCL_HR_WF_MAIL_PA_S1_ACTION',    '/sap/bc/adt/oo/classes/ycl_hr_wf_mail_pa_s1_action',    'clas.abap'),
    ('YHR_WF_PA_LIST_1',               '/sap/bc/adt/programs/programs/yhr_wf_pa_list_1',         'prog.abap'),
    ('YHR_WF_PA_LIST_1_DATA',          '/sap/bc/adt/programs/includes/yhr_wf_pa_list_1_data',    'prog.abap'),
    ('YHR_WF_PA_LIST_1_SEL',           '/sap/bc/adt/programs/includes/yhr_wf_pa_list_1_sel',     'prog.abap'),
    ('Y_HRPAWF_EVENT_RULES_PA0000',    '/sap/bc/adt/functions/groups/yhrpawf1/fmodules/y_hrpawf_event_rules_pa0000', 'func.abap'),
    ('Y_HR_PAWF_FILL_REQUEST',         '/sap/bc/adt/functions/groups/yhrpawf1/fmodules/y_hr_pawf_fill_request',      'func.abap'),
]


def main():
    client = from_env('D01')
    print(f'ADT base: {client.base_url} client={client.client}')
    for name, uri, ext in TARGETS:
        try:
            src = client.get_source(uri)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f'!! HTTP 401 on {name} — STOPPING (no credential retries).')
                sys.exit(1)
            print(f'!! {name}: HTTP {e.code} — skipping')
            continue
        out = OUTDIR / f'{name}.{ext}'
        out.write_text(src, encoding='utf-8')
        print(f'{name}: {len(src.splitlines())} lines -> {out.name}')

    # Table structure via ADT DDIC read
    try:
        t = client.get_table_structure('YTHRWF_STEP_ACT')
        import json
        (OUTDIR / 'YTHRWF_STEP_ACT.json').write_text(json.dumps(t, indent=1), encoding='utf-8')
        print(f"YTHRWF_STEP_ACT: {len(t['fields'])} fields -> YTHRWF_STEP_ACT.json")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print('!! HTTP 401 on table read — STOPPING.')
            sys.exit(1)
        print(f'!! YTHRWF_STEP_ACT: HTTP {e.code}')


if __name__ == '__main__':
    main()
