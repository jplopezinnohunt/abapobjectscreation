ENHANCEMENT 1  .
*For transaction generated from other Modules mainly FI and use earmarked Funds
*Update KBLEW consumption in formation currencies.
*KBLEW table have 2 LInes for each currency 00 Transacion and 10 Local . KBLE only 1.
*Currency type 00 has the transaction Currency amount
*Currency type 10 has the local currency amount converted.
*Enhacement will recalculate the amount for currency type 10 from transaction currency EUR

DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
DATA YYLV_SUBRC TYPE SY-SUBRC.

YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).


IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.

  "Get line in transaction currency
  READ TABLE C_T_KBLEW INTO DATA(LS_TR_KBLEW) WITH KEY BELNR = I_F_KBLE-BELNR
                                                       BLPOS = I_F_KBLE-BLPOS
                                                       BPENT = I_F_KBLE-BPENT
                                                       CURTP = CON_CURRTYPE_WAERS.
  IF SY-SUBRC = 0.
*Start of BR  non Staff Logic ----->START
    IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_BUKRS = I_F_KBLE-RBUKRS
                                                IV_GSBER = ME->M_F_KBLP-GSBER
                                                IV_WAERS = LS_TR_KBLEW-WAERS
                                                IV_FIPEX = ME->M_F_KBLP-FIPEX
                                                IV_VRGNG = I_F_KBLE-VRGNG
                                                IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
                                                           IV_FIKRS = YYLO_BR_EXCHANGE_RATE->GET_FM_AREA_FROM_COMPANY_CODE( IV_BUKRS =  I_F_KBLE-RBUKRS )
                                                           IV_FINCODE = ME->M_F_KBLP-GEBER ) ) = ABAP_TRUE.
      "Get line in company code currency
      READ TABLE C_T_KBLEW ASSIGNING FIELD-SYMBOL(<LS_CC_KBLEW>) WITH KEY BELNR = I_F_KBLE-BELNR
                                                                          BLPOS = I_F_KBLE-BLPOS
                                                                          BPENT = I_F_KBLE-BPENT
                                                                          CURTP = CON_CURRTYPE_HWAER.
      IF SY-SUBRC = 0.
        "Do conversion in constant dollar
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                              IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTR
                                                              IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                              IV_LOCAL_CURRENCY = <LS_CC_KBLEW>-WAERS
                                                    IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <LS_CC_KBLEW>-WRBTR = YYLV_AMOUNT.
        ENDIF.
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                              IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTRAPP
                                                              IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                              IV_LOCAL_CURRENCY = <LS_CC_KBLEW>-WAERS
                                                    IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <LS_CC_KBLEW>-WRBTRAPP = YYLV_AMOUNT.
        ENDIF.
      ENDIF.
    ENDIF.
*END of BR  non Staff Logic ----->END

*START of BR  Staff Logic ----->START
    IF 1 = 2. " On hold staff Logic
      IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_2( IV_BUKRS = I_F_KBLE-RBUKRS  "Company Code
                                                 IV_GSBER = ME->M_F_KBLP-GSBER  "Business Area
                                                 IV_WAERS = LS_TR_KBLEW-WAERS   "Currency
                                                 IV_FIPEX = ME->M_F_KBLP-FIPEX  "Commitment Item
                                                 IV_VRGNG = I_F_KBLE-VRGNG      "Business Transaction
                                                 "ADD HKONT
                                                 "ADD PEESON CHECK
                                                 "Type of fund
                                                 IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
                                                            IV_FIKRS = YYLO_BR_EXCHANGE_RATE->GET_FM_AREA_FROM_COMPANY_CODE( IV_BUKRS =  I_F_KBLE-RBUKRS )
                                                            IV_FINCODE = ME->M_F_KBLP-GEBER ) ) = ABAP_TRUE.
        "Get line in company code currency
        READ TABLE C_T_KBLEW ASSIGNING FIELD-SYMBOL(<LS_CC_KBLEW2>) WITH KEY BELNR = I_F_KBLE-BELNR
                                                                            BLPOS = I_F_KBLE-BLPOS
                                                                            BPENT = I_F_KBLE-BPENT
                                                                            CURTP = CON_CURRTYPE_HWAER.
        IF SY-SUBRC = 0.
          "Do conversion in constant dollar

          IF LS_TR_KBLEW-WAERS = 'EUR'.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                                  IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTR
                                                                  IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                                  IV_LOCAL_CURRENCY = <LS_CC_KBLEW2>-WAERS
                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                  EV_SUBRC = YYLV_SUBRC ).
            IF YYLV_SUBRC = 0.
              <LS_CC_KBLEW2>-WRBTR = YYLV_AMOUNT.
            ENDIF.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                                  IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTRAPP
                                                                  IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                                  IV_LOCAL_CURRENCY = <LS_CC_KBLEW2>-WAERS
                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                  EV_SUBRC = YYLV_SUBRC ).
            IF YYLV_SUBRC = 0.
              <LS_CC_KBLEW2>-WRBTRAPP = YYLV_AMOUNT.
            ENDIF.
*Convert USD UNORE to USD BR
          ELSEIF LS_TR_KBLEW-WAERS = 'USD'.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                               IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTR
                                                               IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                               IV_LOCAL_CURRENCY = <LS_CC_KBLEW2>-WAERS "USD"
                                                     IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                               EV_SUBRC = YYLV_SUBRC ).
            IF YYLV_SUBRC = 0.
              <LS_CC_KBLEW2>-WRBTR = YYLV_AMOUNT.
            ENDIF.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = I_F_REFERENCE-BUDAT
                                                                  IV_FOREIGN_AMOUNT = LS_TR_KBLEW-WRBTRAPP
                                                                  IV_FOREIGN_CURRENCY = LS_TR_KBLEW-WAERS
                                                                  IV_LOCAL_CURRENCY = <LS_CC_KBLEW2>-WAERS "USD"
                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                  EV_SUBRC = YYLV_SUBRC ).
            IF YYLV_SUBRC = 0.
              <LS_CC_KBLEW2>-WRBTRAPP = YYLV_AMOUNT.
            ENDIF.
          ENDIF. "Currencies
        ENDIF.
      ENDIF.


*END of BR  Staff Logic ----->END
    ENDIF. "On hold Staff logic
  ENDIF.

ENDIF.

ENDENHANCEMENT.