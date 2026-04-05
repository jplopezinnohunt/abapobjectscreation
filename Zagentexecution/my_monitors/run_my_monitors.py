"""
run_my_monitors.py — Personal on-demand monitor bundle (G60)

Session #038 · 2026-04-05

What this is
------------
A single launcher that produces ONE self-contained HTML dashboard with two
tabs showing the things JP_LOPEZ actually wants to glance at:

  Tab 1 — BCM Dual-Control
    Same-user batch trend, top operators, $ exposure, per-year drift.
    Source: Gold DB `BNK_BATCH_HEADER` (H13 finding from Session #037).

  Tab 2 — Basis Health
    Background jobs: recent failures, top authors, job volume by status.
    Custom object inventory by type (TADIR Z* counts via Gold DB cache).
    Source: Gold DB `TBTCO`, `TFDIR_CUSTOM`, `ICFSERVICE`.

What this is NOT
----------------
- Not a cron job. Not a scheduled task. Not an email sender.
- Not a replacement for `sap_system_monitor.py` (live SM04/SM37/ST22).
- Not a production monitoring tool.

This is a local, on-demand snapshot that JP runs when he wants the picture.
No infra. No ops. No deployment. Runs offline against the Gold DB.

Usage
-----
    python Zagentexecution/my_monitors/run_my_monitors.py
    # → generates my_monitors_dashboard.html next to this script
    # → open the HTML in a browser

If Gold DB is stale (last extraction was weeks ago), the dashboard shows
the freshness timestamp prominently so you know what you're looking at.
"""

from __future__ import annotations

import io
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
GOLD_DB = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
HTML_OUT = HERE / "my_monitors_dashboard.html"


# ---------------------------------------------------------------------------
# Data collectors
# ---------------------------------------------------------------------------


def collect_bcm(conn: sqlite3.Connection) -> dict:
    """Tab 1 — BCM dual-control facts from BNK_BATCH_HEADER."""
    cur = conn.cursor()
    data: dict = {}

    # Total batches in scope 2024-2026
    data["total_batches"] = cur.execute("""
        SELECT COUNT(*) FROM BNK_BATCH_HEADER
        WHERE substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
    """).fetchone()[0]

    # Same-user (CRUSR = CHUSR) — the H13 finding
    data["same_user_total"] = cur.execute("""
        SELECT COUNT(*) FROM BNK_BATCH_HEADER
        WHERE CRUSR = CHUSR AND CRUSR != ''
          AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
    """).fetchone()[0]

    # $ exposure in local ccy (BATCH_SUM is signed numeric text — cast)
    total_sum = cur.execute("""
        SELECT SUM(CAST(BATCH_SUM AS REAL))
        FROM BNK_BATCH_HEADER
        WHERE CRUSR = CHUSR AND CRUSR != ''
          AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
    """).fetchone()[0] or 0
    data["same_user_sum_loc"] = total_sum

    # Breakdown by year
    data["by_year"] = cur.execute("""
        SELECT substr(CRDATE, 1, 4) AS y, COUNT(*), SUM(CAST(BATCH_SUM AS REAL))
        FROM BNK_BATCH_HEADER
        WHERE CRUSR = CHUSR AND CRUSR != ''
          AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
        GROUP BY y
        ORDER BY y
    """).fetchall()

    # Top 10 same-user operators
    data["top_users"] = cur.execute("""
        SELECT CRUSR, COUNT(*) AS n, SUM(CAST(BATCH_SUM AS REAL)) AS total
        FROM BNK_BATCH_HEADER
        WHERE CRUSR = CHUSR AND CRUSR != ''
          AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
        GROUP BY CRUSR
        ORDER BY n DESC
        LIMIT 10
    """).fetchall()

    # Day-of-week distribution for top operator (Wednesday cycle signature)
    # CRDATE format = YYYYMMDD
    def dow_dist(user: str) -> list:
        rows = cur.execute("""
            SELECT CRDATE FROM BNK_BATCH_HEADER
            WHERE CRUSR = ? AND CRUSR = CHUSR
              AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
        """, (user,)).fetchall()
        dow = Counter()
        for (d,) in rows:
            if len(d) == 8:
                try:
                    wd = datetime.strptime(d, "%Y%m%d").strftime("%A")
                    dow[wd] += 1
                except ValueError:
                    pass
        return dow.most_common(7)

    if data["top_users"]:
        top_user = data["top_users"][0][0]
        data["top_user_dow"] = dow_dist(top_user)
        data["top_user_name"] = top_user

    # CUR_STS distribution (the corrected filter per #037)
    data["by_cur_sts"] = cur.execute("""
        SELECT CUR_STS, COUNT(*) FROM BNK_BATCH_HEADER
        WHERE CRUSR = CHUSR AND CRUSR != ''
          AND substr(CRDATE, 1, 4) BETWEEN '2024' AND '2026'
        GROUP BY CUR_STS
        ORDER BY COUNT(*) DESC
    """).fetchall()

    return data


def collect_basis(conn: sqlite3.Connection) -> dict:
    """Tab 2 — Basis health facts from TBTCO + TFDIR_CUSTOM + ICFSERVICE."""
    cur = conn.cursor()
    data: dict = {}

    # Job volume + recent status
    data["job_total"] = cur.execute("SELECT COUNT(*) FROM TBTCO").fetchone()[0]
    data["jobs_by_status"] = cur.execute("""
        SELECT STATUS, COUNT(*) FROM TBTCO
        GROUP BY STATUS ORDER BY COUNT(*) DESC
    """).fetchall()

    # Recent aborted jobs (STATUS='A') — current year
    year_start = datetime.now().strftime("%Y") + "0101"
    data["jobs_recent_failed"] = cur.execute("""
        SELECT JOBNAME, STRTDATE, AUTHCKNAM
        FROM TBTCO
        WHERE STATUS = 'A'
          AND STRTDATE >= ?
        ORDER BY STRTDATE DESC LIMIT 25
    """, (year_start,)).fetchall()

    # Top job authors (who owns the most scheduled jobs)
    data["top_authors"] = cur.execute("""
        SELECT AUTHCKNAM, COUNT(*) FROM TBTCO
        WHERE AUTHCKNAM != ''
        GROUP BY AUTHCKNAM ORDER BY COUNT(*) DESC LIMIT 15
    """).fetchall()

    # Custom object inventory from TFDIR_CUSTOM (function modules classification)
    data["tfdir_total"] = cur.execute("SELECT COUNT(*) FROM TFDIR_CUSTOM").fetchone()[0]
    data["rfc_enabled"] = cur.execute(
        "SELECT COUNT(*) FROM TFDIR_CUSTOM WHERE FMODE = 'R'"
    ).fetchone()[0]

    # ICF services (HTTP endpoints)
    data["icf_services"] = cur.execute("SELECT COUNT(*) FROM ICFSERVICE").fetchone()[0]

    # Gold DB freshness — max CRDATE from BNK_BATCH_HEADER as a proxy
    data["last_batch"] = cur.execute(
        "SELECT MAX(CRDATE) FROM BNK_BATCH_HEADER"
    ).fetchone()[0]

    return data


# ---------------------------------------------------------------------------
# HTML rendering (inline CSS, no CDN, per feedback_visjs_inline.md)
# ---------------------------------------------------------------------------


def money(x: float) -> str:
    if x is None:
        return "—"
    absx = abs(x)
    if absx >= 1_000_000_000:
        return f"${x/1_000_000_000:,.2f}B"
    if absx >= 1_000_000:
        return f"${x/1_000_000:,.1f}M"
    if absx >= 1_000:
        return f"${x/1_000:,.0f}K"
    return f"${x:,.0f}"


def render_html(bcm: dict, basis: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pct_sameuser = 100 * bcm["same_user_total"] / max(1, bcm["total_batches"])

    # BCM year table rows
    year_rows = "".join(
        f"<tr><td>{y}</td><td>{n:,}</td><td>{money(s)}</td></tr>"
        for y, n, s in bcm["by_year"]
    )
    # BCM top users table
    top_rows = "".join(
        f"<tr><td>{u}</td><td>{n:,}</td><td>{money(t)}</td></tr>"
        for u, n, t in bcm["top_users"]
    )
    # DOW bars for top user
    dow_rows = ""
    if bcm.get("top_user_dow"):
        max_n = max(n for _, n in bcm["top_user_dow"])
        for day, n in bcm["top_user_dow"]:
            w = int(300 * n / max_n)
            dow_rows += (
                f'<div class="bar-row"><span class="bar-label">{day}</span>'
                f'<span class="bar" style="width:{w}px"></span>'
                f'<span class="bar-val">{n:,}</span></div>'
            )
    # CUR_STS
    sts_rows = "".join(
        f"<tr><td><code>{s or '(empty)'}</code></td><td>{n:,}</td></tr>"
        for s, n in bcm["by_cur_sts"]
    )

    # Basis
    job_sts_rows = "".join(
        f"<tr><td><code>{s}</code></td><td>{n:,}</td></tr>"
        for s, n in basis["jobs_by_status"]
    )
    author_rows = "".join(
        f"<tr><td>{a}</td><td>{n:,}</td></tr>"
        for a, n in basis["top_authors"]
    )
    failed_rows = "".join(
        f"<tr><td>{j}</td><td>{d}</td><td>{a}</td></tr>"
        for j, d, a in basis["jobs_recent_failed"]
    )

    last_batch = basis.get("last_batch") or "—"
    if last_batch and len(last_batch) == 8:
        last_batch = f"{last_batch[:4]}-{last_batch[4:6]}-{last_batch[6:8]}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>My Monitors — JP Lopez Personal Dashboard</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 0; background: #0d1117; color: #c9d1d9; }}
  .header {{ background: #161b22; padding: 20px 30px;
             border-bottom: 1px solid #30363d; }}
  .header h1 {{ margin: 0; color: #58a6ff; font-size: 24px; }}
  .header .sub {{ color: #8b949e; font-size: 13px; margin-top: 4px; }}
  .tabs {{ background: #161b22; border-bottom: 1px solid #30363d;
           padding: 0 30px; display: flex; gap: 4px; }}
  .tab {{ padding: 12px 24px; cursor: pointer; color: #8b949e;
          border-bottom: 2px solid transparent; font-size: 14px; }}
  .tab:hover {{ color: #c9d1d9; }}
  .tab.active {{ color: #58a6ff; border-bottom-color: #58a6ff; }}
  .panel {{ display: none; padding: 30px; max-width: 1400px; }}
  .panel.active {{ display: block; }}
  .kpi-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .kpi {{ background: #161b22; border: 1px solid #30363d;
          border-radius: 8px; padding: 16px 20px; flex: 1; min-width: 200px; }}
  .kpi .label {{ color: #8b949e; font-size: 12px; text-transform: uppercase;
                  letter-spacing: 0.5px; }}
  .kpi .value {{ color: #58a6ff; font-size: 28px; font-weight: 600;
                  margin-top: 6px; }}
  .kpi .value.red {{ color: #f85149; }}
  .kpi .value.yellow {{ color: #d29922; }}
  .kpi .sub {{ color: #8b949e; font-size: 11px; margin-top: 4px; }}
  .section {{ background: #161b22; border: 1px solid #30363d;
              border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
  .section h2 {{ margin: 0 0 12px 0; color: #c9d1d9; font-size: 16px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px 12px; text-align: left;
            border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; font-weight: 600; font-size: 11px;
        text-transform: uppercase; }}
  code {{ background: #21262d; padding: 2px 6px; border-radius: 3px;
          font-size: 12px; color: #79c0ff; }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; margin: 4px 0; }}
  .bar-label {{ min-width: 100px; color: #8b949e; font-size: 12px; }}
  .bar {{ display: inline-block; height: 18px;
          background: linear-gradient(90deg, #238636, #58a6ff); border-radius: 3px; }}
  .bar-val {{ color: #c9d1d9; font-size: 12px; min-width: 60px; }}
  .freshness {{ background: #1f2937; border-left: 3px solid #d29922;
                padding: 8px 12px; margin-bottom: 20px; font-size: 12px; }}
</style>
</head>
<body>

<div class="header">
  <h1>My Monitors — Personal Dashboard</h1>
  <div class="sub">On-demand snapshot · {now} · Owner: JP_LOPEZ · No cron, no infra, no deployment</div>
</div>

<div class="tabs">
  <div class="tab active" onclick="show('bcm')">💸 BCM Dual-Control</div>
  <div class="tab" onclick="show('basis')">⚙️ Basis Health</div>
</div>

<div id="panel-bcm" class="panel active">
  <div class="freshness">
    Gold DB data · last batch: <b>{last_batch}</b> · scope 2024-2026 ·
    same-user (CRUSR=CHUSR) filter applied · source H13 Session #037
  </div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="label">Same-user batches</div>
      <div class="value red">{bcm['same_user_total']:,}</div>
      <div class="sub">of {bcm['total_batches']:,} total ({pct_sameuser:.1f}%)</div>
    </div>
    <div class="kpi">
      <div class="label">Local-ccy exposure</div>
      <div class="value red">{money(bcm['same_user_sum_loc'])}</div>
      <div class="sub">unconverted — mixed currencies</div>
    </div>
    <div class="kpi">
      <div class="label">Top operator</div>
      <div class="value yellow">{bcm.get('top_user_name', '—')}</div>
      <div class="sub">see Wednesday signature below</div>
    </div>
  </div>

  <div class="section">
    <h2>Breakdown by year</h2>
    <table>
      <thead><tr><th>Year</th><th>Same-user batches</th><th>Sum (loc ccy)</th></tr></thead>
      <tbody>{year_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Top 10 same-user operators</h2>
    <table>
      <thead><tr><th>User</th><th>Batches</th><th>Sum</th></tr></thead>
      <tbody>{top_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Top operator — day-of-week signature (Wednesday cycle?)</h2>
    {dow_rows}
  </div>

  <div class="section">
    <h2>Status distribution (CUR_STS)</h2>
    <table>
      <thead><tr><th>CUR_STS</th><th>Count</th></tr></thead>
      <tbody>{sts_rows}</tbody>
    </table>
  </div>
</div>

<div id="panel-basis" class="panel">
  <div class="freshness">
    Gold DB cache · TBTCO {basis['job_total']:,} jobs ·
    TFDIR_CUSTOM {basis['tfdir_total']:,} FMs ({basis['rfc_enabled']:,} RFC-enabled) ·
    ICFSERVICE {basis['icf_services']:,} HTTP endpoints
  </div>

  <div class="kpi-row">
    <div class="kpi">
      <div class="label">Background jobs</div>
      <div class="value">{basis['job_total']:,}</div>
      <div class="sub">TBTCO total</div>
    </div>
    <div class="kpi">
      <div class="label">Custom function modules</div>
      <div class="value">{basis['tfdir_total']:,}</div>
      <div class="sub">{basis['rfc_enabled']:,} RFC-enabled</div>
    </div>
    <div class="kpi">
      <div class="label">ICF services</div>
      <div class="value">{basis['icf_services']:,}</div>
      <div class="sub">HTTP endpoints</div>
    </div>
  </div>

  <div class="section">
    <h2>Jobs by status</h2>
    <table>
      <thead><tr><th>Status</th><th>Count</th></tr></thead>
      <tbody>{job_sts_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Top 15 job authors</h2>
    <table>
      <thead><tr><th>Author</th><th>Jobs</th></tr></thead>
      <tbody>{author_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Recent aborted jobs (last 25)</h2>
    <table>
      <thead><tr><th>Job name</th><th>Start date</th><th>Author</th></tr></thead>
      <tbody>{failed_rows}</tbody>
    </table>
  </div>
</div>

<script>
function show(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
}}
</script>

</body>
</html>"""


def main() -> int:
    print("=" * 60)
    print("  My Monitors — Personal Dashboard Generator (G60)")
    print("=" * 60)

    if not GOLD_DB.exists():
        print(f"[FATAL] Gold DB not found: {GOLD_DB}")
        return 1

    print(f"\n[GOLD DB] {GOLD_DB}")
    conn = sqlite3.connect(GOLD_DB)
    try:
        print("[COLLECT] BCM dual-control facts...")
        bcm = collect_bcm(conn)
        print(f"  same-user batches: {bcm['same_user_total']:,} "
              f"/ {bcm['total_batches']:,} total")

        print("[COLLECT] Basis health facts...")
        basis = collect_basis(conn)
        print(f"  jobs: {basis['job_total']:,} · "
              f"FMs: {basis['tfdir_total']:,} · "
              f"ICF: {basis['icf_services']:,}")
    finally:
        conn.close()

    print("\n[RENDER] HTML dashboard...")
    html = render_html(bcm, basis)
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"[OUT] {HTML_OUT}  ({len(html):,} bytes)")

    print(f"\n✅ Done. Open with:")
    print(f"   start {HTML_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
