METHOD unlock.

  DATA no_authority TYPE boole_d.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_unlock_pobj TYPE pobjs_unlock_objects.
  DATA lt_unlock_pobj TYPE pobjt_unlock_objects.
  CLEAR ls_unlock_pobj.
  CLEAR lt_unlock_pobj.
  is_ok = true.

  IF me->a_pobj IS NOT INITIAL.
*get the pobj_instance .
  CALL METHOD cl_pobj_process_object=>get
    EXPORTING
      pobj_guid     = me->a_pobj
      consumer_id   = c_consumer_id
    IMPORTING
      pobj_instance = lo_pobj_instance.


  ls_unlock_pobj-level_id = 1.
  ls_unlock_pobj-level_guid = me->a_pobj.
  APPEND ls_unlock_pobj TO lt_unlock_pobj.
  ENDIF
  .
  IF me->a_scenario IS NOT INITIAL.
  ls_unlock_pobj-level_id = 2.
  ls_unlock_pobj-level_guid = me->a_scenario.
  APPEND ls_unlock_pobj TO lt_unlock_pobj.
  ENDIF.

  IF me->a_step IS NOT INITIAL.
  ls_unlock_pobj-level_id = 3.
  ls_unlock_pobj-level_guid = me->a_step.
  APPEND ls_unlock_pobj TO lt_unlock_pobj.
  ENDIF.
  IF lt_unlock_pobj IS NOT INITIAL.
  CALL METHOD lo_pobj_instance->unlock
    EXPORTING
      unlock_object = lt_unlock_pobj.
  ENDIF.

ENDMETHOD.
