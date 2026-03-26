method toaatset_get_entity.

  data: lo_object         type ref to zcl_hr_document_manager,
        lv_request_id     type ze_hrfiori_guidreq,
        lv_attach_type    type zde_doctype,
        lv_incnb          type ze_hrfiori_incrment_nb,
        lv_archive_doc_id type saeardoid,
        lv_value_string   type string.

  " --- Extraire les valeurs depuis IT_KEY_TAB ---
LOOP AT it_key_tab INTO DATA(ls_key_tab).

  " --- Passer par une variable intermédiaire STRING ---
  lv_value_string = ls_key_tab-value.
  CASE ls_key_tab-name.
    WHEN 'REQUEST_ID' OR 'RequestId'.
      TRY.
          lv_request_id = lv_value_string. " conversion explicite
        CATCH cx_sy_move_cast_error ##NO_HANDLER.
          " Ignorer ou logger la valeur non convertible
      ENDTRY.
    WHEN 'AttachType'.
      TRY.
          lv_attach_type = lv_value_string.
        CATCH cx_sy_move_cast_error ##NO_HANDLER.
      ENDTRY.
    WHEN 'IncNb'.
      TRY.
          lv_incnb = lv_value_string.
        CATCH cx_sy_move_cast_error ##NO_HANDLER.
      ENDTRY.
    WHEN 'ArchiveDocId'.
      TRY.
          lv_archive_doc_id = lv_value_string.
        CATCH cx_sy_move_cast_error ##NO_HANDLER.
      ENDTRY.
  ENDCASE.
ENDLOOP.


  " --- Instancier le singleton ---
  lo_object = zcl_hr_document_manager=>get_instance( ).

  " --- Appeler la méthode get_document ---
  data lv_mime_type type string.
  data lv_filename type zde_filename.
  data lv_success  type flag ##NEEDED.
  data lv_message  type string ##NEEDED.
  data lv_content  type xstring.

  lo_object->get_document(
    exporting
      iv_archive_doc_id = lv_archive_doc_id
      iv_request_id     = lv_request_id
      iv_attach_type    = lv_attach_type
      iv_incnb          = lv_incnb
    importing
      ev_mime_type = lv_mime_type
      ev_filename  = lv_filename
      ev_success   = lv_success
      ev_message   = lv_message
      ev_content   = lv_content
  ).

  " --- Remplir l'entité OData pour le frontend ---
  er_entity-archive_doc_id = lv_archive_doc_id.
  er_entity-guid     = lv_request_id.
  er_entity-attach_type    = lv_attach_type.
  er_entity-inc_nb          = lv_incnb.
  er_entity-mime_type      = lv_mime_type.
  er_entity-filename       = lv_filename.
  er_entity-contents        = lv_content.


endmethod.
