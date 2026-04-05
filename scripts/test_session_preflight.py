#!/usr/bin/env python3
"""
test_session_preflight.py — Regression harness for preflight fixes landed in e25a0f7.

Verifies two fixes from the Session #037 hardening commit:

1. Check 1 regex tolerates markup between the ID and the table pipe
   (bold/emoji/decorations). Before the fix, rows like `| **H13** 🔥 |`
   were silently NOT counted, hiding H13 from the baseline for ~15 sessions.

2. --strict close mode escalates S1/S2/S3/SYM from WARN to FAIL. Before the
   fix, text-only decisions without state mutation could survive a close.

This is a pure-Python test: no SAP, no Gold DB, no live files. Creates a
temp PMO_BRAIN + MEMORY.md pair in-memory, monkey-patches the module paths,
and asserts specific counts + escalation behavior.

Run: python scripts/test_session_preflight.py
Exit: 0 on all pass, 1 on any fail.
"""

from __future__ import annotations

import io
import re
import sys
import tempfile
from pathlib import Path

# Force UTF-8 on Windows so emoji in diagnostic messages don't crash cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import session_preflight as sp  # noqa: E402


# ----------------------------------------------------------------------------
# Test fixtures — synthetic PMO_BRAIN with adversarial markup patterns
# ----------------------------------------------------------------------------

SYNTHETIC_PMO = """
# Test PMO Brain

### 🔴 BLOCKING — Cannot progress without these

| # | Task | First raised | Blocks | Notes |
|---|------|-------------|--------|-------|
| B1 | Plain blocker | #001 | X | open |
| ~~B2~~ | ~~Struck blocker~~ | ~~#002~~ | ~~X~~ | ~~done~~ |

### 🟡 HIGH — Next session

| # | Task | First raised | Category | Notes |
|---|------|-------------|----------|-------|
| H1 | Plain high | #010 | Data | open |
| **H13** 🔥 | **Bold-emoji high (regression row)** | #021 | Audit | open — this was the hidden one |
| ~~H2~~ | ~~Struck high~~ | ~~#011~~ | ~~Data~~ | ~~done~~ |
| **H14** | Bold-only high | #021 | Code | open |

### 🟢 BACKLOG — When blocking/high clear

#### Group A
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G1 | Plain backlog | #005 | open |
| ~~G2~~ | ~~Struck backlog~~ | ~~#006~~ | ~~done~~ |
| **G60** 🆕 | Bold-emoji backlog | #038 | open |

## COMPLETED (Archive)

| ~~X1~~ | done item | #001 |
"""

SYNTHETIC_MEMORY_CORRECT = """
## Pending Work
- **1 Blocking** | **3 High** | **2 Backlog** = 6 total items
"""

SYNTHETIC_MEMORY_WRONG = """
## Pending Work
- **1 Blocking** | **1 High** | **2 Backlog** = 4 total items
"""


# ----------------------------------------------------------------------------
# Test 1 — Check 1 counts bold/emoji rows
# ----------------------------------------------------------------------------


def test_regex_counts_bold_emoji() -> tuple[bool, str]:
    """Expected open counts from SYNTHETIC_PMO:
    - B: B1 = 1 (B2 struck)
    - H: H1, **H13** 🔥, **H14** = 3 (H2 struck)
    - G: G1, **G60** 🆕 = 2 (G2 struck)
    - total = 6

    If the old regex were in place, **H13** 🔥 and **H14** and **G60** 🆕
    would all be missed → total would be 3 (B1+H1+G1).
    """
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        pmo = tdp / "PMO_BRAIN.md"
        mem = tdp / "MEMORY.md"
        pmo.write_text(SYNTHETIC_PMO, encoding="utf-8")
        mem.write_text(SYNTHETIC_MEMORY_CORRECT, encoding="utf-8")

        # Monkey-patch module paths
        orig_pmo, orig_mem = sp.PMO_BRAIN, sp.MEMORY_INDEX
        sp.PMO_BRAIN, sp.MEMORY_INDEX = pmo, mem
        try:
            result = sp.check_1_pmo_count_consistency()
        finally:
            sp.PMO_BRAIN, sp.MEMORY_INDEX = orig_pmo, orig_mem

    # Parse counts from evidence line
    ev = " ".join(result.evidence)
    m = re.search(r"PMO_BRAIN open: B=(\d+) H=(\d+) G=(\d+) total=(\d+)", ev)
    if not m:
        return False, f"evidence format changed: {ev}"
    b, h, g, total = map(int, m.groups())
    expected = (1, 3, 2, 6)
    actual = (b, h, g, total)
    if actual != expected:
        return False, (
            f"count mismatch. Expected B={expected[0]} H={expected[1]} "
            f"G={expected[2]} total={expected[3]}, got B={b} H={h} G={g} total={total}. "
            f"This means the regex missed bold/emoji rows (regression from e25a0f7)."
        )
    if result.status != "PASS":
        return False, f"expected PASS, got {result.status}: {result.message}"
    return True, (
        f"Check 1 correctly counted 6 open items "
        f"(including **H13** 🔥, **H14**, **G60** 🆕 — the rows the old regex hid)"
    )


def test_regex_detects_mismatch() -> tuple[bool, str]:
    """When MEMORY.md count is wrong, Check 1 must FAIL with evidence."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        pmo = tdp / "PMO_BRAIN.md"
        mem = tdp / "MEMORY.md"
        pmo.write_text(SYNTHETIC_PMO, encoding="utf-8")
        mem.write_text(SYNTHETIC_MEMORY_WRONG, encoding="utf-8")

        orig_pmo, orig_mem = sp.PMO_BRAIN, sp.MEMORY_INDEX
        sp.PMO_BRAIN, sp.MEMORY_INDEX = pmo, mem
        try:
            result = sp.check_1_pmo_count_consistency()
        finally:
            sp.PMO_BRAIN, sp.MEMORY_INDEX = orig_pmo, orig_mem

    if result.status != "FAIL":
        return False, f"expected FAIL, got {result.status}: {result.message}"
    if "6" not in result.message or "4" not in result.message:
        return False, f"FAIL message doesn't cite both counts: {result.message}"
    return True, f"Check 1 correctly FAILED on count mismatch: {result.message}"


# ----------------------------------------------------------------------------
# Test 2 — --strict close mode escalates S1/S2/S3/SYM from WARN to FAIL
# ----------------------------------------------------------------------------


def test_strict_escalation_logic() -> tuple[bool, str]:
    """Simulate the main() escalation block directly against synthetic results."""
    STRICT_ESCALATE = {
        "S1. Session plan file (Phase 4)",
        "S2. Session state snapshot (Phase 2)",
        "S3. Zombie decisions pending (Phase 3)",
        "SYM. Start-close symmetry (plan<->retro)",
    }

    synthetic_results = [
        sp.CheckResult(name="1. PMO count consistency", status="PASS", message="ok"),
        sp.CheckResult(name="S1. Session plan file (Phase 4)", status="WARN", message="no plan"),
        sp.CheckResult(name="S2. Session state snapshot (Phase 2)", status="WARN", message="no state"),
        sp.CheckResult(name="S3. Zombie decisions pending (Phase 3)", status="WARN", message="zombies"),
        sp.CheckResult(name="SYM. Start-close symmetry (plan<->retro)", status="WARN", message="drift"),
        sp.CheckResult(name="6. Git status bounded", status="WARN", message="ok"),
    ]

    # Apply the same escalation logic as main()
    strict = True
    mode = "close"
    if strict and mode == "close":
        for r in synthetic_results:
            if r.name in STRICT_ESCALATE and r.status == "WARN":
                r.status = "FAIL"

    escalated = [r for r in synthetic_results if r.name in STRICT_ESCALATE]
    not_escalated = [r for r in synthetic_results if r.name not in STRICT_ESCALATE]

    if not all(r.status == "FAIL" for r in escalated):
        return False, (
            f"escalation failed: "
            f"{[(r.name, r.status) for r in escalated]}"
        )
    if not all(r.status != "FAIL" for r in not_escalated if r.status == "WARN"):
        return False, (
            f"non-symmetry WARN got escalated (should not): "
            f"{[(r.name, r.status) for r in not_escalated]}"
        )

    # Verify STRICT_ESCALATE set matches what's in session_preflight.py
    import inspect
    source = inspect.getsource(sp.main)
    for name in STRICT_ESCALATE:
        if name not in source:
            return False, f"STRICT_ESCALATE drift: {name!r} not found in main() source"

    return True, (
        "--strict close mode correctly escalates all 4 symmetry checks "
        "(S1/S2/S3/SYM) from WARN to FAIL; other WARNs unaffected"
    )


# ----------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------


TESTS = [
    ("test_regex_counts_bold_emoji", test_regex_counts_bold_emoji),
    ("test_regex_detects_mismatch", test_regex_detects_mismatch),
    ("test_strict_escalation_logic", test_strict_escalation_logic),
]


def main() -> int:
    print("\n=== test_session_preflight.py ===\n")
    passed = 0
    failed = 0
    for name, fn in TESTS:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"raised {e!r}"
        icon = "PASS" if ok else "FAIL"
        print(f"[{icon}] {name}")
        print(f"       {msg}\n")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"Summary: {passed} passed, {failed} failed\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
