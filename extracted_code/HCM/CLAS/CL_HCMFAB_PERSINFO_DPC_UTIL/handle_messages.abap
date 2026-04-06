METHOD handle_messages.

  DATA lo_message_container TYPE REF TO /iwbep/if_message_container.
  DATA lt_messages TYPE bapirettab.
  DATA lv_fieldpos TYPE i.
  DATA lt_key_tab TYPE /iwbep/t_mgw_name_value_pair.
  DATA ls_key_tab TYPE /iwbep/s_mgw_name_value_pair.
  DATA lo_metadata_provider TYPE REF TO /iwbep/if_mgw_med_provider.
  DATA lv_internal_service_name TYPE  /iwbep/med_grp_technical_name.
  DATA lv_internal_service_version  TYPE  /iwbep/med_grp_version.
  DATA lo_model	TYPE REF TO	/iwbep/cl_mgw_odata_model.
  DATA lv_target TYPE /iwbep/sup_mc_message_target.
  DATA ls_entity TYPE /iwbep/if_mgw_med_odata_types=>ty_s_med_entity_type.
  DATA ls_prop TYPE /iwbep/if_mgw_med_odata_types=>ty_s_med_property.
  DATA lv_leading_message TYPE boole_d.

  FIELD-SYMBOLS <ls_message> TYPE bapiret2.

  IF it_messages IS NOT INITIAL.
    lt_messages = it_messages.
    DELETE lt_messages WHERE type <> 'E'.
    IF lt_messages IS NOT INITIAL.
      lo_message_container = io_context->get_message_container( ).

      IF is_pskey IS SUPPLIED.                              "n2709841
* fill lt_key_tab from is_pskey
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_pernr.
        ls_key_tab-value = is_pskey-hcmfab_pernr.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_infty.
        ls_key_tab-value = is_pskey-hcmfab_infty.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_subty.
        ls_key_tab-value = is_pskey-hcmfab_subty.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_objps.
        ls_key_tab-value = is_pskey-hcmfab_objps.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_sprps.
        ls_key_tab-value = is_pskey-hcmfab_sprps.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_begda.
        ls_key_tab-value = is_pskey-hcmfab_begda.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_endda.
        ls_key_tab-value = is_pskey-hcmfab_endda.
        APPEND ls_key_tab TO lt_key_tab.
        ls_key_tab-name =  cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_seqnr.
        ls_key_tab-value = is_pskey-hcmfab_seqnr.
        APPEND ls_key_tab TO lt_key_tab.
      ENDIF.

      io_context->get_parameter( EXPORTING
                               iv_name  = /iwbep/if_mgw_context=>gc_param_isn
                             IMPORTING
                               ev_value = lv_internal_service_name ).

      io_context->get_parameter( EXPORTING
                                   iv_name  = /iwbep/if_mgw_context=>gc_param_isv
                                 IMPORTING
                                   ev_value = lv_internal_service_version ).
      lo_metadata_provider = /iwbep/cl_mgw_med_provider=>get_med_provider( ).

      TRY.

          lo_model ?= lo_metadata_provider->get_service_metadata(
            iv_internal_service_name    = lv_internal_service_name
            iv_internal_service_version = lv_internal_service_version
          ).

        CATCH /iwbep/cx_mgw_med_exception.              "#EC NO_HANDLER
      ENDTRY.

      lv_leading_message = abap_true.
      LOOP AT lt_messages ASSIGNING <ls_message>.           "n2709841
        IF <ls_message>-field CS '-'.
* remove structure name so that OData runtime can retrieve property name from ABAP fieldname
          lv_fieldpos = sy-fdpos + 1.
          IF lv_fieldpos < numofchar( <ls_message>-field ).
            <ls_message>-field = <ls_message>-field+lv_fieldpos.
          ENDIF.
        ENDIF.


        IF lo_model IS BOUND AND NOT <ls_message>-field IS INITIAL.
          CLEAR lv_target.
* find property name related to ABAP field name
          READ TABLE lo_model->mt_entities INTO ls_entity WITH KEY external_name = iv_entity_name.
          IF sy-subrc = 0.
            READ TABLE ls_entity-properties INTO ls_prop WITH KEY name = <ls_message>-field.
            IF sy-subrc = 0.
              lv_target = ls_prop-external_name.
            ENDIF.
          ENDIF.
        ENDIF.

*      lo_message_container->add_messages_from_bapi(
*        it_bapi_messages          = lt_messages
*        iv_determine_leading_msg  = /iwbep/if_message_container=>gcs_leading_msg_search_option-last
*        iv_entity_type            = iv_entity_name
*        it_key_tab                = lt_key_tab
*        iv_add_to_response_header = abap_true
*      ).
        lo_message_container->add_message_from_bapi(
          is_bapi_message           = <ls_message>
          iv_is_leading_message     = abap_true
          iv_entity_type            = iv_entity_name
          it_key_tab                = lt_key_tab
          iv_add_to_response_header = abap_true
          iv_message_target         = lv_target
        ).

        CLEAR lv_leading_message. "The first message is the leading one
      ENDLOOP.

      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          textid            = if_t100_message=>default_textid
          message_container = lo_message_container.
    ENDIF.
  ENDIF.

ENDMETHOD.
