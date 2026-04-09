* 6.0
* WKUP7HK006457 04042006 'zusätzlicher Belegsplit pro Kreditor' führt zu
*                        'Saldo in Transaktionswährung' (938275)
* WKUAENK015412 22112004 Determine and transfer profit center (791956)
* 4.6C
* WKUL9CK002816 14072000 all clearings of CO objects in PTRV_TRANSLATE

FUNCTION ptrv_translate.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  IMPORTING
*"     VALUE(I_BUDAT) LIKE  RPRXXXXX-BUDAT
*"     VALUE(I_SOPER) LIKE  RPRXXXXX-SOPER
*"     VALUE(I_BLDAT) LIKE  RPRXXXXX-BLDAT
*"     VALUE(I_GSBER_A) LIKE  RPRXXXXX-KR_FELD3
*"     VALUE(I_GSBER_G) LIKE  RPRXXXXX-KR_FELD11
*"     VALUE(I_A_SGTXT) LIKE  RPRXXXXX-KR_FELD4
*"     VALUE(I_G_SGTXT) LIKE  RPRXXXXX-KR_FELD4
*"     VALUE(I_BLART) LIKE  RPRXXXXX-BLART
*"     VALUE(I_BL_SPL) LIKE  RPRXXXXX-BL_SPL
*"     VALUE(I_A_VERD) LIKE  RPRXXXXX-A_VERD
*"     VALUE(I_G_VERD) LIKE  RPRXXXXX-G_VERD
*"     VALUE(I_REPLACE) LIKE  RPRXXXXX-KR_FELD1
*"     VALUE(I_BL_K) LIKE  RPRXXXXX-KR_FELD7 OPTIONAL
*"     VALUE(I_PRCTR_TR) TYPE  BOOLE_D OPTIONAL
*"     VALUE(I_ADV_PROC) TYPE  CHAR1 OPTIONAL
*"     VALUE(I_BLART_VENDOR) TYPE  RPRXXXXX-BLART OPTIONAL
*"     VALUE(I_SEGMENT_TR) TYPE  BOOLE_D OPTIONAL
*"  TABLES
*"      T_EP_TRANSLATE STRUCTURE  PTRV_EP
*"      T_PTRV_ROT_EP STRUCTURE  PTRV_ROT_EP
*"      T_PTRV_POST_RESULT STRUCTURE  PTRV_POST_RESULT
*"      T_RETURN_TABLE STRUCTURE  BAPIRET2
*"  EXCEPTIONS
*"      ALE_COMMUNICATION_ERROR
*"      FI_CUSTOMIZING_ERROR
*"      NUMBER_RANGE_ERROR
*"----------------------------------------------------------------------

  PERFORM clear_global_variables.

  DATA epk_field(33).                                  "Beleg pro CO-Obj

  budat    = i_budat.
  soper    = i_soper.
  bldat    = i_bldat.
  gsber_a  = i_gsber_a.
  gsber_g  = i_gsber_g.
  a_sgtxt  = i_a_sgtxt.
  g_sgtxt  = i_g_sgtxt.
  blart    = i_blart.
  blart_vendor = i_blart_vendor. "GLW note 2725186
  bl_spl   = i_bl_spl.
  a_verd   = i_a_verd.
  g_verd   = i_g_verd.
  replace  = i_replace.
  bl_k     = i_bl_k.                                        "WKUK015412
  prctr_tr = i_prctr_tr.                                    "WKUK015412
  adv_proc = i_adv_proc.  "GLW note 2713017
  segment_tr = i_segment_tr. "GLW note 2926207

  IF blart_vendor IS INITIAL. "GLW note 2725186
    blart_vendor = blart.
  ENDIF.

* begin WBGK054105;
* business add-in (user-exit);
  CALL METHOD cl_exithandler=>get_instance
    CHANGING
      instance = exit_trip_post_fi.
* end WBGK054105;

* PSREF-fields will be collected in table PSREF_FIELDS.
  PERFORM collect_psref_fields TABLES psref_fields.

  DESCRIBE TABLE t_ep_translate LINES table_lines.

  CREATE OBJECT util.      "GLW note 1645219

  LOOP AT t_ep_translate.

    IF table_lines GE 20.
      rest = sy-tabix MOD ( table_lines / 20 ).
      IF rest = 0.
        percentage = sy-tabix / ( table_lines / 20 ) * 5.
        CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
          EXPORTING
            percentage = percentage
            text       = text-p01.
      ENDIF.
    ENDIF.

    CLEAR ep_translate.
    MOVE-CORRESPONDING  t_ep_translate TO ep_translate.

    IF prctr_tr EQ false AND segment_tr EQ false.           "WKUK015412 "GLW note 2926207
      IF epk-koart = 'K' AND bl_spl NE 'C'.                 "WKUK006457
        CLEAR epk-gsber.                                    "WKUK006457
      ENDIF.                                                "WKUK006457
*   IF EP_TRANSLATE-PTYPE = 'G' AND BL_SPL NE 'C'.          "WKUK002816
      IF ( ep_translate-ptype = 'G'                         "WKUK002816
           OR ep_translate-koart = 'F' )                    "WKUK002816
           AND bl_spl NE 'C'.                               "WKUK002816
*     when current line is a vendor line and accounting document is not
*     per CO-object, all CO-objects in current line have to be deleted
*     WBG Hotline 163914: Buchen mit/ohne G.bereich fkt. nicht;
        LOOP AT psref_fields.
          CHECK psref_fields-field <> 'BUKRS'.
          CHECK psref_fields-field <> 'SGTXT'.
          CHECK psref_fields-field <> 'EXBEL'.
          CHECK psref_fields-field <> 'GSBER'.              " WBG
          epk_field(13) = 'EP_TRANSLATE-'.
          epk_field+13(20) = psref_fields-field.
          ASSIGN (epk_field) TO <f>.
          CLEAR <f>.
        ENDLOOP.
      ENDIF.
    ENDIF.                                                  "WKUK015412

* Tables for tax calculation, CO-precheck and T030/vendor/customer-read
* via mass data transfer will be filled.
    PERFORM fill_tables_for_posting_checks.
*    READ TABLE cl_fitv_posting_util=>gt_append_index WITH KEY      "GLW note 1808477 "comment GLW 2098779
*           ep_line = ep_translate-ep_line BINARY SEARCH TRANSPORTING NO FIELDS.
*    IF sy-subrc IS INITIAL.                                        "GLW note 1808477
*      ep_translate-vat_delta = 'X'.                                "GLW note 1808477
*    ENDIF.                                                         "GLW note 1808477
    APPEND ep_translate.
  ENDLOOP.

*  REFRESH cl_fitv_posting_util=>gt_append_index.                 "GLW note 1808477

  READ TABLE t_ptrv_rot_ep INDEX 1.
  runid = t_ptrv_rot_ep-runid.
  DESCRIBE TABLE t_ptrv_rot_ep LINES t_ptrv_rot_ep_lines.
  IF t_ptrv_rot_ep_lines GE 2.
* PTRV_ROT_EP more than one line, i.e PTRV_TRANSLATE called from >=4.0C
    LOOP AT t_ptrv_rot_ep.
      CLEAR ptrv_rot_ep.
      MOVE-CORRESPONDING t_ptrv_rot_ep TO ptrv_rot_ep.
      APPEND ptrv_rot_ep.
    ENDLOOP.
  ENDIF.

  LOOP AT t_ptrv_post_result.
    CLEAR post_result.
    MOVE-CORRESPONDING t_ptrv_post_result TO post_result.
    APPEND post_result.
    DELETE t_ptrv_post_result.
  ENDLOOP.

  CLEAR: t_ep_translate,
         t_ptrv_rot_ep,
         t_ptrv_post_result.
  REFRESH: t_ep_translate,
           t_ptrv_rot_ep,
           t_ptrv_post_result.

* Tax calculation, CO-precheck and vendor/customer-read via mass data
* transfer will be performed
  PERFORM posting_checks.

* Results of tax calculation, CO-precheck and T030/vendor/customer-read
* will be analysed for each ep-line.
  PERFORM build_epk_from_ep.

* Results of tax calculation, CO-precheck and T030/vendor/customer-read
* will be analysed for each travel,
* Documents (Prima Nota) will be created from EPK
  PERFORM create_document_from_epk.

  COMMIT WORK.

* clear global internal tables and structures
  CLEAR: open_item_check,
         tax_item_in,
         tax_item_out,
         tax_errors,
*        Begin of MAW_EUVAT
         tax_item_in_man,
         tax_item_out_man,
         tax_errors_man,
*        End of MAW_EUVAT
         accountingobjects,
         cobl_errors,
         fi_acct_det_hr,
         customer_selopt_tab,
         customer_result_tab,
         vendor_selopt_tab,
         vendor_result_tab.

  REFRESH: open_item_check,
           tax_item_in,
           tax_item_out,
           tax_errors,
*          Begin of MAW_EUVAT
           tax_item_in_man,
           tax_item_out_man,
           tax_errors_man,
*          End of MAW_EUVAT
           accountingobjects,
           cobl_errors,
           fi_acct_det_hr,
           customer_selopt_tab,
           customer_result_tab,
           vendor_selopt_tab,
           vendor_result_tab.

* Result table will be finished with concluding messages
  SORT post_result
      BY pernr reinr error row brlin
         message_v1 message_v2 message_v3.
  LOOP AT post_result.

    CLEAR wa_t_ptrv_post_result.
    MOVE-CORRESPONDING post_result TO t_ptrv_post_result.
    AT END OF reinr.
      IF t_ptrv_post_result-error = ' '.
        IF t_ptrv_post_result-message IS INITIAL.
* no errors, no warnings: write conclusion success message to act. line
          t_ptrv_post_result-brlin = 1.
          CLEAR wa_bapiret2.
          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'C'
              cl     = '56'
              number = '853'
              row    = 0
            IMPORTING
              return = wa_bapiret2.
          MOVE-CORRESPONDING wa_bapiret2 TO t_ptrv_post_result.
        ELSE.
* no errors, but warnings -> append conclusion success message to table
          wa_t_ptrv_post_result-pernr = t_ptrv_post_result-pernr.
          wa_t_ptrv_post_result-name  = t_ptrv_post_result-name.
          wa_t_ptrv_post_result-reinr = t_ptrv_post_result-reinr.
* BEGIN WKU_PERIODEN
          wa_t_ptrv_post_result-perio = t_ptrv_post_result-perio.
* END WKU_PERIODEN
          wa_t_ptrv_post_result-error = t_ptrv_post_result-error.
          wa_t_ptrv_post_result-brlin = t_ptrv_post_result-brlin + 1.
          CLEAR wa_bapiret2.
          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'C'
              cl     = '56'
              number = '853'
              row    = 0
            IMPORTING
              return = wa_bapiret2.
          MOVE-CORRESPONDING wa_bapiret2 TO wa_t_ptrv_post_result.
        ENDIF.
      ELSE.
* errors and warnings ->
        IF t_ptrv_post_result-type NE 'C'.
* append conclusion failure message to table if not yet done
          wa_t_ptrv_post_result-pernr = t_ptrv_post_result-pernr.
          wa_t_ptrv_post_result-name  = t_ptrv_post_result-name.
          wa_t_ptrv_post_result-reinr = t_ptrv_post_result-reinr.
* BEGIN WKU_PERIODEN
          wa_t_ptrv_post_result-perio = t_ptrv_post_result-perio.
* END WKU_PERIODEN
          wa_t_ptrv_post_result-error = t_ptrv_post_result-error.
          wa_t_ptrv_post_result-brlin = t_ptrv_post_result-brlin + 1.
          IF t_ptrv_rot_ep_lines GE 2.
* PTRV_ROT_EP more than one line, i.e PTRV_TRANSLATE called from >=4.0C
            CLEAR wa_bapiret2.
            CALL FUNCTION 'BALW_BAPIRETURN_GET2'
              EXPORTING
                type   = 'C'
                cl     = '56'
                number = '854'
                row    = 0
              IMPORTING
                return = wa_bapiret2.
            MOVE-CORRESPONDING wa_bapiret2 TO wa_t_ptrv_post_result.
          ELSE.
* PTRV_ROT_EP only one line, i.e PTRV_TRANSLATE called from <4.0C
            CLEAR wa_bapiret2.
            CALL FUNCTION 'BALW_BAPIRETURN_GET2'
              EXPORTING
                type   = 'C'
                cl     = '56'
                number = '855'
                row    = 0
              IMPORTING
                return = wa_bapiret2.
            MOVE-CORRESPONDING wa_bapiret2 TO wa_t_ptrv_post_result.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDAT.
    APPEND t_ptrv_post_result.
    IF NOT wa_t_ptrv_post_result-message IS INITIAL.
      APPEND wa_t_ptrv_post_result TO t_ptrv_post_result.
    ENDIF.

  ENDLOOP.

  CLEAR: post_result,
         ptrv_rot_ep.
  REFRESH: post_result,
           ptrv_rot_ep.

ENDFUNCTION.