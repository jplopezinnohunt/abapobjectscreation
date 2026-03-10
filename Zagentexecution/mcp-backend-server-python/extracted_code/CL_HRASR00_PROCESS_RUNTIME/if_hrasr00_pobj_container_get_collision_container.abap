METHOD if_hrasr00_pobj_container~get_collision_container.

  DATA scenario                TYPE asr_guid.
  DATA exception_obj           TYPE REF TO cx_root.
  DATA collision_container_key TYPE hrasr00doc_key.
  DATA ls_containers_read      TYPE pobjs_container_params.
  DATA lo_pobj_instance        TYPE REF TO if_pobj_process_object.
  DATA lt_containers_read      TYPE pobjt_container_params.
  DATA lt_containers           TYPE pobjt_containers.
  DATA ls_containers           TYPE pobjs_container.
  CLEAR lt_containers.
  CLEAR ls_containers.
  CLEAR ls_containers_read.
  CLEAR lt_containers_read.
  CLEAR collision_container.
  is_ok = true.
  is_authorized = false.

  IF NOT scenario_guid IS INITIAL.
    scenario = scenario_guid.
  ELSE.
    scenario = a_scenario.
  ENDIF.

  TRY.
      IF no_auth_check EQ false.
* get the data container for auth check
        CALL METHOD me->get_latest_data_container
          EXPORTING
            scenario_guid   = scenario
            message_handler = message_handler
            no_auth_check   = no_auth_check
            activity        = activity
          IMPORTING
            is_ok           = is_ok
            is_authorized   = is_authorized.
        CHECK is_ok         EQ true AND
              is_authorized EQ true.
      ENDIF.

*get the pobj instance.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*fill the read params for the read method of the pobj api class.
      ls_containers_read-level_id = 2.
      ls_containers_read-level_guid = scenario.
      ls_containers_read-logical_anchor = c_la_collision_cont_scenario.
      APPEND ls_containers_read TO lt_containers_read.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          container_params = lt_containers_read
        IMPORTING
          containers       = lt_containers.

      LOOP AT lt_containers INTO ls_containers.
        collision_container = ls_containers-container_content.
      ENDLOOP.

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
