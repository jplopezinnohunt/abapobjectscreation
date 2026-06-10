FUNCTION Y_HR_PAWF_FILL_REQUEST
  IMPORTING
    IV_PERNR TYPE P_PERNR
    IV_ACTION_TYPE TYPE ZE_HRFIORI_ACTTYPE
    IV_REASON TYPE ZE_HRFIORI_REASON
    IV_REASON_OLD TYPE ZE_HRFIORI_REASON OPTIONAL
    IV_BEGDA TYPE BEGDA
    IV_ENDDA TYPE ENDDA
    IV_STEP TYPE STRING
    IV_UNAME TYPE UNAME DEFAULT SY-UNAME
  EXPORTING
    EV_IS_OK TYPE XFELD
    ES_RETURN TYPE BAPIRET2.




  DATA lo_offboarding_req TYPE REF TO zcl_hr_fiori_offboarding_req.
  DATA lv_is_ok TYPE xfeld.
  DATA lv_guid TYPE ze_hrfiori_guidreq.
  DATA lv_closed TYPE xfeld.
  DATA ls_user_pernr TYPE ycl_bc_user_info=>ty_user_pernr.

  lo_offboarding_req = zcl_hr_fiori_offboarding_req=>get_instance( ).

  "Get pernr who did action from uname
  ycl_bc_user_info=>get_pernr_from_user( EXPORTING iv_uname = iv_uname
                                                   iv_exact = abap_true
                                         IMPORTING rv_user_pernr = ls_user_pernr ).

  CASE iv_step.
    WHEN 'REQUEST_INIT'.  "Initialisation de la request
      lo_offboarding_req->create_request( EXPORTING iv_pernr = iv_pernr
                                                    iv_reason = iv_reason
                                                    iv_action_type = iv_action_type
                                                    iv_endda = iv_endda
                                                    iv_effective_date = iv_begda
                                                    iv_updater = ls_user_pernr-pernr
                                          IMPORTING es_return = es_return
                                          RECEIVING rv_success = lv_is_ok ).
      IF lv_is_ok = abap_true.
        ev_is_ok = abap_true.
      ELSE.
        ev_is_ok = abap_false.
      ENDIF.
    WHEN 'UPDATE_DATA'.   "Seulement pour la mise à jour de données au niveau de la request
      lo_offboarding_req->update_effective_date_reason( EXPORTING iv_pernr = iv_pernr
                                                                  iv_effective_date = iv_begda
                                                                  iv_reason = iv_reason_old
                                                                  iv_reason_new = iv_reason
                                                                  iv_end_date = iv_endda
                                                        RECEIVING rs_return = es_return ).
    WHEN OTHERS.
      IF iv_step = 'CLOSED'.
        lv_closed = abap_true.
      ENDIF.
      lo_offboarding_req->update_request( EXPORTING iv_action_type = iv_action_type
                                                    iv_effective = iv_begda
                                                    iv_step = iv_step
                                                    iv_updater = ls_user_pernr-pernr
                                                    iv_reason = iv_reason
                                                    iv_pernr = iv_pernr
                                                    iv_closed = lv_closed
                                          CHANGING  cv_guid = lv_guid
                                          RECEIVING rv_ok = lv_is_ok ).
      IF lv_is_ok = abap_true.
        ev_is_ok = abap_true.
      ELSE.
        es_return-number = '108'.
        es_return-id = 'YWF_PA'.
        es_return-type = 'E'.
        MESSAGE ID es_return-id TYPE es_return-type NUMBER es_return-number
                WITH es_return-message_v1 es_return-message_v2 es_return-message_v3 es_return-message_v4
                INTO es_return-message.
        ev_is_ok = abap_false.
      ENDIF.
  ENDCASE.

ENDFUNCTION.