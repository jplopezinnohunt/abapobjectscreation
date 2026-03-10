method CONVERT_INDEXNAMEVAL_2_STRUC.

  DATA: attr TYPE ty_namevalueasstring,
          attr_wa TYPE namevalueasstring,
          attributes_wa TYPE pobjs_level_attribute.
  LOOP AT attributes INTO attributes_wa.
    MOVE-CORRESPONDING attributes_wa TO attr_wa.
    APPEND attr_wa TO attr.
  ENDLOOP.
  CALL METHOD cl_pobj_case_utility=>convert_fieldnameval_2_struc
    EXPORTING
      attributes     = attr
    IMPORTING
      attr_structure = attr_structure.
endmethod.
