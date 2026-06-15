# abap_deploy — THE disciplined ABAP write path (ported from CRP)

Born from **INC-CLASS-LOSS (2026-06-12)** and ported from CRP `unescrp` (the working reference, S-119).
This folder is **the single gated path** for changing ABAP on D01. It replaces the ~78 ad-hoc
`deploy_*/reconstruct_*/force_*/direct_insert_*` scripts in `../mcp-backend-server-python/`.

Governing rule: `ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md` (BROADCAST-007).
Landscape (probed 2026-06-15): **D01 (DEV) → V01 (QAS) → P01 (PROD)**, basis 7.50, transports released at scale.

## What was ported from CRP (point A — done)

| File | Role |
|---|---|
| `objects_manifest.yaml` | THE own-objects-only map. deploy refuses anything not listed (the N_MENARD stopper). |
| `deploy_object.py` | The 9-gate write path: own-objects → TADIR/metadata → PRE-readback → **hard diff-gate (HALT on deletions)** → W-5 operator guard → concurrent-writer guard → confirm → write → **POST-readback byte-verify**. Default `--dry-run`. |
| `verify_mirror.py` | Read-only 0-diff verifier: D01 active vs git mirror (pure ADT GET + normalize, **not abapGit**). |
| `../../.claude/agents/process-guardian.md` | Session-close guardian: HALT if a deploy lacks gated-path evidence; one-in-one-out; ONE corrective action. |

The gate that would have **prevented INC-CLASS-LOSS**: a write to `YCL_FI_*`/`N_MENARD` objects is refused at
**gate-0** (not in our manifest) and the **hard diff-gate** would have HALTED on the mass deletion.

## How to use

```bash
# read-only: prove the gates + plumbing (works today, even with writes kill-switched)
python deploy_object.py ZCL_CRP_CERT_READER --dry-run
python verify_mirror.py --only ZCL_CRP_CERT_READER

# seed the git mirror from D01 (read-only against D01; writes local files)
python verify_mirror.py --adopt-missing

# real write (requires ALLOW_D01_WRITES=1; you confirm in chat first)
python deploy_object.py ZCL_CRP_CERT_READER --yes
```

## What is NOT ported (deliberately — would be cargo-cult)

- **smoke_d01.py invariants** — CRP's are app-specific (zcrp_aprvl_hist pairing, currency render-safety). Ours
  must assert OUR invariants; faking them is the cargo-cult the rule warns against. Add when we have real ones.
- **quality_check.py functionality fingerprints** — same: CRP's fingerprints count CRP-specific write-sites.
  A generic anti-pattern gate can be added; the functionality-preservation baseline must be ours.

## POINT B — deferred (JP, 2026-06-15): the native rails

Neither this project NOR CRP does these yet. Decide later:
1. **Create + RELEASE the transport** (`SAPADTClient.create_transport` / `transport_release` already exist) →
   the durable version + enables import to **V01 (QAS)**.
2. **ATC via REST** (`SAPADTClient.atc_run` / `atc_worklist` already exist) as the pre-release gate, replacing
   any home-made syntax/fingerprint check.
3. Retire the `ALLOW_D01_WRITES` kill-switch once #1 + the gate stack are the path (replace blunt block with
   disciplined process).
