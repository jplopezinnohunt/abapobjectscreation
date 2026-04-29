FUNCTION /citipmw/v3_get_cdtr_mobile.
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

  DATA: lv_telnr_long(35),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        itab_adr2 TYPE TABLE OF adr2,
        wa_adr2 TYPE adr2,
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
  IF NOT l_fpayh-gpa1t EQ '14'. " IF not onetime Vendor
    wa_addrnr = lwa_item-fpayh-zadnr.
    IF NOT wa_addrnr IS INITIAL.
      CALL FUNCTION 'ADDR_SELECT_ADR2_SINGLE'
        EXPORTING
          addrnumber                = wa_addrnr
*   PERSNUMBER                = ' '
       TABLES
         et_adr2                   = itab_adr2
       EXCEPTIONS
         comm_data_not_exist       = 1
         parameter_error           = 2
         internal_error            = 3
         OTHERS                    = 4
               .
      IF sy-subrc <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.

      ELSE.
        READ TABLE itab_adr2 INTO wa_adr2 WITH KEY flg_nouse = ' ' dft_receiv = 'X'.
        IF NOT wa_adr2 IS INITIAL.
          MOVE wa_adr2-telnr_long TO lv_telnr_long.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.
  c_value = lv_telnr_long.

ENDFUNCTION.