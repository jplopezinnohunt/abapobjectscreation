  METHOD check_dsa_eligibility.

    CONSTANTS: lc_30_days          TYPE anzhl VALUE 30,
               lc_12_months        TYPE cmp_nomns VALUE 12,
               lc_30_days_validity TYPE cmp_nodys VALUE 30,
               lc_datetype_u6      TYPE datar VALUE 'U6',
               lc_wt_1506          TYPE subty VALUE '1506',
               lc_wt_1521          TYPE subty VALUE '1521'.

    DATA: lv_nb_days     TYPE cmp_nodys,
          lv_date_it0041 TYPE dardt,
          ls_p0015       TYPE p0015,
          lt_p0015       TYPE STANDARD TABLE OF p0015,
          lo_msg_handler TYPE REF TO if_hrpa_message_handler.

*   Initialize return value
    ov_is_eligible = abap_false.

*   Check wage types (infotype 0015)
    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = iv_pernr
        infty     = '0015'
*       BEGDA     = '18000101'
*       ENDDA     = '99991231'
      TABLES
        infty_tab = lt_p0015.

    CHECK lt_p0015[] IS NOT INITIAL.

*   Check if wage type 1506 or 1521 exist with 30 days (field ANZHL)
    SORT lt_p0015 BY endda DESCENDING.
    LOOP AT lt_p0015 INTO ls_p0015
      WHERE ( subty = lc_wt_1506 OR subty = lc_wt_1521 )
        AND anzhl = lc_30_days.
      EXIT.
    ENDLOOP.

*   Check if search gave results
    CHECK sy-subrc = 0.

*   Treatment depending wage type
    CASE ls_p0015-subty.
      WHEN lc_wt_1506.
*       Check if wage type was recorded at least 30 days before RS request
        CALL FUNCTION 'HRCM_TIME_PERIOD_CALCULATE'
          EXPORTING
            begda = ls_p0015-aedtm
            endda = sy-datum
          IMPORTING
*           NOYRS =
*           NOMNS =
            nodys = lv_nb_days.

        CHECK lv_nb_days >= lc_30_days_validity.

*       Check if date U6 in infotype 0041 is equal to start date of wage type
        CALL FUNCTION 'HR_ECM_GET_DATETYP_FROM_IT0041'
          EXPORTING
            pernr           = iv_pernr
            keydt           = ls_p0015-begda
            datar           = lc_datetype_u6
            message_handler = lo_msg_handler
          IMPORTING
            date            = lv_date_it0041.

*       Check date U6.
        IF lv_date_it0041 IS  NOT INITIAL AND lv_date_it0041 = ls_p0015-begda.
          ov_is_eligible = abap_true.
        ENDIF.

      WHEN lc_wt_1521.
*       Check if date U6 in infotype 0041 is inferior to 12 months
        CALL FUNCTION 'HR_ECM_GET_DATETYP_FROM_IT0041'
          EXPORTING
            pernr           = iv_pernr
            keydt           = sy-datum
            datar           = lc_datetype_u6
            message_handler = lo_msg_handler
          IMPORTING
            date            = lv_date_it0041.

*       Check date U6.
        IF lv_date_it0041 IS  NOT INITIAL AND lv_date_it0041 < lc_12_months.
          ov_is_eligible = abap_true.
        ENDIF.

    ENDCASE.

  ENDMETHOD.
