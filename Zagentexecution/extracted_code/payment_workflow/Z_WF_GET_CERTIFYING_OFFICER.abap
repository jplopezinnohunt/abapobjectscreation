FUNCTION z_wf_get_certifying_officer .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  TABLES
*"      ACTOR_TAB STRUCTURE  SWHACTOR
*"      AC_CONTAINER STRUCTURE  SWCONT
*"  EXCEPTIONS
*"      SYSTEM_FAILURE
*"      COMMUNICATION_FAILURE
*"      ERROR
*"      NOBODY_FOUND
*"----------------------------------------------------------------------
  INCLUDE <cntain>.

  DATA: wt_certifying_officers        TYPE TABLE OF rsplppm_s_uname,
        wt_certifying_officers_emails TYPE TABLE OF adr6-smtp_addr.
  DATA: wl_agent      TYPE wfsyst-agent,
        wl_user_email TYPE adr6-smtp_addr,
        wl_co_user    TYPE sy-uname,
        ls_usr21      TYPE usr21,
        ls_adr6       TYPE adr6.
  FIELD-SYMBOLS: <email> TYPE adr6-smtp_addr.
  FIELD-SYMBOLS: <user> TYPE zfi_payrel_email.
  DATA: lt_emails TYPE TABLE OF zfi_payrel_email.

  "For trace
  DATA lv_subrc TYPE sy-subrc.
  DATA lo_trace TYPE REF TO ycl_bc_trace_table.
  DATA ls_trace_data TYPE ysbc_trace_payment.

  lv_subrc = 9.

  swc_get_element ac_container 'Posting_Invoice_Agent' wl_agent.

* Posting Invoice Agent's e-mail from SU01
  SELECT SINGLE *
    FROM usr21
    INTO ls_usr21
   WHERE bname = wl_agent+2.

  IF sy-subrc = 0.
    SELECT SINGLE *
      FROM adr6
      INTO ls_adr6
     WHERE addrnumber = ls_usr21-addrnumber
       AND persnumber = ls_usr21-persnumber
       AND flgdefault = 'X'.
    IF sy-subrc NE 0.
* User has no email ???

    ELSE.
      wl_user_email = ls_adr6-smtp_addr.
      CALL FUNCTION 'Z_GET_CERTIF_OFFICER_UNESDIR'
*       IN BACKGROUND TASK
*       DESTINATION 'BOC_INVOICE_WF'
        EXPORTING
          posting_invoice_agent_email = wl_user_email
        TABLES
          certifying_officers_emails  = wt_certifying_officers_emails
        EXCEPTIONS
          system_failure              = 1
          communication_failure       = 2
          error                       = 3
          OTHERS                      = 5.

      lv_subrc = sy-subrc.

      CASE sy-subrc.
        WHEN 0.
          LOOP AT wt_certifying_officers_emails ASSIGNING <email>.

            CALL FUNCTION 'Z_UBC_USER_GET_BY_EMAIL'
              EXPORTING
                i_email        = <email>
              IMPORTING
                e_user         = wl_co_user
              EXCEPTIONS
                user_not_found = 1
                OTHERS         = 2.

            IF sy-subrc <> 0.
*             MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*                WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
            ELSE.
              actor_tab-otype = 'US'.
              TRANSLATE wl_co_user TO UPPER CASE.
              actor_tab-objid = wl_co_user.
              APPEND actor_tab.
            ENDIF.

          ENDLOOP.

        WHEN 1.
*          RAISE system_failure.

        WHEN 2.
*          RAISE communication_failure.

        WHEN OTHERS.
*          RAISE error.

      ENDCASE.

    ENDIF.
  ENDIF.

  DESCRIBE TABLE actor_tab.
  CHECK sy-tfill EQ 0.
*          RAISE nobody_found.
* Default User/emails for Workflow FI Payment Release notifications
  SELECT *
    FROM zfi_payrel_email
    INTO TABLE lt_emails.

  LOOP AT lt_emails ASSIGNING <user>.
    actor_tab-otype = 'US'.
    actor_tab-objid = <user>-bname.
    APPEND actor_tab.
  ENDLOOP.

  "Set trace in case of default certifying officers set
  ls_trace_data-agent = wl_agent.
  ls_trace_data-unesdir_subrc = lv_subrc.
  lo_trace = NEW ycl_bc_trace_table( iv_tr_obj = 'WF_PAYMENT' ).
  lo_trace->set_timestamp( ).
  lo_trace->set_trace( iv_data = ls_trace_data ).

ENDFUNCTION.