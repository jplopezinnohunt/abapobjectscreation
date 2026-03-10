METHOD get_elem_dtype_of_struc_field.

  DATA lt_components TYPE cl_abap_structdescr=>component_table.

  FIELD-SYMBOLS <ls_component> TYPE abap_componentdescr.

  get_structure_length(
    EXPORTING
      iv_structure_name = iv_structure_name
    IMPORTING
      et_components     = lt_components ).

  READ TABLE lt_components WITH KEY name = iv_fieldname ASSIGNING <ls_component>.
  IF <ls_component> IS ASSIGNED.
    ev_rel_name = <ls_component>-type->get_relative_name( ). "2930739
    ev_elem_type = <ls_component>-type->type_kind.
    ev_type_length = <ls_component>-type->length.
  ENDIF.

ENDMETHOD.
