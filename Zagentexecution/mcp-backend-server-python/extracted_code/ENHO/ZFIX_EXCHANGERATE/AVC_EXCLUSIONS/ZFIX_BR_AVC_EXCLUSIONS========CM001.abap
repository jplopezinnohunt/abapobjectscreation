  method IF_EX_FMAVC_ENTRY_FILTER~BUDGET_FILTER.
    DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
    DATA yylv_amount TYPE fmifiit-fkbtr.
    DATA yylv_subrc TYPE sy-subrc.
    DATA yyls_avc_fund TYPE ycl_fm_br_exchange_rate_bl=>ty_avc_fund.
    DATA yylo_br_payroll_posting_bl TYPE REF TO ycl_fm_br_payroll_posting_bl.
    DATA yyls_account_gl TYPE bapiacgl04.
    DATA yyls_account_amount TYPE bapiaccr04.

*For BR Skyp AVC as the values are the Same in USD.
    yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
    yylo_br_payroll_posting_bl = ycl_fm_br_payroll_posting_bl=>get_instance( ).

    IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
      If sy-tcode = 'MIRO' or sy-tcode = 'F110'.
        E_FLG_SKIP_ENTRY = 'X'.
    endif.
    Endif.
  endmethod.