METHOD infotype_get_expand_entityset.

  DATA lt_valuehelp_fields TYPE hcmfab_t_pers_fieldname.
  DATA lt_fieldmetadata TYPE cl_hcmfab_persinfo_feeder=>ty_t_fieldmetadata.
  DATA lt_help_values TYPE cl_hcmfab_persinfo_feeder=>ty_t_help_values.
  DATA lt_validity_info TYPE cl_hcmfab_persinfo_feeder=>ty_t_validity_info.
  DATA lt_children TYPE /iwbep/if_mgw_odata_expand=>ty_t_node_children.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA ls_navprop_vhfieldname TYPE if_ex_hcmfab_persinfo_config=>ty_s_navprop_vh_field.
  DATA lt_navprop_vhfieldname TYPE if_ex_hcmfab_persinfo_config=>ty_t_navprop_vh_field.

  FIELD-SYMBOLS <ls_child> TYPE /iwbep/if_mgw_odata_expand=>ty_s_node_child.
  FIELD-SYMBOLS <ls_expanded_entity> TYPE any.
  FIELD-SYMBOLS <lt_expanded_entity> TYPE STANDARD TABLE.

  lt_children = io_expand->get_children( ).
  CHECK NOT lt_children IS INITIAL.
* in case we don't have any children to expand to we will not proceed here
* as otherwise it may result in a dump ...

  LOOP AT lt_children ASSIGNING <ls_child>.
    IF <ls_child>-tech_nav_prop_name CS 'VALUEHELP'.
      ls_navprop_vhfieldname-nav_property = <ls_child>-tech_nav_prop_name.
      APPEND ls_navprop_vhfieldname TO lt_navprop_vhfieldname.
      CLEAR ls_navprop_vhfieldname.
    ENDIF.
  ENDLOOP.

  ASSIGN er_entityset->* TO <lt_expanded_entity>.

  IF NOT lt_navprop_vhfieldname IS INITIAL.
* call BAdI to retrieve valuehelp fieldnames corresponding to navigation path
    GET BADI lo_persinfo_config_badi
      FILTERS
        versionid = iv_versionid.

    CALL BADI lo_persinfo_config_badi->get_valuehelp_fields
      EXPORTING
        iv_app_id           = iv_app_id
      CHANGING
        ct_valuehelp_fields = lt_valuehelp_fields
        ct_navprop_vh_field = lt_navprop_vhfieldname.

  ENDIF.

  IF io_tech_request_context->get_entity_type_name( ) CP '*Default'.

    infotype_default_get_entityset(
      EXPORTING
        iv_app_id                = iv_app_id
        iv_infty                 = iv_infty
        iv_versionid             = iv_versionid
        it_fieldnames            = lt_valuehelp_fields
        io_context               = io_context
        io_tech_request_context  = io_tech_request_context
      IMPORTING
        et_entityset             = <lt_expanded_entity>
        et_field_metadata        = lt_fieldmetadata
        et_help_values           = lt_help_values
        et_validity_info         = lt_validity_info
        es_response_context      = es_response_context ).


  ELSE.

    infotype_get_entityset(
      EXPORTING
        iv_app_id                = iv_app_id
        iv_infty                 = iv_infty
        iv_versionid             = iv_versionid
        it_fieldnames            = lt_valuehelp_fields
        io_context               = io_context
        io_tech_request_context  = io_tech_request_context
      IMPORTING
        et_entityset             = <lt_expanded_entity>
        et_field_metadata        = lt_fieldmetadata
        et_help_values           = lt_help_values
        et_validity_info         = lt_validity_info
        es_response_context      = es_response_context ).

  ENDIF.

  LOOP AT <lt_expanded_entity> ASSIGNING <ls_expanded_entity>.

    build_expanded_entity(
      EXPORTING
        is_entity                = <ls_expanded_entity>
        it_fieldmetadata         = lt_fieldmetadata
        it_help_values           = lt_help_values
        it_validity_info         = lt_validity_info
        it_navprop_vhfield       = lt_navprop_vhfieldname
      IMPORTING
        es_expanded_entity       = <ls_expanded_entity>
      CHANGING
        ct_expanded_tech_clauses = et_expanded_tech_clauses
      ).

  ENDLOOP.

  SORT et_expanded_tech_clauses.
  DELETE ADJACENT DUPLICATES FROM et_expanded_tech_clauses.

ENDMETHOD.
