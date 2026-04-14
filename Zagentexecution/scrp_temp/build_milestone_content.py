"""
Builds verbatim content map for 18 SCRP milestones from parsed framework doc.
ZERO paraphrasing — every description word comes from the source document.
"""
import json
import os

PARSED = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\scrp_doc_parsed.json"
OUT = r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\milestones_content.json"

with open(PARSED, 'r', encoding='utf-8') as f:
    d = json.load(f)

# Milestone rows from Table 0 (skip header)
milestones_table = d['tables'][0][1:]

# Deliverables rows from Table 1 (skip header)
deliverables_table = d['tables'][1][1:]

# Map Table 1 deliverable name -> row
deliv_map = {row[0]: {'content': row[1], 'producer': row[2], 'approver': row[3] if len(row) > 3 else ''} for row in deliverables_table}

# Quarter → (start, end)
def quarter_dates(q):
    q = q.strip()
    if 'Q1 2026' in q: return ('2026-01-01', '2026-03-31')
    if 'Q2 2026' in q: return ('2026-04-01', '2026-06-30')
    if 'Q3 2026' in q: return ('2026-07-01', '2026-09-30')
    if 'Q4 2026' in q: return ('2026-10-01', '2026-12-31')
    if 'Q1 2027' in q: return ('2027-01-01', '2027-03-31')
    if 'Q2 2027' in q: return ('2027-04-01', '2027-06-30')
    if 'Q3 2027' in q: return ('2027-07-01', '2027-09-30')
    if 'Q4 2027' in q: return ('2027-10-01', '2027-12-31')
    if 'Q1 2028' in q: return ('2028-01-01', '2028-03-31')
    if 'S1 2028' in q: return ('2028-01-01', '2028-06-30')
    if 'S2 2028' in q: return ('2028-07-01', '2028-12-31')
    return (None, None)

# Phase assignment per framework §5
def phase_of(mid):
    n = int(mid.replace('M', ''))
    if 1 <= n <= 7:
        return ('phase-1-design-2026', 'Phase 1 — Design & Validation (2026)')
    if 8 <= n <= 13:
        return ('phase-2-impl-2027', 'Phase 2 — Implementation & Deployment (2027)')
    return ('phase-3-bpgm-2028', 'Phase 3 — Business Partners & Grants Management (2028)')

# Pillar component assignment (using component NAMES to match created components)
PILLAR_MAP = {
    'M1':  ['Governance'],
    'M2':  ['FM'],
    'M3':  ['FM'],
    'M4':  ['PS-WBS'],
    'M5':  ['PS-WBS'],
    'M6':  ['BP-GM'],
    'M7':  ['Governance'],                  # Go/No-Go gate
    'M8':  ['FM'],
    'M9':  ['PS-WBS'],
    'M10': ['PS-WBS', 'FM'],                # Core Manager integration (both FM and PS sync)
    'M11': ['FM', 'PS-WBS'],                # Joint UAT
    'M12': ['FM', 'PS-WBS'],                # Joint deployment
    'M13': ['FM', 'PS-WBS'],                # Post-go-live stabilisation
    'M14': ['BP-GM'],
    'M15': ['BP-GM'],
    'M16': ['Governance'],                  # GM Go/No-Go gate
    'M17': ['BP-GM'],
    'M18': ['FM', 'PS-WBS', 'BP-GM', 'Governance'],  # 44 C/5 full deployment
}

# Deliverable name(s) per milestone (key into deliv_map above)
DELIV_MAP = {
    'M1':  ['Programme Charter', 'RACI Matrix', 'Risk & Issue Register', 'Steering Committee TOR'],
    'M2':  ['FM Gap Analysis Report & Design'],
    'M3':  ['FM Sandbox Mapping Document'],
    'M4':  ['WBS Re-Modelling Report & Design'],
    'M5':  ['WBS Sample Mapping Document'],
    'M6':  ['Business Partner Typology Document'],
    'M7':  ['Phase 1 Design Review Report'],
    'M8':  ['FM Configuration Document'],
    'M9':  ['PS/WBS Configuration Document'],
    'M10': ['Integration Test Report (Core Manager)'],
    'M11': ['UAT Plan & Sign-off Document'],
    'M12': ['Cutover & Migration Plan', 'Training Materials'],
    'M13': ['Post Go-Live Hypercare Report'],
    'M14': [],  # Not explicitly in Table 1 — BP Typology (M6) extends into sandbox mapping
    'M15': [],  # Not in Table 1 — GM process design is covered narratively in §5 Phase 3
    'M16': [],  # Gate — no dedicated deliverable row
    'M17': [],  # Not in Table 1 — GM configuration, covered in §5 Phase 3
    'M18': [],  # Not in Table 1 — 44 C/5 readiness, covered in §5 Phase 3
}

# Extract §5 Phase Action Plan bullets with phase/team context
sections = d['sections']
action_bullets = []  # list of (h1, h2, h3, text)
for s in sections:
    if s.get('h1') and '5. Phased Action Plan' in s['h1'] and s['style'] == 'List Paragraph':
        action_bullets.append({
            'phase': s.get('h2', ''),
            'team': s.get('h3', ''),
            'text': s['text']
        })

# Keyword → milestone matching for action bullets (kept narrow, verbatim-preserving)
# Each action bullet goes under the milestone(s) whose scope it describes.
# We search by keyword fingerprint; if no match, the bullet stays only in Phase Action Plan section, not under any specific epic.
def match_actions(mid):
    key = mid
    matches = []
    for b in action_bullets:
        t = b['text'].lower()
        if mid == 'M1':
            if any(k in t for k in ['sandbox environment', 'named business owners', 'provide named business']):
                matches.append(b)
        elif mid == 'M2':
            if 'fm impact analysis' in t or 'as-is fm configuration' in t or 'co-author fm to-be' in t:
                matches.append(b)
        elif mid == 'M3':
            if 'fm sandbox data mapping' in t or 'validate fm sandbox' in t:
                matches.append(b)
        elif mid == 'M4':
            if 'as-is wbs' in t or 'ps/wbs impact analysis' in t or 'co-author ps/wbs to-be' in t:
                matches.append(b)
        elif mid == 'M5':
            if 'wbs sample mappings' in t or 'identify pilots for wbs sandbox' in t or 'validate wbs sample mappings' in t:
                matches.append(b)
        elif mid == 'M6':
            if 'customer (business partner) configuration' in t or 'provide vendor/customer/donor master data' in t:
                matches.append(b)
        elif mid == 'M7':
            if 'design review report' in t or 'go/no-go steering committee' in t:
                matches.append(b)
        elif mid == 'M8':
            if 'build fm configuration' in t or 'promote fm configuration' in t:
                matches.append(b)
        elif mid == 'M9':
            if 'build ps/wbs level 4 configuration' in t:
                matches.append(b)
        elif mid == 'M10':
            if 'integration test suite' in t:
                matches.append(b)
        elif mid == 'M11':
            if 'support uat' in t or 'lead uat' in t or 'provide formal uat sign-off' in t:
                matches.append(b)
        elif mid == 'M12':
            if 'cutover plan' in t or 'production deployment' in t or 'prepare memos' in t or 'train finance and programme' in t:
                matches.append(b)
        elif mid == 'M13':
            if 'support post go-live stabilisation' in t or 'hypercare support' in t:
                matches.append(b)
        elif mid == 'M14':
            if 'configure bp typologies in sandbox' in t or 'validate bp typology definitions' in t:
                matches.append(b)
        elif mid == 'M15':
            if 'design and validate grants management' in t:
                matches.append(b)
        elif mid == 'M17':
            if 'configure grants management module' in t or 'implement gm <> core manager' in t:
                matches.append(b)
        elif mid == 'M18':
            if 'execute bp data migration' in t or 'support gm uat' in t:
                matches.append(b)
    return matches

# Build content for each milestone
out = []
for row in milestones_table:
    mid, mname, deliv, owner, timeline = row[0], row[1], row[2], row[3], row[4]
    start, due = quarter_dates(timeline)
    phase_label, phase_full = phase_of(mid)
    pillars = PILLAR_MAP[mid]
    deliv_names = DELIV_MAP[mid]

    # Build verbatim deliverable details
    deliv_details = []
    for dn in deliv_names:
        if dn in deliv_map:
            dv = deliv_map[dn]
            deliv_details.append({
                'name': dn,
                'content': dv['content'],
                'producer': dv['producer'],
                'approver': dv['approver']
            })

    actions = match_actions(mid)

    # Build markdown description — all verbatim from document
    parts = []
    parts.append(f"# {mid} — {mname}")
    parts.append("")
    parts.append(f"**Phase:** {phase_full}")
    parts.append(f"**Pillar:** {', '.join(pillars)}")
    parts.append(f"**Quarter (from Table 0):** {timeline}")
    parts.append(f"**Owner (from Table 0):** {owner}")
    parts.append("")
    parts.append("## Key Deliverable (verbatim from §2 Table 0)")
    parts.append(f"> {deliv}")
    parts.append("")
    if deliv_details:
        parts.append("## Deliverable Content (verbatim from §3 Table 1)")
        for dd in deliv_details:
            parts.append(f"### {dd['name']}")
            parts.append(f"**Content / What it must include:** {dd['content']}")
            parts.append(f"**Producer:** {dd['producer']}")
            parts.append(f"**Approver:** {dd['approver']}")
            parts.append("")
    if actions:
        parts.append("## Related actions (verbatim from §5 Phased Action Plan)")
        for a in actions:
            parts.append(f"- *{a['team']}* — {a['text']}")
        parts.append("")
    parts.append("---")
    parts.append("*Source: SAP Core Redesign Programme Framework, Version 1.0, April 2026. All text above is verbatim from the source document — no paraphrasing.*")

    description = "\n".join(parts)

    labels = ['milestone', phase_label]
    if 'Go/No-Go' in mname or 'Go/No-Go' in deliv:
        labels.append('go-no-go-gate')

    out.append({
        'id': mid,
        'name': mname,
        'summary': f"{mid} · {mname}",
        'description': description,
        'start_date': start,
        'due_date': due,
        'labels': labels,
        'components': pillars,
        'phase_label': phase_label,
        'phase_full': phase_full,
        'timeline': timeline,
        'owner': owner,
        'key_deliverable_verbatim': deliv,
        'deliverable_details': deliv_details,
        'actions': actions,
    })

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Built content for {len(out)} milestones → {OUT}")
print()
print("=== PREVIEW: M1 ===")
print(out[0]['description'])
print()
print("=== SUMMARY ===")
for m in out:
    print(f"  {m['id']}: {m['start_date']} → {m['due_date']} | {'+'.join(m['components'])} | {len(m['deliverable_details'])} deliv | {len(m['actions'])} actions")
