  METHOD GET_STEP_FOR_A_REQUEST.

    DATA: lv_scenario_guid TYPE scmg_case_guid.

    SELECT SINGLE case_guid INTO lv_scenario_guid
      FROM t5asrscenarios
        WHERE parent_process = iv_process_guid ##WARN_OK.

    SELECT SINGLE case_guid INTO ov_step_guid
      FROM t5asrsteps
       WHERE parent_scenario = lv_scenario_guid
         AND proc_status = iv_status ##WARN_OK.



  ENDMETHOD.
