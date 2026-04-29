FUNCTION /citipmw/v3_get_cdtr_email .
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------

  DATA: lv_email(241),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        itab_adr6 TYPE TABLE OF adr6,
        wa_adr6 TYPE adr6,
        wa_addrnr TYPE ad_addrnum,
        wa_t001        LIKE t001,
        ls_xbelnr    LIKE bsec-belnr,
        ls_xbukrs    LIKE bsec-bukrs,
        ls_xbuzei    LIKE bsec-buzei,
        ls_xgjahr    LIKE bsec-gjahr,
        ls_xbsec     LIKE bsec .

  lwa_item = i_item.
  l_fpayh  = lwa_item-fpayh.

  CLEAR: wa_addrnr.
  IF NOT l_fpayh-gpa1t EQ '14'. "If not Onetime Vendor
    wa_addrnr = lwa_item-fpayh-zadnr.
    IF NOT wa_addrnr IS INITIAL.
      CALL FUNCTION 'ADDR_SELECT_ADR6_SINGLE'
        EXPORTING
          addrnumber                = wa_addrnr
*   PERSNUMBER                = ' '
       TABLES
         et_adr6                   = itab_adr6
       EXCEPTIONS
         comm_data_not_exist       = 1
         parameter_error           = 2
         internal_error            = 3
         OTHERS                    = 4          .
      IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.

      ELSE.
        READ TABLE itab_adr6 INTO wa_adr6 WITH KEY flg_nouse = ' '.
        IF NOT wa_adr6 IS INITIAL.
          MOVE wa_adr6-smtp_addr TO lv_email.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.
  c_value = lv_email.

ENDFUNCTION.