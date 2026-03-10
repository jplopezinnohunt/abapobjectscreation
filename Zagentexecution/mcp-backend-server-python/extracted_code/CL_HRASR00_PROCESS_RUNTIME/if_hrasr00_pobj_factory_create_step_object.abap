METHOD if_hrasr00_pobj_factory~create_step_object.

  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA level_attribute      TYPE pobjt_levelkey_with_attributes.
  DATA level_attribute_wa   TYPE pobjs_levelkey_with_attributes.
  DATA linked_levels      TYPE pobjt_linked_level_details.
  DATA linked_levels_wa   TYPE pobjs_linked_level_details.
  DATA step_attributes_pobj TYPE pobjt_level_attribute.
  DATA attributes_wa TYPE pobjs_level_attribute.


  is_ok = true.
  CLEAR step_guid.

  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      CALL FUNCTION 'GUID_CREATE'
        IMPORTING
          ev_guid_32 = step_guid.

      CALL METHOD cl_hrasr00_process_runtime=>convert_struc_2_indexnameval
        EXPORTING
          attr_structure = step_attributes
          operation      = 'INS'
        IMPORTING
          attributes     = step_attributes_pobj.

      CLEAR attributes_wa.
      MOVE '1' TO attributes_wa-field_index.
      attributes_wa-operation = 'INS'.
      MOVE 'PARENT_SCENARIO' TO attributes_wa-name.
      MOVE me->a_scenario TO attributes_wa-value.
      APPEND attributes_wa TO step_attributes_pobj.

      CLEAR linked_levels_wa.
      linked_levels_wa-parent_level = '2'.
      linked_levels_wa-parent_guid = me->a_scenario.
      linked_levels_wa-logical_anchor = c_la_step_2_scen.
      linked_levels_wa-child_level = '3'.
      linked_levels_wa-child_guid = step_guid.
      linked_levels_wa-operation = 'INS_OBJ'.
      linked_levels_wa-parent_lvl_cons_id = c_consumer_id.
      linked_levels_wa-child_lvl_cons_id = c_consumer_id.
      APPEND linked_levels_wa TO linked_levels.

      CLEAR level_attribute_wa.
      level_attribute_wa-level_id = '3'.
      level_attribute_wa-level_guid = step_guid.
      level_attribute_wa-attributes = step_attributes_pobj.
      APPEND level_attribute_wa TO level_attribute.


      CALL METHOD pobj_instance_process_obj->update
        CHANGING
          linked_levels   = linked_levels
          level_attribute = level_attribute.



*     Set the created step guid as an attribute of runtime class
      CALL METHOD me->set_current_step
        EXPORTING
          step_guid = step_guid.


    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist alredy
      CALL METHOD me->add_gen_msg_to_handler
        EXPORTING
          message_handler = message_handler
          gen_msg_typ     = 'UPDATE'.

*     Write the exception to application log
      CALL METHOD me->write_application_log
        EXPORTING
          message_handler = message_handler
          exception_obj   = exception_obj.

      is_ok = false.
      RETURN.
  ENDTRY.
ENDMETHOD.
