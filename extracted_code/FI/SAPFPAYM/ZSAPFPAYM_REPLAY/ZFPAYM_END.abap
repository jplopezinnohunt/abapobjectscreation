************************************************************************
* Include ZFPAYM_END — REPLAY MODE                                     *
* Origin: FPAYM_END (P01 RPY_PROGRAM_READ session #072)                *
* Change: ROLLBACK WORK appended at the very end so DFPAYG.ANZ_ERL,    *
*         REGUV.STATUS, REGUH.XEB1 etc. updates done by                *
*         FI_PAYM_MEDIUM_OPEN/WRITE/CLOSE are DISCARDED. The XML file  *
*         is already on disk (file I/O is non-transactional).          *
************************************************************************

************************************************************************
* Include FPAYM_END                                                    *
* End Of Selection                                                     *
************************************************************************

END-OF-SELECTION.

* begin 2573070
  if sy-batch = space.
    DATA gd_stop_creation.
    PERFORM check_message_stop_creation CHANGING gd_stop_creation.
  endif.

*  IF gc_xselect EQ 'X'.
  IF gc_xselect EQ 'X' AND gd_stop_creation = space.
* end 2573070

*   close payment medium
    CALL FUNCTION 'FI_PAYM_MEDIUM_CLOSE'
         EXPORTING
              i_xlast = 'X'.

*   no flag on the selection screen was set to have ANY output
    IF par_xpy1 IS INITIAL AND par_xpy3 IS INITIAL
                           AND par_xpy5 IS INITIAL.
      MESSAGE s203.
    ENDIF.

  ELSE.

*   Error log (if filled)
    CALL FUNCTION 'FI_PAYM_MESSAGE_PRINT'
         EXPORTING
              i_error_params = gs_prie
              i_error_arcpar = gs_arce
              i_error_print  = par_xerr.
    CALL FUNCTION 'FI_PAYM_OUTPUT_SHOW_TREE'.

    if NOT ( sy-batch is initial and gc_too_many_files = 'X' ).
      MESSAGE s159 WITH par_form pm_grpno space space.
    endif.
  ENDIF.

*** ★ DISPLAY GENERATED XML ON SCREEN ★
*** Read the file SAPFPAYM just wrote and dump it as the report list,
*** so the user sees the DMEE output without leaving SE38.
    DATA: lt_xml TYPE STANDARD TABLE OF string,
          lv_xml_line TYPE string,
          lv_path     TYPE string.
    lv_path = par_file.
    IF NOT lv_path IS INITIAL.
      OPEN DATASET lv_path FOR INPUT IN TEXT MODE
                                    ENCODING DEFAULT.
      IF sy-subrc = 0.
        DO.
          READ DATASET lv_path INTO lv_xml_line.
          IF sy-subrc <> 0. EXIT. ENDIF.
          APPEND lv_xml_line TO lt_xml.
        ENDDO.
        CLOSE DATASET lv_path.
        WRITE: / '======================================'.
        WRITE: / '== Generated DMEE output =============='.
        WRITE: / '== File:', lv_path.
        WRITE: / '== Lines:', LINES( lt_xml ).
        WRITE: / '======================================'.
        LOOP AT lt_xml INTO lv_xml_line.
          WRITE: / lv_xml_line.
        ENDLOOP.
      ELSE.
        WRITE: / 'Could not read file:', lv_path,
               'sy-subrc=', sy-subrc.
      ENDIF.
    ELSE.
      WRITE: / 'PAR_FILE empty — output went to TemSe.',
             'Use tx FDTA or SP01 to view.'.
    ENDIF.

*** ★ ROLLBACK to keep run repeatable — no DB updates committed ★
*** This is what makes ZSAPFPAYM_REPLAY idempotent. The XML output
*** has already been written to PAR_FILE / TemSe by FI_PAYM_MEDIUM_
*** WRITE → CLOSE; those are non-transactional file operations.
*** Everything else (counter increment, status flags) is rolled back.
    ROLLBACK WORK.
