  METHOD check_eligibility.

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


*   Get functin import parameters
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'AppCode'.
    IF sy-subrc = 0.
      MOVE ls_parameter-value TO lv_app_code.
    ENDIF.
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'PersonnelNumber'.
    IF sy-subrc = 0.
      MOVE ls_parameter-value TO lv_pernr.
    ENDIF.
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'Date'.
    IF sy-subrc = 0.
      MOVE ls_parameter-value TO lv_date.
    ENDIF.
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'OptionEG'.
    IF sy-subrc = 0.
      MOVE ls_parameter-value TO lv_eg_option.
    ENDIF.
    READ TABLE it_parameter INTO ls_parameter WITH KEY name = 'ChildNumber'.
    IF sy-subrc = 0.
      MOVE ls_parameter-value TO lv_objps.
    ENDIF.

*   Get personnel number if not provided
    CREATE OBJECT lo_benefits_util.
    IF lv_pernr IS INITIAL.
      lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr ).
    ENDIF.

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

*   Check eligibility rules
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

    MOVE lv_is_eligible TO ls_actionreturn-iseligible.
    MOVE lv_message TO ls_actionreturn-message.
    MOVE lv_option TO ls_actionreturn-option.

    copy_data_to_ref( EXPORTING is_data = ls_actionreturn
                    CHANGING cr_data  = os_return ).

  ENDMETHOD.
