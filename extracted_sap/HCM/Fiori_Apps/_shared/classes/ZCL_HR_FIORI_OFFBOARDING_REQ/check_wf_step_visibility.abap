  METHOD check_wf_step_visibility.

    DATA: lv_req_id TYPE ze_hrfiori_guidreq,
          lv_pernr  TYPE pernr_d,
          ls_p0001  TYPE p0001,
          lt_p0001  TYPE STANDARD TABLE OF p0001.

*   Initial value for visibility
    ov_to_be_displayed = abap_true.

*   Search request infos
    lv_pernr = iv_pernr.
    IF lv_pernr IS INITIAL.
      lv_req_id = iv_guid.
      SELECT SINGLE creator_pernr INTO lv_pernr
        FROM zthrfiori_hreq
          WHERE guid = lv_req_id.
    ENDIF.

*   Get employee group from request's creator
    CALL FUNCTION 'HR_READ_INFOTYPE'
      EXPORTING
        pernr     = lv_pernr
        infty     = '0001'
        begda     = sy-datum
        endda     = sy-datum
      TABLES
        infty_tab = lt_p0001.
    READ TABLE lt_p0001 INTO ls_p0001 INDEX 1.

*   Rule for International staff
    IF NOT ( ls_p0001-persg = '1' )
      AND ( iv_step = c_travel OR iv_step = c_shipment  ).
      ov_to_be_displayed = abap_false.
    ENDIF.

  ENDMETHOD.
