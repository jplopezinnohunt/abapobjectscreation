  METHOD delete_attachment.

    DATA:lv_subrc      TYPE syst_subrc,
         lv_msg        TYPE string,
         ls_attachment TYPE zthrfiori_attach.

    ov_update_ok = abap_true.

*   Get attachment info from database
    SELECT SINGLE * INTO ls_attachment
      FROM zthrfiori_attach
        WHERE guid = iv_guid
          AND attach_type = iv_attach_type
          AND inc_nb = iv_inc_nb.

*   Delete file from SAP archive
    delete_doc_in_archive( EXPORTING iv_arch_doc_id = ls_attachment-archive_doc_id
                                     iv_archive_id = c_inboarding_archive_id
                                     iv_sap_object = c_inboarding_sap_object
                           IMPORTING ov_subrc = lv_subrc
                                     ov_message = lv_msg ).
    IF lv_subrc <> 0.
      ov_update_ok = abap_false.
      ov_message = lv_msg.

      RETURN.
    ENDIF.

*   Update in database
    DELETE zthrfiori_attach FROM ls_attachment.
    IF sy-subrc <> 0.
      ov_update_ok = abap_false.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '013'
        INTO ov_message.

      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
