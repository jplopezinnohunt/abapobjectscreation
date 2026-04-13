ENHANCEMENT 2  .
 "Update tables Fund Reservation During transaction Execution
 DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
 DATA yylv_amount TYPE fmioi-fkbtr.
 DATA yylv_subrc TYPE sy-subrc.
 DATA i_convfactor TYPE ekko-wkurs.
 DATA i0_trbtrredu TYPE fmioi-trbtr.
 DATA i_trbtrredu TYPE fmioi-trbtr.

 yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).

 IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
   LOOP AT t_kblp INTO DATA(v_t_kblp).
     "Start of BR Non Staff Logic ----->START
     IF yylo_br_exchange_rate->check_conditions( iv_fikrs = t_kblk-fikrs
                                                 iv_gsber = v_t_kblp-gsber
                                                 iv_waers = t_kblk-waers
                                                 iv_fipex = v_t_kblp-fipex
                                                 iv_vrgng = v_t_kblp-vrgng
                                                 iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = t_kblk-fikrs
                                                                                                            iv_fincode = v_t_kblp-geber ) ) = abap_true.
       CLEAR yylv_amount.
       yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = t_kblk-budat
                                                             iv_foreign_amount = v_t_kblp-wtges
                                                             iv_foreign_currency = t_kblk-waers  " Transaction Currency
                                                             iv_local_currency = t_kblk-hwaer    " Local Currency
                                                   IMPORTING ev_local_amount = yylv_amount
                                                             ev_subrc = yylv_subrc ).
       IF yylv_subrc = 0.
         t_kblp-hwges = yylv_amount.
       ENDIF.

       CLEAR yylv_amount.
       yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = t_kblk-budat
                                                             iv_foreign_amount = v_t_kblp-wtgesapp
                                                             iv_foreign_currency = t_kblk-waers
                                                             iv_local_currency = t_kblk-hwaer
                                                   IMPORTING ev_local_amount = yylv_amount
                                                             ev_subrc = yylv_subrc ).
       IF yylv_subrc = 0.
         t_kblp-hwgesapp = yylv_amount.
       ENDIF.
     ENDIF.
   ENDLOOP.
 ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .
 "Update KLBP during reconstruction Program RFFMREPO
*Reconstruction does not revaluate, update the right values for BR

 DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
 DATA yylv_amount TYPE fmioi-fkbtr.
 DATA yylv_subrc TYPE sy-subrc.

 IF sy-cprog = 'RFFMREPO'.
   yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
   IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.

     LOOP AT t_kblp INTO DATA(v_t_kblp2).

       "Delete Lines not applicable for BR Reconstruction
       IF  v_t_kblp2-loekz = 'X'.
         DELETE t_kblp.
       ELSEIF  v_t_kblp2-gsber NE 'GEF'.
         DELETE t_kblp.
       ELSEIF  yylo_br_exchange_rate->check_conditions_3( iv_fipex = v_t_kblp2-fipex ) = abap_true.
         DELETE t_kblp.
       ELSEIF yylo_br_exchange_rate->check_conditions_3( iv_vrgng = v_t_kblp2-vrgng ) = abap_true.
         DELETE t_kblp.
       ELSEIF yylo_br_exchange_rate->check_conditions_3( iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                         iv_fikrs = t_kblk-fikrs
                                                         iv_fincode = v_t_kblp2-geber ) ) = abap_true.
         DELETE t_kblp.
       ENDIF.
     ENDLOOP.

     "Reconstruct LInes affected By BR>
     LOOP AT t_kblp INTO DATA(v_t_kblp).

*Start of BR Non Staff Logic ----->START
       IF yylo_br_exchange_rate->check_conditions( iv_fikrs = t_kblk-fikrs
                                                   iv_gsber = v_t_kblp-gsber
                                                   iv_waers = t_kblk-waers
                                                   iv_fipex = v_t_kblp-fipex
                                                   iv_vrgng = v_t_kblp-vrgng
                                                   iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
       iv_fikrs = t_kblk-fikrs
        iv_fincode = v_t_kblp-geber ) ) = abap_true.

         CLEAR yylv_amount.
         yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = t_kblk-budat
                                                               iv_foreign_amount = v_t_kblp-wtges
                                                               iv_foreign_currency = t_kblk-waers  " Transaction Currency
                                                               iv_local_currency = t_kblk-hwaer    " Local Currency
                                                     IMPORTING ev_local_amount = yylv_amount
                                                               ev_subrc = yylv_subrc ).
         IF yylv_subrc = 0.
           v_t_kblp-hwges = yylv_amount.
         ENDIF.

         CLEAR yylv_amount.
         yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = t_kblk-budat
                                                               iv_foreign_amount = v_t_kblp-wtgesapp
                                                               iv_foreign_currency = t_kblk-waers
                                                               iv_local_currency = t_kblk-hwaer
                                                     IMPORTING ev_local_amount = yylv_amount
                                                               ev_subrc = yylv_subrc ).
         IF yylv_subrc = 0.
           v_t_kblp-hwgesapp = yylv_amount.
         ENDIF.
         MODIFY t_kblp FROM v_t_kblp.
       ENDIF.
     ENDLOOP.
   ENDIF.
 ENDIF.
ENDENHANCEMENT.