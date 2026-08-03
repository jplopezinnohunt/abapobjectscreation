ENHANCEMENT 1  .
*AVC Commitments items Convert commitment to Budget rate

  DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
  DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
  DATA YYLV_SUBRC TYPE SY-SUBRC.

  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
    LOOP AT T_FMIOI ASSIGNING FIELD-SYMBOL(<LS_FMIOI>).
      CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_RLDNR = <LS_FMIOI>-RLDNR
                                                     IV_FIKRS = <LS_FMIOI>-FIKRS
                                                     IV_GSBER = <LS_FMIOI>-BUS_AREA
                                                     IV_WAERS = <LS_FMIOI>-TWAER
                                                     IV_FIPEX = <LS_FMIOI>-FIPEX
                                                     IV_VRGNG = <LS_FMIOI>-VRGNG
                                                     IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = <LS_FMIOI>-FIKRS IV_FINCODE = <LS_FMIOI>-FONDS ) ) = ABAP_TRUE.
      YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <LS_FMIOI>-BUDAT
                                                            IV_FOREIGN_AMOUNT = <LS_FMIOI>-TRBTR
                                                            IV_FOREIGN_CURRENCY = <LS_FMIOI>-TWAER
                                                            IV_LOCAL_CURRENCY = 'USD'
                                                  IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                            EV_SUBRC = YYLV_SUBRC ).
      CHECK YYLV_SUBRC = 0.
      <LS_FMIOI>-FKBTR = YYLV_AMOUNT.
    ENDLOOP.
ENDENHANCEMENT.
ENHANCEMENT 3  .
*02/07/2025 Adding Check in finance Posting.
  DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
  DATA YYLV_AMOUNT TYPE FMIFIIT-FKBTR.
  DATA YYLV_SUBRC TYPE SY-SUBRC.
  DATA YYLS_AVC_FUND TYPE YCL_FM_BR_EXCHANGE_RATE_BL=>TY_AVC_FUND.
  DATA YYLO_BR_PAYROLL_POSTING_BL TYPE REF TO YCL_FM_BR_PAYROLL_POSTING_BL.
  DATA YYLS_ACCOUNT_GL TYPE BAPIACGL04.
  DATA YYLS_ACCOUNT_AMOUNT TYPE BAPIACCR04.
  "Check and set amount to Fix rate constant dollar
   YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

  IF U_T_FMIFIIT IS NOT INITIAL.
    LOOP AT U_T_FMIFIIT ASSIGNING FIELD-SYMBOL(<LS_FMIFIIT>).
      "   WHERE fmbelnr = ls_fmifihd-fmbelnr
      "   AND   fikrs   = ls_fmifihd-fikrs.
      CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_RLDNR = <LS_FMIFIIT>-RLDNR
                                                     IV_FIKRS = <LS_FMIFIIT>-FIKRS
                                                     IV_GSBER = <LS_FMIFIIT>-BUS_AREA
                                                     IV_WAERS = <LS_FMIFIIT>-TWAER
                                                     IV_FIPEX = <LS_FMIFIIT>-FIPEX
                                                     IV_VRGNG = <LS_FMIFIIT>-VRGNG
                                                     IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = <LS_FMIFIIT>-FIKRS IV_FINCODE = <LS_FMIFIIT>-FONDS ) ) = ABAP_TRUE.
      CHECK C_T_AVC IS NOT INITIAL.
      LOOP AT C_T_AVC ASSIGNING  FIELD-SYMBOL(<LS_C_T_AVC>) WHERE RFPOS = <LS_FMIFIIT>-KNBUZEI.
        "Do conversion in constant dollar
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <LS_FMIFIIT>-PSOBT
                                                                 IV_FOREIGN_AMOUNT = <LS_FMIFIIT>-TRBTR
                                                                 IV_FOREIGN_CURRENCY = <LS_FMIFIIT>-TWAER
                                                                 IV_LOCAL_CURRENCY = 'USD'
                                                       IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                 EV_SUBRC = YYLV_SUBRC ).
        CHECK YYLV_SUBRC = 0.
        <LS_C_T_AVC>-FKBTR = YYLV_AMOUNT.
        EXIT.
      ENDLOOP.
    ENDLOOP.
  ENDIF.
ENDENHANCEMENT.