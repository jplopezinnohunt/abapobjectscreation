  METHOD get_last_step_for_a_request.

    DATA: lv_scenario_guid TYPE scmg_case_guid,
          ls_step          TYPE t5asrsteps,
          lt_steps         TYPE STANDARD TABLE OF t5asrsteps.

    SELECT SINGLE case_guid INTO lv_scenario_guid
      FROM t5asrscenarios
        WHERE parent_process = iv_process_guid ##WARN_OK.

    SELECT * INTO TABLE lt_steps
      FROM t5asrsteps
        UP TO 3 ROWS
          WHERE parent_scenario = lv_scenario_guid
          ORDER BY start_date DESCENDING start_time DESCENDING.

    READ TABLE lt_steps INTO ls_step INDEX 1.
    ov_step_guid = ls_step-case_guid.

  ENDMETHOD.
