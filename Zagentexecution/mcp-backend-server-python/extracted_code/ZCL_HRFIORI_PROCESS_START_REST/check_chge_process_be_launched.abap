  METHOD check_chge_process_be_launched.

    DATA: lf_review_exists    TYPE boolean,
          lf_can_be_requested TYPE boolean,
          ls_pa0021           TYPE pa0021,
          lo_pf_common        TYPE REF TO zcl_hrfiori_pf_common.

    ov_can_be_laucnhed = abap_true.

    CASE iv_process.
      WHEN c_process_change_child.
        SELECT SINGLE * INTO ls_pa0021
          FROM pa0021
            WHERE pernr = iv_pernr
              AND subty = '14'
              AND endda >= sy-datum
              AND begda <= sy-datum.
        IF sy-subrc <> 0.
          ov_can_be_laucnhed = abap_false.
        ENDIF.

      WHEN c_process_change_brother.
        SELECT SINGLE * INTO ls_pa0021
          FROM pa0021
            WHERE pernr = iv_pernr
              AND subty = '6'
              AND endda >= sy-datum
              AND begda <= sy-datum.
        IF sy-subrc <> 0.
          ov_can_be_laucnhed = abap_false.
        ENDIF.

      WHEN c_process_change_sister.
        SELECT SINGLE * INTO ls_pa0021
          FROM pa0021
            WHERE pernr = iv_pernr
              AND subty = '7'
              AND endda >= sy-datum
              AND begda <= sy-datum.
        IF sy-subrc <> 0.
          ov_can_be_laucnhed = abap_false.
        ENDIF.

*      WHEN c_process_review_dependents OR c_process_dependents_survey
*        OR c_process_second_dep_survey.
*        CREATE OBJECT lo_pf_common.
*
*        lo_pf_common->check_deadline_for_dep_review( EXPORTING iv_user_id = sy-uname
*                                                     IMPORTING ov_can_be_requested = lf_can_be_requested ).
*        IF lf_can_be_requested = abap_false.
*          ov_msg_error_code = '042'.
*          ov_can_be_laucnhed = abap_false.
*        ENDIF.
*
*        lo_pf_common->check_yearly_dep_review( EXPORTING iv_pernr = iv_pernr
*                                                         iv_process = iv_process
*                                               IMPORTING ov_review_exists = lf_review_exists ).
*        IF lf_review_exists =  abap_true.
*          ov_msg_error_code = '041'.
*          ov_can_be_laucnhed = abap_false.
*        ENDIF.

    ENDCASE.

  ENDMETHOD.
