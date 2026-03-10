METHOD get_local_dpc_instance.

  DATA lv_class_name TYPE seoclsname.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.

  FIELD-SYMBOLS <ls_local_dpc_instance> TYPE ty_s_local_dpc_instance.

  READ TABLE gt_local_dpc_instance WITH KEY versionid = iv_versionid ASSIGNING <ls_local_dpc_instance>.
  IF sy-subrc EQ 0.
    IF <ls_local_dpc_instance>-handler IS ASSIGNED.
      ro_local_dpc_instance = <ls_local_dpc_instance>-handler.
      RETURN.
    ENDIF.
    DELETE TABLE gt_local_dpc_instance FROM <ls_local_dpc_instance>.
  ENDIF.
*
** no local dpc instance available -> create a new one ...
  GET BADI lo_persinfo_config_badi
    FILTERS
      versionid = iv_versionid.

  CALL BADI lo_persinfo_config_badi->get_dpc_instance
    EXPORTING
      iv_app_id       = if_hcmfab_constants=>gc_application_id-mypersonaldata
      io_context      = mo_context
    CHANGING
      co_dpc_instance = ro_local_dpc_instance.

  IF NOT ro_local_dpc_instance IS BOUND.
    CONCATENATE gc_clsname_local_dpc_prefix iv_versionid INTO lv_class_name.
    TRY.
        CREATE OBJECT ro_local_dpc_instance TYPE (lv_class_name)
          EXPORTING
            io_context = mo_context.
      CATCH cx_sy_create_object_error.
*      ro_local_dpc_instance = super.
    ENDTRY.
  ENDIF.

  IF ro_local_dpc_instance IS BOUND.
    APPEND INITIAL LINE TO gt_local_dpc_instance ASSIGNING <ls_local_dpc_instance>.
    <ls_local_dpc_instance>-versionid = iv_versionid.
    <ls_local_dpc_instance>-handler = ro_local_dpc_instance.
  ENDIF.

ENDMETHOD.
