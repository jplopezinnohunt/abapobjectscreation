************************************************************************
* Include FPAYM_END                                                    *
* End Of Selection                                                     *
************************************************************************

END-OF-SELECTION.

* begin 2573070
  IF SY-BATCH = SPACE.
    DATA GD_STOP_CREATION.
    PERFORM CHECK_MESSAGE_STOP_CREATION CHANGING GD_STOP_CREATION.
  ENDIF.

*  IF gc_xselect EQ 'X'.
  IF GC_XSELECT EQ 'X' AND GD_STOP_CREATION = SPACE.
* end 2573070

*   close payment medium
    CALL FUNCTION 'FI_PAYM_MEDIUM_CLOSE'
         EXPORTING
              I_XLAST = 'X'.

*   no flag on the selection screen was set to have ANY output
    IF PAR_XPY1 IS INITIAL AND PAR_XPY3 IS INITIAL
                           AND PAR_XPY5 IS INITIAL.
      MESSAGE S203.
    ENDIF.

  ELSE.

*   Error log (if filled)
    CALL FUNCTION 'FI_PAYM_MESSAGE_PRINT'
         EXPORTING
              I_ERROR_PARAMS = GS_PRIE
              I_ERROR_ARCPAR = GS_ARCE
              I_ERROR_PRINT  = PAR_XERR.
    CALL FUNCTION 'FI_PAYM_OUTPUT_SHOW_TREE'.

    IF NOT ( SY-BATCH IS INITIAL AND GC_TOO_MANY_FILES = 'X' ).
      MESSAGE S159 WITH PAR_FORM PM_GRPNO SPACE SPACE.
    ENDIF.
  ENDIF.