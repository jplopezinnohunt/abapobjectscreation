METHOD get_employees.

  DATA: ls_employee           TYPE hcmfab_s_tcal_employee,
        lv_pernr              TYPE pernr_d,
        lv_root_pernr         TYPE pernr_d,
        ls_root_object        TYPE hrealo,
        lt_pernr              TYPE pernr_tab,
        lv_orgview            TYPE hrwpc_orgview,
        lv_selid              TYPE hr_selid,
        lv_root_object_mode   TYPE hcmfab_tcal_root_mode,
        lt_personalization    TYPE STANDARD TABLE OF hcmfab_d_tcalper,
        ls_personalization    TYPE hcmfab_d_tcalper,
        lv_personalization_allowed  TYPE boolean,
        lv_is_valid           TYPE boolean,
        lt_views              TYPE cl_hcmfab_common_mpc=>tt_teamcalendarview,
        ls_view               TYPE hcmfab_s_tcal_view_ui,
        lv_pers_mode          TYPE hcmfab_tcal_view_pers_mode.

* determine root object
  lv_root_object_mode = me->get_root_mode_for_view(
      iv_application_id      = iv_application_id
      iv_instance_id         = iv_instance_id
      iv_employee_assignment = iv_employee_assignment
      iv_view_type           = iv_view_type
      iv_view_id             = iv_view_id ).

  IF lv_root_object_mode = gc_root_mode-requester.
    lv_root_pernr = iv_requester_id.
  ELSE.
    lv_root_pernr = iv_employee_assignment.
  ENDIF.

* determine the employees via the given view
  CASE iv_view_type.
    WHEN gc_viewtype-standard.
      CASE iv_view_id.
        WHEN gc_view_id-colleagues.
*         standard COLLEAGUES view
          lt_pernr = go_employee_api->get_colleagues(
              iv_application_id = iv_application_id
              iv_pernr          = lv_root_pernr ).

        WHEN gc_view_id-direct_reports.
*         standard DIRECT_REPORTS view
          lt_pernr = go_employee_api->get_direct_reports(
              iv_application_id = iv_application_id
              iv_manager_pernr  = lv_root_pernr ).

        WHEN gc_view_id-self.
*         standard SELF view (only use the root object)
          APPEND lv_root_pernr TO lt_pernr.
      ENDCASE.

    WHEN gc_viewtype-oadpview.
      lv_orgview = iv_view_id.
      ls_root_object-plvar = cl_hcmfab_employee_api=>gv_active_plvar.
      ls_root_object-otype = gc_otype-employee.
      ls_root_object-realo = lv_root_pernr.
      "retrieve the employees via the given OADP-view
      lt_pernr =
        cl_hcmfab_utilities=>get_employees_via_oadp( iv_orgview     = lv_orgview
                                                     is_root_object = ls_root_object ).

    WHEN gc_viewtype-selid.
      "retrieve the employees via the given selection ID (SELID)
      lv_selid = iv_view_id.
      lt_pernr = cl_hcmfab_utilities=>get_employees_via_selid( lv_selid ).

    WHEN gc_viewtype-custom. "note 2846997
      " nothing to do. The PERNRs are read from database only

    WHEN OTHERS.
*     determine list of PERNRs via utility-class
      ls_root_object-plvar = cl_hcmfab_employee_api=>gv_active_plvar.
      ls_root_object-otype = gc_otype-employee.
      ls_root_object-realo = lv_root_pernr.
      lt_pernr = cl_hcmfab_utilities=>get_employees(
          iv_application_id = iv_application_id
          iv_view_type      = iv_view_type
          iv_view_id        = iv_view_id
          is_root_object    = ls_root_object ).
  ENDCASE.

* add root employee ID to the PERNR-list (if missing)
  READ TABLE lt_pernr WITH KEY table_line = lv_root_pernr
                      TRANSPORTING NO FIELDS.
  IF sy-subrc <> 0.
    APPEND lv_root_pernr TO lt_pernr.
  ENDIF.

* check if personalization is allowed for given view
  lv_personalization_allowed = me->is_personalization_allowed(
      iv_application_id          = iv_application_id
      iv_instance_id             = iv_instance_id
      iv_employee_assignment     = iv_employee_assignment
      iv_view_type               = iv_view_type
      iv_view_id                 = iv_view_id
  ).

* read the personalization data
  IF lv_personalization_allowed = abap_true.

*   Add additional employees to result (only if view pers mode = FULL)
    IF iv_view_type = if_hcmfab_constants=>gc_viewtype-custom.
      lv_pers_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
    ELSE.
      CALL METHOD me->get_all_views
        EXPORTING
          iv_application_id      = iv_application_id
          iv_instance_id         = iv_instance_id
          iv_employee_assignment = iv_employee_assignment
        IMPORTING
          et_views               = lt_views.
      READ TABLE lt_views INTO ls_view WITH KEY view_type = iv_view_type view_id = iv_view_id. "must exist
      lv_pers_mode = ls_view-personalization_mode.
    ENDIF.
    IF lv_pers_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
*     read the personalzation data for the view
      SELECT * FROM hcmfab_d_tcalper INTO TABLE lt_personalization
        WHERE emp_assignment = lv_root_pernr
        AND view_type = iv_view_type
        AND view_id = iv_view_id.
      LOOP AT lt_personalization INTO ls_personalization
        WHERE display_state = if_hcmfab_tcal_constants=>gc_display_state-added
          OR display_state = if_hcmfab_tcal_constants=>gc_display_state-requested
          OR display_state = if_hcmfab_tcal_constants=>gc_display_state-rejected.
*       Check if user is authorized to see the employee.
*       Authorizations might have changed since employee was added to the view (note 2846997)
        CALL BADI go_badi_tcal_settings->validate_custom_employee
          EXPORTING
            iv_employee_id = ls_personalization-employee_id
          RECEIVING
            rv_is_valid    = lv_is_valid.
        IF lv_is_valid = abap_true.
*         check if PERNR is not included in the list (note 2800448)
          READ TABLE lt_pernr WITH KEY table_line = ls_personalization-employee_id TRANSPORTING NO FIELDS.
          IF sy-subrc <> 0.
            APPEND ls_personalization-employee_id TO lt_pernr.
          ENDIF.
        ENDIF.
      ENDLOOP.
    ENDIF.
  ENDIF.

* read employee data
  LOOP AT lt_pernr INTO lv_pernr.
    ls_employee-employee_id = lv_pernr.
    ls_employee-name        = go_employee_api->get_name( iv_pernr = lv_pernr iv_no_auth_check = abap_true ).
    ls_employee-sort_name   = go_employee_api->get_sortable_name( iv_pernr = lv_pernr iv_no_auth_check = abap_true ).
    ls_employee-description = me->get_employee_description(
                          iv_application_id       = iv_application_id
                          iv_calendar_instance_id = iv_instance_id
                          iv_employee_assignment  = iv_employee_assignment
                          iv_employee_id          = lv_pernr ).
    ls_employee-tooltip = ls_employee-name.

*   set diplay state
    CALL METHOD me->get_display_state
      EXPORTING
        iv_application_id          = iv_application_id
        iv_instance_id             = iv_instance_id
        iv_employee_assignment     = iv_employee_assignment
        iv_view_type               = iv_view_type
        iv_view_id                 = iv_view_id
        iv_requester_id            = iv_requester_id
        iv_employee_id             = lv_pernr
        iv_personalization_allowed = abap_true
      RECEIVING
        rv_display_state           = ls_employee-display_state.

    APPEND ls_employee TO et_employees.
  ENDLOOP.

* sort is done later (note 3133516)
** sort result set
*  SORT et_employees BY sort_name.
*
** put root PERNR on first position
*  READ TABLE et_employees INTO ls_employee
*                          WITH KEY employee_id = lv_root_pernr.
*  IF sy-subrc = 0 AND
*     sy-tabix <> 1.
*    DELETE et_employees INDEX sy-tabix.
*    INSERT ls_employee INTO et_employees INDEX 1.
*  ENDIF.

ENDMETHOD.
