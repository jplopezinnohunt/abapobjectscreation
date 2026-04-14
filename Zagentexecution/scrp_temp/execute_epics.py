"""
Execute SCRP epic creation (M2-M18) + fix SCRP-1 (M1) with verbatim content.
Uses direct REST because mcp-atlassian-jira v2 doesn't expose Epic start/due date
fields in its simplified create_issue wrapper.
"""
import json
import base64
import urllib.request
import urllib.error
import time

CRED_FILE = r'C:\Users\jp_lopez\.claude.json'
CONTENT_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\milestones_content.json"
COMPS_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\components.json"
OUT_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\epics_created.json"

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

# Load components lookup
with open(COMPS_FILE, 'r') as f:
    comps = json.load(f)
COMP_BY_NAME = {c['name']: c['id'] for c in comps}

# Load milestones
with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
    milestones = json.load(f)


def adf_from_markdown(md_text):
    """Convert markdown to minimal ADF (Atlassian Document Format).
    Jira API v3 requires ADF for description. Very basic conversion."""
    lines = md_text.split('\n')
    content = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # Horizontal rule
        if line.strip() == '---':
            content.append({'type': 'rule'})
            i += 1
            continue
        # Heading
        if line.startswith('# '):
            content.append({'type': 'heading', 'attrs': {'level': 1}, 'content': [{'type': 'text', 'text': line[2:]}]})
            i += 1
            continue
        if line.startswith('## '):
            content.append({'type': 'heading', 'attrs': {'level': 2}, 'content': [{'type': 'text', 'text': line[3:]}]})
            i += 1
            continue
        if line.startswith('### '):
            content.append({'type': 'heading', 'attrs': {'level': 3}, 'content': [{'type': 'text', 'text': line[4:]}]})
            i += 1
            continue
        # Blockquote
        if line.startswith('> '):
            content.append({'type': 'blockquote', 'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': line[2:]}]}]})
            i += 1
            continue
        # Bullet list
        if line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append({
                    'type': 'listItem',
                    'content': [{'type': 'paragraph', 'content': parse_inline(lines[i][2:])}]
                })
                i += 1
            content.append({'type': 'bulletList', 'content': items})
            continue
        # Paragraph (with inline bold)
        content.append({'type': 'paragraph', 'content': parse_inline(line)})
        i += 1
    return {'type': 'doc', 'version': 1, 'content': content}


def parse_inline(text):
    """Parse inline bold **text**. Returns list of text nodes."""
    parts = []
    while '**' in text:
        before, _, rest = text.partition('**')
        bold, _, after = rest.partition('**')
        if before:
            parts.append({'type': 'text', 'text': before})
        if bold:
            parts.append({'type': 'text', 'text': bold, 'marks': [{'type': 'strong'}]})
        text = after
    if text:
        parts.append({'type': 'text', 'text': text})
    if not parts:
        parts = [{'type': 'text', 'text': ' '}]
    return parts


def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        text = resp.read().decode()
        return resp.status, (json.loads(text) if text else {})
    except urllib.error.HTTPError as e:
        return e.code, {'error': e.read().decode()}


EPIC_ISSUE_TYPE_ID = '10914'

def build_issue_payload(m):
    fields = {
        'project': {'key': 'SCRP'},
        'issuetype': {'id': EPIC_ISSUE_TYPE_ID},
        'summary': m['summary'],
        'description': adf_from_markdown(m['description']),
        'labels': m['labels'],
        'components': [{'id': COMP_BY_NAME[c]} for c in m['components']],
        'priority': {'name': 'High' if 'go-no-go-gate' in m['labels'] or m['id'] in ('M1', 'M18') else 'Medium'},
        'duedate': m['due_date'],
        'customfield_10015': m['start_date'],  # Start date
    }
    return {'fields': fields}


# === STEP 1: Fix SCRP-1 (M1) ===
print("=== STEP 1: Update SCRP-1 with verbatim content ===")
m1 = milestones[0]
payload = build_issue_payload(m1)
# For PUT, we don't include project/issuetype
update_fields = {k: v for k, v in payload['fields'].items() if k not in ('project', 'issuetype')}
status, resp = api('PUT', '/rest/api/3/issue/SCRP-1', {'fields': update_fields})
if status in (200, 204):
    print(f"  SCRP-1 updated OK")
else:
    print(f"  SCRP-1 FAIL: {status} - {json.dumps(resp)[:500]}")

# === STEP 2: Create M2-M18 ===
print()
print("=== STEP 2: Create M2-M18 Epics ===")
created = [{'id': 'M1', 'key': 'SCRP-1'}]
for m in milestones[1:]:
    payload = build_issue_payload(m)
    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        created.append({'id': m['id'], 'key': resp.get('key'), 'jira_id': resp.get('id')})
        print(f"  {m['id']} → {resp.get('key')} ({m['start_date']}..{m['due_date']})")
    else:
        print(f"  {m['id']} FAIL: {status} - {json.dumps(resp)[:500]}")
    time.sleep(0.3)

with open(OUT_FILE, 'w') as f:
    json.dump(created, f, indent=2)

print()
print(f"Total created/updated: {len(created)}")
print(f"Saved manifest to {OUT_FILE}")
