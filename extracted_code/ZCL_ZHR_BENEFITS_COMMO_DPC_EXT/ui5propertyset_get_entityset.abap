  METHOD ui5propertyset_get_entityset.

    DATA: lv_request_type TYPE ze_hrfiori_requesttype,
          lv_actor        TYPE ze_hrfiori_actor,
          lv_field        TYPE ze_hrfiori_uifield,
          lv_status       TYPE ze_hrfiori_requeststatus,
          lv_guid         TYPE ze_hrfiori_guidreq,
          ls_filter       TYPE /iwbep/s_mgw_select_option,
          ls_filter_range TYPE /iwbep/s_cod_select_option,
          lt_uiproperty   TYPE STANDARD TABLE OF zthrfiori_ui5pro.

*   Get filter values if any
    IF it_filter_select_options[] IS NOT INITIAL.
      LOOP AT it_filter_select_options INTO ls_filter.
        LOOP AT ls_filter-select_options INTO ls_filter_range.
          CASE ls_filter-property.
            WHEN 'RequestType'.
              MOVE ls_filter_range-low TO lv_request_type.
            WHEN 'Actor'.
              MOVE ls_filter_range-low TO lv_actor.
            WHEN 'Field'.
              MOVE ls_filter_range-low TO lv_field.
            WHEN 'Status'.
              MOVE ls_filter_range-low TO lv_status.
*              MOVE ls_filter_range-low TO lv_field.
            WHEN 'Guid'.
              MOVE ls_filter_range-low TO lv_guid.
          ENDCASE.
        ENDLOOP.
      ENDLOOP.
    ENDIF.

*   get UI5 properties
    SELECT * INTO  TABLE lt_uiproperty
      FROM zthrfiori_ui5pro.

*   Filter results if necessary
    IF lv_request_type IS NOT INITIAL.
      DELETE lt_uiproperty WHERE request_type <> lv_request_type.
    ENDIF.
    IF lv_actor IS NOT INITIAL.
      DELETE lt_uiproperty WHERE actor <> lv_actor.
    ENDIF.
    IF lv_field IS NOT INITIAL.
      DELETE lt_uiproperty WHERE field <> lv_field.
    ENDIF.
*    IF lv_status IS NOT INITIAL. - SIg - DRAFT is Initial
    DELETE lt_uiproperty WHERE status <> lv_status.
*    ENDIF.

    LOOP AT lt_uiproperty ASSIGNING FIELD-SYMBOL(<lfs_uiproperty>) WHERE property EQ '05'.

      CALL FUNCTION <lfs_uiproperty>-function  "'ZHR_GET_VISIBILITY_UI5PRO'
        EXPORTING
          iv_guid     = lv_guid
          iv_field    = <lfs_uiproperty>-field
        IMPORTING
          ev_property = <lfs_uiproperty>-property.


    ENDLOOP.

*   Return results
    et_entityset = lt_uiproperty.

  ENDMETHOD.
