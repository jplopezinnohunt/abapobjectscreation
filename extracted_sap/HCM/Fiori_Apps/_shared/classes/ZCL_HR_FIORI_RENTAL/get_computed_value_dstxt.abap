  METHOD get_computed_value_dstxt.

    DATA: lv_dstat           TYPE pun_dstat,
          ls_ds              TYPE pun_ds.

    get_duty_station_infos( EXPORTING iv_begda = iv_begda
                                      iv_pernr = iv_pernr
                                IMPORTING os_ds = ls_ds ).

    lv_dstat = ls_ds-ext_dstat.

    CALL METHOD cl_hr_t7unpad_ds_t=>read_text
      EXPORTING
        molga = c_molga_un
        dstat = lv_dstat
      RECEIVING
        text  = ov_dstxt.

  ENDMETHOD.
