FUNCTION /citipmw/v3_get_cdtr_bldg.
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

  DATA: lv_building(35),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        l_fpayhx    TYPE fpayhx,
        itab_adrc TYPE TABLE OF adrc,
        wa_adrc TYPE adrc,
        wa_addrnr TYPE ad_addrnum,
        wa_t001        LIKE t001,
        ls_xbelnr    LIKE bsec-belnr,
        ls_xbukrs    LIKE bsec-bukrs,
        ls_xbuzei    LIKE bsec-buzei,
        ls_xgjahr    LIKE bsec-gjahr,
        ls_xbsec     LIKE bsec .

  lwa_item = i_item.
  l_fpayh  = lwa_item-fpayh.
  l_fpayhx = lwa_item-fpayhx.

  CLEAR: wa_addrnr.

  IF NOT l_fpayh-gpa1t EQ '14'. " IF not onetime Vendor

    wa_addrnr = lwa_item-fpayh-zadnr.

    IF NOT wa_addrnr IS INITIAL.                    " Note 1857318
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
*      MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
*            WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
      ELSE.
*    READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = i_uparam+213(1).
        READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = l_fpayhx-nation.
        IF NOT wa_adrc IS INITIAL.
          MOVE wa_adrc-building TO lv_building.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.
  c_value = lv_building.

ENDFUNCTION.