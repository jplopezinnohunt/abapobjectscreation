METHOD get_versionid_from_sname.

  DATA lv_offset      TYPE i.
  DATA lv_countrykey  TYPE intca.
  DATA ls_t500l       TYPE t500l.

  IF iv_ui_structure_name CP '*HCMT_BSP_PA_*' ##no_text .
    lv_offset = sy-fdpos + 12.
*we get the Country Key from HCMP_BSP_PA_* Structure
    lv_countrykey = iv_ui_structure_name+lv_offset(2).
    IF lv_countrykey = 'XX'.
      lv_countrykey = '99'.
    ENDIF.
*we get Version Id using Country Key
    SELECT * FROM t500l INTO ls_t500l UP TO 1 ROWS
             WHERE intca = lv_countrykey.
    ENDSELECT.
    IF sy-subrc = 0.
      rv_versionid = ls_t500l-molga.
    ENDIF.
  ENDIF.

ENDMETHOD.
