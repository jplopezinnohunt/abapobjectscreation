  METHOD get_duty_station_infos.

    DATA: lv_pernr           TYPE persno,
          lv_userid          TYPE sysid,
          lv_is_ok           TYPE boole_d,
          lt_ds_tab          TYPE hrpadun_ds,
          lo_read_infotype   TYPE REF TO if_hrpa_read_infotype,
          lo_message_handler TYPE REF TO cl_hrpa_message_list.

*   Get PERNR of connected user if needed
    IF iv_pernr IS INITIAL.
      MOVE sy-uname TO lv_userid.
      SELECT SINGLE pernr INTO lv_pernr
        FROM pa0105
          WHERE subty = '0001'
            AND endda >= sy-datum
            AND begda <= sy-datum
            AND usrid = lv_userid ##WARN_OK.
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.

*   Search different citerias
    CREATE OBJECT lo_message_handler.

    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
      IMPORTING
        read_infotype = lo_read_infotype.

    CALL METHOD cl_hrpa_infotype_0960=>get_ds_tab
      EXPORTING
        pernr           = lv_pernr
        read_infotype   = lo_read_infotype
        message_handler = lo_message_handler
      IMPORTING
        ds_tab          = lt_ds_tab
        is_ok           = lv_is_ok.

    ot_ds = lt_ds_tab.

    IF lv_is_ok = abap_true.
      CALL METHOD cl_hrpa_infotype_0960=>bl_ds
        EXPORTING
          date            = iv_begda
          ds_tab          = lt_ds_tab
          message_handler = lo_message_handler
        IMPORTING
          ds              = os_ds.

    ENDIF.
  ENDMETHOD.
