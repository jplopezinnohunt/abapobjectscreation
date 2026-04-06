METHOD get_pskey_from_key.

  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.

  LOOP AT it_key_tab INTO ls_key.
    CASE ls_key-name.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_pernr.
        rs_pskey-hcmfab_pernr = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_infty.
        rs_pskey-hcmfab_infty = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty.
        rs_pskey-hcmfab_subty = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_objps.
        rs_pskey-hcmfab_objps =  ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_sprps.
        rs_pskey-hcmfab_sprps = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_begda.
        rs_pskey-hcmfab_begda = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_endda.
        rs_pskey-hcmfab_endda = ls_key-value.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_seqnr.
        rs_pskey-hcmfab_seqnr = ls_key-value.
    ENDCASE.
  ENDLOOP.


ENDMETHOD.
