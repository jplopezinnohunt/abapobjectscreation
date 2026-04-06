METHOD prerequisiteset_get_entityset.

  DATA: lv_barea        TYPE ben_area,
        ls_filter       TYPE /iwbep/s_mgw_select_option,
        ls_filter_range TYPE /iwbep/s_cod_select_option,
        ls_t74fy        TYPE t74fy,
        ls_prereq       TYPE cl_hcmfab_ben_enrollme_mpc=>ts_prerequisite,
        lt_t74fy        TYPE TABLE OF t74fy.

* Get the filter data
  LOOP AT it_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_filter_range INDEX 1.
    IF sy-subrc = 0 AND
       ls_filter_range-sign EQ 'I' AND ls_filter_range-option EQ 'EQ'.
      CASE ls_filter-property.
        WHEN 'BenefitArea'.
          lv_barea = ls_filter_range-low.
        WHEN OTHERS.
      ENDCASE.
    ENDIF.
  ENDLOOP.

  CHECK lv_barea IS NOT INITIAL.

  SELECT * FROM t74fy INTO TABLE lt_t74fy
    WHERE barea = lv_barea.

  LOOP AT lt_t74fy INTO ls_t74fy.
    MOVE-CORRESPONDING ls_t74fy TO ls_prereq.
    APPEND ls_prereq TO et_entityset.
    CLEAR ls_prereq.
  ENDLOOP.

ENDMETHOD.
