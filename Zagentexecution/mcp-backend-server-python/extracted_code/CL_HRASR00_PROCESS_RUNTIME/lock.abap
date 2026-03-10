METHOD lock.

  DATA no_authority TYPE boole_d.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_lock_pobj TYPE pobjs_lock_objects.
  DATA lt_lock_pobj TYPE pobjt_lock_objects.
  DATA ls_unlock_pobj TYPE pobjs_unlock_objects.
  DATA lt_unlock_pobj TYPE pobjt_unlock_objects.
  DATA lock_failed TYPE boole_d.
  DATA exception_obj TYPE REF TO cx_root.
  DATA already_locked TYPE boole_d.
  DATA lock_user TYPE sy-uname.
  DATA msg TYPE symsg.

  DATA lock_count TYPE i.
  CLEAR ls_lock_pobj.
  CLEAR lt_lock_pobj.
  is_ok = true.

  CALL METHOD cl_pobj_process_object=>get
    EXPORTING
      pobj_guid     = me->a_pobj
      consumer_id   = c_consumer_id
    IMPORTING
      pobj_instance = lo_pobj_instance.

**** Locking a POBJ is successful only on successful acquisition of the LEVEL 1 LOCK. This will be the entry point for any lock
**** on POBJ. On success, LEVEL 2 and LEVEL 3 are tried to be acquired. In case if they fail for any reason, is_ok is set to FALSE
***  which is appropriately handled by the called of this LOCK Method

  ls_lock_pobj-level_id = 1.
  ls_lock_pobj-level_guid = me->a_pobj.
  APPEND ls_lock_pobj TO lt_lock_pobj.

  lock_failed = true.
  lock_count = 0.
*Keep trying the lock indefinitely.
  WHILE lock_failed EQ true.
    is_ok = true.
    lock_count = lock_count + 1.

    CALL METHOD lo_pobj_instance->lock
      EXPORTING
        lock_object    = lt_lock_pobj
      IMPORTING
        already_locked = already_locked
        lock_user      = lock_user.
    IF already_locked EQ 'X'.
      lock_failed = true.
      WAIT UP TO 5 SECONDS.
      is_ok = false.
    ELSE.
      is_ok = true.
      lock_failed = false.
    ENDIF.
  ENDWHILE.

  IF lock_failed = false AND lock_count > 1.
    MESSAGE ID 'HRASR00_PROCESS' TYPE 'I' NUMBER '140' WITH 'Number of attempts to acquire the lock: ' lock_count INTO dummy.
    MOVE-CORRESPONDING sy TO msg.
    CALL METHOD message_handler->add_message
      EXPORTING
        message = msg.
*     Write the information to application log: Log the number of attempts to acquire the lock before
    CLEAR exception_obj.
    CALL METHOD me->write_application_log
      EXPORTING
        message_handler = message_handler
        exception_obj   = exception_obj.

    is_ok = true.
  ENDIF.

*** On successful locking of LEVEL 1, try locking LEVEL 2 and 3.
  CLEAR lt_lock_pobj.
  IF NOT me->a_scenario IS INITIAL.
    ls_lock_pobj-level_id = 2.
    ls_lock_pobj-level_guid = me->a_scenario.
    APPEND ls_lock_pobj TO lt_lock_pobj.
  ENDIF.

  IF NOT me->a_step IS INITIAL.
    ls_lock_pobj-level_id = 3.
    ls_lock_pobj-level_guid = me->a_step.
    APPEND ls_lock_pobj TO lt_lock_pobj.
  ENDIF.


  CALL METHOD lo_pobj_instance->lock
    EXPORTING
      lock_object = lt_lock_pobj.

ENDMETHOD.
