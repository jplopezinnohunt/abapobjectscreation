  METHOD check_attachment.

    DATA: lv_step_guid         TYPE asr_guid,
          ls_attachment        TYPE hrasr00attachment ##NEEDED,
          ls_attachment_buffer TYPE hrasr00attachment_dtl ##NEEDED,
          lt_attachment        TYPE hrasr00attachment_tab,
          lt_attachment_buffer TYPE hrasr00attachment_dtl_tab,
          lt_message           TYPE hrasr_return_tab,
          lo_process           TYPE REF TO if_hrasr00_process_execute,
          lo_process_buffer    TYPE REF TO if_hrasr00_proc_obj_handler,
          lo_message_handler   TYPE REF TO cl_hrasr00_dt_message_list.


    IF iv_scenario_guid IS INITIAL AND iv_process_guid IS INITIAL.
* --------------------------------------------------------------------
*   Case IV_SCENARIO_GUID IS INITIAL and IV_PROCESS_GUID IS INITIAL
*     ==> Request submitted by employee without passing by DRAFT step
* --------------------------------------------------------------------

      TRY.
          lo_process = cl_hrasr00_process_execute=>get_instance(
                          iv_process = iv_process ).
        CATCH cx_hrasr00_process_execute ##NO_HANDLER.
      ENDTRY.

      lo_process->get_attachments(
          IMPORTING
            et_attachments  =     lt_attachment
          CHANGING
            ct_message_list =     lt_message " Internet Service Request: Return Table
        ).

      ev_attachment_exist = abap_false.
      LOOP AT lt_attachment INTO ls_attachment
        WHERE attachment_type = iv_attachment_type.
        EXIT.
      ENDLOOP.

      IF sy-subrc <> 0 OR ( sy-subrc = 0 AND ls_attachment-attachment_filename IS INITIAL ).
        ev_attachment_exist = abap_false.
      ELSE.
        ev_attachment_exist = abap_true.
      ENDIF.

    ELSEIF ( iv_scenario_guid IS INITIAL AND iv_process_guid IS NOT INITIAL ) OR
      ( iv_scenario_guid IS NOT INITIAL AND iv_process_guid IS NOT INITIAL ).
* --------------------------------------------------------------------
*   Case IV_SCENARIO_GUID IS INITIAL and IV_PROCESS_GUID IS NOT INITIAL
*     ==> Request submitted by employee after passing by DRAFT step
*   Case IV_SCENARIO_GUID IS NOT INITIAL and IV_PROCESS_GUID IS NOT INITIAL
*     ==> Request is resubmited by Employee
* --------------------------------------------------------------------

      CREATE OBJECT lo_message_handler.

      get_step_for_a_request( EXPORTING iv_process_guid = iv_process_guid
                                        iv_status = 'DRAFT'
                              IMPORTING ov_step_guid = lv_step_guid ).
      IF lv_step_guid IS  INITIAL.
        get_step_for_a_request( EXPORTING iv_process_guid = iv_process_guid
                                          iv_status = ''
                                IMPORTING ov_step_guid = lv_step_guid ).
      ENDIF.

      cl_hrasr00_proc_obj_handler=>get_instance(
      EXPORTING message_handler = lo_message_handler
                step_guid = lv_step_guid
                process_name = iv_process
                activity     = 'R'
      IMPORTING instance = lo_process_buffer ).
      lo_process_buffer->get_attachments( EXPORTING message_handler = lo_message_handler
                                          IMPORTING attachments = lt_attachment_buffer ).



      ev_attachment_exist = abap_false.
      LOOP AT lt_attachment_buffer INTO ls_attachment_buffer
        WHERE attachment_type = iv_attachment_type.
        ev_attachment_exist = abap_true.
      ENDLOOP.

    ENDIF.

  ENDMETHOD.
