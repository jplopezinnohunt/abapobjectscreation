  METHOD update_attachment.

    DATA: lv_request_key    TYPE ze_hrfiori_nt_request_key,
          lv_filename       TYPE string,
          lv_mimetype       TYPE w3conttype,
          lv_arch_doc_id    TYPE saeardoid,
          lv_document_class TYPE  saedoktyp,
          lv_ar_object      TYPE saeobjart,
          lv_object_id      TYPE saeobjid,
          lv_subrc          TYPE syst_subrc,
          lv_msg            TYPE string,
          ls_attachment     TYPE zthrfiori_attach.

    ov_update_ok = abap_true.

*   Get attachment info from database
    SELECT SINGLE * INTO ls_attachment
      FROM zthrfiori_attach
        WHERE guid = iv_guid
          AND attach_type = iv_attach_type
          AND inc_nb = iv_inc_nb.

*   Get all attachment content and properties
*    ls_attachment-contents = is_media_resource-value.
    CONCATENATE ls_attachment-filename ls_attachment-fileext
      INTO lv_filename SEPARATED BY '.'.
    lv_mimetype = is_media_resource-mime_type.

*   Generate object ID for archive
    SELECT SINGLE request_key INTO lv_request_key
      FROM zthrfiori_breq
        WHERE guid = iv_guid.
    generate_doc_object_id( EXPORTING iv_req_key = lv_request_key
                                      iv_attachment_type = iv_attach_type
                                      iv_inc_number = iv_inc_nb
                            IMPORTING ov_doc_object_id = lv_object_id ).
*   Get SAP archive document type
    get_archive_doc_type( EXPORTING iv_attachment_type = iv_attach_type
                          IMPORTING ov_archive_doc_type = lv_ar_object ).
*   Get SAP document type from MIME
    get_doc_type_by_mime_type( EXPORTING iv_mime_type = lv_mimetype
                               IMPORTING ov_doc_type = lv_document_class ).

    update_doc_in_archive( EXPORTING iv_arch_doc_id = ls_attachment-archive_doc_id
                                     iv_archive_id = c_inboarding_archive_id
                                     iv_content = is_media_resource-value
                                     iv_file_name = lv_filename
                                     iv_mime_type = lv_mimetype
                                     iv_document_class = lv_document_class
                                     iv_ar_object = lv_ar_object
                                     iv_object_id = lv_object_id
                           IMPORTING ov_arch_doc_id = lv_arch_doc_id
                                     ov_subrc = lv_subrc
                                     ov_message = lv_msg ).
    IF lv_subrc <> 0.
      ov_update_ok = abap_false.
      ov_message = lv_msg.

      RETURN.
    ENDIF.

    ls_attachment-filesize = xstrlen( is_media_resource-value ).

    ls_attachment-last_upd_date = iv_update_date.
    ls_attachment-last_upd_time = iv_update_time.
    ls_attachment-upd_usr_id = iv_update_usr_id.
    ls_attachment-upd_pernr = iv_update_pernr.
    ls_attachment-upd_lname = iv_update_lname.
    ls_attachment-upd_fname = iv_update_fname.

    ls_attachment-archive_doc_id = lv_arch_doc_id.

*   Update in database
    UPDATE zthrfiori_attach FROM ls_attachment.
    IF sy-subrc <> 0.
      ov_update_ok = abap_false.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '012'
        INTO ov_message.

      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
