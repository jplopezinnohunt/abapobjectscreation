  METHOD get_attachment_inc_number.

    DATA: lv_max_inc_nb TYPE ze_hrfiori_incrment_nb.

    SELECT MAX( inc_nb ) INTO lv_max_inc_nb
      FROM zthrfiori_attach
        WHERE guid = iv_guid
          AND attach_type = iv_attach_type.

    IF lv_max_inc_nb IS INITIAL.
      lv_max_inc_nb = c_inc_nb_init_value.
    ENDIF.

    ov_inc_nb = lv_max_inc_nb.

  ENDMETHOD.
