METHOD if_hrasr00_pobj_factory~delete_process_object.

  DATA msg                  TYPE symsg.
  DATA dummy(1)             TYPE c.
  DATA exception_obj        TYPE REF TO cx_root.
  DATA auth_users           TYPE hrasr00authorizeduser_tab.
  DATA auth_user            TYPE hrasr00authorizeduser.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA lt_level_delete_params TYPE pobjt_level_delete_params.
  DATA lw_level_delete_params TYPE pobjs_level_key.
  DATA lt_scenarios TYPE hrasr00scenarios_tab.
  DATA lt_steps TYPE hrasr00steps_tab.
  DATA lt_attachments TYPE hrasr00doc_guid_and_attr_tab.
  DATA ls_attachment TYPE hrasr00doc_guid_and_attr.
  DATA lw_step  TYPE pobj_level_guid.
  DATA ls_scenario  TYPE pobj_level_guid.
  DATA lt_datacontainers TYPE hrasr00data_container_tab.
  DATA ls_datacontainer  TYPE hrasr00data_container.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA process TYPE asr_process.

  is_ok = true.
  is_authorized = false.

* do authorization check on process
* get attributes of process
  TRY.
      IF no_auth_check IS INITIAL.
        auth_user-uname = sy-uname.
        auth_user-is_authorized = false.
        APPEND auth_user TO auth_users.
        CLEAR auth_user.
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
*          is_ok = false.
          RETURN.
        ENDIF.

*************** Authorization checks on Datacontainers

        CALL METHOD me->get_all_data_containers
          EXPORTING
            message_handler = message_handler
            activity        = activity
            no_auth_check   = true
          IMPORTING
            data_containers = lt_datacontainers
            is_ok           = is_ok.

        CHECK is_ok EQ true.


        LOOP AT lt_datacontainers INTO ls_datacontainer.
          CALL METHOD me->check_container_auth
            EXPORTING
              message_handler = message_handler
              activity        = activity
              data_container  = ls_datacontainer-data_container
              scenario_guid   = ls_datacontainer-scenario_guid
            IMPORTING
              is_ok           = is_ok
              is_authorized   = is_authorized.
          CLEAR ls_datacontainer.
* IF Authorization check failed on the datacontainer, return without continueing to delete the process object.
          IF is_authorized EQ false OR is_ok EQ false.
            RETURN.
          ENDIF.
        ENDLOOP.

*************** Authorization checks on all Attachments

        CALL METHOD me->get_all_attachments_process
          EXPORTING
            message_handler = message_handler
            activity        = activity
            no_auth_check   = true
          IMPORTING
            attachments     = lt_attachments
            is_ok           = is_ok.
        CHECK is_ok EQ true.
        LOOP AT lt_attachments INTO ls_attachment.
* get application and object key
          CALL METHOD me->get_object
            EXPORTING
              message_handler = message_handler
            IMPORTING
              application     = application
              object_key      = object_key
              process         = process
              is_ok           = is_ok.
          CHECK is_ok EQ true.
* check authorization for attachment type
          CALL METHOD me->check_attachment_auth
            EXPORTING
              application     = application
              object_key      = object_key
              process         = process
              attachment_type = ls_attachment-attachment_attr-type
              message_handler = message_handler
              activity        = activity
            IMPORTING
              is_ok           = is_ok
              is_authorized   = is_authorized.
          CLEAR ls_attachment.
* IF Authorization check failed on the attachment, return without continueing to delete the process object.
          IF is_authorized EQ false OR is_ok EQ false.
            RETURN.
          ENDIF.
        ENDLOOP.
      ENDIF.

*If authorization checks are successfull, then continue to delete the POBJ

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      CLEAR lw_level_delete_params.

      MOVE '1' TO lw_level_delete_params-level_id .
      MOVE me->a_pobj TO lw_level_delete_params-level_guid.
      APPEND lw_level_delete_params TO lt_level_delete_params."#EC

      CALL METHOD pobj_instance_process_obj->delete
        EXPORTING
          level_delete_params = lt_level_delete_params.


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

* Delete from the instance directory
  DELETE TABLE a_instance_dir WITH TABLE KEY guid = me->a_pobj.

ENDMETHOD.
