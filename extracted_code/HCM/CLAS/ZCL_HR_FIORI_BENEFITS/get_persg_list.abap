  METHOD get_persg_list.

    DATA: ls_return TYPE ty_persg,
          ls_t501t  TYPE t501t,
          lt_return TYPE tt_persg,
          lt_t501t  TYPE STANDARD TABLE OF t501t.

    SELECT * INTO TABLE lt_t501t
      FROM t501t
        WHERE sprsl = sy-langu.
    LOOP AT lt_t501t INTO ls_t501t.
      ls_return-id = ls_t501t-persg.
      ls_return-text = ls_t501t-ptext.
      APPEND ls_return TO lt_return.
    ENDLOOP.

    ot_list = lt_return.

  ENDMETHOD.
