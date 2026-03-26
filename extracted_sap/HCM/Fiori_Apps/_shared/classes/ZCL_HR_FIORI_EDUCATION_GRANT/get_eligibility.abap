  METHOD get_eligibility.
    DATA lv_kid_eli  TYPE boole_d.
    DATA : lv_emp_eli  TYPE boole_d.

    DATA lt_p0000  TYPE p0000_tab.
    DATA lt_p0001  TYPE p0001_tab.
    DATA lt_p0002  TYPE p0002_tab.
    DATA lt_p0008  TYPE p0008_tab.
    DATA lt_p0016  TYPE p0016_tab.
    DATA ls_p0021   TYPE p0021.
    DATA:lr_eve      TYPE REF TO cl_hrpadun_eve_environment,  lr_msg_list    TYPE REF TO cl_hrpa_message_list.
    DATA l_pnnnn TYPE prelp.
    DATA lt_pnnnn TYPE prelp_tab.
    DATA : lt_eve_log TYPE hrpadun_logging, ls_eve_log     TYPE pun_logging.
    DATA l_emp_eli  TYPE boole_d.
    DATA l_kid_eli  TYPE boole_d.
    DATA gt_p0021  TYPE p0021_tab.
    DATA lt_p0021  TYPE p0021_tab.
    DATA : lv_begda_eli TYPE d, lv_endda_eli TYPE d.
*    data ls_p0021 type p0021.
    DATA lt_c0021  TYPE hrpadun_eg_child.

    "code repris du module pool du 965
    CALL METHOD cl_hrpadun_eg_appl=>get_children
      EXPORTING
        pernr    = is_p0965-pernr
        begda    = '18000101'
        endda    = '99991231'
        gt_p0021 = gt_p0021
      IMPORTING
        lt_p0021 = lt_p0021
        lt_c0021 = lt_c0021.

    LOOP AT lt_p0021 INTO ls_p0021 WHERE begda <= is_p0965-endda
                                          AND   endda >= is_p0965-begda
                                          AND   subty  = is_p0965-subty
                                          AND   objps  = is_p0965-objps.
      EXIT.
    ENDLOOP.


    CALL METHOD cl_hr_pnnnn_type_cast=>pnnnn_to_prelp
      EXPORTING
        pnnnn = is_p0965
      IMPORTING
        prelp = l_pnnnn.

    l_pnnnn-infty = '0965'.
    APPEND l_pnnnn TO lt_pnnnn.

    CREATE OBJECT lr_eve.
    IF iv_elibegda IS NOT INITIAL .
      lv_begda_eli = iv_elibegda.
    ELSE.
      lv_begda_eli = is_p0965-begda.
    ENDIF.

    IF iv_eliendda IS NOT INITIAL .
      lv_endda_eli = iv_eliendda.
    ELSE.
      lv_endda_eli = is_p0965-endda.
    ENDIF.

    CALL METHOD lr_eve->is_eligible
      EXPORTING
        i_pernr        = is_p0965-pernr
        i_begda        =  lv_begda_eli
        i_endda        = lv_endda_eli
        i_entl_id      = 'EDUGR'
        i_molga        = 'UN'
        i_objps        = is_p0965-objps
        i_subty        = is_p0965-subty
        it_prelp       = lt_pnnnn
      IMPORTING
        e_log_tab      = lt_eve_log
        er_msg_handler = lr_msg_list.

    READ TABLE lt_eve_log INTO ls_eve_log WITH KEY is_eligible = 'X'.
    IF sy-subrc = 0.
      l_emp_eli = ls_eve_log-is_eligible.
    ENDIF.


    CALL METHOD cl_hrpadun_eg_check=>check_child
      EXPORTING
        pernr       = is_p0965-pernr
        p0021       = ls_p0021
        p0965       = is_p0965
      IMPORTING
        is_eligible = l_kid_eli.

    IF ( l_emp_eli = abap_true ) AND ( l_kid_eli = abap_true ) .
      er_egsst = abap_false.
    ELSE.
      er_egsst  = abap_true.
    ENDIF.

  ENDMETHOD.
