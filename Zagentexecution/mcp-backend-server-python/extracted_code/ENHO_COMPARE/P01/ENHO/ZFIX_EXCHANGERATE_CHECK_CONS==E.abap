ENHANCEMENT 1  .
DATA yylt_addref_save TYPE fmef_refdata_tt.
DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
DATA yylv_amount TYPE fmioi-fkbtr.
DATA yylv_subrc TYPE sy-subrc.
DATA yylv_upd_done TYPE xfeld.

"Save table M_T_ADDREF to restore at the end of method
yylt_addref_save = m_t_addref.
"Get data from KBLK

"Check and set amount to Fix rate constant dollar
yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

*Start of BR Non Staff Logic ----->START
IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
  LOOP AT m_t_addref ASSIGNING FIELD-SYMBOL(<yyls_addref>).
    CHECK yylo_br_exchange_rate->check_conditions( iv_bukrs = <yyls_addref>-ref-bukrs
                                                   iv_fikrs = m_r_doc->m_f_kblk-fikrs
                                                   iv_gsber = m_f_kblp-gsber
                                                   iv_waers = m_r_doc->m_f_kblk-waers
                                                   iv_fipex = m_f_kblp-fipex
                                                   iv_vrgng = m_f_kblp-vrgng
                                                   iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = m_r_doc->m_f_kblk-fikrs iv_fincode = m_f_kblp-geber ) ) = abap_true.
    yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_addref>-ref-budat
                                                          iv_foreign_amount = <yyls_addref>-ref-wtges
                                                          iv_foreign_currency = <yyls_addref>-ref-waers
                                                          iv_local_currency = 'USD'
                                                IMPORTING ev_local_amount = yylv_amount
                                                          ev_subrc = yylv_subrc ).
    IF yylv_subrc = 0.
      <yyls_addref>-ref-hwges = yylv_amount.
      yylv_upd_done = abap_true.
    ENDIF.
    yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_addref>-ref-budat
                                                          iv_foreign_amount = <yyls_addref>-ref-wtgesapp
                                                          iv_foreign_currency = <yyls_addref>-ref-waers
                                                          iv_local_currency = 'USD'
                                                IMPORTING ev_local_amount = yylv_amount
                                                          ev_subrc = yylv_subrc ).
    IF yylv_subrc = 0.
      <yyls_addref>-ref-hwgesapp = yylv_amount.
      yylv_upd_done = abap_true.
    ENDIF.
  ENDLOOP.
*END of BR Non Staff Logic ----->END
  IF 1 = 2. "Staff logic on hold.
*START of BR STAFF Logic ----->START
    LOOP AT m_t_addref ASSIGNING FIELD-SYMBOL(<yyls_addref2>).
      CHECK yylo_br_exchange_rate->check_conditions_2( iv_bukrs = <yyls_addref2>-ref-bukrs  "Companyh Code
                                                     iv_fikrs = m_r_doc->m_f_kblk-fikrs   "FM Area
                                                     iv_gsber = m_f_kblp-gsber            "Business Area
                                                     iv_waers = m_r_doc->m_f_kblk-waers   "Currency
                                                     iv_fipex = m_f_kblp-fipex            "Commitment Item
                                                     iv_vrgng = m_f_kblp-vrgng            "Business transaction.
                                                     "ADDHKONT
                                                     "PERSONAL CHECK
                                    iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = m_r_doc->m_f_kblk-fikrs iv_fincode = m_f_kblp-geber ) )
                                    = abap_true. " FUND TYPE



      IF <yyls_addref2>-ref-waers = 'EUR'.
        yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_addref2>-ref-budat
                                                              iv_foreign_amount = <yyls_addref2>-ref-wtges
                                                              iv_foreign_currency = <yyls_addref2>-ref-waers
                                                              iv_local_currency = 'USD'
                                                    IMPORTING ev_local_amount = yylv_amount
                                                              ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <yyls_addref2>-ref-hwges = yylv_amount.
          yylv_upd_done = abap_true.
        ENDIF.
        yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_addref2>-ref-budat
                                                              iv_foreign_amount = <yyls_addref2>-ref-wtgesapp
                                                              iv_foreign_currency = <yyls_addref2>-ref-waers
                                                              iv_local_currency = 'USD'
                                                    IMPORTING ev_local_amount = yylv_amount
                                                              ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <yyls_addref2>-ref-hwgesapp = yylv_amount.
          yylv_upd_done = abap_true.
        ENDIF.

* COnvert USD UNORE to USD BR
      ELSEIF <yyls_addref2>-ref-waers = 'USD'.
        yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = <yyls_addref2>-ref-budat
                                                             iv_foreign_amount = <yyls_addref2>-ref-wtges
                                                             iv_foreign_currency = <yyls_addref2>-ref-waers "Transaction Currency
                                                             iv_local_currency = 'USD'
                                                   IMPORTING ev_local_amount = yylv_amount
                                                             ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <yyls_addref2>-ref-hwges = yylv_amount.
          yylv_upd_done = abap_true.
        ENDIF.
        yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = <yyls_addref2>-ref-budat
                                                              iv_foreign_amount = <yyls_addref2>-ref-wtgesapp "Transaction Currency
                                                              iv_foreign_currency = <yyls_addref2>-ref-waers
                                                              iv_local_currency = 'USD'
                                                    IMPORTING ev_local_amount = yylv_amount
                                                              ev_subrc = yylv_subrc ).
        IF yylv_subrc = 0.
          <yyls_addref2>-ref-hwgesapp = yylv_amount.
          yylv_upd_done = abap_true.
        ENDIF.


      ENDIF. " Currency EUR or USD
    ENDLOOP.
*END of BR Staff Logic ----->END
  ENDIF. "Staff logic on hold.
ENDIF.
ENDENHANCEMENT.
ENHANCEMENT 2  .
IF yylt_addref_save IS NOT INITIAL AND yylv_upd_done = abap_true.
  m_t_addref = yylt_addref_save.
ENDIF.
ENDENHANCEMENT.
