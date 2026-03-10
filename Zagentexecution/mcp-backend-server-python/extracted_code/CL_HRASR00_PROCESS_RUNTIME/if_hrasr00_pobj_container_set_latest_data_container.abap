METHOD if_hrasr00_pobj_container~set_latest_data_container.

  DATA exception_obj       TYPE REF TO cx_root.
  DATA steps_in_scenario   TYPE hrasr00step_tab.
  DATA scenario            TYPE asr_guid.
  DATA data_containers TYPE pobjt_containers.
  DATA data_container_wa TYPE pobjs_container.
  DATA scen_data_containers TYPE pobjt_containers.
  DATA scen_data_container_wa TYPE pobjs_container.
  DATA latest_data_containers TYPE pobjt_containers.
  DATA ls_link_scenario_read TYPE pobjs_linked_level_params.
  DATA lt_link_scenario_read TYPE pobjt_linked_level_params.
  DATA lt_steps TYPE pobjt_linked_level_details.
  DATA ls_steps TYPE pobjs_linked_level_details.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA data_container_params TYPE pobjt_container_params.
  DATA data_container_params_wa TYPE pobjs_container_params.
  DATA no_of_steps TYPE i.
  is_ok = true.
  is_authorized = false.

  CHECK data_container IS NOT INITIAL.
* In case caller has passed the scenario guid as INITIAL,
* use the one stored in current context of POBJ Runtime class.
* This case is possible in case of single step processes,
* where from POBJ handler RFC, the scenario guid can be passed as INITIAL.
  IF NOT scenario_guid IS INITIAL.
    scenario = scenario_guid.
  ELSE.
    scenario = a_scenario.
  ENDIF.

  TRY.
* Check authorization for data container
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
      data_container_params_wa-level_id = '2'.
      data_container_params_wa-level_guid = scenario.
      data_container_params_wa-logical_anchor = c_la_data_cont_scen.
      APPEND data_container_params_wa TO data_container_params.

      CLEAR : data_containers, data_container_wa.

      CALL METHOD pobj_instance_process_obj->read
        EXPORTING
          container_params = data_container_params
        IMPORTING
          containers       = latest_data_containers.
      IF latest_data_containers IS NOT INITIAL.
        READ TABLE latest_data_containers INDEX '1' INTO scen_data_container_wa.
        scen_data_container_wa-operation = 'UPD_OBJ'.
      ELSE.
        scen_data_container_wa-operation = 'INS_OBJ'.
        scen_data_container_wa-level_id = '2'.
        scen_data_container_wa-level_guid = scenario.
        scen_data_container_wa-logical_anchor = c_la_data_cont_scen.
      ENDIF.
      scen_data_container_wa-container_content = data_container.
      APPEND scen_data_container_wa TO data_containers.

* Update the data container for the last step.
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
