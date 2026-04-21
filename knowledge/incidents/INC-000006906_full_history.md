# INC-000006906 — Full History (preserved for CP-001 traceability)

> **Purpose:** this file preserves the complete 9-section analysis + Appendix A
> pivot history + Appendix B known-unknowns exactly as authored at incident
> closure. The canonical short form lives at
> `INC-000006906_maputo_mzn_bank_reconciliation_download.md`. This full-history
> copy exists so no causal reasoning, evidence chain, or pivot narrative is
> lost when the canonical doc is compressed (per CP-001 "Knowledge over
> velocity" + CP-002 "Preserve first").
>
> **Relocated:** Session #058 (2026-04-20). Nothing deleted, only split.

---

# INC-000006906 — Maputo MZN Bank Reconciliation: YTR3/YTBAE002 TIME_OUT

**Status:** `RESOLVED_FIX_PROPOSED` — TIER_2 code-backed root cause. One-char fix written.
**Received:** 2026-04-16 14:42:27 UTC
**Dump captured:** 2026-04-20 13:51:49 UTC (P01 client 350, user J_DAVANE)
**Analyzed sessions:** #056–#058 (2026-04-20 → 2026-04-20)
**Domain:** Treasury / Bank Reconciliation / ABAP Custom Reports / Runtime Performance
**Secondary domains:** FI, Master Data Config, EBS
**Reporter = Affected user:** Josina Davane (`J_DAVANE`), FU/MAP (Maputo field office)

---

## 1. Executive Summary

On 2026-04-20 at 13:51:49 (P01 client 350), Maputo field-office accountant
`J_DAVANE` ran transaction **`YTR3`** (custom bank-reconciliation posting
program **`YTBAE002`**, package `YA`, 3,422 lines). Her dialog session
terminated with runtime error **`TIME_OUT`** at include **`SAPDBSDF:1983`
form `PUT_BSIS`**. Despite the dump point naming the SAP-standard logical
database, the root cause is UNESCO-owned and is code-backed (TIER_2):
**`YTBAE002.abap:27`** declares `CONSTANTS: GC_MOD TYPE C VALUE 'E'`, and the
program issues four `CALL TRANSACTION ... USING BDCDTAB MODE GC_MOD` calls
to standard FI clearing TCODEs `FB08` (`:723, :853`), `F-04` (`:771`), and
`FBRA` (`:819`) inside a `GET bsis` / `LDB_PROCESS` loop. MODE `'E'` means
"display errors only" — on any BDC error SAPGUI opens on the user's
workstation. From Maputo (slow WAN), each error handshake adds seconds of
round-trip latency; the cumulative dialog time exceeds `rdisp/max_wprun_time`
and SAP aborts the caller's LDB fetch with `TIME_OUT`. From HQ (fast LAN),
the same program runs in ~2 seconds — user reproduced this. The fix is at
`YTBAE002.abap:27`: change `'E'` to `'N'` (silent mode). Errors are already
captured in `Y_MESSTAB` at each call site and surfaced through
`PROC_RECONCIL_MESS_ADD` (:754, :795, :840, :874), so no functional
regression. Fix written at `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`.

---

## 2. Dump Evidence (TIER_1, from user screenshot 2026-04-20 13:51:49)

```
Runtime error ........ TIME_OUT
Category ............. ABAP Programming Error
Transaction .......... "YTR3 "
Program .............. YTBAE002
Include .............. SAPDBSDF               (SAP standard LDB)
Line ................. 1983
Form ................. PUT_BSIS               (SAP-std row-delivery callback)
Screen ............... SAPMSSY0 1000 line 6   (dialog dispatcher)
User ................. J_DAVANE
Client ............... 350   (P01)
Event ................ START-OF-SELECTION
Date / time .......... 2026-04-20 13:51:49
SAP note hint ........ "Database where the result set is too large"
                       "Use SELECT * INTO internal table ... instead of
                        SELECT * ... ENDSELECT"
                       "Database access without suitable index"
```

TIER_1 source: user-provided ST22 screenshot. The note hint misleads —
`PUT_BSIS` is SAP-standard code and its line 1983 is the SELECT that the
LDB itself runs. The TIME_OUT reflects the CALLER (YTBAE002) exceeding the
work-process cap during its GET-bsis iteration, not an indexing defect in
`PUT_BSIS`.

---

## 3. The Program — `YTR3` / `YTBAE002` / `SAPDBSDF` / `PUT_BSIS`

| Object | Type | Status | Role |
|---|---|---|---|
| `YTR3` | R3TR TRAN | live TSTC: `TCODE=YTR3 PGMNA=YTBAE002 DYPNO=1000 CINFO=9` | Dialog TCODE that J_DAVANE launched. One-to-one binding. |
| `YTBAE002` | R3TR PROG, package `YA` | extracted_code/CUSTOM/YTBAE002/YTBAE002.abap (3,422 lines, monolithic, zero INCLUDEs, zero Y/Z deps) | **Custom bank-reconciliation POSTING program** (not a report). Reverses, clears, and resets-cleared open-item lines on bank sub-bank GLs via BDC to FI transactions. |
| `SAPDBSDF` | SAP-std LDB (logical database for FI documents) | SAP-owned; contains `PUT_BSIS` form | Delivers BSIS rows to the caller via `GET bsis` event or `LDB_PROCESS` callback. `:1983` is the SELECT on BSIS. |
| `PUT_BSIS` | form inside SAPDBSDF | SAP-owned | Row-delivery callback. TIME_OUTs here indicate caller-side pressure, not a defect in `PUT_BSIS`. |

**Author history (CTS, TIER_1):** 10 transports 2023-04-14 → 2023-06-29 by
external consultant **N_MENARD**. Zero transports since 2023-06-29. Code
frozen for ~3 years. Not a regression. Same code succeeded 5 times in BATCH
in March 2026 (TBTCO Status `F`) because batch has no dispatcher cap.

**Selection screen (YTBAE002.abap:297-310):**

| Param | Type | Obligatory | Default | Line |
|---|---|---|---|---|
| `GP_BUKRS` | `BSEG-BUKRS` | YES | `'UNES'` | :297 |
| `GP_HBKID` | `T012-HBKID` | YES | — | :298 |
| `GP_HKTID` | `T012K-HKTID` | YES | — | :299 |
| `GP_BUDAT` | `BSIS-BUDAT` | YES | `SY-DATUM` | :300 |
| `GP_STATE / GP_RECON` | radio group | default `STATE='X'` | — | :305-306 |
| `GP_AUGDT` | `BSEG-AUGDT` | no (hidden unless `RECON='X'`) | — | :310 |

No SELECT-OPTIONS. No date range. One fiscal year only (`GJAHR=GP_BUDAT(4)`
at :369).

**Scope resolution (YTBAE002.abap:1089-1129):**

```abap
1098  SELECT SAKNR XOPVW FROM SKB1 INTO W_SKB1
1099    WHERE BUKRS EQ GP_BUKRS
1100      AND HBKID EQ GP_HBKID
1101      AND HKTID EQ GP_HKTID.
1112    IF ( W_SKB1-SAKNR+3(2) = '11'
1113      OR W_SKB1-SAKNR+3(2) = '13'
1114      OR W_SKB1-SAKNR+3(2) = '15' ).
1115      IF W_SKB1-XOPVW EQ 'X'.
1117        APPEND GS_SAKNR TO GR_SAKNR_OI.
1118      ENDIF.
1119    ENDIF.
1127  ENDSELECT.
```

`GR_SAKNR_OI` is then fed to LDB SDF at `:1509` (`CALL FUNCTION 'LDB_PROCESS'
LDBNAME='SDF'`). The LDB reads BSIS and delivers rows back via callback
`PROC_LDB_CALLBACK` (:1448-1475) → `PROC_BSIS` (:1144-1154) → accumulator
`GT_BSIS_TOT`. **YTBAE002 does NOT use any YBANK_* Report-Painter set** —
the 3,422-line corpus has zero hits for `RS_SET_VALUES_READ`,
`G_SET_GET_ALL_VALUES`, `K_HIERARCHY_TABLES_READ`, `G_SET_LIST_READ`,
`G_SET_FETCH`.

**Output:** classical list report (`WRITE` statements + `CALL SCREEN 9000`).
No ALV, no CL_GUI_*.

---

## 4. Root Cause — MODE 'E' Network Coupling

### 4.1 The constant (`YTBAE002.abap:27`)

```abap
27  CONSTANTS: GC_MOD     TYPE C VALUE 'E',
```

MODE `'E'` for `CALL TRANSACTION ... USING` is defined by SAP as *"Only
display if error — opens SAPGUI when a BDC error occurs so the user can
correct the dialog interactively."* This forces a client-side GUI handshake
whenever the BDC step raises a message.

### 4.2 The four BDC call sites (inside `GET bsis` / LDB loop)

All four `CALL TRANSACTION` statements are inside the BSIS-iteration driven
by `LDB_PROCESS` at `:1509`. Each fires when the program decides (from BSIS
row content + PAYR/BKPF correlation) that a line needs to be reversed,
cleared, or reset-cleared:

| Line | TCODE | Purpose | BDC wrapper |
|---|---|---|---|
| `:723` | `FB08` | Reverse document | `CALL TRANSACTION 'FB08' USING BDCDTAB MODE GC_MOD MESSAGES INTO Y_MESSTAB` |
| `:771` | `F-04` | Post with clearing | same pattern, MODE `GC_MOD` |
| `:819` | `FBRA` | Reset cleared items | same pattern |
| `:853` | `FB08` | Reverse (second site, different branch) | same pattern |

Each CALL is paired with `MESSAGES INTO Y_MESSTAB` and a
`PROC_RECONCIL_MESS_ADD` at `:754 / :795 / :840 / :874` that persists the
`Y_MESSTAB` contents into `GT_RECONCIL_MESS` for the final list output. So
the program already has a silent-capture path. The MODE `'E'` is redundant
with this capture path and ONLY adds the GUI-dialog side effect.

### 4.3 The mechanism

```
J_DAVANE (Maputo WAN) clicks execute in YTR3
  -> YTBAE002 START-OF-SELECTION
     -> SKB1 SELECT (:1098) returns OI GLs (e.g. 0001194424)
     -> LDB_PROCESS LDBNAME='SDF' (:1509)
        -> SAPDBSDF PUT_BSIS (:1983) SELECTs BSIS rows matching GR_SAKNR_OI
           -> for each BSIS row delivered via PROC_BSIS (:1144)
              -> program decides to reverse/clear/reset
                 -> CALL TRANSACTION 'FB08' MODE 'E' (:723)
                    -> BDC encounters any transient error (lock, auth, msg)
                       -> SAPGUI dialog opens on J_DAVANE's workstation
                          -> Maputo WAN RTT = hundreds of ms per round-trip
                             -> cumulative GUI time exceeds rdisp/max_wprun_time
                                -> dispatcher aborts with TIME_OUT
                                   -> stack shows SAPDBSDF:1983 because that's
                                      where the WP was waiting in GET bsis
```

The `SAPDBSDF:1983` location is a **symptom of caller-time consumption**,
not a cause. The LDB is blocked waiting for the caller's GET-handler to
finish; the CALL TRANSACTION inside the handler is what actually consumed
the clock.

### 4.4 Evidence the user reproduced the network axis

User reproduced the same program from HQ (fast LAN) in ~2 seconds with no
dump. Identical program, identical data, identical user inputs — only the
network path differs. This falsifies any data-volume or code-loop
hypothesis and confirms the WAN-dependent MODE 'E' handshake as the
critical path.

### 4.5 Evidence tier

- **TIER_1** for code anchors: `YTBAE002.abap:27`, `:723`, `:771`, `:819`,
  `:853`, `:1098-1101`, `:1112-1118`, `:1509` (extracted source).
- **TIER_1** for the HQ reproduction (user direct observation).
- **TIER_1** for the dump (ST22 screenshot).
- **TIER_2** for the network-coupling mechanism (consistent with all code
  + all observations, no single query isolates it).

---

## 5. Fix

**File:** `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`

**FIX_A (recommended, one character):** `YTBAE002.abap:27` change `'E'` to
`'N'`. MODE `'N'` runs the BDC silently; errors already flow through
`Y_MESSTAB` → `GT_RECONCIL_MESS` → the list output. Execution becomes
network-independent.

**FIX_B (same change + anchor comment):** identical change with an inline
comment citing INC-000006906 so a future dev cannot silently regress `'E'`.

**FIX_C (optional hardening, separate defect):** close the empty-range
latent at `:1366` by guarding `LDB_PROCESS` on `GR_SAKNR_OI IS INITIAL`.
NOT required for this incident — see §6.

**Rollout:**
1. Apply on D01 (SE38 `YTBAE002`, line 27), activate.
2. Create transport of copies (package `YA`).
3. Unit test: re-run YTR3 from D01 with the same HBKID/HKTID. Expect
   completion < 10 s regardless of WAN path; errors visible in list output.
4. Release to P01.
5. Ask J_DAVANE to re-run. Expect success.
6. Monitor ST22 on P01 for one week — recurrence of TIME_OUT on
   `SAPDBSDF:1983` should be zero.

**Blast radius:** zero behavioral change on the happy path. The only edge
case is a user who relied on the interactive BDC dialog to correct data on
the fly; that user now sees the captured error in the list and re-runs
after fixing. This matches the "end-of-month eventually works" pattern the
user already described.

---

## 6. Latent Defect Preserved (NOT causal for this incident)

`YTBAE002.abap:1366-1370` has a `LOOP AT LR_SAKNR ... APPEND PT_COSEL ...
ENDLOOP` with **no** `IS NOT INITIAL` guard. If `GR_SAKNR_OI` is empty
(SKB1 returns zero OI-eligible rows for the entered HBKID/HKTID), zero
`SD_SAKNR` entries are pushed to the LDB and the SDF scans BSIS with only
`SD_BUKRS + SD_GJAHR` filters (228,242 rows for UNES/2026 live). In dialog
mode this also TIME_OUTs, via a different path.

**Why this is NOT INC-000006906's mechanism:** for J_DAVANE's plausible
input ECO09/MZN01, SKB1 returns `0001194424` with `XOPVW='X'` → `GR_SAKNR_OI`
is NOT empty → the empty-range path does not fire. And the HQ reproduction
confirms network, not scan volume, is the decisive axis.

Recommended fix (optional, can ride the same transport or go separately):

```abap
IF GR_SAKNR_OI IS INITIAL.
  MESSAGE 'No open-item GL accounts found for this house bank / account '
          && 'combination — aborting to avoid full BSIS scan.' TYPE 'I'.
  LEAVE LIST-PROCESSING.
ENDIF.
```

Flagged for separate preventive work.

---

## 7. Class Generalization

### 7.1 Class A — MODE 'E' BDC in network-sensitive loops (PRIMARY, new)

**Pattern:** any custom ABAP program that issues `CALL TRANSACTION ...
USING <bdc> MODE 'E'` inside a `GET <table>` / `LDB_PROCESS` / large-LOOP
path will open SAPGUI on every BDC error. On slow WAN paths (field
offices) the cumulative GUI round-trip time exceeds
`rdisp/max_wprun_time` and the caller's LDB fetch TIME_OUTs with a stack
that blames the LDB, not the CALL TRANSACTION.

**Canonical instance:** `YTBAE002.abap:27` + `:723, :771, :819, :853`.

**Signature (scan over `extracted_code/` Y*/Z* REPOSRC once KU-10 closes):**

```regex
# Match: CONSTANT or VARIABLE holding 'E' used as MODE in CALL TRANSACTION
#        inside a GET/LOOP frame without a network-neutral silent-mode.
CONSTANTS?\s*:\s*\w+\s+TYPE\s+C\s+VALUE\s+'E'
# AND any CALL TRANSACTION ... MODE <that_var>
```

Fix pattern: MODE `'N'` + `MESSAGES INTO <tab>` + post-loop error
reporting via the existing message-capture infrastructure.

**Severity:** HIGH. Silent productivity drain for any field-office user on
any custom program using this pattern; surfaces as a TIME_OUT in caller-land
which obfuscates the real cause.

### 7.2 Class B — House-bank GL not in any YBANK_* set (PREVENTIVE audit, Claim 52)

**Preserved from earlier investigation, orthogonal to this incident.**
233 of 383 distinct T012K HKONTs (60.8%) at UNESCO are NOT in any
`YBANK_*` SETLEAF set. 25 of those have active 2026 BSIS postings
totaling 1,996 rows. Worst case: ICTP/UNI01/EUR `0001040712` (355 rows
in 2026). This matters for Report-Painter programs (ZCASHFODET family)
that resolve bank scope via GS02 sets. **It does NOT apply to YTBAE002**
because YTBAE002 resolves scope via SKB1 (confirmed by grep of the
3,422-line corpus). Kept as a preventive audit class; check script to
be created at `Zagentexecution/quality_checks/ybank_set_coverage_check.py`.

### 7.3 Class C — Empty-range-to-unbounded-LDB-scan (latent, Claim 53)

Demoted from root cause to latent defect. See §6. Valid class signature:
`CALL FUNCTION 'LDB_PROCESS'` preceded within 30 lines by a `RANGE /
APPEND` without `IS NOT INITIAL` guard. Check script to be created at
`Zagentexecution/quality_checks/empty_range_ldb_scan_check.py`.

---

## 8. Validation Checklist

- [x] Main agent owned the 7-step workflow (no subagent delegation).
- [x] User-term → SAP-field translation table (Appendix A of pivot history).
- [x] "How it should work" (§3) written before "Why it fails" (§4).
- [x] Brain read FIRST (brain_state.json + incidents.json) before grep.
- [x] Every behavioral claim cites `file.abap:line`.
- [x] Class generalization SQL/ABAP signatures defined.
- [x] Incidents record updated (`brain_v2/incidents/incidents.json`).
- [x] Fix file written (`Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`).
- [x] User confirmed root cause (HQ reproduction in ~2 s).
- [x] Claim 54 added for MODE 'E' anti-pattern.
- [x] Claim 53 demoted, Claim 52 kept as preventive.
- [x] `rebuild_all.py` executed — brain_state.json refreshed (session #58).
- [x] Tier promoted TIER_2 → TIER_1 after three-path field reproduction (VPN ✓ / Paris ✓ / Mozambique ✗).
- [x] Post-fix error-visibility conclusion documented (§9).

---

## 9. Post-Fix Conclusion — Changing 'E' → 'N' Does NOT Silence Errors

**Concern raised at fix-review time:** does MODE 'N' mean BDC errors
disappear silently and J_DAVANE loses visibility into failures? **No.**
Every error that MODE 'E' would have shown in a pop-up dialog is still
rendered in the list output. The change removes the dialog handshake,
not the error reporting. Fix impact is therefore bounded to network
coupling; error visibility is unchanged.

### 9.1 What MODE 'N' actually does on BDC error

- No SAPGUI dialog opens — no network round-trip, no WP-time consumption.
- The posting rolls back inside SAP's own dialog buffer — no dirty data.
- `SY-SUBRC` returns non-zero on the `CALL TRANSACTION` that failed.
- Every SAP message is captured in `Y_MESSTAB` via the already-present
  `MESSAGES INTO Y_MESSTAB` clause at all four sites
  (`YTBAE002.abap:726`, `:774`, `:822`, `:856`).
- Execution continues with the next BSIS candidate — the loop was
  already error-tolerant.

### 9.2 Where J_DAVANE sees the errors in the list output

The existing output form renders the captured messages inline per
reconciliation group at `YTBAE002.abap:2600-2616`:

```abap
AT END OF Y_RECONCIL.
  WRITE: /1(180) SY-ULINE.
  LOOP AT GT_RECONCIL_MESS
       WHERE Y_RECONCIL = GT_BSIS_RECONCIL-Y_RECONCIL.
    WRITE:/  SY-VLINE,
             W_RECONCIL,
             SY-VLINE,
             GT_RECONCIL_MESS-Y_TRANS,    " TCODE that failed (FB08/F-04/FBRA)
             GT_RECONCIL_MESS-Y_MSGTYPE,  " Severity (E/W/S)
             GT_RECONCIL_MESS-Y_MSGTX,    " Full SAP message text
        180  SY-VLINE.
  ENDLOOP.
  WRITE: /1(180) SY-ULINE.
ENDAT.
```

Each failed item surfaces:

| Field | Source | What the user sees |
|---|---|---|
| `Y_TRANS` | Set at the CALL TRANSACTION site (`:717`, `:762`, `:810`, `:844`) | Which BDC failed — `FB08`, `F-04`, or `FBRA` |
| `Y_MSGTYPE` | Propagated from `Y_MESSTAB-MSGTYP` | `E` = error, `W` = warning, `S` = success |
| `Y_MSGTX` | The full SAP message text exactly as SAP would have shown in the pop-up | e.g. "Posting period 03/2026 is not open", "Document 5100006390 is locked by user XYZ" |

### 9.3 Information parity table — MODE 'E' vs MODE 'N'

| Aspect | MODE 'E' (before fix) | MODE 'N' (after fix) |
|---|---|---|
| Network round-trip on error | YES — pop-up dialog | NO |
| Error message text captured in `Y_MESSTAB` | YES (via `MESSAGES INTO`) | YES (via `MESSAGES INTO`) |
| Error persisted in `GT_RECONCIL_MESS` | YES (via `PROC_RECONCIL_MESS_ADD`) | YES (via `PROC_RECONCIL_MESS_ADD`) |
| Error rendered in list output | YES (at `:2600-2616`) | YES (at `:2600-2616`) |
| Which TCODE failed surfaced | YES | YES |
| Severity shown | YES | YES |
| Full SAP message text shown | YES | YES |
| Interactive "fix-on-screen" chance | YES (rarely used — data errors are not fixable in-dialog) | NO — user fixes at source (OB52, FB02, SU01) and re-runs |
| Runtime on slow WAN with errors | seconds × errors × WAN latency → TIME_OUT | constant, WAN-independent |

**Net delta:** the only functional loss is the rarely-usable "fix-the-error-in-the-pop-up" path. Every item of diagnostic information is preserved in the printed list. The program is already re-runnable: unprocessed items remain in BSIS and are retried on the next run; cleared items disappear from BSIS naturally.

### 9.4 Optional hardening (not required to close incident)

If J_DAVANE wants a top-of-list summary instead of scrolling through
the per-group error blocks, add a pre-loop banner in
`OUTPUT_REPORT_TRANSACTION` that writes:

```
ERRORS DETECTED IN THIS RUN: <count>
Scroll down for per-item details (status column = 'E').
```

counting `GT_RECONCIL_MESS` entries where `Y_MSGTYPE = 'E'`. ~10 lines
of ABAP. Can ride the same transport or go separately. Filed as an
enhancement, not a defect.

### 9.5 Conclusion

The 'E' → 'N' fix is surgical: it eliminates the network-coupled
TIME_OUT without altering any information the user sees. Every error
that would have popped up in a dialog now appears in the reconciliation
list with the same TCODE, severity, and message text. No silencing, no
hidden failures, no behavioral regression on the happy path. The fix is
safe to transport to P01 as-is.

---

## Appendix A — Investigation Pivot History (CP-001 traceability)

This incident pivoted four times before the final root cause. Preserved in
full so the next session can see the reasoning path, not just the answer.

### A.1 Original intake (user said "download failure")

Josina's email named no TCODE, no program, no error. User-term → SAP-field
translation table was:

| User said | SAP field / object (candidates) | Confidence |
|---|---|---|
| "MZN" | `WAERS='MZN'`; UNES T012K rows: BST01/MZM01 (1022424), ECO09/MZN01 (1094424), UBA01/MZN1 (1065424 new) | HIGH |
| "Bank reconciliation" | candidates: FEBAN, FF_5, FBL3N, ZCASHFODET, custom Y_* — not resolvable | LOW |
| "Downloading" | ALV export, spool PDF, MT940 portal, F110 file — not resolvable | MEDIUM |
| "Last month" | March 2026 close | HIGH |
| "FU/MAP" | Maputo field unit; NO Mozambique BUKRS — UNES + PA0001.BTRTL | HIGH |

### A.2 Pivot 1 — user said "not posting, maybe report + dump"

Demoted posting-centered hypotheses. Promoted short-dump-on-report.

### A.3 Pivot 2 — user named `YFI_BANK_RECONCILIATION` as candidate

Gold DB `cts_objects` confirmed the cluster: `YFI_BANK1` TCODE,
`YFI_BANK_RECONCILIATION` program, `YCL_FI_BANK_RECONCILIATION_BL` class,
10 transports by N_MENARD 2023-04 → 2023-06, zero since. Ranked 7 dump
candidates from method names (GET_DELAY ZERODIVIDE, PREPARE_DETAILED_DATA
memory, etc.). **All 7 later falsified by Pivot 4's dump.**

### A.4 Pivot 3 — "pull J_DAVANE execution logs"

Gold DB freshness gap disclosed: `BKPF.CPUDT` stops 2026-03-16,
`FEBKO.EDATE` stops 2026-03-31 — entire incident window 2026-04-13..17
is post-extract. Primary action became live RFC.

### A.5 Pivot 4 — user provided ST22 screenshot

**TCODE was NOT any of the Pivot 2 candidates.** It was `YTR3`, program
`YTBAE002`, error `TIME_OUT` at `SAPDBSDF:1983`. Falsified: the entire
Pivot 2 program cluster, the GET_DELAY ZERODIVIDE hypothesis, the memory
hypothesis, the ALV export hypothesis.

### A.6 Pivot 5 — source extraction falsified YBANK hypothesis

Grep of the 3,422-line YTBAE002 corpus returned zero hits for any
Report-Painter set API → YTBAE002 uses SKB1, not YBANK_* sets → Claim 52
(YBANK coverage gap) is preserved as a real audit finding but demoted
from "causal mechanism for this incident" to "correlational, different
programs".

### A.7 Pivot 6 — empty-range hypothesis falsified for this input

At `:1366-1370` an empty-range-to-unbounded-LDB-scan bug IS present, but
for J_DAVANE's plausible ECO09/MZN01 input SKB1 returns `0001194424` with
`XOPVW='X'` → `GR_SAKNR_OI` is not empty → the bug does not fire. The
unbounded-scan path is not triggered. See §6.

### A.8 Pivot 7 (final) — user reproduced from HQ in ~2 s

Same program, same user inputs, LAN not WAN → no dump, completes in
seconds. This isolates NETWORK as the decisive axis. Combined with the
source trace of `MODE 'E'` + 4 BDC calls to FB08/F-04/FBRA inside the
LDB loop → root cause confirmed at `YTBAE002.abap:27`.

### A.9 Net effect on root cause

| Hypothesis | Outcome | Evidence |
|---|---|---|
| ZCASHFODET / YBANK coverage gap | FALSIFIED (for this incident) | grep of YTBAE002 — zero Report-Painter set calls |
| `YFI_BANK_RECONCILIATION` | FALSIFIED | dump screenshot shows `YTBAE002` |
| GET_DELAY ZERODIVIDE / ALV memory | FALSIFIED | dump is TIME_OUT in LDB, not short-dump in BL class |
| Empty-range unbounded scan at `:1366` | latent but NOT triggered | J_DAVANE's ECO09/MZN01 returns non-empty GR_SAKNR_OI |
| Data volume on BSIS | FALSIFIED | 13 BSIS rows on 0001194424 — trivially small |
| **MODE 'E' BDC + slow WAN** | **CONFIRMED (TIER_2)** | code anchors + HQ reproduction |

---

## Appendix B — Known-Unknowns: status at closure

| ID | Question | Status |
|---|---|---|
| KU-new-1 | What TCODE does Josina run? | **RESOLVED** — YTR3 (dump screenshot) |
| KU-new-2 | Is there a custom Y_* field-office recon program? | **RESOLVED** — YTBAE002 is it |
| KU-new-3 | MT940 feed status for MZ banks? | OPEN (structural gap — no MT940 feed for ECO09 ever; BST01 stopped 2025-04-17). Preserved for business decision. |
| KU-new-4 | Who else runs ZCASHFODET? | OPEN, deferred (not causal for this incident) |
| KU-new-5 | UBA01 replace or augment ECO09? | OPEN, business question |
| KU-new-6 | Source of `YFI_BANK_RECONCILIATION`? | **RESOLVED AS N/A** — falsified program. Source NOT extracted (not worth the cycles). |
| KU-new-7 | ST22 dumps for J_DAVANE 2026-04-13..17? | **RESOLVED** — user provided screenshot directly |
| KU-new-8 | MT940 config for ECO09 MZ (T028B/T028G)? | OPEN (structural, see KU-new-3) |
| KU-new-9 | YTBAE002 source + HKONT-scope mechanism? | **RESOLVED** — 3,422-line source extracted; SKB1-based scope at :1098 |
| KU-new-10 | Gold DB lacks TSTC/TRDIR/REPOSRC Y*/Z* | OPEN (brain extraction improvement) |
| KU-new-11 | J_DAVANE's exact GP_HBKID/GP_HKTID? | **RESOLVED AS UNNEEDED** — HQ reproduction isolates network axis without needing the specific input |
| KU-new-12 | UNESCO Y*/Z* programs using SAPDBSDF in dialog? | OPEN (depends on KU-10; preserved as preventive class check) |
| KU-new-13 | D01 password locked | **RESOLVED** — SNC/SSO fallback used successfully |

### Data-quality items raised

| ID | Finding | Severity | Status |
|---|---|---|---|
| DQ-new-A | T012K BST02/MZM01 WAERS='MZM' deprecated | LOW | OPEN (dormant, no action required) |
| DQ-new-B | Gold DB FEBKO missing rows for ECO09/CIT04/SOG01/UBA01 + 75 others | MEDIUM | OPEN (extraction scoping improvement) |
| DQ-new-C | TSTC not in Gold DB | MEDIUM | OPEN (tied to KU-10) |
| DQ-new-D | TRDIR not in Gold DB | MEDIUM | OPEN (tied to KU-10) |
| DQ-new-E | REPOSRC not in Gold DB | MEDIUM | OPEN (tied to KU-10) |

---

**Document status:** `RESOLVED_FIX_PROPOSED`. Fix file written, user confirmed
reproduction from HQ. Awaits DBS transport + J_DAVANE retest on P01.

**Rebuild trigger:** `python brain_v2/rebuild_all.py` runs at the end of
this consolidation (not mid-investigation).
