METHOD orgchartpictures_get_entity.
  DATA lt_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.

  CLEAR: er_entity, es_response_context.

  lt_keys = io_tech_request_context->get_source_keys( ).
  IF lines( lt_keys ) = 0.
    lt_keys = io_tech_request_context->get_keys( ).
  ENDIF.

  LOOP AT lt_keys INTO ls_key.
    CASE ls_key-name.
      WHEN 'APPLICATION_ID'.
        er_entity-application_id = ls_key-value.
      WHEN 'OBJECT_ID'.
        er_entity-object_id = ls_key-value.
      WHEN 'OBJECT_TYPE'.
        er_entity-object_type = ls_key-value.
    ENDCASE.
  ENDLOOP.
ENDMETHOD.
