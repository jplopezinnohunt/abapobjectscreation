  METHOD get_request_type_list.

    DATA: ls_request_type TYPE zthrfiori_reqtyp,
          ls_return       TYPE ty_req_type,
          lt_req_type     TYPE STANDARD TABLE OF zthrfiori_reqtyp,
          lt_return       TYPE tt_req_type.

    SELECT * INTO TABLE lt_req_type
      FROM zthrfiori_reqtyp
        WHERE language = sy-langu.

    LOOP  AT lt_req_type INTO ls_request_type.
      ls_return-id = ls_request_type-id.
      ls_return-text = ls_request_type-name.
      APPEND ls_return TO lt_return.
    ENDLOOP.

    ot_list = lt_return.


  ENDMETHOD.
