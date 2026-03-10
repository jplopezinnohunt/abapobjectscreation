METHOD get_validity_info.

  DATA lt_validity_info_xss TYPE if_hrpa_pernr_infty_xss_ext=>tt_validity_info.

  FIELD-SYMBOLS <ls_validity_info_xss> TYPE if_hrpa_pernr_infty_xss_ext=>ts_validity_info.
  FIELD-SYMBOLS <ls_validity_info> TYPE hcmfab_s_pers_validity.


  CLEAR et_validity_info.

  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_validity_info
    EXPORTING
      iv_object_key    = iv_object_key
      iv_create_mode   = iv_is_create_mode
    IMPORTING
      et_validity_info = lt_validity_info_xss.

  LOOP AT lt_validity_info_xss ASSIGNING <ls_validity_info_xss>.
    APPEND INITIAL LINE TO et_validity_info ASSIGNING <ls_validity_info>.
    MOVE-CORRESPONDING is_pskey TO <ls_validity_info>.
    <ls_validity_info>-begda = <ls_validity_info_xss>-begda.
    <ls_validity_info>-endda = <ls_validity_info_xss>-endda.
    <ls_validity_info>-selected = <ls_validity_info_xss>-selected.
    IF <ls_validity_info_xss>-begda_show = abap_true AND <ls_validity_info_xss>-endda_show = abap_true.
* from <begda> to <endda>
      <ls_validity_info>-validity_type = gc_validity_type-type_from_to.
      CONTINUE.
    ENDIF.
    IF <ls_validity_info_xss>-begda_show = abap_false AND <ls_validity_info_xss>-endda_show = abap_true.
* to <endda>
      <ls_validity_info>-validity_type = gc_validity_type-type_to.
      CONTINUE.
    ENDIF.
    IF <ls_validity_info_xss>-begda_show = abap_true AND <ls_validity_info_xss>-endda_show = abap_false.
* from <begda>
      <ls_validity_info>-validity_type = gc_validity_type-type_from.
      CONTINUE.
    ENDIF.
    IF <ls_validity_info_xss>-begda_show = abap_false AND <ls_validity_info_xss>-endda_show = abap_false.
*  from today
      <ls_validity_info>-validity_type = gc_validity_type-type_today.
      CONTINUE.
    ENDIF.
  ENDLOOP.

ENDMETHOD.
