ENHANCEMENT 2  .
*Convert KBLD consumption lines to Budget Rate
* Create And change Funds Reservation
  DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
  DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
  DATA YYLV_SUBRC TYPE SY-SUBRC.

  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

  IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
    IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FIKRS = KBLD-FIKRS
                                                IV_GSBER = KBLD-GSBER
                                                IV_WAERS = KBLD-WAERS
                                                IV_FIPEX = KBLD-FIPEX
                                                IV_VRGNG = KBLD-VRGNG
                                                IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = KBLD-FIKRS IV_FINCODE = KBLD-GEBER ) ) = ABAP_TRUE.
      YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = KBLD-BUDAT
                                                            IV_FOREIGN_AMOUNT = KBLD-WTGES
                                                            IV_FOREIGN_CURRENCY = KBLD-WAERS
                                                            IV_LOCAL_CURRENCY = 'USD'
                                                  IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                            EV_SUBRC = YYLV_SUBRC ).
      IF YYLV_SUBRC = 0.
        KBLD-HWGESAPP = YYLV_AMOUNT.
      ENDIF.
    ENDIF.
  ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
*Consumption Tables should be updated using Budget rate. KLBE
*Manual consumption Reduce Manually Option
*KLBEW has additional process it manage 2 lines 1 per each currency type.

  DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
  DATA YYLV_EXCHANGE_RATE TYPE KBLD-KURSF.
  DATA YYLV_SUBRC TYPE SY-SUBRC.

  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

  IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
    IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FIKRS = KBLD-FIKRS
                                                IV_GSBER = KBLD-GSBER
                                                IV_WAERS = KBLD-WAERS
                                                IV_FIPEX = KBLD-FIPEX
                                                IV_VRGNG = KBLD-VRGNG
                                                IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = KBLD-FIKRS IV_FINCODE = KBLD-GEBER ) ) = ABAP_TRUE.
      YYLO_BR_EXCHANGE_RATE->GET_EXCHANGE_RATE( EXPORTING IV_DATE = KBLD-WWERT
                                                          IV_FOREIGN_CURRENCY = KBLD-WAERS
                                                          IV_LOCAL_CURRENCY = KBLD-HWAER
                                                IMPORTING EV_EXCHANGE_RATE = YYLV_EXCHANGE_RATE
                                                          EV_SUBRC = YYLV_SUBRC ).
      IF YYLV_SUBRC = 0.
        KBLD-KURSF = YYLV_EXCHANGE_RATE.
      ENDIF.
    ENDIF.
  ENDIF.

ENDENHANCEMENT.