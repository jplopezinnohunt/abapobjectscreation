  METHOD get_school_country_list.

    DATA: ls_t005t  TYPE t005t,
          ls_return TYPE zshr_vh_generic,
          lt_t005t  TYPE STANDARD TABLE OF t005t.

    SELECT * INTO TABLE lt_t005t
      FROM t005t
        WHERE spras = sy-langu.

    LOOP AT lt_t005t INTO ls_t005t.
      CLEAR: ls_return.

      MOVE:
        ls_t005t-land1 TO ls_return-id,
        ls_t005t-landx50 TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

    SORT ot_list BY txt ASCENDING.

  ENDMETHOD.
