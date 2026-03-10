  METHOD create_attachment.

    DATA: lv_request_key     TYPE ze_hrfiori_nt_request_key,
          lv_inc_nb          TYPE ze_hrfiori_incrment_nb,
          lv_mime_type       TYPE w3conttype,
          lv_attach_type_txt TYPE ze_hrfiori_attach_type_text,
          lv_subrc           TYPE syst_subrc,
          lv_msg             TYPE string,
          lv_object_id       TYPE saeobjid,
          lv_ar_object       TYPE saeobjart,
          lv_document_class  TYPE saedoktyp,
          lv_arch_doc_id     TYPE saeardoid,
          ls_attachment      TYPE zthrfiori_attach.

    ov_insert_ok = abap_true.

*   1) File storing preparation ----------------------------------------------
*   Get request key
    SELECT SINGLE request_key INTO lv_request_key
      FROM zthrfiori_breq
        WHERE guid = iv_guid.

*   Get attachment increment number
    get_attachment_inc_number( EXPORTING iv_guid = iv_guid
                                         iv_attach_type = iv_attach_type
                               IMPORTING ov_inc_nb = lv_inc_nb ).
    lv_inc_nb = lv_inc_nb + 1.

    SPLIT iv_slug AT '.'
      INTO ls_attachment-filename ls_attachment-fileext.

    CALL FUNCTION 'SDOK_MIMETYPE_GET'
      EXPORTING
        extension = ls_attachment-fileext
      IMPORTING
        mimetype  = lv_mime_type.
    ls_attachment-mime_type  = lv_mime_type.

*   2) Store file in archive ----------------------------------------------
*   Generate object ID for archive
    generate_doc_object_id( EXPORTING iv_req_key = lv_request_key
                                      iv_attachment_type = iv_attach_type
                                      iv_inc_number = lv_inc_nb
                            IMPORTING ov_doc_object_id = lv_object_id ).
*   Get SAP archive document type
    get_archive_doc_type( EXPORTING iv_attachment_type = iv_attach_type
                          IMPORTING ov_archive_doc_type = lv_ar_object ).
*   Get SAP document type from MIME
    get_doc_type_by_mime_type( EXPORTING iv_mime_type = lv_mime_type
                               IMPORTING ov_doc_type = lv_document_class ).

    create_doc_in_archive( EXPORTING iv_file_name = iv_slug
                                     iv_content = is_media_resource-value
                                     iv_archive_id = c_inboarding_archive_id
                                     iv_sap_object = c_inboarding_sap_object
                                     iv_ar_object = lv_ar_object
                                     iv_object_id = lv_object_id
                                     iv_document_class = lv_document_class
                           IMPORTING ov_arch_doc_id = lv_arch_doc_id
                                     ov_subrc = lv_subrc
                                     ov_message = lv_msg ).

    IF lv_subrc <> 0.
      ov_insert_ok = abap_false.
      ov_message = lv_msg.

      RETURN.
    ENDIF.

*   3) Update attachment table---------------------------------------------
*   Get all attachment content and properties
*    ls_attachment-contents = is_media_resource-value.

    ls_attachment-archive_doc_id = lv_arch_doc_id.
    ls_attachment-guid = iv_guid.
    ls_attachment-attach_type = iv_attach_type.
    ls_attachment-inc_nb = lv_inc_nb.

    SELECT SINGLE attach_type_txt INTO lv_attach_type_txt
      FROM zthrfiori_att_ty
        WHERE attach_type = iv_attach_type
          AND language = sy-langu.
    ls_attachment-attach_type_txt = lv_attach_type_txt.

    ls_attachment-filesize = xstrlen( is_media_resource-value ).

    ls_attachment-creation_date = iv_creation_date.
    ls_attachment-creation_time = iv_creation_time.
    ls_attachment-creator_usr_id = iv_creator_usr_id.
    ls_attachment-creator_pernr = iv_creator_pernr.
    ls_attachment-creator_lname = iv_creator_lname.
    ls_attachment-creator_fname = iv_creator_fname.

    os_attachment = ls_attachment.
*    CLEAR: os_attachment-contents.

*   Save in database
    INSERT INTO zthrfiori_attach VALUES ls_attachment.
    IF sy-subrc <> 0.
      ov_insert_ok = abap_false.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '010'
        INTO ov_message.

      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
