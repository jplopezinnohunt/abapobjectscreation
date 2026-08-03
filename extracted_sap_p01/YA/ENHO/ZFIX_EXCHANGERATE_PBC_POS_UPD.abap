ENHANCEMENT 1  .
  DATA YYLO_BR_PBC_POSTING TYPE REF TO YCL_FM_BR_PBC_POSTING_BL.
  DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
  DATA YYLV_PERNR TYPE P_PERNR.
  DATA YYLT_DOC_POS TYPE HRFPM_FPM_DOC_POS_STAT_IT.
  DATA YYLV_SUBRC1 TYPE SY-SUBRC.
  DATA YYLV_SUBRC2 TYPE SY-SUBRC.
  DATA YYLS_POS_BEFORE TYPE HRFPM_FM_DOC_POS.

  CHECK 1 = 2.   "Deactivated the 2024/01/08

  "Instanciate class
  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
  CHECK YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.

  YYLO_BR_PBC_POSTING = NEW YCL_FM_BR_PBC_POSTING_BL( ).

  "1. Identify personnel number concerned by this posting
  IF ME->FPM-DOC_POS_INS IS NOT INITIAL.
    YYLT_DOC_POS = ME->FPM-DOC_POS_INS.
  ELSEIF ME->FPM-DOC_POS_UPD IS NOT INITIAL.
    YYLT_DOC_POS = ME->FPM-DOC_POS_UPD.
  ELSEIF ME->FPM-DOC_POS_UPD IS NOT INITIAL.
    YYLT_DOC_POS = ME->FPM-DOC_POS_DEL.
  ENDIF.
  YYLO_BR_PBC_POSTING->GET_PERNR( EXPORTING IV_ENC_TYPE = CS_POS-ENC_TYPE
                                            IV_BELNR = CS_POS-BELNR
                                            IV_FPM_POSNR = CS_POS-FPM_POSNR
                                            IT_DOC_POS = YYLT_DOC_POS
                                  IMPORTING EV_PERNR = YYLV_PERNR ).
  CHECK YYLV_PERNR IS NOT INITIAL.

  "2. check conditions
  CHECK YYLO_BR_PBC_POSTING->CHECK_CONDITIONS( IV_PERNR = YYLV_PERNR
                                               IS_POS = CS_POS ) = ABAP_TRUE.

  "3. Save original amounts
  YYLS_POS_BEFORE = CS_POS.



  IF 1 = 2.
    YYLO_BR_PBC_POSTING->CONVERT_TO_BUDGET_RATE( EXPORTING IV_DATE = CS_POS-DUE_DATE
                                                           IV_AMOUNT = CS_POS-BETRG
                                                           IV_WAERS = CS_POS-WAERS
                                                 IMPORTING EV_AMOUNT = CS_POS-BETRG
                                                           EV_SUBRC = YYLV_SUBRC1 ).

    YYLO_BR_PBC_POSTING->CONVERT_TO_BUDGET_RATE( EXPORTING IV_DATE = CS_POS-DUE_DATE
                                                           IV_AMOUNT = CS_POS-DELTA_AMOUNT
                                                           IV_WAERS = CS_POS-CURRENCY
                                                 IMPORTING EV_AMOUNT = CS_POS-DELTA_AMOUNT
                                                            EV_SUBRC = YYLV_SUBRC2 ).
  ENDIF.
  "4. Convert amounts to BR amounts
  "ALL PBC Documents are in USD. Even if postings are in EUR.
  IF CS_POS-WAERS = 'USD'.
    YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE =  CS_POS-DUE_DATE
                                                                 IV_FOREIGN_AMOUNT = CS_POS-BETRG
                                                                 IV_FOREIGN_CURRENCY = CS_POS-WAERS " Transaction Currency
                                                                 IV_LOCAL_CURRENCY = 'USD'   " Local Currency
                                                       IMPORTING EV_LOCAL_AMOUNT = CS_POS-BETRG
                                                                 EV_SUBRC = YYLV_SUBRC2  ).

    YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE =  CS_POS-DUE_DATE
                                                              IV_FOREIGN_AMOUNT = CS_POS-DELTA_AMOUNT
                                                              IV_FOREIGN_CURRENCY = CS_POS-WAERS " Transaction Currency
                                                              IV_LOCAL_CURRENCY = 'USD'   " Local Currency
                                                    IMPORTING EV_LOCAL_AMOUNT = CS_POS-DELTA_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC1  ).
  ENDIF.
  "5. Save modifications in trace table
  IF YYLV_SUBRC1 = 0 OR YYLV_SUBRC2 = 0.
    CALL FUNCTION 'Y_FM_UPDATE_BR_FM_POS' IN UPDATE TASK
      EXPORTING
        IS_POS_BEFORE = YYLS_POS_BEFORE
        IS_POS_AFTER  = CS_POS
      EXCEPTIONS
        ERROR_UPDATE  = 1
        OTHERS        = 2.
  ENDIF.

ENDENHANCEMENT.