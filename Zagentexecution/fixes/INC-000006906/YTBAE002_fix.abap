*&---------------------------------------------------------------------*
*& INC-000006906 — YTBAE002 / YTR3 fix
*& Root cause : GC_MOD = 'E' causes CALL TRANSACTION FB08/F-04/FBRA to
*&              open SAPGUI dialog on any BDC error. On a slow WAN path
*&              (Maputo field office) the cumulative GUI roundtrip time
*&              exceeds rdisp/max_wprun_time -> TIME_OUT dump at
*&              SAPDBSDF PUT_BSIS line 1983.
*& Evidence  : Dump captured 2026-04-20 13:51:49 user J_DAVANE client 350
*&             Same program runs in ~2 seconds from HQ (user reproduced).
*& Mechanism : YTBAE002.abap:27  GC_MOD = 'E' ("Only display if error")
*&             YTBAE002.abap:723,771,819,853  CALL TRANSACTION ... MODE GC_MOD
*& Fix tier  : FIX_A  one-char change (minimum blast radius)
*&             FIX_B  defensive — errors captured, no GUI path possible
*&---------------------------------------------------------------------*

*----------------------------------------------------------------------*
*  FIX_A  (recommended — minimal, reversible)
*----------------------------------------------------------------------*
* File     : YTBAE002 (executable REPS, package YA)
* Line     : 27
* Change   : 'E' -> 'N'
* Before:
*     CONSTANTS: GC_MOD     TYPE C VALUE 'E',
* After:
*     CONSTANTS: GC_MOD     TYPE C VALUE 'N',
*
* Effect:
*   - CALL TRANSACTION now runs silently. Any BDC error is captured in
*     Y_MESSTAB (already collected via MESSAGES INTO Y_MESSTAB at each
*     call site). No SAPGUI dialog opens. No network roundtrip during
*     error. Program completes server-side with the same message table
*     the user already persists via PROC_RECONCIL_MESS_ADD (lines 754,
*     795, 840, 874) into the reconciliation log.
*   - User still sees all errors in the reconciliation result list.
*   - Execution time becomes network-independent.
*
* Risk:
*   - None for the happy path (no behaviour change when BDC succeeds).
*   - Edge case: a user who relied on the interactive error screen to
*     correct a BDC on the fly loses that path. Mitigation: errors are
*     already in Y_MESSTAB + GT_RECONCIL_MESS; user re-runs after fixing
*     the data. This matches the "end-of-month eventually works" pattern
*     J_DAVANE already experiences.
*
* Applies in   : D01 (dev) — create transport of copies
* Transport of : YA package — correction request, cross D01 -> P01
* Tested by    : re-run YTR3 with the same HBKID/HKTID that produced the
*                dump; expect completion in < 10s regardless of WAN path.

*----------------------------------------------------------------------*
*  FIX_B  (stronger — also logs the defensive intent)
*----------------------------------------------------------------------*
* Same change as FIX_A plus an explicit comment so a future dev cannot
* silently flip it back to 'E':
*
*     CONSTANTS:
*       " INC-000006906 (2026-04-20): MUST stay 'N'. MODE 'E' opens
*       " SAPGUI on BDC error; on slow WAN (Maputo/field offices) the
*       " cumulative GUI roundtrips exceed rdisp/max_wprun_time and
*       " produce TIME_OUT at SAPDBSDF PUT_BSIS. Errors are captured in
*       " Y_MESSTAB + GT_RECONCIL_MESS and surfaced in the list output.
*       GC_MOD     TYPE C VALUE 'N',

*----------------------------------------------------------------------*
*  FIX_C  (optional hardening — not required to close incident)
*----------------------------------------------------------------------*
* Additionally close the latent defect at YTBAE002.abap:1366-1370
* (empty HKONT range -> unbounded LDB scan). Insert guard before the
* LDB_PROCESS call at ~:1509:
*
*     IF GR_SAKNR_OI IS INITIAL.
*       MESSAGE 'No open-item GL accounts found for this house bank '
*               && 'account combination — aborting to avoid full BSIS '
*               && 'scan.' TYPE 'I'.
*       LEAVE LIST-PROCESSING.
*     ENDIF.
*
* This is a SEPARATE defect (latent, never triggered J_DAVANE's dump).
* Can ride the same transport or go separately.

*----------------------------------------------------------------------*
*  Rollout
*----------------------------------------------------------------------*
* 1. Log on D01 (172.16.4.66:00) as developer, SE38 YTBAE002.
* 2. Apply FIX_A (or FIX_B) at line 27. Activate.
* 3. Unit test: run YTR3 with the HBKID/HKTID that dumped.
*    Expected: list completes; any BDC errors visible in reconciliation
*    log without opening FB08/F-04/FBRA screens.
* 4. Release transport TR, import to P01.
* 5. Ask J_DAVANE to re-run YTR3 on the failing combination. Expect
*    completion regardless of WAN speed.
* 6. Monitor ST22 on P01 for one week for any recurrence of TIME_OUT
*    in SAPDBSDF PUT_BSIS (should drop to zero).
