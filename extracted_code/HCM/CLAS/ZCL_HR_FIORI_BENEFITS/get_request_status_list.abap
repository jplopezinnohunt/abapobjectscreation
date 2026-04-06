  METHOD get_request_status_list.

    DATA: ls_request_status TYPE zthrfiori_status,
          ls_return         TYPE ty_req_status,
          lt_request_status TYPE STANDARD TABLE OF zthrfiori_status,
          lt_return         TYPE tt_req_status.

    SELECT * INTO TABLE lt_request_status
      FROM zthrfiori_status
        WHERE language = sy-langu.

    LOOP  AT lt_request_status INTO ls_request_status.
      ls_return-id = ls_request_status-id.
      ls_return-text = ls_request_status-name.
      APPEND ls_return TO lt_return.
    ENDLOOP.

    ot_list = lt_return.

  ENDMETHOD.
