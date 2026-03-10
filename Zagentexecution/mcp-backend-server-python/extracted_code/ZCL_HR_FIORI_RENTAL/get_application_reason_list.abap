  METHOD get_application_reason_list.

    DATA: ls_t530f      TYPE t530f,
          ls_app_reason TYPE zshr_vh_generic,
          lt_t530f      TYPE STANDARD TABLE OF t530f.

    SELECT * INTO TABLE lt_t530f
      FROM t530f
        WHERE sprsl = sy-langu
          AND infty = c_infty_0962.

    LOOP AT lt_t530f INTO ls_t530f.
      ls_app_reason-id = ls_t530f-preas.
      ls_app_reason-txt = ls_t530f-rtext.
      APPEND ls_app_reason TO ot_list.
    ENDLOOP.

  ENDMETHOD.
