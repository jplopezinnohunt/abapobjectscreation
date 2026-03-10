  METHOD get_metadata_form_fields.

    SELECT * INTO TABLE ot_metadata_fields
      FROM t5asrfio_mdata
        WHERE form_scenario = iv_form_scenario
        AND form_scen_vers = iv_scenario_version.           "'00000'

  ENDMETHOD.
