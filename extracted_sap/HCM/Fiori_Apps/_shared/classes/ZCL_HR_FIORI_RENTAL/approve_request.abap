  METHOD approve_request.

    DATA:lv_usrid       TYPE sysid,
         lv_pernr       TYPE persno,
         lv_last_name   TYPE pad_nachn,
         lv_first_name  TYPE pad_vorna,
         lv_return_code TYPE syst_subrc,
         lv_message     TYPE string,
         lo_util        TYPE REF TO zcl_hr_fiori_benefits.

    os_return-returncode = '0'.

    CREATE OBJECT lo_util.

*   Get actor infos (current user)
    lo_util->get_actor_infos( IMPORTING ov_first_name = lv_first_name
                               ov_last_name = lv_last_name
                               ov_pernr = lv_pernr
                               ov_usrid = lv_usrid ).

    CASE iv_actor.
      WHEN c_hra.
*       HRA approves and sends request to HRO
*       1-Update table of  request
        lo_util->update_req_table( EXPORTING  iv_guid = iv_guid
                                     iv_new_status = c_req_approved_hra_sent_hro
                                     iv_next_actor = c_hro
                                     iv_upd_first_name = lv_first_name
                                     iv_upd_last_name = lv_last_name
                                     iv_upd_pernr = lv_pernr
                                     iv_upd_usrid = lv_usrid
                                     iv_update_date = sy-datum
                                     iv_update_time = sy-uzeit
                                   IMPORTING ov_return_code = lv_return_code
                                             ov_message = lv_message ).
        IF lv_return_code <> 0.
          os_return-returncode = lv_return_code.
          os_return-message = lv_message.
          RETURN.
        ENDIF.

*       2-Update history log
        lo_util->update_histo_table( EXPORTING iv_actor = c_hra
                                      iv_guid = iv_guid
                                      iv_new_status = c_req_approved_hra_sent_hro
                                      iv_upd_first_name = lv_first_name
                                      iv_upd_last_name = lv_last_name
                                      iv_upd_pernr = lv_pernr
                                      iv_upd_usrid = lv_usrid
                                      iv_update_date = sy-datum
                                      iv_update_time = sy-uzeit
                                     IMPORTING ov_return_code = lv_return_code
                                               ov_message = lv_message ).
        IF lv_return_code <> 0.
          os_return-returncode = lv_return_code.
          os_return-message = lv_message.
          RETURN.
        ENDIF.

*       3-Update coment log
        IF iv_coment IS NOT INITIAL.
          lo_util->create_coment_for_request( EXPORTING iv_actor = c_hra
                                                   iv_coment = iv_coment
                                                   iv_date   = sy-datum
                                                   iv_guid   = iv_guid
                                                   iv_pernr  = lv_pernr
                                                   iv_time   = sy-uzeit
                                                   iv_usrid  = lv_usrid
                                         IMPORTING ov_return_code = lv_return_code
                                                   ov_message = lv_message ).
          IF lv_return_code <> 0.
            os_return-returncode = lv_return_code.
            os_return-message = lv_message.
            RETURN.
          ENDIF.
        ENDIF.

      WHEN c_hro.
*       HRO approves, end of process
*       1-Creation of infotype 0962
        create_infotype_0962( EXPORTING iv_guid = iv_guid
                              IMPORTING ov_return_code = lv_return_code
                                        ov_message = lv_message ).
        IF lv_return_code <> 0.
          os_return-returncode = lv_return_code.
          os_return-message = lv_message.
          RETURN.
        ENDIF.


*       2-Update table of  request
        lo_util->update_req_table( EXPORTING  iv_guid = iv_guid
                                     iv_new_status = c_req_approved_hro
                                     iv_next_actor = c_no_actor
                                     iv_upd_first_name = lv_first_name
                                     iv_upd_last_name = lv_last_name
                                     iv_upd_pernr = lv_pernr
                                     iv_upd_usrid = lv_usrid
                                     iv_update_date = sy-datum
                                     iv_update_time = sy-uzeit
                                   IMPORTING ov_return_code = lv_return_code
                                             ov_message = lv_message ).
        IF lv_return_code <> 0.
          os_return-returncode = lv_return_code.
          os_return-message = lv_message.
          RETURN.
        ENDIF.

*       3-Update history log
        lo_util->update_histo_table( EXPORTING iv_actor = c_hro
                                      iv_guid = iv_guid
                                      iv_new_status = c_req_approved_hro
                                      iv_upd_first_name = lv_first_name
                                      iv_upd_last_name = lv_last_name
                                      iv_upd_pernr = lv_pernr
                                      iv_upd_usrid = lv_usrid
                                      iv_update_date = sy-datum
                                      iv_update_time = sy-uzeit
                                     IMPORTING ov_return_code = lv_return_code
                                               ov_message = lv_message ).
        IF lv_return_code <> 0.
          os_return-returncode = lv_return_code.
          os_return-message = lv_message.
          RETURN.
        ENDIF.

*       4-Update coment log
        IF iv_coment IS NOT INITIAL.
          lo_util->create_coment_for_request( EXPORTING iv_actor = c_hro
                                                   iv_coment = iv_coment
                                                   iv_date   = sy-datum
                                                   iv_guid   = iv_guid
                                                   iv_pernr  = lv_pernr
                                                   iv_time   = sy-uzeit
                                                   iv_usrid  = lv_usrid
                                         IMPORTING ov_return_code = lv_return_code
                                                   ov_message = lv_message ).
          IF lv_return_code <> 0.
            os_return-returncode = lv_return_code.
            os_return-message = lv_message.
            RETURN.
          ENDIF.
        ENDIF.

    ENDCASE.

  ENDMETHOD.
