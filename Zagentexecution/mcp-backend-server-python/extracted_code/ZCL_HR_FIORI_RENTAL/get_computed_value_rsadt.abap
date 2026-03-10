  METHOD get_computed_value_rsadt.

    DATA: lv_index           TYPE i,
          lv_lines           TYPE i,
          lv_dseod           TYPE pun_dseod,
          ls_ds              TYPE pun_ds,
          ls_ds2             TYPE pun_ds,
          ls_prev_ds         TYPE pun_ds,
          lt_ds_tab          TYPE hrpadun_ds.

    get_duty_station_infos( EXPORTING iv_begda = iv_begda
                                      iv_pernr = iv_pernr
                                IMPORTING os_ds = ls_ds
                                          ot_ds = lt_ds_tab ).

    SORT lt_ds_tab BY endda DESCENDING.

    READ TABLE lt_ds_tab INTO ls_ds2
      WITH KEY begda =  ls_ds-begda  endda = ls_ds-endda.
    lv_index = sy-tabix.
    DESCRIBE TABLE lt_ds_tab LINES lv_lines.

    LOOP AT  lt_ds_tab INTO ls_ds2 FROM  lv_index TO lv_lines
                                   WHERE stat2 = c_active.
      IF ls_prev_ds IS NOT INITIAL AND ls_prev_ds-dstat NE ls_ds2-dstat.
        CLEAR ls_prev_ds.
        EXIT.
      ELSE.
        lv_dseod = ls_ds2-dseod.
      ENDIF.

      ls_prev_ds = ls_ds2.
    ENDLOOP.

    IF ls_ds IS NOT INITIAL.
      ov_rsadt = lv_dseod.
    ELSE.
      ov_rsadt = iv_begda.
    ENDIF.

  ENDMETHOD.
