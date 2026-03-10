METHOD if_hrasr00_pobj_attachment~read_attachment.


  DATA exception_obj TYPE REF TO cx_root.
  DATA: BEGIN OF attachment_keynattr.
  INCLUDE TYPE hrasr00doc_key AS key.
  INCLUDE TYPE hrasr00doc_attr AS attr.
  DATA END OF attachment_keynattr.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_attachments_out TYPE pobjs_attachment.
  DATA lt_attachments_out TYPE pobjt_attachments.
  DATA ls_attac_read TYPE pobjs_attachment_params.
  DATA lt_attac_read TYPE pobjt_attachment_params.
  CLEAR content_x.
  CLEAR attributes.
  is_ok =  true.
  is_authorized = false.
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
      ls_attac_read-level_guid = me->a_step.
      ls_attac_read-logical_anchor = c_la_atta_2_step.
      ls_attac_read-attachment_key-logical_guid = document_id.
      ls_attac_read-attachment_key-logical_version = 1.
      ls_attac_read-request_attachment_content = 'X'.
      APPEND ls_attac_read TO lt_attac_read.

*call the read method of the pobj api layer by passing the mapped parameter.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          attachment_params = lt_attac_read
        IMPORTING
          attachments       = lt_attachments_out.

      LOOP AT lt_attachments_out INTO ls_attachments_out.
        content_x = ls_attachments_out-attachment_content_x.
        MOVE-CORRESPONDING ls_attachments_out-attachment_attributes-std_attributes TO attributes.
        mimetype = ls_attachments_out-mimetype.
        filename = ls_attachments_out-filename.
        EXIT.
      ENDLOOP.


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
        IF is_ok EQ false.
          CLEAR: content_x, attributes, mimetype, filename.
          RETURN.
        ENDIF.

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
        IF is_ok EQ false OR is_authorized EQ false.
          CLEAR: content_x, attributes, mimetype, filename.
          RETURN.
        ENDIF.
      ENDIF.

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
