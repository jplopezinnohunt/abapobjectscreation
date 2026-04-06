  METHOD if_hrasr00gen_service~get_operations.

    DATA: ls_operation    TYPE hrasr00gs_operation,
          ls_fieldnames   TYPE hrbas_fieldlist_tab,
          ls_tab_metadata TYPE t5asrfio_mdata,
          lt_tab_metadata TYPE STANDARD TABLE OF t5asrfio_mdata,
          lo_common       TYPE REF TO zcl_hrfiori_pf_common.

    CREATE OBJECT lo_common.
    lo_common->get_metadata_form_fields( EXPORTING iv_form_scenario = 'ZHR_BIRTH_CHILD'
                                                   iv_scenario_version = '00000'
                                         IMPORTING ot_metadata_fields = lt_tab_metadata ).

    LOOP  AT lt_tab_metadata INTO ls_tab_metadata.
      APPEND ls_tab_metadata-field_name TO ls_fieldnames.
    ENDLOOP.

    ls_operation-operation = 'SPEC'.
    ls_operation-fieldnames = ls_fieldnames.

    APPEND ls_operation TO operations.

  ENDMETHOD.
