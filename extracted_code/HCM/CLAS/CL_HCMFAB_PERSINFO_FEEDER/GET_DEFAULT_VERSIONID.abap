METHOD GET_DEFAULT_VERSIONID.

  DATA lv_empty_versionid TYPE itvers.

  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_itvers
    EXPORTING
      raw_versionid    = lv_empty_versionid
    RECEIVING
      cooked_versionid = rv_default_versionid.


ENDMETHOD.
