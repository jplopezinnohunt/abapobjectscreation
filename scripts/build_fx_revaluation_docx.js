// FX Revaluation (F.05 / SAPF100) — Conclusions, Word deliverable
// Source of truth: knowledge/domains/Closing_Activities/fx_revaluation_process.md
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, TableOfContents, Header, Footer, PageNumber, PageBreak
} = require("docx");

const NAVY = "1F3864", BLUE = "2E75B6", GREEN = "2C7A4A", RED = "A32D2D",
      AMBER = "B06B00", GREY = "5B6B7A", HEADBG = "D5E8F0", OKBG = "E0F3E6",
      BADBG = "FDE8E8", WARNBG = "FFF5E0";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

// ---- helpers ----
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const P  = (runs, opts={}) => new Paragraph({ spacing: { after: 120 }, ...opts,
  children: Array.isArray(runs) ? runs : [new TextRun(runs)] });
const bullet = (runs) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 },
  children: Array.isArray(runs) ? runs : [new TextRun(runs)] });
const num = (runs) => new Paragraph({ numbering: { reference: "stp", level: 0 }, spacing: { after: 60 },
  children: Array.isArray(runs) ? runs : [new TextRun(runs)] });
const b = (t) => new TextRun({ text: t, bold: true });
const code = (t) => new TextRun({ text: t, font: "Consolas", size: 20 });
const t = (txt) => new TextRun(txt);

function cell(text, { w, fill, bold=false, color, align } = {}) {
  const runs = Array.isArray(text) ? text :
    [new TextRun({ text: String(text), bold, color, font: bold ? "Arial" : undefined })];
  return new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    children: [new Paragraph({ alignment: align, children: runs })]
  });
}
function table(widths, header, rows) {
  const total = widths.reduce((a,c)=>a+c,0);
  const head = new TableRow({ tableHeader: true, children: header.map((h,i)=>cell(h,{w:widths[i],fill:HEADBG,bold:true,color:NAVY})) });
  const body = rows.map(r => new TableRow({ children: r.map((c,i)=> typeof c==='object' && c!==null && 'text' in c
      ? cell(c.text,{w:widths[i],fill:c.fill,bold:c.bold,color:c.color})
      : cell(c,{w:widths[i]}) ) }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: [head, ...body] });
}
const spacer = () => new Paragraph({ spacing: { after: 60 }, children: [] });

// callout-like shaded single-cell box
function box(fill, titleText, bodyRuns) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
    rows: [ new TableRow({ children: [ new TableCell({
      borders, width: { size: 9360, type: WidthType.DXA },
      shading: { fill, type: ShadingType.CLEAR },
      margins: { top: 120, bottom: 120, left: 160, right: 160 },
      children: [
        new Paragraph({ spacing:{after:60}, children: [new TextRun({ text: titleText, bold: true })] }),
        new Paragraph({ children: bodyRuns })
      ]
    }) ] }) ]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: NAVY, font: "Arial" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: BLUE, font: "Arial" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ]
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level:0, format: LevelFormat.BULLET, text:"•", alignment: AlignmentType.LEFT,
      style:{ paragraph:{ indent:{ left:520, hanging:260 } } } }] },
    { reference: "stp", levels: [{ level:0, format: LevelFormat.DECIMAL, text:"%1.", alignment: AlignmentType.LEFT,
      style:{ paragraph:{ indent:{ left:520, hanging:260 } } } }] },
  ]},
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [ new Paragraph({
      alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 2 } },
      children: [ new TextRun({ text: "UNESCO SAP · Closing Activities · FX Revaluation (F.05 / SAPF100)", color: GREY, size: 16 }) ] }) ] }) },
    footers: { default: new Footer({ children: [ new Paragraph({
      tabStops: [{ type: "right", position: 9360 }],
      children: [ new TextRun({ text: "Confidential — internal", color: GREY, size: 16 }),
        new TextRun({ text: "\tPage ", color: GREY, size: 16 }),
        new TextRun({ children: [PageNumber.CURRENT], color: GREY, size: 16 }) ] }) ] }) },
    children: [
      // ===== Title block =====
      new Paragraph({ spacing: { before: 1200, after: 80 }, children: [ new TextRun({ text: "FX Revaluation — Root Cause, Fix & Improvement Opportunity", bold: true, size: 40, color: NAVY }) ] }),
      new Paragraph({ spacing: { after: 40 }, children: [ new TextRun({ text: "Program F.05 / SAPF100 · Company code UNES · Chart of accounts UNES", size: 22, color: GREY }) ] }),
      new Paragraph({ spacing: { after: 40 }, children: [ new TextRun({ text: "Evidence base: P01 production — T030H, SKB1, T012K, GLT0, BKPF/BSIS, VARI/VARIS + OB09/FS00 screens", size: 18, color: GREY }) ] }),
      new Paragraph({ spacing: { after: 800 }, children: [ new TextRun({ text: "Prepared by the UNESCO SAP Intelligence Platform · 2026-06-07 · Tier-1 evidence", size: 18, color: GREY }) ] }),

      new Paragraph({ children: [ new TextRun({ text: "Contents", bold: true, size: 24, color: NAVY }) ] }),
      new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
      new Paragraph({ children: [new PageBreak()] }),

      // ===== Executive summary =====
      H1("1. Executive Summary"),
      box(OKBG, "FX revaluation is one recurring step in the monthly / annual close. Today it is invisible and manual — and that is the real opportunity.",
        [ t("Every month, foreign-currency balances must be revalued (F.05 / SAPF100) across 9 company codes. Today this runs "),
          b("interactively, by individual accountants, with no scheduling, no execution visibility and no audit of whether it actually ran"),
          t(". The opportunity is not a bug fix — it is to "), b("automate this recurring task and instrument it for visibility"),
          t(": turn “we think it ran” into “the job log proves it ran, on time, completely.”") ]),
      spacer(),
      P([ b("The opportunity (primary). "), t("Schedule the close steps as background jobs and make their execution observable. For FX revaluation: SM36 jobs (the infrastructure already exists — "), code("SAPF124"), t(" clearing runs this way daily) eliminate "), b("missed months, timing lag, single-point-of-failure, and the absence of a sign-off gate"), t(" — all at once. The 78% timing improvement seen in 2026 was driven only by awareness; jobs make it structural and permanent.") ]),
      P([ b("How we know this (methodology: process mining). "), t("We reconstructed the entire reality of this process — who runs it, when, where the gaps are, the configuration and the root cause — purely by "), b("mining logs, data, tables and config"), t(" (BKPF/BSIS, GLT0, T030H, VARI/VARIS, OB09/FS00). No interviews, no guesswork. This is the lens we apply to every domain: read the system, not the documentation.") ]),
      P([ b("The error (minor, immediate). "), t("Along the way we found one small configuration item — an unfinished bank sub-account migration in OB09 — that throws a “blocked for posting” error for "), b("2 accounts"), t(". The fix is "), b("two OB09 entries"), t(". It is an immediate adjustment, not the headline.") ]),
      P([ b("The bigger picture. "), t("FX revaluation is one of "), b("many recurring close tasks"), t(". The same approach — process-mine to understand the reality, fix the immediate issues with full context, then automate and instrument for visibility — applies across "), b("every domain"), t(". This is how UNESCO SAP moves from reactive incident-handling to a system that knows itself and proves its own close was done.") ]),

      // ===== The configuration design =====
      H1("2. How the Configuration Works"),
      P("UNESCO revalues bank accounts in two valid patterns. Across the 944 accounts configured in T030H:"),
      table([3400, 3300, 1330, 1330],
        ["Pattern", "How it revalues", "Accounts", "Status"],
        [
          [{text:"Self-revaluation (HKONT = LKORR)"}, "The account is its own adjustment", {text:"555 (277 active)", align:AlignmentType.LEFT}, {text:"OK — dominant", fill:OKBG, color:GREEN, bold:true}],
          [{text:"Sub-account (BK → S-BK active)"}, "Adjustment posts to a separate active sub", "167 (163 active)", {text:"OK — e.g. Ecobank", fill:OKBG, color:GREEN, bold:true}],
          [{text:"Sub-account BROKEN (BK → closed sub)"}, "Same method, but the sub was closed", "6", {text:"THE ERROR", fill:BADBG, color:RED, bold:true}],
          [{text:"Empty LKORR"}, "No adjustment (mostly USD = local cur.)", "200 (134 active)", {text:"OK", fill:OKBG, color:GREEN}],
        ]),
      spacer(),
      H2("The 3-account design (sub-account pattern)"),
      table([2100, 4060, 1600, 1600],
        ["Role", "What it is", "Banco Chile CLP", "Ecobank ZWG"],
        [
          [{text:"BK (main)", bold:true}, "Operating account, holds cash. This is what F.05 revalues.", {text:"1010574"}, {text:"1094316"}],
          [{text:"S-BK (active sub)", bold:true}, "Adjustment account — receives the FX delta. The LKORR in OB09.", {text:"1110574", color:GREEN, bold:true}, {text:"1194316", color:GREEN, bold:true}],
          [{text:"CLOSED S-BK (old sub)", bold:true}, "Previous sub, retired and blocked.", {text:"1109574"}, {text:"1194314"}],
        ]),
      P([ b("Numbering convention: "), t("active sub = main + 100000  ("), code("1094316 + 100000 = 1194316"), t(" ✓;  "), code("1010574 + 100000 = 1110574"), t(" ✓).") ], { spacing:{before:120, after:120} }),

      // ===== Why it fails =====
      H1("3. Why Ecobank Works and Banco de Chile Fails"),
      P("Same design, different maintenance:"),
      box(OKBG, "Ecobank — correct",
        [ code("1094316 (BK) → LKORR 1194316 (S-BK active)"), t("   — points to the active sub, valuation posts cleanly.") ]),
      spacer(),
      box(BADBG, "Banco de Chile — broken",
        [ code("1010574 (BK) → LKORR 1109574 (CLOSED)"), t("   — should be "), code("1110574"), t(" (active sub). The sub was migrated (old "), code("1109574"), t(" closed → new "), code("1110574"), t("), but OB09 was never updated → "), b("“Account 1109574 blocked for posting.”") ]),
      spacer(),
      P([ b("Two conditions for the runtime error: "), t("(1) the config points to a closed sub, and (2) the main account carries an FX balance to revalue. No balance → no revaluation → no error.") ]),

      // ===== Fix =====
      H1("4. The Fix — Repoint OB09 (Tactical)"),
      P([ b("Do NOT unblock the closed subs"), t(" — they were retired on purpose. Finish the migration: repoint the 2 in-scope main accounts to their active sub.") ]),
      table([2600, 3380, 3380],
        ["Account", "LKORR now (wrong)", "LKORR correct"],
        [
          [{text:"1010574  (CLP)"}, {text:"1109574  (CLOSED)"}, {text:"1110574  (S-BK active)", color:GREEN, bold:true}],
          [{text:"1010571  (USD)"}, {text:"1109571  (CLOSED)"}, {text:"1110571  (S-BK active)", color:GREEN, bold:true}],
        ]),
      P([ t("Transaction: "), code("OB09"), t(" (KDF account determination). Effort: 2 config entries. "), b("Confirm with Treasury/accounting"), t(" that "), code("1110574 / 1110571"), t(" is the intended migration target before applying.") ], { spacing:{before:120, after:80} }),
      P([ b("Also fix in the same pass (hygiene, out of current scope): "), code("1143254"), t(" (Citibank Dakar) points to a VND account, and "), code("1194316"), t(" (Ecobank ZWG) points to the old ZWL sub.") ]),

      // ===== Opportunity =====
      H1("5. The Bigger Opportunity — Automate F.05 (Strategic)"),
      box(OKBG, "The OB09 fix removes one error. Scheduling F.05 as background jobs removes an entire class of problems — and the infrastructure already exists.",
        [ t("Today there are "), b("zero SAPF100 background jobs"), t("; all FX revaluation is launched interactively by individual accountants. Meanwhile "), code("SAPF124"), t(" (automatic clearing) already runs "), b("daily as a JOBBATCH job"), t(" — the exact template to copy.") ]),
      spacer(),
      table([4000, 2680, 2680],
        ["Problem today (manual)", "Evidence", "After SM36 jobs"],
        [
          ["Missed months (period closes with no FX revaluation, undetected)", "ICTP missed Jul + Nov 2025 and May 2026 (single user, no backup)", {text:"Runs regardless of who is present", fill:OKBG}],
          ["Timing lag (posted days/weeks after month-end)", "2025 avg up to ~18–24d; 2026 improved but still manual", {text:"CPUDT = BUDAT, zero lag", fill:OKBG}],
          ["Single-point-of-failure (one accountant, no backup)", "ICTP, UBO; ad-hoc cross-coverage in May 2026", {text:"No human dependency for the run", fill:OKBG}],
          ["No sign-off gate (OB52 locks without checking FX)", "ICTP gaps found by data mining months later", {text:"Job log = sign-off evidence", fill:OKBG}],
          ["No audit trail of “did it run?”", "Reconstructed manually from BKPF", {text:"SM37 job history, automatic", fill:OKBG}],
        ]),
      P([ b("Low-risk, high-value: "), t("the pattern is already proven in this system. The 78% timing improvement seen in 2026 was driven only by awareness — jobs would make it "), b("structural and permanent"), t(".") ], { spacing:{before:120} }),

      // ===== Recommendations =====
      H1("6. Recommended Actions"),
      num([ b("Confirm the migration target"), t(" with Treasury/accounting ("), code("1110574 / 1110571"), t(" = the active adjustment sub).") ]),
      num([ b("Repoint OB09"), t(" for the 2 in-scope accounts (and fix the Citibank/Ecobank mis-mappings in the same change).") ]),
      num([ b("Verify"), t(" with an F.05 test run — no “blocked for posting” error.") ]),
      num([ b("Schedule SM36 jobs for SAPF100"), t(" per company code (valuation + reversal), under JOBBATCH — the strategic fix.") ]),
      num([ b("Add an FX sign-off gate"), t(" before OB52 period lock (the job log becomes the evidence).") ]),
      num([ b("Close the ICTP coverage gap"), t(" (no balance variant) and assign backups for single-user institutes until jobs remove the dependency.") ]),

      spacer(),
      new Paragraph({ border: { top: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 4 } },
        spacing: { before: 200 },
        children: [ new TextRun({ text: "Living source of truth: knowledge/domains/Closing_Activities/fx_revaluation_process.md  ·  Visual companion: companions/closing_activities_v1.html", italics: true, color: GREY, size: 16 }) ] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = "C:\\Users\\jp_lopez\\projects\\abapobjectscreation\\companions\\FX_Revaluation_Conclusions.docx";
  fs.writeFileSync(out, buf);
  console.log("Saved: " + out + "  (" + buf.length + " bytes)");
});
