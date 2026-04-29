FUNCTION /citipmw/v3_exit_cgi_debt_name.
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

  DATA: lv_debt_name(35),
        lv_debt_name_temp(35),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        l_fpayhx    TYPE fpayhx,
        itab_adrc TYPE TABLE OF adrc,
        wa_adrc TYPE adrc,
        wa_addrnr TYPE ad_addrnum,
        wa_t001        LIKE t001.

  lwa_item = i_item.
  l_fpayh  = lwa_item-fpayh.
  l_fpayhx = lwa_item-fpayhx.

  CLEAR: wa_t001,wa_adrc,wa_addrnr.
  SELECT SINGLE * FROM t001 INTO wa_t001 WHERE bukrs = lwa_item-fpayh-zbukr.
  wa_addrnr = wa_t001-adrnr.

  IF NOT wa_addrnr IS INITIAL.            " Note 1857318
    CALL FUNCTION 'ADDR_SELECT_ADRC_SINGLE'
      EXPORTING
        addrnumber        = wa_addrnr
      TABLES
        et_adrc           = itab_adrc
      EXCEPTIONS
        address_not_exist = 1
        parameter_error   = 2
        internal_error    = 3
        OTHERS            = 4.
    IF sy-subrc <> 0.
*    MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
*          WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.

    ELSE.
*        READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = i_uparam+213(1).
      READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = l_fpayhx-nation.
      IF NOT wa_adrc IS INITIAL.
        MOVE wa_adrc-name1 TO lv_debt_name_temp.
      ENDIF.

    ENDIF.
  ENDIF.

  IF lv_debt_name_temp IS INITIAL.
    SELECT SINGLE butxt FROM t001 INTO lv_debt_name
      WHERE bukrs = lwa_item-fpayh-zbukr.
  ELSE.
    lv_debt_name = lv_debt_name_temp.
  ENDIF.

  c_value = lv_debt_name.

ENDFUNCTION.