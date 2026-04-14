"""
Create the 17 Deliverables from §3 Table 1 as child Tasks of their parent
Milestone Epics. ALL text verbatim from the source document.

Mapping (hand-built by matching deliverable name -> milestone it supports):
  M1 Programme Governance Setup -> Programme Charter, RACI Matrix,
                                   Risk & Issue Register, Steering Committee TOR
  M2 FM Impact Analysis         -> FM Gap Analysis Report & Design
  M3 FM Sandbox Data Mapping    -> FM Sandbox Mapping Document
  M4 PS/WBS Impact Analysis     -> WBS Re-Modelling Report & Design
  M5 PS/WBS Data Mapping        -> WBS Sample Mapping Document
  M6 BP Impact Analysis         -> Business Partner Typology Document
  M7 2026 Design Go/No-Go       -> Phase 1 Design Review Report
  M8 FM Configuration           -> FM Configuration Document
  M9 PS/WBS Configuration       -> PS/WBS Configuration Document
  M10 Core Manager Integration  -> Integration Test Report (Core Manager)
  M11 UAT FM & PS               -> UAT Plan & Sign-off Document
  M12 FM & PS Production Deploy -> Training Materials, Cutover & Migration Plan
  M13 Post-Go-Live Stabilisation-> Post Go-Live Hypercare Report

M14-M18 have narrative deliverables only (not in Table 1) — skipped here.
"""
import json
import base64
import urllib.request
import urllib.error
import time

CRED_FILE = r'C:\Users\jp_lopez\.claude.json'
PARSED = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json"
COMPS_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\components.json"
OUT_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\deliverables_created.json"

with open(CRED_FILE, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

TASK_ID = '10911'

with open(COMPS_FILE, 'r') as f:
    comps = json.load(f)
COMP_BY_NAME = {c['name']: c['id'] for c in comps}

with open(PARSED, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Deliverables from Table 1 (skip header)
deliv_rows = doc['tables'][1][1:]
# Build lookup by exact deliverable name
deliv_by_name = {row[0]: row for row in deliv_rows}

# Deliverable -> (parent epic key, pillar components, phase, fix_version, due_offset_from_epic_end)
# due_offset_from_epic_end: 0 = same as epic due date
MAPPING = [
    # M1 Governance deliverables
    ('Programme Charter',                   'SCRP-1', ['Governance'], 'P1-Design-2026', 'phase-1-design-2026'),
    ('RACI Matrix',                         'SCRP-1', ['Governance'], 'P1-Design-2026', 'phase-1-design-2026'),
    ('Risk & Issue Register',               'SCRP-1', ['Governance'], 'P1-Design-2026', 'phase-1-design-2026'),
    ('Steering Committee TOR',              'SCRP-1', ['Governance'], 'P1-Design-2026', 'phase-1-design-2026'),
    # M2 FM
    ('FM Gap Analysis Report & Design',     'SCRP-2', ['FM'],         'P1-Design-2026', 'phase-1-design-2026'),
    # M3 FM Sandbox
    ('FM Sandbox Mapping Document',         'SCRP-3', ['FM'],         'P1-Design-2026', 'phase-1-design-2026'),
    # M4 PS/WBS
    ('WBS Re-Modelling Report & Design',    'SCRP-4', ['PS-WBS'],     'P1-Design-2026', 'phase-1-design-2026'),
    # M5 PS/WBS Data Mapping
    ('WBS Sample Mapping Document',         'SCRP-5', ['PS-WBS'],     'P1-Design-2026', 'phase-1-design-2026'),
    # M6 BP Typology
    ('Business Partner Typology Document',  'SCRP-6', ['BP-GM'],      'P1-Design-2026', 'phase-1-design-2026'),
    # M7 Go/No-Go
    ('Phase 1 Design Review Report',        'SCRP-7', ['Governance'], 'P1-Design-2026', 'phase-1-design-2026'),
    # M8 FM Config
    ('FM Configuration Document',           'SCRP-8', ['FM'],         'P2-Implementation-2027', 'phase-2-impl-2027'),
    # M9 PS/WBS Config
    ('PS/WBS Configuration Document',       'SCRP-9', ['PS-WBS'],     'P2-Implementation-2027', 'phase-2-impl-2027'),
    # M10 Core Manager Integration
    ('Integration Test Report (Core Manager)', 'SCRP-10', ['PS-WBS','FM'], 'P2-Implementation-2027', 'phase-2-impl-2027'),
    # M11 UAT
    ('UAT Plan & Sign-off Document',        'SCRP-11', ['FM','PS-WBS'], 'P2-Implementation-2027', 'phase-2-impl-2027'),
    # M12 Production Deployment
    ('Training Materials',                  'SCRP-12', ['FM','PS-WBS'], 'P2-Implementation-2027', 'phase-2-impl-2027'),
    ('Cutover & Migration Plan',            'SCRP-12', ['FM','PS-WBS'], 'P2-Implementation-2027', 'phase-2-impl-2027'),
    # M13 Hypercare
    ('Post Go-Live Hypercare Report',       'SCRP-13', ['FM','PS-WBS'], 'P2-Implementation-2027', 'phase-2-impl-2027'),
]


def text_node(text, marks=None):
    n = {'type': 'text', 'text': text}
    if marks:
        n['marks'] = marks
    return n


def bold_para(label, value):
    return {'type': 'paragraph', 'content': [
        text_node(f"{label}: ", [{'type': 'strong'}]),
        text_node(value)
    ]}


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


# Fetch parent epic due dates to inherit on deliverable
def get_epic_due_date(epic_key):
    status, resp = api('GET', f'/rest/api/3/issue/{epic_key}?fields=duedate,customfield_10015')
    if status == 200:
        return resp['fields'].get('duedate'), resp['fields'].get('customfield_10015')
    return None, None


print("=== Creating 17 Deliverable Tasks as children of Milestone Epics ===")
created = []
for idx, (deliv_name, parent_epic, pillars, fix_ver, phase_label) in enumerate(MAPPING, start=1):
    if deliv_name not in deliv_by_name:
        print(f"  SKIP [{deliv_name}] — not found in Table 1")
        continue

    row = deliv_by_name[deliv_name]
    _, content, producer, approver = row[0], row[1], row[2], row[3]

    # Inherit dates from parent epic
    epic_due, epic_start = get_epic_due_date(parent_epic)

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2},
         'content': [text_node(f"Deliverable: {deliv_name}")]},
        bold_para('Content / What it must include (verbatim, §3 Table 1)', content),
        bold_para('Producer', producer),
        bold_para('Approver', approver),
        bold_para('Parent Milestone', parent_epic),
        bold_para('Phase', fix_ver),
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 3},
         'content': [text_node('Quality Gates (verbatim, §7)')]},
        {'type': 'paragraph', 'content': [text_node(
            'All deliverables must pass a two-stage quality check before acceptance:'
        )]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Technical review: DBS SAP lead confirms technical correctness and completeness against the acceptance criteria defined in Section 3.'
            )]}]},
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Business review: Named business owner confirms the deliverable reflects actual business requirements and is fit for the next phase.'
            )]}]}
        ]},
        {'type': 'paragraph', 'content': [text_node(
            'No milestone is marked complete until both reviews are signed off. The PMO maintains the Deliverable Tracker as the authoritative record.'
        )]},
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [text_node(
            'Source: SAP Core Redesign Programme Framework, §3 Deliverables + §7 Governance. Verbatim from source document.',
            [{'type': 'em'}]
        )]}
    ]

    # Safe summary (Jira limit 255 chars)
    summary = f"DEL · {deliv_name}"[:200]

    payload = {
        'fields': {
            'project': {'key': 'SCRP'},
            'issuetype': {'id': TASK_ID},
            'summary': summary,
            'description': adf(blocks),
            'labels': ['deliverable', 'raid', phase_label],
            'components': [{'id': COMP_BY_NAME[p]} for p in pillars],
            'priority': {'name': 'High'},
            'fixVersions': [{'name': fix_ver}],
            'parent': {'key': parent_epic},
            'duedate': epic_due,
        }
    }
    # Start date inherit
    if epic_start:
        payload['fields']['customfield_10015'] = epic_start

    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        created.append({
            'key': resp.get('key'),
            'name': deliv_name,
            'parent': parent_epic,
            'fix_version': fix_ver,
        })
        print(f"  [{idx:2d}] {resp.get('key')} ← {parent_epic} | {deliv_name}")
    else:
        print(f"  [{idx:2d}] FAIL {status}: {json.dumps(resp)[:400]}")
    time.sleep(0.2)

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)

print()
print(f"Created {len(created)}/17 deliverables")
print(f"Saved {OUT_FILE}")
