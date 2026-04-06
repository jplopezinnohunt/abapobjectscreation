METHOD check_additionalunits.
  DATA:lt_check_error TYPE hrben00err_ess_det_consistency,
       lt_error_table TYPE hrben00err_ess,
       ls_event_permissions TYPE t74hb,
       ls_existing_costcred TYPE rpben_costcred_trans,
       lv_subrc TYPE sysubrc.

* additional units
  IF ( NOT iv_costcred_trans-addno IS INITIAL ) AND
     ( iv_costcred_trans-addun IS INITIAL ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_processed_plan-pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '043'
        msg_par1          = iv_processed_plan-txt_plan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'ADDNO_NOT_ALLOWED'
        structurename     = 'COSTCRED_TRANS'
        fieldname         = 'ADDNO'
      IMPORTING
        consistency_error = lt_check_error.
    APPEND LINES OF lt_check_error TO et_costcred_check_error.
* min max check
    IF ( iv_costcred_trans-addno < iv_costcred_trans-addmi ) OR
    ( ( iv_costcred_trans-addno > iv_costcred_trans-addma ) AND
    ( NOT iv_costcred_trans-addma IS INITIAL ) ).
      CALL FUNCTION 'HR_BEN_ESS_HANDLE_ERR_MIN_MAX'
        EXPORTING
          pernr               = iv_processed_plan-pernr
          msg_class_min_max   = 'HRBEN00FMODULES'
          msg_number_min_max  = '009'
          msg_class_only_min  = 'HRBEN00FMODULES'
          msg_number_only_min = '101'
          minimum             = iv_costcred_trans-addmi
          maximum             = iv_costcred_trans-addma
          txt_plan            = iv_processed_plan-txt_plan
          severity            = 8
          messagekey_min_max  = 'ADDNO_OUTSIDE_LIMITS'
          messagekey_only_min = 'ADDNO_TOO_LOW'
          structurename       = 'COSTCRED_TRANS'
          fieldname           = 'ADDNO'
        IMPORTING
          consistency_error   = lt_check_error.
      APPEND LINES OF lt_check_error TO et_costcred_check_error.
    ENDIF.
  ENDIF.
* Detailed checks for increase and decrease (for adjustment reasons)
  CHECK iv_selected_enroll_reason-enrty = c_event_offer.
  CALL FUNCTION 'HR_BEN_ESS_GET_EVT_PERMISSIONS'
    EXPORTING
      pernr             = iv_processed_plan-pernr
      barea             = iv_processed_plan-barea
      bpcat             = iv_processed_plan-bpcat
      pltyp             = iv_processed_plan-pltyp
      bplan             = iv_processed_plan-bplan
      begda             = iv_processed_plan-begda
      endda             = iv_processed_plan-endda
    IMPORTING
      event_permissions = ls_event_permissions
      subrc             = lv_subrc
      error_table       = lt_error_table.
* Add or Change allowed -> no restriction for increase or decrease
  IF ls_event_permissions-add_bplan = c_false AND ls_event_permissions-chg_bplan = c_false.
    CALL FUNCTION 'HR_BEN_ESS_GET_EXIST_COSTCRED'
      EXPORTING
        pernr             = iv_processed_plan-pernr
        barea             = iv_processed_plan-barea
        bpcat             = iv_processed_plan-bpcat
        pltyp             = iv_processed_plan-pltyp
        bplan             = iv_processed_plan-bplan
        begda             = iv_processed_plan-begda
        endda             = iv_processed_plan-endda
      IMPORTING
        existing_costcred = ls_existing_costcred
        subrc             = lv_subrc
        error_table       = lt_error_table.
    CHECK ls_existing_costcred IS NOT INITIAL.
    IF ( ( iv_costcred_trans-addno > ls_existing_costcred-addno ) AND
         ( ls_event_permissions-inc_addno = c_false ) ).
      CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
        EXPORTING
          pernr             = iv_processed_plan-pernr
          msg_class         = 'HRBEN00FMODULES'
          msg_number        = '085'
          msg_par1          = iv_processed_plan-txt_plan
          msg_par2          = ''
          msg_par3          = ''
          msg_par4          = ''
          severity          = 8
          messagekey        = 'NO_INCREASE_ADDNO'
          structurename     = 'COSTCRED_TRANS'
          fieldname         = 'ADDNO'
        IMPORTING
          consistency_error = lt_check_error.
      APPEND LINES OF lt_check_error TO et_costcred_check_error.
    ENDIF.
    IF ( ( iv_costcred_trans-addno < ls_existing_costcred-addno ) AND
   ( ls_event_permissions-dec_addno = c_false ) ).
      CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
        EXPORTING
          pernr             = iv_processed_plan-pernr
          msg_class         = 'HRBEN00FMODULES'
          msg_number        = '086'
          msg_par1          = iv_processed_plan-txt_plan
          msg_par2          = ''
          msg_par3          = ''
          msg_par4          = ''
          severity          = 8
          messagekey        = 'NO_DECREASE_ADDNO'
          structurename     = 'COSTCRED_TRANS'
          fieldname         = 'ADDNO'
        IMPORTING
          consistency_error = lt_check_error.
      APPEND LINES OF lt_check_error TO et_costcred_check_error.
    ENDIF.
  ENDIF.
ENDMETHOD.
