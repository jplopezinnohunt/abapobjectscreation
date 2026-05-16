*&---------------------------------------------------------------------*
*& Function Module: Y_FI_DMEE_ADR
*& Function Group:  YFPAYM
*& Package:         YA
*& Short text:      DMEE: Dbtr PstlAdr structured from ADRC
*&
*& Purpose: Custom EXIT_FUNC for DMEE leaves under <PmtInf><Dbtr><PstlAdr>
*&          in /SEPA_CT_UNES V001 (and any other format that needs paying-co
*&          structured-address). Reads paying-co address dynamically from
*&          T001(BUKRS).ADRNR -> ADRC, dispatching by leaf TECH_NAME.
*&
*& Why: SEPA_CT format does NOT allow Event 05 in OBPM3 (validation rejects
*&      "Enter a valid value"), so FPAYHX-REF01/REF06 byte buffers are never
*&      populated, and the SAP-std FALLBACK BAdI WHEN clauses for
*&      <PmtInf><Dbtr><PstlAdr><StrtNm/BldgNb/PstCd/TwnNm> always return blank.
*&      This Z-FM bypasses the BAdI/REF01 chain and reads ADRC directly per
*&      leaf, returning the right field via CASE on i_extension-node-name.
*&
*& Used in: /SEPA_CT_UNES V001 — leaves StrtNm (N_1215903670),
*&                                       BldgNb (N_1396453300),
*&                                       PstCd  (N_2703639030),
*&                                       TwnNm  (N_7609981350)
*&          MP_EXIT_FUNC = Y_FI_DMEE_ADR (in DMEE Tx Attributes tab)
*&
*& Author: JP_LOPEZ (Pablo)
*& Reviewer: N_MENARD
*&---------------------------------------------------------------------*

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

  FIELD-SYMBOLS: <fs_item> TYPE dmee_paym_if_type.

  CLEAR: o_value, c_value, n_value, p_value.

  ASSIGN i_item TO <fs_item>.
  IF sy-subrc <> 0 OR <fs_item>-fpayh-zbukr IS INITIAL.
    RETURN.
  ENDIF.

  " Resolve paying-co ADRNR via T001
  SELECT SINGLE adrnr
    FROM t001 INTO @DATA(lv_adrnr)
    WHERE bukrs = @<fs_item>-fpayh-zbukr.
  IF sy-subrc <> 0 OR lv_adrnr IS INITIAL.
    RETURN.
  ENDIF.

  " Read paying-co address from ADRC (current valid record)
  SELECT SINGLE street, house_num1, post_code1, city1
    FROM adrc INTO @DATA(ls_adrc)
    WHERE addrnumber = @lv_adrnr
      AND date_from <= @sy-datlo
      AND date_to   >= @sy-datlo.
  IF sy-subrc <> 0.
    RETURN.
  ENDIF.

  " Dispatch by leaf TECH_NAME
  CASE i_extension-node-tech_name.
    WHEN 'StrtNm'.
      c_value = ls_adrc-street.
    WHEN 'BldgNb'.
      c_value = ls_adrc-house_num1.
    WHEN 'PstCd'.
      c_value = ls_adrc-post_code1.
    WHEN 'TwnNm'.
      c_value = ls_adrc-city1.
    WHEN OTHERS.
      " Unknown leaf path -- leave c_value blank, X-flag will suppress
      RETURN.
  ENDCASE.

  o_value = c_value.

ENDFUNCTION.
