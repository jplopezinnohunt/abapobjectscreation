  METHOD get_duty_station_sm_list.

    DATA: ls_t7unpad_ds_t TYPE t7unpad_ds_t,
          ls_return       TYPE ty_duty_station_sm,
          lt_t7unpad_ds_t TYPE STANDARD TABLE OF t7unpad_ds_t.

    SELECT * INTO TABLE lt_t7unpad_ds_t
      FROM t7unpad_ds_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_ds_t INTO ls_t7unpad_ds_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_ds_t-dstat TO ls_return-id,
        ls_t7unpad_ds_t-dstxt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
