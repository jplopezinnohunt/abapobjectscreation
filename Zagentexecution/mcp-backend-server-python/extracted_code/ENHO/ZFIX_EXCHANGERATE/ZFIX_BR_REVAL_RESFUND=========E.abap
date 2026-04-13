ENHANCEMENT 1  .

  IF sy-tcode =  'FMZZ'.
    testlauf = 'X'.
    TYPES: BEGIN OF lty_kblp,
             geber TYPE kblp-geber,
             gsber TYPE kblp-gsber,
           END OF lty_kblp.
    DATA yyls_kblp TYPE lty_kblp.
    DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
    yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
    IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.
      LOOP AT xrevaluate  ASSIGNING FIELD-SYMBOL(<yyls_xrevaluate>).
        SELECT SINGLE geber, gsber FROM kblp WHERE belnr = @<yyls_xrevaluate>-belnr
                                             AND   blpos = @<yyls_xrevaluate>-blpos
                 INTO CORRESPONDING FIELDS OF @yyls_kblp.

        IF <yyls_xrevaluate>-bukrs = 'UNES' AND <yyls_xrevaluate>-waers  NE 'EUR'.
          DELETE   xrevaluate.
        ELSEIF yyls_kblp-gsber NE 'GEF'.
          DELETE   xrevaluate.
        ELSEIF yylo_br_exchange_rate->check_conditions_3( iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund(
                                                          iv_fikrs = <yyls_xrevaluate>-bukrs
                                                          iv_fincode = yyls_kblp-geber ) ) = abap_true.
          DELETE xrevaluate.
        ENDIF.
      ENDLOOP.
    ENDIF.
  ENDIF.

ENDENHANCEMENT.