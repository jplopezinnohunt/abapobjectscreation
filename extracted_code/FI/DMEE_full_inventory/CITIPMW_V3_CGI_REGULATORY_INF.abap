FUNCTION /citipmw/v3_cgi_regulatory_inf.
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

  DATA: lv_id_skn(35),
        lwa_item       TYPE dmee_paym_if_type,
        l_fpayh        TYPE fpayh,
        l_fpayp        TYPE fpayp,
        l_fpayhx       TYPE fpayhx,
        itab_adrct TYPE TABLE OF adrct,
        wa_adrct TYPE adrct,
        wa_addrnr TYPE ad_addrnum.

  DATA: lv_nation  TYPE ad_nation.

  lwa_item = i_item.
  l_fpayh  = lwa_item-fpayh.
  l_fpayp = lwa_item-fpayp.
  l_fpayhx = lwa_item-fpayhx.
  lv_nation = l_fpayhx-nation.

  CLEAR: wa_addrnr.
*check for the One time Vendor..for One time Vendor/CPD vendor there would not any address number..
*For one time vendor/CPD vendor the value of FPAYH-GPA1T would be always 14....
  IF l_fpayh-gpa1t EQ '14'.

  ELSE.
* Indonesia domestic payments map SKN.
*    IF l_fpayhx-ubiso = 'ID' AND l_fpayhx-zbiso = 'ID' AND l_fpayhx-waers = 'IDR'.
* IDR payments to ID Vendors need SKN
    IF l_fpayhx-zbiso = 'ID' AND l_fpayhx-waers = 'IDR' AND l_fpayhx-pmtmtd = 'TRF'.

      wa_addrnr = lwa_item-fpayh-zadnr.

      IF NOT wa_addrnr IS INITIAL.                         " Note 1857318
        CALL FUNCTION 'ADDR_SELECT_ADRCT_SINGLE'
          EXPORTING
            addrnumber        = wa_addrnr
          TABLES
            et_adrct          = itab_adrct
          EXCEPTIONS
            address_not_exist = 1
            parameter_error   = 2
            internal_error    = 3
            OTHERS            = 4.

        IF sy-subrc <> 0.

        ELSE.
          READ TABLE itab_adrct INTO wa_adrct WITH KEY nation = lv_nation.            " Note 1961687
          IF NOT wa_adrct IS INITIAL.
            MOVE wa_adrct-remark TO lv_id_skn.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDIF.                                                  "N2050269
    c_value = lv_id_skn.
  ENDIF."One time vendor

* Poland SEPA payments map default value 'A60' for payments over 12500 EUROs
  IF l_fpayhx-svclvl_cd = 'SEPA' AND  l_fpayhx-ubiso = 'PL' AND l_fpayh-rwbtr GE 12500.
    c_value = 'A60'.
  ENDIF.

* New field 'Motive of Payment' is required(mandatory) for all Paraguay Fund Transfers
  DATA : l_bukrs TYPE bkpf-bukrs,
         l_belnr TYPE bkpf-belnr,
         l_gjahr TYPE bkpf-gjahr,
         l_bktxt.

  CLEAR : l_bktxt,l_bukrs,l_belnr,l_gjahr.

  l_bukrs = l_fpayp-doc2r(4).
  l_belnr = l_fpayp-doc2r+4(10).
  l_gjahr = l_fpayp-doc2r+14(4).

  IF l_fpayhx-ubiso = 'PY' AND  ( l_fpayhx-pmtmtd = 'DD' OR l_fpayhx-svclvl_cd = 'URGP' ).

    l_bktxt = 'X'.

  ELSEIF l_fpayhx-ubiso = 'MY'.

    IF l_fpayhx-svclvl_cd = 'BKTR'.

      l_bktxt = 'X'.

    ELSEIF l_fpayhx-svclvl_cd = 'URGP'.

      IF l_fpayhx-zbiso <> 'MY'.
        l_bktxt = 'X'.
      ENDIF.

    ENDIF.

  ENDIF.

  IF l_bktxt = 'X'.

    SELECT SINGLE bktxt FROM bkpf INTO c_value WHERE bukrs =  l_bukrs AND
                                                     belnr =  l_belnr AND
                                                     gjahr =  l_gjahr.
  ENDIF.

  clear l_bktxt.

ENDFUNCTION.