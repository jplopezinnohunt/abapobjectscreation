  METHOD if_ex_hcmfab_myfamilymembers~enrich_familymemberun.

    FIELD-SYMBOLS: <fs_line> TYPE cl_hcmfab_myfamilymemb_mpc=>ts_familymemberun.

    LOOP AT ct_familymemberun ASSIGNING <fs_line>
      WHERE lgart IS NOT INITIAL.
      SELECT SINGLE lgtxt INTO <fs_line>-wt_txt
        FROM t512t
          WHERE sprsl = sy-langu
            AND molga = 'UN'
            AND lgart = <fs_line>-lgart.
    ENDLOOP.

  ENDMETHOD.
