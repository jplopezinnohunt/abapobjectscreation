  METHOD get_computed_value_rsrea.

    DATA: lv_dstat           TYPE pun_dstat,
          lv_rssch           TYPE pun_rssch,
          ls_ds              TYPE pun_ds,
          ls_ds1p            TYPE t7unpad_ds1p.

    get_duty_station_infos( EXPORTING iv_begda = iv_begda
                                      iv_pernr = iv_pernr
                            IMPORTING os_ds = ls_ds ).

    lv_dstat = ls_ds-ext_dstat.

    CALL METHOD cl_hr_t7unpad_ds1p=>read_at_date
      EXPORTING
        molga = c_molga_un
        dstat = lv_dstat
        date  = iv_begda
      RECEIVING
        ds1p  = ls_ds1p.

    lv_rssch = ls_ds1p-rssch.

    IF lv_rssch = c_schema.
      ov_rsrea = c_newcom.
    ELSE.
      ov_rsrea = c_regulr.
    ENDIF.

  ENDMETHOD.
