  METHOD get_attachments.

    DATA: lt_attachments TYPE STANDARD TABLE OF zthrfiori_attach.

*   Get attachments according constructed criterias
    SELECT * INTO TABLE lt_attachments
      FROM zthrfiori_attach
        WHERE guid = iv_guid.

*   Filter results if nedded
    IF iv_attach_type IS NOT INITIAL.
      DELETE lt_attachments WHERE attach_type <> iv_attach_type.
    ENDIF.
    IF iv_inc_nb IS NOT INITIAL.
      DELETE lt_attachments WHERE inc_nb <> iv_inc_nb.
    ENDIF.

    ot_attachment_list[] = lt_attachments[].

  ENDMETHOD.
