METHOD /iwbep/if_mgw_appl_srv_runtime~get_stream.

*  TYPES: BEGIN OF ty_stream,
*           value     TYPE xstring,
*           mime_type TYPE string,
*         END OF ty_stream.

  DATA: lv_archive_doc_id    TYPE saeardoid,
        lv_request_id        TYPE ze_hrfiori_guidreq,
        lv_attach_type       TYPE zde_doctype,
        lv_incnb             TYPE ze_hrfiori_incrment_nb,
        lv_content           TYPE xstring,
        lv_mime_type         TYPE zde_mimetype,
        lv_filename          TYPE zde_filename,
        lv_success           TYPE flag,
        lv_message           TYPE string,
        ls_key_tab           TYPE /iwbep/s_mgw_name_value_pair,
        lo_manager_util      TYPE REF TO zcl_hr_document_manager,
        lo_message_container TYPE REF TO /iwbep/if_message_container,
        ls_header            TYPE ihttpnvp,
        ls_stream            TYPE ty_s_media_resource,
        lv_msg_text          TYPE c LENGTH 220,
        lv_value_string      TYPE string.

  "------------------------------------------------------------
  " Vérification de l'entité
  "------------------------------------------------------------
  IF iv_entity_name NE 'FileUpload'.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " Extraction des clés avec conversion TYPE-SAFE
  "------------------------------------------------------------
  LOOP AT it_key_tab INTO ls_key_tab.

    " --- Passer par une variable intermédiaire STRING ---
    lv_value_string = ls_key_tab-value.

    CASE ls_key_tab-name.

      WHEN 'REQUEST_ID' OR 'RequestId'.
        TRY.
            lv_request_id = lv_value_string. " conversion explicite
          CATCH cx_sy_move_cast_error ##NO_HANDLER.
            " Ignorer ou logger la valeur non convertible
        ENDTRY.

      WHEN 'DocumentType'.
        TRY.
            lv_attach_type = lv_value_string. " conversion explicite
          CATCH cx_sy_move_cast_error ##NO_HANDLER.
            " Ignorer ou logger la valeur non convertible
        ENDTRY.

      WHEN 'AttachType'.
        TRY.
            lv_attach_type = lv_value_string.
          CATCH cx_sy_move_cast_error ##NO_HANDLER.
        ENDTRY.

      WHEN 'IncNb'.
        TRY.
            lv_incnb = lv_value_string.
          CATCH cx_sy_move_cast_error ##NO_HANDLER.
        ENDTRY.

      WHEN 'ArchiveDocId'.
        TRY.
            lv_archive_doc_id = lv_value_string.
          CATCH cx_sy_move_cast_error ##NO_HANDLER.
        ENDTRY.

    ENDCASE.

  ENDLOOP.

  "------------------------------------------------------------
  " Validation : TOUTES les clés doivent être présentes
  "------------------------------------------------------------
* For DEMO purpose only, coment this part
*  if lv_request_id is initial
*   or lv_attach_type is initial
*   or lv_incnb is initial
*   or lv_archive_doc_id is initial.
*
*    lo_message_container = me->mo_context->get_message_container( ).
*    lo_message_container->add_message(
*      iv_msg_type   = 'E'
*      iv_msg_id     = 'ZHR_OFFBOARDING'
*      iv_msg_number = '009'
*      iv_msg_text   = 'All keys required (REQUEST_ID, AttachType, IncNb, ArchiveDocId)'
*    ).
*    raise exception type /iwbep/cx_mgw_busi_exception
*      exporting
*        message_container = lo_message_container.
*  endif.

  "------------------------------------------------------------
  " Récupération du document
  "------------------------------------------------------------
  lo_manager_util = zcl_hr_document_manager=>get_instance( ).

  lo_manager_util->get_document(
    EXPORTING
      iv_archive_doc_id = lv_archive_doc_id
      iv_request_id     = lv_request_id
      iv_attach_type    = lv_attach_type
      iv_incnb          = lv_incnb
    IMPORTING
      ev_content        = lv_content
      ev_mime_type      = lv_mime_type
      ev_filename       = lv_filename
      ev_success        = lv_success
      ev_message        = lv_message
  ).

  "------------------------------------------------------------
  " Gestion d'erreur
  "------------------------------------------------------------
  IF lv_success = abap_false.
    lo_message_container = me->mo_context->get_message_container( ).
    lv_msg_text = lv_message.

    IF strlen( lv_msg_text ) > 220.
      lv_msg_text = lv_msg_text(220).
    ENDIF.

    lo_message_container->add_message(
      iv_msg_type   = 'E'
      iv_msg_id     = 'ZHR_OFFBOARDING'
      iv_msg_number = '010'
      iv_msg_text   = lv_msg_text
    ).

    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        message_container = lo_message_container.
  ENDIF.

  "------------------------------------------------------------
  " Préparer le stream
  "------------------------------------------------------------
  ls_stream-value     = lv_content.
  ls_stream-mime_type = lv_mime_type.

  copy_data_to_ref(
    EXPORTING
      is_data = ls_stream
    CHANGING
      cr_data = er_stream
  ).

  "------------------------------------------------------------
  " En-tête HTTP
  "------------------------------------------------------------
  DATA(lv_unencoded_filename)   = CONV string( lv_filename ).
  DATA(lv_encoded_filename_rfc) = cl_http_utility=>escape_url( lv_unencoded_filename ).

*  ls_header-name  = 'Content-Disposition' ##NO_TEXT.
*  ls_header-value = |inline; filename="{ lv_unencoded_filename }"; filename*=UTF-8''{ lv_encoded_filename_rfc }|.

  ls_header-name = 'Content-Disposition' ##NO_TEXT.
  CONCATENATE 'inline; filename=' lv_encoded_filename_rfc
    INTO ls_header-value RESPECTING BLANKS ##NO_TEXT.
  set_header(
    EXPORTING
      is_header = ls_header
  ).
ENDMETHOD.
