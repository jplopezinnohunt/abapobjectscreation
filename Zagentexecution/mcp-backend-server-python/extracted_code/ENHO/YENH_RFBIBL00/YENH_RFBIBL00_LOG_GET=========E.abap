ENHANCEMENT 1  .
"DATA yyo_rfbibl00_util TYPE REF TO ycl_fi_rfbibl00_util.
DATA yyo_rfbibl00_area TYPE REF TO ycl_fi_rfbibl00_shm_area.
DATA yyv_get_protocol TYPE xfeld.
DATA yyv_no_active_shm TYPE xfeld VALUE abap_false.
DATA yyt_message TYPE FB_T_FIMSG.
DATA yyt_efile TYPE ytt_string.

IF xlog = 'X'.
  TRY.
      yyo_rfbibl00_area = ycl_fi_rfbibl00_shm_area=>attach_for_read( ).
    CATCH cx_root.
      yyv_no_active_shm = abap_true.
  ENDTRY.

  IF yyv_no_active_shm = abap_false.
    yyo_rfbibl00_area->root->get_shared_memory( importing ev_get_protocol = yyv_get_protocol ).
    yyo_rfbibl00_area->detach( ).
    IF yyv_get_protocol = abap_true.
      CALL FUNCTION 'FI_MESSAGE_GET'
        TABLES
          t_fimsg    = yyt_message
        EXCEPTIONS
          no_message = 1
          OTHERS     = 2.
      IF sy-subrc <> 0.
        CLEAR yyt_message.
      ELSE.
        TRY.
            yyo_rfbibl00_area = ycl_fi_rfbibl00_shm_area=>attach_for_update( ).
          CATCH cx_root.
        ENDTRY.
        CLEAR yyt_efile.
        LOOP AT efile INTO DATA(yyefile).
          APPEND yyefile-rec TO yyt_efile.
        ENDLOOP.
        yyo_rfbibl00_area->root->set_shared_memory( exporting iv_get_protocol = yyv_get_protocol
                                                              it_message = yyt_message
                                                              iv_error_run = error_run
                                                              it_bibl_file = yyt_efile ).
        yyo_rfbibl00_area->detach_commit( ).
      ENDIF.
    ENDIF.
    EXIT.
  ENDIF.
ENDIF.

ENDENHANCEMENT.
