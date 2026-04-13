ENHANCEMENT 1  .
  DATA yylo_br_payroll_posting_bl TYPE REF TO ycl_fm_br_payroll_posting_bl.
  yylo_br_payroll_posting_bl = ycl_fm_br_payroll_posting_bl=>get_instance( ).
  yylo_br_payroll_posting_bl->set_account_data( it_accountgl = accountgl[]
                                                it_accountamount = currencyamount[] ).
ENDENHANCEMENT.