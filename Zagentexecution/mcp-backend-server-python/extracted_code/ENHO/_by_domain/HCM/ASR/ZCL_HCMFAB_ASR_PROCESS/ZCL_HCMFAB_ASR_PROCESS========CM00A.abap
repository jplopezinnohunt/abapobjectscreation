  METHOD if_hcmfab_asr_process_confg~change_process_attributes.

    DATA: lo_pf_common TYPE REF TO zcl_hrfiori_pf_common.

    CREATE OBJECT lo_pf_common.
    lo_pf_common->filter_process_list( EXPORTING iv_userid  = sy-uname
                                       CHANGING  ct_process = ct_hcmfab_process_list ).

  ENDMETHOD.
