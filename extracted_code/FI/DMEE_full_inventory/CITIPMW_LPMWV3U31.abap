FUNCTION /citipmw/v3_paymedium_dmee_05 .
*"--------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(IS_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(IS_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"     VALUE(I_PAYMEDIUM) TYPE  XFELD OPTIONAL
*"  EXPORTING
*"     REFERENCE(ES_FPAYHX) LIKE  FPAYHX_FREF STRUCTURE  FPAYHX_FREF
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"--------------------------------------------------------------------

  DATA:   ls_t001      TYPE t001,
          ls_t045t     TYPE t045t,
          l_tabix      TYPE sy-tabix,
          ls_xbelnr    LIKE bsec-belnr,
          ls_xbukrs    LIKE bsec-bukrs,
          ls_xbuzei    LIKE bsec-buzei,
          ls_xgjahr    LIKE bsec-gjahr,
          ls_xbsec     LIKE bsec .

  TABLES: addr1_sel, addr1_val, t001, t045t,fpayp.

  CLEAR: addr1_sel, addr1_val.

  DATA: itab TYPE STANDARD TABLE OF fpayp.
  DATA: wa LIKE LINE OF itab .

  itab[] = t_fpayp[].

  CALL FUNCTION 'FI_COMPANY_CODE_DATA'
    EXPORTING
      i_bukrs      = is_fpayh-zbukr
    IMPORTING
      e_t001       = ls_t001
    EXCEPTIONS
      system_error = 1
      OTHERS       = 2.
  IF sy-subrc NE 0.
    CLEAR ls_t001.
  ENDIF.
  addr1_sel-addrnumber = ls_t001-adrnr.


  CALL FUNCTION 'ADDR_GET'
    EXPORTING
      address_selection = addr1_sel
    IMPORTING
      address_value     = addr1_val
    EXCEPTIONS
      parameter_error   = 0
      address_not_exist = 0
      version_not_exist = 0.

  IF NOT ( addr1_val IS INITIAL ).
    es_fpayhx-ref01+0(60)   = addr1_val-street.
    es_fpayhx-ref01+60(20)  = addr1_val-building.
    es_fpayhx-ref01+80(10)  = addr1_val-post_code1.
    es_fpayhx-ref01+90(10)  = addr1_val-region.
    es_fpayhx-ref01+100(10) = addr1_val-house_num1.         "1923419
    es_fpayhx-ref06+0(40)   = addr1_val-city1.              "1923419
    LOOP AT itab INTO wa.
      wa-ref01+0(60)   = addr1_val-street.
      wa-ref01+60(20)  = addr1_val-building.
      wa-ref01+80(10)  = addr1_val-post_code1.
      wa-ref01+90(10)  = addr1_val-region.
      wa-ref01+100(10)  = addr1_val-house_num1.             "1923419
      l_tabix = sy-tabix.
      MODIFY itab FROM wa INDEX l_tabix.
      CLEAR:wa.
    ENDLOOP.
    t_fpayp[] = itab[].

  ENDIF.
  CLEAR addr1_sel-addrnumber.

*Get Vendor details.
*check for the One time Vendor..for One time Vendor/CPD vendor there would not any address number..
*For one time vendor/CPD vendor the value of FPAYH-GPA1T would be always 14....
  IF is_fpayh-gpa1t EQ '14'.
    ls_xbelnr = is_fpayh-doc1r+4(10).
    ls_xbukrs = is_fpayh-doc1r(4).
    ls_xbuzei = '001'.
    ls_xgjahr = is_fpayh-doc1r+14(4).

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
        es_fpayhx-ref02+0(10)  = ls_xbsec-pstl2.
      ENDIF.
    ENDIF.
  ELSE.
    addr1_sel-addrnumber = is_fpayh-zadnr.

    CALL FUNCTION 'ADDR_GET'
      EXPORTING
        address_selection = addr1_sel
      IMPORTING
        address_value     = addr1_val
      EXCEPTIONS
        parameter_error   = 0
        address_not_exist = 0
        version_not_exist = 0.

    IF NOT ( addr1_val IS INITIAL ).
      es_fpayhx-ref02+0(10)  = addr1_val-post_code2.
      es_fpayhx-ref02+10(10)  = addr1_val-house_num1.       "1923419
    ENDIF.

  ENDIF.
* Check if SEPA payment.
*  SEPA payments with swift code:
  IF 'BE BG DK DE EE FI FR GR IE IT LI LV LT LU MT NL AT PL PT RO SE SK SI ES CZ HU GB CY CH NO MC FL IS HR SM GF GI GP MQ YT RE MF PM'
               CS is_fpayh-zbnks AND                        "N2014681
     'BE BG DK DE EE FI FR GR IE IT LI LV LT LU MT NL AT PL PT RO SE SK SI ES CZ HU GB CY CH NO MC FL IS HR SM GF GI GP MQ YT RE MF PM'
              CS is_fpayhx-ubiso AND                             "Note 2085781
        is_fpayhx-waers =  'EUR' AND
        is_fpayhx-uiban <> space AND
        is_fpayhx-uswif <> space AND
        is_fpayhx-xschk =  space AND
*        is_fpayh-zswif  <> space AND  "N1972493
        is_fpayh-ziban  <> space.

    es_fpayhx-ref03 = 'S'.       "If SEPA payment

  ELSE.
    es_fpayhx-ref03 = 'N'.       "If not SEPA payment

  ENDIF.

*Get Member Bank Identification.
  SELECT SINGLE * FROM  t045t INTO ls_t045t WHERE  bukrs = is_fpayh-zbukr
                                            AND    zlsch = is_fpayh-rzawe
                                            AND    hbkid = is_fpayh-hbkid
                                            AND    hktid = is_fpayh-hktid.
  IF sy-subrc EQ 0.
    es_fpayhx-ref04 = ls_t045t-dtaid.
  ENDIF.

* Check Clearing System ID (ISO External Code List)
  CALL FUNCTION '/CITIPMW/V3_GET_BANKCODE'
    EXPORTING
      i_banks = is_fpayh-zbnks
      i_bankl = is_fpayh-zbnkl
    IMPORTING
      e_ecsic = es_fpayhx-ref05.

ENDFUNCTION.