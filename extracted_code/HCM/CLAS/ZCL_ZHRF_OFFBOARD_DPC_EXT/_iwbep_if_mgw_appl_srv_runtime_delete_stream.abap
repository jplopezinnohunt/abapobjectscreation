METHOD /iwbep/if_mgw_appl_srv_runtime~delete_stream.

  DATA: lv_err_msg           TYPE symsgv,
        lv_archive_doc_id    TYPE saeardoid,
        ls_key_tab           TYPE /iwbep/s_mgw_name_value_pair,
        lo_manager_util      TYPE REF TO zcl_hr_document_manager,
        lv_success           TYPE abap_bool,
        lv_message           TYPE string,
        lo_message_container TYPE REF TO /iwbep/if_message_container.

  IF iv_entity_name NE 'TOAAT'.
    RETURN.
  ENDIF.

  LOOP AT it_key_tab INTO ls_key_tab.
    IF ls_key_tab-name = 'ArchiveDocId'.
      lv_archive_doc_id = ls_key_tab-value.
      EXIT.
    ENDIF.
  ENDLOOP.

  IF lv_archive_doc_id IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '111'
      INTO lv_err_msg.
    lo_message_container = me->mo_context->get_message_container( ).
    lo_message_container->add_message(
      EXPORTING
        iv_msg_type    = 'E'
        iv_msg_id      = '/IWBEP/MC_MSG'
        iv_msg_number  = '001'
        iv_msg_v1      = lv_err_msg
    ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        message_container = lo_message_container.
  ENDIF.

  TRY.
      lo_manager_util = zcl_hr_document_manager=>get_instance( ).
    CATCH cx_root INTO DATA(lx_singleton_error).
      CLEAR lv_err_msg.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '112'
        INTO lv_err_msg WITH lx_singleton_error->get_text( ).
      lo_message_container = me->mo_context->get_message_container( ).
      lo_message_container->add_message(
        EXPORTING
          iv_msg_type    = 'E'
          iv_msg_id      = '/IWBEP/MC_MSG'
          iv_msg_number  = '002'
          iv_msg_v1      = lv_err_msg
      ).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          message_container = lo_message_container.
  ENDTRY.

  TRY.
      lo_manager_util->delete_file(
        EXPORTING
          iv_arc_doc_id = lv_archive_doc_id
        IMPORTING
          ev_success    = lv_success
          ev_message    = lv_message
      ).
    CATCH cx_root INTO DATA(lx_delete_error).
      CLEAR lv_err_msg.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '113'
        INTO lv_err_msg WITH lx_delete_error->get_text( ).
      lo_message_container = me->mo_context->get_message_container( ).
      lo_message_container->add_message(
        EXPORTING
          iv_msg_type    = 'E'
          iv_msg_id      = '/IWBEP/MC_MSG'
          iv_msg_number  = '003'
          iv_msg_v1      = lv_err_msg
      ).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          message_container = lo_message_container.
  ENDTRY.

  IF lv_success = abap_false.
    lo_message_container = me->mo_context->get_message_container( ).
    lo_message_container->add_message(
      EXPORTING
        iv_msg_type    = 'E'
        iv_msg_id      = '/IWBEP/MC_MSG'
        iv_msg_number  = '004'
        iv_msg_v1      = CONV #( lv_message )
    ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        message_container = lo_message_container.
  ENDIF.

  CLEAR lv_err_msg.
  MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '114'
    INTO lv_err_msg WITH lv_archive_doc_id.
  lo_message_container = me->mo_context->get_message_container( ).
  lo_message_container->add_message(
    EXPORTING
      iv_msg_type    = 'S'
      iv_msg_id      = '/IWBEP/MC_MSG'
      iv_msg_number  = '005'
      iv_msg_v1      = lv_err_msg
  ).
ENDMETHOD.
