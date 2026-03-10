METHOD if_hrasr00_pobj_attachment~delete_all_attachments.

  DATA attachments_wa TYPE hrasr00doc_guid_and_attr.
  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_scenarios TYPE asr_guid.
  DATA lt_scenarios TYPE hrasr00scenarios_tab.
  DATA lt_steps TYPE hrasr00steps_tab.
  DATA ls_steps TYPE asr_guid.
  DATA ls_attac_read TYPE pobjs_attachment_params.
  DATA lt_attac_read TYPE pobjt_attachment_params.
  DATA ls_attachments TYPE hrasr00doc_guid_and_attr.
  DATA lt_attachments_out TYPE pobjt_attachments.
  DATA ls_attachments_out TYPE pobjs_attachment.
  data attachment_type type asr_attachment_type.
  data is_authorized type boole_d.

  is_ok = true.
  is_authorized = false.
  TRY.
**get the pobj instance
      TRY.
          CALL METHOD cl_pobj_process_object=>get
            EXPORTING
              pobj_guid     = me->a_pobj
              consumer_id   = c_consumer_id
            IMPORTING
              pobj_instance = lo_pobj_instance.
        CATCH cx_pobj_process_object .
      ENDTRY.

      CALL METHOD me->get_all_scenarios
        EXPORTING
          message_handler = message_handler
        IMPORTING
          scenarios       = lt_scenarios
          is_ok           = is_ok.
      CHECK is_ok EQ true.
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
      ENDIF.

      LOOP AT lt_scenarios INTO ls_scenarios.

        CALL METHOD me->get_all_steps
          EXPORTING
            message_handler = message_handler
            scenario_guid   = ls_scenarios
          IMPORTING
            steps           = lt_steps
            is_ok           = is_ok.
        IF is_ok EQ false.
          RETURN.
        ENDIF.

        LOOP AT lt_steps INTO ls_steps.
          ls_attac_read-level_id = 3.
          ls_attac_read-level_guid = ls_steps.
          ls_attac_read-logical_anchor = c_la_atta_2_step.
          ls_attac_read-request_attachment_content = ' '.
          APPEND ls_attac_read TO lt_attac_read.

*call the read method of the pobj api layer by passing the mapped parameter.
          TRY.
              CALL METHOD lo_pobj_instance->read
                EXPORTING
                  attachment_params = lt_attac_read
                IMPORTING
                  attachments       = lt_attachments_out.
            CATCH cx_pobj_process_object .
          ENDTRY.

          LOOP AT lt_attachments_out INTO ls_attachments_out.
            MOVE ls_attachments_out-attachment_attributes-std_attributes-type TO attachment_type.

* check attachment authorization
            IF no_auth_check EQ false.
* check authorization for attachment type
              CALL METHOD me->check_attachment_auth
                EXPORTING
                  application     = application
                  object_key      = object_key
                  process         = process
                  attachment_type = attachment_type
                  message_handler = message_handler
                  activity        = activity
                IMPORTING
                  is_ok           = is_ok
                  is_authorized   = is_authorized.
              CHECK is_ok         EQ true AND
                    is_authorized EQ true.
            ENDIF.


            CALL METHOD me->delete_attachment
              EXPORTING
                document_id     = ls_attachments_out-attachment_key-logical_guid
                message_handler = message_handler
*            NO_AUTH_CHECK   = 'X'
*            ACTIVITY        =
              IMPORTING
                is_ok           = is_ok
                is_authorized   = is_authorized.
            CHECK is_ok         EQ true AND
                  is_authorized EQ true.
          ENDLOOP.
        ENDLOOP.
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
