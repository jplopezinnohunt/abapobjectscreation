METHOD check_ui_conversion_available.

  DATA lv_ui_structure_name TYPE pad_sname.

  rv_ui_conversion_available = abap_false.

  SELECT sname FROM t588uiconvclas INTO (lv_ui_structure_name) UP TO 1 ROWS "#EC CI_GENBUFF
        WHERE                                         "#EC CI_SGLSELECT
          infty     = iv_infty AND
          stype     = 'MAIN' AND
          versionid = iv_versionid.
  ENDSELECT.

  IF sy-subrc EQ 0.
    rv_ui_conversion_available = abap_true.
  ENDIF.

ENDMETHOD.
