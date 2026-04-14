"""
Create 4 Pillar Meta-Epics with verbatim §1.2 content from source document.
Link each to its milestone epics + (Governance) to Risks + Immediate Actions.
"""
import json
import base64
import urllib.request
import urllib.error
import time

CRED_FILE = r'C:\Users\jp_lopez\.claude.json'
PARSED = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json"
COMPS_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\components.json"
OUT_FILE = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\meta_epics_created.json"

with open(CRED_FILE, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

EPIC_ID = '10914'

with open(COMPS_FILE, 'r') as f:
    comps = json.load(f)
COMP_BY_NAME = {c['name']: c['id'] for c in comps}

with open(PARSED, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# === Extract verbatim §1.2 Pillar paragraphs from document ===
pillar_texts = {}
current_pillar = None
for s in doc['sections']:
    if s.get('h2') == 'The Three Pillars of SAP Redesign':
        text = s['text']
        if text.startswith('Pillar 1'):
            current_pillar = 'P1'
            pillar_texts[current_pillar] = {'title': text, 'body': ''}
        elif text.startswith('Pillar 2'):
            current_pillar = 'P2'
            pillar_texts[current_pillar] = {'title': text, 'body': ''}
        elif text.startswith('Pillar 3'):
            current_pillar = 'P3'
            pillar_texts[current_pillar] = {'title': text, 'body': ''}
        elif current_pillar and s['style'] == 'Normal':
            pillar_texts[current_pillar]['body'] = text
            current_pillar = None

# § 1 Exec Summary + §7 Governance intro for Governance Meta-Epic
exec_summary = ""
gov_intro = ""
for s in doc['sections']:
    if s.get('h1') == '1. Executive Summary & Programme Rationale' and not s.get('h2') and s['style'] == 'Normal':
        exec_summary = s['text']
    if s.get('h1') == '7. Programme Governance & Reporting' and s.get('h2') == 'Governance Structure':
        break

# Approach bullets (§1.3)
approach_bullets = []
for s in doc['sections']:
    if s.get('h2') == 'Approach' and s['style'] == 'List Paragraph':
        approach_bullets.append(s['text'])

print("=== Verbatim content extracted ===")
for k, v in pillar_texts.items():
    print(f"\n{k}: {v['title']}")
    print(f"    {v['body'][:120]}...")
print(f"\nExec Summary: {exec_summary[:120]}...")
print(f"Approach bullets: {len(approach_bullets)}")


def text_node(text, marks=None):
    n = {'type': 'text', 'text': text}
    if marks:
        n['marks'] = marks
    return n


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


def build_meta_desc_pillar(pillar_key, child_milestones):
    p = pillar_texts[pillar_key]
    blocks = [
        {'type': 'heading', 'attrs': {'level': 1}, 'content': [text_node(p['title'])]},
        {'type': 'paragraph', 'content': [text_node(p['body'])]},
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Milestones in this pillar')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [
                {'type': 'paragraph', 'content': [text_node(m)]}
            ]} for m in child_milestones
        ]},
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Programme approach (verbatim, §1.3)')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [
                {'type': 'paragraph', 'content': [text_node(b)]}
            ]} for b in approach_bullets
        ]},
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [
            text_node('Source: SAP Core Redesign Programme Framework, §1.2 The Three Pillars of SAP Redesign + §1.3 Approach. Verbatim from source document.',
                      [{'type': 'em'}])
        ]}
    ]
    return adf(blocks)


def build_meta_desc_governance(child_milestones):
    blocks = [
        {'type': 'heading', 'attrs': {'level': 1}, 'content': [text_node('PROGRAMME GOVERNANCE · PMO, Steering Committee, Risk Register')]},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Executive Summary (verbatim, §1)')]},
        {'type': 'paragraph', 'content': [text_node(exec_summary)]},
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Governance milestones & gates')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [
                {'type': 'paragraph', 'content': [text_node(m)]}
            ]} for m in child_milestones
        ]},
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Programme approach (verbatim, §1.3)')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [
                {'type': 'paragraph', 'content': [text_node(b)]}
            ]} for b in approach_bullets
        ]},
        {'type': 'rule'},
        {'type': 'heading', 'attrs': {'level': 2}, 'content': [text_node('Cross-cutting responsibilities')]},
        {'type': 'bulletList', 'content': [
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Maintains consolidated programme plan, RACI, risk register, and status reporting (PMO — Didem, Francois)'
            )]}]},
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Issues monthly programme status report to CITO and Steering Committee'
            )]}]},
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Reviews milestone status, risks, and Go/No-Go gates (Steering Committee — Monthly)'
            )]}]},
            {'type': 'listItem', 'content': [{'type': 'paragraph', 'content': [text_node(
                'Owns the 7 Risks and 9 Immediate Actions registered in SCRP-19..SCRP-34'
            )]}]},
        ]},
        {'type': 'rule'},
        {'type': 'paragraph', 'content': [
            text_node('Source: SAP Core Redesign Programme Framework, §1 Executive Summary + §7 Governance Structure. Verbatim from source document.',
                      [{'type': 'em'}])
        ]}
    ]
    return adf(blocks)


# === 4 Meta-Epics definition ===
META_EPICS = [
    {
        'summary': 'META · PILLAR 1 — Funds Management (FM) Re-normalisation',
        'component': 'FM',
        'color': 'blue',
        'label': 'meta-epic-pillar-1',
        'children': ['SCRP-2', 'SCRP-3', 'SCRP-8', 'SCRP-10', 'SCRP-11', 'SCRP-12', 'SCRP-13'],
        'children_display': [
            'M2 · FM Impact Analysis Completed (SCRP-2)',
            'M3 · FM Sandbox Data Mapping (SCRP-3)',
            'M8 · FM Data Harmonisation & Configuration (SCRP-8)',
            'M10 · Core Manager Integration Validated (SCRP-10) [joint with PS-WBS]',
            'M11 · UAT FM & PS (SCRP-11) [joint with PS-WBS]',
            'M12 · FM & PS Production Deployment (SCRP-12) [joint with PS-WBS]',
            'M13 · Post-Go-Live Stabilisation (SCRP-13) [joint with PS-WBS]',
        ],
        'description': 'pillar_P1',
    },
    {
        'summary': 'META · PILLAR 2 — Project System / WBS Level 4 Implementation',
        'component': 'PS-WBS',
        'color': 'green',
        'label': 'meta-epic-pillar-2',
        'children': ['SCRP-4', 'SCRP-5', 'SCRP-9', 'SCRP-10', 'SCRP-11', 'SCRP-12', 'SCRP-13'],
        'children_display': [
            'M4 · PS/WBS Impact Analysis Completed (SCRP-4)',
            'M5 · PS/WBS Data Mapping (SCRP-5)',
            'M9 · PS/WBS Configuration & Testing (SCRP-9)',
            'M10 · Core Manager Integration Validated (SCRP-10) [joint with FM]',
            'M11 · UAT FM & PS (SCRP-11) [joint with FM]',
            'M12 · FM & PS Production Deployment (SCRP-12) [joint with FM]',
            'M13 · Post-Go-Live Stabilisation (SCRP-13) [joint with FM]',
        ],
        'description': 'pillar_P2',
    },
    {
        'summary': 'META · PILLAR 3 — Business Partners Redesign / Grants Management',
        'component': 'BP-GM',
        'color': 'purple',
        'label': 'meta-epic-pillar-3',
        'children': ['SCRP-6', 'SCRP-14', 'SCRP-15', 'SCRP-17', 'SCRP-18'],
        'children_display': [
            'M6 · Business Partners Impact Analysis (Donor) (SCRP-6)',
            'M14 · Business Partners Sandbox Mapping (SCRP-14)',
            'M15 · Grants Management Business Process Design (SCRP-15)',
            'M17 · Grants Management Configuration (SCRP-17)',
            'M18 · 44 C/5 Readiness Deployment (SCRP-18)',
        ],
        'description': 'pillar_P3',
    },
    {
        'summary': 'META · PROGRAMME GOVERNANCE — PMO, Steering Committee, Risk Register',
        'component': 'Governance',
        'color': 'orange',
        'label': 'meta-epic-governance',
        # Governance Meta-Epic links to: M1, M7, M16, ALL risks (SCRP-19..25), ALL immediate actions (SCRP-26..34)
        'children': (
            ['SCRP-1', 'SCRP-7', 'SCRP-16']
            + [f'SCRP-{i}' for i in range(19, 26)]   # 7 risks
            + [f'SCRP-{i}' for i in range(26, 35)]   # 9 actions
        ),
        'children_display': [
            'M1 · Programme Governance Setup (SCRP-1)',
            'M7 · 2026 Design Phase Review Go/No-Go (SCRP-7) [GATE]',
            'M16 · 2027 Grants Management Design Phase Review Go/No-Go (SCRP-16) [GATE]',
            '7 Risks: SCRP-19 through SCRP-25',
            '9 Immediate Actions: SCRP-26 through SCRP-34',
        ],
        'description': 'governance',
    },
]

print()
print("=== Creating 4 Meta-Epics ===")
created = []
for m in META_EPICS:
    if m['description'] == 'governance':
        desc = build_meta_desc_governance(m['children_display'])
    else:
        p_key = m['description'].replace('pillar_', '')
        desc = build_meta_desc_pillar(p_key, m['children_display'])

    payload = {
        'fields': {
            'project': {'key': 'SCRP'},
            'issuetype': {'id': EPIC_ID},
            'summary': m['summary'],
            'description': desc,
            'labels': ['meta-epic', m['label'], 'cross-phase'],
            'components': [{'id': COMP_BY_NAME[m['component']]}],
            'priority': {'name': 'Highest'},
            'customfield_10015': '2026-04-01',  # start: programme start
            'duedate': '2028-12-31',            # due: programme end
            'customfield_10017': m['color'],    # epic color
            'fixVersions': [
                {'name': 'P1-Design-2026'},
                {'name': 'P2-Implementation-2027'},
                {'name': 'P3-BPGM-2027-2028'},
            ],
        }
    }
    status, resp = api('POST', '/rest/api/3/issue', payload)
    if status in (200, 201):
        meta_key = resp.get('key')
        created.append({
            'key': meta_key,
            'summary': m['summary'],
            'component': m['component'],
            'color': m['color'],
            'children': m['children'],
        })
        print(f"  {meta_key} — {m['summary']}")
    else:
        print(f"  FAIL {m['summary']}: {status} - {json.dumps(resp)[:400]}")
    time.sleep(0.3)


# === Create "is parent of" / "relates to" issue links ===
# Jira link type: 'Relates' works in all projects. Best semantic type would be
# 'Blocks' or 'is included by' but those need specific configs. 'Relates' is safest.
print()
print("=== Linking Meta-Epics to their children ===")
link_count = 0
for meta in created:
    for child_key in meta['children']:
        link_body = {
            'type': {'name': 'Relates'},
            'inwardIssue': {'key': child_key},   # child "relates to" meta
            'outwardIssue': {'key': meta['key']},
            'comment': {
                'body': {
                    'type': 'doc', 'version': 1,
                    'content': [{
                        'type': 'paragraph',
                        'content': [{'type': 'text', 'text': f"Part of Meta-Epic {meta['key']} (verbatim from §1.2 of Framework document)"}]
                    }]
                }
            }
        }
        status, resp = api('POST', '/rest/api/3/issueLink', link_body)
        if status in (200, 201):
            link_count += 1
        else:
            print(f"  Link FAIL {meta['key']} -> {child_key}: {status} - {json.dumps(resp)[:200]}")
        time.sleep(0.1)

print(f"Created {link_count} links")

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(created, f, indent=2, ensure_ascii=False)
print(f"Saved manifest to {OUT_FILE}")
