METHOD get_default_version_id.
  rv_default_version_id = go_employee_api->get_default_version_id( iv_assignment_id ).
ENDMETHOD.
