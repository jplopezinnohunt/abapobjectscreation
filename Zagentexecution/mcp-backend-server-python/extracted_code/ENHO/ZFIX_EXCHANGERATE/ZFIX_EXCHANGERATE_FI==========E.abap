ENHANCEMENT 2  .
* During FM document creation changing the Local Amount
* From any source PO, Finance, etc
    DATA yylo_br_exchange_rate TYPE REF TO ycl_fm_br_exchange_rate_bl.
    DATA yylv_amount TYPE fmifiit-fkbtr.
    DATA yylv_subrc TYPE sy-subrc.
    DATA yyls_avc_fund TYPE ycl_fm_br_exchange_rate_bl=>ty_avc_fund.
    DATA yylo_br_payroll_posting_bl TYPE REF TO ycl_fm_br_payroll_posting_bl.
    DATA yyls_account_gl TYPE bapiacgl04.
    DATA yyls_account_amount TYPE bapiaccr04.

    yylo_br_exchange_rate = ycl_fm_br_exchange_rate_bl=>get_instance( ).
    yylo_br_payroll_posting_bl = ycl_fm_br_payroll_posting_bl=>get_instance( ).

    IF yylo_br_exchange_rate->check_br_is_active( ) = abap_true.

*START of BR  nonStaff Logic ----->START
      LOOP AT u_t_fmifihd INTO DATA(ls_fmifihd).

        LOOP AT u_t_fmifiit ASSIGNING FIELD-SYMBOL(<ls_fmifiit>) WHERE fmbelnr = ls_fmifihd-fmbelnr
                                                                 AND   fikrs   = ls_fmifihd-fikrs.
          CHECK yylo_br_exchange_rate->check_conditions( iv_rldnr = <ls_fmifiit>-rldnr
                                                         iv_fikrs = <ls_fmifiit>-fikrs
                                                         iv_gsber = <ls_fmifiit>-bus_area
                                                         iv_waers = <ls_fmifiit>-twaer
                                                         iv_fipex = <ls_fmifiit>-fipex
                                                         iv_vrgng = <ls_fmifiit>-vrgng
                                                         iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = <ls_fmifiit>-fikrs iv_fincode = <ls_fmifiit>-fonds ) ) = abap_true.
          "First save data before conversion in table YTFM_BR_FMIFIIT
          IF u_flg_update  = con_off OR g_flg_rebuild = con_on.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT'
              EXPORTING
                is_fmifiit   = <ls_fmifiit>
              EXCEPTIONS
                error_update = 1
                OTHERS       = 2.
          ELSE.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT' IN UPDATE TASK
              EXPORTING
                is_fmifiit   = <ls_fmifiit>
              EXCEPTIONS
                error_update = 1
                OTHERS       = 2.
          ENDIF.

          "Do conversion in constant dollar
          yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = ls_fmifihd-budat
                                                                iv_foreign_amount = <ls_fmifiit>-trbtr
                                                                iv_foreign_currency = <ls_fmifiit>-twaer
                                                                iv_local_currency = 'USD'
                                                      IMPORTING ev_local_amount = yylv_amount
                                                                ev_subrc = yylv_subrc ).
          CHECK yylv_subrc = 0.
          <ls_fmifiit>-fkbtr = yylv_amount.
          "Store Fund to recalculate AVC
          MOVE-CORRESPONDING <ls_fmifiit> TO yyls_avc_fund.
          INSERT yyls_avc_fund INTO TABLE yylo_br_exchange_rate->mt_avc_fund.
        ENDLOOP.
      ENDLOOP.
      IF yylo_br_exchange_rate->mt_avc_fund IS NOT INITIAL.
        SET HANDLER yylo_br_exchange_rate->fmavc_reinit_on_event.
      ENDIF.
    ENDIF.

*END of BR  non Staff Logic ----->END
    IF 1 = 2. " Staff logic on hold
*START of BR  Staff Logic ----->START
      LOOP AT u_t_fmifihd INTO DATA(ls_fmifihd2).
        LOOP AT u_t_fmifiit ASSIGNING FIELD-SYMBOL(<ls_fmifiit2>) WHERE fmbelnr = ls_fmifihd-fmbelnr
                                                                AND   fikrs   = ls_fmifihd-fikrs.
          "NME 20241125
          IF ls_fmifihd2-awtyp = 'HRPAY'.
            "Get FI lines
            yylo_br_payroll_posting_bl->get_account_line( EXPORTING iv_item = <ls_fmifiit2>-knbuzei
                                                          IMPORTING es_account_gl = yyls_account_gl
                                                                    es_account_amount = yyls_account_amount ).
          ENDIF.

          CHECK yylo_br_exchange_rate->check_conditions_2( iv_rldnr = <ls_fmifiit2>-rldnr  " LEDGER
                                               iv_fikrs = <ls_fmifiit2>-fikrs              " FM AREA
                                               iv_gsber = <ls_fmifiit2>-bus_area           " Business Area
                                               iv_waers = <ls_fmifiit2>-twaer              " Currency
                                               iv_fipex = <ls_fmifiit2>-fipex              "Commitment Item
                                               iv_vrgng = <ls_fmifiit2>-vrgng              "BUsiness transaction
                                               "ADD HKONT
                                               "ADD PERSONAL CHECK
                                               "FUND TYPE
                                               iv_ftype = yylo_br_exchange_rate->get_fund_type_from_fund( iv_fikrs = <ls_fmifiit2>-fikrs iv_fincode = <ls_fmifiit2>-fonds ) ) = abap_true.

          "First save data before conversion in table YTFM_BR_FMIFIIT
          IF u_flg_update  = con_off OR g_flg_rebuild = con_on.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT'
              EXPORTING
                is_fmifiit   = <ls_fmifiit2>
              EXCEPTIONS
                error_update = 1
                OTHERS       = 2.
          ELSE.
            CALL FUNCTION 'Y_FM_UPDATE_BR_FMIFIIT' IN UPDATE TASK
              EXPORTING
                is_fmifiit   = <ls_fmifiit2>
              EXCEPTIONS
                error_update = 1
                OTHERS       = 2.
          ENDIF.


          IF <ls_fmifiit2>-twaer = 'EUR'.
            "Do conversion EUR to constant dollar
            yylo_br_exchange_rate->convert_to_currency( EXPORTING iv_date = ls_fmifihd-budat
                                                                  iv_foreign_amount = <ls_fmifiit2>-trbtr
                                                                  iv_foreign_currency = <ls_fmifiit2>-twaer
                                                                  iv_local_currency = 'USD'
                                                        IMPORTING ev_local_amount = yylv_amount
                                                                  ev_subrc = yylv_subrc ).
            CHECK yylv_subrc = 0.
            <ls_fmifiit2>-fkbtr = yylv_amount.
            "Store Fund to recalculate AVC
            MOVE-CORRESPONDING <ls_fmifiit2> TO yyls_avc_fund.
            INSERT yyls_avc_fund INTO TABLE yylo_br_exchange_rate->mt_avc_fund.

          ELSEIF <ls_fmifiit2>-twaer = 'USD'.
            "Do conversion USD UNORE to USD constant dollar TBD.
            yylo_br_exchange_rate->convert_to_currency_2( EXPORTING iv_date = ls_fmifihd-budat
                                                                  iv_foreign_amount = <ls_fmifiit2>-trbtr
                                                                  iv_foreign_currency = <ls_fmifiit2>-twaer
                                                                  iv_local_currency = 'USD'
                                                        IMPORTING ev_local_amount = yylv_amount
                                                                  ev_subrc = yylv_subrc ).
            CHECK yylv_subrc = 0.
            <ls_fmifiit2>-fkbtr = yylv_amount.
            "Store Fund to recalculate AVC
            MOVE-CORRESPONDING <ls_fmifiit2> TO yyls_avc_fund.
            INSERT yyls_avc_fund INTO TABLE yylo_br_exchange_rate->mt_avc_fund.
          ENDIF.

        ENDLOOP.

**End Staff Logic

*Trigger Update AVC total tables after event

      ENDLOOP.
    ENDIF. " Staff logic on hold


ENDENHANCEMENT.
