method GET_PAYCHECK_DATA.

  SELECT SINGLE content FROM hcmfab_enro_cont INTO ev_content
    WHERE pernr = iv_pernr.

endmethod.
