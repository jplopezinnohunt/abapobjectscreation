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
* Cdtr branch — address source by KTOKK (vendor account group):
*
*   KTOKK = 'SCSA' (Staff payroll)
*     ADRC.STREET = department code (not a real address)
*     → Read PA0006 SUBTY='1' (HR Address Infotype, permanent home)
*     → PERNR = LIFNR auto-cast C(10) → NUMC(8) (e.g. 0010199971 → 10199971)
*     → StrtNm = STRAS (already includes house number, e.g. "7, rue des Richardes")
*     → BldgNb = blank (STRAS not split)
*     → PstCd = PSTLZ.  TwnNm = ORT01.  Ctry = LAND1.  CtrySubDvsn = STATE.
*
*   KTOKK = 'INDV' (Individual personal record)
*     ADRC.STREET = real personal/home street
*     → Read ADRC of vendor (ADRNR from FPAYH-ZADNR)
*
*   KTOKK = 'UNES' (UNESCO HQ vendor link)
*     ADRC.STREET = "PLACE FONTENOY" (UNESCO HQ)
*     → Read ADRC of vendor
*
*   KTOKK = 'ICVS' (Inter-Company Vendor / Special)
*     ADRC.STREET = real address (e.g. "1, rue Miollis")
*     → Read ADRC of vendor
*
*   KTOKK = (other / external)
*     ADRC.STREET = real street from supplier master
*     → Read ADRC of vendor
*
* Dbtr branch — paying-co (T001 lookup, unchanged from v4):
*   T001-ADRNR by FPAYH-ZBUKR → ADRC (current valid date record)

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.
  DATA: lv_adrnr            TYPE adrnr,
        lv_parent_id_2      TYPE dmee_nodeid_aba,
        lv_grandparent_tech TYPE dmee_tech_name_aba,
        lv_ktokk            TYPE ktokk,
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
* Cdtr branch — explicit dispatch by vendor account group (KTOKK)
* ════════════════════════════════════════════════════════════════════
    WHEN 'Cdtr'.

      SELECT SINGLE ktokk FROM lfa1 INTO lv_ktokk
        WHERE lifnr = <fs_item>-fpayh-gpa1r.
      IF sy-subrc <> 0.
        RETURN.
      ENDIF.

      CASE lv_ktokk.

* ─── Staff (employee) — PA0006 lookup ──────────────────────────────
        WHEN 'SCSA'.
          lv_pernr = <fs_item>-fpayh-gpa1r.   " C(10) → NUMC(8)

          SELECT SINGLE * FROM pa0006 INTO ls_pa0006
            WHERE pernr = lv_pernr
              AND subty = '1'
              AND endda >= sy-datlo
              AND begda <= sy-datlo.
          IF sy-subrc = 0.
            CASE i_extension-node-tech_name.
              WHEN 'Nm'.            c_value = <fs_item>-fpayh-znme1.
              WHEN 'StrtNm'.        c_value = ls_pa0006-stras.
              WHEN 'BldgNb'.        CLEAR c_value.
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
          " Fall through to ADRC if PA0006 sub1 not found
          lv_adrnr = <fs_item>-fpayh-zadnr.

* ─── Individual / UNESCO HQ / Inter-Company / External vendors ─────
* All read ADRC of vendor (ADRNR populated by LDB FPMF in FPAYH-ZADNR).
* The address contents differ but the *path* is the same.
        WHEN 'INDV'.
          lv_adrnr = <fs_item>-fpayh-zadnr.

        WHEN 'UNES'.
          lv_adrnr = <fs_item>-fpayh-zadnr.

        WHEN 'ICVS'.
          lv_adrnr = <fs_item>-fpayh-zadnr.

        WHEN OTHERS.
          " External supplier or any other account group
          lv_adrnr = <fs_item>-fpayh-zadnr.
      ENDCASE.

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

  " ── Dispatch by leaf TECH_NAME (Cdtr non-SCSA + Dbtr) ────────────
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
