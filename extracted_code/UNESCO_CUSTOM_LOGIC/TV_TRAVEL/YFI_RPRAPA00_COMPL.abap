*&---------------------------------------------------------------------*
*& Report YFI_RPRAPA00_COMPL
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT yfi_rprapa00_compl.

TABLES pernr.

DATA lo_praa_bl TYPE REF TO ycl_fi_praa_bl.
DATA lt_pernr TYPE TABLE OF p_pernr.
DATA lv_title TYPE lvc_title.

PARAMETERS p_bank RADIOBUTTON GROUP r001 DEFAULT 'X' USER-COMMAND r01.
SELECTION-SCREEN BEGIN OF LINE.
PARAMETERS p_ccode RADIOBUTTON GROUP r001.
SELECTION-SCREEN COMMENT 3(31) TEXT-c01 FOR FIELD p_ccode.
PARAMETERS p_bukrs TYPE bukrs MODIF ID buk OBLIGATORY DEFAULT 'UNES'.
SELECTION-SCREEN END OF LINE.
PARAMETERS p_date TYPE datum OBLIGATORY.
PARAMETERS p_nomod AS CHECKBOX.
PARAMETERS p_file TYPE rfbifile OBLIGATORY.
PARAMETERS p_group TYPE apq_grpn DEFAULT 'PRAA_BANK' OBLIGATORY.
PARAMETERS p_update AS CHECKBOX.

INITIALIZATION.
  pnptimed = 'D'.
  p_date = sy-datum - 1.
  p_file = '\\hq-sapitf\itf\<FOLDER>\PRAA\myfile'.
  IF sy-sysid <> 'P01'.
    REPLACE '<FOLDER>' IN p_file WITH '_OTHERS'.
  ELSE.
    REPLACE '<FOLDER>' IN p_file WITH '_PROD'.
  ENDIF.

AT SELECTION-SCREEN ON p_date.
  IF p_date > sy-datum.
    MESSAGE TEXT-e01 TYPE 'E'.
  ENDIF.

AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF screen-group1 = 'BUK'.
      IF p_ccode = abap_true.
        screen-input = 1.
      ELSE.
        screen-input = 0.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.

START-OF-SELECTION.

  lo_praa_bl = ycl_fi_praa_bl=>get_instance( ).

GET pernr.
  IF lo_praa_bl->is_excluded_pernr( pernr-pernr ) = abap_false.
    APPEND pernr-pernr TO lt_pernr.
  ENDIF.

END-OF-SELECTION.

  lo_praa_bl->mt_pernr = lt_pernr.
  lo_praa_bl->mv_no_modif_scan = p_nomod.
  lo_praa_bl->mv_update = p_update.

  CASE abap_true.
    WHEN p_bank.
      lo_praa_bl->get_vendor_to_modify_bank( it_bukrs_range = pnpbukrs[]
                                             iv_date_ref = pn-begda
                                             iv_date_from = p_date ).
      lo_praa_bl->update_vendor( iv_group = p_group
                                 iv_file = p_file ).
      lv_title = TEXT-t01.
    WHEN p_ccode.



      lv_title = TEXT-t02.
  ENDCASE.

  lo_praa_bl->display_alv( iv_tabname = 'MT_LIFNR_PERNR'
                           iv_title = lv_title
                           iv_label_test = TEXT-l01
                           iv_label_upd = TEXT-l02
                           iv_sort_field = 'LIFNR' ).
