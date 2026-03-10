METHOD if_hrasr00_pobj_attachment~assign_attachment.

  DATA exception_obj TYPE REF TO cx_root.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_pobj_attac_attributes TYPE pobjs_attachment.
  DATA lt_pobj_attac_attributes TYPE pobjt_attachments.
  is_ok = true.
  TRY.
*get the pobj instance

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*map the importing attributes to the attributes of the pobj api layer.
      ls_pobj_attac_attributes-level_id = 3.
      ls_pobj_attac_attributes-level_guid = me->a_step.
      ls_pobj_attac_attributes-logical_anchor = c_la_atta_2_step.
      ls_pobj_attac_attributes-attachment_key-logical_guid = document_id.
      ls_pobj_attac_attributes-attachment_key-logical_version = 1.
      ls_pobj_attac_attributes-operation = 'INS_LINK'.
      APPEND ls_pobj_attac_attributes TO lt_pobj_attac_attributes.

*assign the attachment by calling the update method of the pobj api class and passing the mapped attributes.

      CALL METHOD lo_pobj_instance->update
        CHANGING
          attachments = lt_pobj_attac_attributes.

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
