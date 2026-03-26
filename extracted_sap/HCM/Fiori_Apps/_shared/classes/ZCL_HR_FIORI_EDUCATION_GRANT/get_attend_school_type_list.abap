  METHOD get_attend_school_type_list.

    DATA: ls_t7unpad_egst_t TYPE t7unpad_egst_t,
          ls_return         TYPE ty_attendance_school_type,
          lt_t7unpad_egst_t TYPE STANDARD TABLE OF t7unpad_egst_t.

    SELECT * INTO TABLE lt_t7unpad_egst_t
      FROM t7unpad_egst_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_egst_t INTO ls_t7unpad_egst_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egst_t-egtyp TO ls_return-id,
        ls_t7unpad_egst_t-egtyt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
