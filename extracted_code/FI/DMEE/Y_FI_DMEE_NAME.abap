FUNCTION y_fi_dmee_name.
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
* V001 name resolution — sibling to Y_FI_DMEE_ADR (address resolution).
* Handles ONE leaf: 'Nm'.
*
* Why this exit exists:
*   ADRC can split entity names across NAME1 + NAME2 when the full
*   name exceeds 40 chars. The default DMEE tree binds Nm to a single
*   field (FPAYP-NAME1 or ADRC.NAME1) and silently truncates. This
*   exit reads BOTH lines and concatenates so the XML emits the full
*   name (verified case: ADRC[451940]
*     NAME1='Commission of the Republic of'
*     NAME2='Serbia for UNESCO'
*   → c_value 'Commission of the Republic of Serbia for UNESCO').
*
* Context detection: walks 2 hops up via PARENT_ID to identify
* Cdtr / UltmtCdtr / Dbtr — mirrors Y_FI_DMEE_ADR exactly.
*
* Cdtr / UltmtCdtr branch:
*   PA0006(PERNR = FPAYH-GPA1R cast NUMC8) SUBTY='1' found → EMPLOYEE
*     → c_value = FPAYH-ZNME1 (F110-resolved name; staff names fit
*        C(40), no NAME2 split for employees).
*   PA0006 not found → EXTERNAL VENDOR
*     → ADRC(FPAYH-ZADNR).NAME1 + ' ' + NAME2 (condensed).
* Dbtr branch — paying-co:
*   T001(FPAYH-ZBUKR).ADRNR → ADRC.NAME1 + ' ' + NAME2.

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

  " This exit handles only 'Nm' — exit early on any other leaf
  IF i_extension-node-tech_name <> 'Nm'.
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

  " ── Branch by Cdtr / UltmtCdtr / Dbtr context ─────────────────────
  CASE lv_grandparent_tech.
* ════════════════════════════════════════════════════════════════════
* Dbtr branch — paying-co (T001 lookup)
* ════════════════════════════════════════════════════════════════════
    WHEN 'Dbtr'.
      IF <fs_item>-fpayh-zbukr IS INITIAL.
        RETURN.
      ENDIF.
      SELECT SINGLE adrnr FROM t001 INTO lv_adrnr
        WHERE bukrs = <fs_item>-fpayh-zbukr.

* ════════════════════════════════════════════════════════════════════
* Cdtr / UltmtCdtr branch — PA0006-first detection
* ════════════════════════════════════════════════════════════════════
    WHEN 'Cdtr' OR 'UltmtCdtr'.

      lv_pernr = <fs_item>-fpayh-gpa1r.   " auto-cast C(10) → NUMC(8)

      SELECT SINGLE * FROM pa0006 INTO ls_pa0006
        WHERE pernr = lv_pernr
          AND subty = '1'
          AND endda >= sy-datlo
          AND begda <= sy-datlo.

      IF sy-subrc = 0.
        " EMPLOYEE — use F110-resolved name (ZNME1). Staff names fit
        " in C(40), no NAME2 concat needed.
        c_value = <fs_item>-fpayh-znme1.
        o_value = c_value.
        RETURN.
      ENDIF.

      " EXTERNAL VENDOR — read ADRC of vendor (NAME1+NAME2 below)
      lv_adrnr = <fs_item>-fpayh-zadnr.

    WHEN OTHERS.
      RETURN.
  ENDCASE.

  IF lv_adrnr IS INITIAL.
    RETURN.
  ENDIF.

  " ── Read ADRC (current valid record) — NAME1 + NAME2 ──────────────
  " For Dbtr: reads Company Code address.
  " For Cdtr/UltmtCdtr (external vendor): reads vendor address (ZADNR).
  SELECT SINGLE name1, name2
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " Concatenate NAME1 + NAME2 (handles entities whose name spans two
  " ADRC lines — e.g. "Commission of the Republic of Serbia for UNESCO")
  IF ls_adrc-name2 IS NOT INITIAL.
    CONCATENATE ls_adrc-name1 ls_adrc-name2
      INTO c_value SEPARATED BY space.
  ELSE.
    c_value = ls_adrc-name1.
  ENDIF.
  CONDENSE c_value.

  o_value = c_value.

ENDFUNCTION.
