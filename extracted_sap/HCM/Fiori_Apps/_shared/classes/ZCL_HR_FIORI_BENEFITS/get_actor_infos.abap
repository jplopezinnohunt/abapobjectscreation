  METHOD get_actor_infos.

    DATA: lv_usrid TYPE pa0105-usrid,
          ls_p0002 TYPE p0002,
          lt_p0002 TYPE STANDARD TABLE OF p0002.

    IF iv_pernr IS NOT INITIAL.
      ov_pernr = iv_pernr.
    ELSE.
      ov_usrid = sy-uname.
      MOVE sy-uname TO lv_usrid.

      SELECT SINGLE pernr INTO ov_pernr
        FROM pa0105
          WHERE subty = '0001'
            AND endda >= sy-datum
            AND begda <= sy-datum
            AND usrid = lv_usrid ##WARN_OK.
    ENDIF.

    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = ov_pernr
        infty     = '0002'
        begda     = sy-datum
        endda     = sy-datum
      TABLES
        infty_tab = lt_p0002.

    READ TABLE lt_p0002 INTO ls_p0002 INDEX 1.
    ov_first_name = ls_p0002-vorna.
    ov_last_name =  ls_p0002-nachn.
    ov_natio = ls_p0002-natio.

  ENDMETHOD.
