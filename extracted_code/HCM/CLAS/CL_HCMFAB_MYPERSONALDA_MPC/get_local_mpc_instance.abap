METHOD get_local_mpc_instance.

  DATA lv_class_name TYPE seoclsname.
  DATA lo_persinfo_config_badi TYPE REF TO hcmfab_b_persinfo_config.

  FIELD-SYMBOLS <ls_local_mpc_instance> TYPE ty_s_local_mpc_instance.

  READ TABLE gt_local_mpc_instance WITH KEY versionid = iv_versionid ASSIGNING <ls_local_mpc_instance>.
  IF sy-subrc EQ 0.
    IF <ls_local_mpc_instance>-handler IS ASSIGNED.
      ro_local_mpc_instance = <ls_local_mpc_instance>-handler.
      RETURN.
    ENDIF.
    DELETE TABLE gt_local_mpc_instance FROM <ls_local_mpc_instance>.
  ENDIF.
*
** no local mpc instance available -> create a new one ...
  GET BADI lo_persinfo_config_badi
    FILTERS
      versionid = iv_versionid.

  CALL BADI lo_persinfo_config_badi->get_mpc_instance
    EXPORTING
      iv_app_id       = if_hcmfab_constants=>gc_application_id-mypersonaldata
      io_model        = model
    CHANGING
      co_mpc_instance = ro_local_mpc_instance.

  IF ro_local_mpc_instance IS BOUND.
    APPEND INITIAL LINE TO gt_local_mpc_instance ASSIGNING <ls_local_mpc_instance>.
    <ls_local_mpc_instance>-versionid = iv_versionid.
    <ls_local_mpc_instance>-handler = ro_local_mpc_instance.
  ENDIF.

ENDMETHOD.
