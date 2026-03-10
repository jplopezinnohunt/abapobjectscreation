method IF_HRASR00_POBJ_CONTAINER~SET_XI_DATA_CONTAINER.
  DATA no_authority   TYPE boole_d.
  DATA msg            TYPE symsg.
  DATA dummy(1)       TYPE c.
  DATA exception_obj  TYPE REF TO cx_root.
  DATA scenario_guid  TYPE asr_guid.
  DATA scenario_guids LIKE TABLE OF scenario_guid.
  DATA xi_container_params TYPE pobjt_container_params.
  DATA xi_container_params_wa TYPE pobjs_container_params.
  DATA data_containers TYPE pobjt_containers.
  DATA data_container_wa TYPE pobjs_container.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA xi_data_containers TYPE pobjt_containers.
  DATA xi_data_container_wa TYPE pobjs_container.
  DATA xi_data_container_temp_wa TYPE pobjs_container.
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
      CHECK NOT xi_data_container IS INITIAL.

      CLEAR: xi_container_params_wa, xi_container_params.
      xi_container_params_wa-level_id = '1'.
      xi_container_params_wa-level_guid = me->a_pobj.
      xi_container_params_wa-logical_anchor = c_la_xidat_cont_process.
      APPEND xi_container_params_wa TO xi_container_params.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          container_params = xi_container_params
        IMPORTING
          containers       = xi_data_containers.

      CLEAR : xi_data_container_wa.
      xi_data_container_wa-level_id = '1'.
      xi_data_container_wa-level_guid = me->a_pobj.
      xi_data_container_wa-logical_anchor = c_la_xidat_cont_process.

      IF xi_data_containers IS INITIAL.
        xi_data_container_wa-operation = 'INS_OBJ'.
      ELSE.
        xi_data_container_wa-operation = 'UPD_OBJ'.
        READ TABLE xi_data_containers INDEX '1' INTO xi_data_container_temp_wa.
          MOVE xi_data_container_temp_wa-container_key   TO xi_data_container_wa-container_key.
      ENDIF.

      xi_data_container_wa-container_content = xi_data_container.


      APPEND xi_data_container_wa TO data_containers.

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
endmethod.
