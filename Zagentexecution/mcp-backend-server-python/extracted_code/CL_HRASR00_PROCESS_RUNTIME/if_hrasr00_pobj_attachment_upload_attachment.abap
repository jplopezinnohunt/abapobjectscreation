METHOD if_hrasr00_pobj_attachment~upload_attachment.

  DATA exception_obj TYPE REF TO cx_root.
  DATA step_attributes TYPE hrasr00step_attr.
  DATA scenario_attributes TYPE hrasr00scenario_attr.
  DATA process_attributes TYPE hrasr00process_attr.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_pobj_attac_attributes TYPE pobjs_attachment.
  DATA lt_pobj_attac_attributes TYPE pobjt_attachments.
  CLEAR document_id.

  is_ok = true.
  is_authorized = false.

  TRY.
      IF no_auth_check EQ false.
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
            attachment_type = attributes-type
            message_handler = message_handler
            activity        = activity
          IMPORTING
            is_ok           = is_ok
            is_authorized   = is_authorized.
        CHECK is_ok         EQ true AND
              is_authorized EQ true.
      ENDIF.

*get the pobj_instance .

          CALL METHOD cl_pobj_process_object=>get
            EXPORTING
              pobj_guid     = me->a_pobj
              consumer_id   = c_consumer_id
            IMPORTING
              pobj_instance = lo_pobj_instance.
*map the importing attributes to the attributes of the pobj api layer.
      MOVE-CORRESPONDING attributes TO ls_pobj_attac_attributes-attachment_attributes-std_attributes.
      ls_pobj_attac_attributes-level_id = 3.
      ls_pobj_attac_attributes-level_guid = me->a_step.
      ls_pobj_attac_attributes-logical_anchor = c_la_atta_2_step.
      ls_pobj_attac_attributes-attachment_content_x = content_x.
      ls_pobj_attac_attributes-filename = filename.
      ls_pobj_attac_attributes-operation = 'INS_OBJ'.
      APPEND ls_pobj_attac_attributes TO lt_pobj_attac_attributes.

*create the attachment bu calling the update method of the pobj api class and passing the mapped attributes.

          CALL METHOD lo_pobj_instance->update
            CHANGING
              attachments = lt_pobj_attac_attributes.


* Increment the count for no. of attachments
* Get step attributes
      CALL METHOD me->get_step_attributes
        EXPORTING
          message_handler = message_handler
        IMPORTING
          step_attributes = step_attributes
          is_ok           = is_ok.

      CHECK is_ok = true.

      ADD 1 TO step_attributes-no_of_attachment.

* Update the latest step attributes.
      CALL METHOD me->change_step_attributes
        EXPORTING
          step_attributes = step_attributes
          message_handler = message_handler
        IMPORTING
          is_ok           = is_ok.

      CHECK is_ok = true.

* Get scenario attributes
      CALL METHOD me->get_scenario_attributes
        EXPORTING
          message_handler     = message_handler
        IMPORTING
          scenario_attributes = scenario_attributes
          is_ok               = is_ok.

      CHECK is_ok = true.

      ADD 1 TO scenario_attributes-no_of_attachment.

* Update the latest scenario attributes.
      CALL METHOD me->change_scenario_attributes
        EXPORTING
          scenario_attributes = scenario_attributes
          message_handler     = message_handler
        IMPORTING
          is_ok               = is_ok.

      CHECK is_ok = true.

* Get process attributes
      CALL METHOD me->get_process_attributes
        EXPORTING
          message_handler    = message_handler
        IMPORTING
          process_attributes = process_attributes
          is_ok              = is_ok.

      CHECK is_ok = true.

      ADD 1 TO process_attributes-no_of_attachment.

* Update the latest step attributes.
      CALL METHOD me->change_process_attributes
        EXPORTING
          process_attributes = process_attributes
          message_handler    = message_handler
        IMPORTING
          is_ok              = is_ok.

      CHECK is_ok = true.

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
