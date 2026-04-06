  METHOD generate_doc_object_id.

    CONCATENATE iv_req_key iv_attachment_type iv_inc_number
                sy-datum sy-uzeit
      INTO ov_doc_object_id.

  ENDMETHOD.
