METHOD is_employee_in_standard_view.

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
        lt_views TYPE hcmfab_t_tcal_view,
        ls_view TYPE hcmfab_s_tcal_view.



  IF gt_pernr_in_standard_views IS INITIAL.

*   read all views
    CALL BADI go_badi_tcal_settings->get_views
      EXPORTING
        iv_application_id      = iv_application_id
        iv_instance_id         = iv_instance_id
        iv_employee_assignment = iv_employee_assignment
      IMPORTING
        et_views               = lt_views.

    LOOP AT lt_views INTO ls_view WHERE view_type <> gc_viewtype-custom.

*     determine root object
      lv_root_object_mode = me->get_root_mode_for_view(
          iv_application_id      = iv_application_id
          iv_instance_id         = iv_instance_id
          iv_employee_assignment = iv_employee_assignment
          iv_view_type           = ls_view-view_type
          iv_view_id             = ls_view-view_id ).

      IF lv_root_object_mode = gc_root_mode-requester.
        lv_root_pernr = iv_requester_id.
      ELSE.
        lv_root_pernr = iv_employee_assignment.
      ENDIF.

*     determine the employees via the given view
      CASE ls_view-view_type.
        WHEN gc_viewtype-standard.
          CASE ls_view-view_id.
            WHEN gc_view_id-colleagues.
*             standard COLLEAGUES view
              lt_pernr = go_employee_api->get_colleagues(
                  iv_application_id = iv_application_id
                  iv_pernr          = lv_root_pernr ).

            WHEN gc_view_id-direct_reports.
*             standard DIRECT_REPORTS view
              lt_pernr = go_employee_api->get_direct_reports(
                  iv_application_id = iv_application_id
                  iv_manager_pernr  = lv_root_pernr ).

            WHEN gc_view_id-self.
*             standard SELF view (only use the root object)
              APPEND lv_root_pernr TO lt_pernr.
          ENDCASE.

        WHEN gc_viewtype-oadpview.
          lv_orgview = ls_view-view_id.
          ls_root_object-plvar = cl_hcmfab_employee_api=>gv_active_plvar.
          ls_root_object-otype = gc_otype-employee.
          ls_root_object-realo = lv_root_pernr.
          "retrieve the employees via the given OADP-view
          lt_pernr =
            cl_hcmfab_utilities=>get_employees_via_oadp( iv_orgview     = lv_orgview
                                                         is_root_object = ls_root_object ).

        WHEN gc_viewtype-selid.
          "retrieve the employees via the given selection ID (SELID)
          lv_selid = ls_view-view_id.
          lt_pernr = cl_hcmfab_utilities=>get_employees_via_selid( lv_selid ).

        WHEN OTHERS.
*         determine list of PERNRs via utility-class
          ls_root_object-plvar = cl_hcmfab_employee_api=>gv_active_plvar.
          ls_root_object-otype = gc_otype-employee.
          ls_root_object-realo = lv_root_pernr.
          lt_pernr = cl_hcmfab_utilities=>get_employees(
              iv_application_id = iv_application_id
              iv_view_type      = ls_view-view_type
              iv_view_id        = ls_view-view_id
              is_root_object    = ls_root_object ).
      ENDCASE.

*     add root employee ID to the PERNR-list (if missing)
      READ TABLE lt_pernr WITH KEY table_line = lv_root_pernr
                          TRANSPORTING NO FIELDS.
      IF sy-subrc <> 0.
        APPEND lv_root_pernr TO lt_pernr.
      ENDIF.
      APPEND LINES OF lt_pernr TO gt_pernr_in_standard_views.
    ENDLOOP.

    SORT gt_pernr_in_standard_views.
    DELETE ADJACENT DUPLICATES FROM gt_pernr_in_standard_views.
  ENDIF.

  READ TABLE gt_pernr_in_standard_views WITH KEY table_line = iv_employee_id BINARY SEARCH TRANSPORTING NO FIELDS.
  IF sy-subrc = 0.
    rt_is_in_standard_view = abap_true.
  ELSE.
    rt_is_in_standard_view = abap_false.
  ENDIF.

ENDMETHOD.
