METHOD if_hrasr00_pobj_attachment~get_all_attachments_scenario.

  DATA scenario TYPE scmg_case_guid.
  DATA attachments_wa TYPE hrasr00doc_guid_and_attr.
  DATA documents_wa TYPE t5asrdocuments.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA steps TYPE hrasr00steps_tab.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA tabix TYPE sy-tabix.
  DATA is_authorized TYPE boole_d.
  DATA process TYPE asr_process.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA lt_steps TYPE hrasr00steps_tab.
  DATA ls_steps TYPE asr_guid.
  DATA ls_attac_read TYPE pobjs_attachment_params.
  DATA lt_attac_read TYPE pobjt_attachment_params.
  DATA lt_attachments_out TYPE pobjt_attachments.
  DATA ls_attachments_out TYPE pobjs_attachment.
  DATA ls_attachments TYPE hrasr00doc_guid_and_attr.
  DATA lw_attachments TYPE hrasr00doc_guid_and_attr.
  CLEAR attachments.

  is_ok = true.
  is_authorized = false.

* If scenario guid is passed, use that, else use the attribute of runtime class
  IF NOT scenario_guid IS INITIAL.
    scenario = scenario_guid.
  ELSE.
    scenario = a_scenario.
  ENDIF.
  TRY.
*get the pobj_instance .

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

      CALL METHOD me->get_all_steps
        EXPORTING
          message_handler = message_handler
          scenario_guid   = scenario
        IMPORTING
          steps           = lt_steps
          is_ok           = is_ok.
      CHECK is_ok EQ true.
      LOOP AT lt_steps INTO ls_steps.
        ls_attac_read-level_id = 3.
        ls_attac_read-level_guid = ls_steps.
        ls_attac_read-logical_anchor = c_la_atta_2_step.
        ls_attac_read-request_attachment_content = ' '.
        INSERT ls_attac_read INTO lt_attac_read INDEX 1.    "Note: 3209942
*        APPEND ls_attac_read TO lt_attac_read.
      ENDLOOP.
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
        READ TABLE attachments INTO lw_attachments WITH KEY guid = ls_attachments-guid.
        IF sy-subrc NE 0.
          APPEND ls_attachments TO attachments.
        ENDIF.
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
          CLEAR attachments.
          RETURN.
        ENDIF.

        LOOP AT attachments INTO attachments_wa.
          MOVE sy-tabix TO tabix.
* check authorization for attachment type
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
