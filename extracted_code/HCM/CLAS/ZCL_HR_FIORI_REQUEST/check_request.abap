  METHOD check_request.

*&- ----------------------------------------------------------------------- -&*
*&- Check eligibility of requester and validity of request
*&- ----------------------------------------------------------------------- -&*

******si rental, blocage au dela de 1 an
******si education grant, warning au dela de 15 mois
******checker eligibility, blocage
******checker si EG et advance, blocage si date setllemnt dans el passé vide, nimporte quelle occurence

    DATA(ls_request_header) = CORRESPONDING zthrfiori_breq( cs_request ).
    DATA : lv_min_date TYPE d.
    DATA: lv_app_code      TYPE char04,
          lv_pernr         TYPE persno,
          lv_date          TYPE dats,
          lv_eg_option     TYPE char1,
          lv_objps         TYPE objps,
          lv_is_eligible   TYPE flag,
          lv_message       TYPE string,
          lv_option        TYPE char1,
          ls_child_info    TYPE p0021,
          ls_child_info_pa TYPE pa0021,
          ls_actionreturn  TYPE zcl_zhr_benefits_commo_mpc_ext=>actionreturn,
          ls_parameter     TYPE /iwbep/s_mgw_name_value_pair,
          lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits.


    "Get pernr
    lv_pernr = ls_request_header-creator_pernr.
    CREATE OBJECT lo_benefits_util.
    IF lv_pernr IS INITIAL.
      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
    ENDIF.

    IF ls_request_header-request_type EQ c_request_type_eg.

      CALL FUNCTION 'HR_PT_ADD_MONTH_TO_DATE'
        EXPORTING
          dmm_datin = sy-datum
          dmm_count = '15'
          dmm_oper  = '-'
          dmm_pos   = space
        IMPORTING
          dmm_daout = lv_min_date.

      IF ls_request_header-begda LT lv_min_date.
        DATA(lo_ex) = NEW zcx_hr_benef_exception( textid = zcx_hr_benef_exception=>zwarn_educgrant_outside_frame ).
        lo_ex->set_severity( zcx_hr_benef_exception=>co_sev_warning ).
        RAISE EXCEPTION lo_ex.
      ENDIF.

*Check le setllement
      IF ls_request_header-isadvance EQ abap_true.

        SELECT SINGLE @abap_true
          INTO @DATA(lv_advance_not_settled_exists)
          FROM pa0965
          WHERE pernr = @lv_pernr
            AND subty = @ls_request_header-subty
            AND objps = @ls_request_header-objps
            AND egscd EQ '00000000'
            AND endda  < @ls_request_header-begda.
        IF lv_advance_not_settled_exists EQ abap_true.


          RAISE EXCEPTION TYPE zcx_hr_benef_exception
            EXPORTING
              textid = zcx_hr_benef_exception=>zerror_pastadvance_notsetl.


        ENDIF.
      ENDIF.

    ENDIF.


    IF ls_request_header-request_type EQ c_request_type_rs.

      CALL FUNCTION 'HR_PT_ADD_MONTH_TO_DATE'
        EXPORTING
          dmm_datin = sy-datum
          dmm_count = '12'
          dmm_oper  = '-'
          dmm_pos   = space
        IMPORTING
          dmm_daout = lv_min_date.

      IF ls_request_header-begda LT lv_min_date.
        RAISE EXCEPTION TYPE zcx_hr_benef_exception
          EXPORTING
            textid = zcx_hr_benef_exception=>zerror_rental_outside_frame.

      ENDIF.

    ENDIF.

****************************************
************* Eligibility **************
****************************************

*    lv_pernr = ls_request_header-creator_pernr.
*   Get personnel number if not provided
*    CREATE OBJECT lo_benefits_util.
*    IF lv_pernr IS INITIAL.
*      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
*    ENDIF.

    lv_objps = ls_request_header-objps.
*   Get child information if necessary
    IF lv_objps IS NOT INITIAL.
      SELECT SINGLE * INTO ls_child_info_pa
        FROM pa0021
          WHERE pernr = lv_pernr
            AND subty = '14'
            AND objps = lv_objps
            AND endda >= sy-datum
            AND begda <= sy-datum ##WARN_OK.
      MOVE-CORRESPONDING ls_child_info_pa TO ls_child_info ##ENH_OK.
    ENDIF.

    "2 calls
    lv_app_code = COND #( WHEN ls_request_header-request_type EQ c_request_type_rs THEN 'RENT' ELSE 'EDUG' ).
    lv_date = ls_request_header-begda.
    CALL FUNCTION 'Z_HRFIORI_BEN_ELIGIBILITY_RULE'
      EXPORTING
        iv_app         = lv_app_code
        iv_pernr       = lv_pernr
        iv_date        = lv_date
        iv_option      = lv_eg_option
        is_child       = ls_child_info
      IMPORTING
        ov_is_eligible = lv_is_eligible
        ov_message     = lv_message
        ov_option      = lv_option.

    IF lv_is_eligible EQ abap_false.

*   RAISE EXCEPTION TYPE zcx_hr_benef_exception

*      DATA(lo_ex) = NEW zcx_hr_benef_exception( ).   " ou avec textid = ...
*      lo_ex->set_text( lv_message ).
*      RAISE EXCEPTION lo_ex.

*      RAISE EXCEPTION TYPE zcx_hr_benef_exception.
      ##TODO "checker avec UNESCO les régles si pas de 391 par exmple, normal?
    ENDIF.



  ENDMETHOD.
