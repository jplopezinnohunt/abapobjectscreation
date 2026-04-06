METHOD employeepictures_get_entityset.

  DATA: lt_keys TYPE /iwbep/t_mgw_tech_pairs,
        ls_key TYPE /iwbep/s_mgw_tech_pair,
        ls_entity TYPE cl_hcmfab_common_mpc=>ts_employeepicture.

  CLEAR: et_entityset, es_response_context.

  lt_keys = io_tech_request_context->get_source_keys( ).
  READ TABLE lt_keys INTO ls_key WITH KEY name = 'EMPLOYEE_NUMBER'.
  IF sy-subrc = 0.
    ls_entity-employee_id = ls_key-value.
  ENDIF.
  READ TABLE lt_keys INTO ls_key WITH KEY name = 'APPLICATION_ID'.
  IF sy-subrc = 0.
    ls_entity-application_id = ls_key-value.
  ENDIF.

  APPEND ls_entity TO et_entityset.
ENDMETHOD.
