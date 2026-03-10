  METHOD get_nationality_list.

    DATA: ls_t005t  TYPE t005t,
          ls_return TYPE ty_nationality,
          lt_t005t  TYPE STANDARD TABLE OF t005t.

    SELECT * INTO TABLE lt_t005t
      FROM t005t
        WHERE spras = sy-langu.

    LOOP AT lt_t005t INTO ls_t005t.
      CLEAR: ls_return.

      MOVE ls_t005t-land1 TO ls_return-id.
      CONCATENATE ls_t005t-natio50 ls_t005t-land1
        INTO ls_return-txt SEPARATED BY space.
      APPEND ls_return TO ot_list.
    ENDLOOP.

    SORT ot_list BY txt ASCENDING.

  ENDMETHOD.
