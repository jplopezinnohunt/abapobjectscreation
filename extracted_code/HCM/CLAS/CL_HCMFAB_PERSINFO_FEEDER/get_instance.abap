METHOD get_instance.

  DATA ls_feeder_instance TYPE ty_s_feeder_instance.

  READ TABLE gt_feeder_instance WITH KEY pernr = iv_pernr infty = iv_infty INTO ls_feeder_instance.
  IF sy-subrc EQ 0 AND ls_feeder_instance-feeder IS NOT INITIAL.
    ro_feeder = ls_feeder_instance-feeder.
  ELSE.
    ls_feeder_instance-pernr = iv_pernr.
    ls_feeder_instance-infty = iv_infty.

    CREATE OBJECT ls_feeder_instance-feeder
      EXPORTING
        iv_pernr = iv_pernr
        iv_infty = iv_infty
        iv_user_today = iv_user_today.

    APPEND ls_feeder_instance TO gt_feeder_instance.

    ro_feeder = ls_feeder_instance-feeder.

  ENDIF.

ENDMETHOD.
