  METHOD get_currency_list.

    DATA: ls_tcurt  TYPE tcurt,
          ls_return TYPE zshr_vh_generic,
          lt_tcurt  TYPE STANDARD TABLE OF tcurt.

    SELECT * INTO TABLE lt_tcurt
      FROM tcurt
        WHERE spras = sy-langu.

    LOOP AT lt_tcurt INTO ls_tcurt.
      CLEAR: ls_return.

      MOVE:
        ls_tcurt-waers TO ls_return-id,
        ls_tcurt-ltext TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
