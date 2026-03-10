  METHOD get_computed_value_dstat_egdds.

    DATA: lv_pernr           TYPE persno,
          ls_ds              TYPE pun_ds,
          lt_ds_tab2         TYPE hrpadun_ds_tab,
          lt_ds_tab          TYPE hrpadun_ds_tab,
          lo_read_infotype   TYPE REF TO if_hrpa_read_infotype,
          lo_message_handler TYPE REF TO cl_hrpa_message_list,
          lo_benefits_util   TYPE REF TO zcl_hr_fiori_benefits.

    IF iv_pernr IS INITIAL.
      CREATE OBJECT lo_benefits_util.
      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.

    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
      IMPORTING
        read_infotype = lo_read_infotype.
    CREATE OBJECT lo_message_handler.

    CALL METHOD cl_hrpa_infotype_0960=>get_ds_tab
      EXPORTING
        pernr           = lv_pernr
        read_infotype   = lo_read_infotype
        message_handler = lo_message_handler
      IMPORTING
        ds_tab          = lt_ds_tab.

    LOOP AT lt_ds_tab INTO ls_ds WHERE begda <= iv_egyto
                               AND   endda >= iv_egyfr.
      APPEND ls_ds TO lt_ds_tab2.
    ENDLOOP.

    LOOP AT lt_ds_tab2 INTO ls_ds WHERE begda <= iv_egyto
                                 AND   endda >= iv_egyfr.
      EXIT.
    ENDLOOP.

    ov_dstat = ls_ds-ext_dstat.
    ov_egdds = ls_ds-egdds.

  ENDMETHOD.
