  METHOD get_computed_value_natio.

    DATA: lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits.

    CREATE OBJECT lo_benefits_util.
    lo_benefits_util->get_actor_infos( EXPORTING iv_pernr = iv_pernr
                                       IMPORTING ov_natio = ov_natio ).

  ENDMETHOD.
