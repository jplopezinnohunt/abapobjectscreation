*******************************************************************************
* Procjet           : UNESCO wave 1                                           *
* Module            : Inboarding                                              *
*-----------------------------------------------------------------------------*
* Author            :  Saad Igueninni                                         *
* Date              :  12.09.2025                                             *
*-----------------------------------------------------------------------------*
* Description   :  get expanded                                               *
*******************************************************************************
  METHOD /iwbep/if_mgw_appl_srv_runtime~get_expanded_entity.

    DATA : ls_reqheader_main_data TYPE zcl_hr_fiori_request=>ts_reqheader_main_data.
    DATA:
      lt_keys         TYPE        /iwbep/t_mgw_tech_pairs,
      lv_request_id   TYPE        os_guid,
      " error handling
      lr_hr_benef_exc TYPE REF TO zcx_hr_benef_exception.

    FIELD-SYMBOLS <key> LIKE LINE OF lt_keys.
    DATA: lv_entity_set_name TYPE /iwbep/mgw_tech_name,
          ls_reqheader       TYPE zcl_zhr_benefits_reque_mpc=>ts_requestheader,
          ls_key_tab         TYPE /iwbep/s_mgw_name_value_pair,
          ls_eg_main         TYPE zcl_zhr_benefits_reque_mpc=>ts_reqeducationgrantmain,
          ls_rs_main         TYPE zcl_zhr_benefits_reque_mpc=>ts_reqrentalsubsmain.
    DATA : lo_education    TYPE REF TO zcl_hr_fiori_education_grant.

* Get Entity Set Name
    lv_entity_set_name     = io_tech_request_context->get_entity_set_name( ).

    CASE lv_entity_set_name.
      WHEN 'RequestHeaderSet'.

        TRY.
            lt_keys = io_tech_request_context->get_keys( ).
            READ TABLE lt_keys ASSIGNING <key> INDEX 1.
            lv_request_id = <key>-value.

            "Get request Header first
            zcl_hr_fiori_request=>get_instance( )->get_request(
              EXPORTING
                iv_request_guid =   lv_request_id               " Globally Unique Identifier
              IMPORTING
                es_result       =  ls_reqheader
            ).


**********************************************************************************************
**********************              Education Grant             ******************************
**********************************************************************************************

            IF ls_reqheader-request_type EQ zcl_hr_fiori_request=>c_request_type_eg.
              MOVE-CORRESPONDING ls_reqheader TO ls_reqheader_main_data.
              CREATE OBJECT lo_education.
              "Get request detail
              ls_eg_main =  CORRESPONDING #( zcl_hr_fiori_request=>get_instance( )->get_eg_request_detail( EXPORTING
                               iv_guid =   lv_request_id ) ).
              MOVE-CORRESPONDING ls_eg_main TO ls_reqheader_main_data-toedugrantdetail.
              ls_reqheader_main_data-toedugrantdetail-guid = lv_request_id.
              "Get request advances/claims


              IF ls_reqheader-isadvance EQ abap_true.
                lo_education->get_advances_list(
                  EXPORTING
                    iv_guid     =     lv_request_id             " Benefits request - GUID Request
                  IMPORTING
                    et_advances = ls_reqheader_main_data-toedugrantadvances
                ).

              ENDIF.

              IF ls_reqheader-isclaim EQ abap_true.
                lo_education->get_claims_list(
                  EXPORTING
                    iv_guid     =     lv_request_id             " Benefits request - GUID Request
                  IMPORTING
                    et_claims = ls_reqheader_main_data-toedugrantclaims
                ).
              ENDIF.
*****************************
            ENDIF.

**********************************************************************************************
**********************              Rental Subsidy             *******************************
**********************************************************************************************
            IF ls_reqheader-request_type EQ zcl_hr_fiori_request=>c_request_type_rs.
              MOVE-CORRESPONDING ls_reqheader TO ls_reqheader_main_data.

              "Get request detail
              ls_rs_main =  CORRESPONDING #( zcl_hr_fiori_request=>get_instance( )->get_rs_request_detail( EXPORTING
                               iv_guid =   lv_request_id ) ).
              MOVE-CORRESPONDING ls_rs_main TO ls_reqheader_main_data-torentalsubsidydetail.
              ls_reqheader_main_data-torentalsubsidydetail-guid = lv_request_id.
            ENDIF.
            copy_data_to_ref( EXPORTING is_data = ls_reqheader_main_data
                              CHANGING  cr_data = er_entity ).

          CATCH zcx_hr_benef_exception INTO lr_hr_benef_exc.

            RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
              EXPORTING
                textid            = /iwbep/cx_mgw_busi_exception=>business_error_unlimited
                message_unlimited = lr_hr_benef_exc->get_text( ).

        ENDTRY.

*      WHEN OTHERS
    ENDCASE.
  ENDMETHOD.

*            SELECT SINGLE * FROM zthrfiori_breq  INTO CORRESPONDING FIELDS OF @ls_reqheader WHERE guid EQ @lv_request_id.
*            IF sy-subrc NE 0.
*
*              ##TODO " raise exception here
*            ELSE.
*
*              SELECT SINGLE * FROM zthrfiori_eg_mai  INTO @ls_eg_main WHERE guid EQ @lv_request_id.
*
*            ENDIF.

*    Set both header and item data to the response
