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