"""Create 17 Deliverable Tasks as children of Milestone Epics, verbatim from Table 1."""
import json, base64, urllib.request, urllib.error, time

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

TASK_ID = '10911'
PILLAR_FIELD = 'customfield_10823'

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json", 'r', encoding='utf-8') as f:
    doc = json.load(f)
deliv_rows = doc['tables'][1][1:]
deliv_by_name = {row[0]: row for row in deliv_rows}

MAPPING = [
    ('Programme Charter',                      'SCRP-1',  'Governance', 'P1-Design-2026',         'phase-1-design-2026'),
    ('RACI Matrix',                            'SCRP-1',  'Governance', 'P1-Design-2026',         'phase-1-design-2026'),
    ('Risk & Issue Register',                  'SCRP-1',  'Governance', 'P1-Design-2026',         'phase-1-design-2026'),
    ('Steering Committee TOR',                 'SCRP-1',  'Governance', 'P1-Design-2026',         'phase-1-design-2026'),
    ('FM Gap Analysis Report & Design',        'SCRP-2',  'FM',         'P1-Design-2026',         'phase-1-design-2026'),
    ('FM Sandbox Mapping Document',            'SCRP-3',  'FM',         'P1-Design-2026',         'phase-1-design-2026'),
    ('WBS Re-Modelling Report & Design',       'SCRP-4',  'PS-WBS',     'P1-Design-2026',         'phase-1-design-2026'),
    ('WBS Sample Mapping Document',            'SCRP-5',  'PS-WBS',     'P1-Design-2026',         'phase-1-design-2026'),
    ('Business Partner Typology Document',     'SCRP-6',  'BP-GM',      'P1-Design-2026',         'phase-1-design-2026'),
    ('Phase 1 Design Review Report',           'SCRP-7',  'Governance', 'P1-Design-2026',         'phase-1-design-2026'),
    ('FM Configuration Document',              'SCRP-8',  'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('PS/WBS Configuration Document',          'SCRP-9',  'PS-WBS',     'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('Integration Test Report (Core Manager)', 'SCRP-10', 'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('UAT Plan & Sign-off Document',           'SCRP-11', 'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('Training Materials',                     'SCRP-12', 'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('Cutover & Migration Plan',               'SCRP-12', 'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('Post Go-Live Hypercare Report',          'SCRP-13', 'FM',         'P2-Implementation-2027', 'phase-2-impl-2027'),
]


def tn(text, marks=None):
    n = {'type': 'text', 'text': text}
    if marks:
        n['marks'] = marks
    return n


def bp(label, value):
    return {'type': 'paragraph', 'content': [tn(f"{label}: ", [{'type': 'strong'}]), tn(value)]}


def adf(blocks):
    return {'type': 'doc', 'version': 1, 'content': blocks}


def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=H, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        txt = resp.read().decode()
        return resp.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.read().decode()}


def get_epic_dates(key):
    status, resp = api('GET', f'/rest/api/3/issue/{key}?fields=duedate,customfield_10015')
    if status == 200:
        return resp['fields'].get('customfield_10015'), resp['fields'].get('duedate')
    return None, None


print("=== Creating 17 Deliverable Tasks (verbatim from Table 1) ===")
created = []
for idx, (dname, parent_key, pillar, fix_ver, phase_label) in enumerate(MAPPING, start=1):
    if dname not in deliv_by_name:
        print(f"  [{idx:2d}] SKIP: {dname} not in Table 1")
        continue

    row = deliv_by_name[dname]
    content_text  = row[1]
    producer_text = row[2]
    approver_text = row[3] if len(row) > 3 else ''

    epic_start, epic_due = get_epic_dates(parent_key)

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [tn(f"Deliverable: {dname}")]},
        bp('Content / What it must include (verbatim, Section 3 Table 1)', content_text),
        bp('Producer (verbatim)', producer_text),
        bp('Approver (verbatim)', approver_text),
        bp('Parent Milestone', parent_key),
        bp('Phase', fix_ver),
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 3}, 'content': [tn('Quality Gates (verbatim, Section 7)')]},
        {'type': 'paragraph', 'content': [tn('All deliverables must pass a two-stage quality check before acceptance:')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [tn(
                'Technical review: DBS SAP lead confirms technical correctness and completeness against the acceptance criteria defined in Section 3.'
            )]}]},
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [tn(
                'Business review: Named business owner confirms the deliverable reflects actual business requirements and is fit for the next phase.'
            )]}]},
        ]},
        {'type': 'paragraph', 'content': [tn(
            'No milestone is marked complete until both reviews are signed off. The PMO maintains the Deliverable Tracker as the authoritative record.'
        )]},
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [tn(
            'Source: SAP Core Redesign Programme Framework, Section 3 Deliverables + Section 7 Governance. Verbatim from source document.',
            [{'type': 'em'}]
        )]},
    ]

    summary = ("DEL - " + dname)[:200]

    payload = {
        'fields': {
            'project':     {'key': 'SCRP'},
            'issuetype':   {'id': TASK_ID},
            'summary':     summary,
            'description': adf(blocks),
            'labels':      ['deliverable', 'raid', phase_label],
            'priority':    {'name': 'High'},
            'fixVersions': [{'name': fix_ver}],
            'parent':      {'key': parent_key},
            PILLAR_FIELD:  {'value': pillar},
        }
    }
    if epic_due:
        payload['fields']['duedate'] = epic_due
    if epic_start:
        payload['fields']['customfield_10015'] = epic_start

    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        k = resp.get('key')
        created.append({'key': k, 'name': dname, 'parent': parent_key, 'pillar': pillar})
        print(f"  [{idx:2d}] {k} <- {parent_key} | Pillar={pillar} | {dname}")
    else:
        print(f"  [{idx:2d}] FAIL {status}: {json.dumps(resp)[:400]}")
    time.sleep(0.2)

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\deliverables_created.json", 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)

print()
print(f"Created {len(created)}/17 deliverables")
