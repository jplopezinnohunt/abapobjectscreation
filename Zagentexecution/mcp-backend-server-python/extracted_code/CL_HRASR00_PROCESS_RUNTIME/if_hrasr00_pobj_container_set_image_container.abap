METHOD if_hrasr00_pobj_container~set_image_container.
  DATA no_authority   TYPE boole_d.
  DATA msg            TYPE symsg.
  DATA dummy(1)       TYPE c.
  DATA exception_obj  TYPE REF TO cx_root.
  DATA scenario_guid  TYPE asr_guid.
  DATA scenario_guids LIKE TABLE OF scenario_guid.
  DATA image_container_params TYPE pobjt_container_params.
  DATA image_container_params_wa TYPE pobjs_container_params.
  DATA data_containers TYPE pobjt_containers.
  DATA data_container_wa TYPE pobjs_container.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA image_containers TYPE pobjt_containers.
  DATA image_container_wa TYPE pobjs_container.
  DATA latest_image_container_wa TYPE pobjs_container.
  DATA attributes_nameval_wa  TYPE pobjs_ind_nam_val_ops.

  is_ok = true.
  is_authorized = false.

  TRY.
* get all scenarios and get data container for each scenario
* check auth against each data container
      IF no_auth_check EQ false.
        CALL METHOD me->get_all_scenarios
          EXPORTING
            message_handler = message_handler
          IMPORTING
            scenarios       = scenario_guids
            is_ok           = is_ok.
        CHECK is_ok EQ true.

        LOOP AT scenario_guids INTO scenario_guid.
          CALL METHOD me->get_latest_data_container
            EXPORTING
              scenario_guid   = scenario_guid
              message_handler = message_handler
              no_auth_check   = false
              activity        = activity
            IMPORTING
              is_ok           = is_ok
              is_authorized   = is_authorized.
          IF is_ok         EQ false OR
             is_authorized EQ false.
            RETURN.
          ENDIF.
        ENDLOOP.
      ENDIF.

** Get the instance of process object
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

*no need to process further if empty XML string
      CHECK NOT image_container IS INITIAL.

      CLEAR: image_container_params_wa, image_container_params.
      image_container_params_wa-level_id = '1'.
      image_container_params_wa-level_guid = me->a_pobj.
      image_container_params_wa-logical_anchor = c_la_image_cont_process.
      APPEND image_container_params_wa TO image_container_params.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          container_params = image_container_params
        IMPORTING
          containers       = image_containers.

      CLEAR : image_container_wa.
      image_container_wa-level_id = '1'.
      image_container_wa-level_guid = me->a_pobj.
      image_container_wa-logical_anchor = c_la_image_cont_process.
      IF image_containers IS INITIAL.
        image_container_wa-operation = 'INS_OBJ'.
      ELSE.
        READ TABLE image_containers INDEX 1 INTO latest_image_container_wa.
        CHECK image_container NE latest_image_container_wa-container_content.
        image_container_wa-operation = 'INS_VER'.
        image_container_wa-container_key = latest_image_container_wa-container_key.
      ENDIF.
      image_container_wa-container_content = image_container.
* fill step object GUID as an attribute also
      attributes_nameval_wa-field_index = '1'.
      attributes_nameval_wa-name = 'ASR_STEP_CASE_GUID'.
      attributes_nameval_wa-value = step_guid.
      attributes_nameval_wa-operation = 'INS'.
      APPEND attributes_nameval_wa TO image_container_wa-container_attributes.

      APPEND image_container_wa TO data_containers.

      CALL METHOD pobj_instance_process_obj->update
        CHANGING
          containers = data_containers.

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
