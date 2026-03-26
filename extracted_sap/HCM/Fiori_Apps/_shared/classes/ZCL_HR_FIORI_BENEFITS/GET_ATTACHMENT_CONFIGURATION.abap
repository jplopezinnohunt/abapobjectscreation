  METHOD GET_ATTACHMENT_CONFIGURATION.

    CONSTANTS: lc_infty_0962 TYPE subty VALUE '0962'.

    DATA: lv_where_condition TYPE string,
          ls_config          TYPE zthrfiori_att_cf,
          ls_attach_config   TYPE zshrfiori_attachment_config,
          ls_t530f           TYPE t530f,
          ls_dd07v           TYPE dd07v,
          ls_attach_type     TYPE zthrfiori_att_ty,
          lt_config          TYPE STANDARD TABLE OF zthrfiori_att_cf,
          lt_attach_config   TYPE STANDARD TABLE OF zshrfiori_attachment_config,
          lt_t530f           TYPE STANDARD TABLE OF t530f,
          lt_dd07v           TYPE STANDARD TABLE OF dd07v,
          lt_attach_type     TYPE STANDARD TABLE OF zthrfiori_att_ty.

    FIELD-SYMBOLS: <fs_attach_config> TYPE zshrfiori_attachment_config.

*   Construct WHERE condition for query
    CONCATENATE ' request_type = '''  iv_request_type ''''
      INTO lv_where_condition ##NO_TEXT.
    IF iv_attach_type IS NOT INITIAL.
      CONCATENATE lv_where_condition ' AND attach_type = ''' iv_attach_type ''''
        INTO lv_where_condition ##NO_TEXT.
    ENDIF.
    IF iv_eg_att_part IS NOT INITIAL.
      CONCATENATE lv_where_condition ' AND eg_att_part = ''' iv_eg_att_part ''''
        INTO lv_where_condition ##NO_TEXT.
    ENDIF.
    IF iv_rs_reason IS NOT INITIAL.
      CONCATENATE lv_where_condition ' AND rs_reason = ''' iv_rs_reason ''''
        INTO lv_where_condition ##NO_TEXT.
    ENDIF.

*   Get attachment configuration  for related request type
    SELECT * INTO  TABLE lt_config
      FROM zthrfiori_att_cf
        WHERE (lv_where_condition).

*   Get additional information
    SELECT * INTO TABLE lt_t530f
      FROM t530f
        WHERE sprsl = sy-langu
          AND infty = lc_infty_0962.
    SORT lt_t530f BY preas ASCENDING.

    SELECT * INTO TABLE lt_attach_type
      FROM zthrfiori_att_ty
        WHERE language = sy-langu.
    SORT lt_attach_type BY attach_type ASCENDING.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'ZD_HRFIORI_EG_ATTACH_PART'
        text      = abap_true
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.
    SORT lt_dd07v BY domvalue_l ASCENDING.

    LOOP AT lt_config INTO ls_config.
      MOVE-CORRESPONDING ls_config TO ls_attach_config.
      APPEND ls_attach_config TO lt_attach_config.
    ENDLOOP.

*   Complete the structure (texts)
    LOOP AT lt_attach_config ASSIGNING <fs_attach_config>.
      CLEAR: ls_t530f, ls_attach_type, ls_dd07v.

      READ TABLE lt_t530f INTO ls_t530f WITH KEY  preas = <fs_attach_config>-rs_reason.
      <fs_attach_config>-rs_reason_txt = ls_t530f-rtext.

      READ TABLE lt_attach_type INTO ls_attach_type WITH KEY attach_type = <fs_attach_config>-attach_type.
      <fs_attach_config>-attach_type_txt = ls_attach_type-attach_type_txt.

      READ TABLE lt_dd07v INTO ls_dd07v WITH KEY domvalue_l = <fs_attach_config>-eg_att_part ##WARN_OK.
      <fs_attach_config>-eg_att_part_txt = ls_dd07v-ddtext.
    ENDLOOP.

    ot_attach_config[] = lt_attach_config[].

  ENDMETHOD.
