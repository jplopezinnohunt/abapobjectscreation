  METHOD get_attend_school_grade_list.

    DATA: ls_t7unpad_egsg_t TYPE t7unpad_egsg_t,
          ls_return         TYPE zshr_vh_generic,
          lt_t7unpad_egsg_t TYPE STANDARD TABLE OF t7unpad_egsg_t.

    SELECT * INTO TABLE lt_t7unpad_egsg_t
      FROM t7unpad_egsg_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_egsg_t INTO ls_t7unpad_egsg_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egsg_t-eggrd TO ls_return-id,
        ls_t7unpad_egsg_t-eggrt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
