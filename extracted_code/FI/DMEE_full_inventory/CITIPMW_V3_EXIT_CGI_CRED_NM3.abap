FUNCTION /citipmw/v3_exit_cgi_cred_nm3.
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

  DATA: lv_cred_name(35),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        l_fpayp        type fpayp,
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
  l_fpayp  = lwa_item-fpayp.
  l_fpayhx = lwa_item-fpayhx.

  CLEAR: wa_addrnr.
*check for the One time Vendor..for One time Vendor/CPD vendor there would not any address number..
*For one time vendor/CPD vendor the value of FPAYH-GPA1T would be always 14....
  IF l_fpayh-gpa1t EQ '14'.
    ls_xbelnr = l_fpayh-doc1r+4(10).
    ls_xbukrs = l_fpayh-doc1r(4).
    ls_xbuzei = '001'.
    ls_xgjahr = l_fpayh-doc1r+14(4).

    CALL FUNCTION 'READ_BSEC'
      EXPORTING
        xbelnr         = ls_xbelnr
        xbukrs         = ls_xbukrs
        xbuzei         = ls_xbuzei
        xgjahr         = ls_xgjahr
      IMPORTING
        xbsec          = ls_xbsec
      EXCEPTIONS
        key_incomplete = 1
        not_authorized = 2
        not_found      = 3
        OTHERS         = 4.

    IF sy-subrc EQ 0.
      IF NOT ls_xbsec IS INITIAL .
        MOVE ls_xbsec-name3 TO lv_cred_name.
      ENDIF.
    ENDIF.
  ELSE.
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
*        MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
*              WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.

      ELSE.
*        READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = i_uparam+213(1).
        READ TABLE itab_adrc INTO wa_adrc WITH KEY nation = l_fpayhx-nation.
        IF NOT wa_adrc IS INITIAL.
          MOVE wa_adrc-name3 TO lv_cred_name.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF."One time vendor

**logic to check for payment request/F111/BCM. In this case the address can be taken directly from FPAYH
*For HR payments FPAYP-DOC2T = '03'
*For F111 payments FPAYP-DOC2T = '05'
  IF ( l_fpayh-dorigin = 'FI-AP-PR' OR l_fpayp-doc2t = '05' OR l_fpayp-doc2t = '03' ) AND lv_cred_name IS INITIAL.
    lv_cred_name = l_fpayh-znme3.
  ENDIF.

  c_value = lv_cred_name.

ENDFUNCTION.