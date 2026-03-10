METHOD convert_struc_2_indexnameval.

  DATA: attr TYPE ty_namevalueasstring,
      attr_wa TYPE namevalueasstring,
      attributes_wa TYPE pobjs_level_attribute.
  CALL METHOD cl_pobj_case_utility=>convert_struc_2_fieldnameval
    EXPORTING
      attr_structure            = attr_structure
      return_noninit_value_only = ' '
    IMPORTING
      attributes                = attr.
  LOOP AT attr INTO attr_wa.
    MOVE-CORRESPONDING attr_wa TO attributes_wa.
    MOVE '1' TO attributes_wa-field_index.
    attributes_wa-operation = operation.
    APPEND attributes_wa TO attributes.
  ENDLOOP.

ENDMETHOD.
