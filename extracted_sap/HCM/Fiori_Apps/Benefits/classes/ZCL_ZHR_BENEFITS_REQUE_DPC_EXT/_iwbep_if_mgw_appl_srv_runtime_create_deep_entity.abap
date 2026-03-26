*******************************************************************************
* Procjet           : UNESCO wave 1                                           *
* Module            : Inboarding                                              *
*-----------------------------------------------------------------------------*
* Author            :  Saad Igueninni                                         *
* Date              :  12.09.2025                                             *
*-----------------------------------------------------------------------------*
* Description   :  deep inser request update on Save/Submit...                *
*******************************************************************************
  METHOD /iwbep/if_mgw_appl_srv_runtime~create_deep_entity.

* Variables
* =========================

    "Nested structure
    DATA : ls_reqheader_main_data TYPE zcl_hr_fiori_request=>ts_reqheader_main_data.
    DATA: lv_entity_set_name   TYPE /iwbep/mgw_tech_name,
          ls_request_header    TYPE zcl_zhr_benefits_reque_mpc=>ts_requestheader,
          ls_key_tab           TYPE /iwbep/s_mgw_name_value_pair,
          lo_message_container TYPE REF TO /iwbep/if_message_container,
          ls_eg_main           TYPE zthrfiori_eg_mai,
          ls_rs_main           TYPE zthrfiori_rs_mai.
    DATA : lo_education TYPE REF TO zcl_hr_fiori_education_grant,
           lo_rental    TYPE REF TO zcl_hr_fiori_rental.
    DATA: ls_actionreturn      TYPE zcl_zhr_benefits_req_a_mpc_ext=>actionreturn,
          lv_return_code       TYPE syst_subrc,
          lv_message           TYPE string,
          ls_textid            TYPE scx_t100key.

* Init Objects
* ============
    lv_entity_set_name = io_tech_request_context->get_entity_set_name( ).
    lo_message_container = /iwbep/if_mgw_conv_srv_runtime~get_message_container( ).
*  CREATE OBJECT lo_utilities.
*  CLEAR : ls_catsrecords_in,lv_iterator_dat,ls_cat_in,lv_pernr,ls_cat_in,l_subrc.
*  REFRESH : lt_catsrecords_in,lt_recout,lt_message,lt_chkdata,lt_rec2data.

* Case AssociationsSet
* ====================
    CASE lv_entity_set_name.
      WHEN 'RequestHeaderSet'.
        io_data_provider->read_entry_data( IMPORTING es_data = ls_reqheader_main_data   ).
*        lt_cat_in[] = ls_deep_catsrecord-catsheadertocatsrecord[].

        ##TODO "Adapt and clean .... depending on Request Type
        ls_request_header = CORRESPONDING #( ls_reqheader_main_data ).
        DATA ls_request_head_db TYPE zthrfiori_breq.
        ls_request_head_db = CORRESPONDING #( ls_request_header ).

        SELECT SINGLE * FROM zthrfiori_breq  INTO @DATA(ls_existing_head_db) WHERE guid EQ @ls_request_head_db-guid.
        IF ls_request_head_db-request_type EQ zcl_hr_fiori_request=>c_request_type_eg.
          CREATE OBJECT lo_education.

**********************************************************************************************
**********************              Education Grant             ******************************
**********************************************************************************************
          IF ls_request_head_db-request_status NE ls_existing_head_db-request_status.

            IF ls_request_head_db-request_status EQ zcl_hr_fiori_request=>c_req_submited_employee OR ls_request_head_db-request_status EQ zcl_hr_fiori_request=>c_req_submited_employee_claims. "submit
* TICKET 1550
*               IF ls_request_header-isadvance EQ abap_true.
              IF ( ls_request_header-isadvance IS NOT INITIAL
                   AND lines( ls_reqheader_main_data-toedugrantadvances[] ) = 0 )
                OR ( ls_request_header-isclaim IS NOT INITIAL
                   AND lines( ls_reqheader_main_data-toedugrantclaims[] ) = 0 ).
                CLEAR: ls_textid.
                "ls_textid-msgid = 'ZHRFIORI'.
                "ls_textid-msgno = '140'.

                lo_message_container = me->mo_context->get_message_container( ).
                lo_message_container->add_message( EXPORTING iv_msg_type = 'E'
                                                             iv_msg_id = 'ZHRFIORI'
                                                             iv_msg_number = '140' ).

                RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
                  EXPORTING
                    textid            = /iwbep/cx_mgw_busi_exception=>business_error
                    message_container = lo_message_container.

              ENDIF.
*               ENDIF.
*  TICKET 1550
              "change status, update status_txt and NACTOR
              lo_education->submit_request( EXPORTING iv_actor = '01'  ##TODO "Changer avec constant
                                                       iv_guid  = ls_request_head_db-guid
                                                       iv_status = ls_request_head_db-request_status
                                                       iv_coment = ls_reqheader_main_data-note
                                             IMPORTING os_return = ls_actionreturn ).

            ENDIF.
          ELSE. "Save normal

            UPDATE zthrfiori_breq FROM ls_request_head_db.
          ENDIF.

* Updating request detail
* ========================
          ls_eg_main = CORRESPONDING #( ls_reqheader_main_data-toedugrantdetail ).
          ls_eg_main-guid =  ls_request_header-guid.
          UPDATE zthrfiori_eg_mai FROM ls_eg_main.


* Updating advances
* ========================
*          IF lines( ls_reqheader_main_data-toedugrantadvances[] ) > 0.
          IF ls_request_header-isadvance EQ abap_true.
            lo_education->update_advance_list(
              EXPORTING
                iv_guid        =     ls_reqheader_main_data-guid              " Benefits request - GUID Request
                it_advances    =     ls_reqheader_main_data-toedugrantadvances
              IMPORTING
                ev_return_code =           lv_return_code          " ABAP System Field: Return Code of ABAP Statements
                ev_message     =             lv_message
            ).
          ENDIF.

*          ENDIF.


* Updating claims
* ========================
          IF ls_request_header-isclaim EQ abap_true.
            lo_education->update_claim_list(
              EXPORTING
                iv_guid        =     ls_reqheader_main_data-guid              " Benefits request - GUID Request
                it_claims    =     ls_reqheader_main_data-toedugrantclaims
              IMPORTING
                ev_return_code =           lv_return_code          " ABAP System Field: Return Code of ABAP Statements
                ev_message     =             lv_message
            ).
          ENDIF.

        ENDIF.


**********************************************************************************************
**********************              Rental Subsidy             *******************************
**********************************************************************************************
        IF ls_request_head_db-request_type EQ zcl_hr_fiori_request=>c_request_type_rs.
          CREATE OBJECT lo_rental.
          IF ls_request_head_db-request_status EQ zcl_hr_fiori_request=>c_req_submited_employee. "submit

            "change status, update status_txt and NACTOR
            lo_rental->submit_request( EXPORTING iv_actor = '01' ##TODO "Changer avec constant
                                                     iv_guid  = ls_request_head_db-guid
                                                     iv_coment = ls_reqheader_main_data-note
                                           IMPORTING os_return = ls_actionreturn ).


          ELSE. "Save normal

            UPDATE zthrfiori_breq FROM ls_request_head_db.
          ENDIF.

* Updating request detail
* ========================
          ls_rs_main = CORRESPONDING #( ls_reqheader_main_data-torentalsubsidydetail ).
          ls_rs_main-guid =  ls_request_header-guid.
          UPDATE zthrfiori_rs_mai FROM ls_rs_main.


        ENDIF.

        ##TODO "handle errors
        copy_data_to_ref(
         EXPORTING
         is_data = ls_reqheader_main_data
         CHANGING
         cr_data = er_deep_entity
         ).


    ENDCASE.



  ENDMETHOD.
