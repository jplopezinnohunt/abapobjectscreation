  METHOD if_ex_hrasr_pr_start_restrict~check_process_is_executable.

    DATA: lv_pernr           TYPE pernr_d,
          lv_molga           TYPE molga,
          lv_can_be_laucnhed TYPE boolean,
          lv_msg_error_code  TYPE SYMSGNO,
          lr_process         TYPE RANGE OF asr_process,
          ll_process         LIKE LINE OF lr_process,
          ls_msg             TYPE symsg.

*   Check process is one to filter
    ll_process-sign = 'I'.
    ll_process-option = 'EQ'.
    ll_process-low = c_process_change_child.
    APPEND ll_process TO lr_process.
    ll_process-low = c_process_change_brother.
    APPEND ll_process TO lr_process.
    ll_process-low = c_process_change_sister.
    APPEND ll_process TO lr_process.

    ll_process-low = c_process_review_dependents.
    APPEND ll_process TO lr_process.
    ll_process-low = c_process_dependents_survey.
    APPEND ll_process TO lr_process.
    ll_process-low = c_process_second_dep_survey.
    APPEND ll_process TO lr_process.

    CHECK process IN lr_process.

*   Check if treated employee is Unesco (molga UN)
    MOVE object_key TO lv_pernr.
    get_employee_molga( EXPORTING iv_pernr = lv_pernr
                        IMPORTING ov_molga = lv_molga ).
    IF  lv_molga <> c_molga_un.
      ls_msg-msgid = 'ZHRFIORI'.
      ls_msg-msgno = '027'.
      ls_msg-msgty = 'E'.

      message_handler->add_message( EXPORTING message = ls_msg ).
      is_process_executable = abap_false.
      RETURN.
    ENDIF.

*   Check if treated employee has child/brother/sister
    check_chge_process_be_launched( EXPORTING iv_pernr = lv_pernr
                                              iv_process = process
                                    IMPORTING ov_can_be_laucnhed = lv_can_be_laucnhed
                                              ov_msg_error_code = lv_msg_error_code ).
    IF lv_can_be_laucnhed = abap_false.
      CASE process.
        WHEN c_process_change_child.
          ls_msg-msgid = 'ZHRFIORI'.
          ls_msg-msgno = '028'.
          ls_msg-msgty = 'E'.
        WHEN c_process_change_brother.
          ls_msg-msgid = 'ZHRFIORI'.
          ls_msg-msgno = '029'.
          ls_msg-msgty = 'E'.
        WHEN c_process_change_sister.
          ls_msg-msgid = 'ZHRFIORI'.
          ls_msg-msgno = '030'.
          ls_msg-msgty = 'E'.
        WHEN c_process_review_dependents OR c_process_dependents_survey
          OR c_process_second_dep_survey.
          ls_msg-msgid = 'ZHRFIORI'.
*          ls_msg-msgno = '041'.
          ls_msg-msgno = lv_msg_error_code.
          ls_msg-msgty = 'E'.
      ENDCASE.

      message_handler->add_message( EXPORTING message = ls_msg ).
      is_process_executable = abap_false.
    ENDIF.

  ENDMETHOD.
