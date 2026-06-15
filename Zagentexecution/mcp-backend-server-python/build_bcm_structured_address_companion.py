"""Build companions/BCM_StructuredAddressChange.html — FRAGMENT ASSEMBLER (v2).

Single source of truth = the verbatim byte fragments under
    companions/bcm_structured_address_src/   (00_head.html, tabs/NN_<id>.html, 99_tail.html)
listed, in order, by MANIFEST.json. This script concatenates them (in pure
binary) to reproduce the companion byte-for-byte and writes it to OUT.

WHY v2 (read before you touch this)
-----------------------------------
The companion (~930 KB, 33 tabs) was hand-authored across Sessions #63-#75
DIRECTLY on the HTML, while the original v1 builder stayed frozen at Session #62
(16 tabs, ~278 KB). Running v1 REGRESSED the companion — it overwrote 640 KB of
hand-crafted content with its stale 16-tab render. That is the bug this file
fixes: the content now lives in fragments, and this builder only *assembles*
them, so it can never regress what it cannot see.

  * The legacy v1 logic (tab_overview/tab_phase0/... f-strings + components_map
    /CSV/plan data-driven renders) is preserved in this file's git history
    (commit a6b2895 and its successors, up to the commit that introduced v2).
  * To re-cut fragments from a hand-edited HTML: run
    extract_bcm_companion_fragments.py (it self-verifies byte-exact slicing).
  * The phase1_*.py scripts do NOT build this HTML; they only write JSON
    sidecars (components_map.json etc.). Their old docstrings claimed otherwise.

Usage:
    python build_bcm_structured_address_companion.py            # write OUT
    python build_bcm_structured_address_companion.py --check     # dry-run + diff, never writes OUT
"""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "companions" / "BCM_StructuredAddressChange.html"
SRC_DIR = REPO / "companions" / "bcm_structured_address_src"
MANIFEST = SRC_DIR / "MANIFEST.json"


def assemble() -> tuple[bytes, dict]:
    """Concatenate the manifest fragments (binary) → full companion bytes."""
    if not MANIFEST.exists():
        raise SystemExit(
            f"FATAL: {MANIFEST} not found. The companion source fragments are "
            f"missing — run extract_bcm_companion_fragments.py first."
        )
    meta = json.loads(MANIFEST.read_text(encoding="utf-8"))
    blob = bytearray()
    missing = []
    for rel in meta["order"]:
        p = SRC_DIR / rel
        if not p.exists():
            missing.append(rel)
            continue
        blob += p.read_bytes()
    if missing:
        raise SystemExit(f"FATAL: missing fragment(s): {missing}")
    return bytes(blob), meta


def _report(html: bytes, meta: dict) -> None:
    # Compare on the newline-NORMALIZED hash so a CRLF vs LF checkout (git may
    # store the fragments either way) never reports a false mismatch — this
    # tracks git-content identity, which is what actually matters.
    baseline = meta.get("sha256_lf") or meta.get("sha256")
    actual = hashlib.sha256(html.replace(b"\r\n", b"\n")).hexdigest()
    n_tabs = html.count(b'<div id="tab-')
    print(f"  assembled : {len(html):,} bytes · {n_tabs} tab panes")
    if baseline:
        if actual == baseline:
            print(f"  integrity : MATCHES extracted baseline ({actual[:12]}…) — content-exact (newline-agnostic)")
        else:
            # Expected once fragments are legitimately edited; flag the delta.
            delta = len(html) - meta.get("byte_count", len(html))
            print(
                f"  integrity : differs from extracted baseline "
                f"(now {actual[:12]}…, was {baseline[:12]}…, Δ{delta:+,} bytes) "
                f"— fragments were edited since extraction (expected after edits)."
            )


def build(check: bool) -> int:
    html, meta = assemble()
    _report(html, meta)
    if check:
        tmp = Path(tempfile.gettempdir()) / "BCM_StructuredAddressChange.__check__.html"
        tmp.write_bytes(html)
        current = OUT.read_bytes() if OUT.exists() else b""
        same = html == current
        print(f"  --check   : wrote {tmp}")
        print(f"  vs OUT    : {'IDENTICAL' if same else f'DIFFERS (OUT={len(current):,} bytes)'}")
        return 0 if same else 0  # check is informational; non-fatal either way
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(html)
    print(f"Built: {OUT} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build(check="--check" in sys.argv))
