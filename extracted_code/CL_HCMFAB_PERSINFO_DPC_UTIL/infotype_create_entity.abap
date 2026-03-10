METHOD infotype_create_entity.

  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lt_messages TYPE bapirettab.
  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lv_subty_fieldname TYPE fieldname.
  DATA lx_hcmfab_common TYPE REF TO cx_hcmfab_common.

  FIELD-SYMBOLS <lv_pernr> TYPE pernr_d.
  FIELD-SYMBOLS <lv_infty> TYPE infty.
  FIELD-SYMBOLS <lv_subty> TYPE subty.

  io_data_provider->read_entry_data( IMPORTING es_data = es_entity ).

  ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_pernr OF STRUCTURE es_entity TO <lv_pernr>.
  ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_infty OF STRUCTURE es_entity TO <lv_infty>.

* ensure that content is only retrieved for own PERNR
  TRY.
      CALL METHOD go_employee_api->do_employeenumber_validation
        EXPORTING
          iv_pernr          = <lv_pernr>
          iv_application_id = iv_app_id.

      lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = <lv_pernr> iv_infty = <lv_infty> ).

      MOVE-CORRESPONDING es_entity TO ls_pskey.
* fill subtype field of UI structure.
* Otherwise ITF rejects inserting the new record
      lv_subty_fieldname = get_subtype_fieldname( ls_pskey-hcmfab_infty ).
      ASSIGN COMPONENT lv_subty_fieldname OF STRUCTURE es_entity TO <lv_subty>.
      IF <lv_subty> IS ASSIGNED.
        <lv_subty> = ls_pskey-hcmfab_subty.
      ENDIF.

      CALL METHOD lo_feeder->create
        EXPORTING
          is_pskey       = ls_pskey
          iv_versionid   = iv_versionid
        IMPORTING
          et_messages    = lt_messages
        CHANGING
          cs_main_record = es_entity.

* message handling
      CALL METHOD cl_hcmfab_persinfo_dpc_util=>handle_messages
        EXPORTING
          io_context     = io_context
          iv_entity_name = io_tech_request_context->get_entity_type_name( )
          is_pskey       = ls_pskey                         "n2709841
          it_messages    = lt_messages.

    CATCH cx_hcmfab_common INTO lx_hcmfab_common.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_hcmfab_common )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
