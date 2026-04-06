METHOD remove_plan_from_selection.

  DATA: lv_pernr            TYPE pernr_d,
        ls_offer            TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
        ls_selection        TYPE rpben_selection_display,
        ls_cons_error       TYPE rpbenerr_ess_det_consistency,
        ls_error            TYPE rpbenerr,
        lt_cons_error       TYPE hrben00err_ess_det_consistency,
        lt_error_table      TYPE hrben00err_ess,
        lt_error_final      TYPE hrben00err_ess,
        lo_ex               TYPE REF TO cx_root.

  TRY .

      LOOP AT it_offer INTO ls_offer.

        MOVE-CORRESPONDING ls_offer TO ls_selection.

        CALL FUNCTION 'HR_BEN_ESS_RFC_REMOVE_PLAN'
          EXPORTING
            selected_selection_display = ls_selection
          IMPORTING
            check_errors               = lt_cons_error
            error_table                = lt_error_table.

        LOOP AT lt_cons_error INTO ls_cons_error.
          MOVE-CORRESPONDING ls_cons_error TO ls_error.
          APPEND ls_error TO lt_error_final.
          CLEAR ls_error.
        ENDLOOP.

        APPEND LINES OF lt_error_table TO lt_error_final.

        CLEAR :ls_selection, lt_error_table, lt_cons_error.

      ENDLOOP.

    CATCH cx_root INTO lo_ex.

  ENDTRY.

  IF lt_error_final IS NOT INITIAL.
    raise_exceptions( it_messages = lt_error_final ).
  ENDIF.


ENDMETHOD.
