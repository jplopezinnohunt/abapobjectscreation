METHOD execute_action_terms_condition.
  DATA: lt_lines TYPE STANDARD TABLE OF tline,
      ls_parameter LIKE LINE OF it_parameter,
      ls_head TYPE thead,
      lv_dstate TYPE dokstate,
      lv_doc_object TYPE doku_obj,
      ls_t100_msg TYPE scx_t100key.

  CLEAR:lv_doc_object,lt_lines,lv_dstate,ls_head.
  IF it_parameter IS NOT INITIAL.
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'DocObject'.
    IF sy-subrc = 0.
      lv_doc_object = ls_parameter-value.
    ENDIF.
  ENDIF.

  IF lv_doc_object IS NOT INITIAL.
    CALL FUNCTION 'DOCU_GET_FOR_F1HELP'
      EXPORTING
        id       = 'TX'
        langu    = sy-langu
        object   = lv_doc_object
      IMPORTING
        dokstate = lv_dstate
        head     = ls_head
      TABLES
        line     = lt_lines
      EXCEPTIONS
        ret_code = 1
        OTHERS   = 2.
    IF sy-subrc NE 0.
****No valid doc object exists
        CLEAR ls_t100_msg.
        ls_t100_msg-msgid = c_msg_class_enro.
        ls_t100_msg-msgno = '015'.
        RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
          EXPORTING
            textid = ls_t100_msg.
    ENDIF.
    IF lt_lines IS NOT INITIAL.
      copy_data_to_ref(
       EXPORTING
         is_data = lt_lines
       CHANGING
         cr_data = er_data
      ).
    ENDIF.
  ENDIF.

ENDMETHOD.
