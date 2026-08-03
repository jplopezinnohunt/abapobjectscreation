ENHANCEMENT 1  .
      DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
      DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
      DATA YYLV_SUBRC TYPE SY-SUBRC.
      DATA I_CONVFACTOR TYPE EKKO-WKURS.
      DATA I0_TRBTRREDU TYPE FMIOI-TRBTR.
      DATA I_TRBTRREDU TYPE FMIOI-TRBTR.

      YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

      IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
*Start of BR Non Staff Logic ----->START
        IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_RLDNR = C_F_FMOI-RLDNR
                                                    IV_FIKRS = C_F_FMOI-FIKRS
                                                    IV_GSBER = C_F_FMOI-BUS_AREA
                                                    IV_WAERS = C_F_FMOI-TWAER
                                                    IV_FIPEX = C_F_FMOI-FIPEX
                                                    IV_VRGNG = C_F_FMOI-VRGNG
                                                    IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = C_F_FMOI-FIKRS IV_FINCODE = C_F_FMOI-FONDS ) ) = ABAP_TRUE.


*11/08/2025 Transaction Reduction different Exchante rate
C_F_FMOI-TRBTRREDU = C_F_FMOI-TRBTRREDU + C_F_FMOI-TRBTRADJST.
C_F_FMOI-FKBTRADJST = 0.
C_F_FMOI-TRBTRADJST = 0.
*End change 11/08/25

*Recalculate reduction c_f_fmoi-TRBTRREDU
*FKBTRREDU REduction in USD
*TRBTRREDU Reduction in EUR. Should be transaction in EUR. This euros are calculated From the M USD to EUR
*Get Conversion Factor from EKKO is an option too
          IF C_F_FMOI-REVSUM <> 0.
            I_CONVFACTOR = C_F_FMOI-TRBTRORIG / C_F_FMOI-FKBTRORIG.
            I0_TRBTRREDU = ( C_F_FMOI-FKBTRREDU + C_F_FMOI-REVSUM + C_F_FMOI-FKBTRADJST ).
            I_TRBTRREDU = I0_TRBTRREDU * I_CONVFACTOR.
            C_F_FMOI-TRBTRREDU = I_TRBTRREDU.
          ENDIF.
*End recalculation reduction

          YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG
                                                                IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                IV_LOCAL_CURRENCY = 'USD'
                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                EV_SUBRC = YYLV_SUBRC ).
          IF YYLV_SUBRC = 0.
            C_F_FMOI-FKBTRORIG = YYLV_AMOUNT.
            C_F_FMOI-SPLIT = YYLV_AMOUNT.
            CLEAR YYLV_AMOUNT.
          ENDIF.

          YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG_MAX
                                                                IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                IV_LOCAL_CURRENCY = 'USD'
                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                EV_SUBRC = YYLV_SUBRC ).
          IF YYLV_SUBRC = 0.
            C_F_FMOI-FKBTRORIG_MAX = YYLV_AMOUNT.
            CLEAR YYLV_AMOUNT.
          ENDIF.

          IF  C_F_FMOI-TRBTRREDU <> 0.
            YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                   IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRREDU
                                                                   IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                   IV_LOCAL_CURRENCY = 'USD'
                                                         IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                   EV_SUBRC = YYLV_SUBRC ).
            C_F_FMOI-FKBTRREDU = YYLV_AMOUNT.
            CLEAR YYLV_AMOUNT.
          ENDIF.

*Liquidation
*START OF 18/07/2025 Add F Do not generate difference for transaction Reductions
          IF C_F_FMOI-ERLKZ = 'X' OR C_F_FMOI-ERLKZ = 'F'.
*            IF sy-tcode NE 'FMN4N'.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                                IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRADJST
                                                                                IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                                IV_LOCAL_CURRENCY = 'USD'
                                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                                EV_SUBRC = YYLV_SUBRC ).
              C_F_FMOI-FKBTRADJST = YYLV_AMOUNT.
*SATART OF 30/04/2025 Do not generate difference for transaction Reductions
*           c_f_fmoi-trbtrredu  = c_f_fmoi-trbtrorig.
*            c_f_fmoi-fkbtrredu =   c_f_fmoi-fkbtrorig.
*            CLEAR c_f_fmoi-trbtradjst.
*            CLEAR c_f_fmoi-fkbtradjst.
*END OF ADJUSTMENT 30/04/2025 Do not generate difference for transaction Reductions
            ELSE.
              CLEAR C_F_FMOI-TRBTRADJST.
              CLEAR C_F_FMOI-FKBTRADJST.
*            ENDIF.
          ENDIF.

          CLEAR C_F_FMOI-REVSUM.

        ENDIF.

*END of BR Non Staff Logic ----->END

        IF 1 = 2. "Staff Logic on Hold
*Start of BR  Staff Logic ----->START
          IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_2( IV_RLDNR   = C_F_FMOI-RLDNR     "Ledger
                                                          IV_FIKRS = C_F_FMOI-FIKRS     "FM Area
                                                          IV_GSBER = C_F_FMOI-BUS_AREA  "Business Area
                                                          IV_WAERS = C_F_FMOI-TWAER     "Currency
                                                          IV_FIPEX = C_F_FMOI-FIPEX     "Commitment item
                                                          IV_VRGNG = C_F_FMOI-VRGNG     "Business Area
                                                          "Pesonal Check
                                                          "HKONT check

                                                          IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = C_F_FMOI-FIKRS IV_FINCODE = C_F_FMOI-FONDS ) ) = ABAP_TRUE.
            "Fund type
*Recalculate reduction c_f_fmoi-TRBTRREDU
*FKBTRREDU Reduction in USD UNORE WIll Be converted to USD BR
*TRBTRREDU Reduction in EUR. Should be transaction in EUR. This euros are calculated From the M USD to EUR

            IF C_F_FMOI-REVSUM <> 0.
              I_CONVFACTOR = C_F_FMOI-TRBTRORIG / C_F_FMOI-FKBTRORIG.
              I0_TRBTRREDU = ( C_F_FMOI-FKBTRREDU + C_F_FMOI-REVSUM + C_F_FMOI-FKBTRADJST ).
              I_TRBTRREDU = I0_TRBTRREDU * I_CONVFACTOR.
              C_F_FMOI-TRBTRREDU = I_TRBTRREDU.
            ENDIF.
*End recalculation reduction
            IF C_F_FMOI-TWAER = 'EUR'.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                    IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG
                                                                    IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                    IV_LOCAL_CURRENCY = 'USD'
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                C_F_FMOI-FKBTRORIG = YYLV_AMOUNT.
                C_F_FMOI-SPLIT = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                    IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG_MAX
                                                                    IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                    IV_LOCAL_CURRENCY = 'USD'
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                C_F_FMOI-FKBTRORIG_MAX = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

              IF  C_F_FMOI-TRBTRREDU <> 0.
                YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                       IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRREDU
                                                                       IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                       IV_LOCAL_CURRENCY = 'USD'
                                                             IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                       EV_SUBRC = YYLV_SUBRC ).
                C_F_FMOI-FKBTRREDU = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

*Liquidation
              IF C_F_FMOI-ERLKZ = 'X'.
                YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                                  IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRADJST
                                                                                  IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                                  IV_LOCAL_CURRENCY = 'USD'
                                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                                  EV_SUBRC = YYLV_SUBRC ).
                C_F_FMOI-FKBTRADJST = YYLV_AMOUNT.
              ELSE.
                CLEAR C_F_FMOI-TRBTRADJST.
                CLEAR C_F_FMOI-FKBTRADJST.
              ENDIF.
              CLEAR C_F_FMOI-REVSUM.

*****Convert USD UNORE to USD Budget rate
            ELSEIF C_F_FMOI-TWAER = 'USD'.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                 IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG
                                                                 IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                 IV_LOCAL_CURRENCY = 'USD'
                                                       IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                 EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                C_F_FMOI-FKBTRORIG = YYLV_AMOUNT.
                C_F_FMOI-SPLIT = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                    IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRORIG_MAX
                                                                    IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                    IV_LOCAL_CURRENCY = 'USD'
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                C_F_FMOI-FKBTRORIG_MAX = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

              IF  C_F_FMOI-TRBTRREDU <> 0.
                YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                       IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRREDU
                                                                       IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                       IV_LOCAL_CURRENCY = 'USD'
                                                             IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                       EV_SUBRC = YYLV_SUBRC ).
                C_F_FMOI-FKBTRREDU = YYLV_AMOUNT.
                CLEAR YYLV_AMOUNT.
              ENDIF.

*Liquidation
              IF C_F_FMOI-ERLKZ = 'X'.
                YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = C_F_FMOI-BUDAT
                                                                                  IV_FOREIGN_AMOUNT = C_F_FMOI-TRBTRADJST
                                                                                  IV_FOREIGN_CURRENCY = C_F_FMOI-TWAER
                                                                                  IV_LOCAL_CURRENCY = 'USD'
                                                                        IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                                  EV_SUBRC = YYLV_SUBRC ).
                C_F_FMOI-FKBTRADJST = YYLV_AMOUNT.
              ELSE.
                CLEAR C_F_FMOI-TRBTRADJST.
                CLEAR C_F_FMOI-FKBTRADJST.
              ENDIF.
              CLEAR C_F_FMOI-REVSUM.


            ENDIF. "Currency

          ENDIF.

*END of BR  Staff Logic ----->END
        ENDIF. "Staff Logic on Hold
      ENDIF.

ENDENHANCEMENT.