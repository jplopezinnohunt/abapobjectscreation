METHOD get_sname_using_versionid.
* this method is partly copied from
* CL_HRPA_PERNR_INFTY_XSS->GET_SNAME_UICC_USING_VERSIONID

  DATA t7xssreuseuisn TYPE t7xssreuseuisn.
  DATA lv_versionid TYPE hcmfab_versionid.

  lv_versionid = iv_versionid.

* this method call needs to be disabled as it causes issues when note 1537362 is implemented
*  CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_itvers
*    EXPORTING
*      raw_versionid    = lv_versionid
*    RECEIVING
*      cooked_versionid = lv_versionid.

** Check if the Version ID is present in the Reuse UI Structure Name Table or not

  SELECT * FROM t7xssreuseuisn INTO t7xssreuseuisn UP TO 1 ROWS "#EC CI_GENBUFF
           WHERE                                      "#EC CI_SGLSELECT
              infty     = mv_infty  AND
              stype     = 'MAIN' AND
              versionid = lv_versionid.
  ENDSELECT.

** If entry is found then get details from uiconvclas table using the correponding Structure Name

  IF sy-subrc = 0.

    SELECT SINGLE sname FROM t588uiconvclas INTO (rv_ui_structure_name)
      WHERE
        sname = t7xssreuseuisn-sname.

** If entry is not found than search directly on uiconvcals table
  ELSE.

    SELECT sname FROM t588uiconvclas INTO (rv_ui_structure_name) UP TO 1 ROWS "#EC CI_GENBUFF
        WHERE                                         "#EC CI_SGLSELECT
          infty     = mv_infty  AND
          stype     = 'MAIN' AND
          versionid = lv_versionid.
    ENDSELECT.

    IF sy-subrc <> 0.

      SELECT * FROM t7xssreuseuisn INTO t7xssreuseuisn UP TO 1 ROWS "#EC CI_GENBUFF
        WHERE                                         "#EC CI_SGLSELECT
          infty     = mv_infty  AND
          stype     = 'MAIN' AND
          versionid = gc_versionid_xx.
      ENDSELECT.

      IF sy-subrc = 0.
        SELECT SINGLE sname FROM t588uiconvclas INTO (rv_ui_structure_name)
          WHERE
            sname = t7xssreuseuisn-sname.

      ELSE.

        SELECT sname FROM t588uiconvclas INTO (rv_ui_structure_name) UP TO 1 ROWS "#EC CI_GENBUFF
          WHERE                                       "#EC CI_SGLSELECT
            infty     = mv_infty                AND
            stype     = 'MAIN'               AND
            versionid = gc_versionid_xx.
        ENDSELECT.
      ENDIF.

    ENDIF.

  ENDIF.

ENDMETHOD.
