# My Monitors — Personal Dashboard

On-demand snapshot tool for JP. Not deployed, not scheduled, not shared. Run it when you want the picture.

## What it shows

Two tabs in one self-contained HTML:

1. **BCM Dual-Control** — same-user batches, top operators, $ exposure, Wednesday cycle signature. Source: H13 finding from Session #037.
2. **Basis Health** — background jobs, custom function modules, ICF services, recent aborted jobs. Source: Gold DB cache (TBTCO + TFDIR_CUSTOM + ICFSERVICE).

## Run it

```bash
python Zagentexecution/my_monitors/run_my_monitors.py
start Zagentexecution/my_monitors/my_monitors_dashboard.html
```

## What it is NOT

- Not a cron job
- Not an email sender
- Not a production monitor
- Not a replacement for `sap_system_monitor.py` (live SM04/SM37/ST22)

It reads the local Gold DB. If the Gold DB is stale (no recent extraction run), the dashboard still renders but shows old numbers. Freshness date is printed in each tab.

## Why it exists

Session #038 (2026-04-05). `bcm_dual_control_monitor.py` (H13 Deliverable 1) was a good standalone tool but an orphan — no home, no discoverability, no reason to open it again after the first review. Bundling it next to the basis cache into a single launcher gives JP one URL to check weekly.

The original idea to wire it as a cron + SMTP email was rejected by JP in the session opening: this project does not do ops deployment. G60 is the reframing — same tool, different delivery mode.

## Related

- `Zagentexecution/bcm_dual_control_monitor.py` — source of Tab 1 data (run it first if Gold DB BNK_BATCH_HEADER needs refresh)
- `Zagentexecution/mcp-backend-server-python/sap_system_monitor.py` — live SAP monitoring (use when on-VPN for real-time SM04/SM37/ST22)
- `.agents/intelligence/PMO_BRAIN.md` — G60 entry
