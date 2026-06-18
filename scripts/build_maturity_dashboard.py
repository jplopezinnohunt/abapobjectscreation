"""
build_maturity_dashboard.py — GENERATES companions/model_maturity_dashboard.html
================================================================================
Living visual of the exploration-model maturity (Layer 15). Reads the deterministic
scores (brain_v2/capability_model/maturity.json) + the matrix (capability_model.json)
and renders a single self-contained HTML (pure CSS, no external libs, offline-safe).
NEVER edit the HTML by hand — edit the matrix, re-run maturity_score.py, then this.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CM = ROOT / "brain_v2" / "capability_model" / "capability_model.json"
MAT = ROOT / "brain_v2" / "capability_model" / "maturity.json"
OUT = ROOT / "companions" / "model_maturity_dashboard.html"

CELL_COLOR = {"HAVE": "#1f9d55", "PARTIAL": "#d69e2e", "NONE": "#3a4252"}
CELL_GLYPH = {"HAVE": "●", "PARTIAL": "◐", "NONE": "○"}
PATH_COLOR = {"NO_EXTRACTION": "#1f9d55", "EXTRACTION": "#c05621", "MIXED": "#3182ce"}
TIER_BADGE = {"VERIFIED": "#1f9d55", "OWN": "#3182ce", "GAP": "#c53030"}


def bar(pct, color):
    return (f'<div class="bar"><div class="fill" style="width:{pct}%;background:{color}"></div>'
            f'<span class="bval">{pct}%</span></div>')


def build():
    cm = json.load(open(CM, encoding="utf-8"))
    m = json.load(open(MAT, encoding="utf-8"))
    dims = list(cm["dimensions"].keys())
    short = {d: d.split("_")[0] if d[1] == "_" else d[:4] for d in dims}

    # ---- Level 1: capability bars ----
    cap_rows = ""
    for d, v in m["level1_by_capability"].items():
        tier = v["method_tier"]
        badge = f'<span class="badge" style="background:{TIER_BADGE.get(tier,"#555")}">{tier}</span>'
        pth = v["advance_path"]
        pchip = f'<span class="chip" style="border-color:{PATH_COLOR[pth]};color:{PATH_COLOR[pth]}">{pth.replace("_"," ").lower()}</span>'
        col = PATH_COLOR[pth] if v["maturity_pct"] > 0 else "#4a5568"
        cap_rows += (f'<tr><td class="dim">{d}</td><td class="bcell">{bar(v["maturity_pct"], col)}</td>'
                     f'<td>{badge}</td><td>{pchip}</td>'
                     f'<td class="cnt">●{v["have"]} ◐{v["partial"]} ○{v["none"]}</td></tr>')

    # ---- Level 2: domain bars ----
    dom_rows = ""
    for n, v in m["level2_by_domain"].items():
        pc = v["maturity_pct"]
        col = "#1f9d55" if pc >= 40 else "#d69e2e" if pc >= 20 else "#c05621"
        dom_rows += f'<tr><td class="dim">{n}</td><td class="bcell">{bar(pc, col)}</td></tr>'

    # ---- Heatmap matrix ----
    head = "".join(f'<th class="rot"><div>{short[d]}</div></th>' for d in dims)
    body = ""
    for n, v in m["level2_by_domain"].items():
        cells = ""
        for d in dims:
            val = v["cells"][d]
            cells += f'<td class="hc" style="background:{CELL_COLOR[val]}" title="{n} / {d}: {val}">{CELL_GLYPH[val]}</td>'
        body += f'<tr><td class="rowh">{n}</td>{cells}<td class="rowp">{v["maturity_pct"]}%</td></tr>'

    gs = m["gap_split"]
    model_pct = m["model_maturity_pct"]
    ring = f"conic-gradient(#1f9d55 0% {model_pct}%, #2d3340 {model_pct}% 100%)"

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exploration Model — Maturity Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f1318;color:#e6edf3;font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:28px}}
h1{{font-size:22px;font-weight:700;margin-bottom:2px}}
.sub{{color:#8b97a7;font-size:13px;margin-bottom:22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-bottom:24px}}
.card{{background:#161b22;border:1px solid #232a34;border-radius:12px;padding:18px}}
.kpi{{font-size:34px;font-weight:800}}
.klbl{{color:#8b97a7;font-size:12px;text-transform:uppercase;letter-spacing:.5px;margin-top:4px}}
.ring{{width:120px;height:120px;border-radius:50%;background:{ring};display:flex;align-items:center;justify-content:center;margin:0 auto}}
.ring .inner{{width:88px;height:88px;border-radius:50%;background:#161b22;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.ring .pc{{font-size:26px;font-weight:800}}
.sec{{font-size:15px;font-weight:700;margin:26px 0 12px;border-left:3px solid #1f9d55;padding-left:9px}}
table{{width:100%;border-collapse:collapse}}
.dim{{font-family:ui-monospace,monospace;font-size:12.5px;white-space:nowrap;padding:5px 10px 5px 0;color:#cbd5e0}}
.bcell{{width:100%}}
.bar{{position:relative;background:#222932;border-radius:6px;height:22px;overflow:hidden}}
.fill{{height:100%;border-radius:6px;transition:width .4s}}
.bval{{position:absolute;right:8px;top:0;line-height:22px;font-size:12px;font-weight:600}}
.badge{{font-size:10px;font-weight:700;color:#fff;padding:2px 7px;border-radius:10px}}
.chip{{font-size:10.5px;border:1px solid;padding:1px 7px;border-radius:10px;white-space:nowrap}}
.cnt{{font-size:11px;color:#8b97a7;white-space:nowrap}}
td{{padding:4px 8px 4px 0;vertical-align:middle}}
.heat{{border-collapse:separate;border-spacing:2px}}
.heat th.rot{{height:70px;vertical-align:bottom}}
.heat th.rot div{{writing-mode:vertical-rl;transform:rotate(195deg);font-size:11px;color:#8b97a7;font-weight:600;white-space:nowrap}}
.heat .rowh{{font-size:12px;color:#cbd5e0;white-space:nowrap;padding-right:8px;text-align:right}}
.hc{{width:30px;height:26px;text-align:center;color:#fff;font-size:13px;border-radius:4px}}
.rowp{{font-weight:700;font-size:12px;padding-left:6px}}
.leg{{display:flex;gap:18px;flex-wrap:wrap;color:#8b97a7;font-size:12px;margin-top:12px}}
.leg span b{{color:#e6edf3}}
.dot{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:4px}}
.foot{{color:#5c6878;font-size:11px;margin-top:26px;border-top:1px solid #232a34;padding-top:12px}}
</style></head><body>
<h1>Exploration Model — Maturity Dashboard</h1>
<div class="sub">Layer 15 · domain × capability · deterministic (NONE=0 · PARTIAL=0.5 · HAVE=1.0) · regenerated from maturity.json</div>

<div class="grid">
  <div class="card" style="text-align:center"><div class="ring"><div class="inner"><div class="pc">{model_pct}%</div><div style="font-size:10px;color:#8b97a7">MODEL</div></div></div><div class="klbl" style="text-align:center">Exploration model maturity</div></div>
  <div class="card"><div class="kpi">{gs['pct_gap_reachable_without_extraction']}%</div><div class="klbl">of the gap reachable WITHOUT new extraction</div></div>
  <div class="card"><div class="kpi">{m['n_domains']}×{m['n_capabilities']}</div><div class="klbl">domains × capabilities scored</div></div>
  <div class="card"><div class="kpi" style="color:#c05621">{gs['extraction_units']}</div><div class="klbl">gap units needing SAP extraction (of {gs['total_gap_units']})</div></div>
</div>

<div class="sec">Level 1 — Maturity by CAPABILITY (theme)</div>
<table>{cap_rows}</table>
<div class="leg">
  <span><span class="dot" style="background:#1f9d55"></span><b>VERIFIED</b> method exists</span>
  <span><span class="dot" style="background:#3182ce"></span><b>OWN</b> design</span>
  <span><span class="dot" style="background:#c53030"></span><b>GAP</b> no method yet</span>
  <span><span class="chip" style="border-color:#1f9d55;color:#1f9d55">no extraction</span> doable now</span>
  <span><span class="chip" style="border-color:#c05621;color:#c05621">extraction</span> needs SAP pull</span>
</div>

<div class="sec">Level 2 — Maturity by DOMAIN</div>
<table>{dom_rows}</table>

<div class="sec">Matrix — domain × capability</div>
<table class="heat"><tr><th></th>{head}<th></th></tr>{body}</table>
<div class="leg">
  <span><span class="dot" style="background:#1f9d55"></span>● HAVE</span>
  <span><span class="dot" style="background:#d69e2e"></span>◐ PARTIAL</span>
  <span><span class="dot" style="background:#3a4252"></span>○ NONE</span>
  <span>Empty columns (S_STANDARD_REF · E_AUTH · G_CONFORMANCE · R_S4_READINESS) = systemic model gaps</span>
</div>

<div class="foot">Generated by scripts/build_maturity_dashboard.py from brain_v2/capability_model/maturity.json.
A domain = AS-DESIGNED (standard SAP) + AS-RUN (ours); G = the delta. Source of truth: capability_model.json (Layer 15).</div>
</body></html>"""
    OUT.write_text(html, encoding="utf-8")
    print(f"model maturity {model_pct}% · {m['n_domains']}x{m['n_capabilities']} · saved: {OUT}")


if __name__ == "__main__":
    build()
