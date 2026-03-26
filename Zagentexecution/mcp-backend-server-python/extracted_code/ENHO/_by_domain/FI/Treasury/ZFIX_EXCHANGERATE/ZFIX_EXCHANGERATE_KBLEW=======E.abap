ENHANCEMENT 1  .
*For transaction generated from other Modules mainly FI and use earmarked Funds
*Update KBLEW consumption in formation currencies.
*KBLEW table have 2 LInes for each currency 00 Transacion and 10 Local . KBLE only 1.
*Currency type 00 has the transaction Currency amount
*Currency type 10 has the local currency amount converted.
*Enhacement will recalculate the amount for currency type 10 from transaction currency EUR

DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
DATA yylv_amount TYPE fmioi-fkbtr.
DATA yylv_subrc TYPE sy-subrc.

yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).


IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.

  "Get line in transaction currency
  READ TABLE c_t_kblew INTO DATA(ls_tr_kblew) WITH KEY belnr = i_f_kble-belnr
                                                       blpos = i_f_kble-blpos
                                                       bpent = i_f_kble-bpent
                                                       curtp = con_currtype_waers.
  IF sy-subrc = 0.
*Start of BR  non Staff Logic ----->START
    IF yylo_br_exchange_rate->check_conditions( iv_bukrs = i_f_kble-rbukrs
                                                iv_gsber = me->m_f_kblp-gsber
                                                iv_waers = ls_tr_kblew-waers
                                                iv_fipex = me->m_f_kblp-fipex
                                                iv_vrgng = i_f_kble-vrgng
                                                iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                           iv_fikrs = yylo_br_exchange_rate->get_fm_area_from_company_code( iv_bukrs =  i_f_kble-rbukrs )
                                                           iv_fincode = me->m_f_kblp-geber ) ) = abap_true.
      "Get line in company code currency
      READ TABLE c_t_kblew ASSIGNING FIELD-SYMBOL(<ls_cc_kblew>) WITH KEY belnr = i_f_kble-belnr
                                                                          blpos = i_f_kble-blpos
                                                                          bpent = i_f_kble-bpent
                                                                          curtp = con_currtype_hwaer.
      IF sy-subrc = 0.
        "Do conversion in constant dollar
        yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                              iv_foreign_amount = ls_tr_kblew-wrbtr
                                                              iv_foreign_currency = ls_tr_kblew-waers
                                                              iv_local_currency = <ls_cc_kblew>-waers
                                                    IMPORTING ev_local_amount = yylv_amount
                                                              ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <ls_cc_kblew>-wrbtr = yylv_amount.
        ENDIF.
        yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                              iv_foreign_amount = ls_tr_kblew-wrbtrapp
                                                              iv_foreign_currency = ls_tr_kblew-waers
                                                              iv_local_currency = <ls_cc_kblew>-waers
                                                    IMPORTING ev_local_amount = yylv_amount
                                                              ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <ls_cc_kblew>-wrbtrapp = yylv_amount.
        ENDIF.
      ENDIF.
    ENDIF.
*END of BR  non Staff Logic ----->END

*START of BR  Staff Logic ----->START
    IF 1 = 2. " On hold staff Logic
      IF yylo_br_exchange_rate->check_conditions_2( iv_bukrs = i_f_kble-rbukrs  "Company Code
                                                 iv_gsber = me->m_f_kblp-gsber  "Business Area
                                                 iv_waers = ls_tr_kblew-waers   "Currency
                                                 iv_fipex = me->m_f_kblp-fipex  "Commitment Item
                                                 iv_vrgng = i_f_kble-vrgng      "Business Transaction
                                                 "ADD HKONT
                                                 "ADD PEESON CHECK
                                                 "Type of fund
                                                 iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                            iv_fikrs = yylo_br_exchange_rate->get_fm_area_from_company_code( iv_bukrs =  i_f_kble-rbukrs )
                                                            iv_fincode = me->m_f_kblp-geber ) ) = abap_true.
        "Get line in company code currency
        READ TABLE c_t_kblew ASSIGNING FIELD-SYMBOL(<ls_cc_kblew2>) WITH KEY belnr = i_f_kble-belnr
                                                                            blpos = i_f_kble-blpos
                                                                            bpent = i_f_kble-bpent
                                                                            curtp = con_currtype_hwaer.
        IF sy-subrc = 0.
          "Do conversion in constant dollar

          IF ls_tr_kblew-waers = 'EUR'.
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                                  iv_foreign_amount = ls_tr_kblew-wrbtr
                                                                  iv_foreign_currency = ls_tr_kblew-waers
                                                                  iv_local_currency = <ls_cc_kblew2>-waers
                                                        IMPORTING ev_local_amount = yylv_amount
                                                                  ev_subrc = yylv_subrc ).
            IF yylv_subrc = 0.
              <ls_cc_kblew2>-wrbtr = yylv_amount.
            ENDIF.
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                                  iv_foreign_amount = ls_tr_kblew-wrbtrapp
                                                                  iv_foreign_currency = ls_tr_kblew-waers
                                                                  iv_local_currency = <ls_cc_kblew2>-waers
                                                        IMPORTING ev_local_amount = yylv_amount
                                                                  ev_subrc = yylv_subrc ).
            IF yylv_subrc = 0.
              <ls_cc_kblew2>-wrbtrapp = yylv_amount.
            ENDIF.
*Convert USD UNORE to USD BR
          ELSEIF ls_tr_kblew-waers = 'USD'.
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                               iv_foreign_amount = ls_tr_kblew-wrbtr
                                                               iv_foreign_currency = ls_tr_kblew-waers
                                                               iv_local_currency = <ls_cc_kblew2>-waers "USD"
                                                     IMPORTING ev_local_amount = yylv_amount
                                                               ev_subrc = yylv_subrc ).
            IF yylv_subrc = 0.
              <ls_cc_kblew2>-wrbtr = yylv_amount.
            ENDIF.
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = i_f_reference-budat
                                                                  iv_foreign_amount = ls_tr_kblew-wrbtrapp
                                                                  iv_foreign_currency = ls_tr_kblew-waers
                                                                  iv_local_currency = <ls_cc_kblew2>-waers "USD"
                                                        IMPORTING ev_local_amount = yylv_amount
                                                                  ev_subrc = yylv_subrc ).
            IF yylv_subrc = 0.
              <ls_cc_kblew2>-wrbtrapp = yylv_amount.
            ENDIF.
          ENDIF. "Currencies
        ENDIF.
      ENDIF.


*END of BR  Staff Logic ----->END
    ENDIF. "On hold Staff logic
  ENDIF.

ENDIF.

ENDENHANCEMENT.
