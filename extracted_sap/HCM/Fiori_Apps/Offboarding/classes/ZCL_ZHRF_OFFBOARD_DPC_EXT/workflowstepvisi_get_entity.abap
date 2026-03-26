  METHOD workflowstepvisi_get_entity.

    DATA: lv_request_id TYPE string,
          lv_step_code  TYPE ze_hrfiori_offboarding_step,
          lv_step_txt   TYPE ze_hrfiori_offboarding_step_tx,
          lf_visibility TYPE boolean,
          ls_key        TYPE /iwbep/s_mgw_name_value_pair,
          ls_result     TYPE zcl_zhrf_offboard_mpc=>ts_workflowstepvisibility.

*   Get parameters
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'Guid' ##NO_TEXT.
    IF sy-subrc EQ 0.
      MOVE ls_key-value TO lv_request_id.
    ENDIF.

    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'StepCode' ##NO_TEXT.
    IF sy-subrc EQ 0.
      MOVE ls_key-value TO lv_step_code.
    ENDIF.

*   Get workflow step information: step name
    SELECT SINGLE step_txt INTO lv_step_txt
      FROM zthrfiori_offb_s
        WHERE step_code = lv_step_code
          AND language = sy-langu ##WARN_OK.

*   Check visibility
    zcl_hr_fiori_offboarding_req=>check_wf_step_visibility( EXPORTING iv_guid = lv_request_id
                                                                      iv_step = lv_step_code
                                                            IMPORTING ov_to_be_displayed = lf_visibility  ).

*   return result
    ls_result-guid = lv_request_id.
    ls_result-stepcode = lv_step_code.
    ls_result-steptxt = lv_step_txt.
    ls_result-visible = lf_visibility.

    er_entity = ls_result.

  ENDMETHOD.
