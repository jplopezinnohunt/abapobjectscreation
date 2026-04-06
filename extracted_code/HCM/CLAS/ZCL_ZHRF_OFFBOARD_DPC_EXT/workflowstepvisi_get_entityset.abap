  METHOD workflowstepvisi_get_entityset.

    DATA: lv_guid         TYPE string,
          lv_guid_raw     TYPE ze_hrfiori_guidreq,
          lv_pernr        TYPE pernr_d,
          ls_filter       TYPE /iwbep/s_mgw_select_option,
          ls_filter_range TYPE /iwbep/s_cod_select_option,
          ls_wf_step      TYPE zthrfiori_offb_s,
          ls_result       TYPE zcl_zhrf_offboard_mpc=>ts_workflowstepvisibility,
          lt_wf_step      TYPE STANDARD TABLE OF zthrfiori_offb_s,
          lt_result       TYPE zcl_zhrf_offboard_mpc=>tt_workflowstepvisibility.

*   Get filter values
    IF it_filter_select_options[] IS NOT INITIAL.
      LOOP AT it_filter_select_options INTO ls_filter.

        LOOP AT ls_filter-select_options INTO ls_filter_range.
          CASE ls_filter-property.
            WHEN 'Guid'.
              MOVE ls_filter_range-low TO lv_guid.
              lv_guid_raw = lv_guid.
          ENDCASE.
        ENDLOOP.
      ENDLOOP.
    ENDIF.

*   Get workflow step information
    SELECT * INTO TABLE lt_wf_step
      FROM zthrfiori_offb_s
        WHERE language = sy-langu.

*   Get request information
    SELECT SINGLE creator_pernr INTO lv_pernr
      FROM zthrfiori_hreq
        WHERE guid = lv_guid_raw.

    LOOP AT lt_wf_step INTO ls_wf_step.
      ls_result-guid = lv_guid.
      ls_result-stepcode = ls_wf_step-step_code.
      ls_result-steptxt = ls_wf_step-step_txt.

*     Check visibility
      zcl_hr_fiori_offboarding_req=>check_wf_step_visibility(
        EXPORTING iv_guid = lv_guid
                  iv_pernr = lv_pernr
                  iv_step = ls_wf_step-step_code
        IMPORTING ov_to_be_displayed = ls_result-visible  ).

      APPEND ls_result TO lt_result.
    ENDLOOP.

    et_entityset = lt_result.

  ENDMETHOD.
