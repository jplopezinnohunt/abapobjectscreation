* EHP5
* GLWEH5K018586 06112009 default jurisdiction code only for tax comp.code(1403866)
* GLWE34K019210 09092009 jurisd. code and 0 % tax(1383497)
* 4.6C
* WKUL9CK005642 28042000 übergreifende Nummer bei BUV füllen
* WKUL9CK005786 14042000 Buchung von Auslandsbelegen mit TXJCD korr.
* AHRWKUK060745 22101999 Search for vendor improved (esp.duplicates)

*---------------------------------------------------------------------*
*       INCLUDE LHRTSF02 .                                            *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM RE001                                                    *
*---------------------------------------------------------------------*
FORM  re001
USING VALUE(bukrs)
      VALUE(bukst).                         "GLWEH5K018586

  STATICS: bukst_mem LIKE t001-bukrs.       "GLWEH5K018586

  IF t001_bukrs <> bukrs.
*   select single * from t001 where bukrs = bukrs.
    CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
      EXPORTING
        companycode = bukrs
        language    = sy-langu
      IMPORTING
        comp_name   = t001_butxt
        city        = t001_ort01
        country     = t001_land1
        currency    = t001_waers
        langu       = t001_spras
        chrt_accts  = t001_ktopl
        fy_variant  = t001_periv
*       JURISDICTION = T001_TXJCD
      EXCEPTIONS
        not_found   = 1
        OTHERS      = 2.

    t001_bukrs = bukrs.
    IF sy-subrc <> 0.
      WRITE: / text-e12, 'T001', text-e13, bukrs.
      STOP.
    ENDIF.
  ENDIF.

* GLWEH5K018586 begin
  IF bukst_mem NE bukst.
    CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
      EXPORTING
        companycode  = bukst
        language     = sy-langu
      IMPORTING
        jurisdiction = t001_txjcd
      EXCEPTIONS
        not_found    = 1
        OTHERS       = 2.

    bukst_mem = bukst.
    IF sy-subrc <> 0.
      WRITE: / text-e12, 'T001', text-e13, bukst.
      STOP.
    ENDIF.
  ENDIF.
* GLWEH5K018586 end

ENDFORM.                               "END OF RE001

*---------------------------------------------------------------------*
*       FORM RE005                                                    *
*---------------------------------------------------------------------*
*form  re005
*    using value(land1).
*
*  if t005-land1 <> land1.
*    select single * from t005 where land1 = land1.
*    if sy-subrc <> 0.
*       *t005 = space.
*      *t005-land1 = land1.
*     t005 = space.
*     write: / text-e12, 'T005', text-e13, *t005.
*      stop.
*    endif.
*  endif.
*
*endform.


* QIZ muß noch Ersatz geschaffen werden...
*---------------------------------------------------------------------*
*       FORM RE053                                                    *
*---------------------------------------------------------------------*
*FORM  RE053
*USING VALUE(SPRAS)
*      VALUE(KURZT)
*      SUBRC.
*
*  IF T053-SPRAS = SPRAS AND
*     T053-KURZT = KURZT.
*    SUBRC = 0.
*  ELSE.
*    SELECT SINGLE * FROM T053 WHERE SPRAS = SPRAS
*                              AND   KURZT = KURZT.
*    SUBRC = SY-SUBRC.
*  ENDIF.
*ENDFORM.

*---------------------------------------------------------------------*
*       FORM RE549T                                                   *
*---------------------------------------------------------------------*
*form  re549t
*using value(abkrs).
**  IF T549T-ABKRS <> ABKRS OR
**     T549T-SPRSL <> SY-LANGU.
**    SELECT SINGLE * FROM T549T WHERE SPRSL = SY-LANGU
**                               AND   ABKRS = ABKRS.
**    IF SY-SUBRC <> 0.
**       *T549T = SPACE.
**       *T549T-SPRSL = SY-LANGU.
**       *T549T-ABKRS = ABKRS.
**      T549T = SPACE.
**      WRITE: / TEXT-E12, 'T549T', TEXT-E13, *T549T.
**      STOP.
**    ENDIF.
**  ENDIF.
*endform.                               "RE549T

*---------------------------------------------------------------------*
*        ADMINISTRATE_POST_RESULT                                     *
*---------------------------------------------------------------------*
FORM administrate_post_result
     USING error
           onlyonce.

  DATA tabix LIKE sy-tabix.

* look if current message already in result table
  IF onlyonce IS INITIAL.
    READ TABLE post_result
        WITH KEY pernr      = ep_translate-pernr
                 reinr      = ep_translate-reinr
                 perio      = ep_translate-perio    "SVTK1926024
                 brlin      = brlin
                 message    = wa_bapiret2-message
                 row        = wa_bapiret2-row.
  ELSE.
    READ TABLE post_result
        WITH KEY pernr      = ep_translate-pernr
                 reinr      = ep_translate-reinr
                 perio      = ep_translate-perio    "SVTK1926024
                 type       = wa_bapiret2-type
                 id         = wa_bapiret2-id
                 number     = wa_bapiret2-number.
  ENDIF.
  IF sy-subrc NE 0.
* when not, check whether any message already in result table
    READ TABLE post_result
        WITH KEY pernr = ep_translate-pernr
*                 reinr = ep_translate-reinr.       "SVTK1926024
                 reinr = ep_translate-reinr         "SVTK1926024
                 perio = ep_translate-perio.        "SVTK1926024
    tabix = sy-tabix.
    IF NOT post_result-message IS INITIAL.
* when yes, set flag for appending current error message
      append_error_line = 'X'.
    ENDIF.
    PERFORM clear_post_result_bapiret2.
    post_result-error  = error.
    post_result-brlin = brlin.
    MOVE-CORRESPONDING wa_bapiret2 TO post_result.
* append error message if already messages in result table
    IF append_error_line = 'X'.
      APPEND post_result.
* change result table line if no messages yet
    ELSE.
      MODIFY post_result INDEX tabix.
    ENDIF.
    append_replace_line = 'X'.
  ENDIF.
  no_append_flag = error.

ENDFORM.                               "ADMINISTRATE_POST_RESULT

*---------------------------------------------------------------------*
*        CLEAR_POST_RESULT_BAPIRET2                                   *
*---------------------------------------------------------------------*
FORM clear_post_result_bapiret2.

  CLEAR: post_result-type,             "WKU_TUNE
         post_result-id,               "WKU_TUNE
         post_result-number,           "WKU_TUNE
         post_result-message,          "WKU_TUNE
         post_result-log_no,           "WKU_TUNE
         post_result-log_msg_no,       "WKU_TUNE
         post_result-message_v1,       "WKU_TUNE
         post_result-message_v2,       "WKU_TUNE
         post_result-message_v3,       "WKU_TUNE
         post_result-message_v4,       "WKU_TUNE
         post_result-parameter,        "WKU_TUNE
         post_result-row,              "WKU_TUNE
         post_result-field.            "WKU_TUNE

ENDFORM.                               "CLEAR_POST_RESULT_BAPIRET2

*&---------------------------------------------------------------------*
*&      Form  EVALUATE_VENDOR/CUSTOMER_CHECK
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->RESULT_TAB  text
*----------------------------------------------------------------------*
FORM evaluate_vendor_customer_check
     TABLES   result_tab STRUCTURE bapi1007_8.

  DATA: mess_no    TYPE t100c-msgnr,  "GLW note 2347947
        lv_mess_ty LIKE sy-msgty,
        lv_mess_no TYPE sy-msgno.

  CHECK NOT fi_acct_det_hr-vend_cust_line IS INITIAL.         "WKU_TUNE

  READ TABLE result_tab INDEX fi_acct_det_hr-vend_cust_line.  "WKU_TUNE
  IF result_tab-customer IS INITIAL.   "WKU_TUNE
* no account could be found.                                  "WKU_TUNE
    CLEAR wa_bapiret2.                 "WKU_TUNE_TEST
    brlin = 1.                         "WKU_TUNE_TEST
* transport account finding error message                "WKU_TUNE_TEST
    MOVE-CORRESPONDING result_tab TO wa_bapiret2.        "WKU_TUNE_TEST
    wa_bapiret2-row = 0.               "WKU_TUNE_TEST

    PERFORM administrate_post_result USING 'X' ' '.      "WKU_TUNE_TEST

  ELSE.                                "WKU_TUNE
* acoount was found, but look for posting blocks, delete indicators
* and multiple entries
    IF NOT result_tab-pstg_blk_g IS INITIAL OR
       NOT result_tab-pstg_blk_c IS INITIAL.
* posting block for account is active
      CLEAR wa_bapiret2.
      brlin = 1.
* construct posting block error message
      par1 = result_tab-customer.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = 'F5'
          number = '351'
          par1   = par1
          row    = 0
        IMPORTING
          return = wa_bapiret2
        EXCEPTIONS
          OTHERS = 0.

      PERFORM administrate_post_result USING 'X' ' '.

    ENDIF.
    IF NOT result_tab-del_flag_g IS INITIAL OR
       NOT result_tab-del_flag_c IS INITIAL.

* GLW note 2347947 begin
      CASE fi_acct_det_hr-koart.
        WHEN 'D'.
          mess_no = lv_mess_no = '001'.
        WHEN OTHERS.
          mess_no = lv_mess_no = '002'.
      ENDCASE.
      CALL FUNCTION 'READ_CUSTOMIZED_MESSAGE'
        EXPORTING
          i_arbgb = 'F5A'
          i_dtype = 'W'
          i_msgnr = mess_no
        IMPORTING
          e_msgty = lv_mess_ty.
* GLW note 2347947 end
* delete indicator for account is active
      CLEAR wa_bapiret2.
      brlin = 1.
* construct delete indicator  message
      par1 = result_tab-customer.
      par2 = result_tab-comp_code.    "GLW note 2347947
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = lv_mess_ty      "GLW note 2347947
          cl     = 'F5A'
          number = lv_mess_no
          par1   = par1
          par2   = par2
          row    = 0
        IMPORTING
          return = wa_bapiret2
        EXCEPTIONS
          OTHERS = 0.

      IF lv_mess_ty = 'E'.     "GLW note 2347947
        PERFORM administrate_post_result USING 'X' ' '.
      ELSE.
        PERFORM administrate_post_result USING ' ' ' '.
      ENDIF.

    ENDIF.
    IF result_tab-customer EQ 'NOT_UNIQUE'.                 "WKUK060745
* account is not unique                                     "WKUK060745
      CLEAR wa_bapiret2.                                    "WKUK060745
      brlin = 1.                                            "WKUK060745
* construct delete indicator error message                  "WKUK060745
      par1 = result_tab-fieldvalue.                         "WKUK060745
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'                  "WKUK060745
        EXPORTING                                        "WKUK060745
          type   = 'E'                                "WKUK060745
          cl     = '56'                               "WKUK060745
          number = '440'                              "WKUK060745
          par1   = par1                               "WKUK060745
          row    = 0                                  "WKUK060745
        IMPORTING                                        "WKUK060745
          return = wa_bapiret2                        "WKUK060745
        EXCEPTIONS                                       "WKUK060745
          OTHERS = 0.                                 "WKUK060745

      PERFORM administrate_post_result USING 'X' ' '.       "WKUK060745

    ENDIF.                                                  "WKUK060745

  ENDIF.

ENDFORM.                               " EVALUATE_VENDOR_CUSTOMER_CHECK

*&---------------------------------------------------------------------*
*&      Form  EVALUATE_SEARCH_HELP
*&---------------------------------------------------------------------*
*&      Determine first field of the elementary search help....
*&---------------------------------------------------------------------*
FORM evaluate_search_help USING VALUE(general_shlp) VALUE(hotkey)
                                      selopt_tab_tabname
                                      selopt_tab_fieldname.

  DATA: wa_hotkey LIKE dd30v_wa-hotkey.                     "QIZK001967

* search help already in buffer table?
  READ TABLE search_help_buffer WITH KEY shlp = general_shlp
                                         hotkey = hotkey.
  IF sy-subrc IS INITIAL.
* there is an entry in buffer table...
    selopt_tab_tabname = search_help_buffer-tabname.
    selopt_tab_fieldname = search_help_buffer-fieldname.
  ELSE.
* there is no entry in buffer table... create a new entry...
    search_help_buffer-shlp = general_shlp.
    search_help_buffer-hotkey = hotkey.
* 1. step: read general search help and get a list of all elementary
*          search helps.
    CALL FUNCTION 'DDIF_SHLP_GET'
      EXPORTING
        name          = general_shlp
        state         = 'A'
        langu         = sy-langu
      TABLES
        dd31v_tab     = dd31v_tab
      EXCEPTIONS
        illegal_input = 1
        OTHERS        = 2.
    IF sy-subrc <> 0.
      WRITE: 'Fehler bei der Bestimmung der Suchhilfe.'(shp).
      STOP.
    ENDIF.
* 2. step: search for the elementary search help with hotkey = hotkey
*          of table T030.
    LOOP AT dd31v_tab.
      CALL FUNCTION 'DDIF_SHLP_GET'
        EXPORTING
          name          = dd31v_tab-subshlp
          state         = 'A'
          langu         = sy-langu
        IMPORTING
          dd30v_wa      = dd30v_wa
        TABLES
          dd32p_tab     = dd32p_tab
        EXCEPTIONS
          illegal_input = 1
          OTHERS        = 2.
      IF dd30v_wa-hotkey EQ hotkey.
        wa_hotkey = hotkey.                                 "QIZK001967
        SORT dd32p_tab BY shlpselpos.
* search for the first field of popup (of search help)
        LOOP AT dd32p_tab WHERE shlpselpos NE '00'.
          EXIT.
        ENDLOOP.
        selopt_tab_fieldname = dd32p_tab-fieldname.
        search_help_buffer-fieldname = dd32p_tab-fieldname.
* search for assigned table of dd32p_tab-fieldname
        CALL FUNCTION 'DDIF_VIEW_GET'
          EXPORTING
            name          = dd30v_wa-selmethod
            state         = 'A'
            langu         = sy-langu
          TABLES
            dd27p_tab     = dd27p_tab
          EXCEPTIONS
            illegal_input = 1
            OTHERS        = 2.
        IF sy-subrc <> 0.
          WRITE: 'Fehler bei der Bestimmung der Suchhilfe.'(shp).
          STOP.
        ENDIF.
        LOOP AT dd27p_tab WHERE viewfield EQ
                                selopt_tab_fieldname.
          selopt_tab_tabname = dd27p_tab-tabname.
          search_help_buffer-tabname = dd27p_tab-tabname.
          APPEND search_help_buffer.
          EXIT.
        ENDLOOP.
        EXIT.
      ENDIF.
    ENDLOOP.
    IF wa_hotkey IS INITIAL.                                "QIZK001967
* No hotkey found...                                "QIZK001967
      WRITE: 'Fehler bei der Suche nach dem Hotkey'(sh1),
              hotkey,                                       "QIZK001967
             'der Suchhilfe'(sh2), general_shlp.            "QIZK001967
      STOP.                                                 "QIZK001967
    ENDIF.                                                  "QIZK001967
  ENDIF.
ENDFORM.                               " EVALUATE_SEARCH_HELP



*&---------------------------------------------------------------------*
*&      Form  ADMINISTRATE_FI_ACCT_DET_HR
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_FI_ACCT_DET_HR  text
*      -->P_MOMAGKOMOK  text
*      -->P_EPK_BUKST  text
*      -->P_EPK_KTOSL  text
*      -->P_1007   text
*      -->P_FI_ACCT_DET_HR_APPEND_FLAG  text
*----------------------------------------------------------------------*
FORM administrate_fi_acct_det_hr USING    momagkomok
                                          bukrs
                                          ktosl
                                          pernr
                                          append_flag
                                          tabix.

* fill table for accumulated T030-CHECK...
  CLEAR: fi_acct_det_hr,
         append_flag,
         tabix.
* see if T030-check was already done
  READ TABLE fi_acct_det_hr
      WITH KEY bukrs      = bukrs
               ktosl      = ktosl
*              symb_acct  =                             "not yet needed
               momagkomok = momagkomok.
*              add_modif  =                             "not yet needed
  IF sy-subrc = 0.
    tabix = sy-tabix.
  ELSE.

    fi_acct_det_hr-bukrs      = bukrs.
    fi_acct_det_hr-ktosl      = ktosl.
*   fi_acct_det_hr-symb_acct  =                         "not yet needed
    fi_acct_det_hr-momagkomok = momagkomok.
*   fi_acct_det_hr-add_modif  =                         "not yet needed

* read table T030
    CALL FUNCTION 'HRCA_FI_ACCT_DET_HR'
      EXPORTING
        companycode        = bukrs
        process            = ktosl
*       symb_acct          =                          "not yet needed
        eg_acct_det        = momagkomok
*       add_modif          =                          "not yet needed
      IMPORTING
        gl_account_debit   = fi_acct_det_hr-konto
        gl_account_credit  = fi_acct_det_hr-hnkto
        posting_key_debit  = fi_acct_det_hr-slbsl
        posting_key_credit = fi_acct_det_hr-hnbsl
        account_type       = fi_acct_det_hr-koart
      TABLES
        return_table       = return_table.

    READ TABLE return_table INDEX 1.
    IF sy-subrc = 0.
      MESSAGE ID     return_table-id
              TYPE   return_table-type
              NUMBER return_table-number
              WITH   return_table-message_v1
                     return_table-message_v2
                     return_table-message_v3
                     return_table-message_v4
              RAISING ale_communication_error.
    ENDIF.

* fill empty account if the other account is filled correctly
    IF fi_acct_det_hr-konto IS INITIAL AND NOT
       fi_acct_det_hr-hnkto IS INITIAL.
      fi_acct_det_hr-konto = fi_acct_det_hr-hnkto.
    ELSEIF NOT fi_acct_det_hr-konto IS INITIAL AND
               fi_acct_det_hr-hnkto IS INITIAL.
      fi_acct_det_hr-hnkto = fi_acct_det_hr-konto.
    ENDIF.

    fi_acct_det_hr-pernr = pernr.
    append_flag = 'X'.

  ENDIF.

ENDFORM.                               " ADMINISTRATE_FI_ACCT_DET_HR



*&---------------------------------------------------------------------*
*&      Form  CHECK_JURISDICTION_ACTIVE
*&---------------------------------------------------------------------*
* using only global variables:
* -> ep_translate-bukrs
* <- jurisdiction_active = X/_
* <- external_tax_calculation = X/_
*&---------------------------------------------------------------------*
* Routine neu zu WKUK005786, Kopie von Routine in RPRSR000
*&---------------------------------------------------------------------*
FORM check_jurisdiction_active.

  STATICS: companycode LIKE hrca_company-comp_code.

* check jurisdiction only if companycode has changed (performance)
  CHECK ep_translate-bukst NE companycode.            "GLWE34K019210
  companycode = ep_translate-bukst.                   "GLWE34K019210

  CALL FUNCTION 'HRCA_CHECK_JURISDICTION_ACTIVE'
    EXPORTING
      i_bukrs            = ep_translate-bukst    "GLWE34K019210
    IMPORTING
      e_txjcd_active     = jurisdiction_active
      e_tax_external     = tax_calculation_external
    EXCEPTIONS
      input_incomplete   = 1
      input_inconsistent = 2
      other_error        = 3
      OTHERS             = 4.

  IF sy-subrc <> 0.
    CLEAR jurisdiction_active.
    CLEAR tax_calculation_external.
  ENDIF.

ENDFORM.                    "CHECK_JURISDICTION_ACTIVE


*&---------------------------------------------------------------------*
*&      Form  ADMINISTRATE_BUV_HELP
*&---------------------------------------------------------------------*
* neu zu WKUK005642, verwaltet BUV_HELP
*----------------------------------------------------------------------*
*      -->P_N_AWREF
*----------------------------------------------------------------------*
FORM administrate_buv_help USING p_n_awref.

  DATA buv_help_uebnr LIKE buv_help-uebnr.

  READ TABLE buv_help
      WITH KEY awref = p_n_awref.
  IF NOT sy-subrc IS INITIAL.
    buv_help-awref = p_n_awref.
    buv_help-uebnr = n_awref_store.
    APPEND buv_help.
  ELSEIF sy-subrc = 0 AND buv_help-uebnr NE n_awref_store.
    buv_help_uebnr = buv_help-uebnr.
    LOOP AT buv_help WHERE uebnr = n_awref_store.
      buv_help-uebnr =  buv_help_uebnr.
      MODIFY buv_help.
    ENDLOOP.
  ENDIF.

ENDFORM.                               " ADMINISTRATE_BUV_HELP