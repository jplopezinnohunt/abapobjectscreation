  METHOD /iwbep/if_mgw_appl_srv_runtime~execute_action.

    DATA: lv_main_role TYPE ze_hrfiori_actor,
          ls_return    TYPE zcl_zhr_process_and_fo_mpc_ext=>mainrole,
          lo_pf_util   TYPE REF TO zcl_hrfiori_pf_common.

    CASE iv_action_name.
      WHEN 'GetMainRole'.
        CREATE OBJECT lo_pf_util.
        lo_pf_util->get_main_role( IMPORTING ov_actor = lv_main_role ).
        ls_return-role = lv_main_role.

        copy_data_to_ref( EXPORTING is_data = ls_return
                          CHANGING cr_data  = er_data ).
    ENDCASE.

  ENDMETHOD.
