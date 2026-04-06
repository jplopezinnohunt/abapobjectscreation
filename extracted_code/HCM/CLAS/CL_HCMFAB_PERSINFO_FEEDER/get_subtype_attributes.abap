METHOD get_subtype_attributes.

  DATA lt_subty_metadata TYPE if_hrpa_pernr_infty_xss=>subty_metadata_tab.
  DATA lr_ui_structure_tab TYPE REF TO data.
  DATA lv_methodname TYPE seocpdname VALUE 'IF_HRPA_PERNR_INFTY_XSS_EXT~IS_CREATE_ALLOWED'.

  FIELD-SYMBOLS <ls_subty_metadata> TYPE if_hrpa_pernr_infty_xss=>subty_metadata.
  FIELD-SYMBOLS <ls_subtype_attributes> TYPE hcmfab_s_pers_subtypeattribs.
  FIELD-SYMBOLS <lt_ui_structure> TYPE ANY TABLE.


  CLEAR et_subtype_attributes.

  CREATE DATA lr_ui_structure_tab TYPE TABLE OF (mv_xx_structure_name).
  ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

* Initialize container buffers
  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
    IMPORTING
      main_records = <lt_ui_structure>.

  TRY.
      CALL METHOD mo_xss_adapter->read_metadata
        IMPORTING
          metadata_tab = lt_subty_metadata.

    CATCH cx_hrpa_violated_assertion.
      CLEAR lt_subty_metadata.
  ENDTRY.

  LOOP AT lt_subty_metadata ASSIGNING <ls_subty_metadata>.

    APPEND INITIAL LINE TO et_subtype_attributes ASSIGNING <ls_subtype_attributes>.
    <ls_subtype_attributes>-pernr = mv_pernr.
    <ls_subtype_attributes>-infty = mv_infty.
    <ls_subtype_attributes>-subty = <ls_subty_metadata>-subty.
    <ls_subtype_attributes>-stext = <ls_subty_metadata>-subtytxt.
    <ls_subtype_attributes>-default_begda = <ls_subty_metadata>-default_begda.

    IF <ls_subty_metadata>-granularity = 'S' OR <ls_subty_metadata>-granularity = 'O'. "2728534
      <ls_subtype_attributes>-has_subtypes = abap_true.
    ENDIF.

    IF <ls_subty_metadata>-disp_only = abap_true.           "2664785
      <ls_subtype_attributes>-is_creatable = abap_false.
    ELSE.
*    <ls_subtype_attributes>-is_creatable = <ls_subty_metadata>-cre_button.
* we cannot use attribute CRE_BUTTON: it's always 'false' ...

* Unfortunately the interface of method IF_HRPA_PERNR_INFTY_XSS_EXT~IS_CREATE_ALLOWED
* was changed with EHIK071925 ...
      TRY.
          CALL METHOD mo_xss_adapter->(lv_methodname)
            EXPORTING
              iv_subty  = <ls_subty_metadata>-subty
            RECEIVING
              rv_create = <ls_subtype_attributes>-is_creatable.

        CATCH cx_sy_dyn_call_error.

          CALL METHOD mo_xss_adapter->(lv_methodname)
            EXPORTING
              iv_subty  = <ls_subty_metadata>-subty
            IMPORTING
              ev_create = <ls_subtype_attributes>-is_creatable.
      ENDTRY.

    ENDIF.

  ENDLOOP.

ENDMETHOD.
