METHOD map_field_attributes.

  FIELD-SYMBOLS <ls_field_attributes> TYPE hrpad_obj_field_attribute.
  FIELD-SYMBOLS <ls_field_attribute> TYPE hrpad_field_attribute.
  FIELD-SYMBOLS <ls_field_metadata> TYPE hcmfab_s_pers_fieldmetadata.
  FIELD-SYMBOLS <ls_component> TYPE abap_compdescr.

  CLEAR et_field_metadata.

  READ TABLE it_field_attributes WITH KEY object_key = iv_object_key ASSIGNING <ls_field_attributes>.
  IF sy-subrc EQ 0.

    LOOP AT it_components ASSIGNING <ls_component>.
      APPEND INITIAL LINE TO et_field_metadata ASSIGNING <ls_field_metadata>.
      <ls_field_metadata>-hcmfab_pskey = is_pskey.
      <ls_field_metadata>-field_name = <ls_component>-name.
      <ls_field_metadata>-is_edit_mode = iv_locked.
      <ls_field_metadata>-versionid = iv_versionid.
      READ TABLE <ls_field_attributes>-field_attribute WITH KEY field_name = <ls_component>-name ASSIGNING <ls_field_attribute>.
      IF sy-subrc EQ 0.

        CASE <ls_field_attribute>-field_property.
          WHEN 'A'. "not modifiable
            <ls_field_metadata>-is_visible = abap_true.
            <ls_field_metadata>-is_editable = abap_false.
            <ls_field_metadata>-is_required = abap_false.
          WHEN 'B'. "do not display
            <ls_field_metadata>-is_visible = abap_false.
            <ls_field_metadata>-is_editable = abap_false.
            <ls_field_metadata>-is_required = abap_false.
          WHEN 'C'. "mandatory
            <ls_field_metadata>-is_visible = abap_true.
            <ls_field_metadata>-is_editable = abap_true.
            <ls_field_metadata>-is_required = abap_true.
          WHEN ''. "editable
            <ls_field_metadata>-is_visible = abap_true.
            <ls_field_metadata>-is_editable = abap_true.
            <ls_field_metadata>-is_required = abap_false.
        ENDCASE.
      ELSE.
* blow up field_metadata with fields not considered in T588MFPROPS/UI Conversion class
        IF iv_locked = abap_true.
* default setting: visible and editable -> but only in 'EDIT'-mode ...
          <ls_field_metadata>-is_visible = abap_true.
          <ls_field_metadata>-is_editable = abap_true.
          <ls_field_metadata>-is_required = abap_false.
        ELSE.
          <ls_field_metadata>-is_visible = abap_true.
          <ls_field_metadata>-is_editable = abap_false.
          <ls_field_metadata>-is_required = abap_false.
        ENDIF.
      ENDIF.
    ENDLOOP.
  ENDIF.

ENDMETHOD.
