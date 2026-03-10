  METHOD check_ds_value.

    CONSTANTS: lc_home TYPE pun_dscat VALUE 'H'.

    DATA: lv_dscat           TYPE pun_dscat,
          lv_is_ok           TYPE boole_d ##NEEDED,
          ls_ds              TYPE pun_ds,
          lt_ds_tab          TYPE hrpadun_ds,
          lo_read_infotype   TYPE REF TO if_hrpa_read_infotype,
          lo_message_handler TYPE REF TO cl_hrpa_message_list.

*   Initialize return value
    ov_is_eligible = abap_false.

    CREATE OBJECT lo_message_handler.
    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
      IMPORTING
        read_infotype = lo_read_infotype.

    CALL METHOD cl_hrpa_infotype_0960=>get_ds_tab
      EXPORTING
        pernr           = iv_pernr
        read_infotype   = lo_read_infotype
        message_handler = lo_message_handler
      IMPORTING
        ds_tab          = lt_ds_tab
        is_ok           = lv_is_ok.

    CALL METHOD cl_hrpa_infotype_0960=>bl_ds
      EXPORTING
        date            = sy-datum
        ds_tab          = lt_ds_tab
        message_handler = lo_message_handler
      IMPORTING
        ds              = ls_ds.

    lv_dscat = ls_ds-ext_dscat.

    IF lv_dscat <> lc_home.
      ov_is_eligible = abap_true.
    ENDIF.

  ENDMETHOD.
