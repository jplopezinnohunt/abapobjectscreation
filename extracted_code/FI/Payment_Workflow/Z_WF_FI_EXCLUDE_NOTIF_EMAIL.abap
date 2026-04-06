FUNCTION z_wf_fi_exclude_notif_email.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(I_UNAME) TYPE  UNAME OPTIONAL
*"     REFERENCE(I_WI_HDR) TYPE  SWR_WIHDR OPTIONAL
*"  CHANGING
*"     REFERENCE(C_EMAIL) TYPE  STRING OPTIONAL
*"----------------------------------------------------------------------

  DATA: wl_parva TYPE usr05-parva.
  SELECT SINGLE parva
    FROM usr05
    INTO wl_parva
   WHERE bname EQ i_uname
     AND parid EQ 'Z_WKF_EMAIL_NOTIF'
     AND parva EQ 'X'.

  CHECK sy-subrc NE 0.
  c_email = space.
  free c_email.


ENDFUNCTION.