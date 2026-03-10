METHOD if_hrasr00_pobj_container~set_collision_container.

  DATA no_authority      TYPE boole_d.
  DATA msg               TYPE symsg.
  DATA dummy(1)          TYPE c.
  DATA exception_obj     TYPE REF TO cx_root.
  DATA data_container_params TYPE pobjt_container_params.
  DATA data_container_params_wa TYPE pobjs_container_params.
  DATA data_containers TYPE pobjt_containers.
  DATA data_container_wa TYPE pobjs_container.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA collision_containers TYPE pobjt_containers.
  DATA collision_container_wa TYPE pobjs_container.
  DATA collision_container_temp_wa TYPE pobjs_container.

  is_ok = true.
  is_authorized = false.

  TRY.
      IF no_auth_check EQ false.
*       Collision container is stored at the scenario level and can contain form fields from all the form scenario stages.
*       For checking authorization for collision container, we check whether user has authorization for the latest data container of scenario.
        CALL METHOD me->get_latest_data_container
          EXPORTING
            message_handler = message_handler
            no_auth_check   = false
            activity        = activity
          IMPORTING
            is_ok           = is_ok
            is_authorized   = is_authorized.

        CHECK is_ok         EQ true AND
              is_authorized EQ true.
      ENDIF.

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      CLEAR: data_container_params_wa, data_container_params.
      data_container_params_wa-level_id = '2'.
      data_container_params_wa-level_guid = me->a_scenario.
      data_container_params_wa-logical_anchor = c_la_collision_cont_scenario.
      APPEND data_container_params_wa TO data_container_params.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          container_params = data_container_params
        IMPORTING
          containers       = collision_containers.

      CLEAR : collision_container_wa.
      collision_container_wa-level_id = '2'.
      collision_container_wa-level_guid = me->a_scenario.
      collision_container_wa-logical_anchor = c_la_collision_cont_scenario.
      IF collision_containers IS INITIAL.
        collision_container_wa-operation = 'INS_OBJ'.
      ELSE.
        collision_container_wa-operation = 'UPD_OBJ'.
        READ TABLE collision_containers INDEX '1' INTO collision_container_temp_wa.
        MOVE collision_container_temp_wa-container_key   TO collision_container_wa-container_key.
      ENDIF.
      collision_container_wa-container_content = collision_container.
      APPEND collision_container_wa TO data_containers.

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
