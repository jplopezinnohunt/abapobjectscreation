METHOD if_hrasr00_pobj_factory~create_process_object.

*  DATA instance_process_obj TYPE REF TO if_hrasr00_process.
*  DATA hrasr00_case_api     TYPE REF TO if_hrasr00_case.
  DATA no_authority TYPE boole_d.
  DATA auth_users TYPE hrasr00authorizeduser_tab.
  DATA auth_user TYPE hrasr00authorizeduser.
  DATA exception_obj TYPE REF TO cx_root.
  DATA application_log TYPE REF TO cl_hrasr00_application_log.
  DATA description TYPE balnrext.
  DATA msg_list TYPE REF TO cl_hrbas_message_list.
  DATA messages TYPE hrbas_message_tab.
  DATA message TYPE hrbas_message.
  DATA msg_exists_already TYPE boole_d.
  DATA msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA process_attributes_pobj TYPE pobjt_level_attribute.
  DATA level_attribute TYPE pobjt_levelkey_with_attributes.
  DATA level_attribute_wa TYPE pobjs_levelkey_with_attributes.

  is_ok = true.
  is_authorized = false.
  CLEAR: pobj_guid, scenario_guid, step_guid, instance_pobj_runtime.

* do authorization check on process
  TRY.
      IF no_auth_check IS INITIAL.
        auth_user-uname = sy-uname.
        auth_user-is_authorized = false.
        APPEND auth_user TO auth_users.
        CLEAR auth_user.
        CALL METHOD check_process_auth_user
          EXPORTING
            activity        = activity
            application     = process_attributes-application
            object_key      = process_attributes-object_key
            process_name    = process_attributes-process
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
*          is_ok = false.
          RETURN.
        ENDIF.
      ENDIF.
      "Changes for Save Draft Stay on Screen concept
      IF proc_guid IS NOT INITIAL.
        pobj_guid = proc_guid.
      ENDIF.

      CALL METHOD cl_pobj_process_object=>create
        EXPORTING
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = pobj_instance_process_obj
        CHANGING
          pobj_guid     = pobj_guid.

      CALL METHOD cl_hrasr00_process_runtime=>convert_struc_2_indexnameval
        EXPORTING
          attr_structure = process_attributes
          operation      = 'INS'
        IMPORTING
          attributes     = process_attributes_pobj.

      CLEAR level_attribute_wa.
      level_attribute_wa-level_id = '1'.
      level_attribute_wa-level_guid = pobj_guid.
      level_attribute_wa-attributes = process_attributes_pobj.
      APPEND level_attribute_wa TO level_attribute.

      CALL METHOD pobj_instance_process_obj->update
        CHANGING
          level_attribute = level_attribute.

* Get the instance of the process object runtime
      CALL METHOD get_instance
        EXPORTING
          pobj_guid             = pobj_guid
          message_handler       = message_handler
        IMPORTING
          instance_pobj_runtime = instance_pobj_runtime
          is_ok                 = is_ok.

      CHECK is_ok = true.

* Create scenario object
      CALL METHOD instance_pobj_runtime->create_scenario_object
        EXPORTING
          scenario_attributes = scenario_attributes
          message_handler     = message_handler
        IMPORTING
          scenario_guid       = scenario_guid
          is_ok               = is_ok.

      CHECK is_ok = true.

* Create step object
      CALL METHOD instance_pobj_runtime->create_step_object
        EXPORTING
          step_attributes = step_attributes
          message_handler = message_handler
        IMPORTING
          step_guid       = step_guid
          is_ok           = is_ok.

      CHECK is_ok = true.

    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist already
      msg_list ?= message_handler.

      CALL METHOD msg_list->get_message_list
        IMPORTING
          messages = messages.
      LOOP AT messages INTO message.
        IF message-msgty = 'E' AND
           message-msgid = 'HRASR00_POBJ' AND
           message-msgno = '022'.
          msg_exists_already = true.
          EXIT.
        ENDIF.
      ENDLOOP.
      IF msg_exists_already = false.
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '022' INTO dummy.
        MOVE-CORRESPONDING sy TO msg.
        CALL METHOD message_handler->add_message
          EXPORTING
            message = msg.
      ENDIF.

*     Write the exception to application log
      IF NOT process_attributes-reference_number IS INITIAL.
        CONCATENATE 'Prozessreferenznummer'(001) '-' process_attributes-reference_number INTO description.
      ELSE.
        CONCATENATE 'Prozess'(002) '-' process_attributes-process ';' 'Objektschlüssel'(003)  '-' process_attributes-object_key INTO description.
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
