"""extract_bcm_companion_fragments.py — ONE-TIME migration.

Slice the canonical companion HTML into contiguous, verbatim BYTE fragments so
that `build_bcm_structured_address_companion.py` can reassemble it byte-for-byte.

WHY THIS EXISTS
---------------
`companions/BCM_StructuredAddressChange.html` (~930 KB) was hand-authored across
Sessions #63-#75 *directly on the HTML* while the original Python builder stayed
frozen at Session #62 (~278 KB). The builder therefore REGRESSED the companion
(it only knew 16 of the 33 tabs). Re-hardcoding 640 KB of bespoke content back
into Python f-strings would just re-diverge.

Instead we invert the dependency: the HTML content becomes the source of truth.
This extractor cuts the canonical HTML into contiguous byte slices:
    00_head.html      = doctype .. <main class="main"> + first-tab indent
    NN_<tab-id>.html  = each top-level <div id="tab-..."> pane (verbatim)
    99_tail.html      = </main> .. </body></html>  (incl. <script>)
Because the slices are CONTIGUOUS and NON-OVERLAPPING, concatenating them in
order reproduces the original bytes EXACTLY. The extractor proves this before
writing anything (asserts reassembly == original; aborts otherwise).

The fragments under companions/bcm_structured_address_src/ are now the SSOT.
Edit a tab = edit its fragment; re-run the builder to regenerate the companion.

Run:  python extract_bcm_companion_fragments.py
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
SRC_HTML = REPO / "companions" / "BCM_StructuredAddressChange.html"
SRC_DIR = REPO / "companions" / "bcm_structured_address_src"
TABS_DIR = SRC_DIR / "tabs"
MANIFEST = SRC_DIR / "MANIFEST.json"

# Markers (bytes — we never decode, to stay byte-exact regardless of CRLF/LF).
TAB_START = re.compile(rb'<div id="tab-([a-z0-9-]+)" class="content')
MAIN_CLOSE = b"</main>"


def main() -> int:
    raw = SRC_HTML.read_bytes()
    print(f"Canonical source: {SRC_HTML}")
    print(f"  size      : {len(raw):,} bytes")
    print(f"  sha256    : {hashlib.sha256(raw).hexdigest()}")

    # Locate every top-level tab pane and the closing </main>.
    starts = [(m.start(), m.group(1).decode("ascii")) for m in TAB_START.finditer(raw)]
    if not starts:
        print("FATAL: no <div id=\"tab-...\"> panes found", file=sys.stderr)
        return 1
    main_close = raw.rfind(MAIN_CLOSE)
    if main_close == -1 or main_close < starts[-1][0]:
        print("FATAL: </main> not found after last tab", file=sys.stderr)
        return 1
    # Back the tail up to the start of the </main> line so its indent travels
    # with the tail (purely cosmetic — byte-exactness holds either way).
    line_start = raw.rfind(b"\n", 0, main_close)
    tail_start = line_start + 1 if line_start != -1 else main_close

    # Build the ordered cut plan: head, then one slice per tab, then tail.
    pieces: list[tuple[str, bytes]] = []
    pieces.append(("00_head.html", raw[: starts[0][0]]))
    for i, (off, tab_id) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else tail_start
        pieces.append((f"{i + 1:02d}_{tab_id}.html", raw[off:end]))
    pieces.append(("99_tail.html", raw[tail_start:]))

    # PROVE byte-exact reassembly BEFORE touching disk.
    reassembled = b"".join(blob for _, blob in pieces)
    if reassembled != raw:
        print("FATAL: reassembly != original — refusing to write.", file=sys.stderr)
        return 1
    print(f"Byte-exact reassembly verified across {len(pieces)} fragments.")

    # Write fragments.
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    TABS_DIR.mkdir(parents=True, exist_ok=True)
    # Clear any prior tab fragments so renames/removals can't leave orphans.
    for old in TABS_DIR.glob("*.html"):
        old.unlink()

    order: list[str] = []
    for name, blob in pieces:
        if name.startswith(("00_", "99_")):
            path = SRC_DIR / name
            rel = name
        else:
            path = TABS_DIR / name
            rel = f"tabs/{name}"
        path.write_bytes(blob)
        order.append(rel)

    raw_lf = raw.replace(b"\r\n", b"\n")
    MANIFEST.write_text(
        json.dumps(
            {
                "source_file": "companions/BCM_StructuredAddressChange.html",
                "extracted_from": "working tree (2026-06-15, incl. UBISO/De Morgan block)",
                "byte_count": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                # Newline-normalized hash — the line-ending-agnostic identity used by
                # the builder's integrity check, so a CRLF/LF checkout never cries wolf.
                "sha256_lf": hashlib.sha256(raw_lf).hexdigest(),
                "newline": "CRLF",
                "tab_count": len(starts),
                "order": order,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(order)} fragments + MANIFEST to {SRC_DIR}")
    print(f"  tabs: {len(starts)}  ({', '.join(t for _, t in starts[:6])}, ...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
