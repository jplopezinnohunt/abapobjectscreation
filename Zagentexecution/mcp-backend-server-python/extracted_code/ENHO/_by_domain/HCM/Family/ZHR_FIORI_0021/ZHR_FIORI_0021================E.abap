ENHANCEMENT 1  .
  DATA ls_fa_temp TYPE LINE OF HRPAD_FIELD_ATTRIBUTE_TAB.

  CLEAR field_attribute.
  field_attribute-field_name = 'GOVAST'.
  field_attribute-field_property = IF_HRPA_UI_CONVERT_STANDARD~INVISIBLE.
  APPEND field_attribute TO <field_attribute_wa>-field_attribute.

  CLEAR field_attribute.
  field_attribute-field_name = 'SPEMP'.
  field_attribute-field_property = IF_HRPA_UI_CONVERT_STANDARD~INVISIBLE.
  APPEND field_attribute TO <field_attribute_wa>-field_attribute.

*  CLEAR field_attribute.
*  field_attribute-field_name = 'ERBNR'.
*  field_attribute-field_property = IF_HRPA_UI_CONVERT_STANDARD~INVISIBLE.
*  APPEND field_attribute TO <field_attribute_wa>-field_attribute.
  CLEAR ls_fa_temp.
  LOOP AT <field_attribute_wa>-field_attribute into ls_fa_temp WHERE field_name EQ 'ERBNR'.
    ls_fa_temp-field_property = IF_HRPA_UI_CONVERT_STANDARD~INVISIBLE.
    MODIFY <field_attribute_wa>-field_attribute FROM ls_fa_temp.
  ENDLOOP.

  CLEAR ls_fa_temp.
  IF <r0021>-famsa EQ '14' OR <r0021>-famsa EQ '2'.
    LOOP AT <field_attribute_wa>-field_attribute into ls_fa_temp WHERE field_name EQ 'WAERS'.
      ls_fa_temp-field_property = IF_HRPA_UI_CONVERT_STANDARD~READ_ONLY.
      MODIFY <field_attribute_wa>-field_attribute FROM ls_fa_temp.
    ENDLOOP.
    IF sy-subrc NE 0.
      field_attribute-field_name = 'WAERS'.
      field_attribute-field_property = IF_HRPA_UI_CONVERT_STANDARD~READ_ONLY.
      APPEND field_attribute TO <field_attribute_wa>-field_attribute.
    ENDIF.
  ENDIF.


  CALL METHOD cl_hrpa_field_attribs_services=>convert_and_merge_field_attrbs
    EXPORTING
      field_metadatas  = field_metadatas
    CHANGING
      field_attributes = field_attributes.

ENDENHANCEMENT.
