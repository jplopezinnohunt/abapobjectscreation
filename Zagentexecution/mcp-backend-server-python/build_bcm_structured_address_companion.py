"""Build companions/BCM_StructuredAddressChange.html v1.

Single-file HTML companion (dark theme, tab navigation) for the UNESCO BCM
Structured Address migration project. Generated from Phase 0 deliverables.

Tabs:
 1  Overview
 2  The Plan (live)
 3  Reference Architecture
 4  The 3 Trees
 5  Change Matrix
 6  XML Before/After
 7  SAP Architecture
 8  Code Inventory (100%)
 9  User Exit
10  Test Matrix
11  Transport Plan
12  Francesco Audit
13  Vendor Master DQ
14  Q1-Q8 Status
15  Timeline
16  References
"""
from __future__ import annotations
import csv, sys
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "companions" / "BCM_StructuredAddressChange.html"
PHASE0 = REPO / "knowledge" / "domains" / "Payment" / "phase0"
PLAN_FILE = Path(r"C:/Users/jp_lopez/.claude/plans/revisa-nuevamente-todo-hay-parsed-scone.md")

VERSION = "v1.0"
BUILD_TS = datetime.now().strftime("%Y-%m-%d %H:%M")


def load_plan() -> str:
    if PLAN_FILE.exists():
        return PLAN_FILE.read_text(encoding="utf-8")
    return "(plan file not found)"


def load_csv(path: Path, limit: int = 200):
    if not path.exists():
        return None, []
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = list(r)
    return (list(rows[0].keys()) if rows else []), rows[:limit]


def md_to_html_table(md_path: Path) -> str:
    """Very simple markdown renderer - enough to show tables and paragraphs."""
    if not md_path.exists():
        return f"<em>File not found: {md_path}</em>"
    text = md_path.read_text(encoding="utf-8")
    # Convert code fences to <pre>
    out = []
    in_code = False
    in_tbl = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            out.append("<pre>" if in_code else "</pre>")
            continue
        if in_code:
            out.append(esc(line))
            continue
        if line.startswith("# "):
            out.append(f"<h2>{esc(line[2:])}</h2>")
        elif line.startswith("## "):
            out.append(f"<h3>{esc(line[3:])}</h3>")
        elif line.startswith("### "):
            out.append(f"<h4>{esc(line[4:])}</h4>")
        elif line.startswith("|"):
            if not in_tbl:
                out.append("<table>")
                in_tbl = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            tag = "th" if not out[-1].startswith("<tr>") else "td"
            out.append("<tr>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in cells) + "</tr>")
        else:
            if in_tbl:
                out.append("</table>")
                in_tbl = False
            if line.strip():
                out.append(f"<p>{esc(line)}</p>")
    if in_tbl:
        out.append("</table>")
    return "\n".join(out)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_table(headers, rows, limit=50):
    if not rows:
        return "<p><em>No data</em></p>"
    html = ["<table>"]
    html.append("<tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr>")
    for r in rows[:limit]:
        html.append("<tr>" + "".join(f"<td>{esc(str(r.get(h, '')))}</td>" for h in headers) + "</tr>")
    if len(rows) > limit:
        html.append(f"<tr><td colspan='{len(headers)}'><em>... showing first {limit} of {len(rows)} rows</em></td></tr>")
    html.append("</table>")
    return "\n".join(html)


# ===== Build per-tab content =====

def tab_overview():
    return """
    <div class="section">
      <h3>Why this change</h3>
      <p><strong>Bank-driven + CBPR+ Nov 2026 mandate</strong>. Banks will reject XML payment files with only unstructured <code>&lt;AdrLine&gt;</code> addresses starting November 2026 (ISO 20022 CBPR+).</p>
      <p>UNESCO runs <strong>3 custom DMEE trees</strong> in P01 that emit Hybrid or Unstructured addresses today. The migration must ensure at least <code>&lt;TwnNm&gt;</code> + <code>&lt;Ctry&gt;</code> (mandatory) and preferably full 5-tag structured PstlAdr.</p>
      <h3>Compliance states (3 states, not 2) — for context only</h3>
      <table>
        <tr><th>State</th><th>Validity after Nov 2026</th><th>UNESCO position</th></tr>
        <tr><td>Unstructured (AdrLine only)</td><td>REJECTED</td><td>Current V000 state, migrate away</td></tr>
        <tr><td>Hybrid (TwnNm+Ctry + AdrLine mixed)</td><td>OK — minimum viable</td><td><strong>Rejected as default</strong> — mixes legacy+new in one file; rollback + bank validation harder. Kept as fallback if V001 fails bank acceptance on specific vendors.</td></tr>
        <tr><td>Fully structured (5 tags)</td><td>OK + future-proof</td><td><strong>OUR TARGET (V001)</strong> — clean file, future-proof, DMEE-native versioning enables parallel V000/V001 operation + atomic cutover</td></tr>
      </table>
      <h3>Coexistence strategy — 2-file + DMEE native versioning (user-directed)</h3>
      <p>Instead of mixing structured+AdrLine in one file (Hybrid), we keep V000 (current, unstructured/hybrid) and V001 (new, fully structured) as <strong>TWO SEPARATE DMEE versions</strong> of each tree. SAP DMEE supports this natively via <code>DMEE_TREE_NODE.VERSION</code> column.</p>
      <ul>
        <li><strong>During Phase 2-4</strong>: V000 stays ACTIVE (prod), V001 INACTIVE. Z-payment method routes test F110 to V001 only → parallel files generated for bank validation via test gateway.</li>
        <li><strong>At cutover (Phase 5)</strong>: atomic deactivate V000 / activate V001 in D01 → transport to P01. All F110 now produce V001 structured files.</li>
        <li><strong>Rollback</strong>: flip activation back to V000 — instant, data-safe, no file corruption risk.</li>
        <li><strong>After 30 days stable</strong>: decommission V000.</li>
      </ul>
      <p>This is SAP-native. Each DMEE_TREE_NODE row carries its own VERSION — V000's nodes are untouched while V001 is edited. The BAdI <code>FI_CGI_DMEE_EXIT_W_BADI</code> fires on the ACTIVE version's nodes — SAP auto-traverses the right version. <strong>Stateful BAdI logic must be structure-aware</strong> (see <em>User Exit</em> tab — Pattern A fix for <code>YCL_IDFI_CGI_DMEE_FALLBACK_CM001</code> name-overflow-into-StrtNm guard).</p>
      <h3>Key people</h3>
      <ul>
        <li><strong>Marlies Spronk (M_SPRONK)</strong> — Treasury, business owner AND historical DMEE config author (31 transports 2017-2024)</li>
        <li><strong>Pablo Lopez (JP_LOPEZ)</strong> — SAP config + coordination</li>
        <li><strong>Nicolas Ménard (N_MENARD)</strong> — BAdI code owner (9 transports 2024), required reviewer for ABAP changes</li>
        <li><strong>Francesco Spezzano (FP_SPEZZANO)</strong> — 5 PMF variant transports 2025 Q1 (ASSIST/IRRELEVANT), not address-related</li>
        <li><strong>DBS</strong> — business implementation + testing</li>
      </ul>
      <h3>Timeline</h3>
      <table>
        <tr><th>Phase</th><th>Window</th><th>Status</th></tr>
        <tr><td>0 — 100% Code Inventory</td><td>2026-04-24 → 04-27</td><td><strong>IN EXECUTION</strong> (this companion)</td></tr>
        <tr><td>1 — Config matrix + bank specs</td><td>2026-04-27 → 04-30</td><td>Pending Phase 0 close</td></tr>
        <tr><td>2 — Config D01 (SEPA → CITI → CGI)</td><td>May 2026</td><td>Pending</td></tr>
        <tr><td>3 — Unit Test D01/V01</td><td>June 2026</td><td>Pending</td></tr>
        <tr><td>4 — UAT V01</td><td>July 2026</td><td>Pending</td></tr>
        <tr><td>5 — Deploy P01</td><td>Aug-Nov 2026</td><td>Pending — CBPR+ hard deadline</td></tr>
      </table>
    </div>
    """


def tab_plan():
    plan = load_plan()
    return f"""
    <div class="section">
      <h3>The Plan (live) — rendered from plan file</h3>
      <p><em>Source: <code>C:/Users/jp_lopez/.claude/plans/revisa-nuevamente-todo-hay-parsed-scone.md</code> · Last rebuilt: {BUILD_TS} · Companion version: {VERSION}</em></p>
      <div style="background:#0c1926;padding:16px;border-radius:8px;border:1px solid #1e3a4a;max-height:700px;overflow-y:scroll;white-space:pre-wrap;font-family:'Segoe UI',sans-serif;font-size:12px;line-height:1.5">
        {esc(plan)}
      </div>
    </div>
    """


def tab_ref_arch():
    return """
    <div class="section">
      <h3>Reference architecture — from UNESCO_BCM_StructuredAddress_AgentHandoff.docx v1.0</h3>
      <h4>3 compliance states</h4>
      <table>
        <tr><th>State</th><th>Example</th><th>Valid post Nov 2026</th></tr>
        <tr><td>Unstructured</td><td><code>&lt;AdrLine&gt;...&lt;/AdrLine&gt;&lt;Ctry&gt;FR&lt;/Ctry&gt;</code></td><td>REJECTED</td></tr>
        <tr><td>Hybrid</td><td><code>&lt;TwnNm&gt;Paris&lt;/TwnNm&gt;&lt;Ctry&gt;FR&lt;/Ctry&gt;&lt;AdrLine&gt;...&lt;/AdrLine&gt;</code></td><td>OK (TwnNm+Ctry only mandatory)</td></tr>
        <tr><td>Fully Structured</td><td><code>&lt;StrtNm&gt;&lt;BldgNb&gt;&lt;PstCd&gt;&lt;TwnNm&gt;&lt;Ctry&gt;</code></td><td>OK + future-proof</td></tr>
      </table>
      <h4>3 asymmetric technical patterns by XML party</h4>
      <table>
        <tr><th>Party</th><th>Data source</th><th>Change mechanism</th></tr>
        <tr><td>Cdtr (vendor)</td><td>SAP-standard populates FPAYHX from LFA1+ADRC</td><td>DMEE tree config only, no ABAP</td></tr>
        <tr><td>Dbtr (UNESCO)</td><td>NOT in FPAYHX/FPAYH</td><td>NEW user exit Z_DMEE_UNESCO_DEBTOR_ADDR + OBPM4 Event 05 + FPAYHX-ZREF01..05 (CORRECTED from handoff doc's FPAYH-REF)</td></tr>
        <tr><td>UltmtCdtr (Worldlink)</td><td>UNKNOWN (handoff Q3)</td><td>BLOCKED until data source resolved</td></tr>
      </table>
      <h4>17-step checklist (Phase 2 execution, from handoff §9)</h4>
      <p>Adopted verbatim. See <strong>Tab 11 — Transport Plan</strong> for TRKORR tracking.</p>
      <h4>Reference SAP Notes</h4>
      <ol>
        <li><strong>1665873</strong> — CGI_XML_CT full introduction guide (59 pages, canonical)</li>
        <li>2795667 — ISO 20022 adoption / SEPA harmonization</li>
        <li>2668719 — PMW format lifecycle</li>
        <li>2819590 — Structured remittance in CGI XML (check applicability)</li>
        <li>2845063 — CGI IDs config</li>
      </ol>
    </div>
    """


def tab_three_trees():
    return """
    <div class="section">
      <h3>The 3 target DMEE trees (+ 1 twin)</h3>
      <table>
        <tr><th>Tree (P01)</th><th>Nodes</th><th>Address+party nodes</th><th>Marlies Excel state</th><th>Change scope</th></tr>
        <tr>
          <td><code>/SEPA_CT_UNES</code></td><td>95</td><td>15</td>
          <td>Dbtr Hybrid (Ctry+AdrLine PARIS only), Cdtr Hybrid (Ctry+2xAdrLine) — postal code missing</td>
          <td><strong>P1 — structure Dbtr+Cdtr full</strong>, keep AdrLine as Hybrid fallback</td>
        </tr>
        <tr>
          <td><code>/CITI/XML/UNESCO/DC_V3_01</code></td><td>610</td><td>83</td>
          <td>Dbtr Unstructured (AdrLine only, some cases no Ctry!), Cdtr mostly OK, CdtrAgt OK, UltmtCdtr WHO/ICC Hybrid</td>
          <td><strong>P1 — fix Dbtr Ctry + structure</strong>; UltmtCdtr <strong>BLOCKED by Q3</strong> Worldlink data source</td>
        </tr>
        <tr>
          <td><code>/CGI_XML_CT_UNESCO</code> + <code>_1</code></td><td>631+639</td><td>124+132</td>
          <td>Dbtr Structured OK (TEMPLATE), Cdtr Structured OK, <strong>CdtrAgt Unstructured</strong></td>
          <td><strong>P2 — fix CdtrAgt only</strong>, Dbtr/Cdtr kept</td>
        </tr>
      </table>
      <p><em>Source: Marlies Spronk Excel "XML Address un structured.xlsx" 10 real production cases + Session #039 H18 P01 baseline + Phase 0 Finding F (2026-04-24).</em></p>
    </div>
    """


def tab_change_matrix():
    cols, rows = load_csv(PHASE0 / "gap006_dmee_nodes_with_exit.csv", limit=80)
    return f"""
    <div class="section">
      <h3>Change Matrix — derived from DMEE tree probe (P01 2026-04-24)</h3>
      <p><strong>{len(rows) if rows else 0}</strong> nodes shown (of 1,975 total in 4 target trees). Full CSV: <code>knowledge/domains/Payment/phase0/gap006_dmee_nodes_with_exit.csv</code></p>
      {render_table(cols, rows, limit=80) if cols else '<em>CSV not available</em>'}
      <p><em>Phase 1 will expand this into a full change_matrix.csv with target state + action + transport + test status per node.</em></p>
    </div>
    """


def tab_before_after():
    return """
    <div class="section">
      <h3>XML Before/After — from handoff doc §2.1 + Marlies Excel Tab 2</h3>
      <h4>BEFORE — Unstructured (current SEPA/CITI, rejected Nov 2026)</h4>
      <pre>&lt;PstlAdr&gt;
  &lt;AdrLine&gt;123 Main Street, Paris 75001&lt;/AdrLine&gt;
  &lt;Ctry&gt;FR&lt;/Ctry&gt;
&lt;/PstlAdr&gt;</pre>
      <h4>HYBRID — minimum viable (TwnNm+Ctry mandatory)</h4>
      <pre>&lt;PstlAdr&gt;
  &lt;TwnNm&gt;Paris&lt;/TwnNm&gt;
  &lt;Ctry&gt;FR&lt;/Ctry&gt;
  &lt;AdrLine&gt;123 Main Street&lt;/AdrLine&gt;
&lt;/PstlAdr&gt;</pre>
      <h4>AFTER — Fully structured (preferred, already in CGI for UNESCO Dbtr)</h4>
      <pre>&lt;PstlAdr&gt;
  &lt;StrtNm&gt;Place de Fontenoy&lt;/StrtNm&gt;
  &lt;BldgNb&gt;7&lt;/BldgNb&gt;
  &lt;PstCd&gt;75007&lt;/PstCd&gt;
  &lt;TwnNm&gt;PARIS&lt;/TwnNm&gt;
  &lt;Ctry&gt;FR&lt;/Ctry&gt;
&lt;/PstlAdr&gt;</pre>
    </div>
    """


def tab_sap_arch():
    return """
    <div class="section">
      <h3>SAP architecture — Payment file generation E2E</h3>
      <pre>F110 (Automatic Payment Run)
  │
  ▼
FBZP Configuration (Payment method → House bank → PMW format)
  │
  ▼
OBPM1 (Payment Medium Format → DMEE tree mapping)
  │
  ▼
DMEE Engine (tree traversal, reads FPAYHX / FPAYH / FPAYP)
  │         ├── MP_SC_TAB/MP_SC_FLD = direct table-field read
  │         ├── MP_CONST = constant value
  │         └── MP_EXIT_FUNC = call BAdI / FM (794 nodes in our 4 trees)
  │
  ▼
BAdI FI_CGI_DMEE_EXIT_W_BADI → dispatch by country to:
  │         ├── YCL_IDFI_CGI_DMEE_FR    (France)
  │         ├── YCL_IDFI_CGI_DMEE_DE    (Germany, P01-only)
  │         ├── YCL_IDFI_CGI_DMEE_IT    (Italy, P01-only)
  │         └── YCL_IDFI_CGI_DMEE_FALLBACK (default)
  ▼
XML output file written to \\\\hq-sapitf\\SWIFT$\\P01\\input\\
  │
  ▼
BCM (Bank Communication Management — Claim #65: 100% routed via OBPM5/TFIBLMPAYBLOCK)
  │
  ▼
Workflow 90000003 (dual-control approval, signatories from PD OTYPE='RY')
  │
  ▼
SWIFT / Alliance Lite2 → Bank gateway
  │
  ▼
Bank schema validation (pain.001.001.09 XSD + bank-specific rules)</pre>
    </div>
    """


def tab_code_inventory():
    gc = PHASE0 / "xml_touch_points_complete.md"
    return f"""
    <div class="section">
      <h3>Code Inventory (100%) — xml_touch_points_complete.md rendered</h3>
      {md_to_html_table(gc)}
    </div>
    """


def tab_user_exit():
    return """
    <div class="section">
      <h3>User Exit — Z_DMEE_UNESCO_DEBTOR_ADDR (to be created Phase 2 Step 9)</h3>
      <p><strong>[CORRECTED from handoff doc]</strong>: writes to <code>E_FPAYHX-ZREF01..ZREF05</code>, not <code>FPAYH-REF01..05</code>. FPAYH has zero REF fields (Phase 0 Finding E). FPAYHX has ZREF01..ZREF10 customer buffers (10 available, 5 needed for address).</p>
      <h4>FM signature (revised)</h4>
      <pre>FUNCTION z_dmee_unesco_debtor_addr.
*"----------------------------------------------------------------------
*"  IMPORTING
*"     VALUE(I_FPAYH) TYPE  FPAYH
*"     VALUE(I_FPAYP) TYPE  FPAYP
*"  CHANGING
*"     VALUE(CS_FPAYHX) TYPE  FPAYHX
*"----------------------------------------------------------------------
* Populate UNESCO debtor address fields from T001 company code ADRNR → ADRC
* Writes to FPAYHX-ZREF01..ZREF05 buffer fields for DMEE tree consumption.
* Called via OBPM4 Event 05, registered for all 3 PMW formats.
*----------------------------------------------------------------------
  DATA: ls_t001 TYPE t001,
        ls_adrc TYPE adrc.

  SELECT SINGLE adrnr, bukrs INTO @DATA(lv_adrnr)
    FROM t001 WHERE bukrs = @i_fpayh-zbukr.
  IF sy-subrc NE 0. RETURN. ENDIF.

  SELECT SINGLE * INTO @ls_adrc
    FROM adrc WHERE addrnumber = @lv_adrnr
              AND   date_from <= @sy-datum
              AND   nation    = @space.
  IF sy-subrc NE 0. RETURN. ENDIF.

  cs_fpayhx-zref01 = ls_adrc-street.       " StrtNm
  cs_fpayhx-zref02 = ls_adrc-house_num1.   " BldgNb
  cs_fpayhx-zref03 = ls_adrc-post_code1.   " PstCd
  cs_fpayhx-zref04 = ls_adrc-city1.        " TwnNm
  cs_fpayhx-zref05 = ls_adrc-country.      " Ctry
ENDFUNCTION.</pre>
      <h4>DMEE tree nodes for Dbtr (new nodes, point to REF buffers)</h4>
      <pre>Node: &lt;PmtInf&gt;&lt;Dbtr&gt;&lt;PstlAdr&gt;&lt;StrtNm&gt;
  Source: Field — FPAYHX-ZREF01
Node: &lt;PmtInf&gt;&lt;Dbtr&gt;&lt;PstlAdr&gt;&lt;BldgNb&gt;
  Source: Field — FPAYHX-ZREF02
Node: &lt;PmtInf&gt;&lt;Dbtr&gt;&lt;PstlAdr&gt;&lt;PstCd&gt;
  Source: Field — FPAYHX-ZREF03
Node: &lt;PmtInf&gt;&lt;Dbtr&gt;&lt;PstlAdr&gt;&lt;TwnNm&gt;
  Source: Field — FPAYHX-ZREF04  (mandatory)
Node: &lt;PmtInf&gt;&lt;Dbtr&gt;&lt;PstlAdr&gt;&lt;Ctry&gt;
  Source: Field — FPAYHX-ZREF05  (mandatory)</pre>
      <h4>Reviewer</h4>
      <p><strong>N_MENARD</strong> (BAdI code owner per Phase 0 Finding C — 9 DMEE class transports 2024). Required code review for Phase 2 Step 9.</p>
    </div>
    """


def tab_test_matrix():
    return """
    <div class="section">
      <h3>Test Matrix — from handoff doc §8.1 (UT) + §8.2 (UAT) + data-driven anchors</h3>
      <h4>Unit Test scenarios (June 2026 — Phase 3)</h4>
      <table>
        <tr><th>#</th><th>Scenario</th><th>Format</th><th>Pass criteria</th></tr>
        <tr><td>UT-01</td><td>SEPA vendor with full address</td><td>SEPA</td><td>All 5 structured tags present, no AdrLine (if fully-structured target)</td></tr>
        <tr><td>UT-02</td><td>SEPA vendor with city+country only (Hybrid min)</td><td>SEPA</td><td>TwnNm+Ctry populated, file generated without error</td></tr>
        <tr><td>UT-03</td><td>SEPA vendor missing city (ORT1 blank)</td><td>SEPA</td><td>Hybrid falls back to AdrLine; no empty TwnNm tag</td></tr>
        <tr><td>UT-04</td><td>CITI USD vendor with full address</td><td>CITI</td><td>Cdtr PstlAdr fully structured</td></tr>
        <tr><td>UT-05</td><td>CITI Worldlink TND UltmtCdtr structured</td><td>CITI</td><td>BLOCKED by Q3 until data source resolved</td></tr>
        <tr><td>UT-06</td><td>CGI non-EUR, non-USD currency payment</td><td>CGI</td><td>Structured Dbtr kept; CdtrAgt fix verified</td></tr>
        <tr><td>UT-07</td><td>Debtor (UNESCO) address via user exit — all formats</td><td>All</td><td>FPAYHX-ZREF01..05 populated; structured Dbtr in XML</td></tr>
        <tr><td>UT-08</td><td>Mixed payment run (some vendors missing postal)</td><td>All</td><td>XSD valid at file level; Hybrid fallback per vendor</td></tr>
      </table>
      <h4>UAT scenarios (July 2026 — Phase 4)</h4>
      <table>
        <tr><th>#</th><th>Scenario</th><th>Format</th><th>Validator</th></tr>
        <tr><td>UAT-01</td><td>EUR salary/vendor via SocGen monthly</td><td>SEPA</td><td>Finance/Treasury</td></tr>
        <tr><td>UAT-02</td><td>USD payment to international vendor</td><td>CITI</td><td>Finance/Treasury</td></tr>
        <tr><td>UAT-03</td><td>Worldlink TND (Tunisia staff)</td><td>CITI Worldlink</td><td>HRM/Treasury</td></tr>
        <tr><td>UAT-04</td><td>Worldlink MGA (Madagascar staff)</td><td>CITI Worldlink</td><td>HRM/Treasury</td></tr>
        <tr><td>UAT-05</td><td>Local UBO Brazil payment</td><td>CITI</td><td>UBO Finance</td></tr>
        <tr><td>UAT-06</td><td>Local UIS payment</td><td>CITI</td><td>UIS Finance</td></tr>
        <tr><td>UAT-07</td><td>EUR via CGI non-SocGen bank</td><td>CGI</td><td>Finance</td></tr>
        <tr><td>UAT-08</td><td>Multi-currency batch</td><td>All</td><td>Treasury</td></tr>
        <tr><td>UAT-09</td><td>IIEP payment SEPA</td><td>SEPA</td><td>IIEP Finance</td></tr>
        <tr><td>UAT-10</td><td>UIL payment SEPA</td><td>SEPA</td><td>UIL Finance</td></tr>
        <tr><td>UAT-11</td><td>Non-Latin characters (Arabic etc.)</td><td>CGI/CITI</td><td>Finance + IT</td></tr>
        <tr><td>UAT-12</td><td>Bank pilot confirmation of structured format</td><td>All</td><td>Treasury + Bank TRM</td></tr>
      </table>
    </div>
    """


def tab_transport_plan():
    return """
    <div class="section">
      <h3>Transport Plan — 17-step checklist from handoff §9</h3>
      <p><em>Status tracker. TRKORR will be filled as transports are created in Phase 2.</em></p>
      <table>
        <tr><th>#</th><th>Task</th><th>T-code</th><th>Owner</th><th>TRKORR</th><th>Status</th></tr>
        <tr><td>1</td><td>Confirm DMEE tree names in DEV</td><td>DMEE</td><td>Pablo</td><td>—</td><td>CLOSED (Session #039 + Phase 0)</td></tr>
        <tr><td>2</td><td>Create DEV transport request for DMEE changes</td><td>SE09</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>3</td><td>SEPA: Cdtr PstlAdr structured nodes (FPAYHX mapping)</td><td>DMEE</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>4</td><td>SEPA: Deactivate/keep AdrLine (per Hybrid strategy)</td><td>DMEE</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>5</td><td>SEPA: Dbtr PstlAdr structured nodes (REF field mapping)</td><td>DMEE</td><td>Pablo</td><td></td><td>Pending — uses FPAYHX-ZREF not FPAYH-REF</td></tr>
        <tr><td>6</td><td>CITI: Cdtr PstlAdr structured nodes</td><td>DMEE</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>7</td><td>CITI: UltmtCdtr Worldlink structured</td><td>DMEE</td><td>Pablo + DBS</td><td></td><td>BLOCKED by Q3</td></tr>
        <tr><td>8</td><td>CGI: Cdtr + CdtrAgt fixes</td><td>DMEE</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>9</td><td>Create user exit FM Z_DMEE_UNESCO_DEBTOR_ADDR</td><td>SE37</td><td>Pablo + N_MENARD review</td><td></td><td>Pending — requires D01 retrofit first</td></tr>
        <tr><td>10</td><td>Register FM in OBPM4 Event 05 for all 3 formats</td><td>OBPM4</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>11</td><td>Verify OBPM1 format→tree links</td><td>OBPM1</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>12</td><td>Test F110 SEPA — inspect XML</td><td>F110</td><td>Pablo + Marlies</td><td></td><td>Pending</td></tr>
        <tr><td>13</td><td>Test F110 CITI — inspect XML</td><td>F110</td><td>Pablo + Marlies</td><td></td><td>Pending</td></tr>
        <tr><td>14</td><td>Test F110 CGI — inspect XML</td><td>F110</td><td>Pablo + Marlies</td><td></td><td>Pending</td></tr>
        <tr><td>15</td><td>Validate XSD pain.001.001.03</td><td>External</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>16</td><td>Before/after screenshots per tree</td><td>N/A</td><td>Pablo</td><td></td><td>Pending</td></tr>
        <tr><td>17</td><td>Release transport to V01</td><td>SE10</td><td>Basis</td><td></td><td>Pending</td></tr>
      </table>
    </div>
    """


def tab_francesco():
    md = PHASE0 / "francesco_audit.md"
    return f"""
    <div class="section">
      <h3>Francesco Audit — FP_SPEZZANO</h3>
      {md_to_html_table(md)}
    </div>
    """


def tab_vendor_dq():
    md = PHASE0 / "vendor_master_dq.md"
    return f"""
    <div class="section">
      <h3>Vendor Master Data Quality</h3>
      {md_to_html_table(md)}
    </div>
    """


def tab_q1_q8():
    return """
    <div class="section">
      <h3>Q1-Q8 status — from handoff doc §11</h3>
      <table>
        <tr><th>Q#</th><th>Question</th><th>Priority</th><th>Status (2026-04-24)</th></tr>
        <tr><td>Q1</td><td>Exact DMEE tree name for CITI format in PRD vs DEV</td><td>HIGH</td><td><strong>CLOSED</strong> — Session #039 + Phase 0 Finding G confirm /CITI/XML/UNESCO/DC_V3_01 in P01</td></tr>
        <tr><td>Q2</td><td>CITI pain.001 variant tags (proprietary?)</td><td>HIGH</td><td>OPEN — Phase 1 via Citi TRM</td></tr>
        <tr><td>Q3</td><td>Worldlink UltmtCdtr beneficiary address source</td><td>HIGH</td><td><strong>BLOCKED — gating Phase 2 Step 7</strong></td></tr>
        <tr><td>Q4</td><td>IIEP/UIL separate PMW assignments in FBZP?</td><td>MEDIUM</td><td>OPEN — Phase 1 FBZP check</td></tr>
        <tr><td>Q5</td><td>UBO/UIS separate OBPM4 Event 05 registrations?</td><td>MEDIUM</td><td>OPEN — Phase 1 check</td></tr>
        <tr><td>Q6</td><td>Vendor master DQ count</td><td>HIGH</td><td><strong>CLOSED</strong> — Phase 0 Finding A: 5/111,241 missing mandatory = LOW risk</td></tr>
        <tr><td>Q7</td><td>Formal bank deadline communications</td><td>MEDIUM</td><td>OPEN — Phase 1 TRM outreach</td></tr>
        <tr><td>Q8</td><td>SEPA consolidation into CGI_XML_CT?</td><td>LOW</td><td>PARKED — post-go-live decision</td></tr>
      </table>
    </div>
    """


def tab_timeline():
    return """
    <div class="section">
      <h3>Timeline — 5 phases (gated)</h3>
      <table>
        <tr><th>Phase</th><th>Period</th><th>Owner</th><th>Gate</th><th>Status</th></tr>
        <tr><td>0 — 100% Code Inventory</td><td>2026-04-24 → 04-27</td><td>Pablo</td><td>xml_touch_points_complete.md signed</td><td><strong>IN EXECUTION</strong></td></tr>
        <tr><td>1 — Config matrix + bank specs</td><td>2026-04-27 → 04-30</td><td>Pablo + Marlies</td><td>Matrix + specs + DQ signed</td><td>Pending</td></tr>
        <tr><td>2 — Config D01</td><td>May 2026</td><td>Pablo + Marlies</td><td>Each transport signed</td><td>Pending; BLOCKED by D01 retrofit</td></tr>
        <tr><td>3 — Unit Test D01/V01</td><td>June 2026</td><td>Pablo + DBS</td><td>100% XSD + BAdI regression green</td><td>Pending</td></tr>
        <tr><td>4 — UAT V01</td><td>July 2026</td><td>Marlies + Pablo</td><td>3 bank acceptances + UAT sign-off</td><td>Pending</td></tr>
        <tr><td>5 — Deploy</td><td>Aug-Nov 2026</td><td>DBS + Pablo</td><td>Nov 2026 CBPR+ compliance</td><td>Pending</td></tr>
      </table>
    </div>
    """


def tab_references():
    return """
    <div class="section">
      <h3>References (exhaustive, evidence-anchored)</h3>
      <h4>A. UNESCO-internal user-provided (primary inputs)</h4>
      <ul>
        <li><code>Zagentexecution/incidents/xml_payment_structured_address/original_marlies/XML Address un structured.xlsx</code> — Marlies Spronk's tag analysis: 10 cases + Tab 2 SEPA proposal</li>
        <li><code>Zagentexecution/incidents/xml_payment_structured_address/original_marlies/body.txt</code> — Marlies email 2026-04-14</li>
        <li><code>C:/Users/jp_lopez/Downloads/UNESCO_BCM_StructuredAddress_AgentHandoff.docx</code> v1.0 — <strong>reference architecture document</strong></li>
      </ul>
      <h4>B. UNESCO-internal baselines (project-extracted, verified)</h4>
      <ul>
        <li><code>knowledge/domains/Payment/h18_dmee_tree_nodes.csv</code> — 8,308 nodes Session #039 (narrow columns)</li>
        <li><code>knowledge/domains/Payment/phase0/gap006_dmee_nodes_with_exit.csv</code> — 1,975 nodes, 4 trees, with MP_EXIT_FUNC</li>
        <li><code>knowledge/domains/Payment/phase0/d01_vs_p01_inventory.csv</code> — D01 vs P01 component diff</li>
        <li><code>knowledge/domains/Payment/phase0/gap_closure_report.md</code> — Phase 0 consolidated closure</li>
        <li><code>knowledge/domains/Payment/phase0/xml_touch_points_complete.md</code> — single-source code inventory</li>
        <li><code>extracted_code/FI/DMEE/YCL_IDFI_CGI_DMEE_FR/_FALLBACK/_UTIL_*</code> — 3 BAdI classes extracted</li>
        <li><code>brain_v2/brain_state.json</code> — 72 claims, 96 feedback rules, 246 objects</li>
      </ul>
      <h4>C. SAP-official (to fetch from SAP for Me in Phase 0 follow-up)</h4>
      <ul>
        <li>Note <strong>1665873</strong> — CGI_XML_CT full introduction guide (59 pages, canonical)</li>
        <li>Note 2795667 — ISO 20022 / SEPA harmonization</li>
        <li>Note 2668719 — PMW format lifecycle</li>
        <li>Note 2819590 — Structured remittance in CGI XML</li>
        <li>Note 2845063 — CGI IDs config</li>
      </ul>
      <h4>D. SAP Community threads</h4>
      <ul>
        <li><a href="https://community.sap.com/t5/enterprise-resource-planning-q-a/dmee-debtor-address/qaq-p/11572706">DMEE Debtor Address (Event 05 pattern)</a></li>
        <li><a href="https://community.sap.com/t5/financial-management-q-a/how-to-update-dmee-format-cgi-xml-ct-to-the-pain-001-001-09-version/qaq-p/13897978">Update CGI_XML_CT to pain 001.001.09</a></li>
        <li><a href="https://community.sap.com/t5/enterprise-resource-planning-blog-posts-by-sap/source-of-information-for-tags-of-cgi-pain-001-file/ba-p/13536706">Source of CGI pain.001 tags</a></li>
      </ul>
      <h4>E. ISO 20022 / Industry</h4>
      <ul>
        <li><a href="https://corporates.db.com/in-focus/Focus-topics/iso20022/faqs">Deutsche Bank ISO 20022 FAQ</a></li>
        <li><a href="https://thepaypers.com/regulations/explainers/structured-addresses-and-iso-20022-what-corporates-need-to-prepare-before-november-2026">The Paypers CBPR+ 2026 guide</a></li>
        <li><a href="https://medium.com/@domdigby/iso-20022-enhanced-data-structured-addresses-c64c645cc161">Medium — Dominic Digby tag-by-tag</a></li>
      </ul>
      <h4>F. Bank-specific specs (to request Phase 1)</h4>
      <ul>
        <li>SocGen — pain.001 implementation guide</li>
        <li>Citibank — DC_V3_01 CBPR+ addendum + Worldlink TND/MGA/BRL rules</li>
        <li>Shinhan / Metro / GT and others (CGI-routed) — pain.001 supplements</li>
      </ul>
      <h4>G. Governance</h4>
      <ul>
        <li><code>CLAUDE.md</code> Core Principles CP-001/002/003</li>
        <li><code>brain_v2/agent_rules/feedback_rules.json</code> rule #204 (only P01 trustworthy)</li>
        <li>Ecosystem session-start / collaboration-terms protocol</li>
      </ul>
    </div>
    """


def tab_phase0():
    """Phase 0 — Discovery & 100% Code Inventory. COMPLETED 2026-04-24."""
    return f"""
    <div class="section" style="background:#0d2a1f;border-color:#1abc9c">
      <h3 style="color:#1abc9c">Phase 0 — Discovery &amp; 100% Code Inventory <span style="font-size:12px;color:#7fb3d3">(COMPLETED · 2026-04-24)</span></h3>
      <p><strong>Purpose</strong>: understand 100% of the code/config that touches XML payment output BEFORE proposing changes. Rule: no design decision without evidence.</p>
      <p><strong>Inputs</strong>: Marlies email 2026-04-14 + Excel "XML Address un structured.xlsx" (10 production cases) + handoff doc UNESCO_BCM_StructuredAddress_AgentHandoff.docx v1.0 + Session #039 DMEE baseline + Brain v2.</p>
    </div>
    <h4 style="color:#7fb3d3">Section 1 — Reference Architecture (handoff doc interpreted)</h4>
    {tab_ref_arch()}
    <h4 style="color:#7fb3d3">Section 2 — The 3 target trees</h4>
    {tab_three_trees()}
    <h4 style="color:#7fb3d3">Section 3 — XML Before / After</h4>
    {tab_before_after()}
    <h4 style="color:#7fb3d3">Section 4 — SAP Architecture (E2E flow)</h4>
    {tab_sap_arch()}
    <h4 style="color:#7fb3d3">Section 5 — Code Inventory (100%) — every code point that touches XML</h4>
    {tab_code_inventory()}
    <h4 style="color:#7fb3d3">Section 6 — Francesco audit</h4>
    {tab_francesco()}
    <h4 style="color:#7fb3d3">Section 7 — Vendor master DQ</h4>
    {tab_vendor_dq()}
    <h4 style="color:#7fb3d3">Section 8 — Q1-Q8 status (from handoff doc)</h4>
    {tab_q1_q8()}
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">✅ Phase 0 — CONCLUSION</h3>
      <h4 style="color:#f1c40f">What we delivered</h4>
      <ul>
        <li><strong>Complete data-mutation chain decoded</strong>: F110 → PMW → OBPM4 Event 05 → SAP country factory → FPAYHX_FREF/FPAYP_FREF buffers → DMEE tree traversal → TECH switch nodes (-DBTRPSTLADR/-PSTLADRMOR1/2/3/etc.) → BAdI UNESCO impls → CV_RULE transformations → XSLT post-proc (CITI) → file → BCM → SWIFT</li>
        <li><strong>5 of 8 gaps CLOSED, 2 PARKED, 0 blocking</strong>: GAP-003 (AE/BH don't exist in P01) · GAP-004 (FPAYHX Z-fields real names) · GAP-005 (zero UNESCO writes to Z-fields) · GAP-006 (1,975 nodes + 614 conditions + 26-field headers extracted) · GAP-008 (T042 mapping confirmed) · GAP-001/007 parked</li>
        <li><strong>12 Findings A-L documented</strong> in plan with evidence tier (TIER_1)</li>
        <li><strong>D01 vs P01 anomaly identified</strong>: 5 P01-ONLY objects (YCL_IDFI_CGI_DMEE_DE/IT + 3 ENHO) — D01 retrofit required before Phase 2</li>
        <li><strong>Vendor DQ risk downgraded HIGH→LOW</strong>: only 5/111,241 vendors miss mandatory CITY1/COUNTRY</li>
        <li><strong>Francesco classified</strong>: 5 transports 2025 Q1 are PMF variant config (VC_TFPM042F), not tree structure — ASSIST/IRRELEVANT</li>
        <li>Brain v2 enriched: +7 claims (id 66-72, TIER_1), +3 feedback rules</li>
        <li>Companion v1 built (16 original flat tabs → now restructured by phase)</li>
        <li>4 local commits (f1d1598, e3bf312, a01857a, 5dff1e8)</li>
      </ul>
      <h4 style="color:#f1c40f">What we learned that changed the design</h4>
      <ul>
        <li><strong>Handoff doc §5 had wrong field names</strong>: FPAYHX-ZSTRA/ZHSNM/ZPSTL/ZORT1/ZLAND do NOT exist. Real fields: ZPFST/ZPLOR/ZLISO/ZLNDX/ZREGX/ZREF01..ZREF10. FPAYH has ZERO REF fields; buffers live in FPAYHX-ZREF01..ZREF10.</li>
        <li><strong>Event 05 FMs already exist and are SAP-standard</strong>: FI_PAYMEDIUM_DMEE_CGI_05 + /CITIPMW/V3_PAYMEDIUM_DMEE_05 registered for CGI and CITI. SEPA has NO Event 05. UNESCO doesn't need to write Z_DMEE_UNESCO_DEBTOR_ADDR from scratch (handoff doc pattern was correct but unnecessary for CGI/CITI).</li>
        <li><strong>PSTLADRMOR1/2/3 are TECH scaffolding nodes, not magic parameters</strong>: they group address sub-elements and emit conditional on FREF data availability — SAP-native multi-mode.</li>
        <li><strong>DMEE VERSION column supports 2-file strategy natively</strong>: VERSION=000 current, create VERSION=001 structured in parallel, atomic activation/rollback.</li>
        <li><strong>Hybrid (single file mixed) REJECTED</strong> per user directive — too risky, hard to rollback, parser confusion. 2-file + versioning chosen instead.</li>
        <li><strong>BAdI version-awareness needed</strong>: YCL_IDFI_CGI_DMEE_FALLBACK_CM001 has stateful name-overflow-into-StrtNm quirk that would corrupt V001 structured StrtNm. Pattern A fix (structure-aware guard, 1-2 lines) required.</li>
      </ul>
      <h4 style="color:#f1c40f">Blockers for Phase 2 (to resolve in Phase 1)</h4>
      <ul>
        <li><strong>D01 retrofit from P01</strong>: 5 P01-only objects must be synced to D01 via pyrfc extraction + transport</li>
        <li><strong>Extract YCL_IDFI_CGI_DMEE_DE + _IT source</strong> (currently blocked by RFC auth, use ADT/SE24 export)</li>
        <li><strong>Extract XSLT CGI_XML_CT_XSLT</strong> content (SAP-std, devclass ID-DMEE)</li>
        <li><strong>Q3 Worldlink UltmtCdtr data source</strong> (CITI WHO/ICC case) — needs Citi TRM + DBS input</li>
        <li><strong>N_MENARD alignment</strong>: BAdI Pattern A fix review + D01 retrofit approval</li>
        <li><strong>Francesco courtesy alignment</strong>: disclose his 2025 Q1 transports are context-only, no conflict</li>
      </ul>
      <h4 style="color:#f1c40f">Phase 1 starts from</h4>
      <ol>
        <li>Bank spec TRM outreach (SocGen / Citi / CGI-routed) — 7-day window</li>
        <li>Resolve the 5 DQ vendors manually</li>
        <li>Resolve Q3 data source</li>
        <li>Schedule N_MENARD + Francesco alignment calls</li>
        <li>Build <code>change_matrix.csv</code> with per-node action (ADD/MOD/DEL/KEEP) for V001</li>
      </ol>
    </div>
    """


def tab_phase1():
    """Phase 1 — Config matrix + bank specs. PENDING."""
    return f"""
    <div class="section" style="background:#0d1e2a;border-color:#7fb3d3">
      <h3 style="color:#7fb3d3">Phase 1 — Config matrix + bank specs <span style="font-size:12px;color:#e67e22">(PENDING · 2026-04-27 → 04-30)</span></h3>
      <p><strong>Purpose</strong>: lock the per-tree / per-node change matrix, resolve bank-specific strictness, handle pre-Phase-2 blockers.</p>
      <p><strong>Owner</strong>: Pablo + Marlies + TRM network</p>
    </div>
    <h4 style="color:#7fb3d3">Section 1 — Change Matrix (V001 per node per tree)</h4>
    {tab_change_matrix()}
    <h4 style="color:#7fb3d3">Section 2 — Bank Spec Matrix (to fill)</h4>
    <div class="section">
      <table>
        <tr><th>Bank</th><th>Tree</th><th>Strictness required</th><th>Test gateway available?</th><th>TRM contact</th><th>Response date</th></tr>
        <tr><td>Société Générale</td><td>SEPA_CT_UNES + CGI_XML_CT_UNESCO</td><td>TBD — ask</td><td>TBD</td><td>Marlies's SG TRM</td><td>Pending</td></tr>
        <tr><td>Citibank</td><td>CITI/XML/UNESCO/DC_V3_01</td><td>TBD — ask</td><td>TBD (CitiConnect)</td><td>Marlies's Citi TRM</td><td>Pending</td></tr>
        <tr><td>Shinhan Bank (KR)</td><td>CGI_XML_CT_UNESCO (via FR)</td><td>TBD</td><td>TBD</td><td>via Marlies</td><td>Pending</td></tr>
        <tr><td>Metro Bank (GB)</td><td>CGI_XML_CT_UNESCO (via FR)</td><td>TBD</td><td>TBD</td><td>via Marlies</td><td>Pending</td></tr>
        <tr><td>GT Bank (NG)</td><td>CGI_XML_CT_UNESCO (via FR)</td><td>TBD</td><td>TBD</td><td>via Marlies</td><td>Pending</td></tr>
      </table>
    </div>
    <h4 style="color:#7fb3d3">Section 3 — D01 retrofit plan (Finding I)</h4>
    <div class="section">
      <p>5 P01-ONLY objects to sync to D01 before Phase 2 DMEE edits:</p>
      <table>
        <tr><th>Object</th><th>Type</th><th>Author</th><th>Action</th></tr>
        <tr><td>YCL_IDFI_CGI_DMEE_DE</td><td>CLAS</td><td>N_MENARD</td><td>Extract from P01 via ADT → deploy to D01</td></tr>
        <tr><td>YCL_IDFI_CGI_DMEE_IT</td><td>CLAS</td><td>N_MENARD</td><td>Same</td></tr>
        <tr><td>Y_IDFI_CGI_DMEE_COUNTRIES_DE</td><td>ENHO</td><td>N_MENARD</td><td>Extract enhancement + re-implement in D01</td></tr>
        <tr><td>Y_IDFI_CGI_DMEE_COUNTRIES_FR</td><td>ENHO</td><td>N_MENARD</td><td>Same</td></tr>
        <tr><td>Y_IDFI_CGI_DMEE_COUNTRIES_IT</td><td>ENHO</td><td>N_MENARD</td><td>Same</td></tr>
      </table>
    </div>
    <h4 style="color:#7fb3d3">Section 4 — Vendor DQ remediation (5 vendors)</h4>
    <div class="section">
      <p>Query to run in Phase 1 to get the 5 specific LIFNRs missing CITY1 or COUNTRY, then coordinate with Master Data team for manual LFA1/ADRC fix.</p>
      <pre>SELECT l.LIFNR, l.NAME1, a.CITY1, a.COUNTRY, a.STREET, a.POST_CODE1
FROM LFA1 l
JOIN ADRC a ON l.ADRNR = a.ADDRNUMBER
WHERE (a.CITY1 IS NULL OR a.CITY1 = '' OR a.COUNTRY IS NULL OR a.COUNTRY = '')
  AND (l.LOEVM IS NULL OR l.LOEVM = '')
ORDER BY l.LIFNR;</pre>
    </div>
    <h4 style="color:#7fb3d3">Section 5 — Q3 UltmtCdtr Worldlink data source (BLOCKED Phase 2 Step 7)</h4>
    <div class="section">
      <p>The WHO→ICC case in Marlies Excel shows UltmtCdtr has Hybrid address (AdrLine "AVENUE APPIA 20"). Unknown where this data comes from. Options:</p>
      <ul>
        <li>Vendor master alt-payee (LFB1 / LFBK)</li>
        <li>Separate Z-table</li>
        <li>CITIPMW industry solution enriches from its own config</li>
      </ul>
      <p>Resolution: call with Citibank TRM + DBS to clarify Worldlink enriched-beneficiary data model.</p>
    </div>
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">🔶 Phase 1 — CONCLUSION (to fill when done)</h3>
      <p><em>To be populated at Phase 1 close. Template:</em></p>
      <ul>
        <li>Change matrix signed by Pablo + Marlies with 0 UNKNOWN rows</li>
        <li>Bank specs received: [count / 3 banks] — [strict / hybrid tolerant per bank]</li>
        <li>D01 retrofit executed: [transport TRKORR] — 5 objects synced</li>
        <li>Q3 UltmtCdtr resolved: [data source identified] OR [deferred to Phase 2 with AdrLine fallback]</li>
        <li>Vendor DQ: 5 vendors fixed via [MM team / manual]</li>
        <li>N_MENARD + Francesco alignment calls: [dates, decisions]</li>
        <li>Phase 2 starts with: [ready / blocked on X]</li>
      </ul>
    </div>
    """


def tab_phase2():
    """Phase 2 — Config D01 (DMEE V001 creation + BAdI Pattern A fix). PENDING."""
    return f"""
    <div class="section" style="background:#0d1e2a;border-color:#7fb3d3">
      <h3 style="color:#7fb3d3">Phase 2 — Config D01: DMEE V001 creation + BAdI Pattern A fix <span style="font-size:12px;color:#e67e22">(PENDING · May 2026)</span></h3>
      <p><strong>Purpose</strong>: build V001 structured versions of the 4 trees (V000 unchanged) + apply Pattern A BAdI fix. 4 weeks, ~zero to minimal ABAP.</p>
      <p><strong>Owner</strong>: Pablo (config) + N_MENARD (ABAP review) + Marlies (verification)</p>
    </div>
    <h4 style="color:#7fb3d3">Section 1 — 2-file + DMEE versioning strategy (adopted)</h4>
    <div class="section">
      <p>Each target tree gets a V001 copy created via DMEE native Create Version. V000 stays INACTIVE-proof (kept active in prod through Phase 5). V001 dormant until cutover.</p>
      <pre>Phase 2:
  V000 ACTIVE  (current production, untouched)
  V001 INACTIVE (new structured, deployed dormant)

Phase 3-4 test:
  Z-payment method → routes to V001 → test file to bank test gateway
  Regular payment method → V000 → production file (untouched)

Phase 5 cutover:
  DMEE: deactivate V000 / activate V001 atomically
  Rollback = flip back

Phase 5+30:
  Decommission V000</pre>
    </div>
    <h4 style="color:#7fb3d3">Section 2 — 17-step execution checklist (handoff §9 adapted for V001)</h4>
    {tab_transport_plan()}
    <h4 style="color:#7fb3d3">Section 3 — User exit + BAdI Pattern A fix</h4>
    {tab_user_exit()}
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">🔶 Phase 2 — CONCLUSION (to fill when done)</h3>
      <p><em>To be populated at Phase 2 close. Template:</em></p>
      <ul>
        <li>V001 created on all 4 trees: [transport TRKORRs, dates]</li>
        <li>CGI V001: CdtrAgt fix [done / TRKORR]</li>
        <li>CITI V001: Dbtr structured [done / TRKORR]; UltmtCdtr [done / deferred]</li>
        <li>SEPA V001: Sub-option [A / B / C] chosen — rationale</li>
        <li>Pattern A BAdI fix: [N_MENARD approved / TRKORR / date]</li>
        <li>DMEE tree simulation tests passed on each V001</li>
        <li>Phase 3 starts with: [ready / specific blockers]</li>
      </ul>
    </div>
    """


def tab_phase3():
    """Phase 3 — Unit Test D01/V01. PENDING."""
    return f"""
    <div class="section" style="background:#0d1e2a;border-color:#7fb3d3">
      <h3 style="color:#7fb3d3">Phase 3 — Unit Test D01/V01 <span style="font-size:12px;color:#e67e22">(PENDING · June 2026)</span></h3>
      <p><strong>Purpose</strong>: run V001 in DMEE simulation + F110 proposal mode, validate XML against pain.001.001.03 XSD, run BAdI regression on Pattern A fix.</p>
      <p><strong>Owner</strong>: Pablo + DBS + Marlies</p>
    </div>
    <h4 style="color:#7fb3d3">Test matrix (UT scenarios from handoff §8.1)</h4>
    {tab_test_matrix()}
    <h4 style="color:#7fb3d3">Regression scenarios (V000 must still work)</h4>
    <div class="section">
      <p>During parallel operation (V000 + V001 both exist), regression tests ensure V000 unchanged behavior:</p>
      <ul>
        <li>F110 with production payment method → V000 → file matches baseline byte-for-byte</li>
        <li>BAdI Pattern A fix: vendor name &gt; 35 chars + V000 tree → overflow still prepends (legacy behavior preserved)</li>
        <li>BAdI Pattern A fix: vendor name &gt; 35 chars + V001 tree → overflow NOT prepended (StrtNm has real value)</li>
      </ul>
    </div>
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">🔶 Phase 3 — CONCLUSION (to fill when done)</h3>
      <p><em>To be populated at Phase 3 close. Template:</em></p>
      <ul>
        <li>UT cases executed: [passed / total] — fail list with root cause</li>
        <li>XSD validation: [100% pass / issues list]</li>
        <li>Regression V000 vs baseline: [0 diff / diff count]</li>
        <li>Pattern A fix behavior verified in both V000 and V001 contexts</li>
        <li>Phase 4 starts with: [ready for UAT + pilot]</li>
      </ul>
    </div>
    """


def tab_phase4():
    """Phase 4 — UAT V01 + bank pilot. PENDING."""
    return f"""
    <div class="section" style="background:#0d1e2a;border-color:#7fb3d3">
      <h3 style="color:#7fb3d3">Phase 4 — UAT V01 + bank pilot <span style="font-size:12px;color:#e67e22">(PENDING · July 2026)</span></h3>
      <p><strong>Purpose</strong>: business users validate UAT scenarios; V001 files sent to bank TEST gateways for acceptance confirmation.</p>
      <p><strong>Owner</strong>: Marlies + per-entity finance leads + bank TRMs</p>
    </div>
    <div class="section">
      <h4>UAT scenarios (handoff §8.2)</h4>
      <p>See Test Matrix — UAT section. Plus:</p>
      <ul>
        <li>Monthly EUR salary/vendor via SocGen (UNES + IIEP + UIL) — SEPA V001 output</li>
        <li>USD international vendor payment via Citi — CITI V001 output</li>
        <li>Worldlink TND (Tunisia) + MGA (Madagascar) + BRL (UBO) — CITI V001 output (if UltmtCdtr resolved)</li>
        <li>Non-SocGen EUR via CGI — CGI V001 output</li>
        <li>Non-Latin character vendor addresses (Arabic etc.) — char filter regression</li>
      </ul>
      <h4>Bank pilot validation</h4>
      <ul>
        <li>Send V001 file per bank to their TEST gateway (separate from live)</li>
        <li>Collect written acceptance email per bank</li>
        <li>If rejection: diagnose + fix in V001 + re-send</li>
      </ul>
    </div>
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">🔶 Phase 4 — CONCLUSION (to fill when done)</h3>
      <p><em>To be populated at Phase 4 close. Template:</em></p>
      <ul>
        <li>UAT scenarios passed: [count / total] — sign-off per entity</li>
        <li>Bank test-gateway acceptance: [SocGen OK/NO | Citi OK/NO | CGI-routed banks OK/NO]</li>
        <li>Issues found and resolved: [list]</li>
        <li>Phase 5 starts with: [ready to cutover / blocked on bank X]</li>
      </ul>
    </div>
    """


def tab_phase5():
    """Phase 5 — Deploy P01 staged. PENDING."""
    return f"""
    <div class="section" style="background:#0d1e2a;border-color:#7fb3d3">
      <h3 style="color:#7fb3d3">Phase 5 — Deploy P01 staged <span style="font-size:12px;color:#e67e22">(PENDING · Aug-Nov 2026 · CBPR+ hard deadline Nov 1)</span></h3>
      <p><strong>Purpose</strong>: staged cutover V000→V001 per tree. Atomic activation flip. 14-day monitoring per cutover. Rollback path ready.</p>
      <p><strong>Owner</strong>: DBS (transport) + Pablo (monitoring) + Marlies (business confirmation)</p>
    </div>
    <div class="section">
      <h4>Cutover order (staggered 2-week windows)</h4>
      <ol>
        <li><strong>CGI trees first</strong> — narrowest change scope (CdtrAgt only), lowest volume per week</li>
        <li><strong>SEPA_CT_UNES</strong> — medium volume, Sub-option dependent on Phase 2 choice</li>
        <li><strong>CITI/XML/UNESCO/DC_V3_01 last</strong> — highest volume, Worldlink edge cases</li>
      </ol>
      <h4>Rollback plan (per tree)</h4>
      <pre>Trigger: &gt;2 bank rejects in 24h attributable to address format
        OR XSD validation failure rate &gt;1%
        OR Marlies/Treasury-head override

Action:  DMEE activate V000 / deactivate V001 atomically in D01
         Transport to P01 via emergency path
         V001 preserved inactive for investigation
         SLA: cutover &lt;60 minutes from decision

Post-rollback:
  Diagnosis of V001 failure
  Fix in next V001 iteration (or V002)
  Re-cutover in 2-week cycle</pre>
      <h4>Post-go-live monitoring (14 days per tree)</h4>
      <ul>
        <li>Daily BCM batch reject count per tree (existing Zagentexecution/bcm_dual_control_monitor.py extended)</li>
        <li>Schema validation fail rate (should be 0%)</li>
        <li>Vendor-specific errors (expected &lt;0.01% per active-vendor pop)</li>
        <li>Bank confirmations of file acceptance (daily check)</li>
      </ul>
      <h4>V000 decommission (Phase 5+30 days)</h4>
      <ul>
        <li>After 30 days of stable V001 in prod across all 4 trees</li>
        <li>Delete V000 from DMEE tree headers</li>
        <li>Clean transport to remove V000 nodes from all 3 systems</li>
        <li>Final plan retrospective + brain session close</li>
      </ul>
    </div>
    <div class="section" style="background:#1a2a1f;border-color:#f1c40f;margin-top:30px">
      <h3 style="color:#f1c40f">🔶 Phase 5 — CONCLUSION (to fill when done)</h3>
      <p><em>To be populated at Phase 5 close. Template:</em></p>
      <ul>
        <li>Cutover dates per tree: [CGI YYYY-MM-DD | SEPA YYYY-MM-DD | CITI YYYY-MM-DD]</li>
        <li>Rollbacks executed: [count / 0 ideal]</li>
        <li>Bank rejects attributable to address: [0 / N]</li>
        <li>CBPR+ Nov 2026 deadline: [MET / MISSED / partial]</li>
        <li>V000 decommissioned: [date]</li>
        <li>Brain session-close retro: [link]</li>
      </ul>
    </div>
    """


def tab_scope():
    """Scope tab — clear what we change vs not change vs out of scope."""
    return """
    <div class="section">
      <h3>Scope — what we change in V001</h3>
      <h4 style="color:#1abc9c">✅ IN SCOPE — V001 changes (per tree)</h4>
      <table>
        <tr><th>Tree</th><th>Change</th><th>Type</th><th>Effort</th></tr>
        <tr><td><code>/SEPA_CT_UNES</code></td><td>+5 Dbtr structured nodes (StrtNm/BldgNb/PstCd/TwnNm/Ctry) reading FPAYHX-REF01/REF06 with MP_OFFSET. +5 empty-suppress conditions in DMEE_TREE_COND (no XSLT for SEPA).</td><td>CONFIG</td><td>~4 hours</td></tr>
        <tr><td><code>/CITI/XML/UNESCO/DC_V3_01</code></td><td>+5 Dbtr structured nodes. NO conditions needed (XSLT auto-removes empty).</td><td>CONFIG</td><td>~3 hours</td></tr>
        <tr><td><code>/CGI_XML_CT_UNESCO</code></td><td>NO tree edits — Dbtr already structured</td><td>—</td><td>0</td></tr>
        <tr><td><code>/CGI_XML_CT_UNESCO_1</code></td><td>NO tree edits — Dbtr already structured</td><td>—</td><td>0</td></tr>
        <tr><td><code>TFPM042FB</code> (OBPM4)</td><td>+1 row: SEPA tree → Event 05 = FI_PAYMEDIUM_DMEE_CGI_05</td><td>CONFIG</td><td>~30 min</td></tr>
        <tr><td><code>YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT</code></td><td>+3 lines (Pattern A guard) — prevents V001 StrtNm corruption from name-overflow</td><td>CODE</td><td>~1 hour code + 2 hour regression test</td></tr>
        <tr><td>5 LFA1+ADRC vendors</td><td>Manual fix CITY1/COUNTRY OR LOEVM='X'</td><td>DATA</td><td>~30 min Master Data team</td></tr>
      </table>
      <p><b>Total ABAP</b>: 1 method, 3 lines. <b>Total CONFIG</b>: ~16 nodes + 1 OBPM4 row + 5 vendor fixes.</p>

      <h4 style="color:#f39c12">⚖ STAYS THE SAME (V000 untouched)</h4>
      <table>
        <tr><th>Asset</th><th>Why preserved</th></tr>
        <tr><td>All V000 DMEE trees</td><td>Production payment flow continues unchanged during transition. V000 only deactivates at Phase 5 cutover.</td></tr>
        <tr><td>SAP-std FMs (FI_PAYMEDIUM_DMEE_CGI_05, /CITIPMW/V3_PAYMEDIUM_DMEE_05, GENERIC class, country classes FR/DE/IT/GB)</td><td>SAP-delivered, never modified. Reused by V001.</td></tr>
        <tr><td>FPAYHX_FREF + FPAYP_FREF buffer structures</td><td>SAP-std DDIC. V001 reads from them.</td></tr>
        <tr><td>Workflow 90000003 + BCM batch logic</td><td>Out of scope — change is XML-content only.</td></tr>
        <tr><td>UNESCO BAdI classes _FR/_DE/_IT/_UTIL</td><td>Untouched. Only FALLBACK_CM001 gets the 3-line fix.</td></tr>
        <tr><td>Z exits Z_DMEE_EXIT_TAX_NUMBER + ZDMEE_EXIT_SEPA_21</td><td>Not address-related, untouched.</td></tr>
        <tr><td>YTFI_PPC_TAG / STRUC tables</td><td>0 rows for our target countries — no change needed.</td></tr>
        <tr><td>Francesco's PMF variants (5 transports 2025)</td><td>Bank-variant config, parallel to our work, courtesy heads-up only.</td></tr>
        <tr><td>XSLT CGI_XML_CT_XSLT</td><td>SAP-std, devclass=ID-DMEE. CITI tree uses it as-is.</td></tr>
      </table>

      <h4 style="color:#e74c3c">❌ OUT OF SCOPE</h4>
      <ul>
        <li><b>pain.001.001.09 schema migration</b> — separate project (current trees stay on .03)</li>
        <li><b>BCM workflow 90000003 modification</b> — dual-control logic untouched</li>
        <li><b>Bank file naming + transmission</b> — Alliance Lite2 + SWIFT delivery untouched</li>
        <li><b>ICTP Trieste trees</b> (/SEPA_CT_ICTP_*) — separate from UNESCO HQ scope</li>
        <li><b>UltmtCdtr Worldlink (Q3)</b> — DEFERRED to V002 unless Citi TRM clarifies data source by Phase 2 start</li>
        <li><b>Vendor master cleanup beyond the 5 mandatory-missing</b> — fully-structured cleanup is a separate project (76,574 vendors missing HOUSE_NUM1, etc.)</li>
        <li><b>BCM_BATCH_* BAdIs</b> — not extracted, not in change path</li>
      </ul>
    </div>
    """


def tab_change_strategy():
    """Change Strategy tab — articulates HOW we make the change."""
    return """
    <div class="section">
      <h3>Change Strategy — HOW we deploy V001</h3>

      <h4>Why 2-file + DMEE versioning (not Hybrid single-file)</h4>
      <table>
        <tr><th>Approach</th><th>Adopted?</th><th>Why</th></tr>
        <tr><td><b>Hybrid single file</b> (mixed structured + AdrLine in same XML)</td><td>❌ Rejected</td><td>Mixes legacy + new in one file → parser confusion, rollback hard, bank validation harder</td></tr>
        <tr><td><b>2-file + DMEE native versioning</b> (V000 + V001 parallel)</td><td>✅ Adopted</td><td>Per user directive 2026-04-24. Atomic activation/rollback. SAP-native. Bank can validate V001 via test gateway without prod risk</td></tr>
      </table>

      <h4>How V000 + V001 coexist</h4>
      <pre>Phase 2 (May 2026):
  Tree V000 = ACTIVE (current production state, unchanged)
  Tree V001 = INACTIVE (newly deployed dormant)

Phase 3-4 testing:
  Z-payment method routes test F110 → V001 only
  Production payments → V000 (untouched)
  Both files generated for parallel comparison

Phase 5 cutover (atomic):
  Deactivate V000, Activate V001 → instant
  All F110 now produces V001 structured

Rollback (instant if needed):
  Activate V000, Deactivate V001 → seconds, no data loss

Phase 5 + 30 days stable:
  V000 decommissioned</pre>

      <h4>Per-tree strategy nuances</h4>
      <table>
        <tr><th>Tree</th><th>Empty-element handling</th><th>Why different</th></tr>
        <tr><td><code>/CITI/XML/UNESCO/DC_V3_01</code></td><td>Emit all 5 nodes unconditionally. XSLT (CGI_XML_CT_XSLT) auto-removes empty.</td><td>XSLTDESC populated for this tree only — verified Phase 1.</td></tr>
        <tr><td><code>/SEPA_CT_UNES</code></td><td>Add explicit DMEE_TREE_COND per node: emit only if source field NE space</td><td>No XSLT for SEPA — empty nodes would be emitted as-is, breaking schema</td></tr>
        <tr><td><code>/CGI_XML_CT_UNESCO</code> + <code>_1</code></td><td>NO change — Dbtr already structured with conditions in V000</td><td>Existing tree pattern works, no V001 tree edits needed</td></tr>
      </table>

      <h4>Pattern A — the only ABAP change</h4>
      <p>3-line guard in <code>YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT</code>. Prevents V001 structured StrtNm from being corrupted by V000's legacy name-overflow logic. Backward-compatible: V000 behavior preserved.</p>
      <pre>" Add this guard:
WHEN '&lt;PmtInf&gt;&lt;CdtTrfTxInf&gt;&lt;Cdtr&gt;&lt;PstlAdr&gt;&lt;StrtNm&gt;'.
  IF i_fpayh = mv_fpayh
     AND mv_cdtr_name+35 IS NOT INITIAL
     AND c_value IS INITIAL.            "← V001 GUARD: only prepend if StrtNm empty
    c_value = mv_cdtr_name+35.
  ELSEIF i_fpayh = mv_fpayh
     AND mv_cdtr_name+35 IS NOT INITIAL.
    c_value = |{ mv_cdtr_name+35 } { c_value }|.   " V000 legacy preserved
  ENDIF.
  IF c_value+70 IS NOT INITIAL.
    CLEAR c_value+70.
  ENDIF.</pre>
      <p><b>Reviewer</b>: N_MENARD (code owner). Pending alignment call (see Phase 1 tab).</p>

      <h4>Test pyramid (4 levels of risk)</h4>
      <table>
        <tr><th>Level</th><th>Where</th><th>Risk</th><th>Examples</th></tr>
        <tr><td><b>L0 — DMEE Tx Test simulation</b></td><td>D01 read-only</td><td>ZERO</td><td>Synthetic FPAYHX payload, validate XML output. Python XSD harness.</td></tr>
        <tr><td><b>L1 — D01 simulation no transport</b></td><td>D01</td><td>Reversible (no transport)</td><td>F110 proposal mode with Z-payment method routed to V001</td></tr>
        <tr><td><b>L2 — D01 transport, V01 test client</b></td><td>D01 → V01</td><td>Transport-revertable</td><td>Real F110 in V01 with Z-method, compare V000 vs V001 byte-by-byte</td></tr>
        <tr><td><b>L3 — Bank pilot via test gateway</b></td><td>External</td><td>External dependency</td><td>Send V001 sample to bank's test gateway (separate from prod), get written acceptance</td></tr>
      </table>

      <h4>Cutover order (Phase 5)</h4>
      <ol>
        <li><b>CGI tree first</b> — only 3-line BAdI fix activates effects. Lowest blast radius. Validate.</li>
        <li><b>SEPA second</b> — first tree with full V001 node additions. UNESCO + IIEP + UIL.</li>
        <li><b>CITI last</b> — highest volume + Worldlink edge cases. Most exposed if anything fails.</li>
      </ol>
      <p>Each cutover: 14-day monitoring before next tree's cutover.</p>

      <h4>Rollback protocol</h4>
      <pre>Detection criteria:
  - >2 bank rejects in 24h attributed to address structure
  - XSD validation failure rate >1%
  - Marlies/Treasury head override

Action sequence (≤60 minutes from decision):
  1. DMEE Tx → tree → V000 ACTIVE / V001 INACTIVE (atomic flag)
  2. Tx FDTA: re-run 1-vendor F110 sample, verify V000 file emitted
  3. Notify banks via BCM ops DL: "Reverted to V000 unstructured; new ETA TBD"
  4. INC ticket open; preserve V001 inactive for forensics

Decision authority: Marlies (BCM ops) + Pablo (technical) jointly.
Data loss: zero (F110 idempotent on REGUH).</pre>

      <h4>Decisions baked into this strategy</h4>
      <ul>
        <li>UltmtCdtr Worldlink (Q3) → V002 deferred unless Citi TRM resolves before Phase 2</li>
        <li>Per-bank strictness → confirmed Phase 1 (TRM responses)</li>
        <li>Vendor master cleanup → 5 mandatory-missing only (LOW risk per DQ)</li>
        <li>pain.001.001.09 schema upgrade → SEPARATE project, not in V001</li>
        <li>2-tree CGI variants (CGI + _1) → SYNC pattern, no independent design</li>
      </ul>
    </div>
    """


def tab_e2e_flow():
    """E2E Flow — connects all 27 components from F110 to bank in single logical pipeline."""
    md = Path(__file__).resolve().parents[2] / "knowledge" / "domains" / "Payment" / "phase0" / "e2e_flow_components_connected.md"
    return f"""
    <div class="section">
      <h3>End-to-End Flow Map — all components connected</h3>
      <p>Per user directive 2026-04-25 "tenemos que conectar todos los elementos en un flow logico". Single canonical view of the pipeline from F110 to bank, showing where each of the 32 components sits.</p>
      <p><em>Source: <code>knowledge/domains/Payment/phase0/e2e_flow_components_connected.md</code></em></p>
    </div>
    {md_to_html_table(md)}
    """


def tab_components():
    """Components Map — 31 components (CONFIG/CODE/DATA/DDIC/SAP-std)."""
    import json
    cm_path = Path(__file__).resolve().parents[2] / "knowledge" / "domains" / "Payment" / "phase0" / "components_map.json"
    if not cm_path.exists():
        return "<p>Components map not generated yet.</p>"
    with open(cm_path, encoding="utf-8") as f:
        data = json.load(f)
    components = data["components"]
    type_colors = {
        "CONFIG": "#cfe2f3",
        "CODE": "#fce5cd",
        "CODE (SAP std)": "#ead1dc",
        "DDIC": "#d9ead3",
        "DATA": "#fff2cc",
    }
    rows = []
    for c in components:
        bg = type_colors.get(c["type"], "#f5f5f5")
        abap = "<b style='color:#c0392b'>YES</b>" if c.get("abap_needed") else "no"
        rows.append(
            f"<tr style='background:{bg};color:#222'>"
            f"<td><code>{esc(c['id'])}</code></td>"
            f"<td><b>{esc(c['name'])}</b></td>"
            f"<td>{esc(c['type'])}</td>"
            f"<td>{esc(c['layer'])}</td>"
            f"<td>{esc(c['owner'])}</td>"
            f"<td>{esc(c['today_v000'])}</td>"
            f"<td><b>{esc(c['v001_change'])}</b></td>"
            f"<td>{esc(c['evidence'])}</td>"
            f"<td>{esc(c['reviewer'])}</td>"
            f"<td>{abap}</td>"
            f"</tr>"
        )
    return f"""
    <div class="section">
      <h3>Components Map — config + code + data ({data['total']} components)</h3>
      <p><em>Last update: {esc(data.get('last_update', '—'))} · Source of truth: <code>knowledge/domains/Payment/phase0/components_map.json</code></em></p>
      <p>Color legend: <span style="background:#cfe2f3;padding:2px 8px;color:#222">CONFIG</span> &nbsp;
         <span style="background:#fce5cd;padding:2px 8px;color:#222">CODE (UNESCO)</span> &nbsp;
         <span style="background:#ead1dc;padding:2px 8px;color:#222">CODE (SAP std)</span> &nbsp;
         <span style="background:#d9ead3;padding:2px 8px;color:#222">DDIC</span> &nbsp;
         <span style="background:#fff2cc;padding:2px 8px;color:#222">DATA</span></p>
      <table>
        <tr><th>ID</th><th>Component</th><th>Type</th><th>Layer</th><th>Owner</th><th>Today (V000)</th><th>V001 change</th><th>Evidence</th><th>Reviewer</th><th>ABAP?</th></tr>
        {chr(10).join(rows)}
      </table>
      <p style="margin-top:16px"><b>Summary</b>: of {data['total']} components, <b>1 needs ABAP</b> (Pattern A guard in <code>YCL_IDFI_CGI_DMEE_FALLBACK_CM001</code>, 3 lines), <b>5 need CONFIG</b> (DMEE V001 trees + TFPM042FB Event 05 row), the rest are <b>NO CHANGE</b> — SAP-std reused or out of scope.</p>
      <p>Surgical change validated by independent expert agent re-evaluation 2026-04-25: <b>~80% customizing, ~20% code (1 method, 3 lines)</b>.</p>
    </div>
    """


TABS = [
    ("overview", "Overview", tab_overview),
    ("scope", "Scope", tab_scope),
    ("strategy", "Change Strategy", tab_change_strategy),
    ("e2e-flow", "E2E Flow", tab_e2e_flow),
    ("components", "Components Map", tab_components),
    ("phase0", "Phase 0 · Discovery ✅", tab_phase0),
    ("phase1", "Phase 1 · Matrix + Specs", tab_phase1),
    ("phase2", "Phase 2 · Config D01", tab_phase2),
    ("phase3", "Phase 3 · Unit Test", tab_phase3),
    ("phase4", "Phase 4 · UAT + Pilot", tab_phase4),
    ("phase5", "Phase 5 · Deploy", tab_phase5),
    ("timeline", "Timeline", tab_timeline),
    ("plan", "The Plan (live)", tab_plan),
    ("references", "References", tab_references),
]


def build():
    tabs_nav = "\n".join(
        f'<div class="nav-item{" active" if i == 0 else ""}" onclick="show(\'{tid}\', this)" data-full="{label}" data-short="{label.split(chr(183))[0].strip()[:3] if chr(183) in label else label[:3]}">'
        f'<span class="nav-label">{label}</span></div>'
        for i, (tid, label, _) in enumerate(TABS)
    )
    tabs_content = "\n".join(
        f'<div id="tab-{tid}" class="content{" visible" if i == 0 else ""}">{fn()}</div>'
        for i, (tid, label, fn) in enumerate(TABS)
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UNESCO BCM Structured Address Change — {VERSION}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 0; background: #0a1520; color: #d6e5f5; font-size: 13px; line-height: 1.5; }}
  header {{ background: #0c1926; padding: 16px 32px; border-bottom: 2px solid #1e3a4a; position: sticky; top: 0; z-index: 100; display: flex; align-items: center; gap: 20px; }}
  .header-title {{ flex: 1; }}
  h1 {{ margin: 0; font-size: 18px; color: #7fb3d3; }}
  .sub {{ font-size: 11px; color: #5d7a92; margin-top: 4px; }}
  .hamburger {{ cursor: pointer; padding: 8px 12px; background: #12202e; border: 1px solid #1e3a4a; border-radius: 6px; color: #1abc9c; font-size: 18px; line-height: 1; user-select: none; }}
  .hamburger:hover {{ background: #1e3a4a; }}
  .kpis {{ display: flex; gap: 12px; flex-wrap: wrap; }}
  .kpi {{ background: #12202e; padding: 6px 10px; border-radius: 4px; border: 1px solid #1e3a4a; }}
  .kpi .val {{ font-size: 14px; font-weight: 600; color: #7fb3d3; }}
  .kpi .lbl {{ font-size: 10px; color: #5d7a92; }}

  .layout {{ display: flex; min-height: calc(100vh - 70px); }}

  /* Left sidebar — vertical, collapsible */
  .sidebar {{ width: 260px; background: #0c1926; border-right: 2px solid #1e3a4a; padding: 16px 0; transition: width 0.25s ease; overflow-y: auto; flex-shrink: 0; position: sticky; top: 70px; height: calc(100vh - 70px); }}
  .sidebar.collapsed {{ width: 56px; }}
  .nav-item {{ padding: 12px 20px; cursor: pointer; color: #8fa9be; font-size: 13px; border-left: 3px solid transparent; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background 0.15s, color 0.15s, border-left 0.15s; display: flex; align-items: center; }}
  .nav-item:hover {{ color: #7fb3d3; background: #12202e; }}
  .nav-item.active {{ color: #1abc9c; background: #12202e; border-left: 3px solid #1abc9c; font-weight: 600; }}
  .sidebar.collapsed .nav-label {{ opacity: 0; pointer-events: none; width: 0; }}
  .sidebar.collapsed .nav-item {{ padding: 12px 0; justify-content: center; }}
  .sidebar.collapsed .nav-item::before {{ content: attr(data-short); color: inherit; font-weight: 700; font-size: 11px; }}
  .nav-label {{ transition: opacity 0.2s; }}

  /* Main content area */
  .main {{ flex: 1; padding: 24px 32px; max-width: 100%; min-width: 0; overflow-x: auto; }}
  .content {{ display: none; }}
  .content.visible {{ display: block; }}

  .section {{ background: #12202e; padding: 20px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #1e3a4a; }}
  .section h3 {{ margin-top: 0; color: #1abc9c; font-size: 16px; }}
  .section h4 {{ color: #7fb3d3; font-size: 13px; margin-top: 18px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 12px; }}
  th, td {{ border: 1px solid #1e3a4a; padding: 6px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #1e3a4a; color: #7fb3d3; }}
  tr:nth-child(even) td {{ background: #0f1d2a; }}
  code {{ background: #0c1926; padding: 2px 6px; border-radius: 3px; color: #1abc9c; font-size: 11px; }}
  pre {{ background: #0c1926; padding: 12px; border-radius: 6px; border: 1px solid #1e3a4a; overflow-x: auto; font-size: 11px; color: #d6e5f5; }}
  a {{ color: #7fb3d3; }}
  ul li {{ margin-bottom: 4px; }}

  @media (max-width: 900px) {{
    .sidebar {{ width: 56px; }}
    .sidebar .nav-label {{ opacity: 0; width: 0; }}
    .sidebar .nav-item {{ padding: 12px 0; justify-content: center; }}
    .sidebar .nav-item::before {{ content: attr(data-short); color: inherit; font-weight: 700; font-size: 11px; }}
    .kpis {{ display: none; }}
  }}
</style>
</head>
<body>
<header>
  <div class="hamburger" onclick="toggleSidebar()" title="Collapse/expand menu">&#9776;</div>
  <div class="header-title">
    <h1>UNESCO BCM Structured Address Change &nbsp;<span style="font-size:12px;color:#7fb3d3">{VERSION}</span></h1>
    <div class="sub">CBPR+ Nov 2026 · 3 DMEE trees · 2-file + DMEE versioning · Built {BUILD_TS}</div>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="val">3</div><div class="lbl">Target trees</div></div>
    <div class="kpi"><div class="val">1,975</div><div class="lbl">Nodes P01</div></div>
    <div class="kpi"><div class="val">5/111k</div><div class="lbl">Vendor miss</div></div>
    <div class="kpi"><div class="val">31</div><div class="lbl">Marlies 10y</div></div>
    <div class="kpi"><div class="val">Nov 2026</div><div class="lbl">Deadline</div></div>
  </div>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    {tabs_nav}
  </aside>
  <main class="main">
    {tabs_content}
  </main>
</div>
<script>
function show(id, el) {{
  document.querySelectorAll('.content').forEach(c => c.classList.remove('visible'));
  document.getElementById('tab-' + id).classList.add('visible');
  document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  window.scrollTo(0, 0);
}}
function toggleSidebar() {{
  document.getElementById('sidebar').classList.toggle('collapsed');
}}
</script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Built: {OUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    build()
