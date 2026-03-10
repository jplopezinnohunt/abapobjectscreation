METHOD get_structure_length.

  DATA lr_struc_descr TYPE REF TO cl_abap_structdescr.
  DATA lt_components TYPE cl_abap_structdescr=>component_table.

  lr_struc_descr ?= cl_abap_structdescr=>describe_by_name( iv_structure_name ).

  et_components = lr_struc_descr->get_components( ).

  DESCRIBE TABLE et_components LINES ev_length.

ENDMETHOD.
