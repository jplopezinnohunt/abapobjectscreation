  METHOD get_computed_value_kdgbr.

    DATA: lv_pernr         TYPE persno,
          ls_eve_log       TYPE pun_logging,
          lt_eve_log       TYPE hrpadun_logging,
          lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits,
          lo_eve           TYPE REF TO cl_hrpadun_eve_environment.

    IF iv_pernr IS INITIAL.
      CREATE OBJECT lo_benefits_util.
      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
    ELSE.
      lv_pernr = iv_pernr.
    ENDIF.

    CREATE OBJECT lo_eve.
    CALL METHOD lo_eve->is_eligible
      EXPORTING
        i_pernr   = lv_pernr
        i_begda   = iv_begda
        i_endda   = iv_begda
        i_entl_id = c_entitlement_id
        i_molga   = c_molga_un
        i_objps   = iv_child_nb
        i_subty   = c_child_subty
      IMPORTING
        e_log_tab = lt_eve_log.

    LOOP AT lt_eve_log INTO ls_eve_log.
      ov_kdgbr = ls_eve_log-is_eligible.
    ENDLOOP.

  ENDMETHOD.
