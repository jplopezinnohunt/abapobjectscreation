# _obsolete — dead SAP write tooling, moved out of the working tree (s099)

**75 scripts.** Every one could write to SAP (`write_source`, `set_source`, `DDIF_*_PUT`,
`RFC_ABAP_INSTALL_AND_RUN`, `.deploy(`, `BDC_INSERT`) with **no `ALLOW_D01_WRITES`
kill-switch**, and none of them is imported or named by any living file.

## Why they were moved rather than deleted

Deleting code is not the same as governing it. Someone may need to know HOW a thing was
once done. What they must not be is *runnable by accident*: the danger was never that
these were used, it was that a future session finds `deploy_yfi_v5` or
`direct_insert_seoclass` and runs it believing that is how we deploy. That is the class
of tool that corrupted real `N_MENARD` classes in INC-CLASS-LOSS (2026-06-12) — writing
in place, no transport, no review, on objects we do not own.

## Do not run anything in here

**Deploying ABAP is out of scope for this project** (JP, s099). There is no owner for
that capability here — see `brain_v2/capability_ownership.json`. If a write genuinely
has to happen it happens in the project that owns it, through a RELEASED transport, with
4-eyes.

## What was NOT moved

- 3 scripts flagged as possibly holding recovery history — they live in `_applied/`,
  which is already an archive, and they are records rather than tools.
- 9 scripts named by a living file, and 1 imported by its own test. Those need reading
  before any decision.
- `process_mining/accumulate_problems.py` and `method_registry.py` — false positives of
  the call-site regex. `stop_integrity_hook.py` uses them; they are live.

Evidence: `brain_v2/sap_write_tool_inventory.json` · `brain_v2/sap_write_tool_reachability.json` · claim 498 · rule #204 · PMO H100.
