  METHOD get_tax_code_list.

    DATA: ls_t007s  TYPE t007s,
          ls_return TYPE ty_tax_code,
          lt_t007s  TYPE STANDARD TABLE OF t007s.

    SELECT * INTO TABLE lt_t007s
      FROM t007s
        WHERE spras = sy-langu
          AND kalsm = c_procedure_tax.

    LOOP AT lt_t007s INTO ls_t007s.
      CLEAR: ls_return.

      MOVE:
        ls_t007s-mwskz TO ls_return-id,
        ls_t007s-text1 TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
