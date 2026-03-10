METHOD class_constructor.

  go_employee_api = cl_hcmfab_employee_api=>get_instance( ).

  CALL METHOD cl_hrpa_masterdata_factory=>get_business_logic
    IMPORTING
      business_logic = go_masterdata_bl.

  CREATE OBJECT go_paitf_reader
    EXPORTING
      masterdata_bl = go_masterdata_bl.


ENDMETHOD.
