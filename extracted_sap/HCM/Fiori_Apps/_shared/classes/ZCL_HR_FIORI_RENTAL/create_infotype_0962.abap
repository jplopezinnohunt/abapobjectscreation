  METHOD create_infotype_0962.

    DATA: lv_locking_user TYPE syst_uname ##NEEDED,
          ls_req          TYPE zthrfiori_breq,
          ls_infos        TYPE zthrfiori_rs_mai,
          ls_infty        TYPE p0962,
          ls_return       TYPE bapireturn1,
          ls_key          TYPE bapipakey ##NEEDED.

*   Get request and infotype data
    SELECT SINGLE * INTO ls_req
      FROM zthrfiori_breq
        WHERE guid = iv_guid.
    SELECT SINGLE * INTO ls_infos
      FROM zthrfiori_rs_mai
        WHERE guid = iv_guid.

*   Prepare infotype data
    MOVE-CORRESPONDING ls_infos TO ls_infty ##ENH_OK.
    ls_infty-pernr = ls_req-creator_pernr.
    ls_infty-infty = '0962'.
    ls_infty-subty = ls_req-subty.
    ls_infty-objps = ls_req-objps.
    ls_infty-seqnr = ls_req-seqnr.
    ls_infty-begda = ls_req-begda.
    ls_infty-endda = ls_req-endda.

*   Lock employee folder
    CALL FUNCTION 'HR_EMPLOYEE_ENQUEUE'
      EXPORTING
        number       = ls_infty-pernr
      IMPORTING
        return       = ls_return
        locking_user = lv_locking_user.

    IF ls_return-type = 'E'.
      ov_return_code = 4.
      MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
        INTO ov_message.

      RETURN.
    ENDIF.

*   Create infotype
    CALL FUNCTION 'HR_INFOTYPE_OPERATION'
      EXPORTING
        infty         = '0962'
        number        = ls_infty-pernr
*       SUBTYPE       =
*       OBJECTID      =
*       LOCKINDICATOR =
        validityend   = ls_infty-endda
        validitybegin = ls_infty-begda
*       RECORDNUMBER  =
        record        = ls_infty
        operation     = 'INS'
*       TCLAS         = 'A'
*       DIALOG_MODE   = '0'
        nocommit      = iv_no_commit
*       VIEW_IDENTIFIER        =
*       SECONDARY_RECORD       =
      IMPORTING
        return        = ls_return
        key           = ls_key.

    IF ls_return-type = 'E'.
      ov_return_code = 4.
      MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
        WITH ls_return-message_v1 ls_return-message_v2
             ls_return-message_v3 ls_return-message_v4
        INTO ov_message.

      RETURN.
    ENDIF.

*   Unlock employee folder
    CALL FUNCTION 'HR_EMPLOYEE_DEQUEUE'
      EXPORTING
        number = ls_infty-pernr
      IMPORTING
        return = ls_return.

    IF ls_return-type = 'E'.
      ov_return_code = 4.
      MESSAGE ID ls_return-id TYPE ls_return-type NUMBER ls_return-number
        INTO ov_message.

      RETURN.
    ENDIF.

  ENDMETHOD.
