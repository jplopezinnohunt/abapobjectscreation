# D01 vs P01 Drift Protocol — BCM Structured Address Phase 0

**Created**: 2026-04-29 · **Session**: #62 · **Driver**: user concern
*"Pueden haber mantenido cosas en producción"* (P01 patches that never returned to D01).

## Why this matters for our change

Our Phase 2 design rests on **P01-extracted source code** (Pattern A fix at
`YCL_IDFI_CGI_DMEE_FALLBACK_CM001` lines 13-31, Event 05 registrations in
`TFPM042FB`, DMEE node sources from `dmee_tree_node_p01.csv`).

If D01 has a different version of any of these — older, stale, or with
in-flight WIP — then:

1. **Pattern A fix line numbers won't match** in D01 (the `WHEN` block may
   be on different lines or absent entirely)
2. **Activating V001 from D01 → P01 may overwrite production patches** that
   never came back to D01
3. **The 5 P01-only objects (Finding I)** are the visible tip — there may
   be more we haven't enumerated

Drift exists at three levels: **code source** (REPOSRC timestamps),
**TADIR existence** (objects in one system not the other), and
**customizing content** (table rows in P01 not in D01 or vice versa).

## What the script covers

`Zagentexecution/mcp-backend-server-python/d01_vs_p01_drift_detector.py`

### Code objects (named, last-changed comparison)

| Category | Items |
|---|---|
| UNESCO custom Y* classes | 5 (FALLBACK, FR, UTIL, DE, IT) |
| UNESCO custom ENHO impls | 5 (Y_IDFI_CGI_DMEE_COUNTRY/COUNTRIES_*) |
| UNESCO custom Z* utilities | 2 (ZDMEE_EXIT_SEPA_21, Z_DMEE_EXIT_TAX_NUMBER) |
| SAP-std country dispatcher | 6 (FACTORY, GENERIC, FR, DE, IT, GB) |
| SAP-std FI_PAYMEDIUM_DMEE_CGI_05 | 1 |
| CITIPMW industry solution FMs | 9 (V3_PAYMEDIUM_DMEE_05 + 8 exits) |

### DMEE trees (head metadata + node count)

`/SEPA_CT_UNES`, `/CITI/XML/UNESCO/DC_V3_01`, `/CGI_XML_CT_UNESCO`,
`/CGI_XML_CT_UNESCO_1` — `DMEE_TREE_HEAD.LAST_USER/LAST_DATE` per version,
plus full `DMEE_TREE_NODE` row counts. Already known: CGI tree has ~2x
nodes in D01 (per Session #039 H18 finding) — drift detector confirms +
quantifies.

### Customizing tables (full content per-row diff)

| Table | Why drift matters |
|---|---|
| `TFPM042FB` | OBPM4 Event 05 registrations — Pattern A fix flows through this |
| `T042Z` | PMW format → DMEE tree — version activation goes here |
| `T042E` | Country-currency → format — Worldlink mapping |
| `T042I` | IBAN config |
| `T042D` | Paying co code config |
| `T042B` | PMW format header |
| `TFIBLMPAYBLOCK` | BCM routing rule (Claim #65) — change risk |
| `T012`, `T012K`, `T012T` | House banks |
| `TBKK1` | Bank chains |
| `DMEE_TREE_HEAD/NODE/COND/SORT` | All DMEE config holistic |

### Dynamic TADIR enumeration (catches unknown objects)

The script does NOT only check what we already named — it enumerates via
TADIR LIKE patterns to catch objects we never extracted:

```
CLAS YCL_IDFI%       — all Y FI custom classes
CLAS YCL_%DMEE%      — broad DMEE class scan
CLAS /CITIPMW/%      — full CITIPMW class set
FUGR /CITIPMW/%      — full CITIPMW funcgroup set
FUNC Y_FPAY% / Z_FPAY%  — any payment FMs we missed
FUNC Y_DMEE% / Z_DMEE%  — any DMEE FMs we missed
PROG Y* / Z* in YA package — any programs in UNESCO custom package
PROG YRGGB% / ZRGGB%  — substitution exit programs (H48)
ENHO Y* / Z*         — all custom enhancements
XSLT CGI% / Y* / Z*  — XSLT post-processors
TABL YT* in YA       — custom config tables
```

Per pattern, compare set membership in P01 vs D01 + per-object `CHANGED_TS`.

## Severity classification

| Severity | Trigger | Phase 2 impact |
|---|---|---|
| **CRITICAL** | Object in D01 only (possible WIP we'd clobber); DMEE tree node count divergence; tree active version missing in D01 | BLOCKS Phase 2 — must resolve before any D01 transport |
| **HIGH** | Class include drift; FM drift; ENHO drift; customizing table content drift; TADIR P01-only object | Requires N_MENARD review or retrofit before Phase 2 |
| **MEDIUM** | TADIR timestamp drift on BOTH-existing objects | Verify intent, may be acceptable |
| **LOW** | Probe error (table doesn't exist or auth blocked) | Document but continue |

## How to run

```bash
# Need: P01 SNC/SSO active + D01 user/pass
export P01_SNC_PARTNER='p:CN=P01, O=UNESCO, C=FR'  # or similar
export SNC_MYNAME='p:CN=jp_lopez@unesco.org'
export D01_USER='your_user'
export D01_PASS='your_pass'

cd c:/Users/jp_lopez/projects/abapobjectscreation
python Zagentexecution/mcp-backend-server-python/d01_vs_p01_drift_detector.py
```

Outputs:
- `knowledge/domains/Payment/phase0/d01_vs_p01_drift_data.json` — raw probe data
- `knowledge/domains/Payment/phase0/d01_vs_p01_drift_report.md` — categorized drift report

## Phase 2 gate (added to plan)

**Before any D01 transport in Phase 2 we MUST**:

1. Run drift detector
2. Resolve every CRITICAL drift (P01-only retrofit OR D01-only WIP review)
3. Document every HIGH drift (decide: retrofit, ignore, or escalate to N_MENARD)
4. Treat MEDIUM as informational
5. Re-run drift detector after retrofit transport — confirm CRITICAL = 0

This becomes a hard exit gate for Phase 0 → Phase 2.

## What this protocol does NOT cover (acknowledged limits)

- **V01** (QA) — only D01↔P01 compared. V01 may have its own drift but
  only matters for cutover-window verification (Phase 4), not Phase 2 design.
- **Master data** (LFA1/ADRC) — out of scope for code/config drift; vendor
  DQ check separate (Finding A).
- **BCM workflow definitions (90000003)** — workflow tables (HRP1000/1001)
  not included; would need separate probe if change touches workflow (it
  doesn't in our scope).
- **ABAP source content hash** — current version compares timestamps + last
  user. Full source-by-source byte comparison is a follow-up if any HIGH
  drift surfaces and we need to know exactly what changed. Add `ABAP_SOURCE`
  RFC call per object if needed (slow — 100+ objects × 2 systems).

## Cross-reference

- Plan section: "Phase 0 execution findings" → Finding I (D01 vs P01 inventory)
- Brain: `feedback_only_p01_for_config_analysis` (rule #204) — this protocol
  generalizes that rule with verification step
- Companion: tab "Phase 0" should link to drift report once generated
