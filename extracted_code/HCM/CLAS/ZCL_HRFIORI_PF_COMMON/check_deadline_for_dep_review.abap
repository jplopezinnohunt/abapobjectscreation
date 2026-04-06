  METHOD check_deadline_for_dep_review.

    DATA: ls_review_deadline TYPE zthrfiori_dep_dl,
          ls_bypass_deadline TYPE zthrfiori_dep_bp.

*   Initial value for indicator
    ov_can_be_requested = abap_true.

*   Check review deadline for current year
    SELECT SINGLE * INTO ls_review_deadline
      FROM zthrfiori_dep_dl
        WHERE zyear = sy-datum+0(4).
    IF sy-datum > ls_review_deadline-deadline_date.
      ov_can_be_requested = abap_false.
    ENDIF.

*   Check if user can make bypass of this date
    SELECT SINGLE * INTO ls_bypass_deadline
      FROM zthrfiori_dep_bp
        WHERE user_id = iv_user_id
          AND valid_from <= sy-datum
          AND valid_to >= sy-datum ##WARN_OK.
    IF sy-subrc = 0 AND ls_bypass_deadline-can_bypass = abap_true.
      ov_can_be_requested = abap_true.
    ENDIF.

  ENDMETHOD.
