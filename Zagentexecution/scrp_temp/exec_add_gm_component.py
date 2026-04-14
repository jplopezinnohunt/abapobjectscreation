"""Add GM as a 5th component in SCRP.
Update M15 and M17 to use GM component.
Update M18 to add GM to its component list.
Do NOT change the Pillar field (stays at 4 values per framework document)."""
import json, base64, urllib.request, urllib.error, time

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}


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


# Step 1: Check if GM component already exists; create if not
print("=== Step 1: Creating GM component ===")
status, resp = api('GET', '/rest/api/3/project/SCRP')
existing_comps = {c['name']: c['id'] for c in resp.get('components', [])}
print(f"  Current components: {list(existing_comps.keys())}")

gm_id = existing_comps.get('GM')
if not gm_id:
    body = {
        'name': 'GM',
        'description': 'SAP Grants Management module (new module implementation). Per Framework Section 1.2 Pillar 3: The Grants Management (GM) module is non-existent. This component tracks the greenfield GM module implementation work, distinct from the BP-GM workstream which covers Business Partner redesign for donor classification.',
        'project': 'SCRP'
    }
    status, resp = api('POST', '/rest/api/3/component', body)
    if status in (200, 201):
        gm_id = resp.get('id')
        print(f"  Created GM component: id={gm_id}")
    else:
        print(f"  FAIL: {status} - {resp}")
        exit(1)
else:
    print(f"  GM component already exists: id={gm_id}")


# Step 2: Update milestones
# SCRP-15 M15 GM Business Process Design: GM + BP-GM (design touches both)
# SCRP-17 M17 GM Configuration: GM only
# SCRP-18 M18 44 C/5 Readiness: add GM to existing component list (cross-pillar)
print()
print("=== Step 2: Updating milestone Components ===")

UPDATES = [
    ('SCRP-15', ['BP-GM', 'GM'],                       'M15 GM Business Process Design (BP data + GM module)'),
    ('SCRP-17', ['GM'],                                 'M17 GM Configuration (pure GM)'),
    ('SCRP-18', ['FM', 'PS-WBS', 'BP-GM', 'GM', 'Governance'], 'M18 44 C/5 Readiness (cross-pillar final deployment)'),
]

for key, components, label in UPDATES:
    body = {'fields': {'components': [{'name': c} for c in components]}}
    status, resp = api('PUT', f'/rest/api/3/issue/{key}', body)
    if status in (200, 204):
        print(f"  {key} -> {components}  ({label})")
    else:
        print(f"  {key} FAIL {status}: {resp}")
    time.sleep(0.2)


# Step 3: Verify
print()
print("=== Step 3: Verification ===")
for key, _, _ in UPDATES:
    status, resp = api('GET', f'/rest/api/3/issue/{key}?fields=components,summary')
    if status == 200:
        comps = [c['name'] for c in resp['fields'].get('components', [])]
        print(f"  {key}: components={comps}")


# Step 4: List all components in SCRP
print()
print("=== Step 4: Final component list in SCRP ===")
status, resp = api('GET', '/rest/api/3/project/SCRP')
for c in resp.get('components', []):
    print(f"  {c['id']}: {c['name']}")
