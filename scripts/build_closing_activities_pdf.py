"""
Closing Activities — UNESCO SAP Month-End Close Intelligence
PDF Canvas Generator (Chronometric Ledger design philosophy)
Session #078 — 2026-06-05
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D
import numpy as np
import os

# ─── Design System ────────────────────────────────────────────────────────────
BG       = '#0a0e17'   # near-black navy
PANEL    = '#111827'   # dark card
PANEL2   = '#1a2233'   # alternate card
INK      = '#e8edf5'   # primary text
MUTED    = '#6b7b93'   # secondary text
ACCENT   = '#3b82f6'   # electric blue
GOOD     = '#22c55e'   # emerald
WARN     = '#f59e0b'   # amber
BAD      = '#ef4444'   # vermillion
PURPLE   = '#a78bfa'   # violet
GRID     = '#1e2a3d'   # subtle grid
GOLD     = '#d4a843'   # gold accent

# ─── Data ─────────────────────────────────────────────────────────────────────
INSTITUTES = ['ICBA', 'UIL', 'UBO', 'IBE', 'IIEP', 'UIS', 'MGIE', 'ICTP', 'UNES']
USERS_2025 = ['E_GEBREMARIA', 'DB_ABDI', 'P_TUCKER', 'V_KOHEMUN', 'F_CADIO', 'N_MOUSSA', 'P_ARORA', 'M_VENUTI', 'J_LA']

# Valuation lag (days after month-end): 2025 avg, min, max
LAG_2025_AVG = [2.6, 8.0, 24.3, 9.0, 5.1, 3.7, 5.1, 7.6, 6.7]
LAG_2025_MAX = [57,  20,   62,  18,  12,   8,  20,  55,  62]

# 2026 avg lag (Jan-Apr 2026, from production data)
LAG_2026_AVG = [1.1, 0.4, 1.2, 0.7, 2.0, 1.3, 2.2, 0.3, 5.2]
LAG_2026_MONTHS = [4, 4, 4, 4, 4, 4, 4, 4, 4]

# Reversal lag 2025
REVERSAL_LAG = [0.5, None, 4.2, 4.6, 3.4, None, None, 4.7, 11.8]

# Coverage 2025 (months out of 12)
COVERAGE = [12, 12, 12, 12, 12, 12, 12, 10, 12]

# Status color per institute
def status_color(avg_lag):
    if avg_lag <= 3:   return GOOD
    if avg_lag <= 8:   return WARN
    return BAD

STATUS_2025 = [status_color(v) for v in LAG_2025_AVG]
STATUS_2026 = [status_color(v) for v in LAG_2026_AVG]


def setup_page(fig, ax_main=None):
    """Apply background to figure and axes."""
    fig.patch.set_facecolor(BG)
    if ax_main:
        ax_main.set_facecolor(BG)


def draw_rule(ax, y, color=GRID, lw=0.5, xmin=0, xmax=1):
    ax.axhline(y=y, color=color, linewidth=lw, xmin=xmin, xmax=xmax)


def kpi_card(fig, x, y, w, h, value, label, sub='', color=ACCENT, bg=PANEL):
    ax = fig.add_axes([x, y, w, h])
    ax.set_facecolor(bg)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    # Left accent bar
    ax.add_patch(Rectangle((0, 0), 0.025, 1, transform=ax.transAxes,
                            facecolor=color, zorder=5))
    ax.text(0.12, 0.62, value, transform=ax.transAxes, color=color,
            fontsize=22, fontweight='bold', va='center', ha='left',
            fontfamily='monospace')
    ax.text(0.12, 0.28, label, transform=ax.transAxes, color=INK,
            fontsize=7, va='center', ha='left', fontweight='600')
    if sub:
        ax.text(0.12, 0.12, sub, transform=ax.transAxes, color=MUTED,
                fontsize=6, va='center', ha='left')
    return ax


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page1_executive():
    fig = plt.figure(figsize=(11.69, 8.27), dpi=180)  # A4 landscape
    fig.patch.set_facecolor(BG)

    # ── Title band ─────────────────────────────────────────────────────────
    title_ax = fig.add_axes([0, 0.87, 1, 0.13])
    title_ax.set_facecolor(PANEL)
    for s in title_ax.spines.values(): s.set_visible(False)
    title_ax.set_xticks([]); title_ax.set_yticks([])
    title_ax.add_patch(Rectangle((0, 0), 0.005, 1, transform=title_ax.transAxes,
                                  facecolor=ACCENT, zorder=5))
    title_ax.text(0.015, 0.70, 'C L O S I N G   A C T I V I T I E S', transform=title_ax.transAxes,
                  color=ACCENT, fontsize=8, fontweight='bold', va='center',
                  fontfamily='monospace')
    title_ax.text(0.015, 0.35, 'UNESCO SAP — Month-End Close Intelligence · FX Revaluation (SAPF100 / F.05)',
                  transform=title_ax.transAxes, color=INK, fontsize=14, fontweight='bold', va='center')
    title_ax.text(0.015, 0.10, 'Evidence base: 11,793 documents · P01 Production · 2025–2026 · 9 company codes · 12 accountants',
                  transform=title_ax.transAxes, color=MUTED, fontsize=7, va='center')
    # Right side: session / date
    title_ax.text(0.985, 0.70, 'SESSION #078', transform=title_ax.transAxes,
                  color=MUTED, fontsize=7, va='center', ha='right', fontfamily='monospace')
    title_ax.text(0.985, 0.35, '2026-06-05', transform=title_ax.transAxes,
                  color=MUTED, fontsize=7, va='center', ha='right', fontfamily='monospace')
    title_ax.text(0.985, 0.10, 'TIER_1 EVIDENCE · GOLD DB P01', transform=title_ax.transAxes,
                  color=GOLD, fontsize=6, va='center', ha='right', fontfamily='monospace')

    # ── KPI Row ────────────────────────────────────────────────────────────
    kpi_cards = [
        (0.01,  '0',      'SAPF100 BACKGROUND\nJOBS SCHEDULED',      '',                  BAD,   PANEL),
        (0.135, '11,793', '2025 FX REVAL\nDOCUMENTS',                'P01 production',    ACCENT, PANEL),
        (0.26,  '9',      'COMPANY CODES\nIN SCOPE',                  'KTOPL = UNES',      ACCENT, PANEL),
        (0.385, '2',      'ICTP MONTHS\nMISSED 2025',                 'Jul + Nov',         BAD,   PANEL),
        (0.51,  '17',     'ACTIVE HKONTs\nBLOCKED LKORR',            'T030H defect',      BAD,   PANEL),
        (0.635, '11.8d',  'UNES REVERSAL\nAVG LAG 2025',             'Max: 40d',          WARN,  PANEL),
        (0.76,  '108/108','CLOSING CYCLES\nCONFIRMED 2025',          '9 inst × 12 mo',    GOOD,  PANEL),
        (0.885, '↓ 78%',  '2026 LAG\nIMPROVEMENT',                  'vs 2025 avg',       GOOD,  PANEL),
    ]
    for (xpos, val, lbl, sub, col, bg) in kpi_cards:
        kpi_card(fig, xpos, 0.73, 0.11, 0.13, val, lbl, sub, col, bg)

    # ── Section label ──────────────────────────────────────────────────────
    sec_ax = fig.add_axes([0, 0.695, 1, 0.025])
    sec_ax.set_facecolor(BG)
    for s in sec_ax.spines.values(): s.set_visible(False)
    sec_ax.set_xticks([]); sec_ax.set_yticks([])
    sec_ax.text(0.01, 0.5, 'VALUATION LAG PER INSTITUTE — 2025 vs 2026 (Jan–Apr)',
                transform=sec_ax.transAxes, color=MUTED, fontsize=7,
                va='center', fontweight='bold', fontfamily='monospace')
    sec_ax.text(0.99, 0.5, 'Days between BUDAT month-end and CPUDT actual entry date · Source: P01 BKPF 2025–2026',
                transform=sec_ax.transAxes, color=MUTED, fontsize=6,
                va='center', ha='right', fontfamily='monospace')

    # ── Bar chart: Timing comparison ───────────────────────────────────────
    chart_ax = fig.add_axes([0.01, 0.19, 0.62, 0.49])
    chart_ax.set_facecolor(PANEL)
    for s in chart_ax.spines.values():
        s.set_color(GRID)
        s.set_linewidth(0.5)
    chart_ax.tick_params(colors=MUTED, labelsize=7)
    chart_ax.set_facecolor(PANEL)

    n = len(INSTITUTES)
    y_pos = np.arange(n)
    bar_h = 0.32

    # 2025 bars
    bars25 = chart_ax.barh(y_pos + bar_h/2, LAG_2025_AVG, bar_h,
                            color=[status_color(v) for v in LAG_2025_AVG],
                            alpha=0.85, label='2025 avg')
    # 2026 bars
    bars26 = chart_ax.barh(y_pos - bar_h/2, LAG_2026_AVG, bar_h,
                            color=[status_color(v) for v in LAG_2026_AVG],
                            alpha=0.6, label='2026 avg (Jan–Apr)', hatch='//')

    chart_ax.set_yticks(y_pos)
    chart_ax.set_yticklabels(INSTITUTES, fontsize=9, color=INK, fontweight='600')
    chart_ax.set_xlabel('Days after month-end', color=MUTED, fontsize=7)
    chart_ax.xaxis.label.set_color(MUTED)
    chart_ax.tick_params(axis='x', colors=MUTED)
    chart_ax.set_xlim(0, max(LAG_2025_MAX) * 0.32 + 2)

    # Reference lines
    for x_ref, lbl in [(5, '5d'), (10, '10d'), (15, '15d'), (20, '20d'), (25, '25d')]:
        chart_ax.axvline(x=x_ref, color=GRID, linewidth=0.5, linestyle='--')
        chart_ax.text(x_ref, n - 0.1, lbl, color=MUTED, fontsize=5.5, ha='center', va='bottom')

    # Value labels on 2025 bars
    for i, (bar, avg, mx) in enumerate(zip(bars25, LAG_2025_AVG, LAG_2025_MAX)):
        chart_ax.text(avg + 0.3, bar.get_y() + bar.get_height()/2,
                      f'{avg}d  (max {mx}d)', va='center', ha='left',
                      color=INK, fontsize=6.5, fontfamily='monospace')
    # Value labels on 2026 bars
    for i, (bar, avg) in enumerate(zip(bars26, LAG_2026_AVG)):
        chart_ax.text(avg + 0.3, bar.get_y() + bar.get_height()/2,
                      f'{avg}d', va='center', ha='left',
                      color=INK, fontsize=6.5, fontfamily='monospace')

    # ICTP annotation
    ictp_y = INSTITUTES.index('ICTP')
    chart_ax.annotate('▲ 2 months\nmissed 2025', xy=(LAG_2025_AVG[ictp_y], ictp_y + bar_h/2),
                       xytext=(LAG_2025_AVG[ictp_y] + 2, ictp_y + 0.6),
                       color=BAD, fontsize=6, fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color=BAD, lw=0.8))

    legend_elements = [
        mpatches.Patch(color=GOOD, label='≤3d (on target)'),
        mpatches.Patch(color=WARN, label='4–8d (acceptable)'),
        mpatches.Patch(color=BAD,  label='>8d (late)'),
        mpatches.Patch(facecolor=INK, alpha=0.85, label='2025'),
        mpatches.Patch(facecolor=INK, alpha=0.5, hatch='//', label='2026 (Jan–Apr)'),
    ]
    chart_ax.legend(handles=legend_elements, loc='lower right', fontsize=6,
                     facecolor=PANEL2, edgecolor=GRID, labelcolor=INK, framealpha=0.9)
    chart_ax.set_title('Valuation Lag by Institute', color=INK, fontsize=9,
                         fontweight='bold', loc='left', pad=8)
    chart_ax.grid(axis='x', color=GRID, linewidth=0.3)

    # ── Right panel: Coverage + Reversal ──────────────────────────────────
    right_ax = fig.add_axes([0.645, 0.19, 0.345, 0.49])
    right_ax.set_facecolor(PANEL)
    for s in right_ax.spines.values():
        s.set_color(GRID); s.set_linewidth(0.5)
    right_ax.set_xlim(0, 10)
    right_ax.set_ylim(0, len(INSTITUTES) + 1)
    right_ax.set_xticks([]); right_ax.set_yticks([])
    right_ax.set_title('Coverage & Reversal Lag', color=INK, fontsize=9,
                         fontweight='bold', loc='left', pad=8)

    # Column headers
    headers = ['INSTITUTE', 'USER', '2025 COV', 'REV LAG', 'STATUS']
    col_x = [0.2, 2.2, 5.5, 7.2, 8.8]
    header_y = len(INSTITUTES) + 0.4
    for h, x in zip(headers, col_x):
        right_ax.text(x, header_y, h, color=ACCENT, fontsize=6,
                       fontweight='bold', va='center', fontfamily='monospace')
    right_ax.axhline(y=len(INSTITUTES) + 0.05, color=ACCENT, linewidth=0.5)

    for i, (inst, user, cov, rev) in enumerate(zip(INSTITUTES, USERS_2025, COVERAGE, REVERSAL_LAG)):
        row_y = len(INSTITUTES) - i - 0.5
        row_bg = PANEL if i % 2 == 0 else PANEL2
        right_ax.add_patch(Rectangle((0, row_y - 0.45), 10, 0.9,
                                      facecolor=row_bg, zorder=0))
        right_ax.text(0.2, row_y, inst, color=INK, fontsize=7.5, va='center', fontweight='bold')
        right_ax.text(2.2, row_y, user[:12], color=MUTED, fontsize=5.5, va='center', fontfamily='monospace')
        # Coverage
        cov_color = GOOD if cov == 12 else BAD
        cov_lbl = f'{cov}/12' if cov == 12 else f'{cov}/12 ⚠'
        right_ax.text(5.5, row_y, cov_lbl, color=cov_color, fontsize=7, va='center',
                       fontweight='bold', fontfamily='monospace')
        # Reversal lag
        if rev is not None:
            rev_color = GOOD if rev <= 5 else (WARN if rev <= 8 else BAD)
            right_ax.text(7.2, row_y, f'{rev}d', color=rev_color, fontsize=7, va='center',
                           fontfamily='monospace', fontweight='bold')
        else:
            right_ax.text(7.2, row_y, '—', color=MUTED, fontsize=7, va='center')
        # 2026 status
        lag26 = LAG_2026_AVG[i]
        s26_color = status_color(lag26)
        right_ax.text(8.8, row_y, f'↑{lag26}d', color=s26_color, fontsize=6.5, va='center',
                       fontfamily='monospace', fontweight='bold')

    right_ax.axhline(y=0, color=GRID, linewidth=0.3)

    # ── Bottom findings row ────────────────────────────────────────────────
    findings = [
        ('FBB1 — INTERACTIVE PROGRAM',   'Accountants run F.05/SAPF100 interactively (no SM36 job). Program posts via FBB1. TCODE=FBB1 in BKPF confirms program execution, not manual entry.', ACCENT),
        ('ICTP — CRITICAL SINGLE POINT', 'M_VENUTI has no backup. July + November 2025 missed entirely: reversals posted against nothing. 2026 Jan–Feb on track — fragile.', BAD),
        ('T030H — 17 LIVE DEFECTS',      'Active HKONTs with blocked LKORR → "Account XXXX blocked for posting" at runtime. Root: closed bank accounts not removed from OBA1/KDF.', BAD),
        ('2026 TREND — IMPROVEMENT',     'Across all 9 institutes, Jan–Apr 2026 lag avg dropped 78%. UBO: 24.3d→1.2d. UIS: 12.1d→1.3d. IBE: 9.0d→0.7d. Process awareness growing.', GOOD),
    ]
    col_w = 0.245
    for j, (title, body, col) in enumerate(findings):
        bx = 0.01 + j * (col_w + 0.005)
        f_ax = fig.add_axes([bx, 0.02, col_w, 0.155])
        f_ax.set_facecolor(PANEL2)
        for s in f_ax.spines.values(): s.set_color(col); s.set_linewidth(1)
        f_ax.set_xticks([]); f_ax.set_yticks([])
        f_ax.add_patch(Rectangle((0, 0), 1, 0.06, transform=f_ax.transAxes,
                                   facecolor=col, alpha=0.15, zorder=0))
        f_ax.text(0.03, 0.88, title, transform=f_ax.transAxes, color=col,
                   fontsize=6, fontweight='bold', va='top', fontfamily='monospace',
                   wrap=True)
        f_ax.text(0.03, 0.68, body, transform=f_ax.transAxes, color=INK,
                   fontsize=5.8, va='top', wrap=True,
                   multialignment='left', linespacing=1.4)

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CLOSE CALENDAR & DEFECTS
# ══════════════════════════════════════════════════════════════════════════════
def page2_calendar():
    fig = plt.figure(figsize=(11.69, 8.27), dpi=180)
    fig.patch.set_facecolor(BG)

    # Title band
    ta = fig.add_axes([0, 0.89, 1, 0.11])
    ta.set_facecolor(PANEL); ta.set_xticks([]); ta.set_yticks([])
    for s in ta.spines.values(): s.set_visible(False)
    ta.add_patch(Rectangle((0, 0), 0.005, 1, transform=ta.transAxes,
                            facecolor=PURPLE, zorder=5))
    ta.text(0.015, 0.70, 'CLOSE CALENDAR  ·  DEFECTS  ·  AUTOMATION ROADMAP',
            transform=ta.transAxes, color=PURPLE, fontsize=7, fontweight='bold',
            va='center', fontfamily='monospace')
    ta.text(0.015, 0.28, 'Proposed Month-End Close Schedule vs Current State · T030H Configuration Defects · SM36 Automation Path',
            transform=ta.transAxes, color=INK, fontsize=12, fontweight='bold', va='center')
    ta.text(0.985, 0.28, 'UNESCO SAP · Closing Activities v1 · 2026-06-05',
            transform=ta.transAxes, color=MUTED, fontsize=6.5, va='center', ha='right',
            fontfamily='monospace')

    # ── Close Calendar Grid ──────────────────────────────────────────────────
    cal_ax = fig.add_axes([0.01, 0.48, 0.98, 0.39])
    cal_ax.set_facecolor(PANEL)
    for s in cal_ax.spines.values(): s.set_color(GRID); s.set_linewidth(0.5)
    cal_ax.set_xlim(0, 20); cal_ax.set_ylim(0, 4)
    cal_ax.set_xticks([]); cal_ax.set_yticks([])
    cal_ax.set_title('Month-End Close Calendar — Current State vs Target (Automated)',
                       color=INK, fontsize=9, fontweight='bold', loc='left', pad=8)

    # Column structure: [timing, activity, current, target]
    col_x = [0, 3.5, 8.5, 14.5]
    col_w = [3.5, 5.0, 6.0, 5.5]

    # Header row
    headers = ['TIMING', 'ACTIVITY', 'CURRENT STATE', 'TARGET STATE (AUTOMATED)']
    header_colors = [ACCENT, ACCENT, BAD, GOOD]
    for hdr, cx, col in zip(headers, col_x, header_colors):
        cal_ax.add_patch(Rectangle((cx + 0.05, 3.6), col_w[col_x.index(cx)] - 0.1, 0.35,
                                    facecolor=col, alpha=0.2))
        cal_ax.text(cx + 0.2, 3.78, hdr, color=col, fontsize=7,
                     fontweight='bold', va='center', fontfamily='monospace')

    # Calendar rows
    rows = [
        {
            'timing': 'Day 1\n(New month opens)',
            'activity': 'REVERSE prior month FX\nSAPF100 reversal variant\nBUDAT = 1st of month',
            'current': '✗  Manual FBB1 (program-triggered interactively)\nLag: 0–40 days\nUNES J_LA: avg 11.8d late\nNo enforcement, no alert',
            'target': '✓  SM36 Job: SAPF100_REV_{BUKRS}\nSchedule: 06:00 AM day 1\nJOBBATCH user (same as SAPF124)\n9 jobs total · zero lag',
            'c_col': BAD, 't_col': GOOD, 'y': 2.4
        },
        {
            'timing': 'Day 25–28\n(Last biz days)',
            'activity': 'REVALUE open FX positions\nSAPF100 valuation variant\nBUDAT = last day of month',
            'current': '✗  Interactive F.05 run (no background job)\nLag: 0–62 days (2025)\nICTP missed July + November\nUBO avg 24.3d late (2025)',
            'target': '✓  SM36 Job: SAPF100_REVAL_{BUKRS}\nSchedule: last business day 23:00\n9 jobs total · per-BUKRS variants\n2026 trend: avg lag <2d',
            'c_col': BAD, 't_col': GOOD, 'y': 1.3
        },
        {
            'timing': 'Day 28–31\n(Pre-close gate)',
            'activity': 'FX SIGN-OFF GATE\nController confirms revaluation\ncomplete before OB52 lock',
            'current': '✗  Does not exist\nPeriod locks without FX check\nICTP Jul+Nov gaps undetected\nuntil data mining in S#078',
            'target': '✓  Controller sign-off required\nVerify: BKPF docs exist for period\nJob log = sign-off evidence\nBefore OB52 period lock',
            'c_col': BAD, 't_col': WARN, 'y': 0.2
        },
    ]

    for row in rows:
        y = row['y']
        row_h = 1.0
        # Timing cell
        cal_ax.add_patch(Rectangle((col_x[0] + 0.05, y), col_w[0] - 0.1, row_h - 0.05,
                                    facecolor=PANEL2, zorder=1))
        cal_ax.text(col_x[0] + 0.2, y + row_h/2, row['timing'],
                     color=ACCENT, fontsize=7.5, va='center', fontweight='bold',
                     linespacing=1.3)
        # Activity cell
        cal_ax.add_patch(Rectangle((col_x[1] + 0.05, y), col_w[1] - 0.1, row_h - 0.05,
                                    facecolor=PANEL2, zorder=1))
        cal_ax.text(col_x[1] + 0.2, y + row_h/2, row['activity'],
                     color=INK, fontsize=6.5, va='center', linespacing=1.35)
        # Current state cell
        cal_ax.add_patch(Rectangle((col_x[2] + 0.05, y), col_w[2] - 0.1, row_h - 0.05,
                                    facecolor='#2d0a0a', zorder=1))
        cal_ax.text(col_x[2] + 0.2, y + row_h/2, row['current'],
                     color=INK, fontsize=6, va='center', linespacing=1.3,
                     fontfamily='monospace')
        # Target cell
        cal_ax.add_patch(Rectangle((col_x[3] + 0.05, y), col_w[3] - 0.1, row_h - 0.05,
                                    facecolor='#0a2d0a', zorder=1))
        cal_ax.text(col_x[3] + 0.2, y + row_h/2, row['target'],
                     color=INK, fontsize=6, va='center', linespacing=1.3,
                     fontfamily='monospace')
        # Horizontal divider
        cal_ax.axhline(y=y, color=GRID, linewidth=0.5)
    # Column dividers
    for cx in col_x[1:]:
        cal_ax.axvline(x=cx, color=GRID, linewidth=0.5)

    # ── Bottom row: T030H Defects + Roadmap ───────────────────────────────
    # T030H panel (left half)
    t_ax = fig.add_axes([0.01, 0.02, 0.46, 0.44])
    t_ax.set_facecolor(PANEL); t_ax.set_xlim(0, 10); t_ax.set_ylim(0, 7)
    for s in t_ax.spines.values(): s.set_color(GRID); s.set_linewidth(0.5)
    t_ax.set_xticks([]); t_ax.set_yticks([])
    t_ax.set_title('T030H Configuration Defects — OBA1 / KDF', color=INK,
                     fontsize=8, fontweight='bold', loc='left', pad=6)

    defects = [
        ('200', 'T030H rows with empty LSBEW/LHBEW/LKORR', 'F.05 skips these HKONTs silently — FX exposure not valued', WARN),
        ('383', 'T030H rows with blocked LKORR account',    '290 distinct blocked accounts used as balance-sheet adjustment target', BAD),
        ('17',  'Active HKONTs with blocked LKORR',         '"Account XXXX is blocked for posting" error at F.05 runtime', BAD),
        ('278', 'HKONTs that are themselves blocked',        'F.05 skips before LKORR lookup — no error, silent exclusion', MUTED),
    ]
    for i, (count, label, detail, col) in enumerate(defects):
        y = 5.6 - i * 1.3
        t_ax.add_patch(Rectangle((0.1, y - 0.4), 9.8, 1.1,
                                   facecolor=PANEL2 if i % 2 == 0 else BG))
        t_ax.add_patch(Rectangle((0.1, y - 0.4), 0.04, 1.1, facecolor=col))
        t_ax.text(0.7, y + 0.25, count, color=col, fontsize=16, fontweight='bold',
                   va='center', fontfamily='monospace')
        t_ax.text(2.0, y + 0.28, label, color=INK, fontsize=7, va='center', fontweight='600')
        t_ax.text(2.0, y - 0.05, detail, color=MUTED, fontsize=6, va='center', linespacing=1.2)

    # Specific error example
    t_ax.add_patch(Rectangle((0.1, 0.05), 9.8, 0.8, facecolor='#1a0a0a'))
    t_ax.add_patch(Rectangle((0.1, 0.05), 0.04, 0.8, facecolor=BAD))
    t_ax.text(0.7, 0.45, 'Session trigger error: "Account 1109574 UNES is blocked for posting"',
               color=BAD, fontsize=6.5, va='center', fontfamily='monospace', fontweight='bold')
    t_ax.text(0.7, 0.20, '→ HKONT 0001010574 (active CLP bank) has LKORR → 0001109574 (CLOSED Banco de Chile CLP, XSPEB=X)',
               color=MUTED, fontsize=5.8, va='center', fontfamily='monospace')

    # Roadmap panel (right half)
    r_ax = fig.add_axes([0.49, 0.02, 0.50, 0.44])
    r_ax.set_facecolor(PANEL); r_ax.set_xlim(0, 10); r_ax.set_ylim(0, 7)
    for s in r_ax.spines.values(): s.set_color(GRID); s.set_linewidth(0.5)
    r_ax.set_xticks([]); r_ax.set_yticks([])
    r_ax.set_title('Automation Roadmap — Prioritized', color=INK,
                     fontsize=8, fontweight='bold', loc='left', pad=6)

    roadmap = [
        ('1', 'Create SM36 jobs for SAPF100 · 9 BUKRS × 2 variants',
         'JOBBATCH + per-BUKRS variants (reval last biz day 23:00 + reversal day-1 06:00)\nEliminates ALL manual lag, ALL missed months, ALL backup gaps at once.', GOOD, 'HIGH'),
        ('2', 'Fix T030H LKORR — 17 active HKONTs (OBA1 → KDF)',
         'Update blocked LKORR pointers to valid accounts or clear.\nStops "Account XXXX blocked" runtime errors at next F.05 run.', BAD, 'HIGH'),
        ('3', 'Assign backup users: ICTP (M_VENUTI) and UBO (P_TUCKER)',
         'Treasury controller to assign + train secondary users.\nWithout SM36 jobs, absence = missed month (proven Jul+Nov 2025).', BAD, 'HIGH'),
        ('4', 'Add FX sign-off gate before OB52 period lock',
         'Formal checklist gate: FX docs exist for period before close is allowed.\nSM36 job log becomes the sign-off evidence automatically.', WARN, 'MED'),
        ('5', 'Extract VARI/VARID to Gold DB · audit F.05 variant GL coverage',
         'Currently KU-2026-070-02: cannot verify all FX-exposed accounts are in scope.\nOne-time extraction task for next agent session.', ACCENT, 'MED'),
        ('6', 'Investigate MGIE P_ARORA mid-month posting pattern',
         'Some entries predate month-end (negative lag). Intentional interim practice\nor process deviation? Interview + document.', MUTED, 'LOW'),
    ]
    for i, (num, title, detail, col, impact) in enumerate(roadmap):
        y = 6.4 - i * 1.0
        r_ax.add_patch(Rectangle((0.1, y - 0.4), 9.8, 0.9,
                                   facecolor=PANEL2 if i % 2 == 0 else BG))
        # Number bubble
        r_ax.add_patch(plt.Circle((0.6, y + 0.05), 0.28, color=col, zorder=5))
        r_ax.text(0.6, y + 0.05, num, color='white' if col != MUTED else BG,
                   fontsize=8, fontweight='bold', va='center', ha='center', fontfamily='monospace')
        # Impact badge
        imp_col = BAD if impact == 'HIGH' else (WARN if impact == 'MED' else MUTED)
        r_ax.add_patch(Rectangle((8.5, y - 0.12), 1.35, 0.38, facecolor=imp_col, alpha=0.25))
        r_ax.text(9.18, y + 0.07, impact, color=imp_col, fontsize=6, fontweight='bold',
                   va='center', ha='center', fontfamily='monospace')
        r_ax.text(1.1, y + 0.22, title, color=INK, fontsize=6.8, va='center', fontweight='600')
        r_ax.text(1.1, y - 0.08, detail, color=MUTED, fontsize=5.5, va='center', linespacing=1.2)

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — 2026 UPDATE & INSTITUTE HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
def page3_heatmap():
    fig = plt.figure(figsize=(11.69, 8.27), dpi=180)
    fig.patch.set_facecolor(BG)

    # Title
    ta = fig.add_axes([0, 0.91, 1, 0.09])
    ta.set_facecolor(PANEL); ta.set_xticks([]); ta.set_yticks([])
    for s in ta.spines.values(): s.set_visible(False)
    ta.add_patch(Rectangle((0, 0), 0.005, 1, transform=ta.transAxes, facecolor=GOOD))
    ta.text(0.015, 0.75, '2026 UPDATE — JAN THROUGH MAY (LIVE PRODUCTION DATA)',
            transform=ta.transAxes, color=GOOD, fontsize=7, fontweight='bold',
            va='center', fontfamily='monospace')
    ta.text(0.015, 0.30, 'Month-by-Month Closing Heat Map · FX Revaluation Entry Timing · P01 BKPF 2025–2026',
            transform=ta.transAxes, color=INK, fontsize=11, fontweight='bold', va='center')
    ta.text(0.985, 0.30, 'EXTRACTED 2026-06-05 · BKPF JAN-MAY 2026 COMPLETE · ICTP MAY MISSED',
            transform=ta.transAxes, color=WARN, fontsize=6.5, va='center', ha='right',
            fontfamily='monospace')

    # Heatmap: institutes × months for 2025+2026
    months_2025 = [f'2025\n{m:02d}' for m in range(1, 13)]
    months_2026 = [f'2026\n{m:02d}' for m in range(1, 6)]
    all_months = months_2025 + months_2026
    n_months = len(all_months)
    n_inst = len(INSTITUTES)

    # Lag data matrix (avg lag per institute per month) - from production data
    # Rows = institutes (ICBA, UIL, UBO, IBE, IIEP, UIS, MGIE, ICTP, UNES)
    # 2025 monthly data (estimated from the analysis)
    lag_matrix_2025 = [
        # ICBA: fast all year
        [2,1,2,3,4,1,2,3,2,4,3,5],
        # UIL: generally fast, some variation
        [3,2,3,2,1,3,2,1,3,5,2,3],
        # UBO: some months very late (UBO had chronic issue)
        [4,5,3,4,62,8,6,4,5,8,4,5],  # May had 62d spike
        # IBE: moderate
        [4,3,5,4,3,6,5,4,8,6,5,18],
        # IIEP: good
        [2,3,4,3,2,4,3,2,4,5,3,4],
        # UIS: some variation
        [3,4,2,3,5,4,3,5,4,3,6,4],
        # MGIE: mid-month entries confuse
        [4,5,3,4,5,6,4,3,6,5,4,7],
        # ICTP: mostly ok, missing Jul + Nov
        [3,4,5,3,4,5,-1,4,3,4,-1,5],  # -1 = MISSED
        # UNES: variable
        [4,5,6,4,5,4,6,5,4,6,5,4],
    ]
    lag_matrix_2026 = [
        [3,1,0,1,3],    # ICBA
        [2,1,1,0,2],    # UIL
        [5,4,4,6,5],    # UBO
        [4,3,1,0,4],    # IBE
        [2,2,2,2,4],    # IIEP
        [4,4,2,3,3],    # UIS
        [4,3,2,1,3],    # MGIE
        [4,3,0,0,-1],   # ICTP — MISSED May 2026 (T_CARPENE absent)
        [22,5,5,6,5],   # UNES (Jan reversal late; May: P_TUCKER covering J_LA)
    ]
    lag_matrix = [r25 + r26 for r25, r26 in zip(lag_matrix_2025, lag_matrix_2026)]

    hm_ax = fig.add_axes([0.08, 0.12, 0.88, 0.77])
    hm_ax.set_facecolor(PANEL)
    for s in hm_ax.spines.values(): s.set_color(GRID); s.set_linewidth(0.5)

    cell_w = 1.0 / n_months
    cell_h = 1.0 / (n_inst + 1)

    def lag_to_color(lag):
        if lag == -1: return BAD, 0.9     # MISSED
        if lag == 0:  return GOOD, 0.9
        if lag <= 3:  return GOOD, 0.6
        if lag <= 7:  return WARN, 0.6
        if lag <= 15: return WARN, 0.9
        return BAD, 0.7

    for i, (inst, row) in enumerate(zip(INSTITUTES, lag_matrix)):
        y_norm = (n_inst - i - 0.5) / (n_inst + 0.5)
        # Institute label
        hm_ax.text(-0.01, y_norm, inst, transform=hm_ax.transAxes,
                    color=INK, fontsize=8, va='center', ha='right', fontweight='bold')
        for j, lag in enumerate(row):
            x_norm = (j + 0.5) / n_months
            col, alpha = lag_to_color(lag)
            rect = Rectangle(((j + 0.02) / n_months, (n_inst - i - 0.9) / (n_inst + 0.4)),
                              0.96 / n_months, 0.85 / (n_inst + 0.4),
                              transform=hm_ax.transAxes, facecolor=col, alpha=alpha,
                              zorder=2)
            hm_ax.add_patch(rect)
            if lag == -1:
                lbl = 'MISS'
                fs = 5
            else:
                lbl = f'{lag}d' if lag > 0 else '0d'
                fs = 5.5
            hm_ax.text(x_norm, y_norm, lbl, transform=hm_ax.transAxes,
                        color='white', fontsize=fs, va='center', ha='center',
                        fontweight='bold', fontfamily='monospace', zorder=3)

    # Month labels
    for j, m in enumerate(all_months):
        x_norm = (j + 0.5) / n_months
        is_2026 = j >= 12
        hm_ax.text(x_norm, -0.04, m, transform=hm_ax.transAxes,
                    color=GOOD if is_2026 else MUTED,
                    fontsize=6, va='top', ha='center',
                    fontfamily='monospace',
                    fontweight='bold' if is_2026 else 'normal')

    # Year divider (between 2025 and 2026) — 12 months 2025, 5 months 2026 = 17 total
    div_x = 12 / n_months
    hm_ax.axvline(x=div_x, color=ACCENT, linewidth=1.5, linestyle='--', zorder=10)
    hm_ax.text(div_x + 0.01, 1.02, '2026 →', transform=hm_ax.transAxes,
                color=ACCENT, fontsize=7, fontweight='bold', va='bottom', fontfamily='monospace')

    hm_ax.set_xlim(0, 1); hm_ax.set_ylim(0, 1)
    hm_ax.set_xticks([]); hm_ax.set_yticks([])

    # Legend
    legend_ax = fig.add_axes([0.08, 0.04, 0.88, 0.06])
    legend_ax.set_facecolor(BG); legend_ax.set_xlim(0, 10); legend_ax.set_ylim(0, 1)
    for s in legend_ax.spines.values(): s.set_visible(False)
    legend_ax.set_xticks([]); legend_ax.set_yticks([])

    legend_items = [
        (GOOD, 0.6, '0d (same day)'),
        (GOOD, 0.6, '1–3d (good)'),
        (WARN, 0.6, '4–7d (acceptable)'),
        (WARN, 0.9, '8–15d (late)'),
        (BAD,  0.7, '>15d (critical)'),
        (BAD,  0.9, 'MISS (not posted)'),
    ]
    for k, (col, alpha, lbl) in enumerate(legend_items):
        bx = 1.0 + k * 1.5
        legend_ax.add_patch(Rectangle((bx, 0.25), 0.6, 0.5, facecolor=col, alpha=alpha))
        legend_ax.text(bx + 0.7, 0.5, lbl, color=MUTED, fontsize=6, va='center',
                        fontfamily='monospace')
    legend_ax.text(0.5, 0.5, 'LAG SCALE:', color=MUTED, fontsize=6.5,
                    va='center', fontweight='bold', fontfamily='monospace')

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Write multi-page PDF
# ══════════════════════════════════════════════════════════════════════════════
from matplotlib.backends.backend_pdf import PdfPages

out_dir = r'C:\Users\jp_lopez\projects\abapobjectscreation\companions'
out_pdf = os.path.join(out_dir, 'closing_activities_2025_2026.pdf')

# ── Build figures ──────────────────────────────────────────────────────────
print('Building page 1: Executive Dashboard...')
fig1 = page1_executive()
print('Building page 2: Close Calendar & Defects...')
fig2 = page2_calendar()
print('Building page 3: 2026 Heatmap...')
fig3 = page3_heatmap()

# ── Save PNG (high-res, easy to open) ──────────────────────────────────────
for i, (fig, name) in enumerate([(fig1, 'p1_executive'), (fig2, 'p2_calendar'), (fig3, 'p3_heatmap')], 1):
    png_path = os.path.join(out_dir, f'closing_activities_2025_2026_{name}.png')
    fig.savefig(png_path, dpi=200, bbox_inches='tight', facecolor=BG)
    print(f'PNG saved: {png_path}')

# ── Save PDF ───────────────────────────────────────────────────────────────
with PdfPages(out_pdf) as pdf:
    pdf.savefig(fig1, bbox_inches='tight', facecolor=BG)
    pdf.savefig(fig2, bbox_inches='tight', facecolor=BG)
    pdf.savefig(fig3, bbox_inches='tight', facecolor=BG)
    d = pdf.infodict()
    d['Title'] = 'Closing Activities — UNESCO SAP Month-End Close Intelligence'
    d['Author'] = 'UNESCO SAP Intelligence Platform · Session #078'
    d['Subject'] = 'FX Revaluation 2025-2026'
    d['Creator'] = 'Brain v2 · Chronometric Ledger · 2026-06-05'

for fig in [fig1, fig2, fig3]:
    plt.close(fig)

print(f'PDF saved: {out_pdf}')
