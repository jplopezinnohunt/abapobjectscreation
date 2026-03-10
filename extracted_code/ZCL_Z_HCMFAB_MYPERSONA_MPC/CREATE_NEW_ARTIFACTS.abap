  method CREATE_NEW_ARTIFACTS.
*&---------------------------------------------------------------------*
*&           Generated code for the MODEL PROVIDER BASE CLASS          &*
*&                                                                     &*
*&  !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL   &*
*&        DO THIS IN THE MODEL PROVIDER SUBCLASS!!!                    &*
*&                                                                     &*
*&---------------------------------------------------------------------*


DATA:
  lo_entity_type    TYPE REF TO /iwbep/if_mgw_odata_entity_typ,                      "#EC NEEDED
  lo_complex_type   TYPE REF TO /iwbep/if_mgw_odata_cmplx_type,                      "#EC NEEDED
  lo_property       TYPE REF TO /iwbep/if_mgw_odata_property,                        "#EC NEEDED
  lo_association    TYPE REF TO /iwbep/if_mgw_odata_assoc,                           "#EC NEEDED
  lo_assoc_set      TYPE REF TO /iwbep/if_mgw_odata_assoc_set,                       "#EC NEEDED
  lo_ref_constraint TYPE REF TO /iwbep/if_mgw_odata_ref_constr,                      "#EC NEEDED
  lo_nav_property   TYPE REF TO /iwbep/if_mgw_odata_nav_prop,                        "#EC NEEDED
  lo_action         TYPE REF TO /iwbep/if_mgw_odata_action,                          "#EC NEEDED
  lo_parameter      TYPE REF TO /iwbep/if_mgw_odata_property,                        "#EC NEEDED
  lo_entity_set     TYPE REF TO /iwbep/if_mgw_odata_entity_set.                      "#EC NEEDED


lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUN' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzsprsl_txt' iv_abap_fieldname = 'ZZSPRSL_TXT' ). "#EC NOTEXT
lo_property->set_label_from_text_element( iv_text_element_symbol = '' iv_text_element_container = gc_incl_name ).       "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUN' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzreggr_txt' iv_abap_fieldname = 'ZZREGGR_TXT' ). "#EC NOTEXT
lo_property->set_label_from_text_element( iv_text_element_symbol = '' iv_text_element_container = gc_incl_name ).       "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUN' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzreggr' iv_abap_fieldname = 'ZZREGGR' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type->bind_structure( iv_structure_name = 'HCMFAB_S_PERS_PERSONALDATA_UN' iv_bind_conversions = 'X' ). "#EC NOTEXT
lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUNDefault' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzsprsl_txt' iv_abap_fieldname = 'ZZSPRSL_TXT' ). "#EC NOTEXT
lo_property->set_label_from_text_element( iv_text_element_symbol = '' iv_text_element_container = gc_incl_name ).       "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUNDefault' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzreggr_txt' iv_abap_fieldname = 'ZZREGGR_TXT' ). "#EC NOTEXT
lo_property->set_label_from_text_element( iv_text_element_symbol = '' iv_text_element_container = gc_incl_name ).       "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_creatable( abap_false ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type = model->get_entity_type( iv_entity_name = 'PersonalDataUNDefault' ).    "#EC NOTEXT
lo_property = lo_entity_type->create_property( iv_property_name = 'Zzreggr' iv_abap_fieldname = 'ZZREGGR' ). "#EC NOTEXT
lo_property->set_type_edm_string( ).
lo_property->set_maxlength( iv_max_length = 4 ).
lo_property->set_creatable( abap_true ).
lo_property->set_updatable( abap_false ).

lo_property->set_sortable( abap_false ).
lo_property->set_nullable( abap_true ).
lo_property->set_filterable( abap_false ).
lo_entity_type->bind_structure( iv_structure_name = 'HCMFAB_S_PERS_PERSONALDATA_UN' iv_bind_conversions = 'X' ). "#EC NOTEXT
  endmethod.
