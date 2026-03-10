METHOD if_hrasr00_pobj_header_info~change_process_attributes.

  DATA exception_obj TYPE REF TO cx_root.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  DATA lt_attributes TYPE pobjt_level_attribute.
  DATA ls_level_attr TYPE pobjs_levelkey_with_attributes.
  DATA lt_level_attr TYPE pobjt_levelkey_with_attributes.


  CLEAR ls_level_attr.
  CLEAR lt_level_attr.
  CLEAR lt_attributes.
  is_ok = true.

* Get the POBJ instance using POBJ GUID
  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      CALL METHOD cl_hrasr00_process_runtime=>convert_struc_2_indexnameval
        EXPORTING
          attr_structure = process_attributes
          operation      = 'UPD'
        IMPORTING
          attributes     = lt_attributes.

      ls_level_attr-level_id = 1.
      ls_level_attr-level_guid = me->a_pobj.
      APPEND LINES OF lt_attributes TO ls_level_attr-attributes.
      APPEND ls_level_attr TO lt_level_attr.


      CALL METHOD pobj_instance_process_obj->update
        CHANGING
          level_attribute = lt_level_attr.


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
