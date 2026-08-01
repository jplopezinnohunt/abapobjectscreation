FORM CD_CALL_YFMFUNDC5.
  IF   ( UPD_YTFM_FUND_C5 NE SPACE )
  .
    CALL FUNCTION 'YFMFUNDC5_WRITE_DOCUMENT'
        EXPORTING
          OBJECTID                = OBJECTID
          TCODE                   = TCODE
          UTIME                   = UTIME
          UDATE                   = UDATE
          USERNAME                = USERNAME
          PLANNED_CHANGE_NUMBER   = PLANNED_CHANGE_NUMBER
          OBJECT_CHANGE_INDICATOR = CDOC_UPD_OBJECT
          PLANNED_OR_REAL_CHANGES = CDOC_PLANNED_OR_REAL
          NO_CHANGE_POINTERS      = CDOC_NO_CHANGE_POINTERS
* workarea_old of YTFM_FUND_C5
          O_YTFM_FUND_C5
                      = *YTFM_FUND_C5
* workarea_new of YTFM_FUND_C5
          N_YTFM_FUND_C5
                      = YTFM_FUND_C5
* updateflag of YTFM_FUND_C5
          UPD_YTFM_FUND_C5
                      = UPD_YTFM_FUND_C5
        IMPORTING
          CHANGENUMBER            = CDCHANGENUMBER
    .
  ENDIF.
  CLEAR PLANNED_CHANGE_NUMBER.
ENDFORM.