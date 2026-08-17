FUNCTION y_fi_paymedium_41 .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"  TABLES
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"  CHANGING
*"     REFERENCE(C_WAERS) LIKE  FPAYH-WAERS
*"     REFERENCE(C_SUM) LIKE  FPAYH-RWBTR
*"----------------------------------------------------------------------

  STATICS : s_laufd LIKE fpayh-laufd, s_laufi LIKE fpayh-laufi.
  DATA lv_subrc TYPE sy-subrc.
  DATA lv_variant TYPE rsvar-variant.

  IF i_fpayh-laufd = s_laufd AND i_fpayh-laufi = s_laufi.
    EXIT. " leave exit 41
  ELSE.
    s_laufd = i_fpayh-laufd. " continue, first call to exit 41
    s_laufi = i_fpayh-laufi.
  ENDIF.


  DATA : lc_jobname     LIKE tbtcjob-jobname,
         lc_jobcount    LIKE tbtcjob-jobcount,
         lc_jobreleased LIKE btch0000-char1.

  lv_variant = i_fpayh-zbukr.

  "Check if vriant exist for RFFOAVIS_FPAYM
  CALL FUNCTION 'RS_VARIANT_EXISTS'
    EXPORTING
      report              = 'RFFOAVIS_FPAYM'
      variant             = lv_variant
    IMPORTING
      r_c                 = lv_subrc
    EXCEPTIONS
      not_authorized      = 1
      no_report           = 2
      report_not_existent = 3
      report_not_supplied = 4
      OTHERS              = 5.
  IF sy-subrc <> 0 OR lv_subrc <> 0.
    EXIT.
  ENDIF.

  CONCATENATE 'PAYM_ADVICES:' i_fpayh-laufd '/' i_fpayh-laufi
                  INTO lc_jobname.
  CALL FUNCTION 'JOB_OPEN'
    EXPORTING
      jobname  = lc_jobname
    IMPORTING
      jobcount = lc_jobcount
    EXCEPTIONS
      OTHERS   = 1.
  IF sy-subrc NE 0.
    CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
      EXPORTING
        i_msgid     = sy-msgid
        i_msgty     = 'E'
        i_msgno     = sy-msgno
        i_msgv1     = sy-msgv1
        i_msgv2     = sy-msgv2
        i_msgv3     = sy-msgv3
        i_msgv4     = sy-msgv3
        i_probclass = 'E'.
    EXIT.
  ENDIF.

  SUBMIT rffoavis_fpaym
    USING SELECTION-SET lv_variant
    USER sy-uname VIA JOB lc_jobname NUMBER  lc_jobcount
    WITH zw_laufd = i_fpayh-laufd
    WITH zw_laufi = i_fpayh-laufi
    WITH zw_xvorl = i_fpayh-xvorl
    AND RETURN.

  CALL FUNCTION 'JOB_CLOSE'
    EXPORTING
      jobcount         = lc_jobcount
      jobname          = lc_jobname
      strtimmed        = 'X'
    IMPORTING
      job_was_released = lc_jobreleased
    EXCEPTIONS
      OTHERS           = 1.

  IF sy-subrc NE 0.
    CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
      EXPORTING
        i_msgid     = sy-msgid
        i_msgty     = 'E'
        i_msgno     = sy-msgno
        i_msgv1     = sy-msgv1
        i_msgv2     = sy-msgv2
        i_msgv3     = sy-msgv3
        i_msgv4     = sy-msgv3
        i_probclass = 'E'.
  ENDIF.

ENDFUNCTION.