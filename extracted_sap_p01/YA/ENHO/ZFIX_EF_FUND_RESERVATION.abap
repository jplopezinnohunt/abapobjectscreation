ENHANCEMENT 2  .
 "Update tables Fund Reservation During transaction Execution
 DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
 DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
 DATA YYLV_SUBRC TYPE SY-SUBRC.
 DATA I_CONVFACTOR TYPE EKKO-WKURS.
 DATA I0_TRBTRREDU TYPE FMIOI-TRBTR.
 DATA I_TRBTRREDU TYPE FMIOI-TRBTR.

 YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).

 IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.
   LOOP AT T_KBLP INTO DATA(V_T_KBLP).
     "Start of BR Non Staff Logic ----->START
     IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FIKRS = T_KBLK-FIKRS
                                                 IV_GSBER = V_T_KBLP-GSBER
                                                 IV_WAERS = T_KBLK-WAERS
                                                 IV_FIPEX = V_T_KBLP-FIPEX
                                                 IV_VRGNG = V_T_KBLP-VRGNG
                                                 IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND( IV_FIKRS = T_KBLK-FIKRS
                                                                                                            IV_FINCODE = V_T_KBLP-GEBER ) ) = ABAP_TRUE.
       CLEAR YYLV_AMOUNT.
       YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = T_KBLK-BUDAT
                                                             IV_FOREIGN_AMOUNT = V_T_KBLP-WTGES
                                                             IV_FOREIGN_CURRENCY = T_KBLK-WAERS  " Transaction Currency
                                                             IV_LOCAL_CURRENCY = T_KBLK-HWAER    " Local Currency
                                                   IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                             EV_SUBRC = YYLV_SUBRC ).
       IF YYLV_SUBRC = 0.
         T_KBLP-HWGES = YYLV_AMOUNT.
       ENDIF.

       CLEAR YYLV_AMOUNT.
       YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = T_KBLK-BUDAT
                                                             IV_FOREIGN_AMOUNT = V_T_KBLP-WTGESAPP
                                                             IV_FOREIGN_CURRENCY = T_KBLK-WAERS
                                                             IV_LOCAL_CURRENCY = T_KBLK-HWAER
                                                   IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                             EV_SUBRC = YYLV_SUBRC ).
       IF YYLV_SUBRC = 0.
         T_KBLP-HWGESAPP = YYLV_AMOUNT.
       ENDIF.
     ENDIF.
   ENDLOOP.
 ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
 "Update KLBP during reconstruction Program RFFMREPO
*Reconstruction does not revaluate, update the right values for BR

 DATA YYLO_BR_EXCHANGE_RATE TYPE REF TO YCL_FM_BR_EXCHANGE_RATE_BL.
 DATA YYLV_AMOUNT TYPE FMIOI-FKBTR.
 DATA YYLV_SUBRC TYPE SY-SUBRC.

 IF SY-CPROG = 'RFFMREPO'.
   YYLO_BR_EXCHANGE_RATE = YCL_FM_BR_EXCHANGE_RATE_BL=>GET_INSTANCE( ).
   IF YYLO_BR_EXCHANGE_RATE->CHECK_BR_IS_ACTIVE( ) = ABAP_TRUE.

     LOOP AT T_KBLP INTO DATA(V_T_KBLP2).

       "Delete Lines not applicable for BR Reconstruction
       IF  V_T_KBLP2-LOEKZ = 'X'.
         DELETE T_KBLP.
       ELSEIF  V_T_KBLP2-GSBER NE 'GEF'.
         DELETE T_KBLP.
       ELSEIF  YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_3( IV_FIPEX = V_T_KBLP2-FIPEX ) = ABAP_TRUE.
         DELETE T_KBLP.
       ELSEIF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_3( IV_VRGNG = V_T_KBLP2-VRGNG ) = ABAP_TRUE.
         DELETE T_KBLP.
       ELSEIF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS_3( IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
                                                         IV_FIKRS = T_KBLK-FIKRS
                                                         IV_FINCODE = V_T_KBLP2-GEBER ) ) = ABAP_TRUE.
         DELETE T_KBLP.
       ENDIF.
     ENDLOOP.

     "Reconstruct LInes affected By BR>
     LOOP AT T_KBLP INTO DATA(V_T_KBLP).

*Start of BR Non Staff Logic ----->START
       IF YYLO_BR_EXCHANGE_RATE->CHECK_CONDITIONS( IV_FIKRS = T_KBLK-FIKRS
                                                   IV_GSBER = V_T_KBLP-GSBER
                                                   IV_WAERS = T_KBLK-WAERS
                                                   IV_FIPEX = V_T_KBLP-FIPEX
                                                   IV_VRGNG = V_T_KBLP-VRGNG
                                                   IV_FTYPE = YYLO_BR_EXCHANGE_RATE->GET_FUND_TYPE_FROM_FUND(
       IV_FIKRS = T_KBLK-FIKRS
        IV_FINCODE = V_T_KBLP-GEBER ) ) = ABAP_TRUE.

         CLEAR YYLV_AMOUNT.
         YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = T_KBLK-BUDAT
                                                               IV_FOREIGN_AMOUNT = V_T_KBLP-WTGES
                                                               IV_FOREIGN_CURRENCY = T_KBLK-WAERS  " Transaction Currency
                                                               IV_LOCAL_CURRENCY = T_KBLK-HWAER    " Local Currency
                                                     IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                               EV_SUBRC = YYLV_SUBRC ).
         IF YYLV_SUBRC = 0.
           V_T_KBLP-HWGES = YYLV_AMOUNT.
         ENDIF.

         CLEAR YYLV_AMOUNT.
         YYLO_BR_EXCHANGE_RATE->CONVERT_TO_CURRENCY( EXPORTING IV_DATE = T_KBLK-BUDAT
                                                               IV_FOREIGN_AMOUNT = V_T_KBLP-WTGESAPP
                                                               IV_FOREIGN_CURRENCY = T_KBLK-WAERS
                                                               IV_LOCAL_CURRENCY = T_KBLK-HWAER
                                                     IMPORTING EV_LOCAL_AMOUNT = YYLV_AMOUNT
                                                               EV_SUBRC = YYLV_SUBRC ).
         IF YYLV_SUBRC = 0.
           V_T_KBLP-HWGESAPP = YYLV_AMOUNT.
         ENDIF.
         MODIFY T_KBLP FROM V_T_KBLP.
       ENDIF.
     ENDLOOP.
   ENDIF.
 ENDIF.
ENDENHANCEMENT.