  METHOD get_expense_type_list.

    DATA: ls_t7unpad_egcos_t TYPE t7unpad_egcos_t,
          ls_return          TYPE zshr_vh_generic,
          lt_t7unpad_egcos_t TYPE STANDARD TABLE OF t7unpad_egcos_t.

    SELECT * INTO TABLE lt_t7unpad_egcos_t
      FROM t7unpad_egcos_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un
          AND endda >= sy-datum
          AND begda <= sy-datum.

    LOOP AT lt_t7unpad_egcos_t INTO ls_t7unpad_egcos_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egcos_t-excos TO ls_return-id,
        ls_t7unpad_egcos_t-exext TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

    SORT OT_list by txt ASCENDING.

  ENDMETHOD.
