 method define.
   data: lo_entity   type ref to /iwbep/if_mgw_odata_entity_typ,
         lo_property type ref to /iwbep/if_mgw_odata_property.

   " Appel de la définition standard
   super->define( ).
   "==========================
   " FileUpload Entity
   "==========================
   lo_entity = model->get_entity_type( iv_entity_name = 'FileUpload' ).
   if lo_entity is bound.
     lo_property = lo_entity->get_property( iv_property_name = 'MimeType' ).
     lo_property->set_as_content_type( ).
   endif.

   "==========================
   " TOAAT Entity
   "==========================
   lo_entity = model->get_entity_type( iv_entity_name = 'TOAAT' ).
   if lo_entity is bound.
     lo_property = lo_entity->get_property( iv_property_name = 'MimeType' ).
     lo_property->set_as_content_type( ).
   endif.
 endmethod.
