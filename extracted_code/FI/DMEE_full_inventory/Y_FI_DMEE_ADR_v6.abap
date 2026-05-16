FUNCTION y_fi_dmee_adr.
*"----------------------------------------------------------------------
*"*"Local Interface:
*"  IMPORTING
*"     VALUE(I_TREE_TYPE) TYPE  DMEE_TREETYPE_ABA
*"     VALUE(I_TREE_ID) TYPE  DMEE_TREEID_ABA
*"     VALUE(I_ITEM)
*"     VALUE(I_PARAM)
*"     VALUE(I_UPARAM)
*"     REFERENCE(I_EXTENSION) TYPE  DMEE_EXIT_INTERFACE_ABA
*"  EXPORTING
*"     REFERENCE(O_VALUE)
*"     REFERENCE(C_VALUE)
*"     REFERENCE(N_VALUE)
*"     REFERENCE(P_VALUE)
*"  TABLES
*"      I_TAB
*"----------------------------------------------------------------------
* V001 SEPA structured address — handles Cdtr (vendor/employee) + Dbtr.
*
* Context detection: walks 2 hops up via PARENT_ID to find Cdtr/Dbtr.
*
* Cdtr branch — employee detection by PA0006 existence:
*   UNESCO uses LIFNR = PERNR (NUMC8) for employees regardless of KTOKK
*   (verified examples: SCSA / UNES / INDV / ICVS — all may match a PERNR).
*   So we cast LIFNR → PERNR and try to read PA0006 SUBTY='1' first.
*
*   PA0006 SUBTY='1' found → EMPLOYEE — use PA0006 (real home address).
*   PA0006 not found → EXTERNAL VENDOR — use ADRC of vendor.
*
* Dbtr branch — paying-co (T001 lookup, unchanged):
*   T001-ADRNR by FPAYH-ZBUKR → ADRC (current valid date record).

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.
  DATA: lv_adrnr            TYPE adrnr,
        lv_parent_id_2      TYPE dmee_nodeid_aba,
        lv_grandparent_tech TYPE dmee_tech_name_aba,
        lv_pernr            TYPE pernr_d,
        ls_pa0006           TYPE pa0006.

  CLEAR: o_value, c_value, n_value, p_value.

  ASSIGN i_item TO <fs_item>.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " ── Walk 2 hops up via DMEE_TREE_NODE.PARENT_ID ───────────────────
  SELECT SINGLE parent_id
    FROM dmee_tree_node INTO lv_parent_id_2
    WHERE tree_type = i_tree_type
      AND tree_id   = i_tree_id
      AND node_id   = i_extension-node-parent_id.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.
  SELECT SINGLE tech_name
    FROM dmee_tree_node INTO lv_grandparent_tech
    WHERE tree_type = i_tree_type
      AND tree_id   = i_tree_id
      AND node_id   = lv_parent_id_2.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " ── Branch by Cdtr / Dbtr context ──────────────────────────────────
  CASE lv_grandparent_tech.

* ════════════════════════════════════════════════════════════════════
* Cdtr branch — PA0006-first detection
* ════════════════════════════════════════════════════════════════════
    WHEN 'Cdtr'.

      " Try PA0006 SUBTY='1' first — works for SCSA / UNES / INDV / ICVS
      " whenever LIFNR (cast NUMC8) corresponds to a UNESCO PERNR.
      lv_pernr = <fs_item>-fpayh-gpa1r.   " auto-cast C(10) → NUMC(8)

      SELECT SINGLE * FROM pa0006 INTO ls_pa0006
        WHERE pernr = lv_pernr
          AND subty = '1'
          AND endda >= sy-datlo
          AND begda <= sy-datlo.

      IF sy-subrc = 0.
        " ── EMPLOYEE: PA0006 (HR home address) ─────────────────────
        CASE i_extension-node-tech_name.
          WHEN 'Nm'.            c_value = <fs_item>-fpayh-znme1.
          WHEN 'StrtNm'.        c_value = ls_pa0006-stras.
          WHEN 'BldgNb'.        CLEAR c_value.   " STRAS includes house num
          WHEN 'PstCd'.         c_value = ls_pa0006-pstlz.
          WHEN 'TwnNm'.         c_value = ls_pa0006-ort01.
          WHEN 'Ctry'.          c_value = ls_pa0006-land1.
          WHEN 'CtrySubDvsn'.   c_value = ls_pa0006-state.
          WHEN 'Dept'.          CLEAR c_value.
          WHEN 'SubDept'.       CLEAR c_value.
          WHEN OTHERS.          RETURN.
        ENDCASE.
        o_value = c_value.
        RETURN.
      ENDIF.

      " ── EXTERNAL VENDOR: use ADRC of vendor ────────────────────────
      lv_adrnr = <fs_item>-fpayh-zadnr.

* ════════════════════════════════════════════════════════════════════
* Dbtr branch — paying-co (T001 lookup)
* ════════════════════════════════════════════════════════════════════
    WHEN 'Dbtr'.
      IF <fs_item>-fpayh-zbukr IS INITIAL.
        RETURN.
      ENDIF.
      SELECT SINGLE adrnr FROM t001 INTO lv_adrnr
        WHERE bukrs = <fs_item>-fpayh-zbukr.

    WHEN OTHERS.
      RETURN.
  ENDCASE.

  IF lv_adrnr IS INITIAL.
    RETURN.
  ENDIF.

  " ── Read ADRC (current valid record) ─────────────────────────────
  SELECT SINGLE name1, street, house_num1, post_code1,
                city1, country, region
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " ── Dispatch by leaf TECH_NAME (external Cdtr + Dbtr) ────────────
  CASE i_extension-node-tech_name.
    WHEN 'Nm'.            c_value = ls_adrc-name1.
    WHEN 'StrtNm'.        c_value = ls_adrc-street.
    WHEN 'BldgNb'.        c_value = ls_adrc-house_num1.
    WHEN 'PstCd'.         c_value = ls_adrc-post_code1.
    WHEN 'TwnNm'.         c_value = ls_adrc-city1.
    WHEN 'Ctry'.          c_value = ls_adrc-country.
    WHEN 'CtrySubDvsn'.   c_value = ls_adrc-region.
    WHEN 'Dept'.          c_value = ''.
    WHEN 'SubDept'.       c_value = ''.
    WHEN OTHERS.          RETURN.
  ENDCASE.

  o_value = c_value.

ENDFUNCTION.
