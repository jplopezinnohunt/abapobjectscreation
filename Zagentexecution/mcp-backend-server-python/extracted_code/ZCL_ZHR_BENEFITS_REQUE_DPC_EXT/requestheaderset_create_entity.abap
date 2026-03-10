METHOD requestheaderset_create_entity.

  DATA:
        " error handling
        lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception.
  DATA(lo_mc) = mo_context->get_message_container( ).

  io_data_provider->read_entry_data( IMPORTING es_data = er_entity ).

  TRY .
      zcl_hr_fiori_request=>get_instance( )->check_request(
        CHANGING
          cs_request = er_entity
      ).

      zcl_hr_fiori_request=>get_instance( )->create_request(
        CHANGING
          cs_request = er_entity ).

    CATCH zcx_hr_benef_exception INTO lr_hr_benef_exc.

      CASE lr_hr_benef_exc->get_severity( ).
        WHEN zcx_hr_benef_exception=>co_sev_warning
           OR zcx_hr_benef_exception=>co_sev_info
           OR zcx_hr_benef_exception=>co_sev_success.

          " ↪️ Warning/Info: pas d'exception, juste un message OData non bloquant
          lo_mc->add_message(
            iv_msg_type   = lr_hr_benef_exc->get_severity( )     " 'W' / 'I' / 'S'
            iv_msg_id     = 'ZHRFIORI'
            iv_msg_number = '039'                " placeholder SE91 (&1…)
            iv_msg_text   = CONV bapi_msg( lr_hr_benef_exc->get_text( )  )
            iv_add_to_response_header = abap_true   " ton texte libre
          ).
          " puis continuer le traitement normal et répondre 200 OK

          "Si pas erreur on crée la request
          zcl_hr_fiori_request=>get_instance( )->create_request(
          CHANGING
           cs_request = er_entity ).

          RETURN. " ou poursuivre jusqu’au RETURN habituel

        WHEN OTHERS.
          " ↪️ Erreur bloquante: remonter en HTTP 400 avec sap-messages
          lo_mc->add_message(
            iv_msg_type   = 'E'
            iv_msg_id     = 'ZHR_BENEF'
            iv_msg_number = '039'
            iv_msg_text   = CONV bapi_msg( lr_hr_benef_exc->get_text( ) )
            iv_add_to_response_header = abap_true
          ).
*          ROLLBACK WORK.
          RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception.
      ENDCASE.

    CATCH cx_root INTO DATA(lx_any).
*       ROLLBACK WORK.
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_tech_exception
        EXPORTING
          previous = lx_any.

  ENDTRY.
ENDMETHOD.

*METHOD requestheaderset_create_entity.
*  DATA lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception.
*  DATA(lo_mc)          = mo_context->get_message_container( ).
*  DATA lv_proceed      TYPE abap_bool VALUE abap_true.  " on crée la requête sauf erreur bloquante
*
*  " Lire l'input
*  io_data_provider->read_entry_data( IMPORTING es_data = er_entity ).
*
*  TRY.
*      " 1) Validations métier (peut lever zcx_hr_benef_exception)
*      zcl_hr_fiori_request=>get_instance( )->check_request(
*        CHANGING cs_request = er_entity ).
*
*    CATCH zcx_hr_benef_exception INTO lr_hr_benef_exc.
*
*      " Normaliser sévérité vide => 'E'
*      DATA(lv_sev) = lr_hr_benef_exc->get_severity( ).
*      IF lv_sev IS INITIAL.
*        lv_sev = zcx_hr_benef_exception=>co_sev_erro.
*      ENDIF.
*
*      CASE lv_sev.
*        WHEN zcx_hr_benef_exception=>co_sev_warning
*           OR zcx_hr_benef_exception=>co_sev_info
*           OR zcx_hr_benef_exception=>co_sev_success.
*          " Non bloquant : message visible dans la réponse, et on continue
*          lo_mc->add_message(
*            iv_msg_type                = lv_sev           " 'W'/'I'/'S'
*            iv_msg_id                  = 'ZHR_BENEF'
*            iv_msg_number              = '039'            " placeholder
*            iv_msg_text                = CONV bapi_msg( lr_hr_benef_exc->get_text( ) )
*            iv_add_to_response_header  = abap_true
*          ).
*          lv_proceed = abap_true.
*
*        WHEN OTHERS.
*          " Bloquant : ajouter message + lever 400
*          lo_mc->add_message(
*            iv_msg_type                = 'E'
*            iv_msg_id                  = 'ZHR_BENEF'
*            iv_msg_number              = '039'
*            iv_msg_text                = CONV bapi_msg( lr_hr_benef_exc->get_text( ) )
*            iv_add_to_response_header  = abap_true
*          ).
*          RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
*            EXPORTING
*              message_container = lo_mc.
*      ENDCASE.
*
*    CATCH cx_root INTO DATA(lx_any).
*      RAISE EXCEPTION TYPE /iwbep/cx_mgw_tech_exception
*        EXPORTING previous = lx_any.
*  ENDTRY.
*
*  " 2) Création uniquement si pas d'erreur bloquante
*  IF lv_proceed = abap_true.
*    zcl_hr_fiori_request=>get_instance( )->create_request(
*      CHANGING cs_request = er_entity ).
*  ENDIF.
*
*  " (Optionnel) Remplir er_entity (clés générées) avant retour pour 201 + __messages
*ENDMETHOD.
