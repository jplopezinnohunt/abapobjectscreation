ENHANCEMENT 1  .
*AVC Commitments items Convert commitment to Budget rate

  DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
  DATA yylv_amount TYPE fmioi-fkbtr.
  DATA yylv_subrc TYPE sy-subrc.

  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
    LOOP AT t_fmioi ASSIGNING FIELD-SYMBOL(<ls_fmioi>).
      CHECK yylo_br_exchange_rate->check_conditions( iv_rldnr = <ls_fmioi>-rldnr
                                                     iv_fikrs = <ls_fmioi>-fikrs
                                                     iv_gsber = <ls_fmioi>-bus_area
                                                     iv_waers = <ls_fmioi>-twaer
                                                     iv_fipex = <ls_fmioi>-fipex
                                                     iv_vrgng = <ls_fmioi>-vrgng
                                                     iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = <ls_fmioi>-fikrs iv_fincode = <ls_fmioi>-fonds ) ) = abap_true.
      yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <ls_fmioi>-budat
                                                            iv_foreign_amount = <ls_fmioi>-trbtr
                                                            iv_foreign_currency = <ls_fmioi>-twaer
                                                            iv_local_currency = 'USD'
                                                  IMPORTING ev_local_amount = yylv_amount
                                                            ev_subrc = yylv_subrc ).
      CHECK yylv_subrc = 0.
      <ls_fmioi>-fkbtr = yylv_amount.
    ENDLOOP.
ENDENHANCEMENT.
ENHANCEMENT 3  .
*02/07/2025 Adding Check in finance Posting.
  DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
  DATA yylv_amount TYPE fmifiit-fkbtr.
  DATA yylv_subrc TYPE sy-subrc.
  DATA yyls_avc_fund TYPE ycl_fm_br_exchange_rate_bl=>ty_avc_fund.
  DATA yylo_br_payroll_posting_bl TYPE REF TO ycl_fm_br_payroll_posting_bl.
  DATA yyls_account_gl TYPE bapiacgl04.
  DATA yyls_account_amount TYPE bapiaccr04.
  "Check and set amount to Fix rate constant dollar
   yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

  IF u_t_fmifiit IS NOT INITIAL.
    LOOP AT u_t_fmifiit ASSIGNING FIELD-SYMBOL(<ls_fmifiit>).
      "   WHERE fmbelnr = ls_fmifihd-fmbelnr
      "   AND   fikrs   = ls_fmifihd-fikrs.
      CHECK yylo_br_exchange_rate->check_conditions( iv_rldnr = <ls_fmifiit>-rldnr
                                                     iv_fikrs = <ls_fmifiit>-fikrs
                                                     iv_gsber = <ls_fmifiit>-bus_area
                                                     iv_waers = <ls_fmifiit>-twaer
                                                     iv_fipex = <ls_fmifiit>-fipex
                                                     iv_vrgng = <ls_fmifiit>-vrgng
                                                     iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = <ls_fmifiit>-fikrs iv_fincode = <ls_fmifiit>-fonds ) ) = abap_true.
      CHECK c_t_avc IS NOT INITIAL.
      LOOP AT c_t_avc ASSIGNING  FIELD-SYMBOL(<ls_c_t_avc>) WHERE rfpos = <ls_fmifiit>-knbuzei.
        "Do conversion in constant dollar
        yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <ls_fmifiit>-psobt
                                                                 iv_foreign_amount = <ls_fmifiit>-trbtr
                                                                 iv_foreign_currency = <ls_fmifiit>-twaer
                                                                 iv_local_currency = 'USD'
                                                       IMPORTING ev_local_amount = yylv_amount
                                                                 ev_subrc = yylv_subrc ).
        CHECK yylv_subrc = 0.
        <ls_c_t_avc>-fkbtr = yylv_amount.
        EXIT.
      ENDLOOP.
    ENDLOOP.
  ENDIF.
ENDENHANCEMENT.
