*&---------------------------------------------------------------------*
*& PROPOSED EXTENSION — YCL_IDFI_CGI_DMEE_FALLBACK_CM001  GET_CREDIT
*& Session #71  2026-05-08
*& Goal: route paying-co (Dbtr) structured-address leaves of /SEPA_CT_UNES
*&       V001 through this BAdI method, mirroring UNESCO's canonical
*&       FI_CGI_DMEE_EXIT_W_BADI pattern already used in /CGI_XML_CT_UNESCO
*&       Dbtr leaves (P01 production V000).
*&
*& Source of truth for runtime address: T001(BUKRS=i_fpayh-zbukr).ADRNR -> ADRC.
*& Verified ADRNR for BUKRS=UNES via Gold DB ADRC: 21984 / 21985 / 22029
*& (all "UNESCO" / "Place de Fontenoy" / "7" / "75007" / "PARIS" / "FR")
*&
*& Reviewer: N_MENARD (per matrix row 26 BAdI Pattern A precedent)
*& Transport: D01-V001-SEPA-BADI-01  (separate from D01-V001-SEPA-01 DMEE config
*&            so config can be released ahead of code if needed)
*&---------------------------------------------------------------------*
  METHOD get_credit.
******* Put here tag redefinition for FALLBACK class (general case)
******* For country specific redefinition tag, use DMEE VGI country BADI
    CASE i_node_path.
*      WHEN '<PmtInf><CdtTrfTxInf><CdtrAgt><FinInstnId><ClrSysMmbId><MmbId>'.
**       this node holds the value of the Clearing system member ID
*        IF i_fpayh-zbnkl IS NOT INITIAL.
*          c_value = i_fpayh-zbnkl.
*        ELSE.
**          c_value = i_fpayh-zbnky.
*          CLEAR c_value.
*        ENDIF.
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
        "If payment origin is TR-CM-BT, then put item text to this tag
        IF i_fpayp-origin = 'TR-CM-BT'.
          c_value = i_fpayp-sgtxt.
        ENDIF.
        "Only 35 first characters, remaining characters must be set in tag <StrtNm>
        mv_cdtr_name = c_value.
        IF c_value+35 IS NOT INITIAL.
          CLEAR c_value+35.
        ENDIF.
        mv_fpayh = i_fpayh.   "Set to buffer for tag <StrtNm>
      WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
        IF i_fpayh = mv_fpayh AND mv_cdtr_name+35 IS NOT INITIAL.
          c_value = |{ mv_cdtr_name+35 } { c_value }|.
        ENDIF.
        IF c_value+70 IS NOT INITIAL.
          CLEAR c_value+70.
        ENDIF.

*&======================================================================
*& Session #71 2026-05-08 — V001 SEPA Dbtr structured-address (CBPR+ ISO 20022)
*&======================================================================
      WHEN '<PmtInf><Dbtr><PstlAdr><StrtNm>'.
        " Pattern A guard: only override if leaf is empty (config Source
        " already attempted; if non-INITIAL keep existing value)
        IF c_value IS INITIAL.
          DATA(lv_adrnr) = VALUE adrnr( ).
          SELECT SINGLE adrnr INTO @lv_adrnr
            FROM t001
            WHERE bukrs = @i_fpayh-zbukr.
          IF lv_adrnr IS NOT INITIAL.
            DATA: ls_adrc TYPE adrc.
            SELECT SINGLE street, house_num1
              INTO @( ls_adrc-street, ls_adrc-house_num1 )
              FROM adrc
              WHERE addrnumber = @lv_adrnr
                AND date_from <= @sy-datlo
                AND date_to   >= @sy-datlo.
            CONCATENATE ls_adrc-street ls_adrc-house_num1
                   INTO c_value SEPARATED BY space.
            CONDENSE c_value.
            IF c_value+70 IS NOT INITIAL.
              CLEAR c_value+70.   " ISO XSD StrtNm maxLen=70
            ENDIF.
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><Dbtr><PstlAdr><BldgNb>'.
        " Pattern A guard
        IF c_value IS INITIAL.
          DATA(lv_adrnr2) = VALUE adrnr( ).
          SELECT SINGLE adrnr INTO @lv_adrnr2
            FROM t001
            WHERE bukrs = @i_fpayh-zbukr.
          IF lv_adrnr2 IS NOT INITIAL.
            SELECT SINGLE house_num1 INTO @c_value
              FROM adrc
              WHERE addrnumber = @lv_adrnr2
                AND date_from <= @sy-datlo
                AND date_to   >= @sy-datlo.
            IF c_value+16 IS NOT INITIAL.
              CLEAR c_value+16.   " ISO XSD BldgNb maxLen=16
            ENDIF.
          ENDIF.
        ENDIF.

      WHEN '<PmtInf><Dbtr><PstlAdr><PstCd>'.
        IF c_value IS INITIAL.
          DATA(lv_adrnr3) = VALUE adrnr( ).
          SELECT SINGLE adrnr INTO @lv_adrnr3
            FROM t001
            WHERE bukrs = @i_fpayh-zbukr.
          IF lv_adrnr3 IS NOT INITIAL.
            SELECT SINGLE post_code1 INTO @c_value
              FROM adrc
              WHERE addrnumber = @lv_adrnr3
                AND date_from <= @sy-datlo
                AND date_to   >= @sy-datlo.
            IF c_value+16 IS NOT INITIAL.
              CLEAR c_value+16.   " ISO XSD PstCd maxLen=16
            ENDIF.
          ENDIF.
        ENDIF.

    ENDCASE.
  ENDMETHOD.
