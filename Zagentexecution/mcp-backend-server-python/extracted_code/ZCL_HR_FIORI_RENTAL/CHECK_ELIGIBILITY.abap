  METHOD CHECK_ELIGIBILITY.

    DATA: lv_hl_country     TYPE land1,
          lv_ds_country     TYPE land1,
          lv_ansvh          TYPE ansvh,
          lv_persg          TYPE persg,
          lv_dsa_check      TYPE flag,
          lv_entry_ds_check TYPE flag,
          lv_ds_value_check TYPE flag,
          lv_str1           TYPE string,
          lv_str2           TYPE string,
          lo_benefits       TYPE  REF TO zcl_hr_fiori_benefits.

*   Default values for return variables
    ov_is_eligible = abap_false.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '007'
      INTO lv_str1.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '008'
      INTO lv_str2.
    CONCATENATE lv_str1 lv_str2
      INTO ov_message.

*   Get all necessary information
    CREATE OBJECT lo_benefits.
    lo_benefits->get_country_hl_and_ds( EXPORTING iv_pernr = iv_pernr
                                                  iv_date  = iv_date
                                        IMPORTING ov_country_ds = lv_ds_country
                                                  ov_country_hl = lv_hl_country ).
    lo_benefits->get_persg_and_ansvh( EXPORTING iv_pernr = iv_pernr
                                                iv_date  = iv_date
                                      IMPORTING ov_ansvh = lv_ansvh
                                                ov_persg = lv_persg ).

*   Eligibility check
*   1-Emplpoyee group
    IF lv_persg = c_international_staff OR lv_persg = c_local_staff.

*     2-Contract type
      CASE lv_persg.
        WHEN c_international_staff.

          IF lv_ansvh = c_contract_type_ft OR lv_ansvh = c_contract_type_indeterminate
            OR lv_ansvh = c_contract_type_jpo OR lv_ansvh = c_contract_type_pa
            OR lv_ansvh = c_contract_type_secondment_nun OR lv_ansvh = c_contract_type_ypp.

*           3-Country comparaison between DS and HL
            IF lv_ds_country <> lv_hl_country.

*             4-Check 30 days DSA
              check_dsa_eligibility( EXPORTING iv_pernr = iv_pernr
                                     IMPORTING ov_is_eligible = lv_dsa_check ).
              CHECK lv_dsa_check = abap_true.

*             5-Check entry in DS is inferior to 7 years
              check_entry_in_ds( EXPORTING iv_pernr = iv_pernr
                                 IMPORTING ov_is_eligible = lv_entry_ds_check ).
              CHECK lv_entry_ds_check = abap_true.

*             6-Check HS classification is different of H
              check_ds_value( EXPORTING iv_pernr = iv_pernr
                              IMPORTING ov_is_eligible = lv_ds_value_check ).
              CHECK lv_ds_value_check = abap_true.

              CLEAR: ov_message.
              ov_is_eligible = abap_true.

            ELSE.
              RETURN.
            ENDIF.

          ELSE.
            RETURN.
          ENDIF.

        WHEN c_local_staff.

          IF lv_ansvh = c_contract_type_ft OR lv_ansvh = c_contract_type_indeterminate
            OR lv_ansvh = c_contract_type_pa.

*           3-Country comparaison between DS and HL
            IF lv_ds_country <> lv_hl_country.

*             4-Check 30 days DSA
              check_dsa_eligibility( EXPORTING iv_pernr = iv_pernr
                                     IMPORTING ov_is_eligible = lv_dsa_check ).
              CHECK lv_dsa_check = abap_true.

*             5-Check entry in DS is inferior to 7 years
              check_entry_in_ds( EXPORTING iv_pernr = iv_pernr
                                 IMPORTING ov_is_eligible = lv_entry_ds_check ).
              CHECK lv_entry_ds_check = abap_true.

*             6-Check HS classification is different of H
              check_ds_value( EXPORTING iv_pernr = iv_pernr
                              IMPORTING ov_is_eligible = lv_ds_value_check ).
              CHECK lv_ds_value_check = abap_true.

              CLEAR: ov_message.
              ov_is_eligible = abap_true.

            ELSE.
              RETURN.
            ENDIF.

          ELSE.
            RETURN.
          ENDIF.

      ENDCASE.

    ELSE.
      RETURN.
    ENDIF.

  ENDMETHOD.
