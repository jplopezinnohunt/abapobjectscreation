  METHOD get_change_reason_list.

    DATA: ls_t530f  TYPE t530f,
          ls_return TYPE ZSHR_VH_GENERIC,
          lt_t530f  TYPE STANDARD TABLE OF t530f.

    SELECT * INTO TABLE lt_t530f
      FROM t530f
        WHERE sprsl = sy-langu
          AND infty = '0965'.

    LOOP AT lt_t530f INTO ls_t530f.
      CLEAR: ls_return.

      MOVE:
        ls_t530f-preas TO ls_return-id,
        ls_t530f-rtext TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
