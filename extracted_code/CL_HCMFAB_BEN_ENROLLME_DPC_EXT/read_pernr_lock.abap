METHOD read_pernr_lock.
  DATA: lt_return2 TYPE bapirettab.
  DATA: ls_return2 TYPE bapiret2.
  DATA: ls_error_table LIKE LINE OF et_error_table.
  DATA: lv_locked TYPE boole_d.

  CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock( EXPORTING iv_lock = abap_true iv_pernr = iv_pernr IMPORTING ev_locked = lv_locked messages = lt_return2 ).

  IF lt_return2 IS NOT INITIAL AND lv_locked EQ abap_false.
    LOOP AT lt_return2 INTO ls_return2.
      CLEAR ls_error_table.
      ls_error_table-pernr = iv_pernr.
      ls_error_table-class = ls_return2-id.
      ls_error_table-msgno = ls_return2-number.
      ls_error_table-msgv1 = ls_return2-message_v1.
      ls_error_table-msgv2 = ls_return2-message_v2.
      ls_error_table-msgv3 = ls_return2-message_v3.
      ls_error_table-msgv4 = ls_return2-message_v4.
      ls_error_table-sever = 8.
      ls_error_table-etext = ls_return2-message.
      APPEND ls_error_table TO et_error_table.
    ENDLOOP.

  ELSEIF lv_locked EQ abap_true.
    CALL METHOD cl_hrpa_pernr_infty_xss=>manage_lock( iv_lock = abap_false iv_pernr = iv_pernr ).
  ENDIF.

ENDMETHOD.
