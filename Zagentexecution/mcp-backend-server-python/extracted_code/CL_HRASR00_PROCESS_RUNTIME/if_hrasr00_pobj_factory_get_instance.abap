METHOD if_hrasr00_pobj_factory~get_instance.

  CONSTANTS class_name TYPE seoclsname VALUE 'CL_HRASR00_PROCESS_RUNTIME'.

  DATA instance_dir_line        TYPE instance_directory_line.
  DATA instance_pobj_runtime_cl TYPE REF TO cl_hrasr00_process_runtime.
  DATA auth_users               TYPE hrasr00authorizeduser_tab.
  DATA auth_user                TYPE hrasr00authorizeduser.
  DATA exception_obj            TYPE REF TO cx_root.
  DATA application_log          TYPE REF TO cl_hrasr00_application_log.
  DATA description              TYPE balnrext.
  DATA msg_list                 TYPE REF TO cl_hrbas_message_list.
  DATA messages                 TYPE hrbas_message_tab.
  DATA message                  TYPE hrbas_message.
  DATA msg_exists_already       TYPE boole_d.
  DATA msg                      TYPE symsg.
  DATA dummy(1)                 TYPE c.
  DATA is_consistent            TYPE boole_d.
  DATA process_attributes TYPE hrasr00process_attr.
  DATA reference_number TYPE asr_reference_number.

  CLEAR instance_pobj_runtime.
  CLEAR pobj_guid_out.
  CLEAR scenario_guid_out.
  is_ok = true.
  is_authorized = false.

* It is not possible to get the runitme instance if all the 3 keys are empty.
* Caller has to provide at least one of the case guids
*  ASSERT step_guid     IS NOT INITIAL OR
*         scenario_guid IS NOT INITIAL OR
*         pobj_guid     IS NOT INITIAL.
  IF step_guid     IS INITIAL AND
     scenario_guid IS INITIAL AND
     pobj_guid     IS INITIAL.
    MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '026' INTO dummy.
    MOVE-CORRESPONDING sy TO msg.
    CALL METHOD message_handler->add_message
      EXPORTING
        message = msg.
    is_ok = false.
    RETURN.
  ENDIF.

*  CHECK step_guid     IS NOT INITIAL OR
*        scenario_guid IS NOT INITIAL OR
*        pobj_guid     IS NOT INITIAL.
*
  TRY.
      IF NOT step_guid IS INITIAL.
* Get the scenario guid
        CALL METHOD get_scenario_by_step
          EXPORTING
            step_guid       = step_guid
            message_handler = message_handler
          IMPORTING
            scenario_guid   = scenario_guid_out
            is_ok           = is_ok.

        CHECK is_ok = true.

* Get the POBJ guid
        CALL METHOD get_pobj_by_scenario
          EXPORTING
            scenario_guid   = scenario_guid_out
            message_handler = message_handler
          IMPORTING
            pobj_guid       = pobj_guid_out
            is_ok           = is_ok.

        CHECK is_ok = true.

      ELSEIF NOT scenario_guid IS INITIAL.
* Get the POBJ guid
        CALL METHOD get_pobj_by_scenario
          EXPORTING
            scenario_guid   = scenario_guid
            message_handler = message_handler
          IMPORTING
            pobj_guid       = pobj_guid_out
            is_ok           = is_ok.

        CHECK is_ok = true.
        scenario_guid_out = scenario_guid.

      ELSEIF NOT pobj_guid IS INITIAL.
* Check consistency of the supplied POBJ guid
        CALL METHOD cl_hrasr00_process_runtime=>check_consistency_pobj_guid
          EXPORTING
            pobj_guid       = pobj_guid
            message_handler = message_handler
          IMPORTING
            is_ok           = is_ok
            is_consistent   = is_consistent.

        CHECK is_ok = true AND is_consistent = true.
        pobj_guid_out = pobj_guid.
      ENDIF.

      READ TABLE a_instance_dir WITH KEY guid = pobj_guid_out INTO instance_dir_line.

* If instance available in directory, return that.
      IF sy-subrc = 0.
        instance_pobj_runtime = instance_dir_line-instance.

* If instance not available, create one and store the same in directory
      ELSE.
        CREATE OBJECT instance_pobj_runtime TYPE (class_name)
        EXPORTING
          pobj_guid = pobj_guid_out.

        instance_dir_line-guid     = pobj_guid_out.
        instance_dir_line-instance = instance_pobj_runtime.

        INSERT instance_dir_line INTO TABLE a_instance_dir.
      ENDIF.

* Cast the interface instance of process runtime to class instance of process runtime
      instance_pobj_runtime_cl ?= instance_pobj_runtime.

* Set the context in process runtime instance
      CALL METHOD instance_pobj_runtime_cl->set_context
        EXPORTING
          scenario_guid = scenario_guid_out
          step_guid     = step_guid.

* do authorization check on process
* get attributes of process
      CHECK no_auth_check IS INITIAL AND
            pobj_guid_out IS NOT INITIAL.
      auth_user-uname         = sy-uname.
      auth_user-is_authorized = false.
      APPEND auth_user TO auth_users.
      CLEAR auth_user.
      CALL METHOD check_process_auth_user
        EXPORTING
          activity        = activity
          process_guid    = pobj_guid_out
          message_handler = message_handler
        IMPORTING
          is_ok           = is_ok
        CHANGING
          authorizedusers = auth_users.

      READ TABLE auth_users WITH KEY uname         = sy-uname
                                     is_authorized = true
      TRANSPORTING NO FIELDS.
      IF sy-subrc EQ 0.
        is_authorized = true.
      ELSE.
        is_authorized = false.
        is_ok = false.
        CLEAR instance_pobj_runtime.
        CLEAR pobj_guid_out.
        CLEAR scenario_guid_out.
      ENDIF.

    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist already
      msg_list ?= message_handler.

      CALL METHOD msg_list->get_message_list
        IMPORTING
          messages = messages.
      LOOP AT messages INTO message.
        IF message-msgty = 'E' AND
           message-msgid = 'HRASR00_POBJ' AND
           message-msgno = '021'.
          msg_exists_already = true.
          EXIT.
        ENDIF.
      ENDLOOP.
      IF msg_exists_already = false.
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '021' INTO dummy.
        MOVE-CORRESPONDING sy TO msg.
        CALL METHOD message_handler->add_message
          EXPORTING
            message = msg.
      ENDIF.

*     Write the exception to application log

      IF instance_pobj_runtime IS BOUND.
        CALL METHOD instance_pobj_runtime->get_process_attributes
          EXPORTING
            message_handler    = message_handler
          IMPORTING
            process_attributes = process_attributes.

        reference_number = process_attributes-reference_number.

        IF NOT reference_number IS INITIAL.
          CONCATENATE 'Prozessreferenznummer'(001) '-' reference_number INTO description.
        ELSE.
          CONCATENATE 'Prozess'(002) '-' process_attributes-process ';' 'Objektschlüssel'(003)  '-' process_attributes-object_key INTO description.
        ENDIF.
      ENDIF.

      application_log = cl_hrasr00_application_log=>get_instance( description = description
                                                                  object      = c_application_log_object
                                                                  subobject   = c_application_log_subobject ).
      CALL METHOD application_log->add_exception
        EXPORTING
          exception = exception_obj.

      IF msg_list IS BOUND.
        CALL METHOD application_log->add_messages
          EXPORTING
            message_list = msg_list.
      ENDIF.

* Do a rollback/commit if the flag 'no_commit' is not set by the caller of POBJ runtime
      IF no_commit = false.
* Discard any changes made in the backend and / or process object
* With the New POBJ Framework, rollback is redundant
*        ROLLBACK WORK.
        CALL METHOD application_log->persist_log.
* Commit work so that the application log entries are persisted to DB
        COMMIT WORK.
      ELSE.
        CALL METHOD application_log->persist_log.
      ENDIF.

      is_ok = false.
      RETURN.
  ENDTRY.
ENDMETHOD.
