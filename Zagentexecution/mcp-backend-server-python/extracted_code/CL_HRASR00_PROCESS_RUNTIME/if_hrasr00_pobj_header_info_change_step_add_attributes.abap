METHOD if_hrasr00_pobj_header_info~change_step_add_attributes.

  DATA additional_attribute TYPE hrasr00_additional_attr.
  DATA attributes_wa TYPE pobjs_level_attribute.
  DATA step TYPE scmg_case_guid.
  DATA exception_obj TYPE REF TO cx_root.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA lt_attributes TYPE pobjt_level_attribute.
  DATA ls_level_attr_params TYPE pobjs_levelkey_with_attributes.
  DATA lt_level_attr_params TYPE pobjt_levelkey_with_attributes.
  CLEAR ls_level_attr_params.
  CLEAR lt_level_attr_params.
  CLEAR lt_attributes.


  is_ok = true.

  IF NOT step_guid IS INITIAL.
    step = step_guid.
  ELSE.
    step = a_step.
  ENDIF.
  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      LOOP AT step_additional_attributes INTO additional_attribute.
        MOVE-CORRESPONDING additional_attribute TO attributes_wa.
        MOVE additional_attribute-index TO attributes_wa-field_index.
        MOVE 'X' TO attributes_wa-non_standard_flag.
        attributes_wa-operation = 'INS'.
        APPEND attributes_wa TO lt_attributes.
        CLEAR attributes_wa.
      ENDLOOP.

      ls_level_attr_params-level_id = 3.
      ls_level_attr_params-level_guid = step.
      APPEND LINES OF lt_attributes TO ls_level_attr_params-attributes.
      APPEND ls_level_attr_params TO lt_level_attr_params.

      CALL METHOD pobj_instance_process_obj->update
        CHANGING
          level_attribute = lt_level_attr_params.

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
