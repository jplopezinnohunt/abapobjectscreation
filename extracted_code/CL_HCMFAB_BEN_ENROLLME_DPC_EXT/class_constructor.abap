METHOD class_constructor.
* get access to the employee API
  go_employee_api = cl_hcmfab_employee_api=>get_instance( ).

  TRY.
*     initialize GB_HCMFAB_BEN_ENROLL_ENRICH
      GET BADI gb_hcmfab_ben_enroll_enrich.

    CATCH cx_badi.
      CLEAR gb_hcmfab_ben_enroll_enrich.
  ENDTRY.
ENDMETHOD.
