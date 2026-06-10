# Closing Activities Domain

## What is this domain?

**Closing Activities** tracks all period-end and year-end accounting activities at UNESCO — what runs, who runs it, when, and whether it is operating correctly. Each activity is a discrete process that must complete before a fiscal period can be locked.

This is a new domain created in Session #078 (2026-06-05). The first tracked activity is FX Revaluation.

## Why it matters

UNESCO has no formal month-end closing calendar. Activities are run manually by individual accountants with no formal sign-off gate, no backup assignment enforcement, and no automation. This domain is the first step toward building that governance layer.

## Scope

| Activity | Status | Companion | Knowledge Doc |
|----------|--------|-----------|---------------|
| FX Revaluation (F.05 / SAPF100) | ACTIVE — interactive, no background jobs | `closing_activities_v1.html` | **`fx_revaluation_process.md`** (canonical process brain) + `fx_revaluation_closing_calendar_2025.md` (timing) + `sap_variant_forensic_methodology.md` (technique) |
| Automatic Clearing (SAPF124) | AUTOMATED — daily JOBBATCH job | — | — |
| Period Lock (OB52 / MMPV) | MANUAL — no formal gate | — | — |
| GR/IR Clearing | TBD | — | — |
| Accruals / Deferrals | TBD | — | — |
| Asset Depreciation (AFAB) | TBD | — | — |
| Carry-Forward (CJCF / KJHC) | TBD | — | — |

## Data Sources

- `BKPF` — document header (CPUDT=actual entry date, BUDAT=posting date, TCODE=transaction, USNAM=user)
- `TBTCO / TBTCP` — background job header/steps
- `T044A` — valuation method definitions
- `T030H` — OBA1 FX account determination
- `SKB1` — GL master per company code (XSPEB=blocked flag)

## Domain Owner

Finance / Treasury team — controller responsible for period close at each institute.
