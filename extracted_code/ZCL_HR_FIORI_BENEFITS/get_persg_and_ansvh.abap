  METHOD get_persg_and_ansvh.

    DATA: lv_dats  TYPE dats,
          ls_p0001 TYPE p0001,
          lt_p0001 TYPE  STANDARD TABLE OF p0001.

    lv_dats = iv_date.
    IF lv_dats IS INITIAL.
      lv_dats = sy-datum.
    ENDIF.

    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = iv_pernr
        infty     = '0001'
        begda     = lv_dats
        endda     = lv_dats
      TABLES
        infty_tab = lt_p0001.
    READ TABLE lt_p0001 INTO ls_p0001 INDEX 1.

    ov_ansvh = ls_p0001-ansvh.
    ov_persg = ls_p0001-persg.

  ENDMETHOD.
