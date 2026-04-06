  METHOD /iwbep/if_mgw_appl_srv_runtime~create_stream.

    DATA: lv_guid              TYPE ze_hrfiori_guidreq,
          lv_attach_type       TYPE ze_hrfiori_attachment_type,
          lv_inc_nb            TYPE ze_hrfiori_incrment_nb,
          lv_pernr             TYPE persno,
          lv_user_id           TYPE sysid,
          lv_last_name         TYPE pad_nachn,
          lv_first_name        TYPE pad_vorna,
          lv_creation_date     TYPE dats,
          lv_creation_time     TYPE uzeit,
          lv_insert_ok         TYPE flag,
          lv_message           TYPE string ##NEEDED,
          ls_key_tab           TYPE /iwbep/s_mgw_name_value_pair,
          ls_attachment        TYPE zthrfiori_attach,
          lo_benefits_util     TYPE REF TO zcl_hr_fiori_benefits,
          lo_message_container TYPE REF TO /iwbep/if_message_container.

    IF iv_entity_name = 'File'.

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

*     Get actor infos
      lo_benefits_util->get_actor_infos( IMPORTING ov_usrid = lv_user_id
                                                   ov_pernr = lv_pernr
                                                   ov_last_name = lv_last_name
                                                   ov_first_name = lv_first_name ).
      lv_creation_date = sy-datum.
      lv_creation_time = sy-uzeit.

*     Attach document to request
      lo_benefits_util->create_attachment( EXPORTING iv_guid = lv_guid
                                                     iv_attach_type = lv_attach_type
                                                     iv_inc_nb = lv_inc_nb
                                                     is_media_resource = is_media_resource
                                                     iv_slug = iv_slug
                                                     iv_creation_date = lv_creation_date
                                                     iv_creation_time = lv_creation_time
                                                     iv_creator_usr_id = lv_user_id
                                                     iv_creator_pernr = lv_pernr
                                                     iv_creator_lname = lv_last_name
                                                     iv_creator_fname = lv_first_name
                                           IMPORTING ov_insert_ok = lv_insert_ok
                                                     ov_message = lv_message
                                                     os_attachment = ls_attachment ).

      IF lv_insert_ok = abap_false.
        lo_message_container = me->mo_context->get_message_container( ).
        lo_message_container->add_message( EXPORTING iv_msg_type = 'E'
                                                     iv_msg_id = 'ZHRFIORI'
                                                     iv_msg_number = '010' ).
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            message_container = lo_message_container.
      ENDIF.

      copy_data_to_ref( EXPORTING is_data = ls_attachment
                        CHANGING  cr_data = er_entity ).

    ENDIF.

  ENDMETHOD.
