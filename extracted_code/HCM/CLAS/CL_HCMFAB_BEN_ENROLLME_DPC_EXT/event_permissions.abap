METHOD event_permissions.
  DATA: existing_contrib  TYPE rpben_contrib_trans,
        test_error_lt     TYPE hrben00err_ess_det_consistency,
        contrib_check_error TYPE hrben00err_ess_det_consistency,
        ls_contrib_check_error TYPE rpbenerr_ess_det_consistency,
        ls_error TYPE rpbenerr.
  CLEAR:event_permissions,subrc.
  CALL FUNCTION 'HR_BEN_ESS_GET_EVT_PERMISSIONS'
    EXPORTING
      pernr             = iv_pernr
      barea             = iv_ben_area
      bpcat             = iv_bpcat
      pltyp             = iv_pltyp
      bplan             = iv_bplan
      begda             = iv_begda
      endda             = iv_endda
    IMPORTING
      event_permissions = event_permissions
      subrc             = subrc
      error_table       = error_table.
  CHECK subrc = 0.
*
* Add or Change allowed -> no restriction for increase or decrease
  CHECK event_permissions-add_bplan = c_false AND event_permissions-chg_bplan = c_false.
*
  CALL FUNCTION 'HR_BEN_ESS_GET_EXIST_CONTRIB'
    EXPORTING
      pernr            = iv_pernr
      barea            = iv_ben_area
      bpcat            = iv_bpcat
      pltyp            = iv_pltyp
      bplan            = iv_bplan
      begda            = iv_begda
      endda            = iv_endda
    IMPORTING
      existing_contrib = existing_contrib
      subrc            = subrc
      error_table      = error_table.
  CHECK subrc = 0.
  CHECK NOT existing_contrib IS INITIAL.
*
* Regular contributions
  IF ( ( iv_eepct > existing_contrib-eepct ) AND
       ( event_permissions-inc_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '087'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_eepct < existing_contrib-eepct ) AND
       ( event_permissions-dec_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '088'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_eeamt > existing_contrib-eeamt ) AND
       ( event_permissions-inc_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '087'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_eeamt < existing_contrib-eeamt ) AND
       ( event_permissions-dec_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '088'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_eeunt > existing_contrib-eeunt ) AND
       ( event_permissions-inc_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '087'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_eeunt < existing_contrib-eeunt ) AND
       ( event_permissions-dec_preco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '088'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'EEUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptpct > existing_contrib-ptpct ) AND
       ( event_permissions-inc_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '089'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptpct < existing_contrib-ptpct ) AND
       ( event_permissions-dec_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '090'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptamt > existing_contrib-ptamt ) AND
       ( event_permissions-inc_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '089'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptamt < existing_contrib-ptamt ) AND
       ( event_permissions-dec_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '090'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptunt > existing_contrib-ptunt ) AND
       ( event_permissions-inc_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '089'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_ptunt < existing_contrib-ptunt ) AND
       ( event_permissions-dec_pstco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '090'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'PTUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
* Bonus contributions
  IF ( ( iv_bcpct > existing_contrib-bcpct ) AND
       ( event_permissions-inc_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '091'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bcpct < existing_contrib-bcpct ) AND
       ( event_permissions-dec_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '092'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bcamt > existing_contrib-bcamt ) AND
       ( event_permissions-inc_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '091'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bcamt < existing_contrib-bcamt ) AND
       ( event_permissions-dec_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '092'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bcunt > existing_contrib-bcunt ) AND
       ( event_permissions-inc_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '091'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bcunt < existing_contrib-bcunt ) AND
       ( event_permissions-dec_bprco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '092'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_PRETAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BCUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bppct > existing_contrib-bppct ) AND
       ( event_permissions-inc_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '093'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bppct < existing_contrib-bppct ) AND
       ( event_permissions-dec_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '094'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPPCT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bpamt > existing_contrib-bpamt ) AND
       ( event_permissions-inc_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '093'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bpamt < existing_contrib-bpamt ) AND
       ( event_permissions-dec_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '094'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPAMT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bpunt > existing_contrib-bpunt ) AND
       ( event_permissions-inc_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '093'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_INCREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.
*
  IF ( ( iv_bpunt < existing_contrib-bpunt ) AND
       ( event_permissions-dec_bptco = c_false ) ).
    CALL FUNCTION 'HR_BEN_ESS_HANDLE_CHECK_ERRORS'
      EXPORTING
        pernr             = iv_pernr
        msg_class         = 'HRBEN00FMODULES'
        msg_number        = '094'
        msg_par1          = iv_txtplan
        msg_par2          = ''
        msg_par3          = ''
        msg_par4          = ''
        severity          = 8
        messagekey        = 'NO_DECREASE_BONUS_POSTTAX'
        structurename     = 'CONTRIB_TRANS'
        fieldname         = 'BPUNT'
      IMPORTING
        consistency_error = test_error_lt.
    APPEND LINES OF test_error_lt TO contrib_check_error.
  ENDIF.

  IF contrib_check_error IS NOT INITIAL.
    LOOP AT contrib_check_error INTO ls_contrib_check_error.
      CLEAR ls_error.
      MOVE-CORRESPONDING ls_contrib_check_error TO ls_error.
      APPEND ls_error TO error_table.
    ENDLOOP.
  ENDIF.
ENDMETHOD.
