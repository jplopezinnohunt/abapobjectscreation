ENHANCEMENT 2  .
*Convert KBLD consumption lines to Budget Rate
* Create And change Funds Reservation
  DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
  DATA yylv_amount TYPE fmioi-fkbtr.
  DATA yylv_subrc TYPE sy-subrc.

  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

  IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
    IF yylo_br_exchange_rate->check_conditions( iv_fikrs = kbld-fikrs
                                                iv_gsber = kbld-gsber
                                                iv_waers = kbld-waers
                                                iv_fipex = kbld-fipex
                                                iv_vrgng = kbld-vrgng
                                                iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = kbld-fikrs iv_fincode = kbld-geber ) ) = abap_true.
      yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = kbld-budat
                                                            iv_foreign_amount = kbld-wtges
                                                            iv_foreign_currency = kbld-waers
                                                            iv_local_currency = 'USD'
                                                  IMPORTING ev_local_amount = yylv_amount
                                                            ev_subrc = yylv_subrc ).
      IF yylv_subrc = 0.
        kbld-hwgesapp = yylv_amount.
      ENDIF.
    ENDIF.
  ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
*Consumption Tables should be updated using Budget rate. KLBE
*Manual consumption Reduce Manually Option
*KLBEW has additional process it manage 2 lines 1 per each currency type.

  DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
  DATA yylv_exchange_rate TYPE kbld-kursf.
  DATA yylv_subrc TYPE sy-subrc.

  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

  IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
    IF yylo_br_exchange_rate->check_conditions( iv_fikrs = kbld-fikrs
                                                iv_gsber = kbld-gsber
                                                iv_waers = kbld-waers
                                                iv_fipex = kbld-fipex
                                                iv_vrgng = kbld-vrgng
                                                iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = kbld-fikrs iv_fincode = kbld-geber ) ) = abap_true.
      yylo_br_exchange_rate->get_exchange_rate( EXPORTING iv_date = kbld-wwert
                                                          iv_foreign_currency = kbld-waers
                                                          iv_local_currency = kbld-hwaer
                                                IMPORTING ev_exchange_rate = yylv_exchange_rate
                                                          ev_subrc = yylv_subrc ).
      IF yylv_subrc = 0.
        kbld-kursf = yylv_exchange_rate.
      ENDIF.
    ENDIF.
  ENDIF.

ENDENHANCEMENT.
