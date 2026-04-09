* 6.0
* WKUAENK015412 22112004 Determine and transfer profit center (791956)
* 4.6C
* WKUL9CK005642 28042000 übergreifende Nummer bei BUV füllen
* WKUL9CK005786 14042000 Buchung von Auslandsbelegen mit TXJCD korr.

FUNCTION-POOL hrts.                    "MESSAGE-ID ..

INCLUDE rprida10_40.
INCLUDE rprida11_r_40.

TYPES: BEGIN OF store_bz,              "Ästhetik
         awref LIKE bz-awref,          "Ästhetik
         aworg LIKE bz-aworg,          "Ästhetik
         awlin LIKE bz-awlin,          "Ästhetik
         bukrs LIKE bz-bukrs,          "Ästhetik
*         psref type psref,            "Ästhetik            "AKAK011844
         psref TYPE ptrv_psref,                             "AKAK011844
         pernr LIKE bz-pernr,          "Ästhetik
         exbel LIKE bz-exbel,          "Ästhetik
         belnr LIKE bz-belnr,          "Beleg pro Beleg
         konto_sort LIKE bz-hnkto,     "Beleg pro Kreditor  "WKUK015412
         prctr LIKE epk-prctr,                              "WKUK015412
         waers LIKE bz-waers,          "Ästhetik
         umdat LIKE bz-umdat,                            "QKZ_CEE_CZ_SK
         koart LIKE bz-koart,                               "WKUK012485
*         vat_delta  TYPE xfeld,   "GLW note 1808477
         vat_delta type char30,
         xnegp      LIKE bz-xnegp,  "GLW note 2071158
         beldt_split      like epk-beldt_split, "GLW note 2315344
         segment     lIKE epk-segment,
       END OF store_bz.                "Ästhetik

* Begin GS - EU_VAT
TYPES: BEGIN OF recdata,
  key TYPE ptp00,
  data TYPE ptk03,
  END OF recdata.

TYPES:
    BEGIN OF ty_s_data.
TYPES belnr TYPE nrbel.
INCLUDE TYPE ptp_vat_details.
TYPES END OF ty_s_data .

TYPES:
    BEGIN OF ty_bukrs.
TYPES bukrs TYPE bukrs.
TYPES END OF ty_bukrs .
* END  - GS EU_VAT


DATA: store_bz     TYPE store_bz OCCURS 0 WITH HEADER LINE,   "Ästhetik
* latest lines of all normal posting documents are stored here
      store_bz_cap TYPE store_bz OCCURS 0 WITH HEADER LINE, "WKUK012485
* latest lines of all clearing account posting documents are stored here
      store_bz_pds TYPE store_bz OCCURS 0 WITH HEADER LINE. "WKUK012485
* latest lines of all posting document split posting documents

*      begin of store_bz_pds occurs 0.                      "WKUK012485
*        include type store_bz.                             "WKUK012485
*data:   koart like bz-koart,                               "WKUK012485
*      end of store_bz_pds.                                 "WKUK012485

* function parameters as global data
DATA: budat    LIKE rprxxxxx-budat,
      adv_proc TYPE c LENGTH 1,  "GLW note 2713017
      soper    LIKE rprxxxxx-soper,
      bldat    LIKE rprxxxxx-bldat,
      gsber_a  LIKE rprxxxxx-kr_feld3,
      gsber_g  LIKE rprxxxxx-kr_feld11,
      a_sgtxt  LIKE rprxxxxx-kr_feld4,
      g_sgtxt  LIKE rprxxxxx-kr_feld4,
      blart    LIKE rprxxxxx-blart, "GLW note 2725186
      blart_vendor LIKE rprxxxxx-blart,
      bl_spl   LIKE rprxxxxx-bl_spl VALUE 'R',
      g_verd   LIKE rprxxxxx-g_verd VALUE 'R',
      a_verd   LIKE rprxxxxx-a_verd VALUE 'R',
      replace  LIKE rprxxxxx-kr_feld1.
DATA: bl_k     LIKE rprxxxxx-kr_feld7,                      "WKUK015412
      true     TYPE boole_d VALUE 'X',                      "WKUK015412
      false    TYPE boole_d VALUE ' ',                      "WKUK015412
      prctr_tr TYPE boole_d.                                "WKUK015412
DATA  segment_tr TYPE boole_d. "GLW note 2926207

DATA:
*      I_AWREF               TYPE I,       " WBG Hotline 175746
      n_awref(10)           TYPE n,
      n_awref_store         LIKE n_awref,
      awlin                 LIKE sy-tabix,
      new_awkey(1) VALUE 'X',
      runid                 LIKE ptrv_rot_ep-runid,
      saprel                LIKE sy-saprl,
      tax_item_in_tabix     LIKE sy-tabix VALUE 0,
*     Begin of MAW_EUVAT
      tax_item_in_tabix_man LIKE sy-tabix VALUE 0,
*     End of MAW_EUVAT
      wa_t_ptrv_post_result LIKE ptrv_post_result,
      momagkomok            LIKE hrpp_acct_det-eg_acct_det,
      accts_are_equal(1),
      fi_acct_det_hr_append_flag(1),
      tabix                 LIKE sy-tabix,
      t_ptrv_rot_ep_lines   TYPE i,
      no_append_flag(1),
      append_error_line(1),
      append_replace_line(1),
      brlin                 TYPE i,
      wa_bapiret2           LIKE bapiret2,
      max_pernr             LIKE bz-pernr VALUE '99999999',
      max_exbel             LIKE bz-exbel VALUE '9999999999/999',
      max_belnr             LIKE bz-belnr VALUE '999', "Beleg pro Beleg
      rest                  TYPE i,
      percentage            TYPE i,
      table_lines           TYPE i.

TABLES: ptrv_rot_awkey, *ptrv_rot_awkey,
        ptrv_doc_hd,    *ptrv_doc_hd,
        ptrv_doc_it,    *ptrv_doc_it,
        ptrv_doc_tax,   *ptrv_doc_tax,
        ptrv_doc_mess,  *ptrv_doc_mess.

TABLES: t706d.                                              "QIZK054176

* Begin of MAW_EUVAT
*DATA: BEGIN OF ep_translate OCCURS 100.
*        INCLUDE STRUCTURE ptrv_ep.
*DATA:   tax_item_line(5) TYPE n,
*        cobl_check_line(5) TYPE n,
*        acc_det_line(5) TYPE n,
*      END OF ep_translate.
*
*DATA: wa_ep_translate LIKE ep_translate.
TYPES:
      BEGIN OF ts_ep_translate.
INCLUDE TYPE ptrv_ep.
TYPES:
*     tax_item_line(5)   TYPE n,
      tax_item_line      type CL_FITV_VAT=>TV_EP_TAX_ITEM_LINE,
      cobl_check_line(5) TYPE n,
      acc_det_line(5)    TYPE n,
      tax_calculation    TYPE abap_bool,
*  vat_delta          TYPE xfeld,   "GLW note 1808477
END OF ts_ep_translate.

TYPES tt_ep_translate TYPE TABLE OF ts_ep_translate.

DATA ep_translate    TYPE tt_ep_translate WITH HEADER LINE.
DATA wa_ep_translate TYPE ts_ep_translate.
* End of MAW_EUVAT

DATA: BEGIN OF ptrv_rot_ep OCCURS 100.
        INCLUDE STRUCTURE ptrv_rot_ep.
DATA: END OF ptrv_rot_ep.

DATA: return_table LIKE bapiret2 OCCURS 0 WITH HEADER LINE,
      return_table_lines TYPE i.

* data definition of check tables
DATA: BEGIN OF open_item_check OCCURS 0,
        bukrs      LIKE fmdc_activ-bukrs,
        cac_active LIKE fmdc_activ-xfmca,
        cbm_active LIKE fmdc_activ-xfmcb,
        pcm_acitve LIKE fmdc_activ-xfmco,
      END OF open_item_check,
      tax_item_in       LIKE rtax1u38   OCCURS 0 WITH HEADER LINE,
      tax_item_out      LIKE rtax1u38   OCCURS 0 WITH HEADER LINE,
      tax_errors        LIKE bapiret2   OCCURS 0 WITH HEADER LINE,
*     Begin of MAW_EUVAT
      tax_item_in_man  LIKE rtax1u38   OCCURS 0 WITH HEADER LINE,
      tax_item_out_man LIKE rtax1u38   OCCURS 0 WITH HEADER LINE,
      tax_errors_man   LIKE bapiret2   OCCURS 0 WITH HEADER LINE,
*     End of MAW_EUVAT
      accountingobjects LIKE ptrv_cobl_precheck OCCURS 0 WITH HEADER LINE,
      cobl_errors       LIKE bapiret2   OCCURS 0 WITH HEADER LINE,
      BEGIN OF fi_acct_det_hr OCCURS 0,
        bukrs      LIKE acct_det_bf-comp_code,
        ktosl      LIKE acct_det_bf-process,
*       symb_acct  like hrpp_acct_det-symb_acct,        "not yet needed
        momagkomok LIKE hrpp_acct_det-eg_acct_det,
*       add_modif  like hrpp_acct_det-add_modif,        "not yet needed
        konto      LIKE acct_det_bf-gl_account,
        hnkto      LIKE acct_det_bf-gl_account,
        slbsl      LIKE acct_det_bf-post_key,
        hnbsl      LIKE acct_det_bf-post_key,
        koart      LIKE acct_det_bf-acct_type,
        vend_cust_line(5) TYPE n,
        pernr      LIKE ep_translate-pernr,
      END OF fi_acct_det_hr,
      customer_selopt_tab LIKE bapi1007_7 OCCURS 0 WITH HEADER LINE,
      customer_result_tab LIKE bapi1007_8 OCCURS 0 WITH HEADER LINE,
      vendor_selopt_tab   LIKE bapi1007_7 OCCURS 0 WITH HEADER LINE,
      vendor_result_tab   LIKE bapi1007_8 OCCURS 0 WITH HEADER LINE,
      bukst_debit_fields  LIKE acct_det_c_c_bf,
      bukst_credit_fields LIKE acct_det_c_c_bf,
      bukrs_debit_fields  LIKE acct_det_c_c_bf,
      bukrs_credit_fields LIKE acct_det_c_c_bf.

DATA: post_result LIKE ptrv_post_result OCCURS 1000 WITH HEADER LINE.

* Fields for search help KRED/DEBI...
DATA: BEGIN OF dd30v_wa.
        INCLUDE STRUCTURE dd30v.
DATA: END OF dd30v_wa.

DATA: BEGIN OF dd31v_tab OCCURS 0.
        INCLUDE STRUCTURE dd31v.
DATA: END OF dd31v_tab.

DATA: BEGIN OF dd32p_tab OCCURS 0.
        INCLUDE STRUCTURE dd32p.
DATA: END OF dd32p_tab.

DATA: BEGIN OF dd27p_tab OCCURS 0.
        INCLUDE STRUCTURE dd27p.
DATA: END OF dd27p_tab.

* buffer table...
DATA: BEGIN OF search_help_buffer OCCURS 0,
        shlp LIKE dd31v-shlpname,
        hotkey LIKE dd30v-hotkey,
        fieldname LIKE dd32p-fieldname,
        tabname LIKE dd27p-tabname,
      END OF search_help_buffer.

* dummy parameters for BAPI-RETURN fill function
DATA: type       LIKE  bapireturn-type,
      cl         LIKE  sy-msgid,
      number     LIKE  sy-msgno,
      par1       LIKE  sy-msgv1,
      par2       LIKE  sy-msgv2,
      par3       LIKE  sy-msgv3,
      par4       LIKE  sy-msgv4,
      log_no     LIKE  bapireturn-log_no,
      log_msg_no LIKE  bapireturn-log_msg_no,
      parameter  LIKE  bapiret2-parameter,
      row        LIKE  bapiret2-row,
      field      LIKE  bapiret2-field.

* business add-in
CLASS cl_exithandler DEFINITION LOAD.                       "WBGK054105
DATA exit_trip_post_fi TYPE REF TO if_ex_trip_post_fi.      "WBGK054105

DATA: jurisdiction_active,              "Jurisdiction active WKUK005786
      tax_calculation_external.         "external tax calc   WKUK005786

* Tabelle für Verknüpfung Belegnummer : übergreifende Nummer bei BUV
DATA: BEGIN OF buv_help OCCURS 0,                           "WKUK005642
        awref LIKE ptrv_doc_hd-awref,                       "WKUK005642
        uebnr LIKE ptrv_doc_hd-uebnr,                       "WKUK005642
      END OF buv_help.                                      "WKUK005642

DATA: util TYPE REF TO cl_fitv_posting_util,               "GLW note 1645219
      h_subrc like sy-subrc,
      h_tabix like sy-tabix.