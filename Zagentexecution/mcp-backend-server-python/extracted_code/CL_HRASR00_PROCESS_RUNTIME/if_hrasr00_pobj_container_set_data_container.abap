METHOD if_hrasr00_pobj_container~set_data_container.


  DATA dummy(1)              TYPE c.
  DATA exception_obj         TYPE REF TO cx_root.
  DATA data_container_new    TYPE xstring.
  DATA data_container_id_old TYPE bapiguid.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA data_container_params TYPE pobjt_container_params.
  DATA data_container_params_wa TYPE pobjs_container_params.
  DATA data_containers TYPE pobjt_containers.
  DATA data_containers_deassign TYPE pobjt_containers.
  DATA data_container_wa TYPE pobjs_container.
  DATA step_data_containers TYPE pobjt_containers.
  DATA step_data_container_wa TYPE pobjs_container.
  DATA step_data_container_temp_wa TYPE pobjs_container.
  DATA latest_data_containers TYPE pobjt_containers.
  DATA latest_data_container_wa TYPE pobjs_container.
  DATA link_cont_to_scenario TYPE boole_d.
  DATA message_list TYPE REF TO cl_hrbas_message_list.
  DATA error_messages TYPE hrbas_message_tab.
  DATA error_message TYPE  hrbas_message.
  DATA reference_number TYPE asr_reference_number.

* Initialize
  CREATE OBJECT message_list.


  is_ok = true.
  is_authorized = false.

  TRY.
      IF no_auth_check EQ false.
        CALL METHOD me->check_container_auth
          EXPORTING
            message_handler = message_handler
            activity        = activity
            data_container  = data_container
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
      data_container_params_wa-level_id = '3'.
      data_container_params_wa-level_guid = me->a_step.
      data_container_params_wa-logical_anchor = c_la_data_cont_step.
      APPEND data_container_params_wa TO data_container_params.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          container_params = data_container_params
        IMPORTING
          containers       = step_data_containers.
*     In case where there is no data container id i.e. there is no data container stored against the step
*     and also, there is no data container supplied also to this method, we get the latest data container
*     from the scenario level and set the same against the current step.
*     The use case mentioned above can arise when there is absolutely no difference between the data containers of two successive steps.
*     In such a case, the Process object handler class clears the data container being passed to process object runtime class.
*      IF data_container_id IS INITIAL AND data_container IS INITIAL.
      IF step_data_containers IS INITIAL AND data_container IS INITIAL.
*       get latest data container and version
*        CALL METHOD scenario_instance->get_latest_data_container
*          IMPORTING
*            data_container = data_container_new
*            version        = version.
        CLEAR: data_container_params_wa, data_container_params.
        data_container_params_wa-level_id = '2'.
        data_container_params_wa-level_guid = me->a_scenario.
        data_container_params_wa-logical_anchor = c_la_data_cont_scen.
        APPEND data_container_params_wa TO data_container_params.

        CLEAR : data_containers, data_container_wa.

        CALL METHOD pobj_instance_process_obj->read
          EXPORTING
            container_params = data_container_params
          IMPORTING
            containers       = latest_data_containers.
        READ TABLE latest_data_containers INDEX '1' INTO latest_data_container_wa.
        step_data_container_wa-level_id = '3'.
        step_data_container_wa-level_guid = me->a_step.
        step_data_container_wa-logical_anchor = c_la_data_cont_step.
        step_data_container_wa-container_content = latest_data_container_wa-container_content.
        step_data_container_wa-container_attributes = latest_data_container_wa-container_attributes.
        step_data_container_wa-operation = 'INS_OBJ'.
        APPEND step_data_container_wa TO data_containers.
        link_cont_to_scenario = 'X'.

      ELSE.
        CLEAR : step_data_container_wa.
        step_data_container_wa-level_id = '3'.
        step_data_container_wa-level_guid = me->a_step.
        step_data_container_wa-logical_anchor = c_la_data_cont_step.
        IF step_data_containers IS INITIAL AND data_container IS NOT INITIAL.
          step_data_container_wa-operation = 'INS_OBJ'.
          link_cont_to_scenario = 'X'.
          step_data_container_wa-container_content = data_container.
          APPEND step_data_container_wa TO data_containers.
        ELSEIF step_data_containers IS NOT INITIAL AND data_container IS NOT INITIAL.
          step_data_container_wa-operation = 'UPD_OBJ'.
          READ TABLE step_data_containers INDEX '1' INTO step_data_container_temp_wa.
          MOVE step_data_container_temp_wa-container_key   TO step_data_container_wa-container_key.
          step_data_container_wa-container_content = data_container.
          APPEND step_data_container_wa TO data_containers.
        ENDIF.
      ENDIF.
      IF data_containers IS NOT INITIAL.
        CALL METHOD pobj_instance_process_obj->update
          CHANGING
            containers = data_containers.
      ENDIF.

      IF link_cont_to_scenario EQ 'X'.
* Linking the Latest Data Container to the Scenario parallely deassigning the Old data container linked to it.


        CLEAR: data_container_params_wa, data_container_params, latest_data_container_wa.
        data_container_params_wa-level_id = '2'.
        data_container_params_wa-level_guid = me->a_scenario.
        data_container_params_wa-logical_anchor = c_la_data_cont_scen.
        APPEND data_container_params_wa TO data_container_params.
        CALL METHOD pobj_instance_process_obj->read
          EXPORTING
            container_params = data_container_params
          IMPORTING
            containers       = latest_data_containers.
        IF latest_data_containers IS NOT INITIAL.
          READ TABLE latest_data_containers INDEX '1' INTO latest_data_container_wa.
          latest_data_container_wa-operation = 'DEL_LINK'.
          APPEND latest_data_container_wa TO data_containers_deassign.
          CALL METHOD pobj_instance_process_obj->update
            CHANGING
              containers = data_containers_deassign.
        ENDIF.

        CLEAR data_container_wa.
        READ TABLE data_containers INDEX '1' INTO data_container_wa.
        data_container_wa-level_id = '2'.
        data_container_wa-level_guid = me->a_scenario.
        data_container_wa-logical_anchor = c_la_data_cont_scen.
        data_container_wa-operation = 'INS_LINK'.
        MODIFY data_containers FROM data_container_wa TRANSPORTING level_id level_guid logical_anchor operation
        WHERE container_key = data_container_wa-container_key .
        CALL METHOD pobj_instance_process_obj->update
          CHANGING
            containers = data_containers.
      ENDIF.

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
