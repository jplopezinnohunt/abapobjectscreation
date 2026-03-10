  METHOD is_hra_or_hro.

    DATA: lv_actor_id      TYPE ze_hrfiori_actor,
          ls_actor         TYPE zthrfiori_actor,
          ls_return        TYPE zcl_zhr_benefits_commo_mpc_ext=>ts_actor,
          lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits.

    CREATE OBJECT lo_benefits_util.

*   Check role of connected user: HRA or HRO ?
    lo_benefits_util->is_hra_or_hro_actor( IMPORTING ov_actor_role = lv_actor_id ).
    SELECT SINGLE * INTO ls_actor
      FROM zthrfiori_actor
        WHERE id = lv_actor_id
          AND language = sy-langu.
    MOVE ls_actor TO ls_return.

    copy_data_to_ref( EXPORTING is_data = ls_return
                    CHANGING cr_data  = os_return ).

  ENDMETHOD.
