METHOD /iwbep/if_mgw_appl_srv_runtime~create_stream.

  " Déclarations
  DATA: ls_fileupload   TYPE zstr_document_entity,
        ls_file         TYPE zstr_document_entity,
        lv_message      TYPE bapi_msg,
        lv_message_api  TYPE string,
        lv_success      TYPE abap_bool,
        lv_guid_str     TYPE string,
        lv_replace_flag TYPE string,
        lv_file_ext     TYPE string,
        lt_slug_parts   TYPE TABLE OF string,
        lv_count        TYPE i,
        lv_replace      TYPE abap_bool VALUE abap_false,
        lv_error_msg    TYPE bapi_msg.

  CLEAR: lv_message, lv_message_api, lv_success.
  lv_success = abap_false.

  "========================================================
  " 1. VÉRIFICATION CONTENU BINAIRE
  "========================================================
  IF is_media_resource IS INITIAL OR is_media_resource-value IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '115'
      INTO lv_error_msg.
*    lv_error_msg = 'No file content provided (is_media_resource is empty)'.
    me->mo_context->get_message_container( )->add_message_text_only(
      iv_msg_type = 'E'
      iv_msg_text = lv_error_msg ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_container = me->mo_context->get_message_container( ).
  ENDIF.

  "========================================================
  " 2. VÉRIFICATION SLUG
  "========================================================
  IF iv_slug IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '116'
      INTO lv_error_msg.
*    lv_error_msg = 'SLUG parameter is mandatory and cannot be empty'.
    me->mo_context->get_message_container( )->add_message_text_only(
      iv_msg_type = 'E'
      iv_msg_text = lv_error_msg ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_container = me->mo_context->get_message_container( ).
  ENDIF.

  "========================================================
  " 3. PARSING DU SLUG
  " Format: DocType;FileName;MimeType;RequestID;ReplaceFlag;Pernr;Extension
  "========================================================
  SPLIT iv_slug AT ';' INTO TABLE lt_slug_parts.
  DESCRIBE TABLE lt_slug_parts LINES lv_count.

  IF lv_count LT 4.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '117'
      INTO lv_error_msg WITH lv_count iv_slug.
*    lv_error_msg = |Invalid SLUG format. Expected at least 4 parts, got { lv_count }. SLUG={ iv_slug }|.
    me->mo_context->get_message_container( )->add_message_text_only(
      iv_msg_type = 'E'
      iv_msg_text = lv_error_msg ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_container = me->mo_context->get_message_container( ).
  ENDIF.

  TRY.
      " Lecture des parties du SLUG
      READ TABLE lt_slug_parts INDEX 1 INTO ls_fileupload-document_type.
      READ TABLE lt_slug_parts INDEX 2 INTO ls_fileupload-file_name.
      READ TABLE lt_slug_parts INDEX 3 INTO ls_fileupload-mime_type.
      READ TABLE lt_slug_parts INDEX 4 INTO lv_guid_str.

      IF lv_count >= 5.
        READ TABLE lt_slug_parts INDEX 5 INTO lv_replace_flag.
      ENDIF.

      IF lv_count >= 6.
        READ TABLE lt_slug_parts INDEX 6 INTO ls_fileupload-pernr.
      ENDIF.

      IF lv_count >= 7.
        READ TABLE lt_slug_parts INDEX 7 INTO lv_file_ext.
        TRANSLATE lv_file_ext TO UPPER CASE.
      ENDIF.

    CATCH cx_root INTO DATA(lx_read_error).
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '118'
        INTO lv_error_msg WITH lx_read_error->get_text( ).
*    lv_error_msg = |Error parsing SLUG: { lx_read_error->get_text( ) }|.
      me->mo_context->get_message_container( )->add_message_text_only(
        iv_msg_type = 'E'
        iv_msg_text = lv_error_msg ).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          textid            = /iwbep/cx_mgw_busi_exception=>business_error
          message_container = me->mo_context->get_message_container( ).
  ENDTRY.

  "========================================================
  " 4. NETTOYAGE DES DONNÉES
  "========================================================
  REPLACE ALL OCCURRENCES OF '%2F' IN ls_fileupload-mime_type WITH '/'.
  REPLACE ALL OCCURRENCES OF '%20' IN ls_fileupload-file_name WITH '_'.

  IF lv_guid_str IS NOT INITIAL.
    REPLACE ALL OCCURRENCES OF '-' IN lv_guid_str WITH ''.
    REPLACE ALL OCCURRENCES OF '%20' IN lv_guid_str WITH ''.
    REPLACE ALL OCCURRENCES OF '"' IN lv_guid_str WITH ''.
    REPLACE ALL OCCURRENCES OF '''' IN lv_guid_str WITH ''.
    TRANSLATE lv_guid_str TO UPPER CASE.
  ENDIF.

  "========================================================
  " 5. DÉTERMINATION DU FLAG REPLACE
  "========================================================
  DATA(lv_replace_clean) = lv_replace_flag.
  IF lv_replace_flag IS NOT INITIAL.
    TRANSLATE lv_replace_clean TO UPPER CASE.
    CONDENSE lv_replace_clean NO-GAPS.
    IF lv_replace_clean = 'TRUE' OR lv_replace_clean = 'X' OR lv_replace_clean = '1' OR lv_replace_clean = 'YES'.
      lv_replace = abap_true.
    ELSE.
      lv_replace = abap_false.
    ENDIF.
  ENDIF.

  "========================================================
  " 6. VALEURS PAR DÉFAUT
  "========================================================
  IF ls_fileupload-file_name IS INITIAL.
    ls_fileupload-file_name = |document_{ sy-datum }_{ sy-uzeit }.pdf|.
  ENDIF.
  IF ls_fileupload-mime_type IS INITIAL.
    ls_fileupload-mime_type = 'application/pdf'.
  ENDIF.
  IF ls_fileupload-document_type IS INITIAL.
    ls_fileupload-document_type = 'GENERAL_DOC'.
  ENDIF.

  "========================================================
  " 7. RÉCUPÉRATION DU PERNR SI ABSENT
  "========================================================
  IF ls_fileupload-pernr IS INITIAL.
    TRY.
        SELECT SINGLE creator_pernr INTO @ls_fileupload-pernr
          FROM zthrfiori_hreq
          WHERE guid = @lv_guid_str.
      CATCH cx_root.
        CLEAR ls_fileupload-pernr.
    ENDTRY.
  ENDIF.

  "========================================================
  " 8. PRÉPARATION DES DONNÉES POUR UPLOAD_DOCUMENT
  "========================================================
  ls_file-request_id  = lv_guid_str.
  ls_file-file_name   = ls_fileupload-file_name.
  ls_file-mime_type   = ls_fileupload-mime_type.
  ls_file-document_type = ls_fileupload-document_type.
  ls_file-content     = is_media_resource-value.
  ls_file-pernr       = ls_fileupload-pernr.
  ls_file-replace_flag = lv_replace.
  ls_file-file_ext    = lv_file_ext.

  "========================================================
  " 9. APPEL DE LA MÉTHODE UPLOAD_DOCUMENT
  "========================================================
  TRY.
      DATA(lo_doc_manager) = zcl_hr_document_manager=>get_instance( ).
      CALL METHOD lo_doc_manager->upload_document
        EXPORTING
          is_file    = ls_file
        IMPORTING
          ev_message = lv_message_api
          ev_success = lv_success.

      IF lv_success <> abap_true.
        lv_error_msg = lv_message_api.
        me->mo_context->get_message_container( )->add_message_text_only(
          iv_msg_type = 'E'
          iv_msg_text = lv_error_msg ).
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid            = /iwbep/cx_mgw_busi_exception=>business_error
            message_container = me->mo_context->get_message_container( ).
      ENDIF.

      lv_message = lv_message_api.

    CATCH cx_root INTO DATA(lx_error).
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '119'
        INTO lv_error_msg WITH lx_error->get_text( ).
*    lv_error_msg = |Technical error during upload: { lx_error->get_text( ) }|.
      me->mo_context->get_message_container( )->add_message_text_only(
        iv_msg_type = 'E'
        iv_msg_text = lv_error_msg ).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          textid            = /iwbep/cx_mgw_busi_exception=>business_error
          message_container = me->mo_context->get_message_container( ).
  ENDTRY.

  "========================================================
  " 10. PRÉPARATION DE LA RÉPONSE
  "========================================================
  ls_fileupload-request_id = lv_guid_str.
  ls_fileupload-status     = 'SUCCESS'.
  ls_fileupload-message    = lv_message.

  " Utilisation correcte de COPY_DATA_TO_REF pour remplir er_entity
  copy_data_to_ref(
    EXPORTING
      is_data  = ls_fileupload
    CHANGING
      cr_data  = er_entity ).

ENDMETHOD.
