  METHOD get_doc_type_by_mime_type.

    SELECT SINGLE doc_type INTO ov_doc_type
      FROM toadd
        WHERE mimetype = iv_mime_type ##WARN_OK.

  ENDMETHOD.
