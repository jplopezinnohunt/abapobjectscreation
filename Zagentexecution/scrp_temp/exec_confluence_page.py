"""Create the 'Programme Structure & Tooling Guide' page in Confluence space SA.
Describes the full scaffold: Jira project, releases, components, pillar, meta-epics,
milestones, deliverables, risks, actions — as a single authoritative landing page."""
import json, base64, urllib.request, urllib.error

with open(r'C:\Users\jp_lopez\.claude.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
env = cfg['mcpServers']['confluence']['env']
SITE  = env['ATLASSIAN_SITE_NAME']
EMAIL = env['ATLASSIAN_USER_EMAIL']
TOKEN = env['ATLASSIAN_API_TOKEN']

BASE = f"https://{SITE}.atlassian.net/wiki"
AUTH = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
H = {
    'Authorization': f'Basic {AUTH}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

SPACE_ID    = '1666449410'   # SA space ID
HOMEPAGE_ID = '1666449717'   # parent


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


# Content in Confluence storage format (XHTML-like)
# Uses ac:structured-macro for Jira issue embeds
content = """<h1>SAP Core Redesign Programme — Structure &amp; Tooling Guide</h1>

<p><em>This page documents the Jira and Confluence scaffold that executes the SAP Core Redesign Programme Framework (Version 1.0 — April 2026). Every Jira item referenced here contains verbatim text from the source document. No paraphrasing.</em></p>

<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p><strong>Source document:</strong> <code>SAP_Core_Redesign_Programme_Framework.docx</code> (Version 1.0, April 2026, Internal — Restricted). All milestone, deliverable, risk, and action descriptions in the linked Jira items are verbatim from this document.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h2>1. Programme at a glance</h2>

<table>
<tbody>
<tr><th>Scope</th><td>3-pillar SAP redesign: FM Re-normalisation, PS/WBS Level 4, BP/Grants Management</td></tr>
<tr><th>Duration</th><td>2026 Q2 — 2028 Q4 (anchored to 44 C/5 cycle)</td></tr>
<tr><th>Phases</th><td>P1 Design 2026 · P2 Implementation 2027 · P3 BP/GM 2027-2028</td></tr>
<tr><th>Milestones</th><td>18 (including 2 Go/No-Go gates at M7 and M16)</td></tr>
<tr><th>Deliverables</th><td>21 formal deliverables, each with 2 quality gates</td></tr>
<tr><th>Risks</th><td>7 registered (2 High-High requiring immediate mitigation)</td></tr>
<tr><th>Governance</th><td>Monthly Steering Committee · Weekly Working Groups · PMO (Didem, Francois)</td></tr>
<tr><th>DBS SAP Lead</th><td>Pablo</td></tr>
<tr><th>Pillar leads</th><td>Illya (FM) · Rodolfo (PS/WBS + BP/GM) · Nicolas (ABAP)</td></tr>
</tbody>
</table>

<h2>2. Tooling — verbatim from §7 Documentation &amp; Methodology</h2>

<table>
<tbody>
<tr><th>Tool</th><th>Purpose (verbatim)</th></tr>
<tr><td><strong>Teams</strong></td><td>Channel for communication and programme deliverables</td></tr>
<tr><td><strong>Confluence</strong></td><td>Design and technical documents (reference repository)</td></tr>
<tr><td><strong>JIRA</strong></td><td>2-3 weeks Sprint planning, user stories, UAT and post go-live follow-up</td></tr>
</tbody>
</table>

<p>The SCRP Jira project is configured as <strong>Team-managed Scrum with 2-week sprints</strong>, matching the document's mandate.</p>

<h2>3. Jira project structure</h2>

<p><strong>Project:</strong> <a href="https://unescore.atlassian.net/jira/software/projects/SCRP">SCRP — SAP Core Redesign Programme</a></p>

<h3>3.1 Hierarchy (team-managed Jira flat hierarchy)</h3>

<p>Jira team-managed Scrum has 3 hierarchy levels. SCRP uses them as follows:</p>

<table>
<tbody>
<tr><th>Level</th><th>Issue type</th><th>SCRP usage</th></tr>
<tr><td>1</td><td>Epic</td><td>Milestones (M1-M18) + 4 Pillar Meta-Epics</td></tr>
<tr><td>0</td><td>Task</td><td>Deliverables + Immediate Actions (Week 2-6 kickoff)</td></tr>
<tr><td>0</td><td>Story</td><td>Action Stories from §5 Phase Action Plan (one per bullet)</td></tr>
<tr><td>0</td><td>Risk</td><td>7 Risks from §6 Risk Register (migrated from Task)</td></tr>
<tr><td>0</td><td>Bug</td><td>UAT defects + post go-live issues (empty today)</td></tr>
<tr><td>-1</td><td>Subtask</td><td>Quality gate reviews (Technical Review + Business Review per Deliverable)</td></tr>
</tbody>
</table>

<ac:structured-macro ac:name="note">
  <ac:rich-text-body>
    <p><strong>Meta-Epic limitation:</strong> Jira Standard team-managed does not support Epic-to-Epic parent-child. The 4 Pillar Meta-Epics (SCRP-35, 36, 37, 38) are linked to their Milestone Epics via "Relates" issue links instead of true parenting. They appear as siblings on the Timeline but group cleanly in the "Links" panel on each Meta-Epic detail page.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<h3>3.2 Components — the system/platform register</h3>

<p>Components represent the technical surface area (what system a work item touches). Starting set:</p>

<ul>
<li><strong>FM</strong> — SAP Funds Management module</li>
<li><strong>PS-WBS</strong> — SAP Project System / WBS Level 4</li>
<li><strong>BP-GM</strong> — SAP Business Partner (for GM context)</li>
<li><strong>Governance</strong> — Cross-cutting PMO / Steering Committee (data-only classification)</li>
</ul>

<p>The Components register is expected to grow as the programme touches additional platforms (e.g., <code>Salesforce</code>, <code>CoreManager</code>, <code>SuccessFactors</code>, <code>AN Ariba Network</code>, <code>MuleSoft</code>, <code>BizTalk</code>).</p>

<h3>3.3 Pillar field — programme categorization (fixed)</h3>

<p>The <code>Pillar</code> custom dropdown field (editable on every work type except Subtask) classifies work by programme workstream. Values are fixed and match the framework document §1.2:</p>

<ul>
<li><strong>FM</strong> — Pillar 1 Funds Management Re-normalisation</li>
<li><strong>PS-WBS</strong> — Pillar 2 Project System / WBS Level 4 Implementation</li>
<li><strong>BP-GM</strong> — Pillar 3 Business Partners Redesign / Grants Management Implementation</li>
<li><strong>Governance</strong> — Cross-cutting PMO workstream (not a SAP module)</li>
</ul>

<h3>3.4 Releases (Fix Versions) — phase grouping</h3>

<p>Three Releases represent the 3 phases defined in framework §1.3:</p>

<table>
<tbody>
<tr><th>Release</th><th>Start</th><th>End</th><th>Milestones</th></tr>
<tr><td><a href="https://unescore.atlassian.net/projects/SCRP/versions">P1-Design-2026</a></td><td>2026-04-01</td><td>2026-12-31</td><td>M1-M7</td></tr>
<tr><td><a href="https://unescore.atlassian.net/projects/SCRP/versions">P2-Implementation-2027</a></td><td>2027-04-01</td><td>2027-12-31</td><td>M8-M13</td></tr>
<tr><td><a href="https://unescore.atlassian.net/projects/SCRP/versions">P3-BPGM-2027-2028</a></td><td>2027-07-01</td><td>2028-12-31</td><td>M14-M18</td></tr>
</tbody>
</table>

<p>Progress tracking per phase is via the <a href="https://unescore.atlassian.net/projects/SCRP/versions">Releases page</a>, which shows release burndown, remaining issues, and target date countdown.</p>

<h2>4. Milestones (18)</h2>

<p>All 18 milestones with verbatim text from framework §2 Table 0.</p>

<h3>Phase 1 — Design &amp; Validation (2026)</h3>

<table>
<tbody>
<tr><th>ID</th><th>Milestone</th><th>Owner (verbatim)</th><th>Timeline</th><th>Link</th></tr>
<tr><td>M1</td><td>Programme Governance Setup</td><td>CITO / PMO</td><td>Q2 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-1">SCRP-1</a></td></tr>
<tr><td>M2</td><td>FM Impact Analysis Completed</td><td>DBS (SAP) + FIN + DBM</td><td>Q3 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-2">SCRP-2</a></td></tr>
<tr><td>M3</td><td>FM Sandbox Data Mapping</td><td>DBS (SAP) + FIN + DBM</td><td>Q4 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-3">SCRP-3</a></td></tr>
<tr><td>M4</td><td>PS/WBS Impact Analysis Completed</td><td>DBS (SAP) + FIN + DBM + BSP</td><td>Q3 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-4">SCRP-4</a></td></tr>
<tr><td>M5</td><td>PS/WBS Data Mapping</td><td>DBS (SAP) + FIN + DBM + BSP</td><td>Q4 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-5">SCRP-5</a></td></tr>
<tr><td>M6</td><td>Business Partners Impact Analysis (Donor)</td><td>DBS (SAP) + FIN + DBM + BSP</td><td>Q4 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-6">SCRP-6</a></td></tr>
<tr><td><strong>M7</strong> 🚦</td><td><strong>2026 Design Phase Review (Go/No-Go)</strong></td><td>Steering Committee</td><td>Q4 2026</td><td><a href="https://unescore.atlassian.net/browse/SCRP-7">SCRP-7</a></td></tr>
</tbody>
</table>

<h3>Phase 2 — Implementation &amp; Deployment (2027)</h3>

<table>
<tbody>
<tr><th>ID</th><th>Milestone</th><th>Owner (verbatim)</th><th>Timeline</th><th>Link</th></tr>
<tr><td>M8</td><td>FM Data Harmonisation &amp; Configuration</td><td>DBS (SAP) + FIN + DBM</td><td>Q2 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-8">SCRP-8</a></td></tr>
<tr><td>M9</td><td>PS/WBS Configuration &amp; Testing</td><td>DBS (SAP) + FIN + DBM</td><td>Q2 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-9">SCRP-9</a></td></tr>
<tr><td>M10</td><td>Core Manager Integration Validated</td><td>DBS (EPM) + DBS (SAP)</td><td>Q3 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-10">SCRP-10</a></td></tr>
<tr><td>M11</td><td>User Acceptance Testing (UAT) — FM &amp; PS</td><td>FIN + DBM + DBS</td><td>Q3 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-11">SCRP-11</a></td></tr>
<tr><td>M12</td><td>FM &amp; PS Production Deployment</td><td>DBS (SAP) + CITO/PMO</td><td>Q4 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-12">SCRP-12</a></td></tr>
<tr><td>M13</td><td>Post-Go-Live Stabilisation</td><td>DBS (SAP) + FIN</td><td>Q1 2028</td><td><a href="https://unescore.atlassian.net/browse/SCRP-13">SCRP-13</a></td></tr>
</tbody>
</table>

<h3>Phase 3 — Business Partners &amp; Grants Management (2027-2028)</h3>

<table>
<tbody>
<tr><th>ID</th><th>Milestone</th><th>Owner (verbatim)</th><th>Timeline</th><th>Link</th></tr>
<tr><td>M14</td><td>Business Partners Sandbox Mapping</td><td>DBS (SAP) + FIN + BSP + DBM</td><td>Q3 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-14">SCRP-14</a></td></tr>
<tr><td>M15</td><td>Grants Management business process design</td><td>DBS (SAP) + DBS (EPM) + FIN + DBM + BSP</td><td>Q4 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-15">SCRP-15</a></td></tr>
<tr><td><strong>M16</strong> 🚦</td><td><strong>2027 Grants Management Design Phase Review (Go/No-Go)</strong></td><td>Steering Committee</td><td>Q4 2027</td><td><a href="https://unescore.atlassian.net/browse/SCRP-16">SCRP-16</a></td></tr>
<tr><td>M17</td><td>Grants Management Configuration</td><td>DBS (SAP) + FIN + BSP + DBM</td><td>S1 2028</td><td><a href="https://unescore.atlassian.net/browse/SCRP-17">SCRP-17</a></td></tr>
<tr><td><strong>M18</strong> 🎯</td><td><strong>44 C/5 Readiness Deployment</strong></td><td>DBS (SAP) + DBS (EPM) + CITO/PMO + BSP + DBM + FIN</td><td>S2 2028</td><td><a href="https://unescore.atlassian.net/browse/SCRP-18">SCRP-18</a></td></tr>
</tbody>
</table>

<h2>5. Meta-Epics (4 Pillars)</h2>

<p>Four cross-phase Meta-Epics anchor the verbatim §1.2 pillar descriptions and link to their milestones via "Relates" links.</p>

<ul>
<li><strong><a href="https://unescore.atlassian.net/browse/SCRP-35">SCRP-35</a></strong> — META · PILLAR 1 — Funds Management (FM) Re-normalisation (blue)</li>
<li><strong><a href="https://unescore.atlassian.net/browse/SCRP-36">SCRP-36</a></strong> — META · PILLAR 2 — Project System / WBS Level 4 Implementation (green)</li>
<li><strong><a href="https://unescore.atlassian.net/browse/SCRP-37">SCRP-37</a></strong> — META · PILLAR 3 — Business Partners Redesign / Grants Management (purple)</li>
<li><strong><a href="https://unescore.atlassian.net/browse/SCRP-38">SCRP-38</a></strong> — META · PROGRAMME GOVERNANCE — PMO, Steering Committee, Risk Register (orange)</li>
</ul>

<h2>6. Deliverables (21)</h2>

<p>17 formal deliverables from framework §3 Table 1 plus 4 narrative deliverables from §5 Phase 3 (M14-M18). Each Deliverable is a Task under its parent Milestone Epic with verbatim Content / Producer / Approver.</p>

<p>Every Deliverable has 2 Quality Gate subtasks (Technical Review by DBS SAP lead + Business Review by named business owner) per the §7 mandate:</p>

<ac:structured-macro ac:name="quote">
  <ac:rich-text-body>
    <p>"All deliverables must pass a two-stage quality check before acceptance: Technical review (DBS SAP lead confirms technical correctness and completeness against the acceptance criteria defined in Section 3) and Business review (Named business owner confirms the deliverable reflects actual business requirements and is fit for the next phase). No milestone is marked complete until both reviews are signed off. The PMO maintains the Deliverable Tracker as the authoritative record." — Framework §7 Deliverable Quality Gates</p>
  </ac:rich-text-body>
</ac:structured-macro>

<p><strong>All 21 Deliverables + 42 Quality Gates:</strong> <a href="https://unescore.atlassian.net/issues/?jql=project%20%3D%20SCRP%20AND%20labels%20%3D%20%22deliverable%22">JQL: <code>project = SCRP AND labels = "deliverable"</code></a></p>

<h2>7. Action Stories (37)</h2>

<p>Every bullet from framework §5 Phase Action Plan is a Jira Story, verbatim, with parent = the Milestone Epic it supports. Labeled by team type:</p>

<ul>
<li><code>technical-action</code> — DBS SAP + DBS EPM work</li>
<li><code>business-action</code> — FIN + DBM + BSP work</li>
</ul>

<p><strong>All 37 Action Stories:</strong> <a href="https://unescore.atlassian.net/issues/?jql=project%20%3D%20SCRP%20AND%20labels%20%3D%20%22action-story%22">JQL: <code>project = SCRP AND labels = "action-story"</code></a></p>

<h2>8. Risk Register (7)</h2>

<p>All 7 risks from framework §6 Table 3 are first-class Risk issues (not Tasks) with Probability, Impact, Mitigation, and Assignee fields populated verbatim. Parent = <a href="https://unescore.atlassian.net/browse/SCRP-38">SCRP-38 Governance Meta-Epic</a>.</p>

<table>
<tbody>
<tr><th>ID</th><th>Risk (verbatim)</th><th>Prob</th><th>Impact</th><th>Owner (verbatim)</th></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-19">SCRP-19</a></td><td>FM decoupling breaks existing budget controls in active projects</td><td>Med</td><td>High</td><td>DBS SAP + DBM + FIN</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-20">SCRP-20</a> ⚠️</td><td>ABAP/technical capacity insufficient for parallel delivery</td><td>High</td><td>High</td><td>CITO + DBS</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-21">SCRP-21</a></td><td>Business owners insufficiently available for design workshops and UAT</td><td>Med</td><td>High</td><td>PMO + Sponsors</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-22">SCRP-22</a></td><td>WBS re-modelling disrupts Core Manager ↔ SAP synchronisation</td><td>Med</td><td>High</td><td>DBS SAP + DBS EPM</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-23">SCRP-23</a></td><td>Adoption resistance — inconsistent WBS usage across entities</td><td>Med</td><td>Med</td><td>DBS + DBM + BSP + FIN</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-24">SCRP-24</a></td><td>Data quality issues in vendor/customer master data delay BP migration</td><td>High</td><td>Med</td><td>FIN + BSP + DBS SAP</td></tr>
<tr><td><a href="https://unescore.atlassian.net/browse/SCRP-25">SCRP-25</a></td><td>44 C/5 budget cycle constraints compress deployment window</td><td>Med</td><td>High</td><td>DBS</td></tr>
</tbody>
</table>

<p><strong>⚠️ High-High risks (require immediate mitigation per §6):</strong> SCRP-20 (ABAP capacity)</p>

<p><strong>All Risks JQL:</strong> <a href="https://unescore.atlassian.net/issues/?jql=project%20%3D%20SCRP%20AND%20issuetype%20%3D%20%22Risk%22"><code>project = SCRP AND issuetype = "Risk"</code></a></p>

<h2>9. Immediate Actions — Q2 2026 Kickoff (9)</h2>

<p>9 mobilization actions from framework §8, all due within Weeks 2-6 of Q2 2026. Parent = <a href="https://unescore.atlassian.net/browse/SCRP-1">SCRP-1 M1 Programme Governance Setup</a>.</p>

<p><strong>All Immediate Actions:</strong> <a href="https://unescore.atlassian.net/issues/?jql=project%20%3D%20SCRP%20AND%20labels%20%3D%20%22pmo-action%22"><code>project = SCRP AND labels = "pmo-action"</code></a></p>

<h2>10. How to use this scaffold (for the team)</h2>

<h3>For the PMO (Didem / Francois)</h3>
<ul>
<li>Monthly Steering Committee: open <a href="https://unescore.atlassian.net/projects/SCRP/versions">Releases page</a> → screenshot progress bars → paste into status report</li>
<li>Risk review: filter <code>issuetype = Risk AND status != Done</code> → present in SC meeting</li>
<li>Deliverable tracker: filter <code>labels = deliverable</code> → columns: Summary, Parent, Status, Due, Pillar</li>
</ul>

<h3>For DBS SAP (Pablo, Illya, Rodolfo, Nicolas)</h3>
<ul>
<li>Daily: work the Board, drag cards through To Do → In Progress → Done</li>
<li>Sprint planning: 2-week cadence, cap Story points based on capacity</li>
<li>Deliverable sign-off: transition the Technical Review subtask to Done when complete</li>
</ul>

<h3>For Business Owners (FIN / DBM / BSP counterparts)</h3>
<ul>
<li>Review Business Review subtasks at deliverable milestones</li>
<li>Sign off UAT plan (SCRP-52) at M11 gate</li>
<li>Attend weekly Working Group meetings (invite via Teams)</li>
</ul>

<h3>For the Steering Committee</h3>
<ul>
<li>Monthly review of Releases page (progress %, burndown, overdue)</li>
<li>Go/No-Go gates: M7 (Q4 2026), M16 (Q4 2027) — Design Review Reports auto-collected from related epic</li>
<li>Risk register review embedded monthly (RISK-02 and any new High-High items)</li>
</ul>

<h2>11. Key JQL filters</h2>

<pre><code>## Programme dashboard
project = SCRP AND labels = "milestone"                           → 18 Milestone Epics
project = SCRP AND labels = "meta-epic"                           → 4 Pillar Meta-Epics
project = SCRP AND labels = "deliverable"                         → 21 Deliverables
project = SCRP AND labels = "quality-gate"                        → 42 Quality Gate subtasks
project = SCRP AND labels = "action-story"                        → 37 Action Stories
project = SCRP AND issuetype = "Risk"                             → 7 Risks
project = SCRP AND labels = "pmo-action"                          → 9 Immediate Actions
project = SCRP AND labels = "go-no-go-gate"                       → M7 + M16 gates

## Phase views
project = SCRP AND fixVersion = "P1-Design-2026"                  → Phase 1 work
project = SCRP AND fixVersion = "P2-Implementation-2027"          → Phase 2 work
project = SCRP AND fixVersion = "P3-BPGM-2027-2028"               → Phase 3 work

## Pillar views
project = SCRP AND "Pillar" = "FM"                                → FM pillar
project = SCRP AND "Pillar" = "PS-WBS"                            → PS-WBS pillar
project = SCRP AND "Pillar" = "BP-GM"                             → BP-GM pillar
project = SCRP AND "Pillar" = "Governance"                        → Governance items

## Operational
project = SCRP AND due &lt;= 30d AND statusCategory != Done         → Due next 30 days
project = SCRP AND priority = "Highest" AND statusCategory != Done → Critical items
project = SCRP AND issuetype = "Risk" AND "Probability" = "High" AND "Impact" = "High" → High-High risks
</code></pre>

<h2>12. Verbatim guarantee</h2>

<p><strong>Every description in Jira is copied directly from the framework document.</strong> No paraphrasing, no rewording, no creative additions.</p>

<ul>
<li><strong>Milestone descriptions</strong> → verbatim from §2 Table 0 (ID, Milestone, Key Deliverable, Owner, Timeline)</li>
<li><strong>Deliverable descriptions</strong> → verbatim from §3 Table 1 (Deliverable, Content / What it must include, Producer, Approver) + §5 Phase 3 narrative for M14-M18</li>
<li><strong>Risk descriptions</strong> → verbatim from §6 Table 3 (Risk, Prob, Impact, Owner, Mitigation)</li>
<li><strong>Immediate Action descriptions</strong> → verbatim from §8 Table 5 (#, Action, Owner, Due)</li>
<li><strong>Action Story descriptions</strong> → verbatim from §5 Phase Action Plan bullets</li>
<li><strong>Quality Gate descriptions</strong> → verbatim from §7 Deliverable Quality Gates</li>
<li><strong>Meta-Epic descriptions</strong> → verbatim from §1.2 Three Pillars + §1.3 Approach</li>
</ul>

<p>Every Jira item ends with this attribution:</p>
<blockquote><em>Source: SAP Core Redesign Programme Framework, Version 1.0, April 2026. Verbatim from source document.</em></blockquote>

<h2>13. What's next</h2>

<ul>
<li>Confirm named business owners per pillar (§8 Action #4 — due Week 3)</li>
<li>Hold May Steering Committee meeting and ratify Programme Charter (§8 Action #3)</li>
<li>Begin M2 FM Impact Analysis working sessions with FIN/DBM (§8 Action #7)</li>
<li>Complete RACI with named individuals (§8 Action #8)</li>
<li>Set up dedicated sandbox environment (§8 Action #6)</li>
</ul>

<hr/>

<p><em>Last updated: 2026-04-11. Generated from the SCRP scaffold build. Regenerate by re-running <code>Zagentexecution/scrp_temp/exec_confluence_page.py</code>.</em></p>
"""

# Create the page using Confluence v2 API
body = {
    'spaceId': SPACE_ID,
    'status': 'current',
    'title': 'Programme Structure & Tooling Guide — SCRP Scaffold',
    'parentId': HOMEPAGE_ID,
    'body': {
        'representation': 'storage',
        'value': content,
    }
}

print("=== Creating Confluence page ===")
status, resp = api('POST', '/api/v2/pages', body)
if status in (200, 201):
    print(f"  SUCCESS")
    print(f"  id: {resp.get('id')}")
    print(f"  title: {resp.get('title')}")
    print(f"  url: https://unescore.atlassian.net/wiki/spaces/SA/pages/{resp.get('id')}")
    with open(r"C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\scrp_temp\confluence_page.json", 'w', encoding='utf-8') as f:
        json.dump({'id': resp.get('id'), 'title': resp.get('title'), 'url': f"https://unescore.atlassian.net/wiki/spaces/SA/pages/{resp.get('id')}"}, f, indent=2)
else:
    print(f"  FAIL {status}")
    print(f"  Body: {resp.get('error', '')[:1500]}")
