  METHOD get_employee_molga.

    DATA: lo_molga_reader TYPE REF TO cl_hrpa_molga.

    cl_hrpa_masterdata_factory=>get_read_molga( IMPORTING read_molga = lo_molga_reader ).
    ov_molga = lo_molga_reader->read_molga_by_pernr( pernr = iv_pernr ).

  ENDMETHOD.
