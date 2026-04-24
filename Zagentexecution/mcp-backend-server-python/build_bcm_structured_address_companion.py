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
import csv, json, sys, os
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
      <h3>Compliance states (3 states, not 2)</h3>
      <table>
        <tr><th>State</th><th>Validity after Nov 2026</th><th>UNESCO target</th></tr>
        <tr><td>Unstructured (AdrLine only)</td><td>REJECTED</td><td>Must migrate away</td></tr>
        <tr><td>Hybrid (TwnNm+Ctry + AdrLine)</td><td>OK — minimum viable</td><td>Default transition state</td></tr>
        <tr><td>Fully structured (5 tags)</td><td>OK + future-proof</td><td>Long-term target</td></tr>
      </table>
      <h3>Coexistence strategy</h3>
      <p>User directive: run old + new formats in parallel during transition, not hard cutover. Enabled by DMEE <code>VERSION</code> column (multi-version coexistence) and potentially 2-file approach per bank (validation path).</p>
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


TABS = [
    ("overview", "Overview", tab_overview),
    ("plan", "The Plan (live)", tab_plan),
    ("ref-arch", "Reference Architecture", tab_ref_arch),
    ("trees", "The 3 Trees", tab_three_trees),
    ("matrix", "Change Matrix", tab_change_matrix),
    ("before-after", "XML Before/After", tab_before_after),
    ("sap-arch", "SAP Architecture", tab_sap_arch),
    ("inventory", "Code Inventory (100%)", tab_code_inventory),
    ("user-exit", "User Exit", tab_user_exit),
    ("test-matrix", "Test Matrix", tab_test_matrix),
    ("transport", "Transport Plan", tab_transport_plan),
    ("francesco", "Francesco Audit", tab_francesco),
    ("vendor-dq", "Vendor DQ", tab_vendor_dq),
    ("q1-q8", "Q1-Q8 Status", tab_q1_q8),
    ("timeline", "Timeline", tab_timeline),
    ("references", "References", tab_references),
]


def build():
    tabs_nav = "\n".join(
        f'<div class="tab{" active" if i == 0 else ""}" onclick="show(\'{tid}\', this)">{label}</div>'
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
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 0; background: #0a1520; color: #d6e5f5; font-size: 13px; line-height: 1.5; }}
  header {{ background: #0c1926; padding: 20px 32px; border-bottom: 2px solid #1e3a4a; }}
  h1 {{ margin: 0; font-size: 22px; color: #7fb3d3; }}
  .sub {{ font-size: 12px; color: #5d7a92; margin-top: 6px; }}
  .kpis {{ display: flex; gap: 24px; margin-top: 16px; }}
  .kpi {{ background: #12202e; padding: 10px 16px; border-radius: 6px; border: 1px solid #1e3a4a; }}
  .kpi .val {{ font-size: 20px; font-weight: 600; color: #7fb3d3; }}
  .kpi .lbl {{ font-size: 11px; color: #5d7a92; }}
  .tabs {{ display: flex; flex-wrap: wrap; background: #0c1926; padding: 0 32px; border-bottom: 2px solid #1e3a4a; overflow-x: auto; }}
  .tab {{ padding: 12px 16px; cursor: pointer; border-bottom: 3px solid transparent; color: #8fa9be; white-space: nowrap; font-size: 12px; }}
  .tab:hover {{ color: #7fb3d3; }}
  .tab.active {{ border-bottom: 3px solid #1abc9c; color: #1abc9c; }}
  .content {{ display: none; padding: 24px 32px; max-width: 1400px; }}
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
</style>
</head>
<body>
<header>
  <h1>UNESCO BCM Structured Address Change &nbsp;<span style="font-size:14px;color:#7fb3d3">{VERSION}</span></h1>
  <div class="sub">CBPR+ Nov 2026 DMEE migration · 3 trees · Hybrid coexistence · Built {BUILD_TS}</div>
  <div class="kpis">
    <div class="kpi"><div class="val">3</div><div class="lbl">Target DMEE trees</div></div>
    <div class="kpi"><div class="val">1,975</div><div class="lbl">Nodes probed (P01)</div></div>
    <div class="kpi"><div class="val">5/111,241</div><div class="lbl">Vendors missing mandatory</div></div>
    <div class="kpi"><div class="val">0.005%</div><div class="lbl">DQ risk</div></div>
    <div class="kpi"><div class="val">31</div><div class="lbl">Marlies DMEE transports 10y</div></div>
    <div class="kpi"><div class="val">5</div><div class="lbl">P01-ONLY objects (D01 retrofit needed)</div></div>
    <div class="kpi"><div class="val">Nov 2026</div><div class="lbl">CBPR+ deadline</div></div>
  </div>
</header>
<div class="tabs">
  {tabs_nav}
</div>
{tabs_content}
<script>
function show(id, el) {{
  document.querySelectorAll('.content').forEach(c => c.classList.remove('visible'));
  document.getElementById('tab-' + id).classList.add('visible');
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
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
