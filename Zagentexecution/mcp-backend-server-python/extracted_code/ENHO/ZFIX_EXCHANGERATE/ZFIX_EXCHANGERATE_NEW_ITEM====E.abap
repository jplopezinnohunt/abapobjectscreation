ENHANCEMENT 1  .
      DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
      DATA yylv_amount TYPE fmioi-fkbtr.
      DATA yylv_subrc TYPE sy-subrc.
      DATA i_convfactor TYPE ekko-wkurs.
      DATA i0_trbtrredu TYPE fmioi-trbtr.
      DATA i_trbtrredu TYPE fmioi-trbtr.

      yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

      IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
*Start of BR Non Staff Logic ----->START
        IF yylo_br_exchange_rate->check_conditions( iv_rldnr = c_f_fmoi-rldnr
                                                    iv_fikrs = c_f_fmoi-fikrs
                                                    iv_gsber = c_f_fmoi-bus_area
                                                    iv_waers = c_f_fmoi-twaer
                                                    iv_fipex = c_f_fmoi-fipex
                                                    iv_vrgng = c_f_fmoi-vrgng
                                                    iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = c_f_fmoi-fikrs iv_fincode = c_f_fmoi-fonds ) ) = abap_true.


*11/08/2025 Transaction Reduction different Exchante rate
c_f_fmoi-TRBTRREDU = c_f_fmoi-TRBTRREDU + c_f_fmoi-TRBTRADJST.
c_f_fmoi-FKBTRADJST = 0.
c_f_fmoi-TRBTRADJST = 0.
*End change 11/08/25

*Recalculate reduction c_f_fmoi-TRBTRREDU
*FKBTRREDU REduction in USD
*TRBTRREDU Reduction in EUR. Should be transaction in EUR. This euros are calculated From the M USD to EUR
*Get Conversion Factor from EKKO is an option too
          IF c_f_fmoi-revsum <> 0.
            i_convfactor = c_f_fmoi-trbtrorig / c_f_fmoi-fkbtrorig.
            i0_trbtrredu = ( c_f_fmoi-fkbtrredu + c_f_fmoi-revsum + c_f_fmoi-fkbtradjst ).
            i_trbtrredu = i0_trbtrredu * i_convfactor.
            c_f_fmoi-trbtrredu = i_trbtrredu.
          ENDIF.
*End recalculation reduction

          yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                iv_foreign_amount = c_f_fmoi-trbtrorig
                                                                iv_foreign_currency = c_f_fmoi-twaer
                                                                iv_local_currency = 'USD'
                                                      IMPORTING ev_local_amount = yylv_amount
                                                                ev_subrc = yylv_subrc ).
          IF yylv_subrc = 0.
            c_f_fmoi-fkbtrorig = yylv_amount.
            c_f_fmoi-split = yylv_amount.
            CLEAR yylv_amount.
          ENDIF.

          yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                iv_foreign_amount = c_f_fmoi-trbtrorig_max
                                                                iv_foreign_currency = c_f_fmoi-twaer
                                                                iv_local_currency = 'USD'
                                                      IMPORTING ev_local_amount = yylv_amount
                                                                ev_subrc = yylv_subrc ).
          IF yylv_subrc = 0.
            c_f_fmoi-fkbtrorig_max = yylv_amount.
            CLEAR yylv_amount.
          ENDIF.

          IF  c_f_fmoi-trbtrredu <> 0.
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                   iv_foreign_amount = c_f_fmoi-trbtrredu
                                                                   iv_foreign_currency = c_f_fmoi-twaer
                                                                   iv_local_currency = 'USD'
                                                         IMPORTING ev_local_amount = yylv_amount
                                                                   ev_subrc = yylv_subrc ).
            c_f_fmoi-fkbtrredu = yylv_amount.
            CLEAR yylv_amount.
          ENDIF.

*Liquidation
*START OF 18/07/2025 Add F Do not generate difference for transaction Reductions
          IF c_f_fmoi-erlkz = 'X' OR c_f_fmoi-erlkz = 'F'.
*            IF sy-tcode NE 'FMN4N'.
              yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                                iv_foreign_amount = c_f_fmoi-trbtradjst
                                                                                iv_foreign_currency = c_f_fmoi-twaer
                                                                                iv_local_currency = 'USD'
                                                                      IMPORTING ev_local_amount = yylv_amount
                                                                                ev_subrc = yylv_subrc ).
              c_f_fmoi-fkbtradjst = yylv_amount.
*SATART OF 30/04/2025 Do not generate difference for transaction Reductions
*           c_f_fmoi-trbtrredu  = c_f_fmoi-trbtrorig.
*            c_f_fmoi-fkbtrredu =   c_f_fmoi-fkbtrorig.
*            CLEAR c_f_fmoi-trbtradjst.
*            CLEAR c_f_fmoi-fkbtradjst.
*END OF ADJUSTMENT 30/04/2025 Do not generate difference for transaction Reductions
            ELSE.
              CLEAR c_f_fmoi-trbtradjst.
              CLEAR c_f_fmoi-fkbtradjst.
*            ENDIF.
          ENDIF.

          CLEAR c_f_fmoi-revsum.

        ENDIF.

*END of BR Non Staff Logic ----->END

        IF 1 = 2. "Staff Logic on Hold
*Start of BR  Staff Logic ----->START
          IF yylo_br_exchange_rate->check_conditions_2( iv_rldnr   = c_f_fmoi-rldnr     "Ledger
                                                          iv_fikrs = c_f_fmoi-fikrs     "FM Area
                                                          iv_gsber = c_f_fmoi-bus_area  "Business Area
                                                          iv_waers = c_f_fmoi-twaer     "Currency
                                                          iv_fipex = c_f_fmoi-fipex     "Commitment item
                                                          iv_vrgng = c_f_fmoi-vrgng     "Business Area
                                                          "Pesonal Check
                                                          "HKONT check

                                                          iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = c_f_fmoi-fikrs iv_fincode = c_f_fmoi-fonds ) ) = abap_true.
            "Fund type
*Recalculate reduction c_f_fmoi-TRBTRREDU
*FKBTRREDU Reduction in USD UNORE WIll Be converted to USD BR
*TRBTRREDU Reduction in EUR. Should be transaction in EUR. This euros are calculated From the M USD to EUR

            IF c_f_fmoi-revsum <> 0.
              i_convfactor = c_f_fmoi-trbtrorig / c_f_fmoi-fkbtrorig.
              i0_trbtrredu = ( c_f_fmoi-fkbtrredu + c_f_fmoi-revsum + c_f_fmoi-fkbtradjst ).
              i_trbtrredu = i0_trbtrredu * i_convfactor.
              c_f_fmoi-trbtrredu = i_trbtrredu.
            ENDIF.
*End recalculation reduction
            IF c_f_fmoi-twaer = 'EUR'.
              yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                    iv_foreign_amount = c_f_fmoi-trbtrorig
                                                                    iv_foreign_currency = c_f_fmoi-twaer
                                                                    iv_local_currency = 'USD'
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                c_f_fmoi-fkbtrorig = yylv_amount.
                c_f_fmoi-split = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

              yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                    iv_foreign_amount = c_f_fmoi-trbtrorig_max
                                                                    iv_foreign_currency = c_f_fmoi-twaer
                                                                    iv_local_currency = 'USD'
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                c_f_fmoi-fkbtrorig_max = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

              IF  c_f_fmoi-trbtrredu <> 0.
                yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                       iv_foreign_amount = c_f_fmoi-trbtrredu
                                                                       iv_foreign_currency = c_f_fmoi-twaer
                                                                       iv_local_currency = 'USD'
                                                             IMPORTING ev_local_amount = yylv_amount
                                                                       ev_subrc = yylv_subrc ).
                c_f_fmoi-fkbtrredu = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

*Liquidation
              IF c_f_fmoi-erlkz = 'X'.
                yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = c_f_fmoi-budat
                                                                                  iv_foreign_amount = c_f_fmoi-trbtradjst
                                                                                  iv_foreign_currency = c_f_fmoi-twaer
                                                                                  iv_local_currency = 'USD'
                                                                        IMPORTING ev_local_amount = yylv_amount
                                                                                  ev_subrc = yylv_subrc ).
                c_f_fmoi-fkbtradjst = yylv_amount.
              ELSE.
                CLEAR c_f_fmoi-trbtradjst.
                CLEAR c_f_fmoi-fkbtradjst.
              ENDIF.
              CLEAR c_f_fmoi-revsum.

*****Convert USD UNORE to USD Budget rate
            ELSEIF c_f_fmoi-twaer = 'USD'.
              yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = c_f_fmoi-budat
                                                                 iv_foreign_amount = c_f_fmoi-trbtrorig
                                                                 iv_foreign_currency = c_f_fmoi-twaer
                                                                 iv_local_currency = 'USD'
                                                       IMPORTING ev_local_amount = yylv_amount
                                                                 ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                c_f_fmoi-fkbtrorig = yylv_amount.
                c_f_fmoi-split = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

              yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = c_f_fmoi-budat
                                                                    iv_foreign_amount = c_f_fmoi-trbtrorig_max
                                                                    iv_foreign_currency = c_f_fmoi-twaer
                                                                    iv_local_currency = 'USD'
                                                          IMPORTING ev_local_amount = yylv_amount
                                                                    ev_subrc = yylv_subrc ).
              IF yylv_subrc = 0.
                c_f_fmoi-fkbtrorig_max = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

              IF  c_f_fmoi-trbtrredu <> 0.
                yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = c_f_fmoi-budat
                                                                       iv_foreign_amount = c_f_fmoi-trbtrredu
                                                                       iv_foreign_currency = c_f_fmoi-twaer
                                                                       iv_local_currency = 'USD'
                                                             IMPORTING ev_local_amount = yylv_amount
                                                                       ev_subrc = yylv_subrc ).
                c_f_fmoi-fkbtrredu = yylv_amount.
                CLEAR yylv_amount.
              ENDIF.

*Liquidation
              IF c_f_fmoi-erlkz = 'X'.
                yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = c_f_fmoi-budat
                                                                                  iv_foreign_amount = c_f_fmoi-trbtradjst
                                                                                  iv_foreign_currency = c_f_fmoi-twaer
                                                                                  iv_local_currency = 'USD'
                                                                        IMPORTING ev_local_amount = yylv_amount
                                                                                  ev_subrc = yylv_subrc ).
                c_f_fmoi-fkbtradjst = yylv_amount.
              ELSE.
                CLEAR c_f_fmoi-trbtradjst.
                CLEAR c_f_fmoi-fkbtradjst.
              ENDIF.
              CLEAR c_f_fmoi-revsum.


            ENDIF. "Currency

          ENDIF.

*END of BR  Staff Logic ----->END
        ENDIF. "Staff Logic on Hold
      ENDIF.

ENDENHANCEMENT.
