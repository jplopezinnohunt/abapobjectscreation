METHOD class_constructor.

  go_tuid_mapper = cl_hrpa_tuid_mapper=>get_instance( ).

  CALL METHOD cl_hrpa_masterdata_factory=>get_read_molga
    IMPORTING
      read_molga = go_molga_reader.


ENDMETHOD.
