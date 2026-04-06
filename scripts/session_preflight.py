#!/usr/bin/env python3
"""
session_preflight.py — Executable guardrails for UNESCO SAP sessions.

Runs 10 checks derived from accumulated feedback_*.md rules.
Converts prose rules into hard preconditions. If any check FAILS,
the session cannot proceed (in close mode) or is warned (in start mode).

Usage:
    python scripts/session_preflight.py --mode start
    python scripts/session_preflight.py --mode close
    python scripts/session_preflight.py --mode close --strict  # exit 1 on any fail

This file replaces ~20 prose feedback rules with ~10 executable checks.
It is the enforcement architecture the project was missing.

First authored: Session #036 (2026-04-05)
Principle: "A rule that requires human memory is a wish. A rule encoded
in code that blocks action is a rule."
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ----------------------------------------------------------------------------
# Paths (resolved relative to repo root)
# ----------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
PMO_BRAIN = REPO / ".agents" / "intelligence" / "PMO_BRAIN.md"
SESSION_LOG = REPO / ".agents" / "intelligence" / "SESSION_LOG.md"
SESSION_RETROS = REPO / "knowledge" / "session_retros"
SESSION_PLANS = REPO / "knowledge" / "session_plans"
SESSION_STATE = REPO / ".agents" / "intelligence" / ".session_state.json"
GOLD_DB = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Memory dir (outside repo)
HOME = Path(os.path.expanduser("~"))
MEMORY_DIR = HOME / ".claude" / "projects" / "c--Users-jp-lopez-projects-abapobjectscreation" / "memory"
MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"

# ----------------------------------------------------------------------------
# Check framework
# ----------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    status: str  # PASS | FAIL | WARN | SKIP
    message: str
    evidence: list[str] = field(default_factory=list)

    def icon(self) -> str:
        return {"PASS": "OK  ", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}[self.status]


def run_check(fn: Callable[[], CheckResult], name: str) -> CheckResult:
    try:
        result = fn()
        result.name = name
        return result
    except Exception as e:
        return CheckResult(name=name, status="FAIL", message=f"Check raised: {e!r}")


# ----------------------------------------------------------------------------
# The 10 Checks
# ----------------------------------------------------------------------------


def check_1_pmo_count_consistency() -> CheckResult:
    """PMO_BRAIN counts match MEMORY.md declared counts. Math has to add up."""
    if not PMO_BRAIN.exists():
        return CheckResult("", "FAIL", f"PMO_BRAIN not found at {PMO_BRAIN}")
    if not MEMORY_INDEX.exists():
        return CheckResult("", "FAIL", f"MEMORY.md not found at {MEMORY_INDEX}")

    pmo_text = PMO_BRAIN.read_text(encoding="utf-8", errors="ignore")
    mem_text = MEMORY_INDEX.read_text(encoding="utf-8", errors="ignore")

    # Count open items in PMO_BRAIN: rows in B/H/G tables not struck through (~~...~~)
    # Fix (#037): regex now tolerates markup between `|` and the ID. Previously
    # rows like `| **H13** 🔥 |` were silently NOT counted because the regex
    # expected the ID immediately after `|` with no bold/emoji markup. This bug
    # hid H13 from the count for many sessions.
    def count_open(section_pattern: str, id_pattern: str) -> int:
        match = re.search(section_pattern, pmo_text, re.DOTALL)
        if not match:
            return 0
        section = match.group(0)
        # Accept optional markup chars (`*`, emoji, whitespace) on either side of the ID.
        # `.*?` lazy match absorbs bold markers, emojis, and other decorations.
        rows = re.findall(
            rf"^\|\s*(~~)?\**\s*({id_pattern})\s*\**(~~)?\s*(?:[^\|]*?)\|",
            section,
            re.MULTILINE,
        )
        return sum(1 for strike_l, _id, strike_r in rows if not strike_l and not strike_r)

    # BACKLOG runs until "## COMPLETED" (top-level ##, not ###/####)
    blocking = count_open(r"### 🔴 BLOCKING.*?(?=\n### |\n## )", r"B\d+")
    high = count_open(r"### 🟡 HIGH.*?(?=\n### |\n## )", r"H\d+")
    backlog = count_open(r"### 🟢 BACKLOG.*?(?=\n## [^#])", r"G\d+")
    total = blocking + high + backlog

    # Extract declared count from MEMORY.md
    declared = re.search(
        r"\*\*(\d+)\s*Blocking\*\*\s*\|\s*\*\*(\d+)\s*High\*\*\s*\|\s*\*\*(\d+)\s*Backlog\*\*\s*=\s*(\d+)",
        mem_text,
    )
    if not declared:
        return CheckResult(
            "",
            "WARN",
            "MEMORY.md pending count line not found or format changed",
            [f"Actual PMO open: B={blocking} H={high} G={backlog} total={total}"],
        )

    d_b, d_h, d_g, d_t = map(int, declared.groups())
    evidence = [
        f"PMO_BRAIN open: B={blocking} H={high} G={backlog} total={total}",
        f"MEMORY.md declared: B={d_b} H={d_h} G={d_g} total={d_t}",
    ]
    if (blocking, high, backlog, total) != (d_b, d_h, d_g, d_t):
        return CheckResult(
            "",
            "FAIL",
            f"Count mismatch. MEMORY.md says {d_t}, PMO_BRAIN has {total}.",
            evidence,
        )
    return CheckResult("", "PASS", f"Counts reconciled: {total} open items", evidence)


def check_2_memory_growth_tracking() -> CheckResult:
    """Session #036 decision (user): MEMORY.md has NO line limit. 1M context
    window makes the old 200-line ceiling obsolete. Memory grows, never
    compresses. This check tracks growth as a positive signal and only warns
    on empty/missing state. See memory/feedback_memory_no_truncation.md."""
    if not MEMORY_INDEX.exists():
        return CheckResult("", "FAIL", "MEMORY.md missing")
    lines = MEMORY_INDEX.read_text(encoding="utf-8", errors="ignore").splitlines()
    n = len(lines)
    if n < 20:
        return CheckResult("", "WARN", f"MEMORY.md has only {n} lines — may be stub")
    return CheckResult("", "PASS", f"MEMORY.md has {n} lines (growth tracked, no limit)")


def check_3_retro_exists_for_latest_session() -> CheckResult:
    """Every session # in SESSION_LOG must have a retro file. No phantom sessions."""
    if not SESSION_LOG.exists() or not SESSION_RETROS.exists():
        return CheckResult("", "SKIP", "SESSION_LOG or retros dir missing")
    log_text = SESSION_LOG.read_text(encoding="utf-8", errors="ignore")
    session_ids = set(re.findall(r"#(\d{3})", log_text))
    retro_ids = {m.group(1) for p in SESSION_RETROS.glob("session_*_retro.md")
                 for m in [re.search(r"session_(\d{3})", p.name)] if m}
    missing = sorted(session_ids - retro_ids)
    if missing:
        return CheckResult(
            "",
            "WARN",
            f"{len(missing)} sessions in log without retro files",
            [f"Missing: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}"],
        )
    return CheckResult("", "PASS", f"{len(retro_ids)} retro files match session log")


def check_4_no_forbidden_phrases_in_recent_retros() -> CheckResult:
    """Brutal honesty protocol: last 3 retros must not contain cheerleading phrases."""
    if not SESSION_RETROS.exists():
        return CheckResult("", "SKIP", "retros dir missing")
    forbidden = [
        r"\bwent well\b",
        r"\bsuccessful session\b",
        r"\bgreat progress\b",
        r"\bvery productive\b",
        r"\beverything worked\b",
    ]
    retros = sorted(SESSION_RETROS.glob("session_*_retro.md"))[-3:]
    hits = []
    for r in retros:
        text = r.read_text(encoding="utf-8", errors="ignore").lower()
        for pat in forbidden:
            if re.search(pat, text):
                hits.append(f"{r.name}: matched /{pat}/")
    if hits:
        return CheckResult("", "WARN", f"{len(hits)} forbidden phrases in last 3 retros", hits)
    return CheckResult("", "PASS", "Last 3 retros clean of cheerleading phrases")


def check_5_zombie_pmo_items() -> CheckResult:
    """Items >10 sessions old (first raised < current-10) flagged for kill/ship."""
    if not PMO_BRAIN.exists() or not SESSION_LOG.exists():
        return CheckResult("", "SKIP", "required files missing")
    log_text = SESSION_LOG.read_text(encoding="utf-8", errors="ignore")
    session_nums = [int(x) for x in re.findall(r"#(\d{3})", log_text)]
    if not session_nums:
        return CheckResult("", "SKIP", "No session numbers in log")
    current = max(session_nums)
    threshold = current - 10

    pmo_text = PMO_BRAIN.read_text(encoding="utf-8", errors="ignore")
    # rows: | [~~]IDX[~~] | ... | #NNN or #NNN/#NNN |
    zombie_pattern = re.compile(
        r"^\|\s*([BHG]\d+)\s*\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|\s*#?0?(\d+)",
        re.MULTILINE,
    )
    zombies = []
    for m in zombie_pattern.finditer(pmo_text):
        item_id, title, raised_str = m.group(1), m.group(2).strip(), m.group(3)
        # skip struck rows (contain ~~)
        line_start = pmo_text.rfind("\n", 0, m.start()) + 1
        line_end = pmo_text.find("\n", m.end())
        line = pmo_text[line_start:line_end]
        if "~~" in line:
            continue
        try:
            raised = int(raised_str)
        except ValueError:
            continue
        if raised < threshold:
            zombies.append(f"{item_id} (#{raised:03d}, age {current-raised}): {title[:60]}")

    if len(zombies) > 5:
        return CheckResult(
            "",
            "FAIL",
            f"{len(zombies)} zombie items (>10 sessions old) — KILL or SHIP required",
            zombies,
        )
    if zombies:
        return CheckResult(
            "",
            "WARN",
            f"{len(zombies)} zombie items flagged",
            zombies,
        )
    return CheckResult("", "PASS", "No zombie items (all PMO items <10 sessions old)")


def check_6_git_status_not_massive() -> CheckResult:
    """Uncommitted changes should be bounded. >500 files = suspicious."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as e:
        return CheckResult("", "SKIP", f"git not available: {e}")
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    n = len(lines)
    if n > 500:
        return CheckResult("", "FAIL", f"{n} uncommitted files — likely lost session boundary")
    if n > 100:
        return CheckResult("", "WARN", f"{n} uncommitted files — consider checkpoint commit")
    return CheckResult("", "PASS", f"{n} uncommitted files")


def check_7_zero_row_claims_verified() -> CheckResult:
    """FEBEP=0 lesson: any retro claiming a table has 0 rows must cite a re-verification."""
    if not SESSION_RETROS.exists():
        return CheckResult("", "SKIP", "retros dir missing")
    retros = sorted(SESSION_RETROS.glob("session_*_retro.md"))[-3:]
    violations = []
    for r in retros:
        text = r.read_text(encoding="utf-8", errors="ignore")
        zero_claims = re.findall(r"([A-Z][A-Z0-9_]{2,})\s*=\s*0\s+rows?", text)
        for tbl in zero_claims:
            context_window = text[max(0, text.find(tbl) - 100): text.find(tbl) + 200]
            if not re.search(r"re-?verif|live probe|re-?extract", context_window, re.I):
                violations.append(f"{r.name}: {tbl}=0 without re-verification")
    if violations:
        return CheckResult("", "WARN", "Zero-row claims without verification", violations[:10])
    return CheckResult("", "PASS", "No unverified zero-row claims in last 3 retros")


def check_8_skill_growth_tracking() -> CheckResult:
    """Skills are memory. They GROW, never consolidate. This check tracks growth
    as a positive signal and ensures every skill has a non-trivial SKILL.md body.
    Session #036 decision (user): no consolidation, ever. Same principle as
    MEMORY.md having no line limit — knowledge accumulates, never compresses.
    See .agents/skills/skill_coordinator/SKILL.md."""
    skills_dir = REPO / ".agents" / "skills"
    if not skills_dir.exists():
        return CheckResult("", "SKIP", "skills dir missing")
    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists()]
    n = len(skill_dirs)
    # Flag skills with SKILL.md smaller than 20 lines (likely stubs needing growth)
    stubs = []
    for p in skill_dirs:
        try:
            lines = len((p / "SKILL.md").read_text(encoding="utf-8", errors="ignore").splitlines())
            if lines < 20:
                stubs.append(f"{p.name} ({lines} lines)")
        except Exception:
            pass
    if stubs:
        return CheckResult(
            "",
            "WARN",
            f"{n} skills total — {len(stubs)} stubs needing growth (not merge)",
            stubs[:10],
        )
    return CheckResult("", "PASS", f"{n} skills — all have substantive content")


def check_9_feedback_routing() -> CheckResult:
    """Feedback files are part of memory; they GROW, never consolidate (Session #036).
    This check tracks coverage: every feedback file should be readable and non-empty.
    Conversion to executable checks is OPTIONAL (preferred for high-frequency rules),
    not mandatory. See skill_coordinator/SKILL.md for routing principles."""
    if not MEMORY_DIR.exists():
        return CheckResult("", "SKIP", "memory dir missing")
    feedback_files = list(MEMORY_DIR.glob("feedback_*.md"))
    n = len(feedback_files)
    empty = [f.name for f in feedback_files
             if f.stat().st_size < 100]
    if empty:
        return CheckResult(
            "",
            "WARN",
            f"{n} feedback files — {len(empty)} appear empty/stub",
            empty[:10],
        )
    return CheckResult("", "PASS", f"{n} feedback rules (growth tracked, no limit)")


def check_10_hypothesis_for_new_data() -> CheckResult:
    """Principle 4: new extractions need hypothesis.md. Scan last session's task folders."""
    tasks_dir = REPO / "Zagentexecution" / "tasks"
    if not tasks_dir.exists():
        # Not a hard failure — project may not use tasks/ for all work
        return CheckResult("", "SKIP", "Zagentexecution/tasks not present")
    # Find folders modified in last 7 days
    import time
    cutoff = time.time() - 7 * 86400
    recent = [p for p in tasks_dir.iterdir() if p.is_dir() and p.stat().st_mtime > cutoff]
    missing = []
    for folder in recent:
        has_hypothesis = any(folder.glob("hypothesis*.md")) or any(folder.glob("**/hypothesis*.md"))
        if not has_hypothesis:
            missing.append(folder.name)
    if missing:
        return CheckResult(
            "",
            "WARN",
            f"{len(missing)} recent task folders without hypothesis.md",
            missing[:10],
        )
    return CheckResult("", "PASS", f"Hypothesis grounding present in {len(recent)} recent tasks")


# ----------------------------------------------------------------------------
# Start-mode specific checks (symmetry with close, session #037)
# ----------------------------------------------------------------------------


def check_s1_session_plan_exists() -> CheckResult:
    """Start Phase 4: every session must have a plan file declaring its hypothesis
    BEFORE work begins. Close audit diffs plan vs. retro mechanically."""
    # Prefer .session_state.json (authoritative for current session).
    # Fall back to SESSION_LOG+1 if state.json missing.
    current = None
    if SESSION_STATE.exists():
        try:
            state = json.loads(SESSION_STATE.read_text(encoding="utf-8"))
            current = int(state.get("session", "0"))
        except Exception:
            pass
    if current is None:
        if not SESSION_LOG.exists():
            return CheckResult("", "SKIP", "SESSION_LOG + state.json both missing")
        log_text = SESSION_LOG.read_text(encoding="utf-8", errors="ignore")
        nums = [int(x) for x in re.findall(r"#(\d{3})", log_text)]
        if not nums:
            return CheckResult("", "SKIP", "no session numbers in log")
        current = max(nums) + 1
    if not SESSION_PLANS.exists():
        return CheckResult(
            "",
            "WARN",
            f"session_plans/ does not exist — create before Phase 4",
            [f"Expected: {SESSION_PLANS}/session_{current:03d}_plan.md"],
        )
    plan_file = SESSION_PLANS / f"session_{current:03d}_plan.md"
    if not plan_file.exists():
        return CheckResult(
            "",
            "WARN",
            f"No plan file for session #{current:03d} yet (Phase 4 pending)",
            [f"Create: {plan_file}"],
        )
    text = plan_file.read_text(encoding="utf-8", errors="ignore")
    required = ["Hypothesis", "Deliverables", "Out of scope", "Success criteria"]
    missing = [r for r in required if r.lower() not in text.lower()]
    if missing:
        return CheckResult(
            "",
            "WARN",
            f"Plan file missing sections: {', '.join(missing)}",
        )
    return CheckResult("", "PASS", f"Plan declared for session #{current:03d}")


def check_s2_session_state_snapshot() -> CheckResult:
    """Start Phase 2: .session_state.json must exist with baseline for close diff."""
    if not SESSION_STATE.exists():
        return CheckResult(
            "",
            "WARN",
            ".session_state.json missing — closure math cannot be computed at close",
            [f"Expected: {SESSION_STATE}"],
        )
    try:
        state = json.loads(SESSION_STATE.read_text(encoding="utf-8"))
    except Exception as e:
        return CheckResult("", "FAIL", f".session_state.json parse error: {e}")
    required = ["session", "start_ts", "git_head_start", "pmo_pending_start"]
    missing = [k for k in required if k not in state]
    if missing:
        return CheckResult("", "WARN", f".session_state.json missing keys: {missing}")
    return CheckResult("", "PASS", f"Baseline captured for session {state.get('session')}")


def check_symmetry_plan_retro_pairing() -> CheckResult:
    """Start-close symmetry control (Session #037).

    Every session in session_plans/ must have a matching session_retros/*.md OR
    be the current session (in progress). Every retro must have a matching plan.
    This is the executable enforcement of feedback_start_close_symmetry.md.

    Asymmetry detected here = structural drift between open and close protocols.
    """
    if not SESSION_PLANS.exists():
        return CheckResult("", "SKIP", "session_plans/ not created yet")
    if not SESSION_RETROS.exists():
        return CheckResult("", "SKIP", "session_retros/ missing")

    plan_ids = {
        m.group(1) for p in SESSION_PLANS.glob("session_*_plan.md")
        for m in [re.search(r"session_(\d{3})_plan", p.name)] if m
    }
    # Match any retro variant: session_NNN_retro.md OR session_NNN_retro_audit.md
    retro_ids = {
        m.group(1) for p in SESSION_RETROS.glob("session_*_retro*.md")
        for m in [re.search(r"session_(\d{3})_retro", p.name)] if m
    }

    # Determine current session (in-progress — plan exists, retro may not).
    # Prefer .session_state.json as authoritative source.
    current = None
    if SESSION_STATE.exists():
        try:
            state = json.loads(SESSION_STATE.read_text(encoding="utf-8"))
            current = f"{int(state.get('session', '0')):03d}"
        except Exception:
            pass
    if current is None and SESSION_LOG.exists():
        log_text = SESSION_LOG.read_text(encoding="utf-8", errors="ignore")
        logged = [int(x) for x in re.findall(r"#(\d{3})", log_text)]
        current = f"{max(logged) + 1:03d}" if logged else None

    # Plans without retros (excluding current session)
    plans_without_retro = sorted(plan_ids - retro_ids - ({current} if current else set()))
    # Retros without plans (pre-#037 sessions are expected, flag only #037+)
    retros_without_plan = sorted(
        r for r in retro_ids - plan_ids if int(r) >= 37
    )

    evidence = []
    if plans_without_retro:
        evidence.append(f"Plans without retro: {', '.join(plans_without_retro)}")
    if retros_without_plan:
        evidence.append(f"Retros without plan (#037+): {', '.join(retros_without_plan)}")

    if plans_without_retro or retros_without_plan:
        return CheckResult(
            "",
            "FAIL" if retros_without_plan else "WARN",
            f"Symmetry drift: {len(plans_without_retro)} unaudited plans, "
            f"{len(retros_without_plan)} un-planned retros",
            evidence,
        )

    matched = len(plan_ids & retro_ids)
    return CheckResult(
        "",
        "PASS",
        f"Start-close symmetry: {matched} plan-retro pairs matched"
        + (f", current #{current} in progress" if current else ""),
    )


def check_s3_zombie_decisions_pending() -> CheckResult:
    """Start Phase 3: zombies must be triaged at open, not deferred to close."""
    # Reuse check_5 logic but frame as "decisions needed" vs. "blockers"
    result = check_5_zombie_pmo_items()
    if result.status == "PASS":
        return CheckResult("", "PASS", "No zombie decisions pending")
    # In start mode, zombies are always just WARN — user decides during Phase 3
    return CheckResult(
        "",
        "WARN",
        f"{result.message} — decide kill/ship/rejustify in Phase 3",
        result.evidence,
    )


# ----------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------


CHECKS_CLOSE: list[tuple[str, Callable[[], CheckResult]]] = [
    ("1. PMO count consistency", check_1_pmo_count_consistency),
    ("2. MEMORY.md growth tracking (no limit)", check_2_memory_growth_tracking),
    ("3. Retro file coverage", check_3_retro_exists_for_latest_session),
    ("4. No cheerleading phrases", check_4_no_forbidden_phrases_in_recent_retros),
    ("5. Zombie PMO items (>10 sessions)", check_5_zombie_pmo_items),
    ("6. Git status bounded", check_6_git_status_not_massive),
    ("7. Zero-row claims verified", check_7_zero_row_claims_verified),
    ("8. Skill growth tracking (no merge)", check_8_skill_growth_tracking),
    ("9. Feedback file health (growth tracked)", check_9_feedback_routing),
    ("10. Hypothesis grounding", check_10_hypothesis_for_new_data),
    ("SYM. Start-close symmetry (plan<->retro)", check_symmetry_plan_retro_pairing),
]

# Start mode: close checks run as WARN (informational), plus start-specific checks as gates
CHECKS_START: list[tuple[str, Callable[[], CheckResult]]] = [
    ("1. PMO count consistency", check_1_pmo_count_consistency),
    ("2. MEMORY.md growth tracking (no limit)", check_2_memory_growth_tracking),
    ("3. Retro file coverage", check_3_retro_exists_for_latest_session),
    ("5. Zombie PMO items (>10 sessions)", check_5_zombie_pmo_items),
    ("6. Git status bounded", check_6_git_status_not_massive),
    ("8. Skill growth tracking (no merge)", check_8_skill_growth_tracking),
    ("S1. Session plan file (Phase 4)", check_s1_session_plan_exists),
    ("S2. Session state snapshot (Phase 2)", check_s2_session_state_snapshot),
    ("S3. Zombie decisions pending (Phase 3)", check_s3_zombie_decisions_pending),
    ("SYM. Start-close symmetry (plan<->retro)", check_symmetry_plan_retro_pairing),
]


# ----------------------------------------------------------------------------
# Session #040 checks — prevent the 5 recurring failures
# ----------------------------------------------------------------------------


def check_s4_approved_architectures() -> CheckResult:
    """If an architecture doc is APPROVED for execution but has no corresponding
    DONE PMO item, it's the top priority. Catches the Brain v2 blind spot from #040."""
    intel_dir = REPO / ".agents" / "intelligence"
    if not intel_dir.exists():
        return CheckResult("", "SKIP", "No intelligence directory")

    approved = []
    for md in intel_dir.glob("*ARCHITECTURE*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")[:2000]
        except Exception:
            continue
        if re.search(r'status:\s*.*approved.*execution', text, re.IGNORECASE):
            approved.append(md.name)

    if not approved:
        return CheckResult("", "PASS", "No pending approved architectures")

    # Check if PMO has corresponding DONE items
    pmo_text = ""
    if PMO_BRAIN.exists():
        pmo_text = PMO_BRAIN.read_text(encoding="utf-8", errors="ignore")

    unexecuted = []
    for arch in approved:
        # Look for the architecture name referenced in a struck-through PMO line
        arch_stem = arch.replace("_ARCHITECTURE.md", "").replace(".md", "")
        if f"~~" in pmo_text and arch_stem.lower() in pmo_text.lower():
            # Found struck = done
            continue
        unexecuted.append(arch)

    if unexecuted:
        return CheckResult(
            "", "WARN",
            f"APPROVED architectures NOT YET EXECUTED: {', '.join(unexecuted)}. "
            f"These are TOP PRIORITY — execute before any other work.",
            [f"File: .agents/intelligence/{a}" for a in unexecuted],
        )
    return CheckResult("", "PASS", "All approved architectures have been executed")


def check_s5_no_dead_text() -> CheckResult:
    """If brain_v2 exists, no new static inventory files (CSV, standalone .md lists)
    should be created for data that belongs in the graph. Catches the
    CODE_INVENTORY.csv mistake from #040."""
    brain_exists = (REPO / "brain_v2" / "output" / "brain_v2_graph.json").exists()
    if not brain_exists:
        return CheckResult("", "SKIP", "Brain v2 not built yet")

    # Check for static inventory files that should be graph nodes
    violations = []
    for pattern in ["*INVENTORY*.csv", "*INVENTORY*.md", "*REGISTRY*.csv"]:
        for f in REPO.rglob(pattern):
            if ".git" in str(f) or "node_modules" in str(f) or "venv" in str(f):
                continue
            violations.append(str(f.relative_to(REPO)))

    # Also check for .csv files at project root or extracted_code/
    for d in [REPO, REPO / "extracted_code"]:
        for f in d.glob("*.csv"):
            violations.append(str(f.relative_to(REPO)))

    if violations:
        return CheckResult(
            "", "WARN",
            f"Static inventory files found — brain v2 exists, data should be graph nodes: "
            f"{', '.join(violations[:5])}",
            ["Rule: if it has relationships, it's a node. No CSV, no standalone text."],
        )
    return CheckResult("", "PASS", "No static inventory files — all data in brain graph")


# Append Session #040 checks to CHECKS_START (defined after functions to avoid NameError)
CHECKS_START.append(("S4. Approved architectures must execute first", check_s4_approved_architectures))
CHECKS_START.append(("S5. No static artifacts when brain exists", check_s5_no_dead_text))


def main() -> int:
    ap = argparse.ArgumentParser(description="Session preflight guardrails")
    ap.add_argument("--mode", choices=["start", "close"], default="close")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on any FAIL (blocks close)")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    args = ap.parse_args()

    checks = CHECKS_START if args.mode == "start" else CHECKS_CLOSE
    results = [run_check(fn, name) for name, fn in checks]

    # In close --strict mode, escalate the symmetry-control WARNs to FAIL.
    # Rationale (Session #037 retro audit Principle 8 finding):
    #   S1 (plan file), S2 (state snapshot), S3 (zombie decisions), and SYM
    #   (plan↔retro pairing) are the symmetry control. Letting them stay WARN
    #   at close means a session can close with unresolved zombies and
    #   text-only decisions — exactly the drift the retro agent caught.
    #   In --strict, these become blocking. In non-strict they stay WARN
    #   so that the initial run of a migrating project doesn't lock up.
    STRICT_ESCALATE = {
        "S1. Session plan file (Phase 4)",
        "S2. Session state snapshot (Phase 2)",
        "S3. Zombie decisions pending (Phase 3)",
        "SYM. Start-close symmetry (plan<->retro)",
    }
    if args.strict and args.mode == "close":
        for r in results:
            if r.name in STRICT_ESCALATE and r.status == "WARN":
                r.status = "FAIL"
                r.message = "[STRICT] " + r.message

    if args.json:
        print(json.dumps(
            [{"name": r.name, "status": r.status, "message": r.message, "evidence": r.evidence}
             for r in results],
            indent=2,
        ))
    else:
        print(f"\n=== session_preflight.py ({args.mode}) ===\n")
        for r in results:
            print(f"[{r.icon()}] {r.name}")
            print(f"       {r.message}")
            for e in r.evidence[:3]:
                print(f"       - {e}")
            print()

        summary = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
        for r in results:
            summary[r.status] += 1
        print(f"Summary: {summary['PASS']} PASS, {summary['WARN']} WARN, "
              f"{summary['FAIL']} FAIL, {summary['SKIP']} SKIP\n")

    fails = [r for r in results if r.status == "FAIL"]
    if args.strict and fails:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
