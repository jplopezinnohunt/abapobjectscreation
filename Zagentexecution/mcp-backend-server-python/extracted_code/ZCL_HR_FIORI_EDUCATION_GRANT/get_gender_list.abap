  METHOD get_gender_list.

    DATA: ls_return TYPE ty_gender,
          ls_gender TYPE t77pad_gender_t,
          lt_gender TYPE STANDARD TABLE OF t77pad_gender_t.

    SELECT * INTO TABLE lt_gender
      FROM t77pad_gender_t
        WHERE spras = sy-langu
          AND molga = c_molga_99.

    LOOP AT lt_gender INTO ls_gender.
      CLEAR: ls_return.

      MOVE:
        ls_gender-gender TO ls_return-id,
        ls_gender-gender_text TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
