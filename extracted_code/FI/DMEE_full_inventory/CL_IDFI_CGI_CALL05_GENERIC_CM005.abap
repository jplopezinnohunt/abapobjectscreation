METHOD generic_call.
* In this method we call Generic Functionality to change Reference
* fields in structure FPAYHX and table FPAYP for DMEE(x) transaction in
* function module FI_PAYMEDIUM_DMEE_CGI_05.

* This functionality is always called and changes done here cannot be
* replaced

    DATA:
      lv_area                        TYPE string,
      lv_code                        TYPE string,
      lv_not_found                   TYPE boole_d,
      lv_tabix                       TYPE sy-tabix,
      lv_xbelnr                      TYPE bsec-belnr,
      lv_xbukrs                      TYPE bsec-bukrs,
      lv_xbuzei                      TYPE bsec-buzei,
      lv_xgjahr                      TYPE bsec-gjahr,
      lv_is_internal_bank            TYPE boole_d,
      lv_param_dummy                 TYPE dmee_tree_type-if_param,
      lv_uparam_dummy                TYPE dmee_tree_head-param_struc,
      lv_waers                       TYPE isocd,
      lv_po_city                     TYPE string,
      lv_city                        TYPE string,
      lv_instr_id                    TYPE string,
      lv_tax_method                  TYPE witht,
      lv_tax_ctnumber                TYPE ctnumber,
      lv_tax_category                TYPE wt_withcd,
      lv_tax_ctgry_dtls              TYPE text40,
      lv_tax_forms_code              TYPE qsrec,
      lv_tax_amt_rate                TYPE wt_qsatz,
      lv_tax_amt_in_loc_curr         TYPE wt_wt,
      lv_tax_amt_sum                 TYPE wt_wt,
      lv_tax_amt_sum_conv(1500)      TYPE c,
      lv_tax_base_amt_in_loc_curr    TYPE wt_bs,
      lv_tax_base_amt_sum            TYPE wt_bs,
      lv_tax_base_amt_sum_conv(1500) TYPE c,
      lv_tax_amt_abs                 TYPE wt_bs,
      lv_tax_amt_abs_conv(1500)      TYPE c,
      lv_cgiid                       TYPE string,
      lv_cgiir                       TYPE string,
      lv_cgiprt                      TYPE string,
      lv_cgicd                       TYPE string,
      lv_street_house_no             TYPE string,
      lv_house_no                    TYPE string,
      ls_fpayp_tmp                   TYPE fpayp,
      ls_format_params               TYPE fpm_cgi,
      ls_adrc_tmp                    TYPE adrc,
      ls_fpayhx                      TYPE fpayhx,
      ls_t015l                       TYPE t015l_d_bf,
      ls_dmee_item_tmp               TYPE dmee_paym_if_type,
      ls_extension                   TYPE dmee_exit_interface_aba,
      ls_adrc                        TYPE adrc,
      ls_fpayp                       TYPE fpayp,
      ls_xbsec                       TYPE bsec,
      ls_t045t                       TYPE t045t,
      lt_dmee_tab_tmp                TYPE TABLE OF          dmee_tree_type-if_tab,
      lt_fpayp                       TYPE STANDARD TABLE OF fpayp,
      lt_adrc                        TYPE TABLE OF adrc,
      flt_val_country                TYPE intca.

  CONSTANTS:
      lc_sender_code  TYPE fieldname VALUE 'SND_CTRY_CODE'. "n3108984

    FIELD-SYMBOLS:
  <fs_fpayp>       TYPE fpayp,
  <fs_sender_code> TYPE any.      "n3108984

  lt_fpayp = ct_fpayp_fref[].

* Read the first line for the selections                    "n2942194
    READ TABLE ct_fpayp_fref INTO ls_fpayp_tmp INDEX 1.

*     Get CGI parameters                                    "n2699168
  ls_format_params = cl_idfi_cgi_dmee_utils=>get_format_parameters( ).

* ----------------------------------------------------------------------------------------------------
* FPAYHX-REF01:
* ----------------------------------------------------------------------------------------------------
*      0              60               80               90              100             110       116
* Dbtr_Street  +  Debt_Building  + Debt_Post_Cd  + Debt_Region  +  Debt_House_No  +  Btch Book
* ----------------------------------------------------------------------------------------------------
* ----------------------------------------------------------------------------------------------------
* FPAYHX-REF06:
* ----------------------------------------------------------------------------------------------------
*      0              40
* Debt_city     +
* ----------------------------------------------------------------------------------------------------

  ls_adrc = cl_idfi_cgi_dmee_utils=>get_company_address(
  iv_bukrs = is_fpayh-zbukr iv_nation = ls_format_params-nation ).

  IF NOT ( ls_adrc IS INITIAL ).
    cs_fpayhx_fref-ref01+0(60)   = ls_adrc-street.
    cs_fpayhx_fref-ref01+60(20)  = ls_adrc-building.
    cs_fpayhx_fref-ref01+80(10)  = ls_adrc-post_code1.
    cs_fpayhx_fref-ref01+90(10)  = ls_adrc-region.
    cs_fpayhx_fref-ref01+100(10) = ls_adrc-house_num1.
    cs_fpayhx_fref-ref06+0(40)   = ls_adrc-city1.

    READ TABLE lt_fpayp INTO ls_fpayp INDEX 1.

    IF is_fpayh-zbukr NE ls_fpayp-bukrs.
      CLEAR ls_adrc.

      ls_adrc = cl_idfi_cgi_dmee_utils=>get_company_address(
      iv_bukrs = ls_fpayp-bukrs iv_nation = ls_format_params-nation ).
    ENDIF.
    LOOP AT lt_fpayp ASSIGNING <fs_fpayp>.
      <fs_fpayp>-ref01+0(60)   = ls_adrc-street.
      <fs_fpayp>-ref01+60(20)  = ls_adrc-building.
      <fs_fpayp>-ref01+80(10)  = ls_adrc-post_code1.
      <fs_fpayp>-ref01+90(10)  = ls_adrc-region.
      <fs_fpayp>-ref01+100(10) = ls_adrc-house_num1.
      lv_tabix = sy-tabix.
    ENDLOOP.

    ct_fpayp_fref[] = lt_fpayp.

  ENDIF.

  IF cs_fpayhx_fref-ref06+0(40) IS INITIAL.
    cs_fpayhx_fref-ref06+0(40) = is_fpayhx-ort1z.
  ENDIF.

  IF ls_format_params-batch_booking IS NOT INITIAL.               "n3108984
    cs_fpayhx_fref-ref01+110(6) = ls_format_params-batch_booking.
  ENDIF.

* -------------------------------------------------------------------------------
* FPAYHX-REF02:
* -------------------------------------------------------------------------------
*      0              10              20               80         90
* Cdrt_POBox  +  Cdtr_House_No  + Cdtr_Street  + Cdtr_Post_Cd
* -------------------------------------------------------------------------------
*Get Vendor details.
*check for the One time Vendor..for One time Vendor/CPD vendor there would not any address number..
*For one time vendor/CPD vendor the value of FPAYH-GPA1T would be always 14....
  CLEAR: ls_adrc.                                           "n2942194
  IF is_fpayh-zadnr IS INITIAL OR is_fpayh-gpa1t = '14'.    "n2800089 n3108984
    lv_xbelnr = ls_fpayp_tmp-doc2r+4(10).                   "n2942194
    lv_xbukrs = ls_fpayp_tmp-doc2r(4).
    lv_xbuzei = '001'.
    lv_xgjahr = ls_fpayp_tmp-doc2r+14(4).

    CALL FUNCTION 'READ_BSEC'
    EXPORTING
      xbelnr         = lv_xbelnr
      xbukrs         = lv_xbukrs
      xbuzei         = lv_xbuzei
      xgjahr         = lv_xgjahr
    IMPORTING
      xbsec          = ls_xbsec
    EXCEPTIONS
      key_incomplete = 1
      not_authorized = 2
      not_found      = 3
      OTHERS         = 4.

    IF sy-subrc EQ 0.
      IF ls_xbsec IS NOT INITIAL .
        cs_fpayhx_fref-ref02+0(10) =  ls_xbsec-pstl2.
        cs_fpayhx_fref-ref02+80(10) = ls_xbsec-pstlz.        "n2942194
        lv_street_house_no          = ls_xbsec-stras.        "n3043741

        "BSEC-STRAS contains street + house number, we need to split it
        CALL METHOD cl_idfi_cgi_dmee_utils=>split_street_house_no
        EXPORTING
        iv_street_house_no = lv_street_house_no
        IMPORTING
        ev_street          = cs_fpayhx_fref-ref02+20(60)
        ev_house_no        = cs_fpayhx_fref-ref02+10(10).    "n3043741
      ENDIF.
    ELSE.                       "backup to derive house no    n3043741
      lv_street_house_no = is_fpayh-zstra.
      CALL METHOD cl_idfi_cgi_dmee_utils=>split_street_house_no
        EXPORTING
        iv_street_house_no = lv_street_house_no
        IMPORTING
        ev_street          = cs_fpayhx_fref-ref02+20(60)
        ev_house_no        = cs_fpayhx_fref-ref02+10(10).    "n3043741
    ENDIF.
  ELSE.

    CALL FUNCTION 'ADDR_SELECT_ADRC_SINGLE'                 "n2942194
      EXPORTING
        addrnumber             = is_fpayh-zadnr
     TABLES
       et_adrc                 = lt_adrc
     EXCEPTIONS
       OTHERS                  = 99.
    IF sy-subrc = 0.

      DELETE lt_adrc WHERE nation NE ls_format_params-nation.
      SORT lt_adrc BY date_from DESCENDING.
      READ TABLE lt_adrc INTO ls_adrc INDEX 1.

    ENDIF.


    IF NOT ( ls_adrc IS INITIAL ).
      cs_fpayhx_fref-ref02+0(10)  = ls_adrc-post_code2.
      cs_fpayhx_fref-ref02+10(10) = ls_adrc-house_num1.
      cs_fpayhx_fref-ref02+80(10) = ls_adrc-post_code1.
      IF cs_fpayhx_fref-ref02+80(10) IS INITIAL.
        cs_fpayhx_fref-ref02+80(10) = is_fpayh-zpstl.
      ENDIF.
      cs_fpayhx_fref-ref02+20(60) = ls_adrc-street.       "n3043741
    ENDIF.

  ENDIF.

  IF cs_fpayhx_fref-ref02+20(60) IS NOT INITIAL AND       "n3108984
     ls_format_params-nation IS INITIAL.
     CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
        EXPORTING
          intext  = cs_fpayhx_fref-ref02+20(60)
        IMPORTING
          outtext = cs_fpayhx_fref-ref02+20(60).
  ENDIF.

  IF cs_fpayhx_fref-ref02+80(10) IS INITIAL.              "n2942194
    cs_fpayhx_fref-ref02+80(10) = is_fpayh-zpstl.
  ENDIF.

  CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_street   "n2942194
        EXPORTING
          iv_doc2r   = ls_fpayp_tmp-doc2r
          iv_gpa1t   = is_fpayh-gpa1t
          iv_nation  = ls_format_params-nation
          iv_dorigin = is_fpayh-dorigin
          iv_doc2t   = ls_fpayp_tmp-doc2t
          iv_zstra   = is_fpayh-zstra
          iv_zadnr   = is_fpayh-zadnr
          iv_zpfac   = is_fpayh-zpfac
          iv_spras   = is_fpayh-zspra                       "n3310863
        RECEIVING
          rv_result  = cs_fpayhx_fref-ref09+70(60).         "n3043741

  cs_fpayhx_fref-ref11(60) = cs_fpayhx_fref-ref09+70(60). "n2942194


  CLEAR: ls_adrc.                                           "n2942194
* -------------------------------------------------------------------------------
* FPAYHX-REF03:
* -------------------------------------------------------------------------------
*      0              1
*  Is_SEPA  +
* -------------------------------------------------------------------------------
*  Check if SEPA payment.
*  SEPA payments with swift code:
  IF cl_idfi_cgi_dmee_utils=>is_sepa_payment( is_fpayh   = is_fpayh
  is_fpayhx  = is_fpayhx
  ) EQ abap_true.
    cs_fpayhx_fref-ref03 = 'S'.        "If SEPA payment
  ELSE.
    cs_fpayhx_fref-ref03 = 'N'.        "If not SEPA payment
  ENDIF.

* -------------------------------------------------------------------------------
* FPAYHX-REF04:
* -------------------------------------------------------------------------------
*      0           25
*  User ID  +
* -------------------------------------------------------------------------------
*Get Member Bank Identification.
  SELECT SINGLE * FROM  t045t INTO ls_t045t "#EC CI_NOORDER
  WHERE  bukrs EQ is_fpayh-zbukr
  AND   zlsch EQ is_fpayh-rzawe
  AND   hbkid EQ is_fpayh-hbkid
  AND   hktid EQ is_fpayh-hktid.

  IF sy-subrc EQ 0.
    cs_fpayhx_fref-ref04 = ls_t045t-dtaid.
  ENDIF.

* -------------------------------------------------------------------------------
* FPAYHX-REF05:
* -------------------------------------------------------------------------------
*      0                 4
*  Purp_Cd/Inst1,2  +
* -------------------------------------------------------------------------------
* Additional sort criteria
  IF is_fpayh-dorigin EQ 'HR-PY'.
    cs_fpayhx_fref-ref05 = is_fpayh-purp_code.
  ELSE.
    CONCATENATE is_fpayh-dtws1 is_fpayh-dtws2 INTO cs_fpayhx_fref-ref05.
  ENDIF.
* -------------------------------------------------------------------------------
* FPAYHX-REF07:
* -------------------------------------------------------------------------------
*      110              115
*  Clear_Code    +
* -------------------------------------------------------------------------------
* Check Clearing System ID (ISO External Code List)
  CALL FUNCTION 'GET_BANKCODE'
  EXPORTING
    i_banks = is_fpayh-zbnks
    i_bankl = is_fpayh-zbnkl
  IMPORTING
    e_ecsic = cs_fpayhx_fref-ref07+110(5).

* ---------------------------------------------------------------------
* FPAYHX-REF11:                                                n2768124
* ---------------------------------------------------------------------
*        0                 60             100
* GET_CRDT_STREET  +  GET_CRED_CITY  +
* ---------------------------------------------------------------------

* GET_CREDITOR_STREET        CT  <PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><AdrLine1>
*                            DD  <PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><AdrLine1>
                                                            "#EC NOTEXT
*      CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_street
*        EXPORTING
*          iv_doc2r   = ls_fpayp_tmp-doc2r
*          iv_gpa1t   = is_fpayh-gpa1t
*          iv_nation  = ls_format_params-nation
*          iv_dorigin = is_fpayh-dorigin
*          iv_doc2t   = ls_fpayp_tmp-doc2t
*          iv_zstra   = is_fpayh-zstra
*          iv_zadnr   = is_fpayh-zadnr
*          iv_zpfac   = is_fpayh-zpfac
*        RECEIVING
*          rv_result  = cs_fpayhx_fref-ref11(60).   " SEE REF02+20(60) n2942194

* GET_CREDITOR_CITY        CT  <PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><AdrLine2>
*                          DD  <PmtInf><DrctDbtTxInf><Dbtr><PstlAdr><AdrLine2>
                                                            "#EC NOTEXT
    CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_city
      EXPORTING
        iv_doc2r   = ls_fpayp_tmp-doc2r
        iv_gpa1t   = is_fpayh-gpa1t
        iv_nation  = ls_format_params-nation
        iv_dorigin = is_fpayh-dorigin
        iv_doc2t   = ls_fpayp_tmp-doc2t
        iv_zort1   = is_fpayh-zort1
        iv_zadnr   = is_fpayh-zadnr
      RECEIVING
        rv_result  = cs_fpayhx_fref-ref11+60(40).

* Only for DMEE eXtended Transactions
  CHECK mv_is_dmeex_tree IS NOT INITIAL.

* ---------------------------------------------------------------------
* START OF DMEE without EXIT
* ---------------------------------------------------------------------
* new fiori app processing requires logging of non-persistent info

    ls_dmee_item_tmp-fpayh   = is_fpayh.
    ls_dmee_item_tmp-fpayhx  = is_fpayhx.
    ls_dmee_item_tmp-fpayp   = ls_fpayp_tmp.

* Values for Amount Conversion
    ls_extension-node_values-length = 20.
    ls_extension-node-tree_type     = 'PAYM'.               "#EC NOTEXT
    ls_extension-node-tree_id       = is_fpayhx-formi.
    ls_extension-node-version       = 000.
    ls_extension-node-cv_rule       = 'AL.='.               "#EC NOTEXT
    ls_extension-node-length        = 20.

* Get Parameter Values Based on Company Code and Party Name
    CALL METHOD cl_idfi_cgi_dmee_utils=>get_cgi_xml_values
      EXPORTING
        iv_bukrs  = ls_fpayp_tmp-bukrs
        iv_zbukr  = is_fpayh-zbukr
      IMPORTING
        ev_cgiid  = lv_cgiid
        ev_cgiir  = lv_cgiir
        ev_cgiprt = lv_cgiprt
        ev_cgicd  = lv_cgicd.                               "n2893975

* Get CGI parameters
    ls_format_params = cl_idfi_cgi_dmee_utils=>get_format_parameters( ).

* ---------------------------------------------------------------------
* FPAYHX-REF06:
* ----------------------------------------------------------------------------------------------
*     0         40          75           79         83          87             91         92
* OLD_LOG + EXIT_SEPA + SRV_LVL_CD + CTG_PRP_CD + CHCK_TP + CHCK_DEL_MTH + IS_INT_BNK + EXIT_SEPA
* ----------------------------------------------------------------------------------------------

* DMEE_EXIT_SEPA_21 , 31 ,         CT + DD  <PmtInf><PmtInfId>
*   Following code is moved at the end of the FILL_FPAY_FREF method because it coudl incorectly
*   determine end of a batch as at this time are no REFxx fields filled
*   only a placeholder is set
    cs_fpayhx_fref-ref06+40(35) = '******************************'. "#EC NOTEXT
*    ls_fpayhx = is_fpayhx.
*    TRY .
*      CALL METHOD cl_idfi_cgi_dmee_utils=>('GET_DMEE_BATCHES') "#EC NOTEXT
*        EXPORTING
*          is_fpayh     = is_fpayh
*          iv_paymedium = iv_paymedium
*        CHANGING
*          cs_fpayhx    = ls_fpayhx
*          ct_fpayp     = ct_fpayp_fref
*        RECEIVING
*          rv_batch_id  = cs_fpayhx_fref-ref06+40(35).
*    CATCH cx_sy_dyn_call_illegal_method.
*      CLEAR cs_fpayhx_fref-ref06+40(35).
*    ENDTRY.

* SERVICE_LEVEL_CODE            CT + DD <PmtInf><PmtTpInf><SvcLvl><Cd>
*                               CT  <PmtInf><CdtTrfTxInf><PmtTpInf><SvcLvl><Cd>
*                               DD  <PmtInf><DrctDbtTxInf><PmtTpInf><SvcLvl><Cd>
    CALL METHOD cl_idfi_cgi_dmee_utils=>get_area
      EXPORTING
        is_fpayh = is_fpayh
      IMPORTING
        ev_area  = lv_area.

    IF is_fpayhx-xschk NE abap_true.
*   Only for non-cheque payments
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_service_level_code
        EXPORTING
          is_fpayh     = is_fpayh
          iv_area      = lv_area
        IMPORTING
          ev_code      = lv_code
          ev_not_found = lv_not_found.

      IF lv_not_found IS NOT INITIAL OR lv_code IS INITIAL.
        IF cs_fpayhx_fref-ref03 EQ 'S'.                     "#EC NOTEXT
          cs_fpayhx_fref-ref06+75(4) = 'SEPA'.              "#EC NOTEXT
        ENDIF.
      ELSE.
        cs_fpayhx_fref-ref06+75(4)   = lv_code.
      ENDIF. "IF lv_not_found IS NOT INITIAL OR lv_code IS INITIAL.

* CATEGORY_PURPOSE_CODE         CT + DD <PmtInf><PmtTpInf><CtgyPurp><Cd>
*                               CT  <PmtInf><CdtTrfTxInf><PmtTpInf><CtgyPurp><Cd>
*                               DD  <PmtInf><DrctDbtTxInf><PmtTpInf><CtgyPurp><Cd>
      IF is_fpayh-dorigin EQ 'HR-PY'.                       "#EC NOTEXT
        cs_fpayhx_fref-ref06+79(4) = is_fpayh-purp_code.
      ELSE.
        CALL METHOD cl_idfi_cgi_dmee_utils=>get_category_purpose_code
          EXPORTING
            is_fpayh     = is_fpayh
            iv_area      = lv_area
          IMPORTING
            ev_code      = lv_code
            ev_not_found = lv_not_found.

        cs_fpayhx_fref-ref06+79(4) = lv_code.
      ENDIF. "IF is_fpayh-dorigin EQ 'HR-PY'.

    ELSE.
*   Only for cheque payments
* CHECK TYPE                        CT   <PmtInf><CdtTrfTxInf><ChqInstr><ChqTp>
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_check_type
        EXPORTING
          is_fpayh     = is_fpayh
          iv_area      = lv_area
        IMPORTING
          ev_code      = lv_code
          ev_not_found = lv_not_found.

      cs_fpayhx_fref-ref06+83(4) = lv_code.

* CHECK DELIVERY METH               CT  <PmtInf><CdtTrfTxInf><ChqInstr><DlvryMtd><Cd>
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_check_delivery_method
        EXPORTING
          is_fpayh     = is_fpayh
          iv_area      = lv_area
        IMPORTING
          ev_code      = lv_code
          ev_not_found = lv_not_found.

      cs_fpayhx_fref-ref06+87(4) = lv_code.
    ENDIF. " IF is_fpayhx-xschk NE abap_true.

* IS_INTERNAL_BANK                      CT  <PmtInf><CdtTrfTxInf><-CdtrAgt>
    CALL METHOD cl_idfi_cgi_dmee_utils=>is_internal_bank
      EXPORTING
        iv_zbnks  = is_fpayh-zbnks
        iv_ziban  = is_fpayh-ziban
        iv_zswift = is_fpayh-zswif
        iv_zbnkl  = is_fpayh-zbnkl
      RECEIVING
        rv_result = lv_is_internal_bank.

    IF lv_is_internal_bank EQ abap_true OR is_fpayhx-xschk EQ abap_true.
      cs_fpayhx_fref-ref06+91(1) = abap_true.
    ENDIF. "IF lv_is_internal_bank EQ abap_true OR is_fpayhx-xschk EQ abap_true.

* DMEE_EXIT_SEPA_GET_INSTRID            CT  <PmtInf><CdtTrfTxInf><PmtId><InstrId>
*                                       DD  <PmtInf><DrctDbtTxInf><PmtId><InstrId>
    CALL FUNCTION 'DMEE_EXIT_SEPA_GET_INSTRID'
      EXPORTING
        i_tree_type = 'PAYM'
        i_tree_id   = is_fpayhx-formi
        i_item      = ls_dmee_item_tmp
        i_param     = lv_param_dummy
        i_uparam    = lv_uparam_dummy
      IMPORTING
        c_value     = lv_instr_id
      TABLES
        i_tab       = lt_dmee_tab_tmp.

    cs_fpayhx_fref-ref06+92(30) = lv_instr_id.

* ---------------------------------------------------------------------
* FPAYHX-REF07:
* ---------------------------------------------------------------------
*       0             70            90            110            115
* DEBITOR_NAME  +  AMT_SUM  +  AMT_BASE_SUM +  DISPLAY_AMT  +
* ---------------------------------------------------------------------

* DEBITOR_NAME               CT  <PmtInf><Dbtr><Nm>
*                            DD  <PmtInf><Cdtr><Nm>
    IF is_fpayhx-aust1 IS NOT INITIAL AND ls_format_params-nation IS INITIAL.
      CONCATENATE is_fpayhx-aust1 is_fpayhx-aust2
             INTO cs_fpayhx_fref-ref07(70) SEPARATED BY space.
    ELSE.
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_debitor_name
        EXPORTING
          iv_nation = ls_format_params-nation
          is_fpayhx = is_fpayhx
          iv_zbukr  = is_fpayh-zbukr
        RECEIVING
          rv_result = cs_fpayhx_fref-ref07(70).
    ENDIF. "IF is_fpayhx-aust1 IS NOT INITIAL AND ls_format_params-nation IS INITIAL.

* GET TAX INFO           CT   <PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TtlAmt>
*                        CT   <PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>
*                        DD   <PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><TtlAmt>
*                        DD   <PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>
    lv_waers = is_fpayhx-hwiso.                               "n3043741

  LOOP AT ct_fpayp_fref TRANSPORTING NO FIELDS WHERE qsteu IS NOT INITIAL.
    ENDLOOP.
  IF sy-subrc EQ 0.
    LOOP AT ct_fpayp_fref ASSIGNING <fs_fpayp>.

      IF lv_area NE cl_idfi_cgi_dmee_utils=>gc_fi.
*       skip for FI-CA
        EXIT.
      ENDIF.

      IF <fs_fpayp>-qsteu IS INITIAL.
        CALL METHOD cl_idfi_cgi_dmee_utils=>convert "Also 0 needs to be provided  n3108984
          EXPORTING
            iv_p_value   = lv_tax_amt_abs
            iv_currency  = lv_waers
            is_extension = ls_extension
            iv_nation    = ls_format_params-nation
          CHANGING
            cv_o_value   = lv_tax_amt_abs_conv.

        <fs_fpayp>-ref02+90(20)  = lv_tax_amt_abs_conv.
        CLEAR: lv_tax_amt_abs_conv.                             "n3108984
        CONTINUE.
      ENDIF.

      CALL METHOD cl_idfi_cgi_dmee_utils=>get_tax_info
        EXPORTING
          iv_doc2r                    = <fs_fpayp>-doc2r
          iv_zland                    = is_fpayh-zland
          iv_spras                    = is_fpayh-zspra
        IMPORTING
          ev_tax_method               = lv_tax_method
          ev_tax_ctnumber             = lv_tax_ctnumber
          ev_tax_category             = lv_tax_category
          ev_tax_ctgry_dtls           = lv_tax_ctgry_dtls
          ev_tax_forms_code           = lv_tax_forms_code
          ev_tax_amt_rate             = lv_tax_amt_rate
          ev_tax_amt_in_loc_curr      = lv_tax_amt_in_loc_curr
          ev_tax_base_amt_in_loc_curr = lv_tax_base_amt_in_loc_curr.

      <fs_fpayp>-ref02(10)     = lv_tax_method.                "   CT  <PmtInf><CdtTrfTxInf><Tax><Mtd>
      "   DD  <PmtInf><DrctDbtTxInf><Tax><Mtd>
      <fs_fpayp>-ref02+10(10)  = lv_tax_ctnumber.              "   CT  <PmtInf><CdtTrfTxInf><Tax><SeqNb>
      "   DD  <PmtInf><DrctDbtTxInf><Tax><SeqNb>

      <fs_fpayp>-ref02+20(10)  = lv_tax_category.              "   CT  <PmtInf><CdtTrfTxInf><Tax><Rcrd><Ctgy>
      "   DD  <PmtInf><DrctDbtTxInf><Tax><Rcrd><Ctgy>

      <fs_fpayp>-ref02+30(40)  = lv_tax_ctgry_dtls.            "   CT  <PmtInf><CdtTrfTxInf><Tax><Rcrd><CtgyDtls>
      "   DD  <PmtInf><DrctDbtTxInf><Tax><Rcrd><CtgyDtls>

      <fs_fpayp>-ref02+70(10)  = lv_tax_forms_code.            "   CT  <PmtInf><CdtTrfTxInf><Tax><Rcrd><FrmsCd>
      "   DD  <PmtInf><DrctDbtTxInf><Tax><Rcrd><FrmsCd>

      IF lv_tax_amt_rate IS NOT INITIAL.
        <fs_fpayp>-ref02+80(10) = lv_tax_amt_rate.             "   CT  <PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><Rate>
        "   DD  <PmtInf><DrctDbtTxInf><Tax><Rcrd><TaxAmt><Rate>
      ENDIF.

      lv_tax_amt_abs = abs( <fs_fpayp>-qsteu ).     "for Amount absolute value needed   "2533796

*     Get Amount with Currency (Using Spell_Amount)
      CALL METHOD cl_idfi_cgi_dmee_utils=>amount_with_curr    "n2600590
        EXPORTING
          iv_p_value  = lv_tax_amt_abs
          iv_currency = lv_waers
        IMPORTING
          ev_p_value  = lv_tax_amt_abs.

      CALL METHOD cl_idfi_cgi_dmee_utils=>convert
        EXPORTING
          iv_p_value   = lv_tax_amt_abs
          iv_currency  = lv_waers
          is_extension = ls_extension
          iv_nation    = ls_format_params-nation
        CHANGING
          cv_o_value   = lv_tax_amt_abs_conv.

      <fs_fpayp>-ref02+90(20)  = lv_tax_amt_abs_conv.
      CLEAR: lv_tax_amt_abs_conv.                             "n3108984
      "   CT  <PmtInf><CdtTrfTxInf><RmtInf><Strd><RfrdDocAmt><AdjstmntAmtAndRsn><Amt>
      lv_tax_amt_sum      = lv_tax_amt_sum      + lv_tax_amt_in_loc_curr.
      lv_tax_base_amt_sum = lv_tax_base_amt_sum + lv_tax_base_amt_in_loc_curr.                    "n2960399

    ENDLOOP. "LOOP AT lt_fpayp ASSIGNING <fs_fpayp>.

*   Get Amount with Currency (Using Spell_Amount)
    CALL METHOD cl_idfi_cgi_dmee_utils=>amount_with_curr      "n2600590
      EXPORTING
        iv_p_value  = lv_tax_amt_sum
        iv_currency = lv_waers
      IMPORTING
        ev_p_value  = lv_tax_amt_sum.

    CALL METHOD cl_idfi_cgi_dmee_utils=>convert
      EXPORTING
        iv_p_value   = lv_tax_amt_sum
        iv_currency  = lv_waers
        is_extension = ls_extension
        iv_nation    = ls_format_params-nation
      CHANGING
        cv_o_value   = lv_tax_amt_sum_conv.

*   Get Amount with Currency (Using Spell_Amount)
    CALL METHOD cl_idfi_cgi_dmee_utils=>amount_with_curr      "n2600590
      EXPORTING
        iv_p_value  = lv_tax_base_amt_sum
        iv_currency = lv_waers
      IMPORTING
        ev_p_value  = lv_tax_base_amt_sum.

    CALL METHOD cl_idfi_cgi_dmee_utils=>convert
      EXPORTING
        iv_p_value   = lv_tax_base_amt_sum
        iv_currency  = lv_waers
        is_extension = ls_extension
        iv_nation    = ls_format_params-nation
      CHANGING
        cv_o_value   = lv_tax_base_amt_sum_conv.

    cs_fpayhx_fref-ref07+70(20) = lv_tax_amt_sum_conv.                   "<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxAmt>
    cs_fpayhx_fref-ref07+90(20) = lv_tax_base_amt_sum_conv.              "<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>
  ELSE.
    CALL METHOD cl_idfi_cgi_dmee_utils=>convert               "n3043741
        EXPORTING
          iv_p_value   = lv_tax_amt_abs
          iv_currency  = lv_waers
          is_extension = ls_extension
          iv_nation    = ls_format_params-nation
        CHANGING
          cv_o_value   = lv_tax_amt_abs_conv.

    cs_fpayhx_fref-ref07+70(20) = lv_tax_amt_abs_conv.                   "<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxAmt>
    cs_fpayhx_fref-ref07+90(20) = lv_tax_amt_abs_conv.                   "<PmtInf><CdtTrfTxInf><Tax><Rcrd><TaxAmt><TaxblBaseAmt>

    LOOP AT ct_fpayp_fref ASSIGNING <fs_fpayp>.               "n3108984
      <fs_fpayp>-ref02+90(20)  = lv_tax_amt_abs_conv.
    ENDLOOP.
  ENDIF.

* ---------------------------------------------------------------------
* FPAYHX-REF08:
* ---------------------------------------------------------------------
*    0          60          70          80          120        125
* STREET  + HOUSE_NUM  + POST_CODE +   CITY    +  REGION  +  COUNTRY
* ---------------------------------------------------------------------

* ADDRESS CONVERSION          CT  <PmtInf><CdtTrfTxInf><UltmtCdtr><PstlAdr>StrtNm>
*                             DD  <PmtInf><DrctDbtTxInf><UltmtDbtr><PstlAdr><StrtNm>
    IF is_fpayhx-ubiso IS NOT INITIAL.
      flt_val_country = is_fpayhx-ubiso.
    ELSE.
      flt_val_country = is_fpayhx-ubnks.
    ENDIF. "IF is_fpayhx-ubiso IS NOT INITIAL.

    CALL METHOD cl_dmee_paym_ut=>adrc_convert_to_adrlines
      EXPORTING
        iv_addrnum      = ls_fpayp_tmp-adrnr
        iv_nation       = ls_format_params-nation
        iv_bank_country = flt_val_country
      IMPORTING
        es_adrc         = ls_adrc_tmp.

    cs_fpayhx_fref-ref08(60) = ls_adrc_tmp-street.

    IF ls_adrc_tmp-house_num1 IS NOT INITIAL.
      cs_fpayhx_fref-ref08+60(10) =  ls_adrc_tmp-house_num1.
    ELSE.
      cs_fpayhx_fref-ref08+60(10) =  ls_adrc_tmp-house_num2.
    ENDIF. "IF ls_adrc_tmp-house_num1 IS NOT INITIAL.

    IF ls_adrc_tmp-post_code1 IS NOT INITIAL.
      cs_fpayhx_fref-ref08+70(10) =  ls_adrc_tmp-post_code1.
    ELSE.
      cs_fpayhx_fref-ref08+70(10) =  ls_adrc_tmp-post_code2.
    ENDIF. "IF ls_adrc_tmp-post_code1 IS NOT INITIAL.

    cs_fpayhx_fref-ref08+80(40) = ls_adrc_tmp-city1.
    cs_fpayhx_fref-ref08+120(5) = ls_adrc_tmp-region.
    cs_fpayhx_fref-ref08+125(5) = ls_adrc_tmp-country.

* ---------------------------------------------------------------------
* FPAYHX-REF09:
* ---------------------------------------------------------------------
*        0                  70                130
* GET_NATION_BNK  +  GET_CRDT_STREET  +
* ---------------------------------------------------------------------

* GET_NATION_BANK_NAME                 CT  <PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><Nm>
    CALL METHOD cl_idfi_cgi_dmee_utils=>get_nation_bank_name
      EXPORTING
        iv_zbnks  = is_fpayh-zbnks
        iv_zbnky  = is_fpayh-zbnky
        iv_zbnka  = is_fpayh-zbnka
        iv_nation = ls_format_params-nation
      RECEIVING
        rv_return = cs_fpayhx_fref-ref09(70).

** GET_CREDITOR_STREET                  CT  <PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>
*    CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_street
*      EXPORTING
*        iv_doc2r   = ls_fpayp_tmp-doc2r
*        iv_gpa1t   = is_fpayh-gpa1t
*        iv_nation  = ls_format_params-nation
*        iv_dorigin = is_fpayh-dorigin
*        iv_doc2t   = ls_fpayp_tmp-doc2t
*        iv_zstra   = is_fpayh-zstra
*        iv_zadnr   = is_fpayh-zadnr
*        iv_zpfac   = is_fpayh-zpfac
*      RECEIVING
*        rv_result  = cs_fpayhx_fref-ref09+70(60).    " SEE REF02+20(60) n2942194

* ---------------------------------------------------------------------
* FPAYHX-REF10:
* ---------------------------------------------------------------------
*       0                80                120          130
* GET_CRDT_NM  +  GET_CRDT_PO_CITY  +  GET_CRDT_REG  +
* ---------------------------------------------------------------------

* GET CREDITOR_NAME                CT  <PmtInf><CdtTrfTxInf><Cdtr><Nm>
    IF  is_fpayh-koinh IS INITIAL
           OR is_fpayh-koinh EQ is_fpayh-znme1.
      IF is_fpayh-dorigin EQ 'HR-PY'.                       "#EC NOTEXT
        cs_fpayhx_fref-ref10(80) = is_fpayh-znme1.
      ELSE.
        CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_name
          EXPORTING
            iv_doc2r   = ls_fpayp_tmp-doc2r
            iv_gpa1t   = is_fpayh-gpa1t
            iv_nation  = ls_format_params-nation
            iv_dorigin = is_fpayh-dorigin
            iv_doc2t   = ls_fpayp_tmp-doc2t
            iv_zadnr   = is_fpayh-zadnr
            iv_zname1  = is_fpayh-znme1
            iv_zname2  = is_fpayh-znme2
          RECEIVING
            rv_result  = cs_fpayhx_fref-ref10(80).
      ENDIF. "IF is_fpayh-dorigin EQ 'HR-PY'.
    ELSE.
      cs_fpayhx_fref-ref10(80) = is_fpayh-koinh.
    ENDIF.

* GET_CREDITOR_PO_CITY                CT  <PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><TwnNm>
    IF is_fpayhx-xschk EQ abap_true.
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_po_city
        EXPORTING
          iv_doc2r   = ls_fpayp_tmp-doc2r
          iv_gpa1t   = is_fpayh-gpa1t
          iv_nation  = ls_format_params-nation
          iv_dorigin = is_fpayh-dorigin
          iv_doc2t   = ls_fpayp_tmp-doc2t
          iv_zpfor   = is_fpayh-zpfor
          iv_zadnr   = is_fpayh-zadnr
        RECEIVING
          rv_result  = lv_po_city.
    ENDIF. "IF is_fpayhx-xschk EQ abap_true.
    IF lv_po_city IS INITIAL.
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_city
        EXPORTING
          iv_doc2r   = ls_fpayp_tmp-doc2r
          iv_gpa1t   = is_fpayh-gpa1t
          iv_nation  = ls_format_params-nation
          iv_dorigin = is_fpayh-dorigin
          iv_doc2t   = ls_fpayp_tmp-doc2t
          iv_zort1   = is_fpayh-zort1
          iv_zadnr   = is_fpayh-zadnr
        RECEIVING
          rv_result  = cs_fpayhx_fref-ref10+80(40).
    ELSE.
      cs_fpayhx_fref-ref10+80(40) = lv_po_city.
    ENDIF.

* GET_CREDITOR_REGION             CT  <PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><CtrySubDvsn>
    CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_region
      EXPORTING
        iv_doc2r   = ls_fpayp_tmp-doc2r
        iv_gpa1t   = is_fpayh-gpa1t
        iv_nation  = ls_format_params-nation
        iv_dorigin = is_fpayh-dorigin
        iv_doc2t   = ls_fpayp_tmp-doc2t
        iv_zregi   = is_fpayh-zregi
        iv_zadnr   = is_fpayh-zadnr
        iv_zland   = is_fpayh-zland
        iv_zregx   = is_fpayhx-zregx
      RECEIVING
        rv_result  = cs_fpayhx_fref-ref10+120(10).

* ---------------------------------------------------------------------------
* FPAYHX-REF12:
* ---------------------------------------------------------------------------
*      0           10        30      40       50       60       64      99
* GET_SCBIND + GET_TAXID + CGIIR + CGIPRT + CGIID  + CGICD + SCB_ZWCK
* ---------------------------------------------------------------------------

* GET_SCBINDICATOR                 CT  <PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Cd>
*                                  DD  <PmtInf><DrctDbtTxInf><RgltryRptg><Dtls><Cd>
    "n3108984 support of FPAYHX-SND_CTRY_CODE
    ASSIGN COMPONENT lc_sender_code OF STRUCTURE is_fpayhx TO <fs_sender_code>.
    IF sy-subrc = 0 AND <fs_sender_code> IS NOT INITIAL.
      cs_fpayhx_fref-ref12(10) = <fs_sender_code>.
    ELSEIF ls_fpayp_tmp-lzbkz NE space.
      CALL FUNCTION 'FI_SCBINDICATOR_GETDETAIL'
        EXPORTING
          scbindicator = ls_fpayp_tmp-lzbkz
        IMPORTING
          t015l_data   = ls_t015l
        EXCEPTIONS
          not_found    = 1
          OTHERS       = 99.

      IF sy-subrc EQ 0 AND ls_t015l-lvawv IS NOT INITIAL.
        cs_fpayhx_fref-ref12(10) = ls_t015l-lvawv.
        cs_fpayhx_fref-ref12+64(35) = ls_t015l-zwck1.
                "CT  <PmtInf><CdtTrfTxInf><RgltryRptg><Dtls><Inf> n2942194
      ELSE.
        cs_fpayhx_fref-ref12(10) = ls_fpayp_tmp-lzbkz.
      ENDIF. "IF sy-subrc EQ 0.
    ENDIF. "IF ls_fpayp_tmp-lzbkz NE space.

* GET_CREDITOR_TAXID              CT <PmtInf><CdtTrfTxInf><Tax><Cdtr><TaxId>
*                                 DD <PmtInf><DrctDbtTxInf><Tax><Cdtr><TaxId>
    IF lv_area EQ cl_idfi_cgi_dmee_utils=>gc_fi.
      CALL METHOD cl_idfi_cgi_dmee_utils=>get_creditor_taxid
      EXPORTING
        iv_gpa1r  = is_fpayh-gpa1r
      RECEIVING
        rv_result = cs_fpayhx_fref-ref12+10(20).
    ENDIF.


* GET_CGI_IR                  CT + DD  <GrpHdr><InitgPty><Id><OrgId><Othr><Issr>
*                             CT  <PmtInf><Dbtr><Id><OrgId><Othr><Issr>
*                             DD  <PmtInf><Cdtr><Id><OrgId><Othr><Issr>
      cs_fpayhx_fref-ref12+30(10) = lv_cgiir.

* GET_CGI_ID                 CT + DD <GrpHdr><InitgPty><Id><OrgId><BICOrBEI>
*                            CT <PmtInf><Dbtr><Id><OrgId><BICOrBEI>
*                            DD <PmtInf><Cdtr><Id><OrgId><BICOrBEI>
      cs_fpayhx_fref-ref12+40(10) = lv_cgiid.

* GET_CGI_PRT                 CT + DD  <GrpHdr><InitgPty><Id><OrgId><Othr><SchmeNm><Prtry>
*                             CT  <PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Prtry>
*                             DD  <PmtInf><Cdtr><Id><OrgId><Othr><SchmeNm><Prtry>
      cs_fpayhx_fref-ref12+50(10) = lv_cgiprt.

* GET_CGI_CD                  CT + DD  <GrpHdr><InitgPty><Id><OrgId><Othr><SchmeNm><Cd>
*                             CT  <PmtInf><Dbtr><Id><OrgId><Othr><SchmeNm><Cd>
*                             DD  <PmtInf><Cdtr><Id><OrgId><Othr><SchmeNm><Cd>
      cs_fpayhx_fref-ref12+60(4) = lv_cgicd.                "n2893975

* ---------------------------------------------------------------------
* END OF DMEE without EXIT
* ---------------------------------------------------------------------

ENDMETHOD.