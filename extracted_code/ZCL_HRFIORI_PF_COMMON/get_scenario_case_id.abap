  METHOD get_scenario_case_id.

    DATA: lv_case_guid TYPE scmg_case_guid.

    SELECT SINGLE case_guid INTO lv_case_guid
      FROM t5asrprocesses
        WHERE reference_number = iv_ref_number ##WARN_OK.

    SELECT SINGLE case_guid INTO ov_scenario_guid
      FROM t5asrscenarios
        WHERE parent_process = lv_case_guid ##WARN_OK.

  ENDMETHOD.
