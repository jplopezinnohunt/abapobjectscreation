  METHOD PREPARE_DATA.

    DATA LV_END_FISTL TYPE BOOLEAN.
    DATA LS_RESULT TYPE YSFM_DATA_REP_2.
    DATA LS_RESULT_HEAD TYPE YSFM_DATA_REP_2.
    DATA LT_WFMBDT TYPE TTY_WFMBDT.
    DATA LT_WFMBDT_OTH TYPE TTY_WFMBDT.
    DATA LT_WFMBDT_FUND TYPE TTY_WFMBDT.
    DATA LR_FISTL TYPE TTY_FISTL.
    DATA LV_RATE_TODAY TYPE UKURS_CURR.

    LOOP AT MT_FMBDT INTO DATA(LS_FMBDT).

      AT NEW FIKRS.
        CLEAR: MV_WAERS, MV_CONVERT, LV_RATE_TODAY.
        READ TABLE MO_CONV_RATE->MT_CONV INTO DATA(LS_CONV) WITH KEY FIKRS = LS_FMBDT-FIKRS.
        IF SY-SUBRC = 0.
          MV_WAERS = LS_CONV-WAERS.
          MV_CONVERT = ABAP_TRUE.
          "Get rate at sy-datum
*          READ TABLE mt_conv_data INTO DATA(ls_conv_data) WITH KEY waers = mv_waers
*                                                                   gjahr = '0000'
*                                                                   perio = '000'.
          LV_RATE_TODAY = MO_CONV_RATE->GET_RATE( IV_WAERS = MV_WAERS
                                                  IV_GJAHR = '0000'
                                                  IV_PERIO = '000' ).
        ENDIF.
      ENDAT.

      AT NEW FINCODE.
        CLEAR: MS_FIPEX_ALL, LS_RESULT_HEAD, LT_WFMBDT_FUND, LR_FISTL, MV_NO_PROJECT.
        LS_RESULT_HEAD-FIKRS = LS_FMBDT-FIKRS.
        LS_RESULT_HEAD-FINCODE = LS_FMBDT-FINCODE.
        ME->SET_MASTER_DATA( CHANGING CS_RESULT = LS_RESULT_HEAD ).
      ENDAT.

      AT NEW FISTL.
        CLEAR: LT_WFMBDT, LT_WFMBDT_OTH, LS_RESULT.
        MV_EXCL80 = MP_EXCL80.
        LS_RESULT = LS_RESULT_HEAD.
        LS_RESULT-FISTL = LS_FMBDT-FISTL.
      ENDAT.

      "Check project has been selected
      CHECK MV_NO_PROJECT = ABAP_FALSE.

      "Check fund / fund center / commitment item
      IF ME->IS_COMMITMENT_ITEM_IN_AVC( IV_FIKRS = LS_FMBDT-FIKRS
                                        IV_FINCODE = LS_FMBDT-FINCODE
                                        IV_FISTL = LS_FMBDT-FISTL
                                        IV_FIPEX = LS_FMBDT-FIPEX ) = ABAP_TRUE.
        ME->SET_MAIN_TO_LIGHT_TABLE( EXPORTING IS_FMBDT = LS_FMBDT
                                               IV_RATE = LV_RATE_TODAY
                                     CHANGING CT_WFMBDT = LT_WFMBDT ).
      ENDIF.

      AT END OF FISTL.
        DELETE LT_WFMBDT WHERE HAMOUNT IS INITIAL AND FIPEX <> 'REVENUE'.
        IF LT_WFMBDT IS NOT INITIAL.
          "Get amounts out of selection period for ALLOC_TOTAL
          LOOP AT MT_FMBDT_OTH INTO DATA(LS_FMBDT_OTH) WHERE FIKRS = LS_FMBDT-FIKRS
                                                       AND   FINCODE = LS_FMBDT-FINCODE
                                                       AND   FISTL = LS_FMBDT-FISTL.
            IF ME->IS_COMMITMENT_ITEM_IN_AVC( IV_FIKRS = LS_FMBDT_OTH-FIKRS
                                              IV_FINCODE = LS_FMBDT_OTH-FINCODE
                                              IV_FISTL = LS_FMBDT_OTH-FISTL
                                              IV_FIPEX = LS_FMBDT_OTH-FIPEX ) = ABAP_TRUE.
              ME->SET_MAIN_TO_LIGHT_TABLE( EXPORTING IS_FMBDT = LS_FMBDT_OTH
                                                     IV_RATE = LV_RATE_TODAY
                                           CHANGING CT_WFMBDT = LT_WFMBDT_OTH ).
            ENDIF.
          ENDLOOP.
          DELETE LT_WFMBDT_OTH WHERE HAMOUNT IS INITIAL AND FIPEX <> 'REVENUE'.
          "Set amounts in result table
          ME->SET_AMOUNTS( IS_RESULT = LS_RESULT
                           IT_WFMBDT = LT_WFMBDT
                           IT_WFMBDT_OTH = LT_WFMBDT_OTH ).
          APPEND VALUE #( SIGN = 'I' OPTION = 'EQ' LOW = LS_FMBDT-FISTL ) TO LR_FISTL.
          APPEND LINES OF LT_WFMBDT TO LT_WFMBDT_FUND.
        ENDIF.
      ENDAT.

      AT END OF FINCODE.
        LS_RESULT = LS_RESULT_HEAD.
        MV_EXCL80 = ABAP_FALSE.
        ME->SET_OTHER_FUND_CENTER( IS_RESULT = LS_RESULT
                                   IR_FISTL = LR_FISTL
                                   IT_WFMBDT = LT_WFMBDT_FUND ).
        ME->SET_PROJECT_AMOUNTS( IV_FIKRS = LS_FMBDT-FIKRS
                                 IV_FINCODE = LS_FMBDT-FINCODE ).
      ENDAT.

    ENDLOOP.

  ENDMETHOD.