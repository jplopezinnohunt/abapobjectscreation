  METHOD get_dependancy_status.

    DATA : l_pnnnn     TYPE prelp, lt_pnnnn TYPE prelp_tab,
           lt_eve_log  TYPE hrpadun_logging,ls_eve_log       TYPE pun_logging,lr_msg_list    TYPE REF TO cl_hrpa_message_list,
           lr_eve      TYPE REF TO cl_hrpadun_eve_environment,
           ls_main_eg  TYPE zthrfiori_eg_mai
          .

    "Logic from MP 0965
    CLEAR: lt_pnnnn.
    IF lr_eve IS INITIAL.
      CREATE OBJECT lr_eve.
    ENDIF.


    CALL METHOD cl_hr_pnnnn_type_cast=>pnnnn_to_prelp
      EXPORTING
        pnnnn = is_p0965
      IMPORTING
        prelp = l_pnnnn.

    l_pnnnn-infty = '0965'.
    APPEND l_pnnnn TO lt_pnnnn.

    CREATE OBJECT lr_eve.
    CALL METHOD lr_eve->is_eligible
      EXPORTING
        i_pernr        = IS_p0965-pernr
        i_begda        = IS_p0965-begda
        i_endda        = IS_p0965-begda
        i_entl_id      = 'DPCHI'
        i_molga        = 'UN'
        i_objps        = IS_p0965-objps
        i_subty        = IS_p0965-subty
      IMPORTING
        e_log_tab      = lt_eve_log
        er_msg_handler = lr_msg_list.

    LOOP AT lt_eve_log INTO ls_eve_log.
*      ls_main_eg-kdgbr = ls_eve_log-is_eligible.
      rv_kdgbr = ls_eve_log-is_eligible.
    ENDLOOP.

  ENDMETHOD.
