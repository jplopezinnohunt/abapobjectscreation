# BCM Structured Address companion — source fragments (SSOT)

This folder is the **single source of truth** for
`companions/BCM_StructuredAddressChange.html` (~930 KB, 33 tabs).

## Why fragments instead of one builder

The companion was hand-authored across Sessions #63–#75 **directly on the HTML**,
while the original Python builder (`build_bcm_structured_address_companion.py` v1)
stayed frozen at Session #62 — it only knew **16 of the 33 tabs (~278 KB)**.
Running v1 therefore **regressed** the companion, silently destroying ~640 KB of
hand-crafted content (the `dme-*` deep-dives, the per-bank DMEE tree tabs, the
matrix/evolution/current-solution/vendor-routing tabs, and edits to the rest).

The fix inverts the dependency: **the HTML content is the source.** The canonical
HTML is sliced into contiguous, verbatim byte fragments here; the builder (v2)
only *concatenates* them, so it can never regress content it cannot see.

## Layout

```
00_head.html              <!DOCTYPE> … <header> … <aside> nav … <main class="main"> + first-tab indent
tabs/NN_<tab-id>.html      one verbatim <div id="tab-…"> content pane each (01..33, document order)
99_tail.html              </main> … <script> … </body></html>
MANIFEST.json             ordered fragment list + sha256/byte_count of the canonical HTML
```

The fragments are **contiguous, non-overlapping byte slices** of the canonical
HTML, so `concat(order) == original` byte-for-byte (the extractor proves this
before writing, and the builder reports it on every run).

## Workflow

**Edit a tab** → edit its `tabs/NN_<id>.html` fragment → rebuild:

```bash
python ../../Zagentexecution/mcp-backend-server-python/build_bcm_structured_address_companion.py
# dry-run first (writes a temp copy + diffs, never overwrites the companion):
python ../../Zagentexecution/mcp-backend-server-python/build_bcm_structured_address_companion.py --check
```

**Add a tab** → add the `<div id="tab-…">` content as a new `tabs/NN_<id>.html`
fragment, add a matching `.nav-item` to the `<aside>` nav inside `00_head.html`,
append the fragment path to `MANIFEST.json` `order`, then rebuild.

**Re-cut fragments after a hand-edit to the HTML** (round-trip):

```bash
python ../../Zagentexecution/mcp-backend-server-python/extract_bcm_companion_fragments.py
```

The extractor re-slices the current HTML and self-verifies byte-exact reassembly.
After editing fragments, the builder's integrity line will (correctly) report a
new sha vs the extracted baseline — that is expected; re-run the extractor to
re-baseline once the HTML is the version you want to keep.

## Notes

- `MANIFEST.json.sha256` is the **as-extracted baseline** (HTML reproduced exactly).
  It is not a lock — editing fragments is the whole point; the field just lets the
  builder tell you whether the current output still matches the last extraction.
- The legacy v1 builder logic (data-driven renders from `components_map.json`,
  CSVs, the plan file) is preserved in git history of
  `build_bcm_structured_address_companion.py` (commit `a6b2895` onward).
- The `phase1_*.py` scripts never wrote this HTML — they only write JSON sidecars
  (`components_map.json` etc.). Their docstrings were corrected to say so.
