  METHOD get_contract_type_list.

    DATA: ls_t547s  TYPE t547s,
          ls_return TYPE ty_contract_type,
          lt_t547s  TYPE STANDARD TABLE OF t547s.

    SELECT * INTO TABLE lt_t547s
      FROM t547s
        WHERE sprsl = sy-langu.

    LOOP AT lt_t547s INTO ls_t547s.
      CLEAR: ls_return.

      MOVE:
        ls_t547s-cttyp TO ls_return-id,
        ls_t547s-cttxt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
