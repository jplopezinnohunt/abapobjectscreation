"""Migrate SCRP-19..25 from Task to Risk issue type.
Populate Probability (dropdown), Impact (dropdown), Mitigation (text).
Keep parent, labels, description, fix versions, Pillar."""
import json, base64, urllib.request, urllib.error, time

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['jira']['env']
BASE = f"https://{env['ATLASSIAN_SITE_NAME']}.atlassian.net"
AUTH = base64.b64encode(f"{env['ATLASSIAN_USER_EMAIL']}:{env['ATLASSIAN_API_TOKEN']}".encode()).decode()
H = {'Authorization': f'Basic {AUTH}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

RISK_TYPE_ID = '10948'  # Discovered from earlier createmeta
PROB_FIELD   = 'customfield_10819'
IMPACT_FIELD = 'customfield_10820'
MITIG_FIELD  = 'customfield_10821'
PILLAR_FIELD = 'customfield_10823'


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


# Risk data verbatim from Framework Table 3
RISKS = [
    {
        'key': 'SCRP-19', 'num': 1,
        'prob': 'Med', 'impact': 'High',
        'owner': 'DBS SAP + DBM + FIN',
        'risk_text':   'FM decoupling breaks existing budget controls in active projects',
        'mitigation':  'Detailed impact analysis in sandbox before any config change; rollback plan per release',
    },
    {
        'key': 'SCRP-20', 'num': 2,
        'prob': 'High', 'impact': 'High',
        'owner': 'CITO + DBS',
        'risk_text':   'ABAP/technical capacity insufficient for parallel delivery of 2026 priorities and redesign',
        'mitigation':  'Resource plan with explicit capacity allocation; prioritisation protocol agreed with sponsors ; activate external partner support ; budget envelope for external support pre-approved in UNESCORE 3.0;',
    },
    {
        'key': 'SCRP-21', 'num': 3,
        'prob': 'Med', 'impact': 'High',
        'owner': 'PMO + Sponsors',
        'risk_text':   'Business owners insufficiently available for design workshops and UAT',
        'mitigation':  'Formal time commitment in governance charter; named deputies for each business area',
    },
    {
        'key': 'SCRP-22', 'num': 4,
        'prob': 'Med', 'impact': 'High',
        'owner': 'DBS SAP + DBS EPM',
        'risk_text':   'WBS re-modelling disrupts Core Manager <> SAP synchronisation',
        'mitigation':  'Joint integration test plan from Day 1; Core Manager team in scope of all PS design sessions',
    },
    {
        'key': 'SCRP-23', 'num': 5,
        'prob': 'Med', 'impact': 'Med',
        'owner': 'DBS + DBM + BSP + FIN',
        'risk_text':   'Adoption resistance - inconsistent WBS usage across entities',
        'mitigation':  'Change management plan (communications, materials, trainings); mandatory compliance framework post go-live',
    },
    {
        'key': 'SCRP-24', 'num': 6,
        'prob': 'High', 'impact': 'Med',
        'owner': 'FIN + BSP + DBS SAP',
        'risk_text':   'Data quality issues in vendor/customer master data delay BP migration',
        'mitigation':  'Data quality assessment as part of Phase 1; cleansing plan before migration; double entry and consolidation rules to be clarified',
    },
    {
        'key': 'SCRP-25', 'num': 7,
        'prob': 'Med', 'impact': 'High',
        'owner': 'DBS',
        'risk_text':   '44 C/5 budget cycle constraints compress deployment window',
        'mitigation':  'Timeline anchored to C/5 deadline from outset; no-go criteria defined at M7 review',
    },
]


print("=== Migrating 7 Risks: two-step (change type, then populate fields) ===")
migrated = []
for r in RISKS:
    # Step 1: Change issue type ONLY
    body1 = {'fields': {'issuetype': {'id': RISK_TYPE_ID}}}
    status1, resp1 = api('PUT', f'/rest/api/3/issue/{r["key"]}', body1)
    if status1 not in (200, 204):
        print(f"  {r['key']} STEP1 FAIL {status1}: {json.dumps(resp1)[:300]}")
        continue

    # Step 2: Populate Risk-specific fields (now that the Risk screen is active)
    # Mitigation is a paragraph field — needs ADF format
    mitigation_adf = {
        'type': 'doc', 'version': 1,
        'content': [{'type': 'paragraph', 'content': [{'type': 'text', 'text': r['mitigation']}]}]
    }
    body2 = {'fields': {
        PROB_FIELD:    {'value': r['prob']},
        IMPACT_FIELD:  {'value': r['impact']},
        MITIG_FIELD:   mitigation_adf,
    }}
    status2, resp2 = api('PUT', f'/rest/api/3/issue/{r["key"]}', body2)
    if status2 in (200, 204):
        migrated.append({'key': r['key'], 'prob': r['prob'], 'impact': r['impact']})
        print(f"  {r['key']}: Task -> Risk | Prob={r['prob']} | Impact={r['impact']}")
    else:
        print(f"  {r['key']} STEP2 FAIL {status2}: {json.dumps(resp2)[:400]}")
    time.sleep(0.2)

print()
print(f"Migrated {len(migrated)}/7 risks")

# Verify
print()
print("=== Verification ===")
for r in RISKS[:3]:  # spot-check first 3
    status, resp = api('GET', f'/rest/api/3/issue/{r["key"]}?fields=issuetype,summary,customfield_10819,customfield_10820,customfield_10821,customfield_10823,parent')
    if status == 200:
        f = resp['fields']
        it = f['issuetype']['name']
        pv = f.get(PROB_FIELD, {}).get('value') if f.get(PROB_FIELD) else None
        iv = f.get(IMPACT_FIELD, {}).get('value') if f.get(IMPACT_FIELD) else None
        mv = (f.get(MITIG_FIELD) or '')[:50]
        pil = f.get(PILLAR_FIELD, {}).get('value') if f.get(PILLAR_FIELD) else None
        par = f.get('parent', {}).get('key') if f.get('parent') else None
        print(f"  {r['key']}: type={it} prob={pv} impact={iv} pillar={pil} parent={par} mitigation={mv}...")

with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\risks_migrated.json", 'w', encoding='utf-8') as f:
    json.dump(migrated, f, indent=2, ensure_ascii=False)
