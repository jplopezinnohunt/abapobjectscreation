FUNCTION z_ubc_user_get_by_email.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     REFERENCE(I_EMAIL) TYPE  UBC_DT_FEMAIL
*"  EXPORTING
*"     REFERENCE(E_USER) TYPE  UNAME
*"  EXCEPTIONS
*"      USER_NOT_FOUND
*"----------------------------------------------------------------------
  DATA: l_t_comm_keys TYPE TABLE OF adcomkey WITH HEADER LINE,
        l_search LIKE soxea-address.
  l_search = i_email.
  CALL FUNCTION 'ADDR_COMM_FIND_KEY'
    EXPORTING
      comm_type           = 'INT'
      search_string       = l_search
      case_sensitive_smtp = space
    TABLES
      comm_keys           = l_t_comm_keys
    EXCEPTIONS
      OTHERS              = 1.
  IF sy-subrc <> 0.
    MESSAGE e701(UBC_CSP) WITH i_email RAISING user_not_found.
  ENDIF.
  LOOP AT l_t_comm_keys.
    IF l_t_comm_keys-objtype = 'USR01'.
      e_user = l_t_comm_keys-objkey.
      EXIT. "from loop
    ENDIF.
  ENDLOOP.
  IF e_user IS INITIAL.
* eigentlich müsste hier noch mehr/anders geprüft werden
    MESSAGE e701(UBC_CSP) WITH i_email RAISING user_not_found.
  ENDIF.
ENDFUNCTION.