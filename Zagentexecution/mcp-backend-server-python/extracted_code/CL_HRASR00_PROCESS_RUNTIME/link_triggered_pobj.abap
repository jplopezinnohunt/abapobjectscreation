METHOD link_triggered_pobj.
  DATA lo_pobj_process_object TYPE REF TO if_pobj_process_object.
  DATA lt_linked_levels TYPE pobjt_linked_level_details.
  DATA lw_linked_levels TYPE pobjs_linked_level_details.
  DATA lt_add_attrib TYPE pobjt_level_attribute.
  DATA lw_add_attrib TYPE pobjs_level_attribute.
  DATA lt_attributes TYPE pobjt_levelkey_with_attributes.
  DATA lw_attributes TYPE pobjs_levelkey_with_attributes.
  DATA lw_addnl_attrib TYPE qisrdfieldvalue.

*Get the instance of the process object
  CALL METHOD cl_pobj_process_object=>if_pobj_process_object~get
    EXPORTING
      pobj_guid     = trigger_consumer_attributes-trigger_pobj_guid
      consumer_id   = trigger_consumer_attributes-trigger_consumer_id
    IMPORTING
      pobj_instance = lo_pobj_process_object.

*Arrange the importing parameter for update method.
*LINKED LEVELS
  lw_linked_levels-parent_level = 1.
  lw_linked_levels-parent_guid = trigger_consumer_attributes-trigger_pobj_guid.
  IF trigger_consumer_attributes-trigger_consumer_id = 'EIC' AND trigger_consumer_attributes-trigger_logical_anchor IS INITIAL.
    lw_linked_levels-logical_anchor = 'ACTIVITYPROCESSES'.
  ELSEIF trigger_consumer_attributes-trigger_consumer_id = 'CRM_SSC'.
    lw_linked_levels-logical_anchor = 'ACTIVITYPROCESS_CRM'.
  ELSE.
    lw_linked_levels-logical_anchor = trigger_consumer_attributes-trigger_logical_anchor.
  ENDIF.
  lw_linked_levels-child_level = 1.
  lw_linked_levels-child_guid = triggered_pobj.
  lw_linked_levels-operation = 'INS_LINK'.
  lw_linked_levels-parent_lvl_cons_id = trigger_consumer_attributes-trigger_consumer_id.
  lw_linked_levels-child_lvl_cons_id = triggered_consumer_id.
  lw_linked_levels-brother_type = 'SUCCEEDING'.

  APPEND lw_linked_levels TO lt_linked_levels.

*LEVEL ATTRIBUTES

*  LOOP AT trigger_consumer_attributes-trigger_addl_param INTO lw_addnl_attrib.
  lw_add_attrib-field_index = 1.
  lw_add_attrib-operation = 'INS'.
  lw_add_attrib-non_standard_flag = 'X'.
  lw_add_attrib-name = 'TRIGGER_ADDL_PARAM'.
  lw_add_attrib-value = trigger_consumer_attributes-trigger_addl_param.
  APPEND lw_add_attrib TO lt_add_attrib.
*  ENDLOOP.

  lw_attributes-level_id = 1.
  lw_attributes-level_guid = trigger_consumer_attributes-trigger_pobj_guid.
  MOVE lt_add_attrib TO lw_attributes-attributes.
  APPEND lw_attributes TO lt_attributes.

*Call POBJ update method

  CALL METHOD lo_pobj_process_object->update
    CHANGING
      linked_levels   = lt_linked_levels
      level_attribute = lt_attributes
*    ATTACHMENTS     =
*    CONTAINERS      =
*    BOR_OBJECTS     =
*    NOTES           =
*    OBJECTS         =
      .

**Flush to the database

  CALL METHOD lo_pobj_process_object->flush
    EXPORTING
      new_task = ' '.
*  COMMIT WORK.


ENDMETHOD.
