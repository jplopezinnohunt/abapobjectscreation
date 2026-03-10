METHOD if_hrasr00_pobj_container~delete_all_coll_containers.

  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA auth_users TYPE hrasr00authorizeduser_tab.
  DATA auth_users_wa TYPE hrasr00authorizeduser.
  DATA ls_scenarios TYPE asr_guid.
  DATA lt_scenarios TYPE hrasr00scenarios_tab.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_cont_read TYPE pobjs_container_params.
  DATA lt_cont_read TYPE pobjt_container_params.
  DATA lt_containers TYPE pobjt_containers.
  DATA ls_containers TYPE pobjs_container.
  DATA ls_containers_delete TYPE pobjs_container_delete_params.
  DATA lt_containers_delete TYPE pobjt_container_delete_params.

  is_ok = true.
  is_authorized = false.

  TRY.
* do authorization check on process
      IF no_auth_check IS INITIAL.
        auth_users_wa-uname = sy-uname.
        auth_users_wa-is_authorized = false.
        APPEND auth_users_wa TO auth_users.
        CLEAR auth_users_wa.
        CALL METHOD check_process_auth_user
          EXPORTING
            activity        = activity
            process_guid    = a_pobj
            message_handler = message_handler
          IMPORTING
            is_ok           = is_ok
          CHANGING
            authorizedusers = auth_users.
        CHECK is_ok = true.

        READ TABLE auth_users WITH KEY uname = sy-uname
                                       is_authorized = true
        TRANSPORTING NO FIELDS.
        IF sy-subrc EQ 0.
          is_authorized = true.
        ELSE.
          is_authorized = false.
          is_ok = false.
          EXIT.
        ENDIF.
      ENDIF.

*get the pobj instance
          CALL METHOD cl_pobj_process_object=>get
            EXPORTING
              pobj_guid     = me->a_pobj
              consumer_id   = c_consumer_id
            IMPORTING
              pobj_instance = lo_pobj_instance.

      CALL METHOD me->get_all_scenarios
              EXPORTING
                message_handler = message_handler
              IMPORTING
                scenarios       = lt_scenarios
                IS_OK           = is_ok.
      LOOP AT lt_scenarios INTO ls_scenarios.
        clear: lt_containers,lt_containers_delete.
        ls_cont_read-level_id = 2.
        ls_cont_read-level_guid = ls_scenarios.
        ls_cont_read-logical_anchor = c_la_collision_cont_scenario.
        APPEND ls_cont_read TO lt_cont_read.

*call the read method of the pobj api layer by passing the mapped parameter.

            CALL METHOD lo_pobj_instance->read
              EXPORTING
                container_params = lt_cont_read
              IMPORTING
                containers       = lt_containers.


        LOOP AT lt_containers INTO ls_containers.
          MOVE-CORRESPONDING ls_containers TO ls_containers_delete.
          APPEND ls_containers_delete TO lt_containers_delete.
          clear: ls_containers,ls_containers_delete.
        ENDLOOP.
        CALL METHOD lo_pobj_instance->delete
            EXPORTING
              container_delete_params = lt_containers_delete.
      ENDLOOP.
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
