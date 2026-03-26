  METHOD check_doc_link_visibility.

    DATA: ls_p0001 TYPE p0001,
          lt_p0001 TYPE STANDARD TABLE OF p0001.

*   Initial value for visibility
    ov_to_be_displayed = abap_true.

*Rules (based on the value of the reason for action ZE_HRFIORI_REASON)
*
* Leave whitout pay (action_type = 00):
*   If Study leave (reason for action 00, 06 and 03) => id_link = 07
*   If Childcare leave (reason for action 33, 34 and 35) => id_link = 04
*   If Other special leave (reason for action 02, 08 and 05) => id_link = 05
*
* Separation (action_type = 01):
*   If reason for action is Retirement (29) or Early retirement (30) => id_link = 07
*   Only for International Staff (EEG 1) => id_link = 11
*   Only for Local Staff (EEG 2) => id_link = 12


    IF iv_action_type EQ '00'."Action type = Leave Without pay
      CASE iv_id_link.
        WHEN 'LWP_LETTER' OR 'HR_PROCESS'. "If Study leave
          IF NOT ( iv_reason = '00' OR iv_reason = '03' OR iv_reason = '06' ).
            ov_to_be_displayed = abap_false.
          ENDIF.
        WHEN 'HR_MANUAL2' OR 'HR_PROCES2'. "If Childcare leave
          IF NOT ( iv_reason = '33' OR iv_reason = '34' OR iv_reason = '35' ).
            ov_to_be_displayed = abap_false.
          ENDIF.
        WHEN 'HR_MANUAL3' OR 'HR_PROCES3' OR 'HR_PROCES4'. "If Other special leave
          IF NOT ( iv_reason = '02' OR iv_reason = '05' OR iv_reason = '08' ).
            ov_to_be_displayed = abap_false.
          ENDIF.

        WHEN OTHERS.
      ENDCASE.

    ELSEIF iv_action_type EQ '01'. "Action type = Separation
      CALL FUNCTION 'HR_READ_INFOTYPE'
          EXPORTING
            pernr     = iv_pernr
            infty     = '0001'
            begda     = sy-datum
            endda     = sy-datum
          TABLES
            infty_tab = lt_p0001.
      READ TABLE lt_p0001 INTO ls_p0001 INDEX 1.

      CASE iv_id_link.

        WHEN 'REP_TRAV' OR 'OBRD_TIPS1'.
*         Only display this doc link type for interntional staff
          IF NOT ( ls_p0001-persg = '1' ).
            ov_to_be_displayed = abap_false.
          ENDIF.

        WHEN 'AFUS'.
*         Only display this document for retirement or early retirement
          IF NOT ( iv_reason = '29' OR iv_reason = '30' ).
            ov_to_be_displayed = abap_false.
          ENDIF.

        WHEN 'OBRD_TIPS2'.
*         Only display this doc link type for local staff
          IF NOT ( ls_p0001-persg = '2' ).
            ov_to_be_displayed = abap_false.
          ENDIF.

        WHEN OTHERS.
      ENDCASE.
    ENDIF.

  ENDMETHOD.
