"""Create Action Stories from Section 5 Phase Action Plan bullets.
Each bullet becomes a Story, verbatim, with parent = the milestone it supports."""
import json, base64, urllib.request, urllib.error, time

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

STORY_ID = '10913'
PILLAR_FIELD = 'customfield_10823'

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json", 'r', encoding='utf-8') as f:
    doc = json.load(f)


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


# Extract all Phase Action Plan bullets with context
action_bullets = []
for s in doc['sections']:
    if s.get('h1') and '5. Phased Action Plan' in s['h1'] and s['style'] == 'List Paragraph':
        action_bullets.append({
            'phase': s.get('h2', ''),
            'team':  s.get('h3', ''),
            'text':  s['text'],
        })

print(f"Extracted {len(action_bullets)} action bullets from Section 5")


# Map each bullet to a milestone epic and pillar based on keyword matching
def map_to_milestone(text, phase, team):
    t = text.lower()
    # Phase 1 — Design
    if 'sandbox environment for redesign' in t and 'isolated' in t:
        return ('SCRP-1', 'Governance', 'P1-Design-2026', 'phase-1-design-2026')
    if 'named business owners' in t:
        return ('SCRP-1', 'Governance', 'P1-Design-2026', 'phase-1-design-2026')
    if 'as-is fm configuration' in t or 'fm impact analysis' in t or ('co-author fm to-be' in t):
        return ('SCRP-2', 'FM', 'P1-Design-2026', 'phase-1-design-2026')
    if 'fm sandbox data mapping' in t or 'validate fm sandbox' in t:
        return ('SCRP-3', 'FM', 'P1-Design-2026', 'phase-1-design-2026')
    if 'as-is wbs inconsistencies' in t or 'ps/wbs impact analysis' in t or ('co-author ps/wbs to-be' in t):
        return ('SCRP-4', 'PS-WBS', 'P1-Design-2026', 'phase-1-design-2026')
    if 'wbs sample mappings in sandbox' in t or 'identify pilots for wbs sandbox' in t or 'validate wbs sample mappings' in t:
        return ('SCRP-5', 'PS-WBS', 'P1-Design-2026', 'phase-1-design-2026')
    if 'customer (business partner) configuration' in t or 'vendor/customer/donor master data' in t:
        return ('SCRP-6', 'BP-GM', 'P1-Design-2026', 'phase-1-design-2026')
    if 'design review report' in t or 'go/no-go steering committee' in t:
        return ('SCRP-7', 'Governance', 'P1-Design-2026', 'phase-1-design-2026')

    # Phase 2 — Implementation
    if 'build fm configuration' in t or 'promote fm configuration to qa' in t:
        return ('SCRP-8', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'build ps/wbs level 4 configuration' in t:
        return ('SCRP-9', 'PS-WBS', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'review and sign off fm and ps/wbs configuration' in t:
        return ('SCRP-8', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'integration test suite' in t:
        return ('SCRP-10', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'support uat' in t or 'lead uat' in t or 'provide formal uat sign-off' in t:
        return ('SCRP-11', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'cutover plan' in t or 'production deployment' in t or 'prepare memos' in t or 'train finance and programme' in t:
        return ('SCRP-12', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'support post go-live stabilisation' in t or 'hypercare' in t:
        return ('SCRP-13', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')

    # Phase 3 — BP & GM
    if 'configure bp typologies in sandbox' in t or 'validate bp typology definitions' in t:
        return ('SCRP-14', 'BP-GM', 'P3-BPGM-2027-2028', 'phase-3-bpgm-2028')
    if 'design and validate grants management' in t:
        return ('SCRP-15', 'BP-GM', 'P3-BPGM-2027-2028', 'phase-3-bpgm-2028')
    if 'configure grants management module in sandbox' in t:
        return ('SCRP-17', 'BP-GM', 'P3-BPGM-2027-2028', 'phase-3-bpgm-2028')
    if 'implement gm <> core manager' in t or 'execute bp data migration' in t or 'support gm uat' in t:
        return ('SCRP-18', 'BP-GM', 'P3-BPGM-2027-2028', 'phase-3-bpgm-2028')

    # Fallback by phase H2
    if 'Phase 1' in phase:
        return ('SCRP-1', 'Governance', 'P1-Design-2026', 'phase-1-design-2026')
    if 'Phase 2' in phase:
        return ('SCRP-8', 'FM', 'P2-Implementation-2027', 'phase-2-impl-2027')
    if 'Phase 3' in phase:
        return ('SCRP-14', 'BP-GM', 'P3-BPGM-2027-2028', 'phase-3-bpgm-2028')
    return ('SCRP-1', 'Governance', 'P1-Design-2026', 'phase-1-design-2026')


def get_epic_dates(key):
    status, resp = api('GET', f'/rest/api/3/issue/{key}?fields=duedate,customfield_10015')
    if status == 200:
        return resp['fields'].get('customfield_10015'), resp['fields'].get('duedate')
    return None, None


# Determine team label
def team_label(team_h3):
    if 'Technical Team' in team_h3 or 'DBS SAP' in team_h3:
        return 'technical-action'
    if 'Business Team' in team_h3 or 'FIN' in team_h3 or 'BSP' in team_h3 or 'DBM' in team_h3:
        return 'business-action'
    return 'programme-action'


print()
print("=== Creating Action Stories ===")
created = []
for idx, bullet in enumerate(action_bullets, start=1):
    parent, pillar, fix_ver, phase_label = map_to_milestone(bullet['text'], bullet['phase'], bullet['team'])
    epic_start, epic_due = get_epic_dates(parent)
    team_lbl = team_label(bullet['team'])

    # Shorten bullet for summary (strip trailing quarter refs in parens)
    import re
    short = re.sub(r'\s*\([QS][0-9][^)]*\)\s*$', '', bullet['text']).strip()
    short = short[:150] + ('...' if len(short) > 150 else '')
    summary = f"ACT - {short}"[:250]

    blocks = [
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [tn(f"Action Story (verbatim, Section 5)")]},
        bp('Phase (verbatim)', bullet['phase']),
        bp('Team (verbatim)', bullet['team']),
        bp('Action text (verbatim)', bullet['text']),
        bp('Parent Milestone', parent),
        bp('Pillar', pillar),
        bp('Phase release', fix_ver),
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [tn(
            'Source: SAP Core Redesign Programme Framework, Section 5 Phased Action Plan. Verbatim from source document.',
            [{'type': 'em'}]
        )]},
    ]

    payload = {
        'fields': {
            'project':     {'key': 'SCRP'},
            'issuetype':   {'id': STORY_ID},
            'summary':     summary,
            'description': adf(blocks),
            'labels':      ['action-story', team_lbl, phase_label, 'raid'],
            'priority':    {'name': 'Medium'},
            'fixVersions': [{'name': fix_ver}],
            'parent':      {'key': parent},
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
        created.append({'key': k, 'parent': parent, 'pillar': pillar, 'team': team_lbl})
        print(f"  [{idx:2d}] {k} <- {parent} | {team_lbl:17s} | {bullet['text'][:65]}")
    else:
        print(f"  [{idx:2d}] FAIL {status}: {json.dumps(resp)[:300]}")
    time.sleep(0.15)

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\action_stories_created.json", 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)

print()
print(f"Created {len(created)} action stories")
