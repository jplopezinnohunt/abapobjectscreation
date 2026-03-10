METHOD if_hrasr00_pobj_factory~get_all_scenarios.

* DATA exception_obj TYPE REF TO cx_root.
  DATA scenario_guid TYPE asr_guid.
  DATA ls_link_process_read TYPE pobjs_linked_level_params.
  DATA lt_link_process_read TYPE pobjt_linked_level_params.
  DATA lt_scenarios TYPE pobjt_linked_level_details.
  DATA ls_scenarios TYPE pobjs_linked_level_details.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA exception_obj TYPE REF TO cx_root.
  CLEAR ls_link_process_read.
  CLEAR lt_link_process_read.
  CLEAR ls_scenarios.
  CLEAR lt_scenarios.
* Initialize
  is_ok = true.
  CLEAR scenarios.
  REFRESH scenarios.

  TRY.

*get the pobj instance
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*fill the linked levels paramters of the pobj api layer to get all the steps attached to it.
      ls_link_process_read-parent_level = 1.
      ls_link_process_read-parent_guid = a_pobj.
      ls_link_process_read-logical_anchor = c_la_scen_2_proc.
      APPEND ls_link_process_read TO lt_link_process_read.

*call the read method of the pobj api layer by passing the mapped parameter.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          linked_level_params = lt_link_process_read
        IMPORTING
          linked_levels       = lt_scenarios.

      LOOP AT lt_scenarios INTO ls_scenarios.
        INSERT ls_scenarios-child_guid INTO TABLE scenarios.
      ENDLOOP.

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
