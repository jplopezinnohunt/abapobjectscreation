METHOD infotype_update_entity.

  DATA ls_pskey TYPE hcmfab_s_pers_pskey.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.
  DATA lt_messages TYPE bapirettab.
  DATA lx_hcmfab_common TYPE REF TO cx_hcmfab_common.

  FIELD-SYMBOLS <lv_begda> TYPE begda.
  FIELD-SYMBOLS <lv_fio_begda> TYPE begda.
  FIELD-SYMBOLS <lv_endda> TYPE endda.
  FIELD-SYMBOLS <lv_fio_endda> TYPE endda.

  io_data_provider->read_entry_data( IMPORTING es_data = es_entity ).

  ls_pskey = get_pskey_from_key( io_tech_request_context->get_keys( ) ).

* ensure that content is only retrieved for own PERNR
  TRY.
      CALL METHOD go_employee_api->do_employeenumber_validation
        EXPORTING
          iv_pernr          = ls_pskey-hcmfab_pernr
          iv_application_id = iv_app_id.

      lo_feeder = cl_hcmfab_persinfo_feeder=>get_instance( iv_pernr = ls_pskey-hcmfab_pernr iv_infty = ls_pskey-hcmfab_infty ).

* most probably this is not necessary!!!
* reflect changes of HCMFAB_BEGDA/HCMFAB_ENDDA in BEGDA/ENDDA
      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-begda  OF STRUCTURE es_entity TO <lv_begda>.
      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_begda OF STRUCTURE es_entity TO <lv_fio_begda>.
      <lv_begda> = <lv_fio_begda>.
*  er_entity-begda = er_entity-fio_begda.
      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-endda OF STRUCTURE es_entity TO <lv_endda>.
      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_endda OF STRUCTURE es_entity TO <lv_fio_endda>.
      <lv_endda> = <lv_fio_endda>.


      CALL METHOD lo_feeder->update
        EXPORTING
          is_pskey       = ls_pskey
          iv_versionid   = iv_versionid
        IMPORTING
          et_messages    = lt_messages
        CHANGING
          cs_entity_main = es_entity.

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
