"""Create 42 Quality Gate Subtasks — 2 per Deliverable (Technical Review + Business Review).
Section 7 verbatim."""
import json, base64, urllib.request, urllib.error, time, urllib.parse

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

SUBTASK_ID = '10915'
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


# Fetch all Deliverables via JQL
print("=== Fetching all 21 Deliverables ===")
jql = 'project = SCRP AND labels = "deliverable"'
url = f"{BASE}/rest/api/3/search/jql?jql={urllib.parse.quote(jql)}&fields=summary,parent,customfield_10823,fixVersions,duedate,customfield_10015&maxResults=100"
r = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30)
d = json.loads(r.read().decode())

deliverables = []
for i in d.get('issues', []):
    f = i['fields']
    parent = f.get('parent', {}).get('key') if f.get('parent') else None
    pillar = f.get('customfield_10823', {}).get('value') if f.get('customfield_10823') else None
    fvs = [v['name'] for v in f.get('fixVersions', [])]
    deliverables.append({
        'key': i['key'],
        'summary': f['summary'],
        'parent': parent,
        'pillar': pillar,
        'fix_versions': fvs,
        'duedate': f.get('duedate'),
        'start_date': f.get('customfield_10015'),
    })
print(f"Found {len(deliverables)} deliverables")

# For each deliverable, create 2 subtasks
TECH_REVIEW_TEXT = (
    'Technical review: DBS SAP lead confirms technical correctness and completeness '
    'against the acceptance criteria defined in Section 3.'
)
BIZ_REVIEW_TEXT = (
    'Business review: Named business owner confirms the deliverable reflects actual '
    'business requirements and is fit for the next phase.'
)

print()
print("=== Creating 42 Quality Gate Subtasks ===")
created = []
for deliv in deliverables:
    for review_type, desc_text, label in [
        ('Technical Review', TECH_REVIEW_TEXT, 'quality-gate-technical'),
        ('Business Review',  BIZ_REVIEW_TEXT,  'quality-gate-business'),
    ]:
        # Strip 'DEL - ' prefix for cleaner subtask summary
        deliv_name = deliv['summary'].replace('DEL - ', '')
        summary = f"{review_type} - {deliv_name}"[:200]

        blocks = [
            {'type': 'heading', 'attrs': {'level': 2}, 'content': [tn(f"Quality Gate: {review_type}")]},
            bp('Reviewer role (verbatim, Section 7)', 'DBS SAP lead' if review_type == 'Technical Review' else 'Named business owner'),
            bp('Deliverable', deliv['key']),
            bp('Parent Milestone', deliv['parent'] or '-'),
            {'type': 'rule'},
            {'type': 'heading', 'attrs': {'level': 3}, 'content': [tn('Sign-off criteria (verbatim, Section 7 Deliverable Quality Gates)')]},
            {'type': 'paragraph', 'content': [tn('All deliverables must pass a two-stage quality check before acceptance:')]},
            {'type': 'bulletList', 'content': [
                {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [tn(TECH_REVIEW_TEXT)]}]},
                {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [tn(BIZ_REVIEW_TEXT)]}]},
            ]},
            {'type': 'paragraph', 'content': [tn(
                'No milestone is marked complete until both reviews are signed off. The PMO maintains the Deliverable Tracker as the authoritative record.'
            )]},
            {'type': 'rule'},
            {'type': 'paragraph', 'content': [tn(
                'Source: SAP Core Redesign Programme Framework, Section 7 Deliverable Quality Gates. Verbatim from source document.',
                [{'type': 'em'}]
            )]},
        ]

        payload = {
            'fields': {
                'project':     {'key': 'SCRP'},
                'issuetype':   {'id': SUBTASK_ID},
                'summary':     summary,
                'description': adf(blocks),
                'labels':      ['quality-gate', label, 'raid'],
                'priority':    {'name': 'High'},
                'parent':      {'key': deliv['key']},
            }
        }
        if deliv['pillar']:
            payload['fields'][PILLAR_FIELD] = {'value': deliv['pillar']}
        if deliv['fix_versions']:
            payload['fields']['fixVersions'] = [{'name': fv} for fv in deliv['fix_versions']]

        status, resp = api('POST', '/rest/api/3/issue', payload)
        if status in (200, 201):
            k = resp.get('key')
            created.append({'key': k, 'parent': deliv['key'], 'type': review_type})
            print(f"  {k} <- {deliv['key']} | {review_type}")
        else:
            print(f"  FAIL {deliv['key']} {review_type}: {status} - {json.dumps(resp)[:300]}")
        time.sleep(0.15)

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\quality_gates_created.json", 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)

print()
print(f"Created {len(created)} quality gate subtasks")
