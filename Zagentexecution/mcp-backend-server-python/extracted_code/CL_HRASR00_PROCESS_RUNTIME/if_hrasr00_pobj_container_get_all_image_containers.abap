METHOD if_hrasr00_pobj_container~get_all_image_containers.

  DATA exception_obj         TYPE REF TO cx_root.
  DATA image_container_key   TYPE hrasr00doc_key.
  DATA image_container_keys  TYPE TABLE OF hrasr00doc_key.
  DATA image_container       TYPE hrasr00image_container.
  DATA attributes_nameval    TYPE ty_namevalueasstring.
  DATA attribute_nameval     TYPE namevalueasstring.
  DATA scenario_guid         TYPE asr_guid.
  DATA scenario_guids        LIKE TABLE OF scenario_guid.
  DATA ls_containers_read TYPE pobjs_container_params.
  DATA lt_containers_read TYPE pobjt_container_params.
  DATA lt_image_containers      TYPE pobjt_containers.
  DATA ls_image_containers      TYPE pobjs_container.
  DATA image_container_wa TYPE hrasr00image_container.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.

  DATA cont_attribute_wa TYPE pobjs_ind_nam_val_ops.
  CLEAR image_container_tab.
  is_ok = true.
  is_authorized = false.

  TRY.
* if authorization check needs be done-
* get all scenarios and get data container for each scenario
* check auth against each data container
      IF no_auth_check = false.
        CALL METHOD me->get_all_scenarios
          EXPORTING
            message_handler = message_handler
          IMPORTING
            scenarios       = scenario_guids
            is_ok           = is_ok.
        CHECK is_ok EQ true.

        LOOP AT scenario_guids INTO scenario_guid.
          CALL METHOD me->get_latest_data_container
            EXPORTING
              scenario_guid   = scenario_guid
              message_handler = message_handler
              no_auth_check   = no_auth_check
              activity        = activity
            IMPORTING
              is_ok           = is_ok
              is_authorized   = is_authorized.
          IF is_ok         EQ false OR
             is_authorized EQ false.
            RETURN.
          ENDIF.
        ENDLOOP.
      ENDIF.

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = lo_pobj_instance.

      ls_containers_read-level_id = 1.
      ls_containers_read-level_guid = me->a_pobj.
      ls_containers_read-logical_anchor = c_la_image_cont_process.
      APPEND ls_containers_read TO lt_containers_read.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          container_params = lt_containers_read
        IMPORTING
          containers       = lt_image_containers.

      LOOP AT lt_image_containers INTO ls_image_containers.
        image_container_wa-image_container = ls_image_containers-container_content.
        LOOP AT ls_image_containers-container_attributes INTO cont_attribute_wa WHERE name = 'ASR_STEP_CASE_GUID'.
          MOVE cont_attribute_wa-value TO image_container_wa-step_case_guid.
        ENDLOOP.
        APPEND image_container_wa TO image_container_tab.
        CLEAR ls_image_containers.
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
