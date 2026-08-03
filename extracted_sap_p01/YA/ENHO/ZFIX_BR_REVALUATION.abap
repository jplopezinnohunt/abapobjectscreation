ENHANCEMENT 2  .
DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
"Recontruct LInes only affected by BR Rules.
"This routine will delete the lines not affected to not impact by revaluation.

IF SY-TCODE =  'FMN4N'.
  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
  IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
    LOOP AT C_T_FMOI  ASSIGNING FIELD-SYMBOL(<YYLS_C_T_FMOI>).
*    IF  <yyls_c_t_fmoi>-fikrs NE 'UNES' . "Eliminates all transaction not comming from UNES < not required
*    DELETE   c_t_fmoi.
      CHECK <YYLS_C_T_FMOI>-FIKRS = 'UNES'.          " Rule only applicable for UNES
      IF   <YYLS_C_T_FMOI>-TWAER NE 'EUR'.        "Delete if PO are not In EUR
        DELETE   C_T_FMOI.
      ELSEIF  <YYLS_C_T_FMOI>-BUS_AREA NE 'GEF'.
        DELETE   C_T_FMOI.
        "Delete if fund type in PO line are not selectables.
      ELSEIF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
                                                                 IV_FIKRS = <YYLS_C_T_FMOI>-FIKRS IV_FINCODE = <YYLS_C_T_FMOI>-FONDS ) ) = ABAP_FALSE.
        DELETE   C_T_FMOI.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
*Delete Buffer information if not is reinstalled.

DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
IF SY-TCODE =  'FMN4N'.
  YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
  IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
    LOOP AT U_T_FMIOI_BUF   ASSIGNING FIELD-SYMBOL(<YYLS_G_T_FMIOI_BUF>).
      CHECK <YYLS_G_T_FMIOI_BUF>-FIKRS = 'UNES' .
      IF   <YYLS_G_T_FMIOI_BUF>-TWAER NE 'EUR'.
        DELETE   G_T_FMIOI_BUF.
      ELSEIF  <YYLS_G_T_FMIOI_BUF>-BUS_AREA NE 'GEF'.
        DELETE   U_T_FMIOI_BUF .
        "Delete if fund type in PO line are not selectables.
      ELSEIF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
                                                                 IV_FIKRS = <YYLS_G_T_FMIOI_BUF>-FIKRS IV_FINCODE = <YYLS_G_T_FMIOI_BUF>-FONDS ) ) = ABAP_FALSE.
        DELETE   U_T_FMIOI_BUF .
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDIF.

ENDENHANCEMENT.