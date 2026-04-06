FUNCTION z_get_certif_officer_unesdir .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(POSTING_INVOICE_AGENT_EMAIL) TYPE  ADR6-SMTP_ADDR
*"  TABLES
*"      CERTIFYING_OFFICERS_EMAILS STRUCTURE  ZAD_SMTPADR OPTIONAL
*"  EXCEPTIONS
*"      SYSTEM_FAILURE
*"      COMMUNICATION_FAILURE
*"      ERROR
*"----------------------------------------------------------------------
*Modification FGU 24.06.2019
*  CALL FUNCTION 'Z_GET_CERTIF_OFFICER_UNESDIR'
*    DESTINATION 'BOC_INVOICE_WF'
*    EXPORTING
*      posting_invoice_agent_email = posting_invoice_agent_email
*    TABLES
*      certifying_officers_EMAILS  = certifying_officers_emails
*    EXCEPTIONS
*      system_failure              = 1
*      communication_failure       = 2
*      error                       = 3
*      OTHERS                      = 4.
*
*  CASE sy-subrc.
*    WHEN 0.
*      COMMIT WORK.
*
*    WHEN 1.
*      RAISE system_failure.
*
*    WHEN 2.
*      RAISE communication_failure.
*
*    WHEN OTHERS.
*      RAISE error.
*
*  ENDCASE.
  DATA : lo_proxy  TYPE REF TO zrole_mgtco_facade,
         ls_input  TYPE zfacade_get_certifying_office1,
         ls_output TYPE zfacade_get_certifying_officer.
  FIELD-SYMBOLS <fs> TYPE zrole_member_item.
  ls_input-request-email = posting_invoice_agent_email.
  TRY.
      CREATE OBJECT lo_proxy
        EXPORTING
          logical_port_name = 'LP_ROLE_MGT'.
      lo_proxy->get_certifying_officers_by_emp(
        EXPORTING
          input  = ls_input
        IMPORTING
          output =  ls_output
      ).
    CATCH cx_ai_system_fault . " Application Integration: Technical Error
      RAISE communication_failure.
  ENDTRY.
  LOOP AT ls_output-get_certifying_officers_by_emp-items-role_member_item ASSIGNING
    APPEND <fs>-email TO  certifying_officers_emails.
  ENDLOOP.
ENDFUNCTION.