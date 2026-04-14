"""
Seed SCRP with:
  - 7 Risks (Table 3) as Task issues with label 'risk'
  - 9 Immediate Actions (Table 5) as Task issues with label 'pmo-action'

All text verbatim from the source document. No paraphrasing.
"""
import json
import base64
import urllib.request
import urllib.error
import time

CRED_FILE = r'C:\Users\jp_lopez\.claude.json'
PARSED = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json"
COMPS_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\components.json"
OUT_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\raid_created.json"

with open(CRED_FILE, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
SITE = env['ATLASSIAN_SITE_NAME']
EMAIL = env['ATLASSIAN_USER_EMAIL']
TOKEN = env['ATLASSIAN_API_TOKEN']
BASE = f"https://{SITE}.atlassian.net"
AUTH = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    'Authorization': f'Basic {AUTH}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

TASK_ISSUE_TYPE_ID = '10911'

with open(COMPS_FILE, 'r') as f:
    comps = json.load(f)
COMP_BY_NAME = {c['name']: c['id'] for c in comps}

with open(PARSED, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Table 3 (index 3) = Risks; Table 5 (index 5) = Immediate Actions
risks_rows = doc['tables'][3][1:]   # skip header
actions_rows = doc['tables'][5][1:]  # skip header


def text_node(text, marks=None):
    n = {'type': 'text', 'text': text}
    if marks:
        n['marks'] = marks
    return n


def adf(blocks):
    return {'type': 'doc', 'version': 1, 'content': blocks}


def para(text):
    return {'type': 'paragraph', 'content': [text_node(text)]}


def bold_para(label, value):
    return {'type': 'paragraph', 'content': [
        text_node(f"{label}: ", [{'type': 'strong'}]),
        text_node(value)
    ]}


def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        txt = resp.read().decode()
        return resp.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.read().decode()}


# Map risk owners → affected components based on owner text
def components_for_risk(owner_text):
    out = []
    ot = owner_text.upper()
    if 'FM' in ot or 'DBM' in ot or 'FIN' in ot:
        out.append('FM')
    if 'PS' in ot or 'WBS' in ot or 'EPM' in ot or 'BSP' in ot:
        out.append('PS-WBS')
    if 'BSP' in ot or 'BP' in ot or 'GM' in ot:
        out.append('BP-GM')
    if not out:
        out.append('Governance')
    # Dedupe while preserving order
    seen = set()
    return [x for x in out if not (x in seen or seen.add(x))]


# === RISKS ===
print("=== Seeding 7 Risks (Table 3) ===")
risk_created = []
for idx, row in enumerate(risks_rows, start=1):
    risk_text, prob, impact, owner, mitigation = row[0], row[1], row[2], row[3], row[4]
    summary = f"RISK-{idx:02d} · {risk_text[:120]}"

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2},
         'content': [text_node(f"RISK-{idx:02d}")]},
        bold_para('Risk (verbatim, §6 Table)', risk_text),
        bold_para('Probability', prob),
        bold_para('Impact', impact),
        bold_para('Owner', owner),
        bold_para('Mitigation', mitigation),
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [
            text_node('Source: SAP Core Redesign Programme Framework, §6 Programme Risk Register. Verbatim from source document.',
                      [{'type': 'em'}])
        ]}
    ]

    components = components_for_risk(owner)
    severity = 'Highest' if (prob == 'High' and impact == 'High') else ('High' if impact == 'High' else 'Medium')

    payload = {
        'fields': {
            'project': {'key': 'SCRP'},
            'issuetype': {'id': TASK_ISSUE_TYPE_ID},
            'summary': summary,
            'description': adf(blocks),
            'labels': ['risk', 'raid', f'prob-{prob.lower().strip()}', f'impact-{impact.lower().strip()}'],
            'components': [{'id': COMP_BY_NAME[c]} for c in components],
            'priority': {'name': severity},
        }
    }
    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        risk_created.append({'key': resp.get('key'), 'title': risk_text[:80]})
        print(f"  RISK-{idx:02d} → {resp.get('key')} [{prob}/{impact}] → {components}")
    else:
        print(f"  RISK-{idx:02d} FAIL: {status} - {json.dumps(resp)[:300]}")
    time.sleep(0.2)

# === IMMEDIATE ACTIONS ===
print()
print("=== Seeding 9 Immediate Actions (Table 5) ===")
action_created = []
for row in actions_rows:
    num, action_text, owner, due = row[0], row[1], row[2], row[3]
    summary = f"ACT-{int(num):02d} · {action_text[:120]}"

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2},
         'content': [text_node(f"Immediate Action #{num}")]},
        bold_para('Action (verbatim, §8 Table)', action_text),
        bold_para('Owner', owner),
        bold_para('Due', due),
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [
            text_node('Source: SAP Core Redesign Programme Framework, §8 Immediate Next Steps — Q2 2026. Verbatim from source document.',
                      [{'type': 'em'}])
        ]}
    ]

    payload = {
        'fields': {
            'project': {'key': 'SCRP'},
            'issuetype': {'id': TASK_ISSUE_TYPE_ID},
            'summary': summary,
            'description': adf(blocks),
            'labels': ['pmo-action', 'raid', 'phase-1-design-2026', 'q2-2026-kickoff'],
            'components': [{'id': COMP_BY_NAME['Governance']}],
            'priority': {'name': 'High'},
        }
    }
    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        action_created.append({'key': resp.get('key'), 'num': num})
        print(f"  ACT-{num} → {resp.get('key')} (due {due})")
    else:
        print(f"  ACT-{num} FAIL: {status} - {json.dumps(resp)[:300]}")
    time.sleep(0.2)

with open(OUT_FILE, 'w') as f:
    json.dump({'risks': risk_created, 'actions': action_created}, f, indent=2)

print()
print(f"Total risks: {len(risk_created)}")
print(f"Total actions: {len(action_created)}")
print(f"Saved manifest to {OUT_FILE}")
