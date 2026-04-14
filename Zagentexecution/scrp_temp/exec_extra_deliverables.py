"""Create 4 extra Deliverable Tasks for M14-M18 using verbatim text from Section 5 Phase 3.
These are NOT in Table 1 but are explicit deliverables in the narrative."""
import json, base64, urllib.request, urllib.error, time

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

TASK_ID = '10911'
PILLAR_FIELD = 'customfield_10823'

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


# M14-M18 narrative deliverables extracted verbatim from Section 5 Phase 3
EXTRA_DELIVERABLES = [
    {
        'name': 'BP Sandbox Configuration & Re-classification Rules Tested',
        'parent': 'SCRP-14',  # M14 BP Sandbox Mapping
        'pillar': 'BP-GM',
        'fix_version': 'P3-BPGM-2027-2028',
        'phase_label': 'phase-3-bpgm-2028',
        'verbatim_source': 'Configure BP typologies in sandbox; test re-classification rules across all entity types; validate migration from SAP customer objects (Q3 2027)',
        'source_ref': 'Section 5 Phase 3 Technical Team Actions',
    },
    {
        'name': 'Grants Management End-to-End Business Process Design',
        'parent': 'SCRP-15',  # M15 GM Business Process Design
        'pillar': 'BP-GM',
        'fix_version': 'P3-BPGM-2027-2028',
        'phase_label': 'phase-3-bpgm-2028',
        'verbatim_source': 'Design and validate Grants Management end-to-end process: from donor agreement in Core Manager to GM posting in SAP; confirm automation meets audit and compliance requirements (Q4 2027)',
        'source_ref': 'Section 5 Phase 3 Business Team Actions',
    },
    {
        'name': 'GM Sandbox Configuration & Donor Agreement Lifecycle Test',
        'parent': 'SCRP-17',  # M17 GM Configuration
        'pillar': 'BP-GM',
        'fix_version': 'P3-BPGM-2027-2028',
        'phase_label': 'phase-3-bpgm-2028',
        'verbatim_source': 'Configure Grants Management module in sandbox; link to normalised FM and PS structures; test donor agreement lifecycle end-to-end (S1 2028)',
        'source_ref': 'Section 5 Phase 3 Technical Team Actions',
    },
    {
        'name': 'GM Core Manager Integration + BP Data Migration to Production',
        'parent': 'SCRP-18',  # M18 44 C/5 Readiness Deployment
        'pillar': 'BP-GM',
        'fix_version': 'P3-BPGM-2027-2028',
        'phase_label': 'phase-3-bpgm-2028',
        'verbatim_source': 'Implement GM <> Core Manager integration for donor data, organisations and VC workflow (S1 2028) | Execute BP data migration to production; deploy GM (S1 2028) | Support GM UAT and provide sign-off; confirm 44 C/5 budget cycle processes work end-to-end (S1 2028)',
        'source_ref': 'Section 5 Phase 3 Technical + Business Team Actions',
    },
]


print("=== Creating 4 extra Deliverable Tasks for M14-M18 (verbatim from Section 5) ===")
created = []
for idx, d in enumerate(EXTRA_DELIVERABLES, start=1):
    epic_start, epic_due = get_epic_dates(d['parent'])

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [tn(f"Deliverable: {d['name']}")]},
        {'type': 'paragraph', 'content': [tn(
            'Note: This deliverable is NOT listed in Section 3 Table 1 of the Framework document. It is extracted from the narrative Phase Action Plan (Section 5) which explicitly names this work for M14-M18. Text below is verbatim from the source.',
            [{'type': 'em'}]
        )]},
        {'type': 'rule'},
        bp('Verbatim scope (Section 5)', d['verbatim_source']),
        bp('Source reference', d['source_ref']),
        bp('Parent Milestone', d['parent']),
        bp('Phase', d['fix_version']),
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
            'Source: SAP Core Redesign Programme Framework, Section 5 Phased Action Plan (Phase 3) + Section 7 Governance. Verbatim from source document.',
            [{'type': 'em'}]
        )]},
    ]

    summary = ("DEL - " + d['name'])[:200]

    payload = {
        'fields': {
            'project':     {'key': 'SCRP'},
            'issuetype':   {'id': TASK_ID},
            'summary':     summary,
            'description': adf(blocks),
            'labels':      ['deliverable', 'raid', d['phase_label'], 'narrative-deliverable'],
            'priority':    {'name': 'High'},
            'fixVersions': [{'name': d['fix_version']}],
            'parent':      {'key': d['parent']},
            PILLAR_FIELD:  {'value': d['pillar']},
        }
    }
    if epic_due:
        payload['fields']['duedate'] = epic_due
    if epic_start:
        payload['fields']['customfield_10015'] = epic_start

    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        k = resp.get('key')
        created.append({'key': k, 'name': d['name'], 'parent': d['parent']})
        print(f"  [{idx}] {k} <- {d['parent']} | {d['name']}")
    else:
        print(f"  [{idx}] FAIL {status}: {json.dumps(resp)[:400]}")
    time.sleep(0.2)

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\extra_deliverables_created.json", 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)

print()
print(f"Created {len(created)}/4 extra deliverables")
