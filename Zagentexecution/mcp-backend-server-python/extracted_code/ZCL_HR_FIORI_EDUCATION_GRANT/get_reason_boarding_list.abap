  METHOD get_reason_boarding_list.

    DATA: ls_t7unpad_egrs_t TYPE t7unpad_egrs_t,
          ls_return         TYPE ZsHR_VH_GENERIC,
          lt_t7unpad_egrs_t TYPE STANDARD TABLE OF t7unpad_egrs_t.

    SELECT * INTO TABLE lt_t7unpad_egrs_t
      FROM t7unpad_egrs_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_egrs_t INTO ls_t7unpad_egrs_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egrs_t-egbrs TO ls_return-id,
        ls_t7unpad_egrs_t-egbrt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
