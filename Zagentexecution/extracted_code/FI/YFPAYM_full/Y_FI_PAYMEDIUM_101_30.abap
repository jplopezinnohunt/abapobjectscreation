FUNCTION Y_FI_PAYMEDIUM_101_30.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_FPAYH) LIKE  FPAYH STRUCTURE  FPAYH
*"     VALUE(I_FPAYHX) LIKE  FPAYHX STRUCTURE  FPAYHX
*"  TABLES
*"      T_FPAYP STRUCTURE  FPAYP
*"      T_PAYMENT_DETAILS STRUCTURE  FPM_PAYD
*"      T_FILE_OUTPUT STRUCTURE  FPM_FILE
*"  EXCEPTIONS
*"      NO_PAYMENT
*"----------------------------------------------------------------------

*-----------------------------------------------------------------------
* Creates transaction records of payment medium format S.W.I.F.T. MT 101
* (sequence B)
*  Fields:
*  21           payment reference
*  21F          foreign exchange contract reference (not implemented)
*  23E          up to 4 instructions
*  32B          currency + amount
*  56A, C or D  intermediary bank
*  57A, C or D  payee's bank
*  59           payee's bankaccount
*  70           note to payee; payment usage
*  77B          German LZB reporting info
*  71A          details of charges of payment transaction
*  25A          sender's charges account
*-----------------------------------------------------------------------

* Data declarations
  DATA:
    ls_instparams     LIKE i015w1_par,   "instructions (23E)
    lt_payd           TYPE yt_payd,      "note to payee (70)
    l_hbukrs          LIKE t001-bukrs,   "other party (50L)
    ls_fpayh_bch      LIKE fpayh_bch,    "bank chain (56)
    ls_fpayhx_bch     LIKE fpayhx_bch,   "bank chain (56)
    li_sendercorr     TYPE n,            "bank chain (56)
    li_intermediary   TYPE n,            "bank chain (56)
    li_receivercorr   TYPE n,            "bank chain (56)
    ln_msgno          LIKE sy-msgno,
    lc_msgno          LIKE t100c-msgnr,
    lc_msgty          LIKE sy-msgty,
    lc_msgv3          LIKE sy-msgv3,
    lc_msgv4          LIKE sy-msgv4,
    lc_icon           LIKE icon-id.

  DATA:
    lt_bankchain  LIKE STANDARD TABLE OF fpm_bankchain
                 INITIAL SIZE 0 WITH HEADER LINE.     "intermediary bank

  DATA:
    BEGIN OF ls_mt101t,
      21_tag(4)        TYPE c,  "reference type 2
      21_value(16)     TYPE c,  "RENUM
      21F_tag(5)       TYPE c,
      21F_value(16)    TYPE c,
      23e_tag1(5)      TYPE c,  "instruction 1
      23e_value1(35)   TYPE c,
      23e_tag2(5)      TYPE c,  "instruction 2
      23e_value2(35)   TYPE c,
      23e_tag3(5)      TYPE c,  "instruction 3
      23e_value3(35)   TYPE c,
      23e_tag4(5)      TYPE c,  "instruction 4
      23e_value4(35)   TYPE c,
      32b_tag(5)       TYPE c,
      32b_value(18)    TYPE c,
      56_tag(5)        TYPE c,
      56_value1(35)    TYPE c,
      56_value2(35)    TYPE c,
      56_value3(35)    TYPE c,
      56_value4(35)    TYPE c,
      56_value5(35)    TYPE c,
      57_tag(5)        TYPE c,  "payee's bank
      57_value1(35)    TYPE c,
      57_value2(35)    TYPE c,
      57_value3(35)    TYPE c,
      57_value4(35)    TYPE c,
      57_value5(35)    TYPE c,
***seperate 57C for payments to US
      57c_tag(5)        TYPE c,  "payee's bank
      57c_value1(35)    TYPE c,
      57c_value2(35)    TYPE c,
      57c_value3(35)    TYPE c,
      57c_value4(35)    TYPE c,
      57c_value5(35)    TYPE c,
***
      59_tag(4)        TYPE c,
      59_value1(35)    TYPE c,  "payee's bank account
      59_value2(35)    TYPE c,  "account owner
      59_value3(35)    TYPE c,
      59_value4(35)    TYPE c,
      59_value5(35)    TYPE c,
      70_tag(4)        TYPE c,
      70_value1(35)    TYPE c,
      70_value2(35)    TYPE c,
      70_value3(35)    TYPE c,
      70_value4(35)    TYPE c,
      77b_tag(5)       TYPE c,  "used only for German LZBKZ (text)
      77b_value1(35)   TYPE c,
      77b_value2(35)   TYPE c,
      77b_value3(35)   TYPE c,
      71a_tag(5)       TYPE c,
      71a_value(3)     TYPE c,
      25a_tag(5)       TYPE c,
      25a_value(35)    TYPE c,
      delimiter        TYPE paymsgn2_fpm,
    END OF ls_mt101t.


    data: w_wstr(132) type c,
          w_vpr like YVENDOR_PAYM_REF,
          wa_payd type fpm_payd,
          w_fpayp like fpayp.


* Fill field 21 (Transaction Reference) filled with created payment
* detail text of type '2' (internal reference) line 1
  CLEAR t_payment_details.
  READ TABLE t_payment_details WITH KEY type = '2' line = 1.
  clear w_wstr.
  w_wstr = t_payment_details-text+3(7).
  PERFORM fill_field_reference
          USING    ' '                      "Not used
                   w_wstr   "Transaction Reference
                   ':21:'
          CHANGING ls_mt101t-21_tag
                   ls_mt101t-21_value.
***added for HR-PY by request from M.Spronk of 22/10/2010
  if i_fpayh-dorigin = 'HR-PY'.
    ls_mt101t-21_tag = ':21:'.
    clear ls_mt101t-21_value.
    ls_mt101t-21_value = i_fpayh-doc1r+1(7).
  endif.
***

* Fill field 23E (Instruction Code)
  MOVE-CORRESPONDING i_fpayh TO ls_instparams.
  CONCATENATE i_fpayh-zfax1 i_fpayh-zfax2
              INTO ls_instparams-ztlfx
              SEPARATED BY space.
  CONCATENATE i_fpayh-ztel1 i_fpayh-ztel2
              INTO ls_instparams-ztelf
              SEPARATED BY space.

  PERFORM fill_instruction_fields
          USING    '101'                   "usage MT101
                   i_fpayh-doc1r           "payment document reference
                   ls_instparams           "Instructions + related data
                   i_fpayhx-dtzus          "Instruction: additional info
                   ':23E:'
          CHANGING ls_mt101t-23e_tag1
                   ls_mt101t-23e_value1
                   ls_mt101t-23e_tag2
                   ls_mt101t-23e_value2
                   ls_mt101t-23e_tag3
                   ls_mt101t-23e_value3
                   ls_mt101t-23e_tag4
                   ls_mt101t-23e_value4.

* Fill field 32B (Currency and Transaction Amount)
  PERFORM fill_field_32b
          USING    i_fpayh-waers            "Currency
                   i_fpayh-rwbtr            "Payment amount
          CHANGING ls_mt101t-32b_tag
                   ls_mt101t-32b_value.

* Analyze bankchain
  MOVE-CORRESPONDING: i_fpayh  TO ls_fpayh_bch,
                      i_fpayhx TO ls_fpayhx_bch.
  IF NOT ls_fpayh_bch IS INITIAL.
***    lt_bankchain-bntyp = '2'.                 "request intermediary
***    APPEND lt_bankchain.
***
    lt_bankchain-bntyp = ls_fpayh_bch-btyp1.
    append lt_bankchain.
    lt_bankchain-bntyp = ls_fpayh_bch-btyp2.
    append lt_bankchain.
    lt_bankchain-bntyp = ls_fpayh_bch-btyp3.
    append lt_bankchain.
    delete lt_bankchain where bntyp is initial.
***

    CALL FUNCTION 'FI_BL_BANKCHAIN_ANALYZE'
      EXPORTING
        im_bankchain           = ls_fpayh_bch
        im_bankchain_ext       = ls_fpayhx_bch
      IMPORTING
        ex_numbt1              = li_sendercorr
        ex_numbt2              = li_intermediary
        ex_numbt3              = li_receivercorr
      TABLES
        tb_bankchain           = lt_bankchain
      EXCEPTIONS
        too_many_sender_corr   = 1
        too_many_receiver_corr = 2
        too_many_intermediary  = 3.

    IF NOT sy-subrc IS INITIAL.
      ln_msgno = '318'.
      lc_msgno = ln_msgno.
      CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
        EXPORTING
          i_arbgb = 'BFIBL02'
          i_dtype = 'W'
          i_msgnr = lc_msgno
        IMPORTING
          e_msgty = lc_msgty.

      IF NOT lc_msgty CA '-'.
*     Log: bankchain in file is incomplete
        CONCATENATE
          '0/' li_sendercorr   ','
          '1/' li_intermediary ','           "1 intermediary allowed
          '0/' li_receivercorr
          INTO lc_msgv3.                     "format 0/x,1/y,0/z

        CALL FUNCTION 'ICON_CHECK'
          EXPORTING
            icon_name      = 'ICON_CHECKED'
          IMPORTING
            icon_id        = lc_icon
          EXCEPTIONS
            icon_not_found = 1
            OTHERS         = 2.
        lc_msgv4 = lc_icon.
        CALL FUNCTION 'ICON_CHECK'
          EXPORTING
            icon_name      = 'ICON_FAILURE'
          IMPORTING
            icon_id        = lc_icon
          EXCEPTIONS
            icon_not_found = 1
            OTHERS         = 2.
        CONCATENATE lc_msgv4 lc_icon INTO lc_msgv4.

        CALL FUNCTION 'FI_PAYM_MESSAGE_COLLECT'
          EXPORTING
            i_msgno   = ln_msgno
            I_msgty   = 'W'
            i_msgv1   = i_fpayh-doc1r
            i_msgv2   = i_fpayhx-formi
            i_msgv3   = lc_msgv3
            i_msgv4   = lc_msgv4
            i_collect = 'X'.
      ENDIF.
    ENDIF.


***    READ TABLE lt_bankchain INDEX 1.
***    IF sy-subrc = 0.
***
    loop at lt_bankchain.
***
* Fill field 56 (intermediary bank)
      PERFORM fill_bank_field
              USING    lt_bankchain-bankn     "Bank account number
                       ' '                    "ISO Bank Code Identifier
                       ' '                    "Bank name
                       ' '                    "Bank street
                       ' '                    "Bank location
                       ' '                    "Bank region
                       lt_bankchain-banks     "Bank country
                       lt_bankchain-bankl     "Bank key
                       lt_bankchain-bankl_ext "National Bank identifier
                       lt_bankchain-bcode_ext "Nat. Bank Clearing Code
                       ' '                    "Bank branch
                       '56'                   "Tag of field 56
                       'ACD'                  "Allowed options
                       'X'                    "Read bank data
                       i_fpayh-doc1t          "Application (doc. type)
                       i_fpayh-doc1r          "Reference (doc. number)
              CHANGING ls_mt101t-56_tag
                       ls_mt101t-56_value1
                       ls_mt101t-56_value2
                       ls_mt101t-56_value3
                       ls_mt101t-56_value4
                       ls_mt101t-56_value5.
      PERFORM prepare_string_with_x_chars
              CHANGING:ls_mt101t-56_value2,
                       ls_mt101t-56_value3,
                       ls_mt101t-56_value4,
                       ls_mt101t-56_value5.

***    ENDIF. "intermediary exists
***
    endloop. "lt_bankchain
***
  ENDIF.   "any bankchain there

***
case i_fpayhx-zbiso.
  when 'US'.
***for payments to US
    if i_fpayhx-ubiso <> 'US' and i_fpayh-zswif <> space.
      ls_mt101t-57_tag = ':57A:'.
      ls_mt101t-57_value1 = i_fpayh-zswif.
    endif.
    if not i_fpayhx-zbnkl_ext is initial and i_fpayhx-ubiso = 'US' and i_fpayh-waers = 'USD'.
      ls_mt101t-57c_tag = ':57C:'.
      concatenate '//' i_fpayhx-zbcod_ext i_fpayhx-zbnkl_ext into ls_mt101t-57c_value1.
    endif.
***

***Canada exception is removed 24/02/2015 on request from M.Spronk
*  when 'CA'.
*    ls_mt101t-57c_tag = ':57C:'.
*    concatenate '//CC' i_fpayhx-zbnkl_ext into ls_mt101t-57c_value1.
***
  when others.

***for payments not to US
* Fill field 57a (payee's bank)
  PERFORM fill_bank_field
          USING    ' '                      "Bank account number
                   i_fpayh-zswif            "ISO Bank Code Identifier
                   i_fpayh-zbnka            "Bank name
                   i_fpayh-zbstr            "Bank street
                   i_fpayh-zbort            "Bank location
                   i_fpayh-zbreg            "Bank region
                   i_fpayh-zbnks            "Bank country
                   i_fpayh-zbnky            "Bank key
                   i_fpayhx-zbnkl_ext       "National Bank identifier
                   i_fpayhx-zbcod_ext       "National Bank Clearing Code
                   i_fpayh-zbrch            "Bank branch
                   '57'                     "Tag of field 57
                   'ACD'                    "Allowed options
                   ' '                      "Read bank data
                   i_fpayh-doc1t            "Application (doc. type)
                   i_fpayh-doc1r            "Reference (doc. number)
          CHANGING ls_mt101t-57_tag
                   ls_mt101t-57_value1
                   ls_mt101t-57_value2
                   ls_mt101t-57_value3
                   ls_mt101t-57_value4
                   ls_mt101t-57_value5.

***I_KONAKOV 25/01/2016 - special case for MGA
    if i_fpayh-rzawe = 'X' and i_fpayh-waers = 'MGA' and i_fpayhx-zbiso = 'MG'.
      ls_mt101t-57_tag = ':57D:'.
      ls_mt101t-57_value1 = i_fpayh-zbnka.
      ls_mt101t-57_value2 = i_fpayh-zbstr.
      ls_mt101t-57_value3 = i_fpayh-zbort.
      ls_mt101t-57_value4 = i_fpayh-zbrch.
      ls_mt101t-57_value5 = i_fpayh-zswif.
    endif.
***end of insert 25/01/2016

  PERFORM prepare_string_with_x_chars
          CHANGING:ls_mt101t-57_value2,
                   ls_mt101t-57_value3,
                   ls_mt101t-57_value4,
                   ls_mt101t-57_value5.
endcase. "i_fpayhx-zbiso
***

* Fill field 59 (payee)
***I_KONAKOV 01/10/2014 - account holder for specific payments
  if i_fpayh-rzawe = 'A'.
    clear w_fpayp.
    loop at t_fpayp into w_fpayp where origin = 'TR-CM-BT'.
      i_fpayh-koinh = w_fpayp-sgtxt.
    endloop.
  endif.
***
  PERFORM fill_field_59
          USING    i_fpayhx-zbnkn_ext       "Bank account number
                   i_fpayh-ziban            "Int. bank acct. number IBAN
                   i_fpayh-koinh            "Bank account owner
                   i_fpayh-znme1            "Name 1 of beneficiary
                   i_fpayh-znme2            "Name 2 of beneficiary
                   i_fpayhx-zplor           "Post. code & city of ben.
                   i_fpayhx-zpfst           "Post box/Street of ben.
                   i_fpayhx-zliso           "Country of beneficiary
          CHANGING ls_mt101t-59_tag
                   ls_mt101t-59_value1
                   ls_mt101t-59_value2
                   ls_mt101t-59_value3
                   ls_mt101t-59_value4
                   ls_mt101t-59_value5.
***add bank key and account key to 59_1
  IF NOT gs_swift-xiban IS INITIAL
  AND NOT i_fpayh-ziban IS INITIAL.
   else.
     clear ls_mt101t-59_value1.
     concatenate '/' i_fpayh-zbnkl i_fpayh-zbnkn i_fpayh-zbkon into ls_mt101t-59_value1.
  endif.
***
***only bank account in tag 59 for payments to US or Canada
  if i_fpayhx-zbiso = 'US' or i_fpayhx-zbiso = 'CA'.
     clear ls_mt101t-59_value1.
     concatenate '/' i_fpayh-zbnkn into ls_mt101t-59_value1.
  endif.
***

  PERFORM prepare_string_with_x_chars
          CHANGING:ls_mt101t-59_value2,
                   ls_mt101t-59_value3,
                   ls_mt101t-59_value4,
                   ls_mt101t-59_value5.

* Fill field 70 (Remittance information)
  lt_payd[] = t_payment_details[].
***I_KONAKOV 07/2014 - add vendor reference to note to payee
  clear w_fpayp.
  loop at t_fpayp into w_fpayp.
    clear w_vpr.
*find vendor payment reference for a document
    select single *
                 into w_vpr
                 from YVENDOR_PAYM_REF
                 where bukrs = w_fpayp-doc2r(4)
                   and lifnr = w_fpayp-gpa2r
                   and blart = w_fpayp-vor1r.
*                   and belnr = w_fpayp-doc2r+4(10)
*                   and gjahr = w_fpayp-doc2r+14(4).
*
*    if sy-subrc <> 0. "try to find reference for doc.type
*      select single *
*                   into w_vpr
*                   from YVENDOR_PAYM_REF
*                   where bukrs = w_fpayp-doc2r(4)
*                     and lifnr = w_fpayp-gpa2r
*                     and blart = w_fpayp-vor1r
*                     and belnr = space
*                     and gjahr = '0000'.
*    endif. "sy-subrc

    if w_vpr-VENDOR_PAYM_REF <> space.
      clear wa_payd.
      loop at lt_payd into wa_payd where type = '1'.
        wa_payd-text = w_vpr-VENDOR_PAYM_REF.
        modify lt_payd from wa_payd.
      endloop.
    endif.
  endloop.
***end of add 07/2014
***I_KONAKOV 06/2015 - 'Exotic' currencies for payment method 'X'
  data: w_preason like YDET_R_PAYM-reason,
        w_xblnr like fpayp-xblnr.
  if i_fpayh-rzawe = 'X'.
    clear w_fpayp.
    loop at t_fpayp into w_fpayp.
      clear w_preason.
      select single REASON into w_preason
                           from YDET_R_PAYM
                           where blart = w_fpayp-vor1r.
      w_xblnr = w_fpayp-xblnr.
    endloop. "t_fpayp
    clear wa_payd.
    read table lt_payd index 1 into wa_payd.
*    concatenate 'EXO//' w_preason '//' w_xblnr '//' into wa_payd-text.
    concatenate 'EXO//' w_preason into wa_payd-text.
    concatenate wa_payd-text w_xblnr into wa_payd-text separated by space.
    concatenate wa_payd-text '//' into wa_payd-text.
    modify lt_payd index 1 from wa_payd.
  endif. "i_fpayh-rzawe
***end of insert 06/2015
  PERFORM fill_field_70
          USING    lt_payd[]                "Table of payment details
          CHANGING ls_mt101t-70_tag
                   ls_mt101t-70_value1
                   ls_mt101t-70_value2
                   ls_mt101t-70_value3
                   ls_mt101t-70_value4.
  PERFORM prepare_string_with_x_chars
          CHANGING:ls_mt101t-70_value1,
                   ls_mt101t-70_value2,
                   ls_mt101t-70_value3,
                   ls_mt101t-70_value4.

* Fill field 77B (Regulatory Reporting)
***I_KONAKOV - other rules for 77B
***  PERFORM fill_field_77b
***          USING    t_fpayp[]                "Payed items
***                   i_fpayh-doc1t            "Application (doc. type)
***                   i_fpayh-doc1r            "Reference (doc. number)
***                   'MT101'                  "DME format
***          CHANGING ls_mt101t-77b_tag
***                   ls_mt101t-77b_value1
***                   ls_mt101t-77b_value2
***                   ls_mt101t-77b_value3.
  ls_mt101t-77b_tag = ':77B:'.
  ls_mt101t-77b_value1 = '/ORDERRES/FR'.
  concatenate '/BENEFRES/' i_fpayh-zland(2) into ls_mt101t-77b_value2.

* Fill field 33B (Currency and Original Ordered Amount)
* => not supported yet

* Fill field 71A (Details of charges)
  PERFORM fill_field_71a
          USING    i_fpayhx-dtkvs           "Key of bank charges
          CHANGING ls_mt101t-71a_tag
                   ls_mt101t-71a_value.

* Fill field 25A (Charges account, if different from 50H_1)
* (MT101 only)
  IF  ( NOT i_fpayhx-dtgbk IS INITIAL )     "charges account
  AND ( i_fpayhx-dtgbk NE i_fpayhx-ubknt )  "different from tx account
  AND ( i_fpayhx-dtgbk NE i_fpayhx-ubknt_ext )

  AND ( i_fpayhx-dtglz IS INITIAL           "is an account with the
     OR i_fpayhx-dtglz EQ i_fpayhx-ubnkl    "servicing house bank
     OR i_fpayhx-dtglz EQ i_fpayhx-ubnkl_ext
     OR i_fpayhx-dtglz EQ i_fpayhx-uswif ).

    ls_mt101t-25a_tag   = ':25A:'.
    CONCATENATE '/' i_fpayhx-dtgbk INTO ls_mt101t-25a_value.
  ENDIF.

* Fill field 36 (Exchange Rate)
* => not supported yet


*------------------ transaction record complete -----------------------

  IF NOT gs_swift-paymsgn2 IS INITIAL.
* Delimiter at end of transaction record
    ls_mt101t-delimiter = gs_swift-paymsgn2.
  ENDIF.

***suppress spec. characters from data
***  replace all occurrences of ';' in ls_mt101t with ' '.
***  replace all occurrences of '''' in ls_mt101t with ' '.
  translate ls_mt101t using '; '.
  translate ls_mt101t using ''' '.
***

* Collect fields into output table
  PERFORM fill_output_table
          USING    ls_mt101t                "Formate structure
          CHANGING t_file_output[].         "Output table

ENDFUNCTION.