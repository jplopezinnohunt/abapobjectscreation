ENHANCEMENT 1  .
DATA YYLT_ADDREF_SAVE TYPE FMEF_REFDATA_TT.
DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
DATA YYLV_SUBRC TYPE SY-SUBRC.
DATA YYLV_UPD_DONE TYPE XFELD.

"Save table M_T_ADDREF to restore at the end of method
YYLT_ADDREF_SAVE = M_T_ADDREF.
"Get data from KBLK

"Check and set amount to Fix rate constant dollar
YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

*Start of BR Non Staff Logic ----->START
IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
  LOOP AT M_T_ADDREF ASSIGNING FIELD-SYMBOL(<YYLS_ADDREF>).
    CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_BUKRS = <YYLS_ADDREF>-REF-BUKRS
                                                   IV_FIKRS = M_R_DOC->M_F_KBLK-FIKRS
                                                   IV_GSBER = M_F_KBLP-GSBER
                                                   IV_WAERS = M_R_DOC->M_F_KBLK-WAERS
                                                   IV_FIPEX = M_F_KBLP-FIPEX
                                                   IV_VRGNG = M_F_KBLP-VRGNG
                                                   IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = M_R_DOC->M_F_KBLK-FIKRS IV_FINCODE = M_F_KBLP-GEBER ) ) = ABAP_TRUE.
    YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_ADDREF>-REF-BUDAT
                                                          IV_FOREIGN_AMOUNT = <YYLS_ADDREF>-REF-WTGES
                                                          IV_FOREIGN_CURRENCY = <YYLS_ADDREF>-REF-WAERS
                                                          IV_LOCAL_CURRENCY = 'USD'
                                                IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                          EV_SUBRC = YYLV_SUBRC ).
    IF YYLV_SUBRC = 0.
      <YYLS_ADDREF>-REF-HWGES = YYLV_AMOUNT.
      YYLV_UPD_DONE = ABAP_TRUE.
    ENDIF.
    YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_ADDREF>-REF-BUDAT
                                                          IV_FOREIGN_AMOUNT = <YYLS_ADDREF>-REF-WTGESAPP
                                                          IV_FOREIGN_CURRENCY = <YYLS_ADDREF>-REF-WAERS
                                                          IV_LOCAL_CURRENCY = 'USD'
                                                IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                          EV_SUBRC = YYLV_SUBRC ).
    IF YYLV_SUBRC = 0.
      <YYLS_ADDREF>-REF-HWGESAPP = YYLV_AMOUNT.
      YYLV_UPD_DONE = ABAP_TRUE.
    ENDIF.
  ENDLOOP.
*END of BR Non Staff Logic ----->END
  IF 1 = 2. "Staff logic on hold.
*START of BR STAFF Logic ----->START
    LOOP AT M_T_ADDREF ASSIGNING FIELD-SYMBOL(<YYLS_ADDREF2>).
      CHECK YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_2( IV_BUKRS = <YYLS_ADDREF2>-REF-BUKRS  "Companyh Code
                                                     IV_FIKRS = M_R_DOC->M_F_KBLK-FIKRS   "FM Area
                                                     IV_GSBER = M_F_KBLP-GSBER            "Business Area
                                                     IV_WAERS = M_R_DOC->M_F_KBLK-WAERS   "Currency
                                                     IV_FIPEX = M_F_KBLP-FIPEX            "Commitment Item
                                                     IV_VRGNG = M_F_KBLP-VRGNG            "Business transaction.
                                                     "ADDHKONT
                                                     "PERSONAL CHECK
                                    IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = M_R_DOC->M_F_KBLK-FIKRS IV_FINCODE = M_F_KBLP-GEBER ) )
                                    = ABAP_TRUE. " FUND TYPE



      IF <YYLS_ADDREF2>-REF-WAERS = 'EUR'.
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_ADDREF2>-REF-BUDAT
                                                              IV_FOREIGN_AMOUNT = <YYLS_ADDREF2>-REF-WTGES
                                                              IV_FOREIGN_CURRENCY = <YYLS_ADDREF2>-REF-WAERS
                                                              IV_LOCAL_CURRENCY = 'USD'
                                                    IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <YYLS_ADDREF2>-REF-HWGES = YYLV_AMOUNT.
          YYLV_UPD_DONE = ABAP_TRUE.
        ENDIF.
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = <YYLS_ADDREF2>-REF-BUDAT
                                                              IV_FOREIGN_AMOUNT = <YYLS_ADDREF2>-REF-WTGESAPP
                                                              IV_FOREIGN_CURRENCY = <YYLS_ADDREF2>-REF-WAERS
                                                              IV_LOCAL_CURRENCY = 'USD'
                                                    IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <YYLS_ADDREF2>-REF-HWGESAPP = YYLV_AMOUNT.
          YYLV_UPD_DONE = ABAP_TRUE.
        ENDIF.

* COnvert USD UNORE to USD BR
      ELSEIF <YYLS_ADDREF2>-REF-WAERS = 'USD'.
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = <YYLS_ADDREF2>-REF-BUDAT
                                                             IV_FOREIGN_AMOUNT = <YYLS_ADDREF2>-REF-WTGES
                                                             IV_FOREIGN_CURRENCY = <YYLS_ADDREF2>-REF-WAERS "Transaction Currency
                                                             IV_LOCAL_CURRENCY = 'USD'
                                                   IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                             EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <YYLS_ADDREF2>-REF-HWGES = YYLV_AMOUNT.
          YYLV_UPD_DONE = ABAP_TRUE.
        ENDIF.
        YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY_2( EXPORTING IV_DATE = <YYLS_ADDREF2>-REF-BUDAT
                                                              IV_FOREIGN_AMOUNT = <YYLS_ADDREF2>-REF-WTGESAPP "Transaction Currency
                                                              IV_FOREIGN_CURRENCY = <YYLS_ADDREF2>-REF-WAERS
                                                              IV_LOCAL_CURRENCY = 'USD'
                                                    IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                              EV_SUBRC = YYLV_SUBRC ).
        IF YYLV_SUBRC = 0.
          <YYLS_ADDREF2>-REF-HWGESAPP = YYLV_AMOUNT.
          YYLV_UPD_DONE = ABAP_TRUE.
        ENDIF.


      ENDIF. " Currency EUR or USD
    ENDLOOP.
*END of BR Staff Logic ----->END
  ENDIF. "Staff logic on hold.
ENDIF.
ENDENHANCEMENT.
ENHANCEMENT 2  .
IF YYLT_ADDREF_SAVE IS NOT INITIAL AND YYLV_UPD_DONE = ABAP_TRUE.
  M_T_ADDREF = YYLT_ADDREF_SAVE.
ENDIF.
ENDENHANCEMENT.