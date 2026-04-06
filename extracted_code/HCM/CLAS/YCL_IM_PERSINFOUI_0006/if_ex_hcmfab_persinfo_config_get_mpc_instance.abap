  METHOD if_ex_hcmfab_persinfo_config~get_mpc_instance.
*    CASE iv_app_id.
*      WHEN 'MYPERSONALDATA'. " Application My Addresses
*    CREATE OBJECT co_mpc_instance
*      TYPE ZCL_HCMFAB_MYPERSDATA_MPC
*      EXPORTING
*        io_model = io_model.
*    ENDCASE.
  ENDMETHOD.
