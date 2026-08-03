ENHANCEMENT 2  .
* During FM document creation changing the Local Amount
* From any source PO, Finance, etc
    DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
    DATA YYLV_AMOUNT TYPE FMIFIIT-FKBTR.
    DATA YYLV_SUBRC TYPE SY-SUBRC.
    DATA YYLS_AVC_FUND TYPE YCL_FM_BR_EXCHANGE_RATE_BL=>TY_AVC_FUND.
    DATA YYLO_BR_PAYROLL_POSTING_BL TYPE REF TO YCL_FM_BR_PAYROLL_POSTING_BL.
    DATA YYLS_ACCOUNT_GL TYPE BAPIACGL04.
    DATA YYLS_ACCOUNT_AMOUNT TYPE BAPIACCR04.

    YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
    YYLO_BR_PAYROLL_POSTING_BL = YCL_FM_BR_PAYROLL_POSTING_BL=>GET_INSTANCE( ).

    IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.

*START of BR  nonStaff Logic ----->START
      LOOP AT U_T_FMIFIHD INTO DATA(LS_FMIFIHD).

        LOOP AT U_T_FMIFIIT ASSIGNING FIELD-SYMBOL(<LS_FMIFIIT>) WHERE FMBELNR = LS_FMIFIHD-FMBELNR
                                                                 AND   FIKRS   = LS_FMIFIHD-FIKRS.
          CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_RLDNR = <LS_FMIFIIT>-RLDNR
                                                         IV_FIKRS = <LS_FMIFIIT>-FIKRS
                                                         IV_GSBER = <LS_FMIFIIT>-BUS_AREA
                                                         IV_WAERS = <LS_FMIFIIT>-TWAER
                                                         IV_FIPEX = <LS_FMIFIIT>-FIPEX
                                                         IV_VRGNG = <LS_FMIFIIT>-VRGNG
                                                         IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = <LS_FMIFIIT>-FIKRS IV_FINCODE = <LS_FMIFIIT>-FONDS ) ) = ABAP_TRUE.
          "First save data before conversion in table YTFM_BR_FMIFIIT
          IF U_FLG_UPDATE  = CON_OFF OR G_FLG_REBUILD = CON_ON.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT'
              EXPORTING
                IS_FMIFIIT   = <LS_FMIFIIT>
              EXCEPTIONS
                ERROR_UPDATE = 1
                OTHERS       = 2.
          ELSE.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT' IN UPDATE TASK
              EXPORTING
                IS_FMIFIIT   = <LS_FMIFIIT>
              EXCEPTIONS
                ERROR_UPDATE = 1
                OTHERS       = 2.
          ENDIF.

          "Do conversion in constant dollar
          YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = LS_FMIFIHD-BUDAT
                                                                IV_FOREIGN_AMOUNT = <LS_FMIFIIT>-TRBTR
                                                                IV_FOREIGN_CURRENCY = <LS_FMIFIIT>-TWAER
                                                                IV_LOCAL_CURRENCY = 'USD'
                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                EV_SUBRC = YYLV_SUBRC ).
          CHECK YYLV_SUBRC = 0.
          <LS_FMIFIIT>-FKBTR = YYLV_AMOUNT.
          "Store Fund to recalculate AVC
          MOVE-CORRESPONDING <LS_FMIFIIT> TO YYLS_AVC_FUND.
          INSERT YYLS_AVC_FUND INTO TABLE YYLO_BR_EXCHANGE_RATE->MT_AVC_FUND.
        ENDLOOP.
      ENDLOOP.
      IF YYLO_BR_EXCHANGE_RATE->MT_AVC_FUND IS NOT INITIAL.
        SET HANDLER YYLO_BR_EXCHANGE_RATE->FMAVC_REINIT_ON_EVENT.
      ENDIF.
    ENDIF.

*END of BR  non Staff Logic ----->END
    IF 1 = 2. " Staff logic on hold
*START of BR  Staff Logic ----->START
      LOOP AT U_T_FMIFIHD INTO DATA(LS_FMIFIHD2).
        LOOP AT U_T_FMIFIIT ASSIGNING FIELD-SYMBOL(<LS_FMIFIIT2>) WHERE FMBELNR = LS_FMIFIHD-FMBELNR
                                                                AND   FIKRS   = LS_FMIFIHD-FIKRS.
          "NME 20241125
          IF LS_FMIFIHD2-AWTYP = 'HRPAY'.
            "Get FI lines
            YYLO_BR_PAYROLL_POSTING_BL->GET_ACCOUNT_LINE( EXPORTING IV_ITEM = <LS_FMIFIIT2>-KNBUZEI
                                                          IMPORTING ES_ACCOUNT_GL = YYLS_ACCOUNT_GL
                                                                    ES_ACCOUNT_AMOUNT = YYLS_ACCOUNT_AMOUNT ).
          ENDIF.

          CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_2( IV_RLDNR = <LS_FMIFIIT2>-RLDNR  " LEDGER
                                               IV_FIKRS = <LS_FMIFIIT2>-FIKRS              " FM AREA
                                               IV_GSBER = <LS_FMIFIIT2>-BUS_AREA           " Business Area
                                               IV_WAERS = <LS_FMIFIIT2>-TWAER              " Currency
                                               IV_FIPEX = <LS_FMIFIIT2>-FIPEX              "Commitment Item
                                               IV_VRGNG = <LS_FMIFIIT2>-VRGNG              "BUsiness transaction
                                               "ADD HKONT
                                               "ADD PERSONAL CHECK
                                               "FUND TYPE
                                               IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = <LS_FMIFIIT2>-FIKRS IV_FINCODE = <LS_FMIFIIT2>-FONDS ) ) = ABAP_TRUE.

          "First save data before conversion in table YTFM_BR_FMIFIIT
          IF U_FLG_UPDATE  = CON_OFF OR G_FLG_REBUILD = CON_ON.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT'
              EXPORTING
                IS_FMIFIIT   = <LS_FMIFIIT2>
              EXCEPTIONS
                ERROR_UPDATE = 1
                OTHERS       = 2.
          ELSE.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT' IN UPDATE TASK
              EXPORTING
                IS_FMIFIIT   = <LS_FMIFIIT2>
              EXCEPTIONS
                ERROR_UPDATE = 1
                OTHERS       = 2.
          ENDIF.


          IF <LS_FMIFIIT2>-TWAER = 'EUR'.
            "Do conversion EUR to constant dollar
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = LS_FMIFIHD-BUDAT
                                                                  IV_FOREIGN_AMOUNT = <LS_FMIFIIT2>-TRBTR
                                                                  IV_FOREIGN_CURRENCY = <LS_FMIFIIT2>-TWAER
                                                                  IV_LOCAL_CURRENCY = 'USD'
                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                  EV_SUBRC = YYLV_SUBRC ).
            CHECK YYLV_SUBRC = 0.
            <LS_FMIFIIT2>-FKBTR = YYLV_AMOUNT.
            "Store Fund to recalculate AVC
            MOVE-CORRESPONDING <LS_FMIFIIT2> TO YYLS_AVC_FUND.
            INSERT YYLS_AVC_FUND INTO TABLE YYLO_BR_EXCHANGE_RATE->MT_AVC_FUND.

          ELSEIF <LS_FMIFIIT2>-TWAER = 'USD'.
            "Do conversion USD UNORE to USD constant dollar TBD.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = LS_FMIFIHD-BUDAT
                                                                  IV_FOREIGN_AMOUNT = <LS_FMIFIIT2>-TRBTR
                                                                  IV_FOREIGN_CURRENCY = <LS_FMIFIIT2>-TWAER
                                                                  IV_LOCAL_CURRENCY = 'USD'
                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                  EV_SUBRC = YYLV_SUBRC ).
            CHECK YYLV_SUBRC = 0.
            <LS_FMIFIIT2>-FKBTR = YYLV_AMOUNT.
            "Store Fund to recalculate AVC
            MOVE-CORRESPONDING <LS_FMIFIIT2> TO YYLS_AVC_FUND.
            INSERT YYLS_AVC_FUND INTO TABLE YYLO_BR_EXCHANGE_RATE->MT_AVC_FUND.
          ENDIF.

        ENDLOOP.

**End Staff Logic

*Trigger Update AVC total tables after event

      ENDLOOP.
    ENDIF. " Staff logic on hold


ENDENHANCEMENT.