METHOD define.

  DATA lo_model TYPE REF TO object.
  DATA lo_entity_type TYPE REF TO /iwbep/if_mgw_odata_entity_typ.
  DATA lo_entity_property TYPE REF TO /iwbep/if_mgw_odata_property.
  DATA lv_versionid TYPE hcmfab_versionid.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.
  DATA lt_property TYPE hcmfab_t_pers_nodename.
  DATA lv_entityname TYPE string.

  FIELD-SYMBOLS <lt_entity> TYPE /iwbep/if_mgw_med_odata_types=>ty_t_med_entity_types.
  FIELD-SYMBOLS <ls_entity> TYPE /iwbep/if_mgw_med_odata_types=>ty_s_med_entity_type.
  FIELD-SYMBOLS <ls_property> TYPE /iwbep/if_mgw_med_odata_types=>ty_s_med_property.
  FIELD-SYMBOLS <ls_property_name> TYPE hcmfab_pers_nodename.

  CREATE OBJECT lo_model TYPE ('/IWBEP/CL_MGW_ODATA_MODEL').

  lo_model ?= model.
  ASSIGN lo_model->('MT_ENTITIES') TO <lt_entity>.
  CHECK <lt_entity> IS ASSIGNED.

* disable conversion exits for entity properties given by BAdI implementations
  LOOP AT <lt_entity> ASSIGNING <ls_entity> WHERE name CP '*PersonalData*' OR name CP '*ValueHelp*'.
    lv_entityname = <ls_entity>-name.
    lv_versionid = cl_hcmfab_mypersonalda_dpc_gen=>get_versionid( lv_entityname ).
    GET BADI lo_persinfo_config_badi
      FILTERS
        versionid = lv_versionid.

    CLEAR lt_property.
    CALL BADI lo_persinfo_config_badi->get_properties_no_conversion
      EXPORTING
        iv_app_id      = if_hcmfab_constants=>gc_application_id-mypersonaldata
        iv_entity_name = lv_entityname
      CHANGING
        ct_property    = lt_property.

* disable output conversion for given properties
    lo_entity_type = model->get_entity_type( <ls_entity>-name ).
    IF lo_entity_type IS BOUND.
      LOOP AT lt_property ASSIGNING <ls_property_name>.
        lo_entity_property = lo_entity_type->get_property( iv_property_name = <ls_property_name> ).
        IF lo_entity_property IS BOUND.
* disable conversion exit
          lo_entity_property->disable_conversion( ).
        ENDIF.
      ENDLOOP.
    ENDIF.
  ENDLOOP.

ENDMETHOD.
