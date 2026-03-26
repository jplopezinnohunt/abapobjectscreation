ENHANCEMENT 1  .
  DATA yylo_br_pbc_posting TYPE REF TO ycl_fm_br_pbc_posting_bl.
  DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
  DATA yylv_pernr TYPE p_pernr.
  DATA yylt_doc_pos TYPE hrfpm_fpm_doc_pos_stat_it.
  DATA yylv_subrc1 TYPE sy-subrc.
  DATA yylv_subrc2 TYPE sy-subrc.
  DATA yyls_pos_before TYPE hrfpm_fm_doc_pos.

  CHECK 1 = 2.   "Deactivated the 2024/01/08

  "Instanciate class
  yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
  CHECK yylo_br_exchange_rate->check_br_is_active( ) = abap_true.

  yylo_br_pbc_posting = NEW ycl_fm_br_pbc_posting_bl( ).

  "1. Identify personnel number concerned by this posting
  IF me->fpm-doc_pos_ins IS NOT INITIAL.
    yylt_doc_pos = me->fpm-doc_pos_ins.
  ELSEIF me->fpm-doc_pos_upd IS NOT INITIAL.
    yylt_doc_pos = me->fpm-doc_pos_upd.
  ELSEIF me->fpm-doc_pos_upd IS NOT INITIAL.
    yylt_doc_pos = me->fpm-doc_pos_del.
  ENDIF.
  yylo_br_pbc_posting->get_pernr( EXPORTING iv_enc_type = cs_pos-enc_type
                                            iv_belnr = cs_pos-belnr
                                            iv_fpm_posnr = cs_pos-fpm_posnr
                                            it_doc_pos = yylt_doc_pos
                                  IMPORTING ev_pernr = yylv_pernr ).
  CHECK yylv_pernr IS NOT INITIAL.

  "2. check conditions
  CHECK yylo_br_pbc_posting->check_conditions( iv_pernr = yylv_pernr
                                               is_pos = cs_pos ) = abap_true.

  "3. Save original amounts
  yyls_pos_before = cs_pos.



  IF 1 = 2.
    yylo_br_pbc_posting->convert_to_budget_rate( EXPORTING iv_date = cs_pos-due_date
                                                           iv_amount = cs_pos-betrg
                                                           iv_waers = cs_pos-waers
                                                 IMPORTING ev_amount = cs_pos-betrg
                                                           ev_subrc = yylv_subrc1 ).

    yylo_br_pbc_posting->convert_to_budget_rate( EXPORTING iv_date = cs_pos-due_date
                                                           iv_amount = cs_pos-delta_amount
                                                           iv_waers = cs_pos-currency
                                                 IMPORTING ev_amount = cs_pos-delta_amount
                                                            ev_subrc = yylv_subrc2 ).
  ENDIF.
  "4. Convert amounts to BR amounts
  "ALL PBC Documents are in USD. Even if postings are in EUR.
  IF cs_pos-waers = 'USD'.
    yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date =  cs_pos-due_date
                                                                 iv_foreign_amount = cs_pos-betrg
                                                                 iv_foreign_currency = cs_pos-waers " Transaction Currency
                                                                 iv_local_currency = 'USD'   " Local Currency
                                                       IMPORTING ev_local_amount = cs_pos-betrg
                                                                 ev_subrc = yylv_subrc2  ).

    yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date =  cs_pos-due_date
                                                              iv_foreign_amount = cs_pos-delta_amount
                                                              iv_foreign_currency = cs_pos-waers " Transaction Currency
                                                              iv_local_currency = 'USD'   " Local Currency
                                                    IMPORTING ev_local_amount = cs_pos-delta_amount
                                                              ev_subrc = yylv_subrc1  ).
  ENDIF.
  "5. Save modifications in trace table
  IF yylv_subrc1 = 0 OR yylv_subrc2 = 0.
    CALL FUNCTION 'Y_FM_UPDATE_BR_FM_POS' IN UPDATE TASK
      EXPORTING
        is_pos_before = yyls_pos_before
        is_pos_after  = cs_pos
      EXCEPTIONS
        error_update  = 1
        OTHERS        = 2.
  ENDIF.

ENDENHANCEMENT.
