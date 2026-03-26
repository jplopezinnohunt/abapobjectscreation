  METHOD get_wage_type_list.

    DATA: ls_t512t     TYPE t512t,
          ls_t512z     TYPE t512z,
          ls_wage_type TYPE ty_wage_type,
          lr_lgart     TYPE RANGE OF lgart,
          ls_lgart     LIKE LINE OF lr_lgart,
          lt_t512z     TYPE STANDARD TABLE OF t512z,
          lt_t512t     TYPE STANDARD TABLE OF t512t.

    SELECT * INTO TABLE lt_t512z
      FROM t512z
        WHERE infty = c_infty_0962
          AND molga = c_molga_un
          AND endda >= sy-datum.

    ls_lgart-sign = 'I'.
    ls_lgart-option = 'EQ'.
    LOOP AT lt_t512z INTO ls_t512z.
      ls_lgart-low = ls_t512z-lgart.
      APPEND ls_lgart TO lr_lgart.
    ENDLOOP.

    SELECT * INTO TABLE lt_t512t
      FROM t512t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un
          AND lgart IN lr_lgart.

    LOOP AT lt_t512t INTO ls_t512t.
      ls_wage_type-id = ls_t512t-lgart.
      ls_wage_type-txt = ls_t512t-lgtxt.
      APPEND ls_wage_type TO ot_list.
    ENDLOOP.


  ENDMETHOD.
