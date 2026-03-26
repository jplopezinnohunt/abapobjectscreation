ENHANCEMENT 1  .
      DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
      DATA yylv_amount TYPE resab-dmbtr.
      DATA yylv_subrc TYPE sy-subrc.

      yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
      IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
*Start of BR Non Staff Logic ----->START
        LOOP AT t_reftab ASSIGNING FIELD-SYMBOL(<yyls_reftab>).
          CHECK yylo_br_exchange_rate->check_conditions( iv_rldnr = u_f_acchd-rldnr          " Ledger
                                                         iv_fikrs = u_f_accit-fikrs            " FM Area
                                                         iv_gsber = u_f_accit-gsber            " BUsiness Area
                                                         iv_waers = <yyls_reftab>-waers        " Transaction Currency
                                                         iv_fipex = |{ u_f_accit-fipos }|      " Commitment Item
                                                         iv_vrgng = <yyls_reftab>-vrgng        " Business Transaction
                                                         iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = u_f_accit-fikrs iv_fincode = u_f_accit-geber ) ) = abap_true.
          CLEAR yylv_amount.
          yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_reftab>-budat
                                                                iv_foreign_amount = <yyls_reftab>-wtges
                                                                iv_foreign_currency = <yyls_reftab>-waers  " Transaction Currency
                                                                iv_local_currency = <yyls_reftab>-hwaer    " Local Currency
                                                      IMPORTING ev_local_amount = yylv_amount
                                                                ev_subrc = yylv_subrc ).
          IF yylv_subrc = 0.
            <yyls_reftab>-hwges = yylv_amount.
          ENDIF.
          CLEAR yylv_amount.
          yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_reftab>-budat
                                                                iv_foreign_amount = <yyls_reftab>-wtgesapp
                                                                iv_foreign_currency = <yyls_reftab>-waers
                                                                iv_local_currency = <yyls_reftab>-hwaer
                                                      IMPORTING ev_local_amount = yylv_amount
                                                                ev_subrc = yylv_subrc ).
          IF yylv_subrc = 0.
            <yyls_reftab>-hwgesapp = yylv_amount.
          ENDIF.
        ENDLOOP.

****END of BR Non Staff Logic      <-----END
        IF 1 = 2. "Staff Logic on hold.
*Start of BR  Staff Logic ----->START
*1 Check If are Payrrol Transactions
          LOOP AT t_reftab ASSIGNING FIELD-SYMBOL(<yyls_reftab2>).
            CHECK yylo_br_exchange_rate->check_conditions_2( iv_rldnr = u_f_acchd-rldnr          " Ledger
                                                           iv_fikrs = u_f_accit-fikrs          " FM Area
                                                           iv_gsber = u_f_accit-gsber          " BUsiness Area
                                                           iv_waers = <yyls_reftab2>-waers     " Transaction Currency
*                                                       iv_fipex = |{ u_f_accit-fipos }|    " Commitment Item
                                                           iv_vrgng = <yyls_reftab2>-vrgng     " Business Transaction
                                                           "PESON APPLICABILITY CONDITION OR SIMILAR
                                                           iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = u_f_accit-fikrs iv_fincode = u_f_accit-geber ) )
                                                            = abap_true.

            CLEAR yylv_amount.
*2 Amount Conversion based on Currency
*2.1 EUR UNORE to USD BR

            IF <yyls_reftab2>-waers  = 'EUR'.
              yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_reftab>-budat
                                                                    iv_foreign_amount = <yyls_reftab2>-wtges
                                                                    iv_foreign_currency = <yyls_reftab2>-waers " Transaction Currency
                                                                    iv_local_currency = <yyls_reftab2>-hwaer   " Local Currency
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                <yyls_reftab2>-hwges = yylv_amount.
              ENDIF.
              CLEAR yylv_amount.
              yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = <yyls_reftab2>-budat
                                                                    iv_foreign_amount = <yyls_reftab2>-wtgesapp
                                                                    iv_foreign_currency = <yyls_reftab2>-waers
                                                                    iv_local_currency = <yyls_reftab2>-hwaer
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                <yyls_reftab2>-hwgesapp = yylv_amount.
              ENDIF.
*2.2 USD UNORE to USD BR
            ELSEIF   <yyls_reftab2>-waers  = 'USD'.

              yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = <yyls_reftab>-budat
                                                                    iv_foreign_amount = <yyls_reftab2>-wtges
                                                                    iv_foreign_currency = <yyls_reftab2>-waers " Transaction Currency
                                                                    iv_local_currency = <yyls_reftab2>-hwaer   " Local Currency
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                <yyls_reftab2>-hwges = yylv_amount.
              ENDIF.
              CLEAR yylv_amount.
              yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = <yyls_reftab2>-budat
                                                                    iv_foreign_amount = <yyls_reftab2>-wtgesapp
                                                                    iv_foreign_currency = <yyls_reftab2>-waers
                                                                    iv_local_currency = <yyls_reftab2>-hwaer
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                <yyls_reftab2>-hwgesapp = yylv_amount.
              ENDIF.

            ENDIF.
          ENDLOOP.
****END of BR Staff Logic      <-----END
        ENDIF. "Staff Logic on hold

      ENDIF.

ENDENHANCEMENT.
