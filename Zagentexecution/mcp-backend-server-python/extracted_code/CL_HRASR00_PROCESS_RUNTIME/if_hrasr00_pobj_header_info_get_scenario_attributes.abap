METHOD if_hrasr00_pobj_header_info~get_scenario_attributes.

  DATA scenario TYPE scmg_case_guid.
  DATA exception_obj TYPE REF TO cx_root.
  DATA level_attr_params TYPE pobjt_level_key.
  DATA level_attr_params_wa TYPE pobjs_level_key.
  DATA level_attributes TYPE pobjt_levelkey_with_attributes.
  DATA level_attributes_wa TYPE pobjs_levelkey_with_attributes.
  DATA pobj_instance_process_obj   TYPE REF TO if_pobj_process_object.

  CLEAR scenario_attributes.
  is_ok = true.

  IF NOT scenario_guid IS INITIAL.
    scenario = scenario_guid.
  ELSE.
    scenario = a_scenario.
  ENDIF.

  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.


      CLEAR: level_attr_params, level_attr_params_wa.
      level_attr_params_wa-level_id = '2'.
      level_attr_params_wa-level_guid = scenario.
      APPEND level_attr_params_wa TO level_attr_params.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          level_attribute_params = level_attr_params
        IMPORTING
          level_attributes       = level_attributes.

      READ TABLE level_attributes INDEX '1' INTO level_attributes_wa.

      CALL METHOD cl_hrasr00_process_runtime=>convert_indexnameval_2_struc
        EXPORTING
          attributes     = level_attributes_wa-attributes
        IMPORTING
          attr_structure = scenario_attributes.
    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist alredy
      CALL METHOD me->add_gen_msg_to_handler
        EXPORTING
          message_handler = message_handler
          gen_msg_typ     = 'READ'.

*     Write the exception to application log
      CALL METHOD me->write_application_log
        EXPORTING
          message_handler = message_handler
          exception_obj   = exception_obj.

      is_ok = false.
      RETURN.
  ENDTRY.
ENDMETHOD.
