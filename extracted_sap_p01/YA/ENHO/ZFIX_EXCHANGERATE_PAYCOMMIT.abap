ENHANCEMENT 1  .
      DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
      DATA YYLV_AMOUNT TYPE RESAB-DMBTR.
      DATA YYLV_SUBRC TYPE SY-SUBRC.

      YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
      IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
*Start of BR Non Staff Logic ----->START
        LOOP AT T_REFTAB ASSIGNING FIELD-SYMBOL(<YYLS_REFTAB>).
          CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_RLDNR = U_F_ACCHD-RLDNR          " Ledger
                                                         IV_FIKRS = U_F_ACCIT-FIKRS            " FM Area
                                                         IV_GSBER = U_F_ACCIT-GSBER            " BUsiness Area
                                                         IV_WAERS = <YYLS_REFTAB>-WAERS        " Transaction Currency
                                                         IV_FIPEX = |{ U_F_ACCIT-FIPOS }|      " Commitment Item
                                                         IV_VRGNG = <YYLS_REFTAB>-VRGNG        " Business Transaction
                                                         IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = U_F_ACCIT-FIKRS IV_FINCODE = U_F_ACCIT-GEBER ) ) = ABAP_TRUE.
          CLEAR YYLV_AMOUNT.
          YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_REFTAB>-BUDAT
                                                                IV_FOREIGN_AMOUNT = <YYLS_REFTAB>-WTGES
                                                                IV_FOREIGN_CURRENCY = <YYLS_REFTAB>-WAERS  " Transaction Currency
                                                                IV_LOCAL_CURRENCY = <YYLS_REFTAB>-HWAER    " Local Currency
                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                EV_SUBRC = YYLV_SUBRC ).
          IF YYLV_SUBRC = 0.
            <YYLS_REFTAB>-HWGES = YYLV_AMOUNT.
          ENDIF.
          CLEAR YYLV_AMOUNT.
          YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_REFTAB>-BUDAT
                                                                IV_FOREIGN_AMOUNT = <YYLS_REFTAB>-WTGESAPP
                                                                IV_FOREIGN_CURRENCY = <YYLS_REFTAB>-WAERS
                                                                IV_LOCAL_CURRENCY = <YYLS_REFTAB>-HWAER
                                                      IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                EV_SUBRC = YYLV_SUBRC ).
          IF YYLV_SUBRC = 0.
            <YYLS_REFTAB>-HWGESAPP = YYLV_AMOUNT.
          ENDIF.
        ENDLOOP.

****END of BR Non Staff Logic      <-----END
        IF 1 = 2. "Staff Logic on hold.
*Start of BR  Staff Logic ----->START
*1 Check If are Payrrol Transactions
          LOOP AT T_REFTAB ASSIGNING FIELD-SYMBOL(<YYLS_REFTAB2>).
            CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_2( IV_RLDNR = U_F_ACCHD-RLDNR          " Ledger
                                                           IV_FIKRS = U_F_ACCIT-FIKRS          " FM Area
                                                           IV_GSBER = U_F_ACCIT-GSBER          " BUsiness Area
                                                           IV_WAERS = <YYLS_REFTAB2>-WAERS     " Transaction Currency
*                                                       iv_fipex = |{ u_f_accit-fipos }|    " Commitment Item
                                                           IV_VRGNG = <YYLS_REFTAB2>-VRGNG     " Business Transaction
                                                           "PESON APPLICABILITY CONDITION OR SIMILAR
                                                           IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = U_F_ACCIT-FIKRS IV_FINCODE = U_F_ACCIT-GEBER ) )
                                                            = ABAP_TRUE.

            CLEAR YYLV_AMOUNT.
*2 Amount Conversion based on Currency
*2.1 EUR UNORE to USD BR

            IF <YYLS_REFTAB2>-WAERS  = 'EUR'.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_REFTAB>-BUDAT
                                                                    IV_FOREIGN_AMOUNT = <YYLS_REFTAB2>-WTGES
                                                                    IV_FOREIGN_CURRENCY = <YYLS_REFTAB2>-WAERS " Transaction Currency
                                                                    IV_LOCAL_CURRENCY = <YYLS_REFTAB2>-HWAER   " Local Currency
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                <YYLS_REFTAB2>-HWGES = YYLV_AMOUNT.
              ENDIF.
              CLEAR YYLV_AMOUNT.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_REFTAB2>-BUDAT
                                                                    IV_FOREIGN_AMOUNT = <YYLS_REFTAB2>-WTGESAPP
                                                                    IV_FOREIGN_CURRENCY = <YYLS_REFTAB2>-WAERS
                                                                    IV_LOCAL_CURRENCY = <YYLS_REFTAB2>-HWAER
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                <YYLS_REFTAB2>-HWGESAPP = YYLV_AMOUNT.
              ENDIF.
*2.2 USD UNORE to USD BR
            ELSEIF   <YYLS_REFTAB2>-WAERS  = 'USD'.

              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = <YYLS_REFTAB>-BUDAT
                                                                    IV_FOREIGN_AMOUNT = <YYLS_REFTAB2>-WTGES
                                                                    IV_FOREIGN_CURRENCY = <YYLS_REFTAB2>-WAERS " Transaction Currency
                                                                    IV_LOCAL_CURRENCY = <YYLS_REFTAB2>-HWAER   " Local Currency
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                <YYLS_REFTAB2>-HWGES = YYLV_AMOUNT.
              ENDIF.
              CLEAR YYLV_AMOUNT.
              YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = <YYLS_REFTAB2>-BUDAT
                                                                    IV_FOREIGN_AMOUNT = <YYLS_REFTAB2>-WTGESAPP
                                                                    IV_FOREIGN_CURRENCY = <YYLS_REFTAB2>-WAERS
                                                                    IV_LOCAL_CURRENCY = <YYLS_REFTAB2>-HWAER
                                                          IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                                    EV_SUBRC = YYLV_SUBRC ).
              IF YYLV_SUBRC = 0.
                <YYLS_REFTAB2>-HWGESAPP = YYLV_AMOUNT.
              ENDIF.

            ENDIF.
          ENDLOOP.
****END of BR Staff Logic      <-----END
        ENDIF. "Staff Logic on hold

      ENDIF.

ENDENHANCEMENT.