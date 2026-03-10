  METHOD /iwbep/if_mgw_appl_srv_runtime~delete_stream.

    DATA: lv_guid              TYPE ze_hrfiori_guidreq,
          lv_attach_type       TYPE ze_hrfiori_attachment_type,
          lv_inc_nb            TYPE ze_hrfiori_incrment_nb,
          lv_update_ok         TYPE flag,
          lv_message           TYPE string ##NEEDED,
          ls_key_tab           TYPE /iwbep/s_mgw_name_value_pair,
          lo_benefits_util     TYPE REF TO zcl_hr_fiori_benefits,
          lo_message_container TYPE REF TO /iwbep/if_message_container.

    IF iv_entity_name = 'Attachment'.

      LOOP AT it_key_tab INTO ls_key_tab.
        CASE ls_key_tab-name.
          WHEN 'Guid'.
            MOVE ls_key_tab-value TO lv_guid.
          WHEN 'AttachType'.
            MOVE ls_key_tab-value TO lv_attach_type.
          WHEN 'IncNb'.
            MOVE ls_key_tab-value TO lv_inc_nb.
        ENDCASE.
      ENDLOOP.

      CREATE OBJECT lo_benefits_util.

*     Delete document of request
      lo_benefits_util->delete_attachment( EXPORTING iv_guid = lv_guid
                                                     iv_attach_type = lv_attach_type
                                                     iv_inc_nb = lv_inc_nb
                                           IMPORTING ov_update_ok = lv_update_ok
                                                     ov_message = lv_message ).

      IF lv_update_ok = abap_false.
        lo_message_container = me->mo_context->get_message_container( ).
        lo_message_container->add_message( EXPORTING iv_msg_type = 'E'
                                                     iv_msg_id = 'ZHRFIORI'
                                                     iv_msg_number = '013' ).
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            message_container = lo_message_container.
      ENDIF.

    ENDIF.

  ENDMETHOD.
