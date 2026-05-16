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
* V001 SEPA structured address — handles BOTH Cdtr (vendor) AND Dbtr (paying co)
* Context detection: walks 2 hops up the DMEE tree via PARENT_ID to find
* the 'Cdtr' or 'Dbtr' container.
*
* ADRNR resolution by context:
*   Cdtr (vendor)     <- FPAYH-ZADNR (already populated by LDB FPMF)
*   Dbtr (paying co)  <- T001-ADRNR  (lookup by FPAYH-ZBUKR)
*
* Mapping (same for both):
*   Nm           <- ADRC-NAME1
*   StrtNm       <- ADRC-STREET
*   BldgNb       <- ADRC-HOUSE_NUM1
*   PstCd        <- ADRC-POST_CODE1
*   TwnNm        <- ADRC-CITY1
*   Ctry         <- ADRC-COUNTRY
*   CtrySubDvsn  <- ADRC-REGION
*   Dept/SubDept <- '' (Treasury decision pending; suppress via condition)

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.
  DATA: lv_adrnr            TYPE adrnr,
        lv_parent_id_2      TYPE dmee_nodeid_aba,
        lv_grandparent_tech TYPE dmee_tech_name_aba.

  CLEAR: o_value, c_value, n_value, p_value.

  ASSIGN i_item TO <fs_item>.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " ── Walk 2 hops up to find Cdtr / Dbtr container ──────────────────
  " For leaf X under <Cdtr|Dbtr><PstlAdr><X>:
  "   parent  = PstlAdr           (i_extension-node-parent_id)
  "   grandpa = Cdtr or Dbtr      (need 1 more SELECT)
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

  " ── Resolve ADRNR by context ──────────────────────────────────────
  CASE lv_grandparent_tech.
    WHEN 'Cdtr'.
      " vendor address — FPAYH-ZADNR already carries the vendor's ADRNR
      lv_adrnr = <fs_item>-fpayh-zadnr.
    WHEN 'Dbtr'.
      " paying-co address — resolve via T001 by ZBUKR
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

  " ── Read address from ADRC (current valid record) ─────────────────
  SELECT SINGLE name1, street, house_num1, post_code1,
                city1, country, region
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " ── Dispatch by leaf TECH_NAME ────────────────────────────────────
  CASE i_extension-node-tech_name.
    WHEN 'Nm'.
      c_value = ls_adrc-name1.
    WHEN 'StrtNm'.
      c_value = ls_adrc-street.
    WHEN 'BldgNb'.
      c_value = ls_adrc-house_num1.
    WHEN 'PstCd'.
      c_value = ls_adrc-post_code1.
    WHEN 'TwnNm'.
      c_value = ls_adrc-city1.
    WHEN 'Ctry'.
      c_value = ls_adrc-country.
    WHEN 'CtrySubDvsn'.
      c_value = ls_adrc-region.
    WHEN 'Dept'.
      c_value = ''.
    WHEN 'SubDept'.
      c_value = ''.
    WHEN OTHERS.
      RETURN.
  ENDCASE.

  o_value = c_value.

ENDFUNCTION.
