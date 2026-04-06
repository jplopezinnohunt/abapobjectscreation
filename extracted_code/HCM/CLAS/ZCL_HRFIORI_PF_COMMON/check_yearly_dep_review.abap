  METHOD check_yearly_dep_review.

    DATA: lv_guid         TYPE scmg_case_guid,
          lv_obj_key      TYPE asr_object_key,
          lv_status       TYPE asr_process_status,
          lv_processor    TYPE asr_processor_role,
          lv_begda        TYPE dats,
          lv_endda        TYPE dats,
          lr_current_year TYPE RANGE OF dats,
          ls_current_year LIKE LINE OF lr_current_year.

    lv_begda+0(4) = sy-datum+0(4).
    lv_begda+4(4) = '0101'.

    lv_endda+0(4) = sy-datum+0(4).
    lv_endda+4(4) = '1231'.

    ls_current_year-low = lv_begda.
    ls_current_year-high = lv_endda.
    ls_current_year-option = 'BT'.
    ls_current_year-sign = 'I'.
    APPEND ls_current_year TO lr_current_year.

    MOVE iv_pernr TO lv_obj_key.

    SELECT SINGLE case_guid status
      INTO ( lv_guid, lv_status )
      FROM t5asrprocesses
        WHERE process = iv_process
          AND object_key = lv_obj_key
          AND init_date IN lr_current_year
          AND object_type = 'P' ##WARN_OK.

*   No result: there is no process this year
    IF sy-subrc <> 0.
      ov_review_exists = abap_false.
    ELSE.
      CASE lv_status.
        WHEN 'DRAFT' OR 'STARTED'.
          ov_review_exists = abap_true.
        WHEN 'WITHDRAWN' OR 'ERROR'.
          ov_review_exists = abap_false.
        WHEN 'COMPLETED'.
*         Check if this process was approved or not
*         We check table T5ASRSTEPDETAILS: if approved, there are at least 3 rows with actors
*         employee (HRASRD), HRA (HRASRB) and HRO (HRASRA).
*         HRA can approve or reject. If rejection, there are 2 rows or more (depending if request was sent back to  author),
*         and HRO is not present in table.
*         HRO can approve or withdraw. In case of withdraw, Status of request is set to WITHDRAWN.
*         In case of HRO approval, status is set to COMPLETED
          SELECT SINGLE processor_role INTO lv_processor
            FROM t5asrstepdetails
              WHERE process_guid = lv_guid
                AND processor_role = 'HRASRA' ##WARN_OK.

*         Case review approved by HRO
          IF lv_processor IS NOT INITIAL.
            ov_review_exists = abap_true.
*         Others cases
          ELSE.
            ov_review_exists = abap_false.
          ENDIF.

      ENDCASE.
    ENDIF.

  ENDMETHOD.
