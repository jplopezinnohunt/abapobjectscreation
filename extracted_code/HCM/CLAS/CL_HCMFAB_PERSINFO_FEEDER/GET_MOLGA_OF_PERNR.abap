METHOD GET_MOLGA_OF_PERNR.

  rv_molga = go_molga_reader->read_molga_by_pernr( tclas = cl_hrpa_tclas=>tclas_employee pernr = iv_pernr ).

ENDMETHOD.
