METHOD valuehelp_get_entityset.

  DATA ls_filter TYPE /iwbep/s_mgw_select_option.
  DATA ls_select TYPE /iwbep/s_cod_select_option.
  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA ls_help_values TYPE cl_hcmfab_persinfo_feeder=>ty_s_help_values.
  DATA lt_fieldnames TYPE hcmfab_t_pers_fieldname.
  DATA ls_fieldname TYPE hcmfab_s_pers_fieldname.
  DATA lv_mapped_fieldnames TYPE string.
  DATA lo_filter TYPE REF TO /iwbep/if_mgw_req_filter.
  DATA lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA lt_field_values TYPE cl_hcmfab_persinfo_feeder=>ty_t_fieldvalue.
  DATA ls_field_value TYPE cl_hcmfab_persinfo_feeder=>ty_s_fieldvalue.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_mapping TYPE STANDARD TABLE OF string.
  DATA lv_vh_fieldname TYPE fieldname.
  DATA lv_ui_fieldname TYPE fieldname.

  FIELD-SYMBOLS <ls_mapping> TYPE string.
  FIELD-SYMBOLS <ls_field_value> TYPE cl_hcmfab_persinfo_feeder=>ty_s_fieldvalue.

  IF ls_pskey IS INITIAL.
    ls_pskey = get_pskey_from_filter( io_tech_request_context = io_tech_request_context ).
  ENDIF.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

* get filter values
  LOOP AT lt_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
* retrieve UI values of dependent fields
    IF ls_filter-property CS 'HCMFAB_'.
      CONTINUE. "exclude fields from PSKEY which might be set via filter, too
    ENDIF.
    IF ls_filter-property = 'FIELDNAME'.
      ls_fieldname-fieldname = ls_select-low.
      APPEND ls_fieldname TO lt_fieldnames.
      CONTINUE.
    ENDIF.
    IF ls_filter-property = 'MAPPED_FIELDNAMES'.
      lv_mapped_fieldnames = ls_select-low.
      CONTINUE.
    ENDIF.
    IF ls_filter-property = 'IS_SEARCHHELP'.
      CONTINUE. "we don't need this property here
    ENDIF.
    ls_field_value-fieldname = ls_filter-property.
    ls_field_value-fieldvalue = ls_select-low.
    APPEND ls_field_value TO lt_field_values.

  ENDLOOP.

  SPLIT lv_mapped_fieldnames AT ';' INTO TABLE lt_mapping.

  LOOP AT lt_mapping ASSIGNING <ls_mapping>.
    CLEAR lv_vh_fieldname.
    CLEAR lv_ui_fieldname.
    SPLIT <ls_mapping> AT '=' INTO lv_vh_fieldname lv_ui_fieldname.
    IF lv_vh_fieldname IS INITIAL OR lv_ui_fieldname IS INITIAL.
      CONTINUE.
    ENDIF.
    READ TABLE lt_field_values WITH KEY fieldname = lv_vh_fieldname ASSIGNING <ls_field_value>.
    IF sy-subrc EQ 0.
      <ls_field_value>-fieldname = lv_ui_fieldname.
    ENDIF.
  ENDLOOP.

  IF lt_fieldnames IS INITIAL.
* call BAdI to retrieve valuehelp fieldnames corresponding to value help entity
    GET BADI lo_persinfo_config_badi
      FILTERS
        versionid = iv_versionid.

    CALL BADI lo_persinfo_config_badi->get_valuehelp_fields
      EXPORTING
        iv_app_id           = iv_app_id
        iv_entity_name      = iv_entity_name
        iv_subty            = ls_pskey-hcmfab_subty
      CHANGING
        ct_valuehelp_fields = lt_fieldnames.

  ENDIF.

  lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = ls_pskey-hcmfab_pernr iv_infty = ls_pskey-hcmfab_infty ).

  lo_feeder->get_value_help_set(
    EXPORTING
      is_pskey                = ls_pskey
      iv_versionid            = iv_versionid
      it_fieldnames           = lt_fieldnames
      it_changed_field_values = lt_field_values
    IMPORTING
      es_help_values          = ls_help_values ).

  convert_f4_to_valuehelp(
   EXPORTING
     is_pskey            = ls_pskey
     is_help_values      = ls_help_values
     iv_entity_name      = iv_entity_name
   IMPORTING
     et_valuehelp = et_entityset ).


ENDMETHOD.
