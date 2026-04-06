METHOD toaatset_delete_entity.

  DATA: lv_err_msg        TYPE string,
        lv_archive_doc_id TYPE saeardoid,
        lo_doc_manager    TYPE REF TO zcl_hr_document_manager,
        lv_success        TYPE abap_bool,
        lv_message        TYPE string,
        ls_keys           TYPE zthrfiori_attac.

  " Récupération des clés converties
  io_tech_request_context->get_converted_keys(
    IMPORTING
      es_key_values = ls_keys
  ).

  lv_archive_doc_id = ls_keys-archive_doc_id.

  IF lv_archive_doc_id IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '102'
      INTO lv_err_msg.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_unlimited = lv_err_msg.
  ENDIF.

  lo_doc_manager = zcl_hr_document_manager=>get_instance( ).

  lo_doc_manager->delete_file(
    EXPORTING iv_arc_doc_id = lv_archive_doc_id
    IMPORTING ev_success    = lv_success
              ev_message    = lv_message
  ).

  IF lv_success = abap_false.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '103'
      INTO lv_err_msg WITH lv_archive_doc_id lv_message.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_unlimited = lv_err_msg.
  ENDIF.

ENDMETHOD.
