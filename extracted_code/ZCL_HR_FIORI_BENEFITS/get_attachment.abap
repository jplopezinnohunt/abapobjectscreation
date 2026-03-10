  METHOD get_attachment.

    DATA: ls_attachment TYPE zthrfiori_attach.

    SELECT SINGLE * INTO ls_attachment
     FROM zthrfiori_attach
       WHERE guid = iv_guid
         AND attach_type = iv_attach_type
         AND inc_nb = iv_inc_nb.

    ov_filename = ls_attachment-filename.
    ov_file_ext = ls_attachment-fileext.

    os_media-mime_type = ls_attachment-mime_type.
*    os_media-value = ls_attachment-contents.

    get_doc_from_archive( EXPORTING iv_arch_doc_id = ls_attachment-archive_doc_id
                                    iv_archive_id = c_inboarding_archive_id
                                    iv_mime_type = ls_attachment-mime_type
                          IMPORTING ov_content = os_media-value ).

  ENDMETHOD.
