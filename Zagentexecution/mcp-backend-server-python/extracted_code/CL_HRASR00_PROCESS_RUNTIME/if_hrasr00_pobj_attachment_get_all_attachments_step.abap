METHOD if_hrasr00_pobj_attachment~get_all_attachments_step.


  DATA step TYPE scmg_case_guid.
  DATA exception_obj TYPE REF TO cx_root.
  DATA attachments_wa TYPE hrasr00doc_guid_and_attr.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA tabix TYPE sy-tabix.
  DATA is_authorized TYPE boole_d.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_attachments TYPE hrasr00doc_guid_and_attr.
  DATA lt_attachments_out TYPE pobjt_attachments.
  DATA ls_attachments_out TYPE pobjs_attachment.
  DATA ls_attac_read TYPE pobjs_attachment_params.
  DATA lt_attac_read TYPE pobjt_attachment_params.
  CLEAR attachments.

  is_ok =  true.
  is_authorized = false.

* If step guid is passed, use that, else use the attribute of runtime class
  IF NOT step_guid IS INITIAL.
    step = step_guid.
  ELSE.
    step = a_step.
  ENDIF.
  TRY.
*get the pobj instance
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

* map the importing parameter to the read parameters to be passed to the pobj api class.
      ls_attac_read-level_id = 3.
      ls_attac_read-level_guid = step.
      ls_attac_read-logical_anchor = c_la_atta_2_step.
      ls_attac_read-request_attachment_content = ' '.
      APPEND ls_attac_read TO lt_attac_read.

*call the read method of the pobj api layer by passing the mapped parameter.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          attachment_params = lt_attac_read
        IMPORTING
          attachments       = lt_attachments_out.

      LOOP AT lt_attachments_out INTO ls_attachments_out.
*map the attachments that were returned back to the exporting parameter.
        MOVE-CORRESPONDING ls_attachments_out-attachment_attributes-std_attributes TO ls_attachments-attachment_attr.
        ls_attachments-guid = ls_attachments_out-attachment_key-logical_guid.
        APPEND ls_attachments TO attachments.
      ENDLOOP.
      IF no_auth_check EQ false.
*       get application and object key
        CALL METHOD me->get_object
          EXPORTING
            message_handler = message_handler
          IMPORTING
            application     = application
            object_key      = object_key
            process         = process
            is_ok           = is_ok.
        IF is_ok EQ false.
          CLEAR attachments.
          RETURN.
        ENDIF.

        LOOP AT attachments INTO attachments_wa.
          MOVE sy-tabix TO tabix.
*         check authorization for attachment type
          CALL METHOD me->check_attachment_auth
            EXPORTING
              application     = application
              object_key      = object_key
              process         = process
              attachment_type = attachments_wa-attachment_attr-type
              message_handler = message_handler
              activity        = activity
            IMPORTING
              is_authorized   = is_authorized
              is_ok           = is_ok.
          IF is_authorized EQ false OR is_ok EQ false.
            DELETE attachments INDEX tabix.
          ENDIF.
        ENDLOOP.
      ENDIF.
*
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
