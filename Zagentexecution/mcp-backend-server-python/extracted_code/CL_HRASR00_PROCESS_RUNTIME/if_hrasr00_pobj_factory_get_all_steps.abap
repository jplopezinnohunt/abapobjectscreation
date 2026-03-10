METHOD if_hrasr00_pobj_factory~get_all_steps.

* DATA exception_obj TYPE REF TO cx_root.
  DATA scenario TYPE scmg_case_guid.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_link_process_read TYPE pobjs_linked_level_params.
  DATA lt_link_process_read TYPE pobjt_linked_level_params.
  DATA lt_steps TYPE pobjt_linked_level_details.
  DATA ls_steps TYPE pobjs_linked_level_details.
  DATA exception_obj TYPE REF TO cx_root.
  CLEAR ls_link_process_read.
  CLEAR lt_link_process_read.
  CLEAR ls_steps.
  CLEAR lt_steps.
  CLEAR steps.
  REFRESH steps.
  IF NOT scenario_guid IS INITIAL.
    scenario = scenario_guid.
  ELSE.
    scenario = a_scenario.
  ENDIF.
  TRY.

*get the pobj instance.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*fill the linked levels paramters of the pobj api layer to get all the steps attached to it.
      ls_link_process_read-parent_level = 2.
      ls_link_process_read-parent_guid = scenario.
      ls_link_process_read-logical_anchor = c_la_step_2_scen.
      APPEND ls_link_process_read TO lt_link_process_read.

*call the read method of the pobj api layer by passing the mapped parameter.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          linked_level_params = lt_link_process_read
        IMPORTING
          linked_levels       = lt_steps.

      LOOP AT lt_steps INTO ls_steps.
        INSERT ls_steps-child_guid INTO TABLE steps.
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
