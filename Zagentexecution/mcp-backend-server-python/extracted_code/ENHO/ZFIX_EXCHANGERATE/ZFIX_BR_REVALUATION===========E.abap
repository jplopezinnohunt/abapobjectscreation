ENHANCEMENT 2  .
DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
"Recontruct LInes only affected by BR Rules.
"This routine will delete the lines not affected to not impact by revaluation.

IF sy-tcode =  'FMN4N'.
  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
  IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
    LOOP AT c_t_fmoi  ASSIGNING FIELD-SYMBOL(<yyls_c_t_fmoi>).
*    IF  <yyls_c_t_fmoi>-fikrs NE 'UNES' . "Eliminates all transaction not comming from UNES < not required
*    DELETE   c_t_fmoi.
      CHECK <yyls_c_t_fmoi>-fikrs = 'UNES'.          " Rule only applicable for UNES
      IF   <yyls_c_t_fmoi>-twaer NE 'EUR'.        "Delete if PO are not In EUR
        DELETE   c_t_fmoi.
      ELSEIF  <yyls_c_t_fmoi>-bus_area NE 'GEF'.
        DELETE   c_t_fmoi.
        "Delete if fund type in PO line are not selectables.
      ELSEIF yylo_br_exchange_rate->check_conditions( iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                                 iv_fikrs = <yyls_c_t_fmoi>-fikrs iv_fincode = <yyls_c_t_fmoi>-fonds ) ) = abap_false.
        DELETE   c_t_fmoi.
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
*Delete Buffer information if not is reinstalled.

DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
IF sy-tcode =  'FMN4N'.
  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
  IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
    LOOP AT u_t_fmioi_buf   ASSIGNING FIELD-SYMBOL(<yyls_g_t_fmioi_buf>).
      CHECK <yyls_g_t_fmioi_buf>-fikrs = 'UNES' .
      IF   <yyls_g_t_fmioi_buf>-twaer NE 'EUR'.
        DELETE   g_t_fmioi_buf.
      ELSEIF  <yyls_g_t_fmioi_buf>-bus_area NE 'GEF'.
        DELETE   u_t_fmioi_buf .
        "Delete if fund type in PO line are not selectables.
      ELSEIF yylo_br_exchange_rate->check_conditions( iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                                 iv_fikrs = <yyls_g_t_fmioi_buf>-fikrs iv_fincode = <yyls_g_t_fmioi_buf>-fonds ) ) = abap_false.
        DELETE   u_t_fmioi_buf .
      ENDIF.
    ENDLOOP.
  ENDIF.
ENDIF.

ENDENHANCEMENT.