  METHOD get_country_hl_and_ds.

    DATA: lv_ds_persa   TYPE werks,
          lv_dats       TYPE dats,
          ls_p0001      TYPE p0001,
          ls_p0391      TYPE p0391,
          ls_p0395      TYPE p0395,
          lt_p0001      TYPE  STANDARD TABLE OF p0001,
          lt_p0391      TYPE  STANDARD TABLE OF p0391,
          lt_p0395      TYPE  STANDARD TABLE OF p0395.

    lv_dats = iv_date.
    IF lv_dats IS INITIAL.
      lv_dats = sy-datum.
    ENDIF.

*   Get all necessary infotype data: 0391, 0395 or 0001 if 0395 doesn't exist
    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = iv_pernr
        infty     = '0391'
        begda     = lv_dats
        endda     = lv_dats
      TABLES
        infty_tab = lt_p0391.

    READ TABLE lt_p0391 INTO ls_p0391 INDEX 1.

    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = iv_pernr
        infty     = '0395'
        begda     = lv_dats
        endda     = lv_dats
      TABLES
        infty_tab = lt_p0395.
    DESCRIBE TABLE lt_p0395.

    IF sy-tfill = 0.
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
          pernr     = iv_pernr
          infty     = '0001'
          begda     = lv_dats
          endda     = lv_dats
        TABLES
          infty_tab = lt_p0001.

      READ TABLE lt_p0001 INTO ls_p0001 INDEX 1.
      lv_ds_persa = ls_p0001-werks.
    ELSE.
      READ TABLE lt_p0395 INTO ls_p0395 INDEX 1.
      lv_ds_persa = ls_p0395-werks.
    ENDIF.

*   Get country information
    ov_country_hl = ls_p0391-land1.
    SELECT SINGLE land1 INTO ov_country_ds
      FROM t500p
        WHERE persa = lv_ds_persa
          AND molga = c_molga_un.

  ENDMETHOD.
