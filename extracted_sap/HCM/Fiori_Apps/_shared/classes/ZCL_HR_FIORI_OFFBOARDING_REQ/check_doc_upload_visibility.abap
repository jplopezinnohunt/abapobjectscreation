  METHOD check_doc_upload_visibility.

    DATA: ls_p0001 TYPE p0001,
          lt_p0001 TYPE STANDARD TABLE OF p0001.

*   Initial value for visibility
    ov_to_be_displayed = abap_true.

*   Check employee group
*     Get employee Data from request's creator
      CALL FUNCTION 'HR_READ_INFOTYPE'
        EXPORTING
          pernr     = iv_pernr
          infty     = '0001'
          begda     = sy-datum
          endda     = sy-datum
        TABLES
          infty_tab = lt_p0001.

      READ TABLE lt_p0001 INTO ls_p0001 INDEX 1.

      IF ls_p0001-PERSG EQ 1 . " Internationnal staff
*       Check doc type
        CASE iv_doc_upload.
          WHEN c_repat_ship.
*           Display this doc type for fixed-term staff only
            IF NOT ( ls_p0001-ANSVH = '01' ).
              ov_to_be_displayed = abap_false.
            ENDIF.
        ENDCASE.

      ELSEIF ls_p0001-PERSG EQ 2 . " Local staff
*       Check doc type
        CASE iv_doc_upload.
          WHEN c_repat_ship OR C_REPAT_TRAVEL.
              ov_to_be_displayed = abap_false.
        ENDCASE.
      ENDIF.


  ENDMETHOD.
