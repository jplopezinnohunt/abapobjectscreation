"""
build_zsapfpaym_replay.py
=========================
Generate ZFPAYM_STA, ZFPAYM_GET, ZFPAYM_END from the originals,
commenting out the specific blocks identified in the design and
inserting the replay-mode hooks (BREAK-POINT + ROLLBACK WORK).

Source files in : extracted_code/FI/SAPFPAYM/
Targets in       : extracted_code/FI/SAPFPAYM/ZSAPFPAYM_REPLAY/

NO INVENTING. Each removed block is marked with comment markers.
The original code stays in the file (commented), nothing is deleted —
that way the diff is always inspectable line-by-line vs the SAP std.
"""
import os, re

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "extracted_code", "FI", "SAPFPAYM")
OUT  = os.path.join(BASE, "ZSAPFPAYM_REPLAY")

def read_lines(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read().splitlines()

def write_lines(name, lines):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  wrote {path} ({len(lines)} lines)")

# === ZFPAYM_STA — remove 8 blocks ===
# Block ranges in original FPAYM_STA.abap (1-indexed inclusive)
# Verified against the file we extracted from P01 RFC RPY_PROGRAM_READ.
STA_REMOVE = [
    (17,  28,  "DD prenotif gate (REGUV.X_DD_PRENOTIF check)"),
    (31,  56,  "FIBL_PAYMENT_RUN_MERGE_CHECK gate"),
    (92,  100, "check_reguv_status(sapfpaym_schedule) — REGUV.STATUS gate"),
    # MERGED 103-132 + 136-155 + line 159 ENDIF into ONE balanced block (103-159)
    # so the IF pm_grpno IS INITIAL opener AND its matching ENDIF are commented
    # together — otherwise ENDIF on line 159 is orphan ("ENDIF without IF").
    (103, 159, "Pre-service + popup F4 + matching ENDIF of IF pm_grpno IS INITIAL"),
    (161, 184, "ENQUEUE_EFDFPAYG lock"),
    # The ELSEIF block 205-231: comment the body but PRESERVE line 232 (outer ENDIF
    # which closes the IF sy-subrc NE 0 on line 198 — active code, not part of our removal).
    # The ELSEIF condition itself gets commented; structure stays IF (198) ... ELSEIF (202)
    # ... [commented] ... ENDIF (232). Valid ABAP nesting.
    (205, 231, "*** CRITICAL *** ANZ_ERZ LE ANZ_ERL re-execution gate (body only — keep outer ENDIF on 232)"),
    (378, 378, "COMMIT WORK (deferred — ROLLBACK at END-OF-SELECTION)"),
]

def build_sta():
    src = read_lines("FPAYM_STA.abap")
    out = []
    out.append("************************************************************************")
    out.append("* Include ZFPAYM_STA — REPLAY MODE                                     *")
    out.append("* Origin: FPAYM_STA (P01 RPY_PROGRAM_READ session #072)                *")
    out.append("* 8 blocks commented out — see markers '* >>> ZREPLAY-REMOVED'.        *")
    out.append("*                                                                      *")
    out.append("* Validation chain:                                                    *")
    for s, e, why in STA_REMOVE:
        out.append(f"*   lines {s:>3}-{e:<3}  {why}")
    out.append("************************************************************************")
    out.append("")

    skip_until = 0
    for i, line in enumerate(src, start=1):
        if i <= skip_until:
            out.append("* " + line)  # commented passthrough
            continue
        # check if this line starts a removed block
        opened = False
        for (s, e, why) in STA_REMOVE:
            if i == s:
                out.append(f"*** >>> ZREPLAY-REMOVED ({why}) — lines {s}-{e} of original FPAYM_STA")
                if s == e:
                    out.append("* " + line)
                    out.append(f"*** <<< ZREPLAY-REMOVED")
                    skip_until = 0
                else:
                    out.append("* " + line)
                    skip_until = e
                opened = True
                break
        if opened:
            continue
        # Track end of multi-line removal
        if skip_until and i == skip_until:
            out.append("* " + line)
            out.append(f"*** <<< ZREPLAY-REMOVED")
            skip_until = 0
            continue
        if skip_until and i < skip_until:
            out.append("* " + line)
            continue
        # Normal passthrough
        out.append(line)

    write_lines("ZFPAYM_STA.abap", out)


# === ZFPAYM_GET — remove FI_REF_DOCUMENT_CHECK + insert BREAK-POINT ===
GET_REMOVE = [
    (11, 40, "FI_REF_DOCUMENT_CHECK gate (would REJECT payments failing ref-doc validation)"),
]
# Insertion: add BREAK-POINT block immediately BEFORE original line 71
# (which is "    CALL FUNCTION 'FI_PAYM_MEDIUM_WRITE'")
GET_BREAK_BEFORE = 71

def build_get():
    src = read_lines("FPAYM_GET.abap")
    out = []
    out.append("************************************************************************")
    out.append("* Include ZFPAYM_GET — REPLAY MODE                                     *")
    out.append("* Origin: FPAYM_GET (P01 RPY_PROGRAM_READ session #072)                *")
    out.append("* Changes:                                                             *")
    out.append("*   1. lines 11-40 commented (FI_REF_DOCUMENT_CHECK + REJECT)          *")
    out.append("*   2. BREAK-POINT ID 'YDMEE_REPLAY' inserted before FI_PAYM_MEDIUM_WRITE")
    out.append("************************************************************************")
    out.append("")

    skip_until = 0
    for i, line in enumerate(src, start=1):
        if skip_until and i <= skip_until:
            out.append("* " + line)
            if i == skip_until:
                out.append("*** <<< ZREPLAY-REMOVED")
                skip_until = 0
            continue
        for (s, e, why) in GET_REMOVE:
            if i == s:
                out.append(f"*** >>> ZREPLAY-REMOVED ({why}) — lines {s}-{e}")
                out.append("* " + line)
                skip_until = e
                break
        else:
            if i == GET_BREAK_BEFORE:
                # insert BREAK-POINT block BEFORE the line
                out.append("")
                out.append("*** ★★★ DEBUG ENTRY POINT — antes de invocar el motor DMEE ★★★")
                out.append("*** Estructuras visibles aquí (todas INTTAB, populadas por LDB FPMF):")
                out.append("***   fpayh    144 fields, header del pago actual")
                out.append("***   gt_fpayp internal table de items del header")
                out.append("***   par_form DMEE TREE_ID activo (e.g. /SEPA_CT_UNES)")
                out.append("*** F5 → step into FI_PAYM_MEDIUM_WRITE → motor DMEE")
                out.append("*** Para break en nodo X del árbol DMEE: SE24 USER-BP en")
                out.append("***   YCL_IDFI_CGI_DMEE_FALLBACK_CM001->GET_CREDIT")
                out.append("***   FI_PAYMEDIUM_DMEE_CGI_05  (Event 05 callback SAP std)")
                out.append("    BREAK-POINT.   \"plain BP — no checkpoint group needed")
                out.append("")
                out.append(line)
            else:
                out.append(line)

    write_lines("ZFPAYM_GET.abap", out)


# === ZFPAYM_END — append ROLLBACK WORK ===
def build_end():
    src = read_lines("FPAYM_END.abap")
    out = []
    out.append("************************************************************************")
    out.append("* Include ZFPAYM_END — REPLAY MODE                                     *")
    out.append("* Origin: FPAYM_END (P01 RPY_PROGRAM_READ session #072)                *")
    out.append("* Change: ROLLBACK WORK appended at the very end so DFPAYG.ANZ_ERL,    *")
    out.append("*         REGUV.STATUS, REGUH.XEB1 etc. updates done by                *")
    out.append("*         FI_PAYM_MEDIUM_OPEN/WRITE/CLOSE are DISCARDED. The XML file  *")
    out.append("*         is already on disk (file I/O is non-transactional).          *")
    out.append("************************************************************************")
    out.append("")
    out.extend(src)
    out.append("")
    out.append("*** ★ ROLLBACK to keep run repeatable — no DB updates committed ★")
    out.append("*** This is what makes ZSAPFPAYM_REPLAY idempotent. The XML output   ")
    out.append("*** has already been written to PAR_FILE / TemSe by FI_PAYM_MEDIUM_  ")
    out.append("*** WRITE → CLOSE; those are non-transactional file operations.      ")
    out.append("*** Everything else (counter increment, status flags) is rolled back.")
    out.append("    ROLLBACK WORK.")

    write_lines("ZFPAYM_END.abap", out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_sta()
    build_get()
    build_end()
    print("\nDone. Files in:", OUT)
