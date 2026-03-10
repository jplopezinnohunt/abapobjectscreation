METHOD if_hrasr00_pobj_attachment~delete_attachment.

  DATA exception_obj TYPE REF TO cx_root.
  DATA step_attributes TYPE hrasr00step_attr.
  DATA scenario_attributes TYPE hrasr00scenario_attr.
  DATA process_attributes TYPE hrasr00process_attr.
  DATA attachment_type TYPE asr_attachment_type.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_pobj_attac_delete TYPE pobjs_attachment_delete_params.
  DATA lt_pobj_attac_delete TYPE pobjt_attachment_delete_params.
  DATA ls_attachments_out TYPE pobjs_attachment.
  DATA ls_attac_read TYPE pobjs_attachment_params.
  DATA lt_attac_read TYPE pobjt_attachment_params.
  DATA lt_attachments_out TYPE pobjt_attachments.


  is_ok = true.
  is_authorized = false.

*get the pobj_instance .
  CALL METHOD cl_pobj_process_object=>get
    EXPORTING
      pobj_guid     = me->a_pobj
      consumer_id   = c_consumer_id
    IMPORTING
      pobj_instance = lo_pobj_instance.

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

* get attachment type
*        SELECT SINGLE type FROM t5asrdocuments INTO attachment_type
*          WHERE guid = document_id.
*        CHECK sy-subrc EQ 0.

* map the importing parameter to the read parameters to be passed to the pobj api class.
        ls_attac_read-level_id = 3.
        ls_attac_read-level_guid = me->a_step.
        ls_attac_read-logical_anchor = c_la_atta_2_step.
        ls_attac_read-request_attachment_content = ' '.
        ls_attac_read-attachment_key-logical_guid = document_id.
        ls_attac_read-attachment_key-logical_version = 1.
        APPEND ls_attac_read TO lt_attac_read.

*call the read method of the pobj api layer by passing the mapped parameter.

        CALL METHOD lo_pobj_instance->read
          EXPORTING
            attachment_params = lt_attac_read
          IMPORTING
            attachments       = lt_attachments_out.

        READ TABLE lt_attachments_out INDEX '1' INTO ls_attachments_out .

        CHECK sy-subrc EQ 0.
*map the attachments that were returned back to the exporting parameter.
        MOVE ls_attachments_out-attachment_attributes-std_attributes-type TO attachment_type.


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



*map the importing paramter to the attachment level delete parameters to be passed to pobj api class
      ls_pobj_attac_delete-level_id = 3.
      ls_pobj_attac_delete-level_guid = me->a_step.
      ls_pobj_attac_delete-logical_anchor = c_la_atta_2_step.
      ls_pobj_attac_delete-attachment_key-logical_guid = document_id.
      ls_pobj_attac_delete-attachment_key-logical_version = 1.
      APPEND ls_pobj_attac_delete TO lt_pobj_attac_delete.

* call the delete method of the pobj api class and pass the mapped parameters.

      CALL METHOD lo_pobj_instance->delete
        EXPORTING
          attachment_delete_params = lt_pobj_attac_delete.

* Decrement the count for no. of attachments
* Get step attributes
      CALL METHOD me->get_step_attributes
        EXPORTING
          message_handler = message_handler
        IMPORTING
          step_attributes = step_attributes
          is_ok           = is_ok.

      CHECK is_ok = true.

    IF step_attributes-no_of_attachment IS NOT INITIAL.          "Note 2421028
      SUBTRACT 1 FROM step_attributes-no_of_attachment.
    ENDIF.                                                       "Note 2421028

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

    IF scenario_attributes-no_of_attachment IS NOT INITIAL.      "Note 2421028
      SUBTRACT 1 FROM scenario_attributes-no_of_attachment.
    ENDIF.                                                       "Note 2421028

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

    IF process_attributes-no_of_attachment IS NOT INITIAL.      "Note 2421028
      SUBTRACT 1 FROM process_attributes-no_of_attachment.
    ENDIF.                                                      "Note 2421028

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
