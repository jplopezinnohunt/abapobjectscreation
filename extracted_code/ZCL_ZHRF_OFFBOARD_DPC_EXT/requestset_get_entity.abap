METHOD requestset_get_entity.

  "------------------------------------------------------------
  " Déclarations locales
  "------------------------------------------------------------
  DATA: lv_err_msg  TYPE bapi_msg,
        lo_instance TYPE REF TO zcl_hr_fiori_offboarding_req,
        ls_entity   TYPE zv_hrfiori_req,
        ls_return   TYPE bapiret2,
        lv_pernr    TYPE persno,
        lv_guid     TYPE raw16,
        ls_key_guid TYPE string,
        ls_key      TYPE /iwbep/s_mgw_name_value_pair.

  TRY.

      "------------------------------------------------------------
      " Obtenir l'instance singleton métier
      "------------------------------------------------------------
      lo_instance = zcl_hr_fiori_offboarding_req=>get_instance( ).

      "------------------------------------------------------------
      " Déterminer l'entity set
      "------------------------------------------------------------
      CASE iv_entity_set_name.

        WHEN 'RequestSet'.

          "------------------------------------------------------------
          " Extraction du GUID depuis it_key_tab
          "------------------------------------------------------------
          LOOP AT it_key_tab INTO ls_key WHERE name = 'Guid'.
            ls_key_guid = ls_key-value.
          ENDLOOP.

          IF ls_key_guid IS INITIAL.
            MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '062'
              INTO lv_err_msg.
            RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
              EXPORTING
                textid  = /iwbep/cx_mgw_busi_exception=>business_error
                message = lv_err_msg.
          ENDIF.

          "------------------------------------------------------------
          " Nettoyer le GUID
          "------------------------------------------------------------
          IF ls_key_guid CS 'guid'''.
            REPLACE ALL OCCURRENCES OF 'guid''' IN ls_key_guid WITH ''.
          ENDIF.

          IF strlen( ls_key_guid ) > 36 AND ls_key_guid+35(1) = ''''.
            ls_key_guid = ls_key_guid(36).
          ENDIF.

          REPLACE ALL OCCURRENCES OF '-' IN ls_key_guid WITH ''.

          IF strlen( ls_key_guid ) <> 32.
            CLEAR lv_err_msg.
            MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '107'
              INTO lv_err_msg WITH ls_key_guid.
            RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
              EXPORTING
                textid  = /iwbep/cx_mgw_busi_exception=>business_error
                message = lv_err_msg.
          ENDIF.

          "------------------------------------------------------------
          " Conversion GUID string -> RAW16
          "------------------------------------------------------------
          TRY.
              lv_guid = ls_key_guid.
            CATCH cx_sy_conversion_no_raw INTO DATA(lx_conv).
              CLEAR lv_err_msg.
              MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '108'
                INTO lv_err_msg WITH lx_conv->get_text( ).
              RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
                EXPORTING
                  textid  = /iwbep/cx_mgw_busi_exception=>business_error
                  message = lv_err_msg.
          ENDTRY.

          "------------------------------------------------------------
          " Sélection du PERNR correspondant
          "------------------------------------------------------------
          SELECT SINGLE creator_pernr
            FROM zv_hrfiori_req
            INTO @lv_pernr
            WHERE guid = @lv_guid ##WARN_OK.

          IF sy-subrc <> 0.
            CLEAR lv_err_msg.
            MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '109'
              INTO lv_err_msg WITH ls_key_guid.
            RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
              EXPORTING
                textid  = /iwbep/cx_mgw_busi_exception=>business_error
                message = lv_err_msg.
          ENDIF.

          "------------------------------------------------------------
          " Récupération du détail de la requête
          " LA CONVERSION SE FAIT DÉJÀ DANS CETTE MÉTHODE
          "------------------------------------------------------------
          CALL METHOD lo_instance->get_request_detail
            EXPORTING
              iv_pernr  = lv_pernr
              iv_guid   = lv_guid
            IMPORTING
              es_detail = ls_entity
              rs_return = ls_return.

          "------------------------------------------------------------
          "  PAS DE CONVERSION ICI - get_request_detail L'A DÉJÀ FAITE
          "------------------------------------------------------------
          CASE ls_return-type.
            WHEN 'S'.
              er_entity = CORRESPONDING #( ls_entity ).
            WHEN 'E'.
              RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
                EXPORTING
                  textid  = /iwbep/cx_mgw_busi_exception=>business_error
                  message = ls_return-message.
            WHEN OTHERS.
              er_entity = CORRESPONDING #( ls_entity ).
          ENDCASE.

        WHEN OTHERS.
          "------------------------------------------------------------
          " Rediriger vers la méthode parent pour autres entitysets
          "------------------------------------------------------------
          CALL METHOD super->requestset_get_entity
            EXPORTING
              iv_entity_name          = iv_entity_name
              iv_entity_set_name      = iv_entity_set_name
              iv_source_name          = iv_source_name
              it_key_tab              = it_key_tab
              io_tech_request_context = io_tech_request_context
              it_navigation_path      = it_navigation_path
            IMPORTING
              er_entity               = er_entity.
      ENDCASE.

      "------------------------------------------------------------
      " Gestion des exceptions
      "------------------------------------------------------------
    CATCH /iwbep/cx_mgw_busi_exception INTO DATA(lo_busi_exception).
      RAISE EXCEPTION lo_busi_exception.

    CATCH /iwbep/cx_mgw_tech_exception INTO DATA(lo_tech_exception).
      RAISE EXCEPTION lo_tech_exception.

    CATCH cx_root INTO DATA(lo_exception).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_tech_exception
        EXPORTING
          textid   = /iwbep/cx_mgw_tech_exception=>internal_error
          previous = lo_exception.

  ENDTRY.

ENDMETHOD.
