METHOD class_constructor.

  "get reference to BAdI HCMFAB_B_TEAMCALENDAR_SETTINGS
  GET BADI go_badi_tcal_settings.

  "get reference to BADI HCBFAB_B_TEAMCALENDAR_EXTEND to call the entity enrichments
  TRY.
      GET BADI go_badi_tcal_extension.
    CATCH cx_badi.
      CLEAR go_badi_tcal_extension.
  ENDTRY.

* instantiate BAdI HCMFAB_B_COMMON
  TRY.
      GET BADI gb_hcmfab_b_common.
    CATCH cx_badi.
      CLEAR gb_hcmfab_b_common.
  ENDTRY.

* instantiate BAdI HCMFAB_B_PERSINFO_SETTINGS
  TRY.
      GET BADI gb_hcmfab_b_persinfo_settings.
    CATCH cx_badi.
      CLEAR gb_hcmfab_b_persinfo_settings.
  ENDTRY.

* instantiate BADI for orgchart settings
  TRY.
      GET BADI go_badi_orgchart_settings.
    CATCH cx_badi.
      CLEAR go_badi_orgchart_settings.
  ENDTRY.

  "get reference to central employee API
  go_employee_api = cl_hcmfab_employee_api=>get_instance( ).

ENDMETHOD.
